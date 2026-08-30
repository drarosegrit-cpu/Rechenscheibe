"""
chart_generator.py - DXF Vector Generator and Matplotlib Visualizer
Generates laser-engraving vectors and preview graphics for the Nautical Rechenscheibe.
Supports CAM/laser layer separation (Rotor vs Stator, Engraving vs Alignment/Cut).
"""

import math
import cmath
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np

import ezdxf
from ezdxf.enums import TextEntityAlignment
import matplotlib.pyplot as plt

from polar_parser import PolarData


DEFAULT_CONFIG = {
    "R_MAX": 57.5,              # Total outer radius in mm (115 mm diameter)
    "TEXT_HEIGHT": 3.8,         # Text height for compass & log scales
    "POLAR_LABEL_HEIGHT": 4.5,  # Text height for TWS labels on polar curves
    "GRID_LABEL_HEIGHT": 4.0,   # Text height for grid percentage labels
    "AWA_RAY_LABEL_SIZE": 3.5,  # Text height for AWA angles
    "VMG_LABEL_SIZE": 3.0,      # Text height for Beat/Run VMG targets
    "TICK_LEN_MAJOR": 1.4,
    "TICK_LEN_MINOR": 0.7,
    "TEXT_GAP": -0.5,
    "GRID_LABEL_GAP": 1.0,
    "HOLE_RADIUS": 1.6,         # Center axle hole (3.2 mm diameter for M3)
    "LOG_ZONES": [
        {"min": 100, "max": 300,  "step": 1},
        {"min": 300, "max": 600,  "step": 2},
        {"min": 600, "max": 1001, "step": 5},
    ]
}


def z_to_coords(z: complex) -> Tuple[float, float]:
    """Mapping: X = East (Imag), Y = North (Real)."""
    return (z.imag, z.real)


def get_base_geometry(cfg: Dict[str, Any]) -> Dict[str, Any]:
    effective_text_h = cfg["TEXT_HEIGHT"] * 0.9
    band_width = cfg["TICK_LEN_MAJOR"] + cfg["TEXT_GAP"] + effective_text_h
    r_log_split = cfg["R_MAX"] - band_width
    r_boundary = r_log_split - band_width
    r_main = r_boundary - band_width

    return {
        "R_MAX": cfg["R_MAX"],
        "R_LOG_SPLIT": r_log_split,
        "R_BOUNDARY": r_boundary,
        "R_MAIN": r_main,
        "HOLE_RADIUS": cfg.get("HOLE_RADIUS", 1.6)
    }


def calculate_dynamic_awa_geometry(geo: Dict[str, Any], polar_data: PolarData) -> Dict[str, Any]:
    max_norm = polar_data.max_ratio
    # Scale factor 1.00 (+5.3% vs 0.95) perfectly fills the rotor disc
    mm_per_100pct = (1.00 * geo["R_MAIN"]) / max_norm
    awa_offset = complex(-mm_per_100pct, 0)

    geo["MM_PER_100PCT"] = mm_per_100pct
    geo["AWA_OFFSET"] = awa_offset
    geo["MAX_NORM"] = max_norm
    return geo


def clip_segment(z_start: complex, z_end: complex, clip_radius: float) -> Optional[Tuple[complex, complex]]:
    d1, d2 = abs(z_start), abs(z_end)
    if d1 <= clip_radius and d2 <= clip_radius:
        return (z_start, z_end)
    if d1 > clip_radius and d2 > clip_radius:
        return None
    ox, oy = z_start.real, z_start.imag
    d = z_end - z_start
    dx, dy = d.real, d.imag
    A = dx**2 + dy**2
    if A == 0:
        return None
    B = 2 * (ox * dx + oy * dy)
    C = ox**2 + oy**2 - clip_radius**2
    det = B**2 - 4 * A * C
    if det < 0:
        return None
    sqrt_det = math.sqrt(det)
    t1 = (-B + sqrt_det) / (2 * A)
    t2 = (-B - sqrt_det) / (2 * A)
    t = t1 if (0 <= t1 <= 1) else t2
    if 0 <= t <= 1:
        z_clip = z_start + t * d
        return (z_start, z_clip) if d1 <= clip_radius else (z_clip, z_end)
    return None


