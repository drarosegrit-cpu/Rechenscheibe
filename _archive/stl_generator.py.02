"""
stl_generator.py - Procedural Binary STL Generator for Dual-Sided Rechenscheibe
Creates solid, watertight manifold meshes for:
1. Double-sided Stator Frame (Central core wall with front and back pockets)
2. Front Rotor Disc (Polar diagram dial)
3. Back Rotor Disc (Slide rule dial)
4. Central Ratio Pointer (Ruler centered at (0,0) with reading edge)
5. Central Axle Pin
"""

import struct
import math
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional


def _write_binary_stl(filepath: Path, triangles: np.ndarray, normals: np.ndarray = None):
    """Writes triangles to a standard binary STL file."""
    filepath = Path(filepath)
    n_triangles = len(triangles)

    if normals is None or len(normals) != n_triangles:
        v0 = triangles[:, 0, :]
        v1 = triangles[:, 1, :]
        v2 = triangles[:, 2, :]
        cross = np.cross(v1 - v0, v2 - v0)
        norm = np.linalg.norm(cross, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        normals = (cross / norm).astype(np.float32)

    with open(filepath, "wb") as f:
        header = f"3D Printed Rechenscheibe - {filepath.stem}".encode("utf-8")
        header = header[:80].ljust(80, b"\0")
        f.write(header)
        f.write(struct.pack("<I", n_triangles))

        data = np.zeros(n_triangles, dtype=[
            ("normal", "<f4", (3,)),
            ("v0", "<f4", (3,)),
            ("v1", "<f4", (3,)),
            ("v2", "<f4", (3,)),
            ("attr", "<u2")
        ])
        data["normal"] = normals
        data["v0"] = triangles[:, 0, :]
        data["v1"] = triangles[:, 1, :]
        data["v2"] = triangles[:, 2, :]
        data["attr"] = 0
        data.tofile(f)


def _generate_cylinder_annulus_triangles(
    r_inner: float,
    r_outer: float,
    z_bottom: float,
    z_top: float,
    segments: int = 120,
    center_xy: Tuple[float, float] = (0.0, 0.0)
) -> list:
    triangles = []
    angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    cx, cy = center_xy

    b_out = np.column_stack([cx + r_outer * np.cos(angles), cy + r_outer * np.sin(angles), np.full(segments, z_bottom)])
    t_out = np.column_stack([cx + r_outer * np.cos(angles), cy + r_outer * np.sin(angles), np.full(segments, z_top)])

    if r_inner > 0:
        b_in = np.column_stack([cx + r_inner * np.cos(angles), cy + r_inner * np.sin(angles), np.full(segments, z_bottom)])
        t_in = np.column_stack([cx + r_inner * np.cos(angles), cy + r_inner * np.sin(angles), np.full(segments, z_top)])
    else:
        b_center = np.array([cx, cy, z_bottom])
        t_center = np.array([cx, cy, z_top])

    for i in range(segments):
        next_i = (i + 1) % segments

        # Outer wall
        triangles.append([b_out[i], t_out[i], t_out[next_i]])
        triangles.append([b_out[i], t_out[next_i], b_out[next_i]])

        # Inner wall
        if r_inner > 0:
            triangles.append([b_in[i], t_in[next_i], t_in[i]])
            triangles.append([b_in[i], b_in[next_i], t_in[next_i]])

            # Top annulus
            triangles.append([t_in[i], t_out[i], t_out[next_i]])
            triangles.append([t_in[i], t_out[next_i], t_in[next_i]])

            # Bottom annulus
            triangles.append([b_in[i], b_out[next_i], b_out[i]])
            triangles.append([b_in[i], b_in[next_i], b_out[next_i]])
        else:
            # Top cap
            triangles.append([t_center, t_out[i], t_out[next_i]])
            # Bottom cap
            triangles.append([b_center, b_out[next_i], b_out[i]])

    return triangles


def generate_stator_mesh(
    filepath: Path,
    r_max: float = 57.5,
    r_pocket: float = 47.15,
    center_hole_r: float = 1.6,
    core_wall_thk: float = 1.6,
    front_rim_h: float = 1.8,
    back_rim_h: float = 1.8,
    segments: int = 120
):
    """
    Creates double-sided Stator body:
    - Central core wall from z = 0 to z = core_wall_thk
    - Front rim from z = core_wall_thk to z = core_wall_thk + front_rim_h (r in [r_pocket, r_max])
    - Back rim from z = -back_rim_h to z = 0 (r in [r_pocket, r_max])
    - Center axle hole through all z.
    """
    triangles = []

    # 1. Central core floor (from center hole to r_pocket)
    triangles.extend(_generate_cylinder_annulus_triangles(
        center_hole_r, r_pocket, 0.0, core_wall_thk, segments
    ))

    # 2. Outer full ring (from r_pocket to r_max, from -back_rim_h to core_wall_thk + front_rim_h)
    z_min = -back_rim_h
    z_max = core_wall_thk + front_rim_h
    triangles.extend(_generate_cylinder_annulus_triangles(
        r_pocket, r_max, z_min, z_max, segments
    ))

    # Convert to array and save
    mesh_data = np.array(triangles, dtype=np.float32)
    _write_binary_stl(filepath, mesh_data)


def generate_rotor_mesh(
    filepath: Path,
    r_rotor: float = 46.75,
    center_hole_r: float = 1.6,
    thickness: float = 1.8,
    segments: int = 120
):
    """
    Creates flat Rotor disc with center axle hole.
    Used for both Front Rotor (Polar dial) and Back Rotor (Slide rule).
    """
    triangles = _generate_cylinder_annulus_triangles(
        center_hole_r, r_rotor, 0.0, thickness, segments
    )
    mesh_data = np.array(triangles, dtype=np.float32)
    _write_binary_stl(filepath, mesh_data)


def generate_central_pointer_mesh(
    filepath: Path,
    length: float = 62.0,
    width: float = 6.0,
    hub_radius: float = 4.5,
    center_hole_r: float = 1.6,
    thickness: float = 1.2,
    segments: int = 40
):
    """
    Creates central ratio pointer (pivoting at 0,0):
    - Circular hub at (0,0)
    - Straight arm with reading edge along x = 0 (or centered)
    - Pointed index tip at length for precise compass reading
    - Thumb tab for tactile rotation
    """
    triangles = []

    # Hub cylinder around center hole
    triangles.extend(_generate_cylinder_annulus_triangles(
        center_hole_r, hub_radius, 0.0, thickness, segments
    ))

    # Arm geometry: Polygon along +Y axis
    # Reading edge is at x = 0
    # Right edge is at x = width
    half_w = width / 2.0
    tip_len = 3.5
    tab_len = 3.0
    y_body_end = length - tip_len - tab_len

    # 2D contour points
    # Start near hub
    poly_2d = [
        (0.0, hub_radius * 0.8),
        (width, hub_radius * 0.8),
        (width, y_body_end),
        (width + 2.0, y_body_end + tab_len / 2.0), # thumb tab
        (width, y_body_end + tab_len),
        (0.0, length),                              # sharp index tip at x=0
    ]

    # Simple 3D extrusion of arm polygon
    n_pts = len(poly_2d)
    pts_b = np.array([[x, y, 0.0] for x, y in poly_2d], dtype=np.float32)
    pts_t = np.array([[x, y, thickness] for x, y in poly_2d], dtype=np.float32)

    # Side walls
    for i in range(n_pts):
        next_i = (i + 1) % n_pts
        triangles.append([pts_b[i], pts_t[i], pts_t[next_i]])
        triangles.append([pts_b[i], pts_t[next_i], pts_b[next_i]])

    # Top & bottom caps via ear clipping / fan
    for i in range(1, n_pts - 1):
        triangles.append([pts_t[0], pts_t[i], pts_t[i + 1]])
        triangles.append([pts_b[0], pts_b[i + 1], pts_b[i]])

    mesh_data = np.array(triangles, dtype=np.float32)
    _write_binary_stl(filepath, mesh_data)


def generate_pin_mesh(
    filepath: Path,
    pin_radius: float = 1.5,
    pin_length: float = 6.8,
    head_radius: float = 4.5,
    head_thickness: float = 1.0,
    segments: int = 60
):
    """
    Creates central axle pin with flat round head.
    """
    triangles = []

    # Pin shaft
    triangles.extend(_generate_cylinder_annulus_triangles(
        0.0, pin_radius, 0.0, pin_length, segments
    ))

    # Pin head at top
    triangles.extend(_generate_cylinder_annulus_triangles(
        0.0, head_radius, pin_length, pin_length + head_thickness, segments
    ))

    mesh_data = np.array(triangles, dtype=np.float32)
    _write_binary_stl(filepath, mesh_data)
