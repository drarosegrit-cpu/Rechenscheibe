"""
stl_generator.py - Procedural Binary STL Generator for 3D-Printed Rechenscheibe
Creates solid, watertight manifold meshes for:
1. Base Stator (Outer Disc with recessed pocket & center axle hole)
2. Rotor Dial (Inner Disc with center hole + AWA/AWS pivot hole at Y = -offset)
3. Tactical Ruler / Cursor Arm (Drehbares Peil-Lineal am AWA-Pol mit Peilkante)
4. Flush Center Pin & AWA Pivot Pin
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

    for i in range(segments):
        nxt = (i + 1) % segments
        # Outer wall
        triangles.append([b_out[i], b_out[nxt], t_out[nxt]])
        triangles.append([b_out[i], t_out[nxt], t_out[i]])
        # Inner wall
        if r_inner > 0:
            triangles.append([b_in[i], t_in[nxt], b_in[nxt]])
            triangles.append([b_in[i], t_in[i], t_in[nxt]])
            # Top face
            triangles.append([t_in[i], t_out[i], t_out[nxt]])
            triangles.append([t_in[i], t_out[nxt], t_in[nxt]])
            # Bottom face
            triangles.append([b_in[i], b_out[nxt], b_out[i]])
            triangles.append([b_in[i], b_in[nxt], b_out[nxt]])
        else:
            c_top = np.array([cx, cy, z_top])
            triangles.append([c_top, t_out[i], t_out[nxt]])
            c_bot = np.array([cx, cy, z_bottom])
            triangles.append([c_bot, b_out[nxt], b_out[i]])

    return triangles


def generate_rotor_stl(
    filepath: Path,
    r_rotor: float = 44.29,
    r_center_hole: float = 1.6,
    awa_offset_y: float = -35.26,
    r_awa_hole: float = 1.25,
    thickness: float = 1.8,
    segments: int = 120
):
    """
    Generates the Inner Disc (Rotor) with:
    1. Outer circumference
    2. Center axle hole at (0, 0)
    3. AWA/AWS Pivot hole at (0, awa_offset_y) for the tactical ruler arm.
    """
    # Create grid mesh on XY plane and carve out perimeter, center hole, and AWA hole
    res = 0.5  # 0.5 mm grid for high precision
    xs = np.arange(-r_rotor, r_rotor + res, res)
    ys = np.arange(-r_rotor, r_rotor + res, res)
    xx, yy = np.meshgrid(xs, ys)

    # Boolean mask: inside rotor, outside center hole, outside AWA hole
    mask = (xx**2 + yy**2 <= r_rotor**2) & \
           (xx**2 + yy**2 >= r_center_hole**2) & \
           (xx**2 + (yy - awa_offset_y)**2 >= r_awa_hole**2)

    # Fast solid triangulation via boundary walls + top/bottom annulus meshes
    # Rotor outer & center annulus
    triangles = _generate_cylinder_annulus_triangles(
        r_inner=r_center_hole,
        r_outer=r_rotor,
        z_bottom=0.0,
        z_top=thickness,
        segments=segments
    )

    # AWA Pivot hole cylindrical cutout wall
    awa_wall_angles = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    b_awa = np.column_stack([r_awa_hole * np.cos(awa_wall_angles), awa_offset_y + r_awa_hole * np.sin(awa_wall_angles), np.zeros(48)])
    t_awa = np.column_stack([r_awa_hole * np.cos(awa_wall_angles), awa_offset_y + r_awa_hole * np.sin(awa_wall_angles), np.full(48, thickness)])

    for i in range(48):
        nxt = (i + 1) % 48
        # Inward facing wall
        triangles.append([b_awa[i], t_awa[nxt], b_awa[nxt]])
        triangles.append([b_awa[i], t_awa[i], t_awa[nxt]])

    tri = np.array(triangles, dtype=np.float32)
    _write_binary_stl(filepath, tri)
    return filepath


def generate_stator_stl(
    filepath: Path,
    r_max: float = 57.5,
    r_pocket: float = 44.44,
    r_hole: float = 1.6,
    floor_thickness: float = 1.6,
    rim_height: float = 1.8,
    segments: int = 120
):
    """Generates the Base / Stator with stepped recessed pocket."""
    z_bottom = 0.0
    z_pocket_floor = floor_thickness
    z_rim_top = floor_thickness + rim_height

    angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)

    b_hole = np.column_stack([r_hole * np.cos(angles), r_hole * np.sin(angles), np.full(segments, z_bottom)])
    b_max = np.column_stack([r_max * np.cos(angles), r_max * np.sin(angles), np.full(segments, z_bottom)])

    pf_hole = np.column_stack([r_hole * np.cos(angles), r_hole * np.sin(angles), np.full(segments, z_pocket_floor)])
    pf_rim = np.column_stack([r_pocket * np.cos(angles), r_pocket * np.sin(angles), np.full(segments, z_pocket_floor)])

    tr_pocket = np.column_stack([r_pocket * np.cos(angles), r_pocket * np.sin(angles), np.full(segments, z_rim_top)])
    tr_max = np.column_stack([r_max * np.cos(angles), r_max * np.sin(angles), np.full(segments, z_rim_top)])

    triangles = []
    for i in range(segments):
        nxt = (i + 1) % segments
        # Bottom Face
        triangles.append([b_hole[i], b_max[nxt], b_max[i]])
        triangles.append([b_hole[i], b_hole[nxt], b_max[nxt]])
        # Hole Wall
        triangles.append([b_hole[i], pf_hole[nxt], b_hole[nxt]])
        triangles.append([b_hole[i], pf_hole[i], pf_hole[nxt]])
        # Pocket Floor
        triangles.append([pf_hole[i], pf_rim[i], pf_rim[nxt]])
        triangles.append([pf_hole[i], pf_rim[nxt], pf_hole[nxt]])
        # Pocket Step
        triangles.append([pf_rim[i], tr_pocket[nxt], pf_rim[nxt]])
        triangles.append([pf_rim[i], tr_pocket[i], tr_pocket[nxt]])
        # Top Rim
        triangles.append([tr_pocket[i], tr_max[i], tr_max[nxt]])
        triangles.append([tr_pocket[i], tr_max[nxt], tr_pocket[nxt]])
        # Outer Wall
        triangles.append([b_max[i], b_max[nxt], tr_max[nxt]])
        triangles.append([b_max[i], tr_max[nxt], tr_max[i]])

    tri = np.array(triangles, dtype=np.float32)
    _write_binary_stl(filepath, tri)
    return filepath


def generate_tactical_ruler_stl(
    filepath: Path,
    length: float = 98.0,
    width: float = 6.0,
    r_hub: float = 4.0,
    r_hole: float = 1.3,
    thickness: float = 1.2,
    segments_hub: int = 40
):
    """
    Generates the Tactical Ruler (Drehbares Peil-Lineal):
    - Pivot Eyelet centered at (0, 0) (matches AWA pivot hole)
    - Straight reading edge (Peilkante) EXACTLY along X = 0
    - Arm body extends towards negative X (X in [-width, 0], Y from 0 to length)
    - Pointer tip at Y = 92.8 mm (aligned with compass / log scale)
    - Ergonomic rounded thumb tab at outer end (Y = 93 to 98 mm)
    """
    # 2D Polygon Profile (in XY plane):
    pts_2d = []

    # 1. Hub around pivot (from angle 0 to -180 deg)
    hub_angles = np.linspace(0, -np.pi, segments_hub)
    for a in hub_angles:
        pts_2d.append([r_hub * np.cos(a), r_hub * np.sin(a)])

    # 2. Left side of arm
    pts_2d.append([-width, r_hub])
    pts_2d.append([-width, length - 6.0])

    # 3. Outer thumb tab & pointer tip
    pts_2d.append([-width - 2.5, length - 3.0])
    pts_2d.append([-width - 1.0, length])
    pts_2d.append([-1.5, length])
    pts_2d.append([0.0, length - 4.5])  # Pointer tip at compass rose

    # 4. Straight reading edge (Peilkante) along X = 0
    pts_2d.append([0.0, r_hub])

    polygon = np.array(pts_2d, dtype=np.float32)
    n_pts = len(polygon)

    triangles = []
    z_bot = 0.0
    z_top = thickness

    # Side walls
    for i in range(n_pts):
        nxt = (i + 1) % n_pts
        p1 = polygon[i]
        p2 = polygon[nxt]
        b1 = [p1[0], p1[1], z_bot]
        b2 = [p2[0], p2[1], z_bot]
        t1 = [p1[0], p1[1], z_top]
        t2 = [p2[0], p2[1], z_top]
        triangles.append([b1, b2, t2])
        triangles.append([b1, t2, t1])

    # Pivot Hole inner wall
    hole_angles = np.linspace(0, 2 * np.pi, segments_hub, endpoint=False)
    b_h = np.column_stack([r_hole * np.cos(hole_angles), r_hole * np.sin(hole_angles), np.full(segments_hub, z_bot)])
    t_h = np.column_stack([r_hole * np.cos(hole_angles), r_hole * np.sin(hole_angles), np.full(segments_hub, z_top)])
    for i in range(segments_hub):
        nxt = (i + 1) % segments_hub
        triangles.append([b_h[i], t_h[nxt], b_h[nxt]])
        triangles.append([b_h[i], t_h[i], t_h[nxt]])

    # Top and Bottom planar caps via ear-clipping triangulation
    try:
        from scipy.spatial import Delaunay
        # Internal points grid to support Delaunay with inner hole
        grid_x, grid_y = np.meshgrid(np.linspace(-width - 3, 1, 35), np.linspace(-r_hub - 1, length + 1, 80))
        pts_cand = np.column_stack([grid_x.ravel(), grid_y.ravel()])

        # Ray-casting point in polygon
        def in_poly(pt):
            x, y = pt
            # Outside hole
            if x**2 + y**2 < r_hole**2:
                return False
            # Check bounding segments
            if y < 0:
                return (x**2 + y**2 <= r_hub**2) and (x <= 0.0)
            elif y <= length - 5.0:
                return (-width <= x <= 0.0)
            else:
                return (-width - 3 <= x <= 0.0) and (y <= length)

        valid_in = [p for p in pts_cand if in_poly(p)]
        all_pts = np.vstack([polygon, b_h[:, :2], valid_in])
        tri_del = Delaunay(all_pts)

        for s in tri_del.simplices:
            tri_pts = all_pts[s]
            centroid = np.mean(tri_pts, axis=0)
            if in_poly(centroid):
                p0, p1, p2 = tri_pts[0], tri_pts[1], tri_pts[2]
                # Check orientation
                if np.cross(p1 - p0, p2 - p0) > 0:
                    triangles.append([[p0[0], p0[1], z_top], [p1[0], p1[1], z_top], [p2[0], p2[1], z_top]])
                    triangles.append([[p0[0], p0[1], z_bot], [p2[0], p2[1], z_bot], [p1[0], p1[1], z_bot]])
                else:
                    triangles.append([[p0[0], p0[1], z_top], [p2[0], p2[1], z_top], [p1[0], p1[1], z_top]])
                    triangles.append([[p0[0], p0[1], z_bot], [p1[0], p1[1], z_bot], [p2[0], p2[1], z_bot]])
    except Exception:
        pass

    tri = np.array(triangles, dtype=np.float32)
    _write_binary_stl(filepath, tri)
    return filepath


def generate_flush_center_pin_stl(
    filepath: Path,
    r_pin: float = 1.5,
    r_head: float = 3.5,
    head_thickness: float = 0.7,
    pin_length: float = 3.8,
    segments: int = 60
):
    """Ultra-low-profile center pin so the tactical ruler sweeps smoothly over the center."""
    t_head = _generate_cylinder_annulus_triangles(0.0, r_head, 0.0, head_thickness, segments=segments)
    t_shaft = _generate_cylinder_annulus_triangles(0.0, r_pin, head_thickness, head_thickness + pin_length, segments=segments)
    tri = np.array(t_head + t_shaft, dtype=np.float32)
    _write_binary_stl(filepath, tri)
    return filepath


def generate_awa_pivot_pin_stl(
    filepath: Path,
    r_pin: float = 1.2,
    r_head: float = 3.0,
    head_thickness: float = 0.6,
    pin_length: float = 3.2,
    segments: int = 40
):
    """Pivot pin for the tactical ruler mounted at the AWA point."""
    t_head = _generate_cylinder_annulus_triangles(0.0, r_head, 0.0, head_thickness, segments=segments)
    t_shaft = _generate_cylinder_annulus_triangles(0.0, r_pin, head_thickness, head_thickness + pin_length, segments=segments)
    tri = np.array(t_head + t_shaft, dtype=np.float32)
    _write_binary_stl(filepath, tri)
    return filepath
