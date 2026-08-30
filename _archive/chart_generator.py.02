"""
chart_generator.py - CAD/CAM Vector Rendering (ezdxf) for Dual-Sided Rechenscheibe
Generates:
1. Front Side (Taktik & Polaren):
   - Rotor: 8 ORC Polar curves, AWA grid, AWS speed arcs, VMG diamonds
   - Stator: 360° Compass rose (outer scale) + AWA angle scale from lower pole (inner scale)
2. Back Side (Logarithmischer Rechenschieber):
   - Rotor: Inner logarithmic scale (1 to 10/100, ticks outward to R_split)
   - Stator: Outer logarithmic scale (1 to 10/100, ticks inward to R_split)
3. Central Ratio Pointer:
   - Pivoting at (0,0) with engraved Ratio scale V_BS / TWS (0.0 to 1.20)
"""

import math
import cmath
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

import ezdxf
from ezdxf.enums import TextEntityAlignment
import matplotlib.pyplot as plt


def z_to_coords(z: complex) -> Tuple[float, float]:
    return (z.real, z.imag)


def clip_segment(p1: complex, p2: complex, r_max: float) -> Optional[Tuple[complex, complex]]:
    d1, d2 = abs(p1), abs(p2)
    if d1 <= r_max and d2 <= r_max:
        return (p1, p2)
    if d1 > r_max and d2 > r_max:
        return None
    dp = p2 - p1
    a = dp.real**2 + dp.imag**2
    if a == 0:
        return None
    b = 2 * (p1.real * dp.real + p1.imag * dp.imag)
    c = p1.real**2 + p1.imag**2 - r_max**2
    disc = b**2 - 4 * a * c
    if disc < 0:
        return None
    t1 = (-b - math.sqrt(disc)) / (2 * a)
    t2 = (-b + math.sqrt(disc)) / (2 * a)
    valid_t = [t for t in (t1, t2) if 0 <= t <= 1]
    if not valid_t:
        return None
    t = valid_t[0]
    p_inter = p1 + t * dp
    return (p1, p_inter) if d1 <= r_max else (p_inter, p2)


def get_arc_angles_within_circle_dxf(c_arc: complex, r_arc: float, c_bound: complex, r_bound: float) -> Optional[Tuple[float, float]]:
    d = abs(c_arc - c_bound)
    if d + r_arc <= r_bound:
        return (0.0, 360.0)
    if d >= r_arc + r_bound or r_arc >= d + r_bound:
        return None
    alpha = math.acos((d**2 + r_arc**2 - r_bound**2) / (2 * d * r_arc))
    phi = cmath.phase(c_bound - c_arc)
    start_ang = math.degrees(phi - alpha) % 360
    end_ang = math.degrees(phi + alpha) % 360
    return (start_ang, end_ang)