def get_arc_angles_within_circle_dxf(c_center: complex, c_radius: float, clip_center: complex, clip_radius: float):
    dist_vec = clip_center - c_center
    d = abs(dist_vec)
    if d >= c_radius + clip_radius:
        return None
    if d + c_radius <= clip_radius:
        return (0.0, 360.0)
    if d + clip_radius <= c_radius:
        return None

    a = (c_radius**2 - clip_radius**2 + d**2) / (2 * d)
    h = math.sqrt(max(0.0, c_radius**2 - a**2))
    p2 = c_center + a * (clip_center - c_center) / d
    x3_1 = p2.real + h * (clip_center.imag - c_center.imag) / d
    y3_1 = p2.imag - h * (clip_center.real - c_center.real) / d
    x3_2 = p2.real - h * (clip_center.imag - c_center.imag) / d
    y3_2 = p2.imag + h * (clip_center.real - c_center.real) / d

    def get_dxf_angle(center, point):
        dx = point.imag - center.imag
        dy = point.real - center.real
        return math.degrees(math.atan2(dy, dx)) % 360

    ang1 = get_dxf_angle(c_center, complex(x3_1, y3_1))
    ang2 = get_dxf_angle(c_center, complex(x3_2, y3_2))
    mid_angle_deg = (ang1 + ang2) / 2
    if ang1 > ang2:
        mid_angle_deg += 180
    mid_rad = math.radians(mid_angle_deg)
    test_pt = complex(c_center.real + c_radius * math.sin(mid_rad), c_center.imag + c_radius * math.cos(mid_rad))
    if abs(test_pt - clip_center) <= clip_radius + 0.001:
        return (ang1, ang2)
    else:
        return (ang2, ang1)


class NauticalChart:
    """
    Unified manager for ezdxf CAD export and matplotlib visual inspection.
    """
    def __init__(self, cfg: Dict[str, Any] = None):
        self.cfg = cfg or DEFAULT_CONFIG
        self.doc = ezdxf.new('R2018')
        self.modspc = self.doc.modelspace()

        # Define laser layers with specific ACI colors (1=Red, 2=Yellow, 3=Green, 4=Cyan, 5=Blue, 6=Magenta, 7=White/Black)
        self._init_layers()

        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(11, 11), dpi=150)
        self.ax.set_aspect('equal')
        self.ax.set_facecolor('#ffffff')
        self.ax.axis('off')

    def _init_layers(self):
        layers = {
            "CUT_REFERENCE": 1,        # Red: Aligning / Outer and Inner Circles
            "ENGRAVE_AWA": 4,          # Cyan: AWA speed arcs and angle rays
            "ENGRAVE_POLARS": 3,       # Green: Polar speed curves
            "ENGRAVE_COMPASS": 5,      # Blue: Compass rose & ticks
            "ENGRAVE_LOG": 6,          # Magenta: Logarithmic slide rule scale
            "ENGRAVE_TEXT": 7,         # Black/White: Text annotations & numbers
            "ENGRAVE_VMG": 2           # Yellow: Beat/Run VMG targets
        }
        for name, color in layers.items():
            if name not in self.doc.layers:
                self.doc.layers.new(name=name, dxfattribs={"color": color})

    def draw_line(self, z_start: complex, z_end: complex, layer: str = "0", color: str = "#000000", linewidth: float = 0.6):
        p1, p2 = z_to_coords(z_start), z_to_coords(z_end)
        self.modspc.add_line(p1, p2, dxfattribs={"layer": layer})
        self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=linewidth, alpha=0.85)

    def draw_circle(self, radius: float, center: complex = 0j, layer: str = "0", color: str = "#000000", linewidth: float = 0.8):
        pos = z_to_coords(center)
        self.modspc.add_circle(pos, radius, dxfattribs={"layer": layer})
        circle = plt.Circle(pos, radius, color=color, fill=False, linewidth=linewidth)
        self.ax.add_patch(circle)

    def draw_arc(self, center: complex, radius: float, start_ang: float, end_ang: float, layer: str = "0", color: str = "#888888", linewidth: float = 0.5):
        pos = z_to_coords(center)
        self.modspc.add_arc(pos, radius, start_ang, end_ang, dxfattribs={"layer": layer})
        if end_ang < start_ang:
            end_ang += 360
        th = [math.radians(start_ang + (end_ang - start_ang) * i / 25) for i in range(26)]
        xs = [pos[0] + radius * math.cos(t) for t in th]
        ys = [pos[1] + radius * math.sin(t) for t in th]
        self.ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=0.7)

    def draw_text(self, text: str, pos_z: complex, height: float, angle_deg: float, layer: str = "ENGRAVE_TEXT", align: str = "MIDDLE_CENTER", color: str = "#000000"):
        pos = z_to_coords(pos_z)
        align_enum = getattr(TextEntityAlignment, align, TextEntityAlignment.MIDDLE_CENTER)
        t = self.modspc.add_text(text, dxfattribs={"layer": layer, "height": height, "rotation": angle_deg})
        t.set_placement(pos, align=align_enum)
        self.ax.text(pos[0], pos[1], text, fontsize=height * 1.6, rotation=angle_deg, ha='center', va='center', color=color)

    def draw_point_marker(self, pos_z: complex, radius: float = 0.6, layer: str = "ENGRAVE_VMG", color: str = "#d62728"):
        self.draw_circle(radius, pos_z, layer=layer, color=color, linewidth=1.0)


