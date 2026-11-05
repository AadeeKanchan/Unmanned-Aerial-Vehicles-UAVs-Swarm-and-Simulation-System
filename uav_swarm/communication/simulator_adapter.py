"""High-performance local simulation adapter operating purely in-memory."""

import time
from typing import Any, Tuple
import numpy as np

from uav_swarm.communication.base import VehicleAdapterBase, VehicleTelemetry
from uav_swarm.config import DroneState


class LocalSimulationAdapter(VehicleAdapterBase):
    """In-memory virtual vehicle adapter providing deterministic state and physics for local simulation."""

    def __init__(
        self,
        drone_id: int,
        home_position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        speed: float = 4.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(drone_id=drone_id, **kwargs)
        self.home_position = home_position
        self.speed = speed

        self._position = np.array(home_position, dtype=np.float64)
        self._target_position = np.array(home_position, dtype=np.float64)
        self._velocity = np.zeros(3, dtype=np.float64)
        self._state = DroneState.IDLE
        self._armed = False
        self._battery = 100.0
        self._connected = True

    def connect(self) -> bool:
        self._connected = True
        self._telemetry.connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False
        self._telemetry.connected = False

    def send_arm_and_takeoff(self, target_altitude: float) -> bool:
        if not self._connected:
            return False
        self._armed = True
        self._state = DroneState.LAUNCHING
        self._target_position[1] = target_altitude
        return True

    def send_target_position(self, x: float, y: float, z: float) -> bool:
        if not self._connected:
            return False
        self._target_position = np.array([x, y, z], dtype=np.float64)
        if self._state not in (DroneState.LAUNCHING, DroneState.LANDING):
            self._state = DroneState.TRANSITIONING
        return True

    def send_land(self) -> bool:
        if not self._connected:
            return False
        self._state = DroneState.LANDING
        # Vertical descent to ground elevation at current horizontal coordinates
        self._target_position[0] = self._position[0]
        self._target_position[1] = self.home_position[1]
        self._target_position[2] = self._position[2]
        return True

    def send_reset(self, home_pos: Tuple[float, float, float]) -> bool:
        self.home_position = home_pos
        self._position = np.array(home_pos, dtype=np.float64)
        self._target_position = np.array(home_pos, dtype=np.float64)
        self._velocity = np.zeros(3, dtype=np.float64)
        self._state = DroneState.IDLE
        self._armed = False
        self._battery = 100.0
        return True

    def get_telemetry(self) -> VehicleTelemetry:
        self._telemetry.connected = self._connected
        self._telemetry.state = self._state
        self._telemetry.position = (
            float(self._position[0]),
            float(self._position[1]),
            float(self._position[2]),
        )
        self._telemetry.target_position = (
            float(self._target_position[0]),
            float(self._target_position[1]),
            float(self._target_position[2]),
        )
        self._telemetry.velocity = (
            float(self._velocity[0]),
            float(self._velocity[1]),
            float(self._velocity[2]),
        )
        self._telemetry.battery_percent = self._battery
        self._telemetry.armed = self._armed
        self._telemetry.last_heartbeat = time.time()
        return self._telemetry

    def update(self, dt: float) -> None:
        if not self._connected or dt <= 0.0:
            return

        # Simple battery drain during flight
        if self._armed and self._battery > 0.0:
            self._battery = max(0.0, self._battery - (0.015 * dt))

        # Direct position stepping when active
        delta = self._target_position - self._position
        distance = float(np.linalg.norm(delta))

        if distance > 0.01:
            step_size = self.speed * dt
            if step_size >= distance:
                self._position = np.copy(self._target_position)
                self._velocity = np.zeros(3, dtype=np.float64)
                # Reached destination on this step
                if self._state == DroneState.LAUNCHING:
                    self._state = DroneState.IN_FLIGHT
                elif self._state == DroneState.TRANSITIONING:
                    self._state = DroneState.IN_FLIGHT
                elif self._state == DroneState.LANDING:
                    self._state = DroneState.LANDED
                    self._armed = False
            else:
                direction = delta / distance
                self._position += direction * step_size
                self._velocity = direction * self.speed
        else:
            self._velocity = np.zeros(3, dtype=np.float64)

            # State transition upon arrival
            if self._state == DroneState.LAUNCHING:
                self._state = DroneState.IN_FLIGHT
            elif self._state == DroneState.TRANSITIONING:
                self._state = DroneState.IN_FLIGHT
            elif self._state == DroneState.LANDING:
                self._state = DroneState.LANDED
                self._armed = False
