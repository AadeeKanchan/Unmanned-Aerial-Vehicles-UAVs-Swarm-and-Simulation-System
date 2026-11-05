"""Minimal, high-contrast, integrated dashboard HUD for UAV fleet operations."""

import os
import time
from typing import Callable, Optional
from ursina import (
    Button,
    Entity,
    Text,
    Vec2,
    camera,
    color,
    destroy,
    window,
)

from uav_swarm.swarm.formations import AVAILABLE_FORMATIONS
from uav_swarm.swarm.manager import SwarmManager


class MinimalDashboard:
    """Integrated HUD presenting fleet status, formation selection, and execution controls."""

    def __init__(self, manager: SwarmManager) -> None:
        self.manager = manager
        self.ui_elements = []

        # Color palette for dark UI (0.0 to 1.0 range)
        self.bg_panel_color = color.rgba(0.06, 0.07, 0.09, 0.90)
        self.btn_idle_color = color.rgb(0.14, 0.16, 0.19)
        self.btn_highlight = color.rgb(0.20, 0.40, 0.70)
        self.accent_green = color.rgb(0.12, 0.75, 0.42)
        self.accent_red = color.rgb(0.88, 0.20, 0.20)
        self.accent_amber = color.rgb(0.92, 0.65, 0.12)

        # 1. Top Status Banner Panel
        self.top_panel = Entity(
            parent=camera.ui,
            model="quad",
            scale=(1.75, 0.11),
            position=(0, 0.44),
            color=self.bg_panel_color,
        )
        self.ui_elements.append(self.top_panel)

        # Fleet Telemetry Summary Text
        self.fleet_text = Text(
            parent=camera.ui,
            text="",
            position=(-0.85, 0.48),
            scale=0.9,
            color=color.white,
        )
        self.ui_elements.append(self.fleet_text)

        # Safety & Collision Warning Line
        self.safety_text = Text(
            parent=camera.ui,
            text="",
            position=(-0.85, 0.425),
            scale=0.85,
            color=color.rgb(0.40, 0.90, 0.55),
        )
        self.ui_elements.append(self.safety_text)

        # Notification / Toast message
        self.notification_text = Text(
            parent=camera.ui,
            text="Ready. Use buttons below or keyboard: [Space] Pause, [1-4] Views, [R] Reset",
            position=(0.0, 0.425),
            origin=(0, 0),
            scale=0.75,
            color=color.rgb(0.65, 0.72, 0.80),
        )
        self.ui_elements.append(self.notification_text)
        self._notification_expire: float = 0.0

        # 2. Bottom Controls Bar
        self.bottom_panel = Entity(
            parent=camera.ui,
            model="quad",
            scale=(1.75, 0.14),
            position=(0, -0.42),
            color=self.bg_panel_color,
        )
        self.ui_elements.append(self.bottom_panel)

        # Build interactive control buttons
        self._build_action_buttons()
        self._build_formation_buttons()
        self._build_parameter_buttons()
        self._build_trajectory_buttons()

    def show_message(self, msg: str, duration: float = 4.0) -> None:
        """Display a temporary notification message in the header."""
        self.notification_text.text = msg
        self._notification_expire = time.time() + duration

    def _build_action_buttons(self) -> None:
        """Create primary fleet action buttons (Launch, Land, Reset, Pause)."""
        btn_y = -0.38
        btn_h = 0.045
        btn_w = 0.11
        spacing = 0.118
        start_x = -0.82

        # Launch All
        self.btn_launch = Button(
            parent=camera.ui,
            text="Launch All",
            scale=(btn_w, btn_h),
            position=(start_x + 0 * spacing, btn_y),
            color=color.rgb(0.08, 0.48, 0.24),
            highlight_color=color.rgb(0.12, 0.64, 0.32),
            on_click=self._on_launch_click,
        )
        self.btn_launch.text_entity.scale = 0.8
        self.ui_elements.append(self.btn_launch)

        # Land All
        self.btn_land = Button(
            parent=camera.ui,
            text="Land All",
            scale=(btn_w, btn_h),
            position=(start_x + 1 * spacing, btn_y),
            color=color.rgb(0.55, 0.28, 0.08),
            highlight_color=color.rgb(0.70, 0.36, 0.10),
            on_click=self._on_land_click,
        )
        self.btn_land.text_entity.scale = 0.8
        self.ui_elements.append(self.btn_land)

        # Reset
        self.btn_reset = Button(
            parent=camera.ui,
            text="Reset",
            scale=(btn_w, btn_h),
            position=(start_x + 2 * spacing, btn_y),
            color=self.btn_idle_color,
            highlight_color=color.rgb(0.24, 0.26, 0.30),
            on_click=self._on_reset_click,
        )
        self.btn_reset.text_entity.scale = 0.8
        self.ui_elements.append(self.btn_reset)

        # Pause / Resume
        self.btn_pause = Button(
            parent=camera.ui,
            text="Pause",
            scale=(btn_w, btn_h),
            position=(start_x + 3 * spacing, btn_y),
            color=self.btn_idle_color,
            highlight_color=color.rgb(0.24, 0.26, 0.30),
            on_click=self._on_pause_click,
        )
        self.btn_pause.text_entity.scale = 0.8
        self.ui_elements.append(self.btn_pause)

    def _build_formation_buttons(self) -> None:
        """Create buttons for each of the 6 3D formations."""
        btn_y = -0.445
        btn_h = 0.042
        btn_w = 0.10
        spacing = 0.108
        start_x = -0.82

        self.formation_buttons = {}
        for idx, fmt_name in enumerate(AVAILABLE_FORMATIONS):
            btn = Button(
                parent=camera.ui,
                text=fmt_name,
                scale=(btn_w, btn_h),
                position=(start_x + idx * spacing, btn_y),
                color=self.btn_idle_color,
                highlight_color=self.btn_highlight,
                on_click=lambda name=fmt_name: self._on_formation_click(name),
            )
            btn.text_entity.scale = 0.72
            self.formation_buttons[fmt_name] = btn
            self.ui_elements.append(btn)

    def _build_parameter_buttons(self) -> None:
        """Create Spacing and Speed stepper controls."""
        btn_y_spacing = -0.38
        btn_y_speed = -0.445
        btn_h = 0.042
        btn_w_step = 0.035
        btn_w_lbl = 0.12

        col_x = 0.10

        # Spacing: [-] [ Spacing: 3.0m ] [+]
        self.btn_spacing_minus = Button(
            parent=camera.ui,
            text="-",
            scale=(btn_w_step, btn_h),
            position=(col_x, btn_y_spacing),
            color=self.btn_idle_color,
            on_click=self._on_spacing_dec,
        )
        self.lbl_spacing = Button(
            parent=camera.ui,
            text=f"Spacing: {self.manager.spacing:.1f}m",
            scale=(btn_w_lbl, btn_h),
            position=(col_x + 0.082, btn_y_spacing),
            color=color.rgb(0.10, 0.11, 0.14),
        )
        self.lbl_spacing.text_entity.scale = 0.75
        self.btn_spacing_plus = Button(
            parent=camera.ui,
            text="+",
            scale=(btn_w_step, btn_h),
            position=(col_x + 0.165, btn_y_spacing),
            color=self.btn_idle_color,
            on_click=self._on_spacing_inc,
        )
        self.ui_elements.extend([self.btn_spacing_minus, self.lbl_spacing, self.btn_spacing_plus])

        # Speed: [-] [ Speed: 4.0m/s ] [+]
        self.btn_speed_minus = Button(
            parent=camera.ui,
            text="-",
            scale=(btn_w_step, btn_h),
            position=(col_x, btn_y_speed),
            color=self.btn_idle_color,
            on_click=self._on_speed_dec,
        )
        self.lbl_speed = Button(
            parent=camera.ui,
            text=f"Speed: {self.manager.speed:.1f}m/s",
            scale=(btn_w_lbl, btn_h),
            position=(col_x + 0.082, btn_y_speed),
            color=color.rgb(0.10, 0.11, 0.14),
        )
        self.lbl_speed.text_entity.scale = 0.75
        self.btn_speed_plus = Button(
            parent=camera.ui,
            text="+",
            scale=(btn_w_step, btn_h),
            position=(col_x + 0.165, btn_y_speed),
            color=self.btn_idle_color,
            on_click=self._on_speed_inc,
        )
        self.ui_elements.extend([self.btn_speed_minus, self.lbl_speed, self.btn_speed_plus])

    def _build_trajectory_buttons(self) -> None:
        """Create buttons for Save JSON, Save CSV, and Load & Play trajectory."""
        btn_h = 0.045
        btn_w = 0.13
        start_x = 0.52

        # Export JSON
        self.btn_exp_json = Button(
            parent=camera.ui,
            text="Save JSON",
            scale=(btn_w, btn_h),
            position=(start_x, -0.38),
            color=self.btn_idle_color,
            highlight_color=self.btn_highlight,
            on_click=self._on_save_json,
        )
        self.btn_exp_json.text_entity.scale = 0.75
        self.ui_elements.append(self.btn_exp_json)

        # Export CSV
        self.btn_exp_csv = Button(
            parent=camera.ui,
            text="Save CSV",
            scale=(btn_w, btn_h),
            position=(start_x + 0.14, -0.38),
            color=self.btn_idle_color,
            highlight_color=self.btn_highlight,
            on_click=self._on_save_csv,
        )
        self.btn_exp_csv.text_entity.scale = 0.75
        self.ui_elements.append(self.btn_exp_csv)

        # Load & Playback
        self.btn_load_play = Button(
            parent=camera.ui,
            text="Load & Replay",
            scale=(btn_w * 2.05, 0.042),
            position=(start_x + 0.07, -0.445),
            color=color.rgb(0.14, 0.30, 0.52),
            highlight_color=color.rgb(0.18, 0.38, 0.68),
            on_click=self._on_load_and_replay,
        )
        self.btn_load_play.text_entity.scale = 0.75
        self.ui_elements.append(self.btn_load_play)

    # --- Click Handlers ---

    def _on_launch_click(self) -> None:
        self.manager.launch_all()
        self.show_message("Dispatched: LAUNCH ALL -> Ascending to altitude")

    def _on_land_click(self) -> None:
        self.manager.land_all()
        self.show_message("Dispatched: LAND ALL -> Returning to home coordinates")

    def _on_reset_click(self) -> None:
        self.manager.reset_simulation()
        self.show_message("Dispatched: RESET -> Fleet returned to ground positions")

    def _on_pause_click(self) -> None:
        is_paused = self.manager.toggle_pause()
        self.btn_pause.text = "Resume" if is_paused else "Pause"
        self.show_message(f"Simulation {'PAUSED' if is_paused else 'RESUMED'}")

    def _on_formation_click(self, name: str) -> None:
        success = self.manager.change_formation(name)
        if success:
            if self.manager.pending_transition_warnings:
                warn_count = len(self.manager.pending_transition_warnings)
                self.show_message(f"Formation -> {name} | PREDICTED: {warn_count} proximity warnings!")
            else:
                self.show_message(f"Formation -> {name} (Safe trajectory planned)")

    def _on_spacing_inc(self) -> None:
        self.manager.spacing = round(self.manager.spacing + 0.5, 1)
        self.lbl_spacing.text = f"Spacing: {self.manager.spacing:.1f}m"
        # Re-apply current formation if airborne
        if self.manager.current_formation in AVAILABLE_FORMATIONS:
            self.manager.change_formation(self.manager.current_formation)
        self.show_message(f"Spacing increased to {self.manager.spacing:.1f}m")

    def _on_spacing_dec(self) -> None:
        self.manager.spacing = max(1.5, round(self.manager.spacing - 0.5, 1))
        self.lbl_spacing.text = f"Spacing: {self.manager.spacing:.1f}m"
        if self.manager.current_formation in AVAILABLE_FORMATIONS:
            self.manager.change_formation(self.manager.current_formation)
        self.show_message(f"Spacing decreased to {self.manager.spacing:.1f}m")

    def _on_speed_inc(self) -> None:
        self.manager.speed = round(self.manager.speed + 1.0, 1)
        self.lbl_speed.text = f"Speed: {self.manager.speed:.1f}m/s"
        self.show_message(f"Flight speed set to {self.manager.speed:.1f} m/s")

    def _on_speed_dec(self) -> None:
        self.manager.speed = max(1.0, round(self.manager.speed - 1.0, 1))
        self.lbl_speed.text = f"Speed: {self.manager.speed:.1f}m/s"
        self.show_message(f"Flight speed set to {self.manager.speed:.1f} m/s")

    def _on_save_json(self) -> None:
        path = os.path.join("data", "formations", f"trajectory_{int(time.time())}.json")
        if self.manager.export_trajectory_data(path, "json"):
            self.show_message(f"Exported JSON: {path}")

    def _on_save_csv(self) -> None:
        path = os.path.join("data", "formations", f"trajectory_{int(time.time())}.csv")
        if self.manager.export_trajectory_data(path, "csv"):
            self.show_message(f"Exported CSV: {path}")

    def _on_load_and_replay(self) -> None:
        """Find latest exported trajectory file in data/formations and play it."""
        folder = os.path.join("data", "formations")
        if not os.path.exists(folder):
            self.show_message("No saved trajectories found in data/formations")
            return

        files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.endswith(".json") or f.endswith(".csv")
        ]
        if not files:
            # Auto-generate a sample trajectory to demonstrate playback!
            sample_path = os.path.join(folder, "sample_helix_flight.json")
            self.manager.export_trajectory_data(sample_path, "json")
            files.append(sample_path)

        latest = max(files, key=os.path.getmtime)
        try:
            keyframes = self.manager.import_trajectory_data(latest)
            self.manager.start_playback(keyframes)
            self.show_message(f"Replaying: {os.path.basename(latest)} ({len(keyframes)} frames)")
        except Exception as ex:
            self.show_message(f"Error loading playback: {ex}")

    def update(self) -> None:
        """Continuous HUD update reflecting fleet state, counts, and proximity status."""
        mgr = self.manager

        # Update Fleet Summary Header
        adapter_name = "MAVLink/SITL" if mgr.adapter_type == "mavlink" else "LocalSim"
        status_mode = "PAUSED" if mgr.is_paused else ("PLAYBACK" if mgr.is_playback_active else "RUNNING")

        self.fleet_text.text = (
            f"FLEET: {mgr.total_drones} Drones | Active: {mgr.active_drones} | "
            f"Connected: {mgr.connected_drones} | Formation: {mgr.current_formation} | "
            f"Status: {status_mode} [{adapter_name}]"
        )

        # Update Collision & Safety Report
        rep = mgr.collision_report
        if rep.has_critical:
            pair = rep.critical_pairs[0]
            self.safety_text.text = f"[CRITICAL COLLISION] Drone {pair[0]:02d} <-> Drone {pair[1]:02d} at {pair[2]:.2f}m!"
            self.safety_text.color = self.accent_red
        elif rep.has_warnings:
            pair = rep.warning_pairs[0]
            self.safety_text.text = f"[PROXIMITY WARNING] Drone {pair[0]:02d} <-> Drone {pair[1]:02d} at {pair[2]:.2f}m (Threshold: 2.2m)"
            self.safety_text.color = self.accent_amber
        else:
            min_d_str = f"{rep.min_observed_distance:.2f}m" if rep.min_observed_distance != float("inf") else "Safe"
            self.safety_text.text = f"PROXIMITY: CLEAR | Min Separation: {min_d_str}"
            self.safety_text.color = self.accent_green

        # Notification timeout
        if self._notification_expire > 0 and time.time() > self._notification_expire:
            self._notification_expire = 0.0
            self.notification_text.text = "[Space] Pause | [1-4] Preset Views | [F] Focus | [RMB Drag] Orbit"

    def destroy(self) -> None:
        """Destroy UI entities."""
        for e in self.ui_elements:
            try:
                destroy(e)
            except Exception:
                pass
        self.ui_elements.clear()