class NauticalChart:
    def __init__(self, geo_cfg: Dict[str, Any], title: str = "Rechenscheibe"):
        self.cfg = geo_cfg
        self.title = title
        self.doc = ezdxf.new("R2010")
        self.modspc = self.doc.modelspace()
        self._setup_layers()

        # Matplotlib visualization
        self.fig, self.ax = plt.subplots(figsize=(10, 10), dpi=300)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        r_lim = self.cfg.get("R_MAX", 57.5) * 1.08
        self.ax.set_xlim(-r_lim, r_lim)
        self.ax.set_ylim(-r_lim, r_lim)

    def _setup_layers(self):
        layers = [
            ("CUT_REFERENCE", 1),       # Red
            ("ENGRAVE_AWA", 4),         # Cyan
            ("ENGRAVE_POLARS", 5),      # Blue
            ("ENGRAVE_VMG", 3),         # Green
            ("ENGRAVE_COMPASS", 7),     # White / Black
            ("ENGRAVE_LOG", 7),         # Black
            ("ENGRAVE_TEXT", 7),        # Black
            ("ENGRAVE_POLAR_JIB", 8),   # Grey
            ("ENGRAVE_POLAR_ASYM", 30), # Orange
            ("ENGRAVE_POLAR_SYM", 210), # Magenta
            ("POINTER", 1)              # Red
        ]
        for name, color in layers:
            if name not in self.doc.layers:
                self.doc.layers.new(name=name, dxfattribs={"color": color})

    def draw_circle(self, radius: float, center: complex = 0j, layer: str = "CUT_REFERENCE", color: str = "#d62728", linewidth: float = 0.8):
        pos = z_to_coords(center)
        self.modspc.add_circle(pos, radius, dxfattribs={"layer": layer})
        circ = plt.Circle(pos, radius, color=color, fill=False, linewidth=linewidth)
        self.ax.add_patch(circ)

    def draw_line(self, p1: complex, p2: complex, layer: str = "ENGRAVE_AWA", color: str = "#00bcd4", linewidth: float = 0.5):
        self.modspc.add_line(z_to_coords(p1), z_to_coords(p2), dxfattribs={"layer": layer})
        self.ax.plot([p1.real, p2.real], [p1.imag, p2.imag], color=color, linewidth=linewidth)

    def draw_arc(self, center: complex, radius: float, start_ang: float, end_ang: float, layer: str = "ENGRAVE_AWA", color: str = "#00bcd4", linewidth: float = 0.5):
        pos = z_to_coords(center)
        self.modspc.add_arc(pos, radius, start_ang, end_ang, dxfattribs={"layer": layer})
        if end_ang < start_ang:
            end_ang += 360
        th = [math.radians(start_ang + (end_ang - start_ang) * i / 30) for i in range(31)]
        xs = [pos[0] + radius * math.cos(t) for t in th]
        ys = [pos[1] + radius * math.sin(t) for t in th]
        self.ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=0.7)

    def draw_text(self, text: str, pos_z: complex, height: float, angle_deg: float, layer: str = "ENGRAVE_TEXT", align: str = "MIDDLE_CENTER", color: str = "#000000"):
        pos = z_to_coords(pos_z)
        align_enum = getattr(TextEntityAlignment, align, TextEntityAlignment.MIDDLE_CENTER)
        t = self.modspc.add_text(text, dxfattribs={"layer": layer, "height": height, "rotation": angle_deg})
        t.set_placement(pos, align=align_enum)
        self.ax.text(pos[0], pos[1], text, fontsize=height * 1.5, rotation=angle_deg, ha='center', va='center', color=color)

    def draw_point_marker(self, pos_z: complex, radius: float = 0.6, layer: str = "ENGRAVE_VMG", color: str = "#d62728"):
        self.draw_circle(radius, pos_z, layer=layer, color=color, linewidth=1.0)


