"""Mathematical 3D formation generation for UAV swarms.

Pure NumPy calculations independent of the rendering engine.
Supported formations:
1. Line
2. V Formation
3. Circle
4. Square
5. Triangle
6. Helix (3D)
"""

from typing import List, Tuple
import numpy as np


AVAILABLE_FORMATIONS: List[str] = [
    "Line",
    "V Formation",
    "Circle",
    "Square",
    "Triangle",
    "Helix",
]


def generate_line(
    count: int,
    spacing: float = 3.0,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    altitude: float = 5.0,
) -> np.ndarray:
    """Generate a horizontal 1D line formation along the X axis centered at center.

    Returns:
        np.ndarray: shape (count, 3) with [X, Y, Z] coordinates.
    """
    if count <= 0:
        return np.empty((0, 3), dtype=np.float64)

    cx, _, cz = center
    indices = np.arange(count, dtype=np.float64)
    offsets = (indices - (count - 1) / 2.0) * spacing

    x = cx + offsets
    y = np.full(count, altitude, dtype=np.float64)
    z = np.full(count, cz, dtype=np.float64)

    return np.column_stack((x, y, z))


def generate_v_formation(
    count: int,
    spacing: float = 3.0,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    altitude: float = 5.0,
    sweep_angle_deg: float = 35.0,
) -> np.ndarray:
    """Generate a symmetric V-shape (chevron) formation with apex pointing forward (+Z).

    Returns:
        np.ndarray: shape (count, 3) with [X, Y, Z] coordinates.
    """
    if count <= 0:
        return np.empty((0, 3), dtype=np.float64)

    cx, _, cz = center
    rad = np.radians(sweep_angle_deg)
    dx = spacing * np.cos(rad)
    dz = spacing * np.sin(rad)

    coords = np.zeros((count, 3), dtype=np.float64)

    # Lead drone (index 0)
    coords[0] = [0.0, altitude, 0.0]

    for i in range(1, count):
        wing_rank = (i + 1) // 2
        side = -1.0 if (i % 2 == 1) else 1.0  # left (-X) or right (+X)
        coords[i] = [side * wing_rank * dx, altitude, -wing_rank * dz]

    # Center coordinates around (cx, cz)
    mean_x = np.mean(coords[:, 0])
    mean_z = np.mean(coords[:, 2])
    coords[:, 0] += (cx - mean_x)
    coords[:, 2] += (cz - mean_z)

    return coords


def generate_circle(
    count: int,
    spacing: float = 3.0,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    altitude: float = 5.0,
) -> np.ndarray:
    """Generate a horizontal circular formation in the X-Z plane.

    Returns:
        np.ndarray: shape (count, 3) with [X, Y, Z] coordinates.
    """
    if count <= 0:
        return np.empty((0, 3), dtype=np.float64)
    if count == 1:
        return np.array([[center[0], altitude, center[2]]], dtype=np.float64)

    # Radius calculated to maintain approximately equal arc-length spacing
    circumference = count * spacing
    radius = max(spacing, circumference / (2.0 * np.pi))

    angles = np.linspace(0, 2.0 * np.pi, count, endpoint=False)
    cx, _, cz = center

    x = cx + radius * np.cos(angles)
    y = np.full(count, altitude, dtype=np.float64)
    z = cz + radius * np.sin(angles)

    return np.column_stack((x, y, z))


