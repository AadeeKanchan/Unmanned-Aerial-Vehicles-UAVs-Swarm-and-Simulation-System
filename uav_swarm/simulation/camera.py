"""Interactive camera navigation supporting orbit, pan, zoom, and preset viewing angles."""

import math
from ursina import (
    Vec3,
    camera,
    clamp,
    destroy,
    held_keys,
    mouse,
)


class SwarmCameraController:
    """Orbit, pan, and zoom camera controller with keyboard presets."""

    def __init__(
        self,
        target_center: Vec3 = Vec3(0, 4.0, 0),
        distance: float = 30.0,
        pitch: float = 28.0,
        yaw: float = 35.0,
    ) -> None:
        self.target = Vec3(target_center)
        self.distance = distance
        self.pitch = pitch
        self.yaw = yaw

        # Limits
        self.min_distance = 4.0
        self.max_distance = 120.0
        self.min_pitch = -85.0
        self.max_pitch = 89.0

        # Sensitivity settings
        self.orbit_sensitivity = 40.0
        self.zoom_sensitivity = 3.5
        self.pan_sensitivity = 0.8
        self.key_orbit_speed = 60.0

        self._last_mouse_pos = (mouse.x, mouse.y)
        self._update_camera_transform()

    def set_preset_view(self, view_id: int) -> None:
        """Switch to standard preset viewing angles.

        1: Oblique 3D Perspective
        2: Top-Down Aerial View
        3: Front Facing View
        4: Side Lateral View
        """
        if view_id == 1:
            self.yaw = 35.0
            self.pitch = 28.0
            self.distance = 32.0
        elif view_id == 2:
            self.yaw = 0.0
            self.pitch = 88.0
            self.distance = 38.0
        elif view_id == 3:
            self.yaw = 0.0
            self.pitch = 5.0
            self.distance = 30.0
        elif view_id == 4:
            self.yaw = 90.0
            self.pitch = 5.0
            self.distance = 30.0

        self._update_camera_transform()

    def focus_on(self, point: Vec3) -> None:
        """Re-center camera pivot target."""
        self.target = Vec3(point)
        self._update_camera_transform()

    def handle_input(self, key: str) -> None:
        """Handle discrete hotkeys for viewpoints and zoom wheel."""
        if key == "1":
            self.set_preset_view(1)
        elif key == "2":
            self.set_preset_view(2)
        elif key == "3":
            self.set_preset_view(3)
        elif key == "4":
            self.set_preset_view(4)
        elif key in ("f", "f_up"):
            self.focus_on(Vec3(0, 4.0, 0))
        elif key == "scroll up":
            self.distance = clamp(
                self.distance - self.zoom_sensitivity,
                self.min_distance,
                self.max_distance,
            )
            self._update_camera_transform()
        elif key == "scroll down":
            self.distance = clamp(
                self.distance + self.zoom_sensitivity,
                self.min_distance,
                self.max_distance,
            )
            self._update_camera_transform()

    def update(self, dt: float) -> None:
        """Continuous frame update for mouse drag orbit, panning, and keyboard navigation."""
        current_mx = mouse.x
        current_my = mouse.y
        dx = current_mx - self._last_mouse_pos[0]
        dy = current_my - self._last_mouse_pos[1]
        self._last_mouse_pos = (current_mx, current_my)

        changed = False

        # Orbit with Right Mouse Button
        if mouse.right and not (held_keys["shift"] or mouse.middle):
            self.yaw += dx * self.orbit_sensitivity * 10.0
            self.pitch = clamp(
                self.pitch - dy * self.orbit_sensitivity * 10.0,
                self.min_pitch,
                self.max_pitch,
            )
            changed = True

        # Pan with Middle Mouse Button or Shift + Right Mouse Button
        elif mouse.middle or (mouse.right and held_keys["shift"]):
            rad_yaw = math.radians(self.yaw)
            # Right and Up camera vectors
            right_dir = Vec3(math.cos(rad_yaw), 0, -math.sin(rad_yaw))
            up_dir = Vec3(0, 1, 0)

            pan_speed = self.pan_sensitivity * (self.distance * 0.5)
            self.target -= right_dir * (dx * pan_speed)
            self.target -= up_dir * (dy * pan_speed)
            changed = True

        # Keyboard arrow navigation
        if held_keys["left arrow"]:
            self.yaw -= self.key_orbit_speed * dt
            changed = True
        if held_keys["right arrow"]:
            self.yaw += self.key_orbit_speed * dt
            changed = True
        if held_keys["up arrow"]:
            self.pitch = clamp(
                self.pitch + self.key_orbit_speed * dt,
                self.min_pitch,
                self.max_pitch,
            )
            changed = True
        if held_keys["down arrow"]:
            self.pitch = clamp(
                self.pitch - self.key_orbit_speed * dt,
                self.min_pitch,
                self.max_pitch,
            )
            changed = True

        if changed:
            self._update_camera_transform()

    def _update_camera_transform(self) -> None:
        """Compute spherical orbit position relative to target center."""
        rad_pitch = math.radians(self.pitch)
        rad_yaw = math.radians(self.yaw)

        # Spherical coordinates
        cx = self.target.x + self.distance * math.cos(rad_pitch) * math.sin(rad_yaw)
        cy = self.target.y + self.distance * math.sin(rad_pitch)
        cz = self.target.z - self.distance * math.cos(rad_pitch) * math.cos(rad_yaw)

        camera.position = Vec3(cx, cy, cz)
        camera.look_at(self.target)