def build_front_side(chart: NauticalChart, geo: Dict[str, Any], polar_data):
    """
    Builds the Front Side (Taktik & Polaren):
    - Rotor: Polars, AWA-Grid, AWS-Arcs, VMG Targets
    - Stator: Outer 360° Compass Rose + Inner AWA Scale from lower pole
    """
    cfg = chart.cfg
    r_max = geo["R_MAX"]
    r_split = geo["R_SPLIT"]
    hole_r = geo["HOLE_RADIUS"]
    awa_o = geo["AWA_OFFSET"]
    mm_100 = geo["MM_PER_100PCT"]
    max_norm = geo["MAX_NORM"]

    # 1. Reference boundaries
    chart.draw_circle(r_max, layer="CUT_REFERENCE", color="#d62728", linewidth=1.2)
    chart.draw_circle(r_split, layer="CUT_REFERENCE", color="#d62728", linewidth=0.9)
    chart.draw_circle(hole_r, layer="CUT_REFERENCE", color="#d62728", linewidth=0.8)

    # 2. INNER ROTOR: Concentric Ratio Rings (0.2, 0.4, 0.6, 0.8, 1.0, 1.2)
    step = 0.2 * mm_100
    i = 1
    while True:
        r = i * step
        if r >= r_split - 1.5:
            break
        chart.draw_circle(r, layer="ENGRAVE_AWA", color="#e0e0e0", linewidth=0.35)
        lbl_pos = complex(r - 0.8, 0)
        chart.draw_text(f"{i*0.2:.1f}", lbl_pos, cfg.get("GRID_LABEL_HEIGHT", 3.8), 0, layer="ENGRAVE_TEXT", align="TOP_CENTER", color="#888888")
        i += 1

    # Heading arrow at top (0° True Wind reference / Boat centerline)
    chart.draw_line(0j, complex(0, r_split - 2.0), layer="ENGRAVE_AWA", color="#999999", linewidth=0.6)
    chart.draw_line(complex(0, r_split - 2.0), complex(-1.2, r_split - 4.5), layer="ENGRAVE_AWA", color="#999999", linewidth=0.6)
    chart.draw_line(complex(0, r_split - 2.0), complex(1.2, r_split - 4.5), layer="ENGRAVE_AWA", color="#999999", linewidth=0.6)

    # 3. INNER ROTOR: AWA Rays & Speed Arcs from lower pole (0, -Y_AWA)
    for a in range(0, 360, 10):
        p_far = awa_o + cmath.rect(r_split * 3, math.radians(a))
        seg = clip_segment(awa_o, p_far, r_split - 0.5)
        if seg:
            chart.draw_line(awa_o, seg[1], layer="ENGRAVE_AWA", color="#00bcd4", linewidth=0.35)

        ang_norm = a if a <= 180 else a - 360
        if -80 <= ang_norm <= 80 and abs(ang_norm) > 0:
            r_lbl = 0.35 * mm_100
            pos_lbl = awa_o + cmath.rect(r_lbl, math.radians(a))
            chart.draw_text(str(abs(ang_norm)), pos_lbl, 2.8, -a, layer="ENGRAVE_TEXT", color="#00838f")

    # AWA Speed arcs
    step_awa = 0.2 * mm_100
    i = 1
    while True:
        r = i * step_awa
        d = abs(awa_o.imag)
        if r - d >= r_split:
            break
        angles = get_arc_angles_within_circle_dxf(awa_o, r, 0j, r_split - 0.5)
        if angles:
            s, e = angles
            chart.draw_arc(awa_o, r, s, e, layer="ENGRAVE_AWA", color="#80deea", linewidth=0.4)
            if r > 4.0:
                pos = awa_o + complex(r + 0.8, 0)
                chart.draw_text(f"{i*0.2:.1f}", pos, 2.6, 0, layer="ENGRAVE_TEXT", align="BOTTOM_CENTER", color="#00838f")
        i += 1

    # 4. INNER ROTOR: 8 ORC Polar Speed Curves of JPK 1080
    dyn_scale = (1.00 * (r_split - 0.5)) / max_norm
    curves = polar_data.get_spline_curves(dyn_scale)
    color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#17becf']

    for idx, c_info in enumerate(curves):
        color = color_palette[idx % len(color_palette)]
        tws = c_info["tws"]
        targets = c_info["targets"]

        # Draw Starboard and Port curve segments
        for side in [c_info["starboard"], c_info["port"]]:
            filtered_pts = [p for p in side if 18 <= (math.degrees(cmath.phase(p)) % 360) <= 342]
            if len(filtered_pts) > 1:
                for k in range(len(filtered_pts) - 1):
                    seg = clip_segment(filtered_pts[k], filtered_pts[k+1], r_split - 0.5)
                    if seg:
                        chart.draw_line(seg[0], seg[1], layer="ENGRAVE_POLARS", color=color, linewidth=0.9)

        # Labels (TWS) at entry
        if c_info["starboard"]:
            first_pt = c_info["starboard"][0]
            ang = cmath.phase(first_pt)
            pos_r = cmath.rect(abs(first_pt), ang - math.radians(4))
            pos_l = complex(pos_r.real, -pos_r.imag)
            lbl = f"{int(tws)}" if tws.is_integer() else f"{tws}"
            chart.draw_text(lbl, pos_r, cfg.get("POLAR_LABEL_HEIGHT", 4.5), 0, layer="ENGRAVE_TEXT", color=color)
            chart.draw_text(lbl, pos_l, cfg.get("POLAR_LABEL_HEIGHT", 4.5), 0, layer="ENGRAVE_TEXT", color=color)

        # Beat VMG Target (Red diamond)
        beat_r = (targets["beat_sog"] / tws) * dyn_scale
        beat_pt_stbd = cmath.rect(beat_r, math.radians(targets["beat_angle"]))
        beat_pt_port = complex(beat_pt_stbd.real, -beat_pt_stbd.imag)
        chart.draw_point_marker(beat_pt_stbd, radius=0.6, layer="ENGRAVE_VMG", color="#d62728")
        chart.draw_point_marker(beat_pt_port, radius=0.6, layer="ENGRAVE_VMG", color="#d62728")

        # Run VMG Target (Green diamond)
        run_r = (targets["run_sog"] / tws) * dyn_scale
        run_pt_stbd = cmath.rect(run_r, math.radians(targets["gybe_angle"]))
        run_pt_port = complex(run_pt_stbd.real, -run_pt_stbd.imag)
        chart.draw_point_marker(run_pt_stbd, radius=0.6, layer="ENGRAVE_VMG", color="#2ca02c")
        chart.draw_point_marker(run_pt_port, radius=0.6, layer="ENGRAVE_VMG", color="#2ca02c")

    # Optional: Dedicated sail curves
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
                            seg = clip_segment(filtered_pts[k], filtered_pts[k+1], r_split - 0.5)
                            if seg:
                                chart.draw_line(seg[0], seg[1], layer=s_layer, color=s_color, linewidth=0.5)

    # 5. OUTER STATOR RIM: Dual Scales
    # 5A. 360° Compass Rose (Outermost Scale)
    r_comp = r_max - 0.3
    t_maj = cfg.get("COMPASS_TICK_MAJ", 1.6)
    t_min = cfg.get("COMPASS_TICK_MIN", 0.9)
    txt_h = cfg.get("COMPASS_TEXT_H", 3.2)
    chart.draw_circle(r_comp, layer="ENGRAVE_COMPASS", color="#000000", linewidth=0.5)

    for deg in range(0, 360, 2):
        is_major = (deg % 10 == 0)
        is_labeled = (deg % 30 == 0)
        length = t_maj if is_major else t_min
        p_out = cmath.rect(r_comp, math.radians(deg))
        p_in = cmath.rect(r_comp - length, math.radians(deg))
        chart.draw_line(p_out, p_in, layer="ENGRAVE_COMPASS", color="#000000", linewidth=0.6 if is_major else 0.3)

        if is_labeled:
            p_txt = cmath.rect(r_comp - t_maj - txt_h * 0.5 - 0.3, math.radians(deg))
            lbl = f"{deg}°" if deg > 0 else "0°/360°"
            chart.draw_text(lbl, p_txt, txt_h, -deg + 90, layer="ENGRAVE_TEXT", color="#000000")

    # 5B. AWA Angle Scale from lower pole (Inner Scale on Stator)
    r_awa_scale = r_split + 0.8
    chart.draw_circle(r_awa_scale, layer="ENGRAVE_AWA", color="#00838f", linewidth=0.5)
    awa_t_maj = cfg.get("AWA_TICK_MAJ", 1.4)
    awa_t_min = cfg.get("AWA_TICK_MIN", 0.7)
    awa_txt_h = cfg.get("AWA_TEXT_H", 2.8)

    y0 = abs(awa_o.imag)
    for beta_deg in range(10, 181, 2):
        beta = math.radians(beta_deg)
        sin_b = math.sin(beta)
        cos_b = math.cos(beta)
        det = r_awa_scale**2 - (y0 * sin_b)**2
        if det < 0:
            continue
        t_dist = y0 * cos_b + math.sqrt(det)
        pt_stbd = awa_o + complex(t_dist * sin_b, t_dist * cos_b)
        pt_port = complex(-pt_stbd.real, pt_stbd.imag)

        is_major = (beta_deg % 10 == 0)
        is_labeled = (beta_deg % 20 == 0 or beta_deg == 180)
        l_tick = awa_t_maj if is_major else awa_t_min

        for pt in [pt_stbd, pt_port]:
            phi = cmath.phase(pt - awa_o)
            p_out = pt + cmath.rect(l_tick, phi)
            chart.draw_line(pt, p_out, layer="ENGRAVE_AWA", color="#00838f", linewidth=0.5 if is_major else 0.3)

            if is_labeled and pt.real > 0:
                p_text = pt + cmath.rect(l_tick + awa_txt_h * 0.5 + 0.3, phi)
                chart.draw_text(f"{beta_deg}°", p_text, awa_txt_h, -math.degrees(phi) + 90, layer="ENGRAVE_TEXT", color="#00838f")


