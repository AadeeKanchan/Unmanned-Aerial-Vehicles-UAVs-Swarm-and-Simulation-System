"""Central swarm management coordinator handling fleet lifecycle, formations, and playback."""

import csv
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from uav_swarm.communication.base import VehicleAdapterBase
from uav_swarm.communication.simulator_adapter import LocalSimulationAdapter
from uav_swarm.communication.mavlink_adapter import MAVLinkAdapter
from uav_swarm.config import (
    DEFAULT_ALTITUDE,
    DEFAULT_DRONE_COUNT,
    DEFAULT_SPACING,
    DEFAULT_SPEED,
    STATE_COLORS,
    CRITICAL_DISTANCE,
    WARNING_DISTANCE,
    DroneState,
)
from uav_swarm.swarm.collision import (
    CollisionReport,
    check_proximity,
    predict_trajectory_conflicts,
)
from uav_swarm.swarm.formations import AVAILABLE_FORMATIONS, generate_formation
from uav_swarm.swarm.trajectory import SwarmTrajectory

logger = logging.getLogger(__name__)


class DroneRecord:
    """Logical model representing a single virtual UAV within the swarm."""

    def __init__(
        self,
        drone_id: int,
        home_pos: Tuple[float, float, float],
        adapter: VehicleAdapterBase,
    ) -> None:
        self.drone_id = drone_id
        self.home_pos = np.array(home_pos, dtype=np.float64)
        self.current_pos = np.copy(self.home_pos)
        self.target_pos = np.copy(self.home_pos)
        self.state = DroneState.IDLE
        self.color_rgb = STATE_COLORS[DroneState.IDLE]
        self.adapter = adapter
        self.has_warning = False
        self.has_critical = False
        self.battery = 100.0

    @property
    def connected(self) -> bool:
        return self.adapter.is_connected


