"""Unit tests for trajectory interpolation and smooth motion planning."""

import numpy as np
import pytest

from uav_swarm.swarm.trajectory import SwarmTrajectory, smoothstep


def test_smoothstep_properties() -> None:
    assert smoothstep(0.0) == 0.0
    assert smoothstep(1.0) == 1.0
    assert smoothstep(0.5) == 0.5
    # Clamping behavior
    assert smoothstep(-0.2) == 0.0
    assert smoothstep(1.5) == 1.0


def test_swarm_trajectory_progression() -> None:
    starts = np.zeros((4, 3))
    targets = np.array([
        [10.0, 5.0, 0.0],
        [0.0, 5.0, 10.0],
        [-10.0, 5.0, 0.0],
        [0.0, 5.0, -10.0],
    ])

    traj = SwarmTrajectory(starts, targets, speed=5.0, min_duration=1.0)
    assert not traj.is_finished
    assert traj.progress == 0.0

    # Step by half duration
    half_time = traj.duration / 2.0
    mid_pos = traj.update(half_time)
    assert 0.49 <= traj.progress <= 0.51
    # Positions should be halfway between start and target
    assert np.allclose(mid_pos, 0.5 * (starts + targets), atol=1e-4)

    # Step past end
    end_pos = traj.update(half_time + 1.0)
    assert traj.is_finished
    assert traj.progress == 1.0
    assert np.allclose(end_pos, targets)


def test_trajectory_sampling() -> None:
    starts = np.zeros((3, 3))
    targets = np.ones((3, 3)) * 5.0

    traj = SwarmTrajectory(starts, targets, speed=2.0)
    samples = traj.sample_trajectory_points(num_samples=10)

    assert samples.shape == (10, 3, 3)
    assert np.allclose(samples[0], starts)
    assert np.allclose(samples[-1], targets)