def build_back_side(chart: NauticalChart, geo: Dict[str, Any]):
    """
    Builds the Back Side (Logarithmischer Rechenschieber):
    - Rotor: Inner logarithmic scale (1 to 10), ticks outward to R_split
    - Stator: Outer logarithmic scale (1 to 10), ticks inward to R_split
    Both meet precisely at R_split and slide past each other!
    """
    cfg = chart.cfg
    r_max = geo["R_MAX"]
    r_split = geo["R_SPLIT"]
    hole_r = geo["HOLE_RADIUS"]
    txt_h = cfg.get("LOG_TEXT_H", 3.0)
    dash = 0.5

    # Reference circles
    chart.draw_circle(r_max, layer="CUT_REFERENCE", color="#d62728", linewidth=1.2)
    chart.draw_circle(r_split, layer="CUT_REFERENCE", color="#d62728", linewidth=0.9)
    chart.draw_circle(hole_r, layer="CUT_REFERENCE", color="#d62728", linewidth=0.8)

    # Classic high-precision logarithmic tick generation (matching rechenscheibe_V1.0.py)
    circum = 2 * math.pi * r_split
    inc_list = [1, 2, 5]
    threshold = 0.45
    x = 100
    arc = 0.0
    inc = inc_list.pop(0)

    while x <= 1000:
        y = math.log10(x / 100.0)
        angle = y * 360.0
        delta_arc = y * circum - arc
        arc = y * circum

        # Tick length factor
        f = 1
        if x % 10 == 0: f = 2
        if x % 50 == 0: f = 3
        if x % 100 == 0: f = 4

        # Seemannisch: 0° oben (Nord), rechtsdrehend
        rot_ang = 90.0 - angle
        cs = math.cos(math.radians(rot_ang))
        sn = math.sin(math.radians(rot_ang))

        # Base point on parting line
        p_base = complex(cs * r_split, sn * r_split)

        # 1. Inner Ring (on Rotor): Ticks go inwards from r_split
        p_in = complex(cs * (r_split - f * dash * 1.2), sn * (r_split - f * dash * 1.2))
        chart.draw_line(p_base, p_in, layer="ENGRAVE_LOG", color="#000000", linewidth=0.6 if f >= 3 else 0.35)

        # 2. Outer Ring (on Stator): Ticks go outwards from r_split
        p_out = complex(cs * (r_split + f * dash * 1.2), sn * (r_split + f * dash * 1.2))
        chart.draw_line(p_base, p_out, layer="ENGRAVE_LOG", color="#000000", linewidth=0.6 if f >= 3 else 0.35)

        # Numbers
        n = x / 100.0
        if n == 10.0:
            n = 1.0

        if f == 3 and n < 6:
            text = f"{n:.1f}"
            p_txt_in = complex(cs * (r_split - 3.8), sn * (r_split - 3.8))
            p_txt_out = complex(cs * (r_split + 3.8), sn * (r_split + 3.8))
            chart.draw_text(text, p_txt_in, txt_h * 0.65, rot_ang, layer="ENGRAVE_TEXT", color="#000000")
            chart.draw_text(text, p_txt_out, txt_h * 0.65, rot_ang, layer="ENGRAVE_TEXT", color="#000000")

        if f == 4:
            text = f"{int(n)}"
            p_txt_in = complex(cs * (r_split - 4.2), sn * (r_split - 4.2))
            p_txt_out = complex(cs * (r_split + 4.2), sn * (r_split + 4.2))
            chart.draw_text(text, p_txt_in, txt_h, rot_ang, layer="ENGRAVE_TEXT", color="#000000")
            chart.draw_text(text, p_txt_out, txt_h, rot_ang, layer="ENGRAVE_TEXT", color="#000000")

        if x % 100 == 0 and delta_arc < threshold and inc_list:
            inc = inc_list.pop(0)

        x += inc


