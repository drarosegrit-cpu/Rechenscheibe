"""
vector_engine.py - Complete 1:1 CAM / Laser Vector Engine (SVG) for 180 mm Rechenscheibe
JPK 1080 (GER 7447 - TRUE GRIT)

Laser standards:
- Cut Lines:     stroke="#FF0000", stroke-width="0.15" (Red vector cut)
- Fine Engrave:  stroke="#000000", stroke-width="0.25" (Black vector engrave)
- Text Engrave:  fill="#000000" or thematic color
- Color Accents: Stbd Green #27AE60, Port Red #C0392B, Start Line Blue #2980B9, Crossover Purple #8E44AD
"""

import math
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
from polar_parser import PolarData, catmull_rom_spline


def polar_to_cart(r: float, deg: float) -> Tuple[float, float]:
    """0° is North (12 o'clock, -Y in SVG), 90° East (+X), clockwise."""
    rad = math.radians(deg)
    return r * math.sin(rad), -r * math.cos(rad)


def find_circle_intersection(p1: Tuple[float, float], p2: Tuple[float, float], r_max: float) -> Optional[Tuple[float, float]]:
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    a = dx**2 + dy**2
    if a < 1e-9:
        return None
    b = 2.0 * (p1[0] * dx + p1[1] * dy)
    c = p1[0]**2 + p1[1]**2 - r_max**2
    disc = b**2 - 4.0 * a * c
    if disc < 0:
        return None
    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / (2.0 * a)
    t2 = (-b + sqrt_disc) / (2.0 * a)
    valid_t = [t for t in (t1, t2) if 0.0 <= t <= 1.0]
    if not valid_t:
        return None
    t = valid_t[0]
    return (p1[0] + t * dx, p1[1] + t * dy)


def clip_polyline_to_circle(pts: List[Tuple[float, float]], r_max: float) -> List[List[Tuple[float, float]]]:
    lines = []
    current_line = []
    for i in range(len(pts) - 1):
        p1, p2 = pts[i], pts[i+1]
        d1 = math.hypot(p1[0], p1[1])
        d2 = math.hypot(p2[0], p2[1])

        if d1 <= r_max and d2 <= r_max:
            if not current_line:
                current_line.append(p1)
            current_line.append(p2)
        elif d1 <= r_max and d2 > r_max:
            p_inter = find_circle_intersection(p1, p2, r_max)
            if not current_line:
                current_line.append(p1)
            if p_inter:
                current_line.append(p_inter)
            lines.append(current_line)
            current_line = []
        elif d1 > r_max and d2 <= r_max:
            p_inter = find_circle_intersection(p1, p2, r_max)
            current_line = []
            if p_inter:
                current_line.append(p_inter)
            current_line.append(p2)
        else:
            pass

    if current_line:
        lines.append(current_line)
    return lines


def find_ray_spline_intersection(ray_angle_deg: float, spline_pts: List[complex], sign_y: float = -1.0) -> Optional[Tuple[float, float]]:
    rad = math.radians(ray_angle_deg)
    rx = math.sin(rad)
    ry = sign_y * math.cos(rad)

    for i in range(len(spline_pts) - 1):
        p1 = spline_pts[i]
        p2 = spline_pts[i + 1]
        x1, y1 = p1.real, p1.imag
        x2, y2 = p2.real, p2.imag
        dx = x2 - x1
        dy = y2 - y1
        denom = dx * ry - dy * rx
        if abs(denom) < 1e-9:
            continue
        t = (y1 * rx - x1 * ry) / denom
        if 0.0 <= t <= 1.0:
            s = (x1 + t * dx) / rx if abs(rx) > abs(ry) else (y1 + t * dy) / ry
            if s > 0:
                return (x1 + t * dx, y1 + t * dy)
    return None


