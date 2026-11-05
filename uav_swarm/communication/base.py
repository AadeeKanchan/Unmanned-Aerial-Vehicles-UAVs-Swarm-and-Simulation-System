"""Abstract base class and data containers for UAV communication adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
from typing import Any, Dict, Optional, Tuple

from uav_swarm.config import DroneState


@dataclass
class VehicleTelemetry:
    """Unified telemetry packet returned by any communication adapter."""
    drone_id: int
    connected: bool = False
    state: DroneState = DroneState.IDLE
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    battery_percent: float = 100.0
    last_heartbeat: float = field(default_factory=time.time)
    armed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert telemetry state to dictionary for logging and serialization."""
        return {
            "drone_id": self.drone_id,
            "connected": self.connected,
            "state": self.state.value,
            "position": list(self.position),
            "target_position": list(self.target_position),
            "velocity": list(self.velocity),
            "battery_percent": round(self.battery_percent, 1),
            "last_heartbeat": self.last_heartbeat,
            "armed": self.armed,
        }


class VehicleAdapterBase(ABC):
    """Abstract interface defining required contract for all drone communication adapters."""

    def __init__(self, drone_id: int, **kwargs: Any) -> None:
        self.drone_id = drone_id
        self._connected: bool = False
        self._telemetry = VehicleTelemetry(drone_id=drone_id)

    @property
    def is_connected(self) -> bool:
        """Check whether the vehicle connection is currently active."""
        return self._connected

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection with the simulated or external vehicle."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Gracefully disconnect from vehicle."""
        pass

    @abstractmethod
    def send_arm_and_takeoff(self, target_altitude: float) -> bool:
        """Arm the drone and initiate takeoff to target altitude."""
        pass

    @abstractmethod
    def send_target_position(self, x: float, y: float, z: float) -> bool:
        """Dispatch 3D waypoint coordinate command."""
        pass

    @abstractmethod
    def send_land(self) -> bool:
        """Initiate landing sequence."""
        pass

    @abstractmethod
    def send_reset(self, home_pos: Tuple[float, float, float]) -> bool:
        """Reset drone state and teleport back to ground home coordinates."""
        pass

    @abstractmethod
    def get_telemetry(self) -> VehicleTelemetry:
        """Retrieve the latest telemetry snapshot."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Periodic update cycle (handles keepalives, timeouts, integration)."""
        pass