def build_pointer_dxf(filepath: Path, geo: Dict[str, Any]):
    """
    Builds the laser/cut DXF for the Central Ratio Pointer (Ruler centered at 0,0).
    Has engraved Ratio scale V_BS / TWS (0.0 to 1.20) along the reading edge.
    """
    length = geo["POINTER_LENGTH"]
    width = geo["POINTER_WIDTH"]
    hub_r = geo["POINTER_HUB_R"]
    hole_r = geo["HOLE_RADIUS"]
    max_norm = geo["MAX_NORM"]
    r_split = geo["R_SPLIT"]
    mm_100 = geo["MM_PER_100PCT"]

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    doc.layers.new(name="CUT_OUTLINE", dxfattribs={"color": 1})
    doc.layers.new(name="ENGRAVE_SCALE", dxfattribs={"color": 7})
    doc.layers.new(name="ENGRAVE_TEXT", dxfattribs={"color": 7})

    # Center axle hole
    msp.add_circle((0, 0), hole_r, dxfattribs={"layer": "CUT_OUTLINE"})

    # Pointer outline along +Y axis
    tip_len = 3.5
    tab_len = 3.0
    y_end_body = length - tip_len - tab_len

    outline_pts = [
        (0.0, hub_r * 0.8),
        (width, hub_r * 0.8),
        (width, y_end_body),
        (width + 2.0, y_end_body + tab_len / 2.0),
        (width, y_end_body + tab_len),
        (0.0, length),                              # Index tip at x=0
        (0.0, hub_r * 0.8)
    ]
    msp.add_lwpolyline(outline_pts, dxfattribs={"layer": "CUT_OUTLINE"})

    # Hub outline (semicircle on back side)
    msp.add_arc((0, 0), hub_r, 90, 270, dxfattribs={"layer": "CUT_OUTLINE"})

    # Engrave Ratio scale along reading edge (x = 0)
    # Ratio = r / mm_100
    for ratio_i in range(1, int(max_norm * 20) + 1):
        ratio = ratio_i * 0.05
        y_pos = ratio * mm_100
        if y_pos > length - 4.0:
            break

        is_major = (ratio_i % 2 == 0) # every 0.1
        is_labeled = (ratio_i % 4 == 0) # every 0.2
        tick_w = 2.4 if is_major else 1.2
        msp.add_line((0.0, y_pos), (tick_w, y_pos), dxfattribs={"layer": "ENGRAVE_SCALE"})

        if is_labeled:
            text = f"{ratio:.1f}"
            t = msp.add_text(text, dxfattribs={"layer": "ENGRAVE_TEXT", "height": 1.8, "rotation": 0})
            t.set_placement((tick_w + 0.6, y_pos), align=TextEntityAlignment.MIDDLE_LEFT)

    doc.saveas(str(filepath))
