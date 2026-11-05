"""Unit tests for communication adapters (Local Simulation and MAVLink/SITL)."""

import time
import pytest

from uav_swarm.communication.base import VehicleTelemetry
from uav_swarm.communication.simulator_adapter import LocalSimulationAdapter
from uav_swarm.communication.mavlink_adapter import MAVLinkAdapter, HAS_PYMAVLINK
from uav_swarm.config import DroneState


def test_local_simulation_adapter_lifecycle() -> None:
    adapter = LocalSimulationAdapter(drone_id=1, home_position=(2.0, 0.0, 2.0), speed=5.0)
    assert adapter.is_connected
    telem = adapter.get_telemetry()
    assert telem.drone_id == 1
    assert telem.state == DroneState.IDLE
    assert telem.position == (2.0, 0.0, 2.0)

    # Takeoff
    assert adapter.send_arm_and_takeoff(target_altitude=5.0)
    adapter.update(0.5)
    telem_after = adapter.get_telemetry()
    assert telem_after.armed
    assert telem_after.position[1] > 0.0

    # Step to completion of takeoff
    adapter.update(1.0)
    telem_arrived = adapter.get_telemetry()
    assert telem_arrived.state == DroneState.IN_FLIGHT

    # Target position
    assert adapter.send_target_position(10.0, 5.0, 10.0)
    telem_tgt = adapter.get_telemetry()
    assert telem_tgt.target_position == (10.0, 5.0, 10.0)

    # Landing
    assert adapter.send_land()
    adapter.update(2.0)
    telem_landed = adapter.get_telemetry()
    assert telem_landed.state == DroneState.LANDED
    assert not telem_landed.armed

    # Reset
    assert adapter.send_reset((0.0, 0.0, 0.0))
    telem_reset = adapter.get_telemetry()
    assert telem_reset.state == DroneState.IDLE
    assert telem_reset.position == (0.0, 0.0, 0.0)


def test_mavlink_adapter_initialization_and_failure_handling() -> None:
    # Test connection and non-blocking failure tolerance
    adapter = MAVLinkAdapter(drone_id=0, host="127.0.0.1", port=14550)
    # Connecting to localhost UDP port when no SITL is active should not raise exceptions
    connected = adapter.connect()
    assert isinstance(connected, bool)

    telem = adapter.get_telemetry()
    assert isinstance(telem, VehicleTelemetry)
    assert telem.drone_id == 0

    # Sending commands when SITL daemon is absent should return False or handle safely without crashing
    res_arm = adapter.send_arm_and_takeoff(target_altitude=5.0)
    assert isinstance(res_arm, bool)

    res_pos = adapter.send_target_position(5.0, 5.0, 5.0)
    assert isinstance(res_pos, bool)

    res_land = adapter.send_land()
    assert isinstance(res_land, bool)

    # Updating should execute without throwing
    adapter.update(0.1)

    # Disconnect cleanly
    adapter.disconnect()
    assert not adapter.is_connected

