"""Unit tests for SwarmManager fleet coordination, commands, JSON/CSV I/O, and playback."""

import os
import tempfile
import numpy as np
import pytest

from uav_swarm.config import DroneState
from uav_swarm.swarm.manager import SwarmManager


def test_swarm_manager_initialization() -> None:
    mgr = SwarmManager(drone_count=8, altitude=5.0, spacing=3.0, speed=4.0)
    assert mgr.total_drones == 8
    assert mgr.connected_drones == 8
    assert mgr.active_drones == 0
    assert mgr.current_formation == "Ground Grid"
    assert not mgr.is_paused


def test_swarm_manager_launch_and_land() -> None:
    mgr = SwarmManager(drone_count=4, altitude=6.0)

    mgr.launch_all()
    assert mgr.active_drones == 4
    for d in mgr.drones:
        assert d.state == DroneState.LAUNCHING

    # Step simulation until arrival
    mgr.update(2.0)
    for d in mgr.drones:
        assert d.state == DroneState.IN_FLIGHT
        assert np.isclose(d.current_pos[1], 6.0, atol=0.1)

    # Command landing
    mgr.land_all()
    for d in mgr.drones:
        assert d.state == DroneState.LANDING

    mgr.update(2.5)
    for d in mgr.drones:
        assert d.state == DroneState.LANDED
        assert np.isclose(d.current_pos[1], 0.0, atol=0.1)


def test_formation_transition() -> None:
    mgr = SwarmManager(drone_count=6, altitude=5.0, spacing=3.0)
    mgr.launch_all()
    mgr.update(2.0)

    success = mgr.change_formation("Circle", spacing=3.5)
    assert success
    assert mgr.current_formation == "Circle"
    assert mgr.active_trajectory is not None

    # Step to completion
    mgr.update(3.0)
    assert mgr.active_trajectory is None
    for d in mgr.drones:
        assert d.state == DroneState.IN_FLIGHT


def test_export_and_import_json_and_csv() -> None:
    mgr = SwarmManager(drone_count=5, altitude=4.0)
    mgr.launch_all()
    mgr.update(1.5)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "trajectory.json")
        csv_file = os.path.join(tmpdir, "trajectory.csv")

        # Test JSON
        assert mgr.export_trajectory_data(json_file, format_type="json")
        assert os.path.exists(json_file)
        imported_json = mgr.import_trajectory_data(json_file)
        assert len(imported_json) == 5
        assert imported_json[0]["drone_id"] == 0

        # Test CSV
        assert mgr.export_trajectory_data(csv_file, format_type="csv")
        assert os.path.exists(csv_file)
        imported_csv = mgr.import_trajectory_data(csv_file)
        assert len(imported_csv) == 5
        assert imported_csv[1]["drone_id"] == 1


def test_playback_execution() -> None:
    mgr = SwarmManager(drone_count=4, altitude=5.0)

    # Simulated keyframes over 2.0 seconds
    keyframes = [
        {"drone_id": 0, "timestamp": 100.0, "x": 0.0, "y": 2.0, "z": 0.0, "r": 0.2, "g": 0.8, "b": 0.5, "state": "IN_FLIGHT"},
        {"drone_id": 0, "timestamp": 102.0, "x": 5.0, "y": 8.0, "z": 2.0, "r": 0.2, "g": 0.8, "b": 0.5, "state": "IN_FLIGHT"},
    ]

    assert mgr.start_playback(keyframes)
    assert mgr.is_playback_active
    assert mgr.current_formation == "Playback"

    # Step halfway
    mgr.update(1.0)
    assert mgr.is_playback_active

    # Step past end
    mgr.update(2.5)
    assert not mgr.is_playback_active

