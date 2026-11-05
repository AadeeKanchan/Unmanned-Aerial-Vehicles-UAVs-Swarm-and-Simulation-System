"""Ursina 3D simulation environment, ground grid, and 3D reference axes."""

from ursina import (
    Entity,
    Grid,
    Vec3,
    color,
    destroy,
    window,
)

from uav_swarm.config import (
    BG_COLOR,
    GRID_COLOR,
    GRID_SIZE,
    GRID_SPACING,
)


class SimulationEnvironment:
    """Manages 3D scene lighting, ground reference grid, and RGB orientation axes."""

    def __init__(self) -> None:
        # 1. Dark, high-contrast viewport background (0.0 to 1.0 range)
        window.color = color.rgb(BG_COLOR[0], BG_COLOR[1], BG_COLOR[2])

        self.entities = []

        # 2. Ground Reference Plane & Grid (X-Z horizontal ground plane)
        # Ursina default Grid is in XY plane, rotate 90 deg around X to lay flat on XZ plane
        grid_scale = GRID_SIZE * GRID_SPACING
        self.ground_grid = Entity(
            model=Grid(GRID_SIZE, GRID_SIZE),
            rotation_x=90,
            position=(0, -0.01, 0),
            scale=grid_scale,
            color=color.rgba(GRID_COLOR[0], GRID_COLOR[1], GRID_COLOR[2], GRID_COLOR[3]),
        )
        self.entities.append(self.ground_grid)

        # Subtle dark ground baseplate
        self.ground_plate = Entity(
            model="plane",
            position=(0, -0.02, 0),
            scale=(grid_scale, 1, grid_scale),
            color=color.rgb(0.05, 0.06, 0.08),
        )
        self.entities.append(self.ground_plate)

        # 3. 3D Reference Coordinate Axes (X: Red, Y/Up: Green, Z: Blue)
        axis_length = 8.0
        axis_thickness = 0.08

        # X Axis (+X: Red / Lateral)
        self.x_axis = Entity(
            model="cube",
            position=(axis_length / 2.0, 0.05, 0),
            scale=(axis_length, axis_thickness, axis_thickness),
            color=color.rgb(0.90, 0.25, 0.25),
        )
        self.entities.append(self.x_axis)

        # Y Axis (+Y: Green / Vertical Altitude)
        self.y_axis = Entity(
            model="cube",
            position=(0, axis_length / 2.0, 0),
            scale=(axis_thickness, axis_length, axis_thickness),
            color=color.rgb(0.20, 0.82, 0.35),
        )
        self.entities.append(self.y_axis)

        # Z Axis (+Z: Blue / Longitudinal Forward)
        self.z_axis = Entity(
            model="cube",
            position=(0, 0.05, axis_length / 2.0),
            scale=(axis_thickness, axis_thickness, axis_length),
            color=color.rgb(0.24, 0.52, 0.95),
        )
        self.entities.append(self.z_axis)

        # Origin center circle
        self.origin_marker = Entity(
            model="circle",
            rotation_x=90,
            position=(0, 0.01, 0),
            scale=(1.2, 1.2, 1.2),
            color=color.rgba(1.0, 1.0, 1.0, 0.32),
        )
        self.entities.append(self.origin_marker)

    def destroy(self) -> None:
        """Clean up environment entities."""
        for e in self.entities:
            try:
                destroy(e)
            except Exception:
                pass
        self.entities.clear()

