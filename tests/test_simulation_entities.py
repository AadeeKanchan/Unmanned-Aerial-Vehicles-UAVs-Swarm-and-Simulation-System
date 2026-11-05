"""Integration tests verifying Ursina 3D visual components in headless mode."""

import pytest
from ursina import Ursina, application

from uav_swarm.dashboard.controls import MinimalDashboard
from uav_swarm.simulation.camera import SwarmCameraController
from uav_swarm.simulation.drone import DroneVisualEntity
from uav_swarm.simulation.environment import SimulationEnvironment
from uav_swarm.swarm.manager import SwarmManager


@pytest.fixture(scope="module")
def ursina_headless_app():
    """Create a headless Ursina application context for test execution."""
    app = Ursina(headless=True)
    yield app
    # No need to call application.quit() as it calls sys.exit()


def test_simulation_entities_and_dashboard(ursina_headless_app) -> None:
    # 1. Environment
    env = SimulationEnvironment()
    assert env.ground_grid is not None
    assert env.x_axis is not None
    assert env.y_axis is not None
    assert env.z_axis is not None

    # 2. Manager & Visual Drones
    mgr = SwarmManager(drone_count=4)
    visuals = [DroneVisualEntity(record=d) for d in mgr.drones]
    assert len(visuals) == 4

    # 3. Camera Controller
    cam = SwarmCameraController()
    cam.set_preset_view(1)
    assert cam.pitch == 28.0
    cam.set_preset_view(2)
    assert cam.pitch == 88.0

    # 4. Dashboard
    dash = MinimalDashboard(manager=mgr)
    assert dash.fleet_text is not None
    assert dash.safety_text is not None

    # Step simulation and visual entities
    mgr.launch_all()
    mgr.update(0.1)
    for vis in visuals:
        vis.update_visuals(0.1)
    cam.update(0.1)
    dash.update()

    # Clean up
    for vis in visuals:
        vis.destroy()
    env.destroy()
    dash.destroy()
