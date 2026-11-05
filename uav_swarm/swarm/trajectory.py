"""Trajectory interpolation and smooth motion planning for UAV swarms."""

from typing import Tuple, Optional
import numpy as np


def smoothstep(t: float) -> float:
    """Cubic smoothstep easing function: 3t^2 - 2t^3.

    Provides zero first derivatives at endpoints for smooth acceleration
    and deceleration without abrupt velocity jumps.
    """
    t = float(np.clip(t, 0.0, 1.0))
    return t * t * (3.0 - 2.0 * t)


class SwarmTrajectory:
    """Coordinates smooth, synchronized trajectory transitions for all drones in the swarm."""

    def __init__(
        self,
        start_positions: np.ndarray,
        target_positions: np.ndarray,
        speed: float = 4.0,
        min_duration: float = 1.0,
    ) -> None:
        """Initialize a new multi-drone trajectory transition.

        Args:
            start_positions: (N, 3) array of current drone positions.
            target_positions: (N, 3) array of target destination positions.
            speed: Target flight speed in units (meters) per second.
            min_duration: Minimum transition duration in seconds.
        """
        self.start_positions = np.array(start_positions, dtype=np.float64)
        self.target_positions = np.array(target_positions, dtype=np.float64)
        self.speed = max(0.1, float(speed))
        self.drone_count = len(self.start_positions)

        # Calculate Euclidean displacement per drone
        displacements = self.target_positions - self.start_positions
        distances = np.linalg.norm(displacements, axis=1)
        self.max_distance = float(np.max(distances)) if len(distances) > 0 else 0.0

        # Synchronized duration based on furthest drone travel
        calc_duration = self.max_distance / self.speed if self.speed > 0 else 1.0
        self.duration = max(min_duration, calc_duration)
        self.elapsed: float = 0.0

    @property
    def progress(self) -> float:
        """Normalized linear progress from 0.0 to 1.0."""
        if self.duration <= 0.0:
            return 1.0
        return float(np.clip(self.elapsed / self.duration, 0.0, 1.0))

    @property
    def is_finished(self) -> bool:
        """Check whether trajectory interpolation has completed."""
        return self.elapsed >= self.duration

    def update(self, dt: float) -> np.ndarray:
        """Advance time by dt and return the current interpolated positions for all drones.

        Args:
            dt: Delta time in seconds.

        Returns:
            np.ndarray: (N, 3) interpolated coordinates.
        """
        self.elapsed += dt
        return self.evaluate_at_progress(self.progress)

    def evaluate_at_progress(self, linear_progress: float) -> np.ndarray:
        """Evaluate positions for all drones at a given normalized linear progress [0, 1].

        Uses cubic smoothstep easing to achieve continuous velocity transitions.
        """
        alpha = smoothstep(linear_progress)
        return (1.0 - alpha) * self.start_positions + alpha * self.target_positions

    def sample_trajectory_points(self, num_samples: int = 20) -> np.ndarray:
        """Sample all drone positions across the full trajectory timeline.

        Used for pre-transition collision prediction and trajectory visualization.

        Returns:
            np.ndarray: shape (num_samples, N, 3)
        """
        alphas = np.linspace(0.0, 1.0, num_samples)
        samples = np.zeros((num_samples, self.drone_count, 3), dtype=np.float64)
        for idx, a in enumerate(alphas):
            samples[idx] = self.evaluate_at_progress(a)
        return samples