def build_rechenscheibe(chart: NauticalChart, geo: Dict[str, Any], polar_data: PolarData):
    """
    Builds the complete multi-layer Rechenscheibe.
    """
    cfg = chart.cfg
    clip_r = geo["R_MAIN"]
    awa_o = geo["AWA_OFFSET"]
    mm_100 = geo["MM_PER_100PCT"]

    # 1. REFERENCE CIRCLES (Laser alignment & boundary)
    chart.draw_circle(geo["R_MAX"], layer="CUT_REFERENCE", color="#d62728", linewidth=1.2)
    chart.draw_circle(clip_r, layer="CUT_REFERENCE", color="#d62728", linewidth=0.8)
    chart.draw_circle(geo["HOLE_RADIUS"], layer="CUT_REFERENCE", color="#d62728", linewidth=0.8)
    # AWA / AWS Pivot Hole for Tactical Ruler
    chart.draw_circle(1.25, center=awa_o, layer="CUT_REFERENCE", color="#d62728", linewidth=0.8)

    # 2. INNER ROTOR: Concentric Percentage Grid
    step = 0.2 * mm_100
    i = 1
    while True:
        r = i * step
        if r >= clip_r - 2.0:
            break
        chart.draw_circle(r, layer="ENGRAVE_AWA", color="#cccccc", linewidth=0.4)
        lbl_pos = complex(r - cfg["GRID_LABEL_GAP"], 0)
        chart.draw_text(f"{i*0.2:.1f}", lbl_pos, cfg["GRID_LABEL_HEIGHT"], 0, layer="ENGRAVE_TEXT", align="TOP_CENTER", color="#888888")
        i += 1

    # Center 10° rays
    for a in range(0, 360, 10):
        z_end = cmath.rect(clip_r, math.radians(a))
        chart.draw_line(0j, z_end, layer="ENGRAVE_AWA", color="#e0e0e0", linewidth=0.3)

    # 3. INNER ROTOR: AWA Rays & Labels
    for a in range(0, 360, 10):
        p_far = awa_o + cmath.rect(clip_r * 3, math.radians(a))
        seg = clip_segment(awa_o, p_far, clip_r)
        if seg:
            chart.draw_line(awa_o, seg[1], layer="ENGRAVE_AWA", color="#00bcd4", linewidth=0.4)

        ang_norm = a if a <= 180 else a - 360
        if -80 <= ang_norm <= 80:
            r_lbl = 0.4 * mm_100
            pos_lbl = awa_o + cmath.rect(r_lbl, math.radians(a))
            chart.draw_text(str(abs(ang_norm)), pos_lbl, cfg["AWA_RAY_LABEL_SIZE"], -a, layer="ENGRAVE_TEXT", color="#00838f")

    # 4. INNER ROTOR: AWA Speed Arcs
    step_awa = 0.2 * mm_100
    i = 1
    while True:
        r = i * step_awa
        d = abs(awa_o.real)
        if r - d >= clip_r:
            break
        angles = get_arc_angles_within_circle_dxf(awa_o, r, 0j, clip_r)
        if angles:
            s, e = angles
            chart.draw_arc(awa_o, r, s, e, layer="ENGRAVE_AWA", color="#80deea", linewidth=0.5)
            if r > 3.0:
                pos = awa_o + complex(r + cfg["GRID_LABEL_GAP"], 0)
                chart.draw_text(f"{i*0.2:.1f}", pos, cfg["GRID_LABEL_HEIGHT"], 0, layer="ENGRAVE_TEXT", align="BOTTOM_CENTER", color="#00838f")
        i += 1

    # 5. INNER ROTOR: Polar Speed Curves & Target VMG Markers
    dyn_scale = (1.00 * clip_r) / geo["MAX_NORM"]
    curves = polar_data.get_spline_curves(dyn_scale)
    color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#17becf', '#7f7f7f']

    for idx, c_info in enumerate(curves):
        color = color_palette[idx % len(color_palette)]
        tws = c_info["tws"]
        targets = c_info["targets"]

        # Draw Starboard and Port curve segments
        for side in [c_info["starboard"], c_info["port"]]:
            filtered_pts = [p for p in side if 18 <= (math.degrees(cmath.phase(p)) % 360) <= 342]
            if len(filtered_pts) > 1:
                for k in range(len(filtered_pts) - 1):
                    seg = clip_segment(filtered_pts[k], filtered_pts[k+1], clip_r)
                    if seg:
                        chart.draw_line(seg[0], seg[1], layer="ENGRAVE_POLARS", color=color, linewidth=0.9)

        # Labels (TWS) at entry
        if c_info["starboard"]:
            first_pt = c_info["starboard"][0]
            ang = cmath.phase(first_pt)
            pos_r = cmath.rect(abs(first_pt), ang - math.radians(4))
            pos_l = complex(pos_r.real, -pos_r.imag)
            label_text = f"{int(tws)}" if tws.is_integer() else f"{tws}"
            chart.draw_text(label_text, pos_r, cfg["POLAR_LABEL_HEIGHT"], 0, layer="ENGRAVE_TEXT", color=color)
            chart.draw_text(label_text, pos_l, cfg["POLAR_LABEL_HEIGHT"], 0, layer="ENGRAVE_TEXT", color=color)

        # Highlight Beat VMG Target point (Diamond marker + speed text)
        beat_r = (targets["beat_sog"] / tws) * dyn_scale
        beat_pt_stbd = cmath.rect(beat_r, math.radians(targets["beat_angle"]))
        beat_pt_port = complex(beat_pt_stbd.real, -beat_pt_stbd.imag)
        chart.draw_point_marker(beat_pt_stbd, radius=0.6, layer="ENGRAVE_VMG", color="#d62728")
        chart.draw_point_marker(beat_pt_port, radius=0.6, layer="ENGRAVE_VMG", color="#d62728")

        # Run VMG Target point
        run_r = (targets["run_sog"] / tws) * dyn_scale
        run_pt_stbd = cmath.rect(run_r, math.radians(targets["gybe_angle"]))
        run_pt_port = complex(run_pt_stbd.real, -run_pt_stbd.imag)
        chart.draw_point_marker(run_pt_stbd, radius=0.6, layer="ENGRAVE_VMG", color="#2ca02c")
        chart.draw_point_marker(run_pt_port, radius=0.6, layer="ENGRAVE_VMG", color="#2ca02c")

    # 5b. Optional: Dedicated Sail Curves (Jib, Asym, Sym) when flag is enabled
    if geo.get("RENDER_SAIL_LAYERS", False) and hasattr(polar_data, "get_sail_spline_curves"):
        sail_specs = [
            ("Jib", "ENGRAVE_POLAR_JIB", "#78909c"),
            ("AsymCL", "ENGRAVE_POLAR_ASYM", "#ffb74d"),
            ("Sym", "ENGRAVE_POLAR_SYM", "#ba68c8")
        ]
        for s_name, s_layer, s_color in sail_specs:
            s_curves = polar_data.get_sail_spline_curves(s_name, dyn_scale)
            for c_info in s_curves:
                for side in [c_info["starboard"], c_info["port"]]:
                    filtered_pts = [p for p in side if 18 <= (math.degrees(cmath.phase(p)) % 360) <= 342]
                    if len(filtered_pts) > 1:
                        for k in range(len(filtered_pts) - 1):
                            seg = clip_segment(filtered_pts[k], filtered_pts[k + 1], clip_r)
                            if seg:
                                chart.draw_line(seg[0], seg[1], layer=s_layer, color=s_color, linewidth=0.5)

    # 6. STATOR / OUTER RING: Dual Circumferential Scales
    r_split = geo["R_MAIN"]
    chart.draw_circle(r_split, layer="CUT_REFERENCE", color="#000000", linewidth=0.8)
    l_maj = cfg["TICK_LEN_MAJOR"]
    l_min = cfg["TICK_LEN_MINOR"]
    txt_h = cfg["TEXT_HEIGHT"]
    dist_txt = l_maj + cfg["TEXT_GAP"] + (txt_h * 0.4)

    # 6A. INNERE SKALA (Winkel vom geometrischen Mittelpunkt (0,0) aus - 360° Kompasskurs / True Heading / TWA)
    for a in range(0, 360, 2):
        is_maj = (a % 10 == 0)
        l = l_maj if is_maj else l_min
        z_c = cmath.rect(r_split, math.radians(a))
        # Ticks wachsen von r_split nach INNEN
        chart.draw_line(cmath.rect(r_split - l, math.radians(a)), z_c, layer="ENGRAVE_COMPASS", color="#000000", linewidth=0.5)

        if a % 10 == 0:
            rot = -a
            chart.draw_text(str(a), cmath.rect(r_split - dist_txt, math.radians(a)), txt_h, rot, layer="ENGRAVE_TEXT")

    # 6B. ÄUSSERE SKALA (Winkel vom unteren Zentrum P_AWA aus - Apparent Wind Angle)
    y0 = abs(awa_o.real)

    def get_awa_intersection(beta_deg, sign=1):
        rad_b = math.radians(beta_deg)
        cos_b = math.cos(rad_b)
        sin_b = math.sin(rad_b)
        t = y0 * cos_b + math.sqrt(max(0.0, r_split**2 - (y0 * sin_b)**2))
        x = sign * t * sin_b
        y = -y0 + t * cos_b
        alpha = math.degrees(math.atan2(x, y)) % 360
        return complex(y, x), alpha

    for sign in [1, -1]:
        for beta in range(0, 181):
            if sign == -1 and (beta == 0 or beta == 180):
                continue  # 0° und 180° liegen auf der Mittellinie

            is_maj = (beta % 10 == 0)
            is_mid = (beta <= 60 and beta % 2 == 0) or (60 < beta <= 120 and beta % 5 == 0)

            if not (is_maj or is_mid):
                continue

            l = l_maj if is_maj else l_min
            z_inter, alpha = get_awa_intersection(beta, sign)
            rad_fac = (r_split + l) / r_split
            z_outer = z_inter * rad_fac

            # Ticks wachsen von r_split nach AUSSEN
            chart.draw_line(z_inter, z_outer, layer="ENGRAVE_COMPASS", color="#000000", linewidth=0.5)

            # Beschriftung für die Hauptteilstriche (bis 110° alle 10°, danach 120, 140, 160, 180)
            should_label = False
            if is_maj:
                if beta <= 110:
                    should_label = True
                elif beta in [120, 140, 160, 180]:
                    should_label = True

            if should_label:
                lbl_fac = (r_split + dist_txt) / r_split
                z_lbl = z_inter * lbl_fac
                rot = -alpha
                chart.draw_text(str(beta), z_lbl, txt_h, rot, layer="ENGRAVE_TEXT", color="#00838f")

    # 7. STATOR / OUTER RING: Logarithmic Slide Rule Scale
    r_log = geo["R_LOG_SPLIT"]
    chart.draw_circle(r_log, layer="CUT_REFERENCE", color="#000000", linewidth=0.8)
    zones = cfg["LOG_ZONES"]
    x = 100
    while x <= 1000:
        zone = next((z for z in zones if x >= z["min"] and x < z["max"]), zones[-1])
        val = x / 100.0
        deg = math.log10(val) * 360.0
        l = l_min
        is_lbl = False
        if zone["step"] == 1:
            if x % 10 == 0:
                l = l_maj
                is_lbl = True
            elif x % 5 == 0:
                l = l_maj * 0.8
        elif zone["step"] == 2:
            if x % 10 == 0:
                l = l_maj
                is_lbl = True
        elif zone["step"] == 5:
            if x % 50 == 0:
                l = l_maj
                is_lbl = True
            elif x % 10 == 0:
                l = l_maj * 0.8

        z_c = cmath.rect(r_log, math.radians(deg))
        chart.draw_line(cmath.rect(r_log - l, math.radians(deg)), z_c, layer="ENGRAVE_LOG", color="#000000", linewidth=0.5)
        chart.draw_line(z_c, cmath.rect(r_log + l, math.radians(deg)), layer="ENGRAVE_LOG", color="#000000", linewidth=0.5)

        if is_lbl:
            txt = "{:1.0f}".format(val) if val.is_integer() else "{:1.1f}".format(val)
            if val == 10:
                txt = "1"
            chart.draw_text(txt, cmath.rect(r_log - dist_txt, math.radians(deg)), txt_h, -deg, layer="ENGRAVE_TEXT")
            chart.draw_text(txt, cmath.rect(r_log + dist_txt, math.radians(deg)), txt_h, -deg, layer="ENGRAVE_TEXT")
        x += zone["step"]


