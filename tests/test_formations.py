"""Unit tests for mathematical 3D formation generation."""

import numpy as np
import pytest

from uav_swarm.swarm.formations import (
    AVAILABLE_FORMATIONS,
    generate_circle,
    generate_formation,
    generate_helix,
    generate_line,
    generate_square,
    generate_triangle,
    generate_v_formation,
)


@pytest.mark.parametrize("fmt_name", AVAILABLE_FORMATIONS)
def test_all_formations_output_shape(fmt_name: str) -> None:
    count = 16
    coords = generate_formation(fmt_name, count=count, spacing=3.0, altitude=5.0)
    assert isinstance(coords, np.ndarray)
    assert coords.shape == (count, 3)
    assert not np.isnan(coords).any()
    assert not np.isinf(coords).any()


def test_line_formation_altitude_and_spacing() -> None:
    count = 5
    spacing = 4.0
    alt = 6.5
    coords = generate_line(count=count, spacing=spacing, center=(0, 0, 0), altitude=alt)

    # Verify uniform altitude
    assert np.allclose(coords[:, 1], alt)
    # Verify Z is constant along center
    assert np.allclose(coords[:, 2], 0.0)
    # Verify distance between consecutive drones equals spacing
    diffs = np.diff(coords[:, 0])
    assert np.allclose(diffs, spacing)


def test_v_formation_symmetry() -> None:
    count = 7
    coords = generate_v_formation(count=count, spacing=3.0, center=(0, 0, 0), altitude=5.0)
    assert coords.shape == (7, 3)
    # Check that wings spread laterally on both positive and negative X
    assert np.any(coords[:, 0] < 0.0)
    assert np.any(coords[:, 0] > 0.0)


def test_circle_formation_equidistant() -> None:
    count = 12
    coords = generate_circle(count=count, spacing=3.0, center=(10.0, 0.0, -5.0), altitude=8.0)
    assert coords.shape == (12, 3)
    assert np.allclose(coords[:, 1], 8.0)

    # Distances to center (10, -5) in X-Z plane should all be equal to radius
    radii = np.hypot(coords[:, 0] - 10.0, coords[:, 2] - (-5.0))
    assert np.allclose(radii, radii[0], atol=1e-5)


def test_square_formation() -> None:
    count = 16
    coords = generate_square(count=count, spacing=2.5, center=(0, 0, 0), altitude=4.0)
    assert coords.shape == (16, 3)
    assert np.allclose(coords[:, 1], 4.0)


def test_triangle_formation() -> None:
    count = 10
    coords = generate_triangle(count=count, spacing=3.0, center=(0, 0, 0), altitude=5.0)
    assert coords.shape == (10, 3)
    assert np.allclose(coords[:, 1], 5.0)


def test_helix_formation_3d_dispersion() -> None:
    count = 16
    coords = generate_helix(count=count, spacing=3.0, altitude=6.0, vertical_span=10.0)
    assert coords.shape == (16, 3)
    # Y coordinates should vary continuously across the vertical span
    assert np.min(coords[:, 1]) < np.max(coords[:, 1])
    diff_y = np.diff(coords[:, 1])
    assert np.all(diff_y >= 0.0)


def test_single_drone_and_empty() -> None:
    assert generate_line(0).shape == (0, 3)
    c1 = generate_circle(1, spacing=3.0, center=(2.0, 0.0, 3.0), altitude=5.0)
    assert c1.shape == (1, 3)
    assert np.allclose(c1[0], [2.0, 5.0, 3.0])


def test_unknown_formation_raises() -> None:
    with pytest.raises(ValueError):
        generate_formation("Octagon", count=10)

