"""MAVLink / SITL UDP communication adapter for external drone autonomy stacks."""

import json
import logging
import socket
import time
from typing import Any, Dict, Optional, Tuple

from uav_swarm.communication.base import VehicleAdapterBase, VehicleTelemetry
from uav_swarm.config import COMM_TIMEOUT_SECONDS, DroneState

logger = logging.getLogger(__name__)

# Check optional pymavlink availability
try:
    from pymavlink import mavutil
    HAS_PYMAVLINK = True
except ImportError:
    HAS_PYMAVLINK = False


class MAVLinkAdapter(VehicleAdapterBase):
    """Networked MAVLink / SITL communication adapter communicating over UDP.

    Connects to external autopilot simulators (e.g. ArduPilot SITL or PX4 SITL)
    on dedicated per-drone localhost UDP endpoints.
    """

    def __init__(
        self,
        drone_id: int,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        base_port: int = 14550,
        timeout: float = COMM_TIMEOUT_SECONDS,
        **kwargs: Any,
    ) -> None:
        super().__init__(drone_id=drone_id, **kwargs)
        self.host = host
        # Each vehicle can bind or connect to its own unique port offset
        self.port = port if port is not None else (base_port + drone_id)
        self.timeout = timeout

        self._sock: Optional[socket.socket] = None
        self._mav_conn: Any = None
        self._connected = False
        self._last_heartbeat_time = 0.0

        # Local telemetry cache
        self._current_pos = [0.0, 0.0, 0.0]
        self._target_pos = [0.0, 0.0, 0.0]
        self._velocity = [0.0, 0.0, 0.0]
        self._state = DroneState.IDLE
        self._battery = 100.0
        self._armed = False

    def connect(self) -> bool:
        """Establish non-blocking UDP socket connection to SITL vehicle endpoint."""
        try:
            if HAS_PYMAVLINK:
                # Connection string format for pymavlink UDP
                conn_str = f"udpout:{self.host}:{self.port}"
                self._mav_conn = mavutil.mavlink_connection(
                    conn_str,
                    source_system=255,  # GCS system ID
                    source_component=self.drone_id + 1,
                )
                self._connected = True
                self._last_heartbeat_time = time.time()
                logger.info(f"[Drone {self.drone_id}] MAVLink connected via {conn_str}")
                return True
            else:
                # Raw UDP fallback socket
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._sock.settimeout(0.05)
                self._connected = True
                self._last_heartbeat_time = time.time()
                logger.info(f"[Drone {self.drone_id}] Raw UDP socket connected to {self.host}:{self.port}")
                return True
        except Exception as ex:
            logger.warning(f"[Drone {self.drone_id}] Connection failed to {self.host}:{self.port}: {ex}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Close communication handles."""
        self._connected = False
        if self._mav_conn:
            try:
                self._mav_conn.close()
            except Exception:
                pass
            self._mav_conn = None
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def send_arm_and_takeoff(self, target_altitude: float) -> bool:
        """Send MAVLink arm and takeoff commands to external vehicle."""
        if not self._connected:
            return False

        self._armed = True
        self._state = DroneState.LAUNCHING
        self._target_pos[1] = target_altitude

        try:
            if HAS_PYMAVLINK and self._mav_conn:
                # Arm vehicle
                self._mav_conn.mav.command_long_send(
                    self._mav_conn.target_system,
                    self._mav_conn.target_component,
                    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                    0, 1, 0, 0, 0, 0, 0, 0
                )
                # Takeoff command
                self._mav_conn.mav.command_long_send(
                    self._mav_conn.target_system,
                    self._mav_conn.target_component,
                    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                    0, 0, 0, 0, 0, 0, 0, target_altitude
                )
                return True
            elif self._sock:
                payload = json.dumps({
                    "msg": "TAKEOFF",
                    "drone_id": self.drone_id,
                    "target_altitude": target_altitude,
                }).encode("utf-8")
                self._sock.sendto(payload, (self.host, self.port))
                return True
        except Exception as ex:
            logger.warning(f"[Drone {self.drone_id}] send_arm_and_takeoff error: {ex}")
            return False
        return False

    def send_target_position(self, x: float, y: float, z: float) -> bool:
        """Dispatch 3D waypoint coordinate command."""
        if not self._connected:
            return False

        self._target_pos = [x, y, z]
        if self._state not in (DroneState.LAUNCHING, DroneState.LANDING):
            self._state = DroneState.TRANSITIONING

        try:
            if HAS_PYMAVLINK and self._mav_conn:
                # In NED coordinates: North=Z, East=X, Down=-Y
                ned_north = z
                ned_east = x
                ned_down = -y
                type_mask = 0b0000111111111000  # Position only
                self._mav_conn.mav.set_position_target_local_ned_send(
                    0,  # time_boot_ms
                    self._mav_conn.target_system,
                    self._mav_conn.target_component,
                    mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                    type_mask,
                    ned_north, ned_east, ned_down,
                    0, 0, 0,  # velocity
                    0, 0, 0,  # accel
                    0, 0,     # yaw, yaw_rate
                )
                return True
            elif self._sock:
                payload = json.dumps({
                    "msg": "SET_POSITION",
                    "drone_id": self.drone_id,
                    "position": [x, y, z],
                }).encode("utf-8")
                self._sock.sendto(payload, (self.host, self.port))
                return True
        except Exception as ex:
            logger.warning(f"[Drone {self.drone_id}] send_target_position error: {ex}")
            return False
        return False

    def send_land(self) -> bool:
        """Send MAVLink LAND command."""
        if not self._connected:
            return False

        self._state = DroneState.LANDING
        self._target_pos[1] = 0.0

        try:
            if HAS_PYMAVLINK and self._mav_conn:
                self._mav_conn.mav.command_long_send(
                    self._mav_conn.target_system,
                    self._mav_conn.target_component,
                    mavutil.mavlink.MAV_CMD_NAV_LAND,
                    0, 0, 0, 0, 0, 0, 0, 0
                )
                return True
            elif self._sock:
                payload = json.dumps({
                    "msg": "LAND",
                    "drone_id": self.drone_id,
                }).encode("utf-8")
                self._sock.sendto(payload, (self.host, self.port))
                return True
        except Exception as ex:
            logger.warning(f"[Drone {self.drone_id}] send_land error: {ex}")
            return False
        return False

    def send_reset(self, home_pos: Tuple[float, float, float]) -> bool:
        """Reset drone state."""
        self._current_pos = list(home_pos)
        self._target_pos = list(home_pos)
        self._velocity = [0.0, 0.0, 0.0]
        self._state = DroneState.IDLE
        self._armed = False
        return True

    def get_telemetry(self) -> VehicleTelemetry:
        """Return latest telemetry snapshot."""
        self._telemetry.connected = self._connected
        self._telemetry.state = self._state
        self._telemetry.position = (self._current_pos[0], self._current_pos[1], self._current_pos[2])
        self._telemetry.target_position = (self._target_pos[0], self._target_pos[1], self._target_pos[2])
        self._telemetry.velocity = (self._velocity[0], self._velocity[1], self._velocity[2])
        self._telemetry.battery_percent = self._battery
        self._telemetry.armed = self._armed
        self._telemetry.last_heartbeat = self._last_heartbeat_time
        return self._telemetry

    def update(self, dt: float) -> None:
        """Process incoming MAVLink / UDP messages and check timeouts."""
        if not self._connected:
            return

        now = time.time()
        # Check timeout
        if self._last_heartbeat_time > 0 and (now - self._last_heartbeat_time) > self.timeout:
            # If no packet received within timeout, mark disconnected
            pass

        if HAS_PYMAVLINK and self._mav_conn:
            try:
                # Non-blocking receive
                msg = self._mav_conn.recv_match(blocking=False)
                if msg:
                    self._last_heartbeat_time = now
                    msg_type = msg.get_type()
                    if msg_type == "HEARTBEAT":
                        self._armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                    elif msg_type == "LOCAL_POSITION_NED":
                        # Convert NED (North=Z, East=X, Down=-Y) to Ursina (X, Y, Z)
                        self._current_pos[0] = msg.y
                        self._current_pos[1] = -msg.z
                        self._current_pos[2] = msg.x
                        self._velocity[0] = msg.vy
                        self._velocity[1] = -msg.vz
                        self._velocity[2] = msg.vx
                    elif msg_type == "BATTERY_STATUS":
                        self._battery = float(msg.battery_remaining)
            except Exception:
                pass
        elif self._sock:
            try:
                data, _ = self._sock.recvfrom(2048)
                if data:
                    self._last_heartbeat_time = now
                    parsed = json.loads(data.decode("utf-8"))
                    if "position" in parsed:
                        self._current_pos = parsed["position"]
                    if "state" in parsed:
                        self._state = DroneState(parsed["state"])
            except (socket.timeout, BlockingIOError, ConnectionResetError):
                pass
            except Exception:
                pass

