"""Main application entry point for the UAV Swarm Simulation System."""

import argparse
import os
import sys
from typing import List

# Ensure parent directory is in sys.path when running as script
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ursina import (
    Entity,
    Ursina,
    application,
    time,
    window,
)

from uav_swarm.config import (
    DEFAULT_ALTITUDE,
    DEFAULT_DRONE_COUNT,
    DEFAULT_SPACING,
    DEFAULT_SPEED,
    WINDOW_SIZE,
    WINDOW_TITLE,
)
from uav_swarm.dashboard.controls import MinimalDashboard
from uav_swarm.simulation.camera import SwarmCameraController
from uav_swarm.simulation.drone import DroneVisualEntity
from uav_swarm.simulation.environment import SimulationEnvironment
from uav_swarm.swarm.manager import SwarmManager


def create_sample_trajectory(manager: SwarmManager) -> None:
    """Pre-generate a demonstration trajectory file in data/formations."""
    folder = os.path.join(parent_dir, "data", "formations")
    os.makedirs(folder, exist_ok=True)
    sample_file = os.path.join(folder, "sample_helix_flight.json")
    if not os.path.exists(sample_file):
        # Generate helix snapshot
        manager.change_formation("Helix", spacing=3.0, altitude=6.0)
        manager.export_trajectory_data(sample_file, format_type="json")
        manager.reset_simulation()


def main() -> None:
    parser = argparse.ArgumentParser(description="UAV Swarm Simulation System")
    parser.add_argument("--drones", type=int, default=DEFAULT_DRONE_COUNT, help="Number of virtual UAVs in swarm")
    parser.add_argument("--altitude", type=float, default=DEFAULT_ALTITUDE, help="Default flight altitude in meters")
    parser.add_argument("--spacing", type=float, default=DEFAULT_SPACING, help="Formation spacing in meters")
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED, help="Flight speed in m/s")
    parser.add_argument("--adapter", type=str, default="simulation", choices=["simulation", "mavlink"], help="Communication adapter")
    parser.add_argument("--headless", action="store_true", help="Run headlessly without opening an interactive window (for automated testing)")
    parser.add_argument("--steps", type=int, default=0, help="If > 0, run exactly this many update steps then exit cleanly")
    args = parser.parse_args()

    # 1. Initialize Ursina Engine
    window.icon = ""
    app = Ursina(
        title=WINDOW_TITLE,
        borderless=False,
        fullscreen=False,
        size=WINDOW_SIZE,
        headless=args.headless,
    )
    if not args.headless:
        window.fps_counter.enabled = True
        window.exit_button.visible = False

    # 2. Build 3D Environment (Ground grid, reference axes, dark theme)
    env = SimulationEnvironment()

    # 3. Initialize Fleet Swarm Manager
    manager = SwarmManager(
        drone_count=args.drones,
        altitude=args.altitude,
        spacing=args.spacing,
        speed=args.speed,
        adapter_type=args.adapter,
    )

    # 4. Create 3D Visual Drone Entities
    drone_visuals: List[DroneVisualEntity] = [
        DroneVisualEntity(record=d) for d in manager.drones
    ]

    # 5. Interactive Camera & HUD Dashboard
    camera_ctrl = SwarmCameraController()
    dashboard = MinimalDashboard(manager=manager)

    # Pre-generate sample data
    create_sample_trajectory(manager)

    # Clean Controller Entity handling frame updates and input events
    class SwarmController(Entity):
        def __init__(self) -> None:
            super().__init__()
            self.step_count = 0

        def update(self) -> None:
            dt = time.dt if time.dt > 0.0 else 0.016
            manager.update(dt)

            for vis in drone_visuals:
                vis.update_visuals(dt)

            camera_ctrl.update(dt)
            dashboard.update()

            self.step_count += 1
            if args.steps > 0 and self.step_count >= args.steps:
                print(f"Simulation completed {self.step_count} steps successfully.")
                application.quit()

        def input(self, key: str) -> None:
            if key == "escape":
                application.quit()
            elif key == "space":
                dashboard._on_pause_click()
            elif key in ("l", "l_up"):
                dashboard._on_launch_click()
            elif key in ("k", "k_up"):
                dashboard._on_land_click()
            elif key in ("r", "r_up"):
                dashboard._on_reset_click()
            else:
                camera_ctrl.handle_input(key)

    controller = SwarmController()

    # If headless with steps specified, step deterministically and exit
    if args.headless and args.steps > 0:
        for _ in range(args.steps):
            app.step()
        print(f"Headless simulation completed {args.steps} steps successfully.")
        return

    # Run Ursina interactive simulation loop
    app.run()


if __name__ == "__main__":
    main()
