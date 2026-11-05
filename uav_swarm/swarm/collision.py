"""Pairwise proximity and collision detection for UAV swarm formations and trajectories."""

from dataclasses import dataclass, field
from typing import List, Set, Tuple
import numpy as np

from uav_swarm.config import CRITICAL_DISTANCE, WARNING_DISTANCE
from uav_swarm.swarm.trajectory import SwarmTrajectory


@dataclass
class CollisionReport:
    """Detailed collision and proximity evaluation report."""
    warning_pairs: List[Tuple[int, int, float]] = field(default_factory=list)
    critical_pairs: List[Tuple[int, int, float]] = field(default_factory=list)
    affected_drones: Set[int] = field(default_factory=set)
    min_observed_distance: float = float("inf")

    @property
    def has_warnings(self) -> bool:
        return len(self.warning_pairs) > 0

    @property
    def has_critical(self) -> bool:
        return len(self.critical_pairs) > 0

    def get_summary_text(self) -> str:
        """Formatted human-readable single-line summary for dashboard status."""
        if self.has_critical:
            pair = self.critical_pairs[0]
            return f"CRITICAL: D{pair[0]:02d} <-> D{pair[1]:02d} ({pair[2]:.2f}m)"
        if self.has_warnings:
            pair = self.warning_pairs[0]
            return f"WARNING: D{pair[0]:02d} <-> D{pair[1]:02d} ({pair[2]:.2f}m)"
        return "CLEAR: All drones within safe separation"


def compute_distance_matrix(positions: np.ndarray) -> np.ndarray:
    """Compute symmetric pairwise Euclidean distance matrix for an (N, 3) positions array."""
    if len(positions) == 0:
        return np.empty((0, 0), dtype=np.float64)
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    return np.linalg.norm(diff, axis=-1)


def check_proximity(
    positions: np.ndarray,
    warning_distance: float = WARNING_DISTANCE,
    critical_distance: float = CRITICAL_DISTANCE,
) -> CollisionReport:
    """Evaluate pairwise separation distances and detect proximity and collision events.

    Args:
        positions: (N, 3) coordinates of all active drones.
        warning_distance: Proximity threshold in meters triggering a warning state.
        critical_distance: Critical threshold in meters triggering a collision alarm.

    Returns:
        CollisionReport with flagged pairs and affected drone IDs.
    """
    n = len(positions)
    report = CollisionReport()
    if n < 2:
        return report

    dist_matrix = compute_distance_matrix(positions)
    min_dist = float("inf")

    # Evaluate upper triangle only (i < j)
    for i in range(n):
        for j in range(i + 1, n):
            d = float(dist_matrix[i, j])
            if d < min_dist:
                min_dist = d

            if d < critical_distance:
                report.critical_pairs.append((i, j, d))
                report.warning_pairs.append((i, j, d))
                report.affected_drones.add(i)
                report.affected_drones.add(j)
            elif d < warning_distance:
                report.warning_pairs.append((i, j, d))
                report.affected_drones.add(i)
                report.affected_drones.add(j)

    report.min_observed_distance = min_dist if min_dist != float("inf") else 0.0
    return report


def predict_trajectory_conflicts(
    trajectory: SwarmTrajectory,
    warning_distance: float = WARNING_DISTANCE,
    critical_distance: float = CRITICAL_DISTANCE,
    num_time_steps: int = 25,
) -> Tuple[bool, List[str]]:
    """Simulate and evaluate intermediate trajectory waypoints before execution.

    Detects if any two drones will intersect or breach safety separation during transition.

    Returns:
        (has_conflict, list_of_warning_strings)
    """
    samples = trajectory.sample_trajectory_points(num_samples=num_time_steps)
    conflicts: List[str] = []
    has_critical = False

    for step_idx, step_positions in enumerate(samples):
        progress = step_idx / (num_time_steps - 1)
        report = check_proximity(step_positions, warning_distance, critical_distance)

        if report.has_critical:
            has_critical = True
            for i, j, dist in report.critical_pairs:
                msg = f"Predicted CRITICAL breach: D{i:02d} <-> D{j:02d} at {progress:.0%} progress ({dist:.2f}m)"
                if msg not in conflicts:
                    conflicts.append(msg)
        elif report.has_warnings:
            for i, j, dist in report.warning_pairs:
                msg = f"Predicted proximity warning: D{i:02d} <-> D{j:02d} at {progress:.0%} progress ({dist:.2f}m)"
                if msg not in conflicts:
                    conflicts.append(msg)

    return (has_critical or len(conflicts) > 0, conflicts)

