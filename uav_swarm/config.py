"""Global configuration constants and settings for the UAV Swarm Simulation System."""

from enum import Enum
from typing import Tuple


class DroneState(str, Enum):
    """Lifecycle and operational states of a UAV."""
    IDLE = "IDLE"
    ARMED = "ARMED"
    LAUNCHING = "LAUNCHING"
    IN_FLIGHT = "IN_FLIGHT"
    TRANSITIONING = "TRANSITIONING"
    LANDING = "LANDING"
    LANDED = "LANDED"
    WARNING = "WARNING"


# Window and Rendering Settings
WINDOW_TITLE: str = "UAV Swarm Simulation System"
WINDOW_SIZE: Tuple[int, int] = (1280, 720)
TARGET_FPS: int = 60
BG_COLOR: Tuple[float, float, float] = (0.07, 0.08, 0.10)
GRID_SIZE: int = 80
GRID_SPACING: float = 2.0
GRID_COLOR: Tuple[float, float, float, float] = (0.20, 0.22, 0.27, 0.6)

# Swarm Defaults
DEFAULT_DRONE_COUNT: int = 16
DEFAULT_ALTITUDE: float = 5.0
DEFAULT_SPACING: float = 3.0
DEFAULT_SPEED: float = 4.0  # units per second
DRONE_SCALE: float = 0.5

# Proximity and Safety Metrics (meters / units)
CRITICAL_DISTANCE: float = 1.2
WARNING_DISTANCE: float = 2.2

# RGB Color Mapping for Drone States (0.0 to 1.0 range)
STATE_COLORS = {
    DroneState.IDLE: (0.65, 0.70, 0.75),           # Soft metallic gray
    DroneState.ARMED: (1.00, 0.85, 0.25),          # Bright amber
    DroneState.LAUNCHING: (0.25, 0.80, 1.00),      # Electric sky blue
    DroneState.IN_FLIGHT: (0.15, 0.90, 0.45),      # Emerald active green
    DroneState.TRANSITIONING: (0.40, 0.70, 1.00),  # Cyan transition
    DroneState.LANDING: (1.00, 0.55, 0.15),        # Warm orange
    DroneState.LANDED: (0.40, 0.42, 0.46),         # Muted resting gray
    DroneState.WARNING: (1.00, 0.20, 0.20),        # Critical collision crimson
}

# Communication Settings
DEFAULT_ADAPTER_TYPE: str = "simulation"  # "simulation" or "mavlink"
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_BASE_PORT: int = 14550
COMM_TIMEOUT_SECONDS: float = 3.0
HEARTBEAT_INTERVAL: float = 1.0

