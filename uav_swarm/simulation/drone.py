"""3D Visual Entity representation of a virtual quadcopter UAV."""

from typing import Tuple
from ursina import (
    Entity,
    Text,
    Vec3,
    color,
    destroy,
)

from uav_swarm.config import DRONE_SCALE, DroneState
from uav_swarm.swarm.manager import DroneRecord


class DroneVisualEntity:
    """3D composite Ursina entity representing an individual quadcopter UAV in the swarm."""

    def __init__(self, record: DroneRecord) -> None:
        self.record = record
        self.drone_id = record.drone_id

        # Root entity for position and orientation
        self.root = Entity(
            position=Vec3(
                float(record.current_pos[0]),
                float(record.current_pos[1]),
                float(record.current_pos[2]),
            ),
            scale=DRONE_SCALE,
        )

        # 1. Central fuselage body
        self.body = Entity(
            parent=self.root,
            model="cube",
            scale=(0.8, 0.22, 0.8),
            color=color.rgb(0.14, 0.16, 0.19),
        )

        # Central status beacon LED (changes color according to state & warnings)
        self.beacon = Entity(
            parent=self.root,
            model="sphere",
            position=(0, 0.16, 0),
            scale=(0.42, 0.35, 0.42),
            color=color.rgb(
                float(record.color_rgb[0]),
                float(record.color_rgb[1]),
                float(record.color_rgb[2]),
            ),
        )

        # 2. Diagonal quadcopter cross arms (X-configuration)
        arm_length = 1.8
        arm_thickness = 0.08
        self.arm1 = Entity(
            parent=self.root,
            model="cube",
            rotation_y=45,
            scale=(arm_length, arm_thickness, arm_thickness),
            color=color.rgb(0.08, 0.09, 0.11),
        )
        self.arm2 = Entity(
            parent=self.root,
            model="cube",
            rotation_y=-45,
            scale=(arm_length, arm_thickness, arm_thickness),
            color=color.rgb(0.08, 0.09, 0.11),
        )

        # 3. Four motor hubs and spinning rotor propellers
        self.rotors = []
        arm_rad = (arm_length / 2.0) * 0.7071  # 45-degree component
        motor_offsets = [
            (arm_rad, 0.08, arm_rad),
            (-arm_rad, 0.08, arm_rad),
            (arm_rad, 0.08, -arm_rad),
            (-arm_rad, 0.08, -arm_rad),
        ]

        for offset in motor_offsets:
            # Motor mount
            Entity(
                parent=self.root,
                model="cube",
                position=offset,
                scale=(0.18, 0.12, 0.18),
                color=color.rgb(0.06, 0.06, 0.07),
            )
            # Propeller blade
            prop = Entity(
                parent=self.root,
                model="cube",
                position=(offset[0], offset[1] + 0.06, offset[2]),
                scale=(0.75, 0.02, 0.08),
                color=color.rgba(0.90, 0.94, 1.0, 0.70),
            )
            self.rotors.append(prop)

        # 4. Floating Identification Label (Billboard Text)
        self.label = Text(
            text=f"D{self.drone_id:02d}",
            parent=self.root,
            position=(0, 0.75, 0),
            scale=8.0,
            origin=(0, 0),
            billboard=True,
            color=color.white,
        )

        # 5. Altitude ground reference drop-line
        self.drop_line = Entity(
            model="cube",
            scale=(0.04, 1, 0.04),
            color=color.rgba(0.40, 0.60, 0.88, 0.28),
        )

    def update_visuals(self, dt: float) -> None:
        """Update 3D world position, rotor rotation, and LED state colors."""
        pos = self.record.current_pos
        self.root.position = Vec3(float(pos[0]), float(pos[1]), float(pos[2]))

        # Update LED beacon color based on logical record
        r, g, b = self.record.color_rgb
        self.beacon.color = color.rgb(float(r), float(g), float(b))

        # Rotate propellers if drone is armed or active
        is_active = self.record.state not in (DroneState.IDLE, DroneState.LANDED)
        spin_speed = 1800.0 if is_active else 0.0
        if spin_speed > 0.0:
            spin_delta = spin_speed * dt
            for idx, rtr in enumerate(self.rotors):
                # Counter-rotating pairs for visual realism
                direction = 1 if idx % 2 == 0 else -1
                rtr.rotation_y = (rtr.rotation_y + direction * spin_delta) % 360

        # Update vertical altitude drop-line to ground
        current_y = max(0.01, float(pos[1]))
        self.drop_line.scale_y = current_y
        self.drop_line.position = Vec3(float(pos[0]), current_y / 2.0, float(pos[2]))
        # Hide drop line when resting on ground
        self.drop_line.enabled = current_y > 0.15

        # Update label text and color
        if self.record.has_critical:
            self.label.color = color.rgb(1.0, 0.24, 0.24)
            self.label.text = f"D{self.drone_id:02d} [COLLISION]"
        elif self.record.has_warning:
            self.label.color = color.rgb(1.0, 0.70, 0.15)
            self.label.text = f"D{self.drone_id:02d} [WARN]"
        else:
            self.label.color = color.white
            self.label.text = f"D{self.drone_id:02d}"

    def destroy(self) -> None:
        """Clean up 3D visual entities."""
        try:
            destroy(self.drop_line)
            destroy(self.label)
            destroy(self.root)
        except Exception:
            pass