def generate_square(
    count: int,
    spacing: float = 3.0,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    altitude: float = 5.0,
) -> np.ndarray:
    """Generate a perimeter square formation in the X-Z plane.

    Returns:
        np.ndarray: shape (count, 3) with [X, Y, Z] coordinates.
    """
    if count <= 0:
        return np.empty((0, 3), dtype=np.float64)
    if count == 1:
        return np.array([[center[0], altitude, center[2]]], dtype=np.float64)

    # Perimeter length to accommodate drones with given spacing
    perimeter = count * spacing
    side = max(spacing * 2.0, perimeter / 4.0)
    half = side / 2.0

    cx, _, cz = center
    coords = np.zeros((count, 3), dtype=np.float64)

    for i in range(count):
        # Parametric progression s in [0, 4) around 4 edges
        s = 4.0 * (i / count)
        edge = int(s)
        t = s - edge  # progress along edge [0, 1)

        if edge == 0:  # Bottom edge: -X -> +X at -Z
            px = -half + t * side
            pz = -half
        elif edge == 1:  # Right edge: -Z -> +Z at +X
            px = half
            pz = -half + t * side
        elif edge == 2:  # Top edge: +X -> -X at +Z
            px = half - t * side
            pz = half
        else:  # Left edge: +Z -> -Z at -X
            px = -half
            pz = half - t * side

        coords[i] = [cx + px, altitude, cz + pz]

    return coords


def generate_triangle(
    count: int,
    spacing: float = 3.0,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    altitude: float = 5.0,
) -> np.ndarray:
    """Generate an equilateral triangle / delta formation pointing forward (+Z).

    Returns:
        np.ndarray: shape (count, 3) with [X, Y, Z] coordinates.
    """
    if count <= 0:
        return np.empty((0, 3), dtype=np.float64)
    if count == 1:
        return np.array([[center[0], altitude, center[2]]], dtype=np.float64)

    # Place drones in structured triangular rows (1 in row 0, 2 in row 1, etc.)
    row = 0
    col = 0
    row_height = spacing * (np.sqrt(3.0) / 2.0)
    raw_coords = []

    for _ in range(count):
        # Center of row is (row / 2)
        x_offset = (col - (row / 2.0)) * spacing
        z_offset = -row * row_height
        raw_coords.append([x_offset, altitude, z_offset])

        col += 1
        if col > row:
            row += 1
            col = 0

    coords = np.array(raw_coords, dtype=np.float64)

    # Center triangle around (cx, cz)
    mean_x = np.mean(coords[:, 0])
    mean_z = np.mean(coords[:, 2])
    coords[:, 0] += (center[0] - mean_x)
    coords[:, 2] += (center[2] - mean_z)

    return coords


def generate_helix(
    count: int,
    spacing: float = 3.0,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    altitude: float = 5.0,
    vertical_span: float = 8.0,
    turns: float = 2.0,
) -> np.ndarray:
    """Generate a 3D cylindrical helix spiral formation with vertical dispersion.

    Returns:
        np.ndarray: shape (count, 3) with [X, Y, Z] coordinates.
    """
    if count <= 0:
        return np.empty((0, 3), dtype=np.float64)
    if count == 1:
        return np.array([[center[0], altitude, center[2]]], dtype=np.float64)

    radius = max(spacing * 1.2, (count * spacing) / (2.0 * np.pi * turns * 1.5))
    cx, _, cz = center

    angles = np.linspace(0, 2.0 * np.pi * turns, count, endpoint=False)
    y_min = max(1.5, altitude - vertical_span / 2.0)
    y_vals = np.linspace(y_min, y_min + vertical_span, count)

    x = cx + radius * np.cos(angles)
    y = y_vals
    z = cz + radius * np.sin(angles)

    return np.column_stack((x, y, z))


def generate_formation(
    formation_type: str,
    count: int,
    spacing: float = 3.0,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    altitude: float = 5.0,
) -> np.ndarray:
    """Factory function dispatching to specific formation generator by name."""
    fmt = formation_type.strip().lower()
    if fmt == "line":
        return generate_line(count, spacing, center, altitude)
    elif fmt in ("v formation", "v", "v-shape", "v_formation"):
        return generate_v_formation(count, spacing, center, altitude)
    elif fmt == "circle":
        return generate_circle(count, spacing, center, altitude)
    elif fmt == "square":
        return generate_square(count, spacing, center, altitude)
    elif fmt in ("triangle", "delta"):
        return generate_triangle(count, spacing, center, altitude)
    elif fmt == "helix":
        return generate_helix(count, spacing, center, altitude)
    else:
        raise ValueError(
            f"Unknown formation '{formation_type}'. Available: {AVAILABLE_FORMATIONS}"
        )