def build_ruler_dxf(
    out_path: Path,
    length: float = 100.0,
    width: float = 6.0,
    r_hub: float = 4.0,
    r_hole: float = 1.3,
    mm_per_100pct: float = 37.12
):
    """
    Generates a dedicated laser-cut / engraving DXF file for the Tactical Ruler:
    - CUT_REFERENCE (Red): Outer perimeter and center pivot hole.
    - ENGRAVE_AWA (Cyan): AWS speed scale along the reading edge (every 0.1 / 0.2 TWS ratio).
    - ENGRAVE_TEXT (Black): Numbers ("0.4", "0.6", "0.8", "1.0", "1.2", "1.4", "1.6", "1.8", "2.0") and labels.
    """
    doc = ezdxf.new('R2018')
    msp = doc.modelspace()

    # Setup layers
    doc.layers.new(name="CUT_REFERENCE", dxfattribs={"color": 1})  # Red
    doc.layers.new(name="ENGRAVE_AWA", dxfattribs={"color": 4})    # Cyan
    doc.layers.new(name="ENGRAVE_TEXT", dxfattribs={"color": 7})   # Black/White

    # 1. Pivot Hole at (0, 0)
    msp.add_circle((0.0, 0.0), r_hole, dxfattribs={"layer": "CUT_REFERENCE"})

    # 2. Outer Perimeter Polygon
    pts = []
    # Hub arc (from angle 0 to -180 deg)
    hub_angles = np.linspace(0, -np.pi, 30)
    for a in hub_angles:
        pts.append((float(r_hub * np.cos(a)), float(r_hub * np.sin(a))))
    # Left edge
    pts.append((-width, r_hub))
    pts.append((-width, length - 6.0))
    # Thumb tab
    pts.append((-width - 2.5, length - 3.0))
    pts.append((-width - 1.0, length))
    pts.append((-1.5, length))
    # Pointer tip
    pts.append((0.0, length - 4.5))
    # Reading edge along X = 0
    pts.append((0.0, r_hub))

    for i in range(len(pts)):
        p1 = pts[i]
        p2 = pts[(i + 1) % len(pts)]
        msp.add_line(p1, p2, dxfattribs={"layer": "CUT_REFERENCE"})

    # 3. AWS Speed Ticks along X = 0
    # Steps: 0.1 * mm_per_100pct
    step_10pct = 0.1 * mm_per_100pct
    val = 0.1
    while True:
        y = val * mm_per_100pct
        if y > length - 6.0:
            break
        is_major = round(val * 10) % 2 == 0  # 0.2, 0.4, 0.6...
        tick_len = 2.2 if is_major else 1.2

        # Draw tick from reading edge (X = 0) inward into ruler body (negative X)
        msp.add_line((0.0, y), (-tick_len, y), dxfattribs={"layer": "ENGRAVE_AWA"})

        if is_major:
            txt = f"{val:.1f}"
            t = msp.add_text(txt, dxfattribs={"layer": "ENGRAVE_TEXT", "height": 2.2, "rotation": 0})
            t.set_placement((-tick_len - 1.2, y), align=TextEntityAlignment.MIDDLE_RIGHT)
        val += 0.1

    # 4. Text Labels
    t_title = msp.add_text("AWS / TWS", dxfattribs={"layer": "ENGRAVE_TEXT", "height": 2.4, "rotation": 90})
    t_title.set_placement((-width + 1.2, 25.0), align=TextEntityAlignment.MIDDLE_CENTER)

    t_boat = msp.add_text("JPK 1080", dxfattribs={"layer": "ENGRAVE_TEXT", "height": 2.0, "rotation": 90})
    t_boat.set_placement((-width + 1.2, 60.0), align=TextEntityAlignment.MIDDLE_CENTER)

    doc.saveas(str(out_path))

