"""Unit tests for proximity detection and trajectory conflict prediction."""

import numpy as np
import pytest

from uav_swarm.swarm.collision import (
    check_proximity,
    compute_distance_matrix,
    predict_trajectory_conflicts,
)
from uav_swarm.swarm.trajectory import SwarmTrajectory


def test_distance_matrix_calculation() -> None:
    pts = np.array([
        [0.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
        [0.0, 4.0, 0.0],
    ])
    mat = compute_distance_matrix(pts)
    assert mat.shape == (3, 3)
    assert np.isclose(mat[0, 1], 3.0)
    assert np.isclose(mat[0, 2], 4.0)
    assert np.isclose(mat[1, 2], 5.0)  # 3-4-5 right triangle


def test_proximity_warning_and_critical_detection() -> None:
    positions = np.array([
        [0.0, 5.0, 0.0],
        [1.8, 5.0, 0.0],  # 1.8m apart -> warning threshold is 2.2m
        [10.0, 5.0, 0.0], # far away
    ])

    report = check_proximity(positions, warning_distance=2.2, critical_distance=1.2)
    assert report.has_warnings
    assert not report.has_critical
    assert (0, 1, 1.8) in [(p[0], p[1], round(p[2], 1)) for p in report.warning_pairs]
    assert 0 in report.affected_drones
    assert 1 in report.affected_drones
    assert 2 not in report.affected_drones

    # Move closer to breach critical distance 1.2m
    positions[1] = [0.8, 5.0, 0.0]  # 0.8m apart
    report_crit = check_proximity(positions, warning_distance=2.2, critical_distance=1.2)
    assert report_crit.has_critical
    assert len(report_crit.critical_pairs) >= 1


def test_trajectory_conflict_prediction() -> None:
    # 2 drones flying directly towards each other and crossing at the exact center
    starts = np.array([
        [-5.0, 5.0, 0.0],
        [5.0, 5.0, 0.0],
    ])
    targets = np.array([
        [5.0, 5.0, 0.0],
        [-5.0, 5.0, 0.0],
    ])

    traj = SwarmTrajectory(starts, targets, speed=2.0)
    has_conflict, msgs = predict_trajectory_conflicts(
        trajectory=traj,
        warning_distance=2.2,
        critical_distance=1.2,
        num_time_steps=20,
    )

    assert has_conflict
    assert len(msgs) > 0
    assert any("CRITICAL" in m or "warning" in m for m in msgs)