def svg_header(width_mm: float = 180.0, height_mm: float = 180.0) -> str:
    half_w = width_mm / 2.0
    half_h = height_mm / 2.0
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_mm}mm" height="{height_mm}mm" '
        f'viewBox="{-half_w:.2f} {-half_h:.2f} {width_mm:.2f} {height_mm:.2f}">\n'
        f'  <defs>\n'
        f'    <style>\n'
        f'      .laser-cut {{ fill: none; stroke: #FF0000; stroke-width: 0.15; }}\n'
        f'      .laser-engrave {{ fill: none; stroke: #000000; stroke-width: 0.25; }}\n'
        f'      .bg {{ fill: #FFFFFF; }}\n'
        f'      .grid-line {{ stroke: #BDC3C7; stroke-width: 0.30; fill: none; stroke-dasharray: 2,2; }}\n'
        f'      .grid-text {{ font-family: sans-serif; font-size: 2.2px; fill: #7F8C8D; text-anchor: middle; }}\n'
        f'      .sector-beat-stbd {{ fill: #2ECC71; fill-opacity: 0.22; stroke: #27AE60; stroke-width: 0.45; }}\n'
        f'      .sector-beat-port {{ fill: #E74C3C; fill-opacity: 0.22; stroke: #C0392B; stroke-width: 0.45; }}\n'
        f'      .sector-gybe-stbd {{ fill: #2ECC71; fill-opacity: 0.16; stroke: #27AE60; stroke-width: 0.40; }}\n'
        f'      .sector-gybe-port {{ fill: #E74C3C; fill-opacity: 0.16; stroke: #C0392B; stroke-width: 0.40; }}\n'
        f'      .start-line {{ stroke: #2980B9; stroke-width: 1.1; stroke-linecap: round; }}\n'
        f'      .bias-tick {{ stroke: #2980B9; stroke-width: 0.45; }}\n'
        f'      .bias-text {{ font-family: sans-serif; font-size: 1.7px; fill: #2980B9; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .bias-subtext-green {{ font-family: sans-serif; font-weight: bold; font-size: 1.6px; fill: #27AE60; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .bias-subtext-red {{ font-family: sans-serif; font-weight: bold; font-size: 1.6px; fill: #C0392B; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .shift-tick {{ stroke: #2C3E50; stroke-width: 0.45; }}\n'
        f'      .shift-indicator {{ font-family: sans-serif; font-weight: bold; font-size: 1.8px; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .shift-subtext {{ font-family: sans-serif; font-weight: bold; font-size: 1.7px; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .compass-tick {{ stroke: #2C3E50; stroke-width: 0.4; }}\n'
        f'      .compass-text {{ font-family: sans-serif; font-weight: bold; font-size: 2.6px; fill: #2C3E50; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .polar-curve {{ fill: none; stroke-width: 0.70; }}\n'
        f'      .polar-label {{ font-family: sans-serif; font-weight: bold; font-size: 2.3px; dominant-baseline: central; }}\n'
        f'      .awa-line {{ fill: none; stroke: #2980B9; stroke-width: 0.40; stroke-dasharray: 2.5,1.2; }}\n'
        f'      .awa-label {{ font-family: sans-serif; font-size: 2.0px; fill: #1B4F72; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .title-text {{ font-family: sans-serif; font-weight: bold; font-size: 2.8px; fill: #2C3E50; text-anchor: middle; }}\n'
        f'      .sub-text {{ font-family: sans-serif; font-size: 1.8px; fill: #7F8C8D; text-anchor: middle; }}\n'
        f'      .tack-label-stbd {{ font-family: sans-serif; font-weight: bold; font-size: 2.3px; fill: #27AE60; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .tack-label-port {{ font-family: sans-serif; font-weight: bold; font-size: 2.3px; fill: #C0392B; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .gybe-label-stbd {{ font-family: sans-serif; font-weight: bold; font-size: 2.3px; fill: #27AE60; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .gybe-label-port {{ font-family: sans-serif; font-weight: bold; font-size: 2.3px; fill: #C0392B; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .line-label {{ font-family: sans-serif; font-weight: bold; font-size: 2.2px; fill: #2980B9; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .vmg-beat {{ fill: #E74C3C; stroke: #962D22; stroke-width: 0.3; }}\n'
        f'      .vmg-run {{ fill: #2ECC71; stroke: #27AE60; stroke-width: 0.3; }}\n'
        f'      .crossover-marker {{ fill: #9B59B6; stroke: #8E44AD; stroke-width: 0.35; }}\n'
        f'      .crossover-line {{ fill: none; stroke: #8E44AD; stroke-width: 0.60; stroke-dasharray: 2.0,1.4; }}\n'
        f'      .crossover-text {{ font-family: sans-serif; font-weight: bold; font-size: 2.0px; fill: #8E44AD; }}\n'
        f'      .stator-rim {{ fill: #F8F9F9; stroke: #2C3E50; stroke-width: 0.6; }}\n'
        f'    </style>\n'
        f'  </defs>\n'
    )