class SwarmManager:
    """Coordinates the entire fleet: state synchronization, transitions, commands, and telemetry."""

    def __init__(
        self,
        drone_count: int = DEFAULT_DRONE_COUNT,
        altitude: float = DEFAULT_ALTITUDE,
        spacing: float = DEFAULT_SPACING,
        speed: float = DEFAULT_SPEED,
        adapter_type: str = "simulation",
    ) -> None:
        self.drone_count = drone_count
        self.altitude = altitude
        self.spacing = spacing
        self.speed = speed
        self.adapter_type = adapter_type.lower()

        self.drones: List[DroneRecord] = []
        self.current_formation: str = "Ground Grid"
        self.active_trajectory: Optional[SwarmTrajectory] = None
        self.is_paused: bool = False
        self.collision_report = CollisionReport()
        self.pending_transition_warnings: List[str] = []

        # Playback system state
        self.is_playback_active: bool = False
        self.playback_keyframes: List[Dict[str, Any]] = []
        self.playback_time: float = 0.0
        self.playback_duration: float = 0.0

        # Build initial fleet
        self._initialize_fleet()

    def _initialize_fleet(self) -> None:
        """Create initial ground home layout for all drones in a compact grid."""
        self.drones.clear()
        cols = int(np.ceil(np.sqrt(self.drone_count)))
        rows = int(np.ceil(self.drone_count / cols))
        grid_spacing = 2.0  # compact ground separation

        for i in range(self.drone_count):
            r = i // cols
            c = i % cols
            # Centered on ground at Y = 0.0
            hx = (c - (cols - 1) / 2.0) * grid_spacing
            hy = 0.0
            hz = (r - (rows - 1) / 2.0) * grid_spacing

            if self.adapter_type == "mavlink":
                adapter: VehicleAdapterBase = MAVLinkAdapter(drone_id=i)
            else:
                adapter = LocalSimulationAdapter(drone_id=i, home_position=(hx, hy, hz), speed=self.speed)

            adapter.connect()
            self.drones.append(DroneRecord(drone_id=i, home_pos=(hx, hy, hz), adapter=adapter))

    @property
    def total_drones(self) -> int:
        return len(self.drones)

    @property
    def active_drones(self) -> int:
        """Count of drones currently airborne or transitioning."""
        return sum(
            1 for d in self.drones
            if d.state in (DroneState.ARMED, DroneState.LAUNCHING, DroneState.IN_FLIGHT, DroneState.TRANSITIONING)
        )

    @property
    def connected_drones(self) -> int:
        return sum(1 for d in self.drones if d.connected)

    def launch_all(self, target_altitude: Optional[float] = None) -> bool:
        """Command all drones to arm and launch to hover altitude."""
        alt = target_altitude if target_altitude is not None else self.altitude
        self.altitude = alt
        self.current_formation = "Hover Grid"
        self.is_playback_active = False

        starts = np.array([d.current_pos for d in self.drones], dtype=np.float64)
        targets = np.copy(starts)
        targets[:, 1] = alt  # Ascend vertically to target altitude

        for d in self.drones:
            d.state = DroneState.LAUNCHING
            d.target_pos = np.copy(targets[d.drone_id])
            d.adapter.send_arm_and_takeoff(alt)

        self.active_trajectory = SwarmTrajectory(
            start_positions=starts,
            target_positions=targets,
            speed=self.speed,
            min_duration=1.2,
        )
        return True

    def land_all(self) -> bool:
        """Command all drones to return to home X-Z ground footprint and touch down."""
        self.current_formation = "Landing"
        self.is_playback_active = False

        starts = np.array([d.current_pos for d in self.drones], dtype=np.float64)
        targets = np.array([d.home_pos for d in self.drones], dtype=np.float64)

        for d in self.drones:
            d.state = DroneState.LANDING
            d.target_pos = np.copy(targets[d.drone_id])
            d.adapter.send_land()

        self.active_trajectory = SwarmTrajectory(
            start_positions=starts,
            target_positions=targets,
            speed=self.speed,
            min_duration=1.5,
        )
        return True

    def reset_simulation(self) -> bool:
        """Instantly reset all drones to home coordinates and idle ground state."""
        self.active_trajectory = None
        self.is_playback_active = False
        self.current_formation = "Ground Grid"
        self.pending_transition_warnings.clear()

        for d in self.drones:
            d.current_pos = np.copy(d.home_pos)
            d.target_pos = np.copy(d.home_pos)
            d.state = DroneState.IDLE
            d.has_warning = False
            d.has_critical = False
            d.battery = 100.0
            d.adapter.send_reset(tuple(d.home_pos))

        self.collision_report = check_proximity(
            np.array([d.current_pos for d in self.drones], dtype=np.float64)
        )
        return True

    def toggle_pause(self) -> bool:
        """Toggle simulation pause state."""
        self.is_paused = not self.is_paused
        return self.is_paused

    def change_formation(
        self,
        formation_name: str,
        spacing: Optional[float] = None,
        altitude: Optional[float] = None,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> bool:
        """Generate target formation coordinates and begin smooth synchronized transition."""
        if formation_name not in AVAILABLE_FORMATIONS:
            logger.warning(f"Unsupported formation: {formation_name}")
            return False

        if spacing is not None:
            self.spacing = max(1.0, float(spacing))
        if altitude is not None:
            self.altitude = max(1.0, float(altitude))

        self.is_playback_active = False
        current_positions = np.array([d.current_pos for d in self.drones], dtype=np.float64)

        target_positions = generate_formation(
            formation_type=formation_name,
            count=self.drone_count,
            spacing=self.spacing,
            center=center,
            altitude=self.altitude,
        )

        # Plan smooth trajectory
        trajectory = SwarmTrajectory(
            start_positions=current_positions,
            target_positions=target_positions,
            speed=self.speed,
        )

        # Pre-transition collision prediction
        has_conflict, warnings = predict_trajectory_conflicts(
            trajectory=trajectory,
            warning_distance=WARNING_DISTANCE,
            critical_distance=CRITICAL_DISTANCE,
        )
        self.pending_transition_warnings = warnings

        # Apply target coordinates to drones and adapters
        for i, d in enumerate(self.drones):
            d.target_pos = np.copy(target_positions[i])
            d.state = DroneState.TRANSITIONING
            d.adapter.send_target_position(
                float(target_positions[i, 0]),
                float(target_positions[i, 1]),
                float(target_positions[i, 2]),
            )

        self.active_trajectory = trajectory
        self.current_formation = formation_name
        return True

    def update(self, dt: float) -> None:
        """Frame update advancing trajectories, adapters, proximity checks, and colors."""
        if self.is_paused or dt <= 0.0:
            return

        # 1. Update Playback if active
        if self.is_playback_active:
            self._update_playback(dt)

        # 2. Update Active Formation Trajectory
        elif self.active_trajectory is not None:
            new_positions = self.active_trajectory.update(dt)
            for i, d in enumerate(self.drones):
                d.current_pos = np.copy(new_positions[i])

            if self.active_trajectory.is_finished:
                # Arrival complete
                for d in self.drones:
                    if d.state == DroneState.TRANSITIONING or d.state == DroneState.LAUNCHING:
                        d.state = DroneState.IN_FLIGHT
                    elif d.state == DroneState.LANDING:
                        d.state = DroneState.LANDED
                self.active_trajectory = None

        # 3. Update communication adapters & fetch telemetry
        for d in self.drones:
            d.adapter.update(dt)
            telem = d.adapter.get_telemetry()
            d.battery = telem.battery_percent
            if self.adapter_type == "mavlink" and telem.connected:
                # If external SITL is providing authoritative positioning
                d.current_pos = np.array(telem.position, dtype=np.float64)

        # 4. Proximity & Collision Detection
        positions = np.array([d.current_pos for d in self.drones], dtype=np.float64)
        self.collision_report = check_proximity(
            positions=positions,
            warning_distance=WARNING_DISTANCE,
            critical_distance=CRITICAL_DISTANCE,
        )

        # 5. Update Drone Color states & Warnings
        for d in self.drones:
            d.has_warning = d.drone_id in self.collision_report.affected_drones
            d.has_critical = any(
                pair[0] == d.drone_id or pair[1] == d.drone_id
                for pair in self.collision_report.critical_pairs
            )

            # Apply state color
            if d.has_critical or d.has_warning:
                d.color_rgb = STATE_COLORS[DroneState.WARNING]
            else:
                d.color_rgb = STATE_COLORS.get(d.state, (0.7, 0.7, 0.7))

    # --- Trajectory Playback and Import/Export ---

    def export_trajectory_data(self, filepath: str, format_type: str = "json") -> bool:
        """Export current formation / trajectory snapshot to JSON or CSV."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        now = time.time()
        records: List[Dict[str, Any]] = []

        for d in self.drones:
            records.append({
                "drone_id": d.drone_id,
                "timestamp": round(now, 3),
                "x": round(float(d.current_pos[0]), 3),
                "y": round(float(d.current_pos[1]), 3),
                "z": round(float(d.current_pos[2]), 3),
                "r": round(float(d.color_rgb[0]), 3),
                "g": round(float(d.color_rgb[1]), 3),
                "b": round(float(d.color_rgb[2]), 3),
                "state": d.state.value,
            })

        fmt = format_type.lower()
        try:
            if fmt == "csv" or filepath.endswith(".csv"):
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=["drone_id", "timestamp", "x", "y", "z", "r", "g", "b", "state"],
                    )
                    writer.writeheader()
                    writer.writerows(records)
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump({"formation": self.current_formation, "keyframes": records}, f, indent=2)
            return True
        except Exception as ex:
            logger.error(f"Failed to export trajectory: {ex}")
            return False

    def import_trajectory_data(self, filepath: str) -> List[Dict[str, Any]]:
        """Import trajectory keyframe data from JSON or CSV file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Trajectory file not found: {filepath}")

        keyframes: List[Dict[str, Any]] = []
        if filepath.endswith(".csv"):
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    keyframes.append({
                        "drone_id": int(row["drone_id"]),
                        "timestamp": float(row["timestamp"]),
                        "x": float(row["x"]),
                        "y": float(row["y"]),
                        "z": float(row["z"]),
                        "r": float(row.get("r", 0.7)),
                        "g": float(row.get("g", 0.7)),
                        "b": float(row.get("b", 0.7)),
                        "state": row.get("state", "IN_FLIGHT"),
                    })
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "keyframes" in data:
                    keyframes = data["keyframes"]
                elif isinstance(data, list):
                    keyframes = data

        return keyframes

    def start_playback(self, keyframes: List[Dict[str, Any]]) -> bool:
        """Initialize and begin trajectory playback inside the simulator."""
        if not keyframes:
            return False

        # Group keyframes by drone_id
        drone_map: Dict[int, List[Dict[str, Any]]] = {}
        for k in keyframes:
            did = k["drone_id"]
            drone_map.setdefault(did, []).append(k)

        # Normalize timestamps starting at 0.0
        min_time = min(k["timestamp"] for k in keyframes)
        max_time = max(k["timestamp"] for k in keyframes)
        for k in keyframes:
            k["rel_time"] = k["timestamp"] - min_time

        self.playback_keyframes = keyframes
        self.playback_time = 0.0
        self.playback_duration = max(0.5, max_time - min_time)
        self.is_playback_active = True
        self.active_trajectory = None
        self.current_formation = "Playback"

        # Set initial positions at rel_time = 0.0
        self._update_playback(0.0)
        return True

    def stop_playback(self) -> None:
        self.is_playback_active = False

    def _update_playback(self, dt: float) -> None:
        """Step playback timeline and update drone positions and colors."""
        self.playback_time += dt
        if self.playback_time > self.playback_duration:
            self.playback_time = self.playback_duration
            self.is_playback_active = False

        # Apply positions from nearest keyframe for each drone
        for d in self.drones:
            candidates = [k for k in self.playback_keyframes if k["drone_id"] == d.drone_id]
            if not candidates:
                continue
            # Pick keyframe closest to current playback_time
            best_k = min(candidates, key=lambda item: abs(item.get("rel_time", 0.0) - self.playback_time))
            d.current_pos = np.array([best_k["x"], best_k["y"], best_k["z"]], dtype=np.float64)
            d.color_rgb = (best_k["r"], best_k["g"], best_k["b"])
            try:
                d.state = DroneState(best_k.get("state", "IN_FLIGHT"))
            except ValueError:
                d.state = DroneState.IN_FLIGHT