def generate_tactical_rim() -> str:
    """Generates TackingMaster tactical ring elements for Rotor (r in [66.0, 75.0])."""
    elements = []
    r_outer = 75.0
    r_inner = 66.0

    # 1. TRUE WIND arrow & Lift/Header scale
    p_tip = (0.0, -r_outer + 0.4)
    p_l = (-2.6, -r_outer + 6.2)
    p_r = (2.6, -r_outer + 6.2)
    p_c = (0.0, -r_outer + 4.8)
    elements.append(
        f'  <polygon points="{p_tip[0]:.2f},{p_tip[1]:.2f} {p_l[0]:.2f},{p_l[1]:.2f} {p_c[0]:.2f},{p_c[1]:.2f} {p_r[0]:.2f},{p_r[1]:.2f}" '
        f'fill="#C0392B" stroke="#962D22" stroke-width="0.3" />'
    )
    elements.append(f'  <text x="0" y="{-r_outer + 8.4:.2f}" class="compass-text" fill="#C0392B">TRUE WIND</text>')
    elements.append(f'  <text x="0" y="{-r_outer + 11.2:.2f}" class="shift-subtext" fill="#27AE60">◄ PORT LIFT | STBD LIFT ►</text>')

    for side in [1, -1]:
        for shift_deg in [5.0, 10.0, 15.0]:
            d = shift_deg * side
            p1 = polar_to_cart(r_outer, d)
            p2 = polar_to_cart(r_outer - 2.2, d)
            elements.append(f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" class="shift-tick" />')
            pt = polar_to_cart(r_outer - 3.8, d)
            elements.append(f'  <text x="{pt[0]:.2f}" y="{pt[1]:.2f}" class="bias-text" fill="#2C3E50">{int(shift_deg)}°</text>')

        lbl_x, lbl_y = polar_to_cart(r_inner + 1.8, 11.5 * side)
        rot = (11.5 * side) - 90 if side > 0 else (11.5 * side) + 90
        txt = "LIFT ▶" if side > 0 else "◀ LIFT"
        elements.append(
            f'  <text x="{lbl_x:.2f}" y="{lbl_y:.2f}" class="shift-indicator" fill="#27AE60" transform="rotate({rot:.1f} {lbl_x:.2f} {lbl_y:.2f})">{txt}</text>'
        )

    # 2. TACK Corridors (38° to 42°)
    for side in [1, -1]:
        a1, a2 = 38.0 * side, 42.0 * side
        if side < 0:
            a1, a2 = a2, a1
        x1_in, y1_in = polar_to_cart(r_inner, a1)
        x2_in, y2_in = polar_to_cart(r_inner, a2)
        x1_out, y1_out = polar_to_cart(r_outer, a1)
        x2_out, y2_out = polar_to_cart(r_outer, a2)

        sweep = 1 if side > 0 else 0
        path = (
            f"M {x1_in:.2f} {y1_in:.2f} "
            f"L {x1_out:.2f} {y1_out:.2f} "
            f"A {r_outer} {r_outer} 0 0 {sweep} {x2_out:.2f} {y2_out:.2f} "
            f"L {x2_in:.2f} {y2_in:.2f} "
            f"A {r_inner} {r_inner} 0 0 {1 - sweep} {x1_in:.2f} {y1_in:.2f} Z"
        )
        sector_cls = "sector-beat-stbd" if side > 0 else "sector-beat-port"
        elements.append(f'  <path d="{path}" class="{sector_cls}" />')

        lbl_x, lbl_y = polar_to_cart(r_inner + 4.5, 40.0 * side)
        rot = (40.0 * side) - 90 if side > 0 else (40.0 * side) + 90
        lbl_txt = "STBD TACK 40°" if side > 0 else "PORT TACK 40°"
        lbl_cls = "tack-label-stbd" if side > 0 else "tack-label-port"
        elements.append(
            f'  <text x="{lbl_x:.2f}" y="{lbl_y:.2f}" class="{lbl_cls}" transform="rotate({rot:.1f} {lbl_x:.2f} {lbl_y:.2f})">{lbl_txt}</text>'
        )

    # 3. Start Line Bias System (+-90°)
    for side in [1, -1]:
        base_angle = 90.0 * side
        p_in = polar_to_cart(r_inner, base_angle)
        p_out = polar_to_cart(r_outer, base_angle)
        elements.append(f'  <line x1="{p_in[0]:.2f}" y1="{p_in[1]:.2f}" x2="{p_out[0]:.2f}" y2="{p_out[1]:.2f}" class="start-line" />')

        for b_deg in [5.0, 10.0, 15.0]:
            for s_sgn in [1, -1]:
                b_ang = base_angle + (b_deg * s_sgn)
                pt1 = polar_to_cart(r_outer, b_ang)
                pt2 = polar_to_cart(r_outer - 2.2, b_ang)
                elements.append(f'  <line x1="{pt1[0]:.2f}" y1="{pt1[1]:.2f}" x2="{pt2[0]:.2f}" y2="{pt2[1]:.2f}" class="bias-tick" />')
                pt_txt = polar_to_cart(r_outer - 3.8, b_ang)
                rot_txt = b_ang
                elements.append(f'  <text x="{pt_txt[0]:.2f}" y="{pt_txt[1]:.2f}" class="bias-text" transform="rotate({rot_txt:.1f} {pt_txt[0]:.2f} {pt_txt[1]:.2f})">{int(b_deg)}°</text>')

        lbl_center = polar_to_cart(r_inner + 4.5, base_angle)
        line_name = "BOAT END (RC)" if side > 0 else "PIN END"
        badge_w = 4.8
        badge_h = 19.0 if side > 0 else 13.5
        rot_main = 90.0 if side > 0 else -90.0
        elements.append(
            f'  <rect x="{lbl_center[0] - badge_w/2:.2f}" y="{lbl_center[1] - badge_h/2:.2f}" '
            f'width="{badge_w:.2f}" height="{badge_h:.2f}" rx="1.2" '
            f'fill="#FFFFFF" stroke="#2980B9" stroke-width="0.5" />'
        )
        elements.append(
            f'  <text x="{lbl_center[0]:.2f}" y="{lbl_center[1]:.2f}" class="line-label" transform="rotate({rot_main:.1f} {lbl_center[0]:.2f} {lbl_center[1]:.2f})">{line_name}</text>'
        )

        upwind_ang = base_angle - (9.5 * side)
        pt_up = polar_to_cart(r_inner + 1.8, upwind_ang)
        rot_up = upwind_ang
        fav_up_txt = "▲ BOAT FAV" if side > 0 else "PIN FAV ▲"
        elements.append(
            f'  <text x="{pt_up[0]:.2f}" y="{pt_up[1]:.2f}" class="bias-subtext-green" transform="rotate({rot_up:.1f} {pt_up[0]:.2f} {pt_up[1]:.2f})">{fav_up_txt}</text>'
        )

        downwind_ang = base_angle + (9.5 * side)
        pt_down = polar_to_cart(r_inner + 1.8, downwind_ang)
        rot_down = downwind_ang
        fav_down_txt = "PIN FAV ▼" if side > 0 else "▼ BOAT FAV"
        elements.append(
            f'  <text x="{pt_down[0]:.2f}" y="{pt_down[1]:.2f}" class="bias-subtext-red" transform="rotate({rot_down:.1f} {pt_down[0]:.2f} {pt_down[1]:.2f})">{fav_down_txt}</text>'
        )

    # 4. GYBE Corridors (145° to 165°)
    for side in [1, -1]:
        a1, a2 = 145.0 * side, 165.0 * side
        if side < 0:
            a1, a2 = a2, a1
        x1_in, y1_in = polar_to_cart(r_inner, a1)
        x2_in, y2_in = polar_to_cart(r_inner, a2)
        x1_out, y1_out = polar_to_cart(r_outer, a1)
        x2_out, y2_out = polar_to_cart(r_outer, a2)

        sweep = 1 if side > 0 else 0
        path = (
            f"M {x1_in:.2f} {y1_in:.2f} "
            f"L {x1_out:.2f} {y1_out:.2f} "
            f"A {r_outer} {r_outer} 0 0 {sweep} {x2_out:.2f} {y2_out:.2f} "
            f"L {x2_in:.2f} {y2_in:.2f} "
            f"A {r_inner} {r_inner} 0 0 {1 - sweep} {x1_in:.2f} {y1_in:.2f} Z"
        )
        sector_cls = "sector-gybe-stbd" if side > 0 else "sector-gybe-port"
        elements.append(f'  <path d="{path}" class="{sector_cls}" />')

        lbl_x, lbl_y = polar_to_cart(r_inner + 4.5, 155.0 * side)
        rot = (155.0 * side) - 90 if side > 0 else (155.0 * side) + 90
        lbl_txt = "STBD GYBE 155°" if side > 0 else "PORT GYBE 155°"
        lbl_cls = "gybe-label-stbd" if side > 0 else "gybe-label-port"
        elements.append(
            f'  <text x="{lbl_x:.2f}" y="{lbl_y:.2f}" class="{lbl_cls}" transform="rotate({rot:.1f} {lbl_x:.2f} {lbl_y:.2f})">{lbl_txt}</text>'
        )

    # 5. Free Sector Compass Ticks
    for deg in range(10, 180, 5):
        in_shift = (deg <= 18)
        in_tack = (36 <= deg <= 44)
        in_line = (73 <= deg <= 107)
        in_gybe = (143 <= deg <= 167)
        in_down = (deg >= 177)
        if in_shift or in_tack or in_line or in_gybe or in_down:
            continue

        for side in [1, -1]:
            d = deg * side
            is_10 = (deg % 10 == 0)
            is_30 = (deg % 30 == 0)
            t_len = 3.0 if is_30 else (2.0 if is_10 else 1.2)
            p1 = polar_to_cart(r_outer, d)
            p2 = polar_to_cart(r_outer - t_len, d)
            elements.append(f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" class="compass-tick" />')
            if is_30:
                pt = polar_to_cart(r_outer - 4.6, d)
                elements.append(f'  <text x="{pt[0]:.2f}" y="{pt[1]:.2f}" class="compass-text">{deg}°</text>')

    return "\n".join(elements)


def generate_laser_seite_a_rotor(polar: PolarData, output_file: Path):
    """Generates laser cutting & engraving SVG for Front Rotor (Weg A V1.0)."""
    L = 64.0
    r_clip = 65.2

    parts = [svg_header(180.0, 180.0)]
    # Background & Cut lines
    parts.append('  <!-- Laser Cut lines (Red) -->')
    parts.append('  <circle cx="0" cy="0" r="75.0" class="laser-cut" />')
    parts.append('  <circle cx="0" cy="0" r="1.6" class="laser-cut" />')
    parts.append('  <circle cx="0" cy="0" r="75.0" class="bg" />')

    # Tactical rim
    parts.append(generate_tactical_rim())

    # Titles
    parts.append('  <text x="0" y="-46.0" class="title-text">WEG A: NORMIERTE POLAREN (RATIO)</text>')
    parts.append('  <text x="0" y="-42.5" class="sub-text">Windpol (0,0) | L = 64 mm | JPK 1080 TRUE GRIT</text>')
    parts.append('  <text x="0" y="-39.5" class="bias-text">Taktik: TWD · Shift/Lift · Tack · Start Line Bias · Gybe</text>')

    # Concentric Ratio circles
    for ratio in [0.2, 0.4, 0.6, 0.8, 1.0]:
        r = ratio * L
        parts.append(f'  <circle cx="0" cy="0" r="{r:.2f}" class="grid-line" />')
        parts.append(f'  <text x="{r - 1.2:.2f}" y="-1.5" class="grid-text">{ratio:.1f}</text>')

    # Baseline OP1 down to (0, L)
    parts.append(f'  <line x1="0" y1="0" x2="0" y2="{L:.2f}" stroke="#C0392B" stroke-width="1.1" stroke-linecap="round" />')
    parts.append(f'  <circle cx="0" cy="{L:.2f}" r="1.4" fill="#C0392B" />')
    parts.append(f'  <text x="0" y="{L - 2.5:.2f}" class="awa-label" font-weight="bold" fill="#C0392B">P1 (180°)</text>')
    parts.append(f'  <text x="0" y="-3.2" class="awa-label" font-weight="bold" fill="#C0392B">Windpol (0,0)</text>')

    # AWA Fasskreise
    awa_angles = [25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 75.0, 90.0, 110.0, 135.0, 155.0]
    for alpha in awa_angles:
        rad = math.radians(alpha)
        sin_a = math.sin(rad)
        cos_a = math.cos(rad)
        if sin_a == 0:
            continue
        r_c = L / (2.0 * sin_a)
        ym = L / 2.0
        xc_stb = (L / 2.0) * (cos_a / sin_a)

        theta_limit = 180.0 - alpha
        n_pts = 90
        thetas = np.linspace(-math.radians(theta_limit), math.radians(theta_limit), n_pts)
        raw_pts_stb = [(xc_stb + r_c * math.cos(t), ym + r_c * math.sin(t)) for t in thetas]

        for side in [1, -1]:
            pts_side = [(side * p[0], p[1]) for p in raw_pts_stb]
            sub_paths = clip_polyline_to_circle(pts_side, r_clip)
            for sub in sub_paths:
                if len(sub) >= 2:
                    d_str = "M " + " ".join([f"{p[0]:.2f} {p[1]:.2f}" for p in sub])
                    parts.append(f'  <path d="{d_str}" class="awa-line" />')

            if side > 0 and sub_paths and alpha in [30.0, 40.0, 50.0, 60.0, 75.0, 90.0, 110.0, 135.0]:
                main_sub = max(sub_paths, key=len)
                if len(main_sub) >= 4:
                    idx_lbl = len(main_sub) // 2 if alpha <= 50.0 else len(main_sub) * 3 // 5
                    lbl_p = main_sub[min(idx_lbl, len(main_sub) - 1)]
                    parts.append(f'  <text x="{lbl_p[0]:.2f}" y="{lbl_p[1]:.2f}" class="awa-label">{int(alpha)}°</text>')

    # ORC Polars JPK 1080
    colors = [
        "#1F618D", "#2980B9", "#2471A3", "#17A589",
        "#138D75", "#D4AC0D", "#CA6F1E", "#922B21"
    ]
    crossover_pts_stbd = []
    crossover_pts_port = []

    for idx, tws in enumerate(polar.tws_list):
        col = colors[idx % len(colors)]
        curve = polar.curves_raw[idx]
        pts_complex = []

        for pt in curve:
            twa = pt["twa"]
            ratio = pt["bsp"] / tws
            r_mm = ratio * L
            rad = math.radians(twa)
            pts_complex.append(complex(r_mm * math.sin(rad), -r_mm * math.cos(rad)))

        smooth_pts = catmull_rom_spline(pts_complex, num_points=12)
        d_stb = "M " + " ".join([f"{p.real:.2f} {p.imag:.2f}" for p in smooth_pts])
        d_bb = "M " + " ".join([f"{-p.real:.2f} {p.imag:.2f}" for p in smooth_pts])
        parts.append(f'  <path d="{d_stb}" class="polar-curve" stroke="{col}" />')
        parts.append(f'  <path d="{d_bb}" class="polar-curve" stroke="{col}" />')

        if smooth_pts:
            end_p = smooth_pts[int(len(smooth_pts) * 0.65)]
            parts.append(f'  <text x="{end_p.real + 1.2:.2f}" y="{end_p.imag:.2f}" class="polar-label" fill="{col}">{int(tws)}k</text>')

        # VMG TARGETS: Beat & Run
        tgt = polar.vmg_targets[idx]
        beat_r = (tgt["beat_sog"] / tws) * L
        bx_stb, by_stb = polar_to_cart(beat_r, tgt["beat_angle"])
        for bx, by in [(bx_stb, by_stb), (-bx_stb, by_stb)]:
            parts.append(
                f'  <polygon points="{bx:.2f},{by-1.1:.2f} {bx+1.1:.2f},{by:.2f} {bx:.2f},{by+1.1:.2f} {bx-1.1:.2f},{by:.2f}" class="vmg-beat" />'
            )

        run_r = (tgt["run_sog"] / tws) * L
        rx_stb, ry_stb = polar_to_cart(run_r, tgt["gybe_angle"])
        for rx, ry in [(rx_stb, ry_stb), (-rx_stb, ry_stb)]:
            parts.append(
                f'  <polygon points="{rx:.2f},{ry-1.1:.2f} {rx+1.1:.2f},{ry:.2f} {rx:.2f},{ry+1.1:.2f} {rx-1.1:.2f},{ry:.2f}" class="vmg-run" />'
            )

        # SAIL CROSSOVER POINT
        jib_pts = {pt["twa"]: pt["bsp"] for pt in polar.sail_polars.get("Jib", {}).get(tws, [])}
        asym_pts = {pt["twa"]: pt["bsp"] for pt in polar.sail_polars.get("AsymCL", {}).get(tws, [])}
        common_twas = sorted(set(jib_pts.keys()) & set(asym_pts.keys()))
        cross_twa = 110.0 if tws >= 20.0 else None
        for i in range(len(common_twas) - 1):
            t1, t2 = common_twas[i], common_twas[i+1]
            diff1 = asym_pts[t1] - jib_pts[t1]
            diff2 = asym_pts[t2] - jib_pts[t2]
            if diff1 <= 0 and diff2 >= 0:
                frac = (-diff1) / (diff2 - diff1) if diff2 != diff1 else 0.5
                cross_twa = t1 + frac * (t2 - t1)
                break

        if cross_twa:
            inter = find_ray_spline_intersection(cross_twa, smooth_pts, sign_y=-1.0)
            if inter:
                cx_stb, cy_stb = inter
                crossover_pts_stbd.append((cx_stb, cy_stb))
                crossover_pts_port.append((-cx_stb, cy_stb))
                r_tri = 1.2
                for cx, cy in [(cx_stb, cy_stb), (-cx_stb, cy_stb)]:
                    p1 = (cx, cy - r_tri)
                    p2 = (cx + r_tri * math.sqrt(3)/2, cy + r_tri / 2.0)
                    p3 = (cx - r_tri * math.sqrt(3)/2, cy + r_tri / 2.0)
                    parts.append(
                        f'  <polygon points="{p1[0]:.2f},{p1[1]:.2f} {p2[0]:.2f},{p2[1]:.2f} {p3[0]:.2f},{p3[1]:.2f}" class="crossover-marker" />'
                    )

    # Crossover line
    if len(crossover_pts_stbd) >= 2:
        parts.append('  <path d="M ' + " ".join([f"{p[0]:.2f} {p[1]:.2f}" for p in crossover_pts_stbd]) + '" class="crossover-line" />')
        parts.append('  <path d="M ' + " ".join([f"{p[0]:.2f} {p[1]:.2f}" for p in crossover_pts_port]) + '" class="crossover-line" />')
        lbl_p = crossover_pts_stbd[len(crossover_pts_stbd) // 2]
        parts.append(f'  <text x="{lbl_p[0] + 1.5:.2f}" y="{lbl_p[1] + 1.0:.2f}" class="crossover-text">GENNAKER / SPI</text>')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_seite_a_deckel(output_file: Path):
    """Generates 360° Compass Rose Stator Cover (Ø 150 - 180 mm)."""
    parts = [svg_header(190.0, 190.0)]
    parts.append('  <!-- Cut lines (Red) -->')
    parts.append('  <circle cx="0" cy="0" r="90.0" class="laser-cut" />')
    parts.append('  <circle cx="0" cy="0" r="75.0" class="laser-cut" />')

    # 6 M3 holes on PCD Ø 176 mm
    for i in range(6):
        ang = math.radians(i * 60.0)
        sx = 88.0 * math.cos(ang)
        sy = 88.0 * math.sin(ang)
        parts.append(f'  <circle cx="{sx:.2f}" cy="{sy:.2f}" r="1.6" class="laser-cut" />')

    # 360° Compass Rose graduation
    r_outer = 87.5
    for deg in range(360):
        is_10 = (deg % 10 == 0)
        is_5 = (deg % 5 == 0)
        t_len = 3.5 if is_10 else (2.2 if is_5 else 1.2)

        p1 = polar_to_cart(r_outer, deg)
        p2 = polar_to_cart(r_outer - t_len, deg)
        parts.append(f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" class="laser-engrave" />')

        if is_10:
            pt = polar_to_cart(r_outer - 5.5, deg)
            lbl = f"{deg:03d}°" if deg > 0 else "000°"
            rot = deg if deg <= 180 else deg - 180
            parts.append(f'  <text x="{pt[0]:.2f}" y="{pt[1]:.2f}" class="compass-text" font-size="2.4px" transform="rotate({rot} {pt[0]:.2f} {pt[1]:.2f})">{lbl}</text>')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_seite_b_rotor(output_file: Path):
    """Generates Back Rotor: C-Scale, S-Scale, Performance Nonius (Ø 150 mm)."""
    parts = [svg_header(180.0, 180.0)]
    parts.append('  <!-- Cut lines (Red) -->')
    parts.append('  <circle cx="0" cy="0" r="75.0" class="laser-cut" />')
    parts.append('  <circle cx="0" cy="0" r="1.6" class="laser-cut" />')

    r_c = 74.5
    dash = 0.8

    # 1. Logarithmic C-Scale (1.0 to 10.0)
    for x in range(100, 1001):
        if x < 200:
            valid = (x % 1 == 0)
        elif x < 500:
            valid = (x % 2 == 0)
        else:
            valid = (x % 5 == 0)
        if not valid:
            continue

        deg = math.log10(x / 100.0) * 360.0
        f_len = 4.0 if (x in [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000]) else (2.5 if x % 10 == 0 else 1.5)

        p1 = polar_to_cart(r_c, deg)
        p2 = polar_to_cart(r_c - f_len * dash, deg)
        parts.append(f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" class="laser-engrave" />')

        if f_len >= 4.0:
            pt = polar_to_cart(r_c - 4.5, deg)
            txt = f"{x/100:.1f}" if x < 200 else f"{x//100}" if x % 100 == 0 else f"{x/100:.1f}"
            parts.append(f'  <text x="{pt[0]:.2f}" y="{pt[1]:.2f}" class="compass-text" font-size="2.2px">{txt}</text>')

    # 2. Logarithmic S-Scale (Sinus) at r = 48.0 mm
    r_s = 48.0
    parts.append(f'  <circle cx="0" cy="0" r="{r_s:.2f}" class="grid-line" />')
    parts.append(f'  <text x="0" y="{-r_s + 4.5:.2f}" class="title-text" font-size="2.6px">S (SINUS)</text>')

    s_labeled = [6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 50.0, 60.0, 70.0, 90.0]
    for alpha_int in range(60, 901, 5):
        alpha = alpha_int / 10.0
        val = 10.0 * math.sin(math.radians(alpha))
        if val <= 0:
            continue
        deg = math.log10(val) * 360.0

        is_maj = alpha in s_labeled
        t_len = 3.0 if is_maj else 1.5
        p1 = polar_to_cart(r_s, deg)
        p2 = polar_to_cart(r_s + t_len, deg)
        parts.append(f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" class="laser-engrave" stroke="#2980B9" />')

        if is_maj:
            pt = polar_to_cart(r_s + 4.5, deg)
            parts.append(f'  <text x="{pt[0]:.2f}" y="{pt[1]:.2f}" class="awa-label" font-size="2.0px">{int(alpha)}°</text>')

    # 3. Performance Nonius at 1.0 (0°)
    for pct in [-15, -10, -5, 5]:
        deg = math.log10(1.0 + pct / 100.0) * 360.0
        p1 = polar_to_cart(r_c, deg)
        p2 = polar_to_cart(r_c - 3.0, deg)
        col = "#27AE60" if pct > 0 else "#C0392B"
        parts.append(f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" stroke="{col}" stroke-width="0.5" />')
        pt = polar_to_cart(r_c - 4.5, deg)
        lbl = f"{pct:+d}%"
        parts.append(f'  <text x="{pt[0]:.2f}" y="{pt[1]:.2f}" font-family="sans-serif" font-size="1.8px" font-weight="bold" fill="{col}" text-anchor="middle">{lbl}</text>')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_seite_b_boden(output_file: Path):
    """Generates Back Stator Ring: D-Scale (Ø 150 - 180 mm)."""
    parts = [svg_header(190.0, 190.0)]
    parts.append('  <!-- Cut lines (Red) -->')
    parts.append('  <circle cx="0" cy="0" r="90.0" class="laser-cut" />')
    parts.append('  <circle cx="0" cy="0" r="75.0" class="laser-cut" />')

    for i in range(6):
        ang = math.radians(i * 60.0)
        sx = 88.0 * math.cos(ang)
        sy = 88.0 * math.sin(ang)
        parts.append(f'  <circle cx="{sx:.2f}" cy="{sy:.2f}" r="1.6" class="laser-cut" />')

    r_d = 75.5
    dash = 0.8
    for x in range(100, 1001):
        if x < 200:
            valid = (x % 1 == 0)
        elif x < 500:
            valid = (x % 2 == 0)
        else:
            valid = (x % 5 == 0)
        if not valid:
            continue

        deg = math.log10(x / 100.0) * 360.0
        f_len = 4.0 if (x in [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000]) else (2.5 if x % 10 == 0 else 1.5)

        p1 = polar_to_cart(r_d, deg)
        p2 = polar_to_cart(r_d + f_len * dash, deg)
        parts.append(f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" class="laser-engrave" />')

        if f_len >= 4.0:
            pt = polar_to_cart(r_d + 5.5, deg)
            txt = f"{x/100:.1f}" if x < 200 else f"{x//100}" if x % 100 == 0 else f"{x/100:.1f}"
            parts.append(f'  <text x="{pt[0]:.2f}" y="{pt[1]:.2f}" class="compass-text" font-size="2.2px">{txt}</text>')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_zeiger(output_file: Path):
    """Generates Central Ratio Pointer Arm cut & engraved scale."""
    length = 85.0
    width = 7.0
    hub_r = 5.0

    parts = [svg_header(40.0, 100.0)]
    # Red Cut line
    path = (
        f"M 0.0 {hub_r * 0.8:.2f} "
        f"L {width:.2f} {hub_r * 0.8:.2f} "
        f"L {width:.2f} 76.0 "
        f"L {width + 2.5:.2f} 78.0 "
        f"L {width:.2f} 80.0 "
        f"L 0.0 {length:.2f} "
        f"L 0.0 {hub_r:.2f} "
        f"A {hub_r} {hub_r} 0 1 1 0.0 {-hub_r:.2f} "
        f"A {hub_r} {hub_r} 0 0 1 0.0 {hub_r * 0.8:.2f} Z"
    )
    parts.append(f'  <path d="{path}" class="laser-cut" />')
    parts.append('  <circle cx="0" cy="0" r="1.6" class="laser-cut" />')

    # Engraved Ratio Scale along x = 0 (L = 64 mm)
    L = 64.0
    for r_idx in range(0, 13):
        ratio = r_idx * 0.1
        y_pos = ratio * L
        tick_w = 2.5 if r_idx % 2 == 0 else 1.4
        parts.append(f'  <line x1="0" y1="{y_pos:.2f}" x2="{tick_w:.2f}" y2="{y_pos:.2f}" class="laser-engrave" />')
        if r_idx % 2 == 0:
            parts.append(f'  <text x="{tick_w + 1.2:.2f}" y="{y_pos:.2f}" font-family="sans-serif" font-size="2.0px" fill="#000000" dominant-baseline="central">{ratio:.1f}</text>')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_all_laser_svgs(polar: PolarData, out_dir: Path):
    """Generates all 5 manufacturing SVGs for laser cut & engrave."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "laser_seite_a_rotor_vorderseite.svg": lambda p: generate_laser_seite_a_rotor(polar, p),
        "laser_seite_a_deckel_kompassrose.svg": lambda p: generate_laser_seite_a_deckel(p),
        "laser_seite_b_rotor_rueckseite.svg": lambda p: generate_laser_seite_b_rotor(p),
        "laser_seite_b_boden_d_skala.svg": lambda p: generate_laser_seite_b_boden(p),
        "laser_zentralzeiger.svg": lambda p: generate_laser_zeiger(p),
    }

    generated = []
    for fname, gen_func in files.items():
        fpath = out_dir / fname
        gen_func(fpath)
        generated.append(fpath)

    return generated
