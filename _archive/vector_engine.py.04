#!/usr/bin/env python3
"""
vector_engine.py - Parametrische CAM- / Laser-Vektorengine (SVG) für die Rechenscheibe
Yacht: JPK 1080 (GER 7447 - TRUE GRIT)

Architektur & Standards:
- Zentrale Geometrie und Layerkonfiguration über `config_manager.py` (Single Source of Truth).
- Mathematisch konsistente Vektoralgebra mit `cmath` (komplexe Zahlen für 2D-Punkte, Vektorclipping und Schnittpunkte).
- Laser-Fertigungsstandards:
  * Schneidlinien (Cut):   stroke="#E74C3C", stroke-width="0.20"
  * Gravurlinien (Engrave): stroke-width="0.30" bis "0.70" je nach Layer
  * Gravurtext:            dominant-baseline="central", exakte Tangenten- und Radialausrichtung
- Vollständig geschlossene Bogen- und Ringkorridore (korrekte SVG Arc-Sweep-Flags).
"""

import math
import cmath
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import numpy as np

from config_manager import CONFIG, GEOM
from polar_parser import PolarData, catmull_rom_spline


# ==============================================================================
# 1. VEKTOR- & KOMPLEXE MATHEMATIK (cmath)
# ==============================================================================

def polar_to_complex(r: float, deg_nautical: float) -> complex:
    """
    Konvertiert nautische Polarkoordinaten in kartesische SVG-Koordinaten als komplexe Zahl:
    - 0° ist Nord (12 Uhr, -Y in SVG)
    - 90° ist Ost (3 Uhr, +X in SVG)
    - 180° ist Süd (6 Uhr, +Y in SVG)
    - 270° ist West (9 Uhr, -X in SVG)
    Drehung erfolgt im Uhrzeigersinn.
    """
    rad = math.radians(deg_nautical)
    return complex(r * math.sin(rad), -r * math.cos(rad))


def calc_readable_rotation(deg: float) -> float:
    """
    Standard-Nautik-Konvention für lesbaren Text auf Zifferblättern:
    Verhindert, dass Zahlen in der unteren Scheibenhälfte auf dem Kopf stehen.
    """
    deg_norm = deg % 360.0
    if 90.0 < deg_norm < 270.0:
        return deg_norm - 180.0
    else:
        return deg_norm


def find_circle_intersection(p1: complex, p2: complex, r_max: float) -> Optional[complex]:
    """
    Berechnet den Schnittpunkt des Geradensegments p1 -> p2 mit dem Begrenzungskreis |z| = r_max
    unter Verwendung nativer komplexer Algebra:
      |p1 + t * dp|^2 = r_max^2
      => |dp|^2 * t^2 + 2 * Re(p1 * dp*) * t + (|p1|^2 - r_max^2) = 0
    """
    dp = p2 - p1
    a = abs(dp)**2
    if a < 1e-9:
        return None
    b = 2.0 * (p1 * dp.conjugate()).real
    c = abs(p1)**2 - r_max**2
    disc = b**2 - 4.0 * a * c
    if disc < 0:
        return None
    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / (2.0 * a)
    t2 = (-b + sqrt_disc) / (2.0 * a)
    valid_t = [t for t in (t1, t2) if 0.0 <= t <= 1.0]
    if not valid_t:
        return None
    return p1 + valid_t[0] * dp


def clip_polyline_to_circle(pts: List[complex], r_max: float) -> List[List[complex]]:
    """
    Schneidet einen Polygonzug (z. B. Polarkurven oder Fasskreise) am Kreis r_max ab.
    Gibt eine Liste zusammenhängender Segmente zurück, die vollständig innerhalb des Kreises liegen.
    """
    lines = []
    current_line = []
    for i in range(len(pts) - 1):
        p1, p2 = pts[i], pts[i + 1]
        d1 = abs(p1)
        d2 = abs(p2)

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


def find_ray_spline_intersection(ray_angle_deg: float, spline_pts: List[complex], sign_y: float = -1.0) -> Optional[complex]:
    """
    Berechnet den Schnittpunkt eines radialen Peilstrahls (z. B. Crossover-Winkel)
    mit einem Spline-Polygonzug im komplexen Raum via 2D-Kreuzprodukt.
    """
    rad = math.radians(ray_angle_deg)
    ray_dir = complex(math.sin(rad), sign_y * math.cos(rad))

    for i in range(len(spline_pts) - 1):
        p1 = spline_pts[i]
        p2 = spline_pts[i + 1]
        dp = p2 - p1
        # 2D Kreuzprodukt: (dp* * ray_dir).imag = dp.real * ray_dir.imag - dp.imag * ray_dir.real
        denom = (dp.conjugate() * ray_dir).imag
        if abs(denom) < 1e-9:
            continue
        t = (p1.conjugate() * ray_dir).imag / denom
        if 0.0 <= t <= 1.0:
            p_inter = p1 + t * dp
            s = (p_inter * ray_dir.conjugate()).real
            if s > 0:
                return p_inter
    return None


# ==============================================================================
# 2. SVG-HEADER & DYNAMISCHE STIL-DEFINITIONEN
# ==============================================================================

def svg_header(width_mm: float = 190.0, height_mm: float = 190.0) -> str:
    """
    Erzeugt den W3C-konformen SVG-Header mit millimetergenauer Skalierung
    und dynamischer Einbindung aller Laser-/CAM-Klassen aus config.json.
    """
    half_w = width_mm / 2.0
    half_h = height_mm / 2.0
    layers = CONFIG.layers
    typo = CONFIG.typography

    f_fam = typo.get("font_family", "sans-serif")
    c_cut_out = layers.get("cut_outer", {}).get("color", "#E74C3C")
    w_cut_out = layers.get("cut_outer", {}).get("stroke_width", 0.20)
    c_cut_in = layers.get("cut_inner", {}).get("color", "#C0392B")
    w_cut_in = layers.get("cut_inner", {}).get("stroke_width", 0.20)
    c_comp = layers.get("engrave_compass", {}).get("color", "#2C3E50")
    w_comp = layers.get("engrave_compass", {}).get("stroke_width", 0.35)
    c_awa = layers.get("engrave_awa", {}).get("color", "#2980B9")
    w_awa = layers.get("engrave_awa", {}).get("stroke_width", 0.40)
    d_awa = layers.get("engrave_awa", {}).get("dasharray", "2.5,1.2")
    w_polar = layers.get("engrave_polars", {}).get("stroke_width", 0.70)
    c_grid_maj = layers.get("engrave_grid_major", {}).get("color", "#BDC3C7")
    w_grid_maj = layers.get("engrave_grid_major", {}).get("stroke_width", 0.50)
    d_grid_maj = layers.get("engrave_grid_major", {}).get("dasharray", "2.0,1.5")
    c_grid_min = layers.get("engrave_grid_minor", {}).get("color", "#E5E7E9")
    w_grid_min = layers.get("engrave_grid_minor", {}).get("stroke_width", 0.30)
    d_grid_min = layers.get("engrave_grid_minor", {}).get("dasharray", "1.0,1.2")

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_mm}mm" height="{height_mm}mm" '
        f'viewBox="{-half_w:.2f} {-half_h:.2f} {width_mm:.2f} {height_mm:.2f}">\n'
        f'  <defs>\n'
        f'    <style>\n'
        f'      .laser-cut {{ fill: none; stroke: {c_cut_out}; stroke-width: {w_cut_out}; stroke-linecap: round; }}\n'
        f'      .laser-cut-inner {{ fill: none; stroke: {c_cut_in}; stroke-width: {w_cut_in}; stroke-linecap: round; }}\n'
        f'      .laser-engrave {{ fill: none; stroke: {c_comp}; stroke-width: {w_comp}; }}\n'
        f'      .grid-line {{ fill: none; stroke: {c_grid_maj}; stroke-width: {w_grid_maj}; stroke-dasharray: {d_grid_maj}; }}\n'
        f'      .grid-line-minor {{ fill: none; stroke: {c_grid_min}; stroke-width: {w_grid_min}; stroke-dasharray: {d_grid_min}; }}\n'
        f'      .grid-text {{ font-family: {f_fam}; font-size: {typo.get("grid_text_size_px", 1.9)}px; fill: #2C3E50; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .compass-tick {{ stroke: {c_comp}; stroke-width: {w_comp}; }}\n'
        f'      .compass-text {{ font-family: {f_fam}; font-weight: bold; font-size: {typo.get("compass_text_size_px", 2.4)}px; fill: {c_comp}; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .polar-curve {{ fill: none; stroke-width: {w_polar}; }}\n'
        f'      .polar-label {{ font-family: {f_fam}; font-weight: bold; font-size: {typo.get("polar_label_size_px", 2.3)}px; dominant-baseline: central; }}\n'
        f'      .awa-line {{ fill: none; stroke: {c_awa}; stroke-width: {w_awa}; stroke-dasharray: {d_awa}; }}\n'
        f'      .awa-label {{ font-family: {f_fam}; font-size: {typo.get("awa_label_size_px", 2.0)}px; fill: #1B4F72; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .title-text {{ font-family: {f_fam}; font-weight: bold; font-size: {typo.get("title_size_px", 2.8)}px; fill: #2C3E50; text-anchor: middle; }}\n'
        f'      .sub-text {{ font-family: {f_fam}; font-size: {typo.get("sub_size_px", 1.8)}px; fill: #7F8C8D; text-anchor: middle; }}\n'
        f'      .shift-indicator {{ font-family: {f_fam}; font-weight: bold; font-size: 2.2px; dominant-baseline: central; text-anchor: middle; }}\n'
        f'      .sector-beat-stbd {{ fill: #2ECC71; fill-opacity: 0.22; stroke: #27AE60; stroke-width: 0.45; }}\n'
        f'      .sector-beat-port {{ fill: #E74C3C; fill-opacity: 0.22; stroke: #C0392B; stroke-width: 0.45; }}\n'
        f'      .sector-gybe-stbd {{ fill: #2ECC71; fill-opacity: 0.22; stroke: #27AE60; stroke-width: 0.45; }}\n'
        f'      .sector-gybe-port {{ fill: #E74C3C; fill-opacity: 0.22; stroke: #C0392B; stroke-width: 0.45; }}\n'
        f'      .start-line {{ stroke: #2980B9; stroke-width: 1.2; }}\n'
        f'      .bias-tick {{ stroke: #2980B9; stroke-width: 0.4; }}\n'
        f'      .bias-text {{ font-family: {f_fam}; font-size: 1.9px; fill: #2980B9; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .bias-subtext-green {{ font-family: {f_fam}; font-weight: bold; font-size: 1.9px; fill: #27AE60; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .bias-subtext-red {{ font-family: {f_fam}; font-weight: bold; font-size: 1.9px; fill: #C0392B; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .tack-label-stbd {{ font-family: {f_fam}; font-weight: bold; font-size: 2.3px; fill: #27AE60; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .tack-label-port {{ font-family: {f_fam}; font-weight: bold; font-size: 2.3px; fill: #C0392B; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .gybe-label-stbd {{ font-family: {f_fam}; font-weight: bold; font-size: 2.3px; fill: #27AE60; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .gybe-label-port {{ font-family: {f_fam}; font-weight: bold; font-size: 2.3px; fill: #C0392B; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .line-label {{ font-family: {f_fam}; font-weight: bold; font-size: 2.2px; fill: #2980B9; text-anchor: middle; dominant-baseline: central; }}\n'
        f'      .vmg-beat {{ fill: #E74C3C; stroke: #962D22; stroke-width: 0.3; }}\n'
        f'      .vmg-run {{ fill: #2ECC71; stroke: #27AE60; stroke-width: 0.3; }}\n'
        f'      .crossover-marker {{ fill: #9B59B6; stroke: #8E44AD; stroke-width: 0.35; }}\n'
        f'      .crossover-line {{ fill: none; stroke: #8E44AD; stroke-width: 0.60; stroke-dasharray: 2.0,1.4; }}\n'
        f'      .crossover-text {{ font-family: {f_fam}; font-weight: bold; font-size: 2.0px; fill: #8E44AD; }}\n'
        f'      .stator-rim {{ fill: #F8F9F9; stroke: #2C3E50; stroke-width: 0.6; }}\n'
        f'    </style>\n'
        f'  </defs>\n'
    )


# ==============================================================================
# 3. TACKINGMASTER-TAKTIKRING ELEMENTE (ROTOR RAND)
# ==============================================================================

def generate_tactical_rim() -> str:
    """
    Generiert alle TackingMaster-Taktikelemente für den Rotor (Radius r in [66.0, 75.0]):
    1. TRUE WIND Pfeil & Winddreher-Skalen (Shift / Lift ±15°)
    2. TACK-Wendekorridore (38° bis 42°) - geometrisch korrigierte Sweep-Flags
    3. START LINE BIAS System (±90° mit Boat End / Pin End Badges)
    4. GYBE-Halsenkorridore (145° bis 165°) - geometrisch korrigierte Sweep-Flags
    5. Freisektor-Kompassmarkierungen (5°-Teilung, 30°/60°/120°-Beschriftungen)
    """
    elements = []
    r_outer = GEOM.rotor_radius                # 75.0 mm
    r_inner = GEOM.tactical_rim_inner_radius   # 66.0 mm

    # 1. TRUE WIND Pfeil (12 Uhr) & Lift/Header
    p_tip = polar_to_complex(r_outer - 0.4, 0.0)
    p_l = polar_to_complex(r_outer - 6.2, -2.0)
    p_r = polar_to_complex(r_outer - 6.2, 2.0)
    p_c = polar_to_complex(r_outer - 4.8, 0.0)

    elements.append(
        f'  <polygon points="{p_tip.real:.2f},{p_tip.imag:.2f} {p_l.real:.2f},{p_l.imag:.2f} '
        f'{p_c.real:.2f},{p_c.imag:.2f} {p_r.real:.2f},{p_r.imag:.2f}" '
        f'fill="#C0392B" stroke="#962D22" stroke-width="0.3" />'
    )
    elements.append(
        f'  <text x="0" y="{-r_outer + 8.2:.2f}" font-family="sans-serif" font-weight="bold" '
        f'font-size="2.6px" fill="#C0392B" text-anchor="middle">TRUE WIND</text>'
    )
    elements.append(
        f'  <text x="0" y="{-r_inner + 0.8:.2f}" font-family="sans-serif" font-weight="bold" '
        f'font-size="1.9px" fill="#27AE60" text-anchor="middle">◄ PORT LIFT | STBD LIFT ►</text>'
    )

    # Shift / Lift Teilstriche
    for side in [1, -1]:
        for shift_deg in [5.0, 10.0, 15.0]:
            d = shift_deg * side
            p1 = polar_to_complex(r_outer, d)
            p2 = polar_to_complex(r_outer - 2.2, d)
            elements.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" class="compass-tick" />')
            pt = polar_to_complex(r_outer - 3.8, d)
            elements.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="bias-text">{int(shift_deg)}°</text>')

        p_lbl = polar_to_complex(r_inner + 1.8, 11.5 * side)
        rot = 11.5 if side > 0 else -11.5
        txt = "LIFT ▶" if side > 0 else "◀ LIFT"
        elements.append(
            f'  <text x="{p_lbl.real:.2f}" y="{p_lbl.imag:.2f}" class="shift-indicator" fill="#27AE60" '
            f'transform="rotate({rot:.1f} {p_lbl.real:.2f} {p_lbl.imag:.2f})">{txt}</text>'
        )

    # 2. TACK-Wendekorridore (38° bis 42°)
    for side in [1, -1]:
        a1, a2 = 38.0 * side, 42.0 * side
        if side < 0:
            a1, a2 = a2, a1  # a1 < a2 sicherstellen

        p1_in = polar_to_complex(r_inner, a1)
        p2_in = polar_to_complex(r_inner, a2)
        p1_out = polar_to_complex(r_outer, a1)
        p2_out = polar_to_complex(r_outer, a2)

        # SVG: Außenbogen im Uhrzeigersinn (sweep=1), Innenbogen gegen Uhrzeigersinn (sweep=0)
        path = (
            f"M {p1_in.real:.2f} {p1_in.imag:.2f} "
            f"L {p1_out.real:.2f} {p1_out.imag:.2f} "
            f"A {r_outer} {r_outer} 0 0 1 {p2_out.real:.2f} {p2_out.imag:.2f} "
            f"L {p2_in.real:.2f} {p2_in.imag:.2f} "
            f"A {r_inner} {r_inner} 0 0 0 {p1_in.real:.2f} {p1_in.imag:.2f} Z"
        )
        sector_cls = "sector-beat-stbd" if side > 0 else "sector-beat-port"
        elements.append(f'  <path d="{path}" class="{sector_cls}" />')

        p_lbl = polar_to_complex(r_inner + 4.5, 40.0 * side)
        rot = 40.0 if side > 0 else -40.0
        lbl_txt = "STBD TACK 40°" if side > 0 else "PORT TACK 40°"
        lbl_cls = "tack-label-stbd" if side > 0 else "tack-label-port"
        elements.append(
            f'  <text x="{p_lbl.real:.2f}" y="{p_lbl.imag:.2f}" class="{lbl_cls}" '
            f'transform="rotate({rot:.1f} {p_lbl.real:.2f} {p_lbl.imag:.2f})">{lbl_txt}</text>'
        )

    # 3. Start Line Bias System (±90°)
    for side in [1, -1]:
        base_angle = 90.0 * side
        p_in = polar_to_complex(r_inner, base_angle)
        p_out = polar_to_complex(r_outer, base_angle)
        elements.append(f'  <line x1="{p_in.real:.2f}" y1="{p_in.imag:.2f}" x2="{p_out.real:.2f}" y2="{p_out.imag:.2f}" class="start-line" />')

        for b_deg in [5.0, 10.0, 15.0]:
            for s_sgn in [1, -1]:
                b_ang = base_angle + (b_deg * s_sgn)
                pt1 = polar_to_complex(r_outer, b_ang)
                pt2 = polar_to_complex(r_outer - 2.2, b_ang)
                elements.append(f'  <line x1="{pt1.real:.2f}" y1="{pt1.imag:.2f}" x2="{pt2.real:.2f}" y2="{pt2.imag:.2f}" class="bias-tick" />')
                pt_txt = polar_to_complex(r_outer - 3.8, b_ang)
                elements.append(f'  <text x="{pt_txt.real:.2f}" y="{pt_txt.imag:.2f}" class="bias-text">{int(b_deg)}°</text>')

        p_center = polar_to_complex(r_inner + 4.5, base_angle)
        badge_w = 4.8
        badge_h = 19.0 if side > 0 else 13.5
        rot_main = 90.0 if side > 0 else -90.0
        line_name = "BOAT END (RC)" if side > 0 else "PIN END"

        elements.append(
            f'  <rect x="{p_center.real - badge_w/2:.2f}" y="{p_center.imag - badge_h/2:.2f}" '
            f'width="{badge_w}" height="{badge_h}" rx="1.2" fill="#FFFFFF" stroke="#2980B9" stroke-width="0.5" '
            f'transform="rotate({rot_main} {p_center.real:.2f} {p_center.imag:.2f})" />'
        )
        elements.append(
            f'  <text x="{p_center.real:.2f}" y="{p_center.imag:.2f}" class="line-label" '
            f'transform="rotate({rot_main} {p_center.real:.2f} {p_center.imag:.2f})">{line_name}</text>'
        )

        # Luv- und Lee-Vorteilsanzeiger
        upwind_ang = base_angle - (9.5 * side)
        p_up = polar_to_complex(r_inner + 1.8, upwind_ang)
        fav_up_txt = "▲ BOAT FAV" if side > 0 else "PIN FAV ▲"
        rot_up = calc_readable_rotation(upwind_ang)
        elements.append(
            f'  <text x="{p_up.real:.2f}" y="{p_up.imag:.2f}" class="bias-subtext-green" '
            f'transform="rotate({rot_up:.1f} {p_up.real:.2f} {p_up.imag:.2f})">{fav_up_txt}</text>'
        )

        downwind_ang = base_angle + (9.5 * side)
        p_down = polar_to_complex(r_inner + 1.8, downwind_ang)
        fav_down_txt = "PIN FAV ▼" if side > 0 else "▼ BOAT FAV"
        rot_down = calc_readable_rotation(downwind_ang)
        elements.append(
            f'  <text x="{p_down.real:.2f}" y="{p_down.imag:.2f}" class="bias-subtext-red" '
            f'transform="rotate({rot_down:.1f} {p_down.real:.2f} {p_down.imag:.2f})">{fav_down_txt}</text>'
        )

    # 4. GYBE-Halsenkorridore (145° bis 165°)
    for side in [1, -1]:
        a1, a2 = 145.0 * side, 165.0 * side
        if side < 0:
            a1, a2 = a2, a1  # a1 < a2 sicherstellen

        p1_in = polar_to_complex(r_inner, a1)
        p2_in = polar_to_complex(r_inner, a2)
        p1_out = polar_to_complex(r_outer, a1)
        p2_out = polar_to_complex(r_outer, a2)

        # Außenbogen im Uhrzeigersinn (sweep=1), Innenbogen gegen Uhrzeigersinn (sweep=0)
        path = (
            f"M {p1_in.real:.2f} {p1_in.imag:.2f} "
            f"L {p1_out.real:.2f} {p1_out.imag:.2f} "
            f"A {r_outer} {r_outer} 0 0 1 {p2_out.real:.2f} {p2_out.imag:.2f} "
            f"L {p2_in.real:.2f} {p2_in.imag:.2f} "
            f"A {r_inner} {r_inner} 0 0 0 {p1_in.real:.2f} {p1_in.imag:.2f} Z"
        )
        sector_cls = "sector-gybe-stbd" if side > 0 else "sector-gybe-port"
        elements.append(f'  <path d="{path}" class="{sector_cls}" />')

        p_lbl = polar_to_complex(r_inner + 4.5, 155.0 * side)
        rot = -25.0 if side > 0 else 25.0
        lbl_txt = "STBD GYBE 155°" if side > 0 else "PORT GYBE 155°"
        lbl_cls = "gybe-label-stbd" if side > 0 else "gybe-label-port"
        elements.append(
            f'  <text x="{p_lbl.real:.2f}" y="{p_lbl.imag:.2f}" class="{lbl_cls}" '
            f'transform="rotate({rot:.1f} {p_lbl.real:.2f} {p_lbl.imag:.2f})">{lbl_txt}</text>'
        )

    # 5. Freisektor-Kompassmarkierungen (5°-Teilung, 30°/60°/120°)
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
            t_len = 3.2 if is_30 else (2.2 if is_10 else 1.2)

            p1 = polar_to_complex(r_outer, d)
            p2 = polar_to_complex(r_outer - t_len, d)
            elements.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" class="compass-tick" />')

            if is_30:
                pt = polar_to_complex(r_outer - 4.5, d)
                rot = calc_readable_rotation(d)
                elements.append(
                    f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="compass-text" '
                    f'transform="rotate({rot:.1f} {pt.real:.2f} {pt.imag:.2f})">{deg}°</text>'
                )

    return "\n".join(elements)


# ==============================================================================
# 4. EINZELDATEI-GENERATOREN (CAM / LASER)
# ==============================================================================

def generate_laser_seite_a_rotor(output_file: Path, polar: PolarData):
    """
    Generiert die Laser-CAM-Vektordatei für die Mittelscheibe Vorderseite (Ø 150 mm).
    Features:
    - Schnittlinien: Außenrand R = 75.0 mm und zentrale Achsbohrung r = 1.6 mm.
    - TackingMaster-Taktikring auf r in [66.0, 75.0] mm.
    - 10 konzentrische Ratio-Kreise für BoatSPD (0.1 bis 1.0).
    - Feste BoatSPD / TWS-Skala entlang der 90°-Steuerbordachse mit Beschriftung bei y = -5.2 mm.
    - Rote vertikale Referenzlinie zum Gegenpol P1(180°) bei L = 64.0 mm.
    - ORC-Polaren für 8 Windstärken (6 bis 24 kt), ausgespart für |TWA| > 175°.
    - Symmetrische TWS-Beschriftung 1.0 mm innen neben den Upwind-Beat-Rauten.
    - AWA-Fasskreise für scheinbaren Wind.
    """
    L = GEOM.polar_norm_length
    r_rotor = GEOM.rotor_radius
    r_clip = r_rotor - 9.8  # 65.2 mm (innerhalb des Taktikrings)

    parts = [svg_header(180.0, 180.0)]
    parts.append('  <!-- Schnittlinien (Laser-Cut) -->')
    parts.append(f'  <circle cx="0" cy="0" r="{r_rotor:.2f}" class="laser-cut" />')
    parts.append(f'  <circle cx="0" cy="0" r="{GEOM.axle_hole_radius:.2f}" class="laser-cut-inner" />')

    # Taktikring
    parts.append('  <!-- TackingMaster Taktikring -->')
    parts.append(generate_tactical_rim())

    # Titel & Beschriftung
    parts.append('  <!-- Titel & Legende -->')
    parts.append(f'  <text x="0" y="-46.0" class="title-text">WEG A: NORMIERTE POLAREN (RATIO)</text>')
    parts.append(f'  <text x="0" y="-42.5" class="sub-text">Windpol (0,0) | L = {L:.1f} mm | JPK 1080 TRUE GRIT</text>')
    parts.append(f'  <text x="0" y="-39.5" class="sub-text" fill="#2980B9">Taktik: TWD · Shift/Lift · Tack · Start Line Bias · Gybe</text>')

    # 10 Konzentrische Ratio-Kreise
    parts.append('  <!-- Konzentrische Ratio-Kreise (BoatSPD / TWS) -->')
    for r_idx in range(1, 11):
        r_val = r_idx * 0.1 * L
        cls_name = "grid-line" if (r_idx % 2 == 0) else "grid-line-minor"
        parts.append(f'  <circle cx="0" cy="0" r="{r_val:.2f}" class="{cls_name}" />')

    # BoatSPD / TWS Skala auf Rotor (90° Steuerbord)
    parts.append('  <!-- Feste BoatSPD / TWS Skala auf 90° Steuerbordachse -->')
    parts.append(f'  <line x1="5.0" y1="0" x2="{L:.2f}" y2="0" stroke="#2C3E50" stroke-width="0.45" />')
    for r_idx in range(1, 11):
        ratio = r_idx * 0.1
        rx = ratio * L
        is_major = (r_idx % 2 == 0)
        tick_len = 2.0 if is_major else 1.2
        parts.append(f'  <line x1="{rx:.2f}" y1="{-tick_len:.2f}" x2="{rx:.2f}" y2="{tick_len:.2f}" stroke="#2C3E50" stroke-width="0.35" />')
        lbl_txt = f"{ratio:.1f}" if is_major else f".{r_idx}"
        parts.append(f'  <text x="{rx:.2f}" y="-2.2" class="grid-text" font-size="1.9px" fill="#2C3E50">{lbl_txt}</text>')
    parts.append(f'  <text x="{L/2.0:.2f}" y="-5.2" class="grid-text" font-size="2.0px" font-weight="bold" fill="#2C3E50">BoatSPD / TWS</text>')

    # Rote Basislinie OP1
    parts.append('  <!-- Rote Referenz-Basislinie OP1 -->')
    parts.append(f'  <line x1="0" y1="0" x2="0" y2="{L:.2f}" stroke="#C0392B" stroke-width="1.1" stroke-linecap="round" />')
    parts.append(f'  <circle cx="0" cy="{L:.2f}" r="1.4" fill="#C0392B" />')
    parts.append(f'  <text x="0" y="{L - 2.5:.2f}" class="awa-label" font-weight="bold" fill="#C0392B">P1 (180°)</text>')
    parts.append(f'  <text x="0" y="-3.2" class="awa-label" font-weight="bold" fill="#C0392B">Windpol (0,0)</text>')

    # AWA Fasskreise
    parts.append('  <!-- AWA Fasskreisbögen -->')
    awa_angles = CONFIG.tactical.get("awa_angles_deg", [25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 75.0, 90.0, 110.0, 135.0, 155.0])
    for alpha in awa_angles:
        rad = math.radians(alpha)
        sin_a = math.sin(rad)
        cos_a = math.cos(rad)
        if sin_a == 0:
            continue
        r_c = L / (2.0 * sin_a)
        ym = L / 2.0
        xc_stb = (L / 2.0) * (cos_a / sin_a)

        thetas = np.linspace(-math.radians(180.0 - alpha), math.radians(180.0 - alpha), 90)
        raw_stb = [complex(xc_stb + r_c * math.cos(t), ym + r_c * math.sin(t)) for t in thetas]

        for s in [1, -1]:
            pts_side = [complex(s * p.real, p.imag) for p in raw_stb]
            for sub in clip_polyline_to_circle(pts_side, r_clip):
                if len(sub) >= 2:
                    d_str = "M " + " ".join([f"{p.real:.2f} {p.imag:.2f}" for p in sub])
                    parts.append(f'  <path d="{d_str}" class="awa-line" />')

        # Beschriftung
        if alpha in [30.0, 45.0, 60.0, 90.0, 135.0]:
            p_lbl = polar_to_complex(r_clip - 1.2, alpha)
            parts.append(f'  <text x="{p_lbl.real:.2f}" y="{p_lbl.imag:.2f}" class="awa-label">{int(alpha)}°</text>')
            parts.append(f'  <text x="{-p_lbl.real:.2f}" y="{p_lbl.imag:.2f}" class="awa-label">{int(alpha)}°</text>')

    # ORC Polaren (JPK 1080)
    parts.append('  <!-- ORC Geschwindigkeitspolaren JPK 1080 -->')
    colors = CONFIG.polars.get("curve_colors", ["#1F618D", "#2980B9", "#2471A3", "#17A589", "#138D75", "#D4AC0D", "#CA6F1E", "#922B21"])
    cutoff_deg = float(CONFIG.polars.get("curve_cutoff_twa_deg", 175.0))
    crossover_stb, crossover_bb = [], []

    for idx, tws in enumerate(polar.tws_list):
        col = colors[idx % len(colors)]
        curve = polar.curves_raw[idx]
        pts_complex = []

        for i, pt in enumerate(curve):
            twa = pt["twa"]
            if twa <= cutoff_deg:
                p_c = polar_to_complex((pt["bsp"] / tws) * L, twa)
                pts_complex.append(p_c)
            else:
                if i > 0:
                    prev_pt = curve[i - 1]
                    if prev_pt["twa"] < cutoff_deg:
                        frac = (cutoff_deg - prev_pt["twa"]) / (twa - prev_pt["twa"])
                        bsp_cut = prev_pt["bsp"] + frac * (pt["bsp"] - prev_pt["bsp"])
                        pts_complex.append(polar_to_complex((bsp_cut / tws) * L, cutoff_deg))
                break

        smooth_pts = catmull_rom_spline(pts_complex, num_points=12)
        d_stb = "M " + " ".join([f"{p.real:.2f} {p.imag:.2f}" for p in smooth_pts])
        d_bb = "M " + " ".join([f"{-p.real:.2f} {p.imag:.2f}" for p in smooth_pts])
        parts.append(f'  <path d="{d_stb}" class="polar-curve" stroke="{col}" />')
        parts.append(f'  <path d="{d_bb}" class="polar-curve" stroke="{col}" />')

        # VMG TARGETS: Beat & Run
        tgt = polar.vmg_targets[idx]
        beat_r = (tgt["beat_sog"] / tws) * L
        p_beat = polar_to_complex(beat_r, tgt["beat_angle"])

        for bx in [p_beat.real, -p_beat.real]:
            by = p_beat.imag
            parts.append(
                f'  <polygon points="{bx:.2f},{by-1.1:.2f} {bx+1.1:.2f},{by:.2f} {bx:.2f},{by+1.1:.2f} {bx-1.1:.2f},{by:.2f}" class="vmg-beat" />'
            )

        # Symmetrische TWS-Labels 1.0 mm innen neben den Upwind-Beat-Rauten
        parts.append(f'  <text x="{p_beat.real - 2.1:.2f}" y="{p_beat.imag:.2f}" class="polar-label" text-anchor="end" fill="{col}">{int(tws)}</text>')
        parts.append(f'  <text x="{-p_beat.real + 2.1:.2f}" y="{p_beat.imag:.2f}" class="polar-label" text-anchor="start" fill="{col}">{int(tws)}</text>')

        run_r = (tgt["run_sog"] / tws) * L
        p_run = polar_to_complex(run_r, tgt["gybe_angle"])
        for rx in [p_run.real, -p_run.real]:
            ry = p_run.imag
            parts.append(
                f'  <polygon points="{rx:.2f},{ry-1.1:.2f} {rx+1.1:.2f},{ry:.2f} {rx:.2f},{ry+1.1:.2f} {rx-1.1:.2f},{ry:.2f}" class="vmg-run" />'
            )

        # Segel-Crossover (Jib vs. AsymCL)
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
                crossover_stb.append(inter)
                crossover_bb.append(complex(-inter.real, inter.imag))
                for cx in [inter.real, -inter.real]:
                    cy = inter.imag
                    parts.append(
                        f'  <polygon points="{cx:.2f},{cy-1.3:.2f} {cx+1.2:.2f},{cy+1.0:.2f} {cx-1.2:.2f},{cy+1.0:.2f}" class="crossover-marker" />'
                    )

    if len(crossover_stb) >= 2:
        d_c_stb = "M " + " ".join([f"{p.real:.2f} {p.imag:.2f}" for p in crossover_stb])
        d_c_bb = "M " + " ".join([f"{p.real:.2f} {p.imag:.2f}" for p in crossover_bb])
        parts.append(f'  <path d="{d_c_stb}" class="crossover-line" />')
        parts.append(f'  <path d="{d_c_bb}" class="crossover-line" />')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_seite_a_deckel(output_file: Path):
    """
    Generiert die Laser-CAM-Vektordatei für den Gehäusedeckel (Stator Vorderseite Ø 180 mm).
    Features:
    - Außenkontur Ø 180 mm (R = 90.0 mm), Sichtfenster Ø 150 mm (R = 75.0 mm).
    - 6 M3-Senkungsbohrungen auf Teilkreis PCD Ø 176 mm (R = 88.0 mm).
    - 360°-Kompassrose nach den neuen Vorgaben:
      * Teilstriche nach INNEN gerückt (R = 75.8 bis 79.2 mm).
      * 10°-Striche: 75.8 bis 79.2 mm (Länge 3.4 mm).
      * 5°-Striche:  77.0 bis 79.2 mm (Länge 2.2 mm).
      * 1°-Striche:  78.0 bis 79.2 mm (Länge 1.2 mm).
      * Gradbeschriftung ('000°' bis '350°') nach AUSSEN verlegt bei R = 82.5 mm.
    """
    r_out = GEOM.stator_outer_radius
    r_win = GEOM.stator_window_radius
    t_in = GEOM.stator_compass_ticks_inner   # 75.8 mm
    t_out = GEOM.stator_compass_ticks_outer  # 79.2 mm
    r_txt = GEOM.stator_compass_text_radius  # 82.5 mm

    parts = [svg_header(190.0, 190.0)]
    parts.append('  <!-- Schnittlinien (Laser-Cut) -->')
    parts.append(f'  <circle cx="0" cy="0" r="{r_out:.2f}" class="laser-cut" />')
    parts.append(f'  <circle cx="0" cy="0" r="{r_win:.2f}" class="laser-cut-inner" />')

    # 6 M3-Schraubenlöcher auf PCD Ø 176 mm
    for i in range(GEOM.screw_count):
        ang_deg = i * (360.0 / GEOM.screw_count)
        p_screw = polar_to_complex(GEOM.screw_pcd_radius, ang_deg)
        parts.append(f'  <circle cx="{p_screw.real:.2f}" cy="{p_screw.imag:.2f}" r="{GEOM.axle_hole_radius:.2f}" class="laser-cut" />')

    # 360° Kompassrose
    parts.append('  <!-- 360° Kompassrose auf Stator (Ticks innen, Ziffern außen) -->')
    for deg in range(360):
        is_10 = (deg % 10 == 0)
        is_5 = (deg % 5 == 0)
        tick_start_r = t_in if is_10 else (t_in + 1.2 if is_5 else t_in + 2.2)

        p1 = polar_to_complex(tick_start_r, deg)
        p2 = polar_to_complex(t_out, deg)
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" class="laser-engrave" />')

        if is_10:
            pt = polar_to_complex(r_txt, deg)
            lbl = f"{deg:03d}°" if deg > 0 else "000°"
            rot = calc_readable_rotation(deg)
            parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="compass-text" transform="rotate({rot:.1f} {pt.real:.2f} {pt.imag:.2f})">{lbl}</text>')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_seite_b_rotor(output_file: Path):
    """
    Generiert die Laser-CAM-Vektordatei für die Mittelscheibe Rückseite (Ø 150 mm).
    Features:
    - Schnittlinien: Außenrand R = 75.0 mm und zentrale Achsbohrung r = 1.6 mm.
    - Logarithmische C-Skala (1.0 bis 10.0) am Außenrand (R = 74.5 mm, Teilstriche nach innen).
    - Vergrößerte S-Sinusskala (R = 65.0 mm, Teilstriche nach innen, Gradzahlen bei 58.5 mm).
    - Performance-Nonius bei 1.0 (-15%, -10%, -5%, +5%).
    - Formeln für Winddreiecksberechnung und Nautik.
    """
    r_rotor = GEOM.rotor_radius
    r_c = GEOM.c_scale_radius
    r_s = GEOM.s_scale_radius
    dash = 0.8

    parts = [svg_header(180.0, 180.0)]
    parts.append('  <!-- Schnittlinien (Laser-Cut) -->')
    parts.append(f'  <circle cx="0" cy="0" r="{r_rotor:.2f}" class="laser-cut" />')
    parts.append(f'  <circle cx="0" cy="0" r="{GEOM.axle_hole_radius:.2f}" class="laser-cut-inner" />')

    # 1. Logarithmische C-Skala (1.0 bis 10.0)
    parts.append('  <!-- Logarithmische C-Skala auf Rotor Rückseite -->')
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

        p1 = polar_to_complex(r_c, deg)
        p2 = polar_to_complex(r_c - f_len * dash, deg)
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" class="laser-engrave" />')

        if f_len >= 4.0:
            pt = polar_to_complex(r_c - 4.5, deg)
            txt = f"{x/100:.1f}" if x < 200 else f"{x//100}" if x % 100 == 0 else f"{x/100:.1f}"
            parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="compass-text" font-size="2.2px">{txt}</text>')

    # 2. Vergrößerte Logarithmische S-Skala (Sinus) bei R = 65.0 mm
    parts.append('  <!-- Vergrößerte S-Sinusskala (R = 65.0 mm) -->')
    parts.append(f'  <circle cx="0" cy="0" r="{r_s:.2f}" class="grid-line" stroke="#2980B9" stroke-width="0.3" />')

    sin_angles = [
        6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
        22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 45, 50, 55, 60, 70, 80, 90
    ]
    for alpha in sin_angles:
        deg = math.log10(10.0 * math.sin(math.radians(alpha))) * 360.0
        is_labeled = alpha in [6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 35, 40, 50, 60, 70, 90]
        tick_len = 3.2 if is_labeled else 1.8

        p1 = polar_to_complex(r_s, deg)
        p2 = polar_to_complex(r_s - tick_len, deg)
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" stroke="#2980B9" stroke-width="0.35" />')

        if is_labeled:
            pt = polar_to_complex(r_s - 5.5, deg)
            rot = calc_readable_rotation(deg)
            parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="compass-text" font-size="2.0px" fill="#2980B9" transform="rotate({rot:.1f} {pt.real:.2f} {pt.imag:.2f})">{alpha}°</text>')

    # 3. Performance-Nonius bei 1.0 (0°)
    for pct in [-15, -10, -5, 5]:
        val = 1.0 + (pct / 100.0)
        deg = math.log10(val) * 360.0
        p1 = polar_to_complex(r_c, deg)
        p2 = polar_to_complex(r_c - 3.0, deg)
        col = "#27AE60" if pct > 0 else "#C0392B"
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" stroke="{col}" stroke-width="0.5" />')
        pt = polar_to_complex(r_c - 4.5, deg)
        lbl = f"{pct:+d}%"
        parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" font-family="sans-serif" font-size="1.8px" font-weight="bold" fill="{col}" text-anchor="middle">{lbl}</text>')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_seite_b_boden(output_file: Path):
    """
    Generiert die Laser-CAM-Vektordatei für den Gehäuseboden (Stator Rückseite Ø 180 mm).
    Features:
    - Schnittlinien: Außenrand R = 90.0 mm, Innenöffnung R = 75.0 mm.
    - 6 M3-Bohrungen auf Teilkreis PCD Ø 176 mm.
    - Logarithmische D-Skala (1.0 bis 10.0) entlang R = 75.5 mm (Teilstriche weisen nach außen).
    """
    r_out = GEOM.stator_outer_radius
    r_win = GEOM.stator_window_radius
    r_d = GEOM.d_scale_radius
    dash = 0.8

    parts = [svg_header(190.0, 190.0)]
    parts.append('  <!-- Schnittlinien (Laser-Cut) -->')
    parts.append(f'  <circle cx="0" cy="0" r="{r_out:.2f}" class="laser-cut" />')
    parts.append(f'  <circle cx="0" cy="0" r="{r_win:.2f}" class="laser-cut" />')

    # 6 M3-Schraubenlöcher
    for i in range(GEOM.screw_count):
        ang_deg = i * (360.0 / GEOM.screw_count)
        p_screw = polar_to_complex(GEOM.screw_pcd_radius, ang_deg)
        parts.append(f'  <circle cx="{p_screw.real:.2f}" cy="{p_screw.imag:.2f}" r="{GEOM.axle_hole_radius:.2f}" class="laser-cut" />')

    # D-Skala
    parts.append('  <!-- Logarithmische D-Skala auf Stator Boden -->')
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

        p1 = polar_to_complex(r_d, deg)
        p2 = polar_to_complex(r_d + f_len * dash, deg)
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" class="laser-engrave" />')

        if f_len >= 4.0:
            pt = polar_to_complex(r_d + 5.5, deg)
            txt = f"{x/100:.1f}" if x < 200 else f"{x//100}" if x % 100 == 0 else f"{x/100:.1f}"
            parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="compass-text" font-size="2.2px">{txt}</text>')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_zentralzeiger(output_file: Path):
    """
    Generiert die Laser-CAM-Vektordatei für den Acryl-Peilzeiger der Vorderseite (Länge 85.0 mm).
    Features:
    - Konturschnitt mit Nabe R = 5.0 mm, Armbreite 6.0 mm und Zeigerspitze bis R = 85.0 mm.
    - Zentrische Achsbohrung r = 1.6 mm.
    - Gravierte Ratio-Skala von 0.0 bis 1.2 entlang der Peilkante.
    """
    p_len = GEOM.pointer_length_front
    w_ptr = 6.0
    hub_r = 5.0

    parts = [svg_header(190.0, 190.0)]
    parts.append('  <!-- Schnittlinien (Laser-Cut) -->')
    parts.append(f'  <circle cx="0" cy="0" r="{GEOM.axle_hole_radius:.2f}" class="laser-cut" />')

    path_arm = (
        f"M 0 {-hub_r} "
        f"L 0 {-p_len + 3.0} "
        f"L {-w_ptr/2:.2f} {-p_len} "
        f"L {-w_ptr:.2f} {-p_len + 3.0} "
        f"L {-w_ptr:.2f} {-hub_r} "
        f"A {hub_r} {hub_r} 0 1 0 0 {-hub_r} Z"
    )
    parts.append(f'  <path d="{path_arm}" class="laser-cut" />')

    # Gravur: Rote Peilkante & Ratio-Teilung
    parts.append(f'  <line x1="0" y1="{-hub_r:.2f}" x2="0" y2="{-p_len:.2f}" stroke="#E74C3C" stroke-width="0.35" />')
    L = GEOM.polar_norm_length
    for r_idx in range(1, 13):
        ratio = r_idx * 0.1
        y_pos = -ratio * L
        if -y_pos <= p_len - 5.0:
            is_major = (r_idx % 2 == 0)
            t_w = 2.4 if is_major else 1.4
            parts.append(f'  <line x1="0" y1="{y_pos:.2f}" x2="{-t_w:.2f}" y2="{y_pos:.2f}" stroke="#2C3E50" stroke-width="0.3" />')
            if is_major:
                parts.append(f'  <text x="{-t_w - 0.8:.2f}" y="{y_pos:.2f}" class="grid-text" font-size="1.8px" text-anchor="end">{ratio:.1f}</text>')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_zentralzeiger_rueckseite(output_file: Path):
    """
    Generiert die Laser-CAM-Vektordatei für den transparenten Läufer der Rückseite (Länge 86.0 mm).
    Features:
    - Acryl-Arm (86.0 mm) mit zentraler roter Peillinie zur Projektion zwischen S-, C- und D-Skala.
    """
    p_len = GEOM.pointer_length_back
    w_ptr = 6.0
    hub_r = 5.0

    parts = [svg_header(190.0, 190.0)]
    parts.append('  <!-- Schnittlinien (Laser-Cut) -->')
    parts.append(f'  <circle cx="0" cy="0" r="{GEOM.axle_hole_radius:.2f}" class="laser-cut" />')

    path_arm = (
        f"M 0 {-hub_r} "
        f"L 0 {-p_len + 3.0} "
        f"L {-w_ptr/2:.2f} {-p_len} "
        f"L {-w_ptr:.2f} {-p_len + 3.0} "
        f"L {-w_ptr:.2f} {-hub_r} "
        f"A {hub_r} {hub_r} 0 1 0 0 {-hub_r} Z"
    )
    parts.append(f'  <path d="{path_arm}" class="laser-cut" />')
    parts.append(f'  <line x1="0" y1="{-hub_r:.2f}" x2="0" y2="{-p_len:.2f}" stroke="#E74C3C" stroke-width="0.35" />')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


# ==============================================================================
# 5. MONTIERTE KOMPOSIT-SVGS (SINGLE SOURCE OF TRUTH)
# ==============================================================================

def generate_laser_seite_a_montiert(output_file: Path, polar: PolarData, twa_pointer_deg: float = 40.0):
    """
    Erzeugt das montierte Gesamt-SVG der Vorderseite (Seite A):
    1. Gehäusedeckel mit Außenrand Ø 180 mm, M3-Schrauben und neuer Kompassrose (Ticks innen, Ziffern außen)
    2. Daumen-Tabs an 45°, 135°, 225°, 315° (Ø 186 mm)
    3. Mittelscheibe mit Taktikring, Polaren Weg A, 10 Ratio-Kreisen und BoatSPD-Skala
    4. Zentraler Acryl-Zeigerarm ausgerichtet auf twa_pointer_deg mit Ratio-Skala
    5. Mittelbolzen & Befestigungspin
    """
    parts = [svg_header(200.0, 200.0)]

    # Hintergrund Gehäusedeckel Stator (Ø 180 mm)
    parts.append('  <!-- 1. Stator Gehäusehintergrund -->')
    parts.append(f'  <circle cx="0" cy="0" r="{GEOM.stator_outer_radius:.2f}" fill="#FFFFFF" stroke="#2C3E50" stroke-width="0.8" />')

    # Daumen-Tabs der Mittelscheibe (stehen radial über Stator über)
    for ang in GEOM.thumb_tabs_angles:
        d_arc = GEOM.thumb_tabs_arc_deg / 2.0
        a1, a2 = ang - d_arc, ang + d_arc
        p1_out = polar_to_complex(GEOM.thumb_tabs_outer_radius, a1)
        p2_out = polar_to_complex(GEOM.thumb_tabs_outer_radius, a2)
        p1_in = polar_to_complex(GEOM.stator_outer_radius, a1)
        p2_in = polar_to_complex(GEOM.stator_outer_radius, a2)
        tab_path = (
            f"M {p1_in.real:.2f} {p1_in.imag:.2f} "
            f"L {p1_out.real:.2f} {p1_out.imag:.2f} "
            f"A {GEOM.thumb_tabs_outer_radius} {GEOM.thumb_tabs_outer_radius} 0 0 1 {p2_out.real:.2f} {p2_out.imag:.2f} "
            f"L {p2_in.real:.2f} {p2_in.imag:.2f} Z"
        )
        parts.append(f'  <path d="{tab_path}" fill="#BDC3C7" stroke="#7F8C8D" stroke-width="0.5" />')

    # M3-Senkkopfschrauben
    for i in range(GEOM.screw_count):
        ang_deg = i * (360.0 / GEOM.screw_count)
        p_screw = polar_to_complex(GEOM.screw_pcd_radius, ang_deg)
        parts.append(f'  <circle cx="{p_screw.real:.2f}" cy="{p_screw.imag:.2f}" r="3.0" fill="#BDC3C7" stroke="#7F8C8D" stroke-width="0.5" />')
        parts.append(f'  <line x1="{p_screw.real - 1.2:.2f}" y1="{p_screw.imag:.2f}" x2="{p_screw.real + 1.2:.2f}" y2="{p_screw.imag:.2f}" stroke="#2C3E50" stroke-width="0.4" />')
        parts.append(f'  <line x1="{p_screw.real:.2f}" y1="{p_screw.imag - 1.2:.2f}" x2="{p_screw.real:.2f}" y2="{p_screw.imag + 1.2:.2f}" stroke="#2C3E50" stroke-width="0.4" />')

    # Kompassrose auf Stator (Ticks innen, Ziffern außen)
    t_in = GEOM.stator_compass_ticks_inner
    t_out = GEOM.stator_compass_ticks_outer
    r_txt = GEOM.stator_compass_text_radius
    for deg in range(360):
        is_10 = (deg % 10 == 0)
        is_5 = (deg % 5 == 0)
        tick_start_r = t_in if is_10 else (t_in + 1.2 if is_5 else t_in + 2.2)

        p1 = polar_to_complex(tick_start_r, deg)
        p2 = polar_to_complex(t_out, deg)
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" stroke="#2C3E50" stroke-width="0.35" />')

        if is_10:
            pt = polar_to_complex(r_txt, deg)
            lbl = f"{deg:03d}°" if deg > 0 else "000°"
            rot = calc_readable_rotation(deg)
            parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="compass-text" transform="rotate({rot:.1f} {pt.real:.2f} {pt.imag:.2f})">{lbl}</text>')

    # Rotor Hintergrund (Ø 150 mm)
    parts.append('  <!-- 2. Rotor Scheibe (Vorderseite) -->')
    parts.append(f'  <circle cx="0" cy="0" r="{GEOM.rotor_radius:.2f}" fill="#FFFFFF" stroke="#2C3E50" stroke-width="0.6" />')

    # Rotor Inhalt (Taktikring & Polaren)
    parts.append(generate_tactical_rim())

    L = GEOM.polar_norm_length
    r_clip = GEOM.rotor_radius - 9.8

    # Titel
    parts.append(f'  <text x="0" y="-46.0" class="title-text">WEG A: NORMIERTE POLAREN (RATIO)</text>')
    parts.append(f'  <text x="0" y="-42.5" class="sub-text">Windpol (0,0) | L = {L:.1f} mm | JPK 1080 TRUE GRIT</text>')
    parts.append(f'  <text x="0" y="-39.5" class="sub-text" fill="#2980B9">Taktik: TWD · Shift/Lift · Tack · Start Line Bias · Gybe</text>')

    # 10 Ratio-Kreise
    for r_idx in range(1, 11):
        r_val = r_idx * 0.1 * L
        cls_name = "grid-line" if (r_idx % 2 == 0) else "grid-line-minor"
        parts.append(f'  <circle cx="0" cy="0" r="{r_val:.2f}" class="{cls_name}" />')

    # BoatSPD-Skala
    parts.append(f'  <line x1="5.0" y1="0" x2="{L:.2f}" y2="0" stroke="#2C3E50" stroke-width="0.45" />')
    for r_idx in range(1, 11):
        ratio = r_idx * 0.1
        rx = ratio * L
        is_major = (r_idx % 2 == 0)
        tick_len = 2.0 if is_major else 1.2
        parts.append(f'  <line x1="{rx:.2f}" y1="{-tick_len:.2f}" x2="{rx:.2f}" y2="{tick_len:.2f}" stroke="#2C3E50" stroke-width="0.35" />')
        lbl_txt = f"{ratio:.1f}" if is_major else f".{r_idx}"
        parts.append(f'  <text x="{rx:.2f}" y="-2.2" class="grid-text" font-size="1.9px" fill="#2C3E50">{lbl_txt}</text>')
    parts.append(f'  <text x="{L/2.0:.2f}" y="-5.2" class="grid-text" font-size="2.0px" font-weight="bold" fill="#2C3E50">BoatSPD / TWS</text>')

    # Basislinie
    parts.append(f'  <line x1="0" y1="0" x2="0" y2="{L:.2f}" stroke="#C0392B" stroke-width="1.1" stroke-linecap="round" />')
    parts.append(f'  <circle cx="0" cy="{L:.2f}" r="1.4" fill="#C0392B" />')
    parts.append(f'  <text x="0" y="{L - 2.5:.2f}" class="awa-label" font-weight="bold" fill="#C0392B">P1 (180°)</text>')
    parts.append(f'  <text x="0" y="-3.2" class="awa-label" font-weight="bold" fill="#C0392B">Windpol (0,0)</text>')

    # AWA Fasskreise
    awa_angles = CONFIG.tactical.get("awa_angles_deg", [25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 75.0, 90.0, 110.0, 135.0, 155.0])
    for alpha in awa_angles:
        rad = math.radians(alpha)
        sin_a = math.sin(rad)
        cos_a = math.cos(rad)
        if sin_a == 0:
            continue
        r_c = L / (2.0 * sin_a)
        ym = L / 2.0
        xc_stb = (L / 2.0) * (cos_a / sin_a)
        thetas = np.linspace(-math.radians(180.0 - alpha), math.radians(180.0 - alpha), 90)
        raw_stb = [complex(xc_stb + r_c * math.cos(t), ym + r_c * math.sin(t)) for t in thetas]

        for s in [1, -1]:
            pts_side = [complex(s * p.real, p.imag) for p in raw_stb]
            for sub in clip_polyline_to_circle(pts_side, r_clip):
                if len(sub) >= 2:
                    d_str = "M " + " ".join([f"{p.real:.2f} {p.imag:.2f}" for p in sub])
                    parts.append(f'  <path d="{d_str}" class="awa-line" />')

    # Polaren & Targets
    colors = CONFIG.polars.get("curve_colors", ["#1F618D", "#2980B9", "#2471A3", "#17A589", "#138D75", "#D4AC0D", "#CA6F1E", "#922B21"])
    cutoff_deg = float(CONFIG.polars.get("curve_cutoff_twa_deg", 175.0))
    crossover_stb, crossover_bb = [], []

    for idx, tws in enumerate(polar.tws_list):
        col = colors[idx % len(colors)]
        curve = polar.curves_raw[idx]
        pts_complex = []
        for i, pt in enumerate(curve):
            twa = pt["twa"]
            if twa <= cutoff_deg:
                pts_complex.append(polar_to_complex((pt["bsp"] / tws) * L, twa))
            else:
                if i > 0:
                    prev_pt = curve[i - 1]
                    if prev_pt["twa"] < cutoff_deg:
                        frac = (cutoff_deg - prev_pt["twa"]) / (twa - prev_pt["twa"])
                        bsp_cut = prev_pt["bsp"] + frac * (pt["bsp"] - prev_pt["bsp"])
                        pts_complex.append(polar_to_complex((bsp_cut / tws) * L, cutoff_deg))
                break

        smooth_pts = catmull_rom_spline(pts_complex, num_points=12)
        d_stb = "M " + " ".join([f"{p.real:.2f} {p.imag:.2f}" for p in smooth_pts])
        d_bb = "M " + " ".join([f"{-p.real:.2f} {p.imag:.2f}" for p in smooth_pts])
        parts.append(f'  <path d="{d_stb}" class="polar-curve" stroke="{col}" />')
        parts.append(f'  <path d="{d_bb}" class="polar-curve" stroke="{col}" />')

        tgt = polar.vmg_targets[idx]
        beat_r = (tgt["beat_sog"] / tws) * L
        p_beat = polar_to_complex(beat_r, tgt["beat_angle"])
        for bx in [p_beat.real, -p_beat.real]:
            by = p_beat.imag
            parts.append(f'  <polygon points="{bx:.2f},{by-1.1:.2f} {bx+1.1:.2f},{by:.2f} {bx:.2f},{by+1.1:.2f} {bx-1.1:.2f},{by:.2f}" class="vmg-beat" />')

        parts.append(f'  <text x="{p_beat.real - 2.1:.2f}" y="{p_beat.imag:.2f}" class="polar-label" text-anchor="end" fill="{col}">{int(tws)}</text>')
        parts.append(f'  <text x="{-p_beat.real + 2.1:.2f}" y="{p_beat.imag:.2f}" class="polar-label" text-anchor="start" fill="{col}">{int(tws)}</text>')

        run_r = (tgt["run_sog"] / tws) * L
        p_run = polar_to_complex(run_r, tgt["gybe_angle"])
        for rx in [p_run.real, -p_run.real]:
            ry = p_run.imag
            parts.append(f'  <polygon points="{rx:.2f},{ry-1.1:.2f} {rx+1.1:.2f},{ry:.2f} {rx:.2f},{ry+1.1:.2f} {rx-1.1:.2f},{ry:.2f}" class="vmg-run" />')

        # Crossover
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
                crossover_stb.append(inter)
                crossover_bb.append(complex(-inter.real, inter.imag))
                for cx in [inter.real, -inter.real]:
                    cy = inter.imag
                    parts.append(f'  <polygon points="{cx:.2f},{cy-1.3:.2f} {cx+1.2:.2f},{cy+1.0:.2f} {cx-1.2:.2f},{cy+1.0:.2f}" class="crossover-marker" />')

    if len(crossover_stb) >= 2:
        d_c_stb = "M " + " ".join([f"{p.real:.2f} {p.imag:.2f}" for p in crossover_stb])
        d_c_bb = "M " + " ".join([f"{p.real:.2f} {p.imag:.2f}" for p in crossover_bb])
        parts.append(f'  <path d="{d_c_stb}" class="crossover-line" />')
        parts.append(f'  <path d="{d_c_bb}" class="crossover-line" />')

    # 3. Zentralzeiger (Transparentes Acryl, rotiert auf twa_pointer_deg)
    parts.append('  <!-- 3. Zentralzeiger Vorderseite -->')
    p_len = GEOM.pointer_length_front
    w_ptr = 6.0
    rot_ptr = twa_pointer_deg

    path_ptr_body = (
        f"M 0 0 "
        f"L 0 {-p_len} "
        f"L {-w_ptr} {-p_len} "
        f"L {-w_ptr} 0 Z"
    )
    parts.append(f'  <g transform="rotate({rot_ptr} 0 0)">')
    parts.append(f'    <path d="{path_ptr_body}" fill="#EBF5FB" fill-opacity="0.55" stroke="#2980B9" stroke-width="0.5" />')
    parts.append(f'    <line x1="0" y1="0" x2="0" y2="{-p_len:.2f}" stroke="#E74C3C" stroke-width="0.8" />')
    parts.append('  </g>')

    # Zeiger-Annotation Text außerhalb des Stators
    p_annot = polar_to_complex(p_len + 5.0, rot_ptr)
    parts.append(f'  <text x="{p_annot.real:.2f}" y="{p_annot.imag:.2f}" font-family="sans-serif" font-weight="bold" font-size="3.2px" fill="#C0392B" text-anchor="middle" dominant-baseline="central">Zeiger: TWA {rot_ptr:.0f}°</text>')

    # 4. Mittelbolzen & Befestigungskappe
    parts.append('  <!-- 4. Mittelachse / Haltekappe -->')
    parts.append('  <circle cx="0" cy="0" r="5.0" fill="#BDC3C7" stroke="#2C3E50" stroke-width="0.8" />')
    parts.append('  <circle cx="0" cy="0" r="2.2" fill="#E74C3C" stroke="#962D22" stroke-width="0.6" />')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_laser_seite_b_montiert(output_file: Path, cursor_angle_deg: float = 30.0):
    """
    Erzeugt das montierte Gesamt-SVG der Rückseite (Seite B - Rechenschieber):
    1. Gehäuseboden mit Außenrand Ø 180 mm, M3-Schrauben und D-Skala (R = 75.5 bis 79.5 mm)
    2. Daumen-Tabs an 45°, 135°, 225°, 315° (Ø 186 mm)
    3. Mittelscheibe mit C-Skala (R = 74.5 mm), S-Sinusskala (R = 65.0 mm), Nonius und Formeln
    4. Zentraler Acryl-Läufer ausgerichtet auf cursor_angle_deg mit roter Haarlinie
    5. Mittelbolzen
    """
    parts = [svg_header(200.0, 200.0)]

    # Gehäuseboden Stator (Ø 180 mm)
    parts.append('  <!-- 1. Stator Gehäuseboden Hintergrund -->')
    parts.append(f'  <circle cx="0" cy="0" r="{GEOM.stator_outer_radius:.2f}" fill="#FFFFFF" stroke="#2C3E50" stroke-width="0.8" />')

    # Daumen-Tabs
    for ang in GEOM.thumb_tabs_angles:
        d_arc = GEOM.thumb_tabs_arc_deg / 2.0
        a1, a2 = ang - d_arc, ang + d_arc
        p1_out = polar_to_complex(GEOM.thumb_tabs_outer_radius, a1)
        p2_out = polar_to_complex(GEOM.thumb_tabs_outer_radius, a2)
        p1_in = polar_to_complex(GEOM.stator_outer_radius, a1)
        p2_in = polar_to_complex(GEOM.stator_outer_radius, a2)
        tab_path = (
            f"M {p1_in.real:.2f} {p1_in.imag:.2f} "
            f"L {p1_out.real:.2f} {p1_out.imag:.2f} "
            f"A {GEOM.thumb_tabs_outer_radius} {GEOM.thumb_tabs_outer_radius} 0 0 1 {p2_out.real:.2f} {p2_out.imag:.2f} "
            f"L {p2_in.real:.2f} {p2_in.imag:.2f} Z"
        )
        parts.append(f'  <path d="{tab_path}" fill="#BDC3C7" stroke="#7F8C8D" stroke-width="0.5" />')

    # M3-Schrauben
    for i in range(GEOM.screw_count):
        ang_deg = i * (360.0 / GEOM.screw_count)
        p_screw = polar_to_complex(GEOM.screw_pcd_radius, ang_deg)
        parts.append(f'  <circle cx="{p_screw.real:.2f}" cy="{p_screw.imag:.2f}" r="3.0" fill="#BDC3C7" stroke="#7F8C8D" stroke-width="0.5" />')
        parts.append(f'  <line x1="{p_screw.real - 1.2:.2f}" y1="{p_screw.imag:.2f}" x2="{p_screw.real + 1.2:.2f}" y2="{p_screw.imag:.2f}" stroke="#2C3E50" stroke-width="0.4" />')
        parts.append(f'  <line x1="{p_screw.real:.2f}" y1="{p_screw.imag - 1.2:.2f}" x2="{p_screw.real:.2f}" y2="{p_screw.imag + 1.2:.2f}" stroke="#2C3E50" stroke-width="0.4" />')

    # D-Skala auf Stator
    r_d = GEOM.d_scale_radius
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
        p1 = polar_to_complex(r_d, deg)
        p2 = polar_to_complex(r_d + f_len * dash, deg)
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" stroke="#2C3E50" stroke-width="0.35" />')
        if f_len >= 4.0:
            pt = polar_to_complex(r_d + 5.5, deg)
            txt = f"{x/100:.1f}" if x < 200 else f"{x//100}" if x % 100 == 0 else f"{x/100:.1f}"
            parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="compass-text" font-size="2.2px">{txt}</text>')

    p_lbl_d = polar_to_complex(r_d + 6.5, 340.0)
    rot_d = calc_readable_rotation(340.0)
    parts.append(f'  <text x="{p_lbl_d.real:.2f}" y="{p_lbl_d.imag:.2f}" font-family="sans-serif" font-weight="bold" font-size="2.6px" fill="#1F618D" text-anchor="middle" dominant-baseline="central" transform="rotate({rot_d:.1f} {p_lbl_d.real:.2f} {p_lbl_d.imag:.2f})">D (STATOR)</text>')

    # Rotor Hintergrund (Ø 150 mm)
    parts.append('  <!-- 2. Rotor Scheibe (Rückseite) -->')
    parts.append(f'  <circle cx="0" cy="0" r="{GEOM.rotor_radius:.2f}" fill="#FFFFFF" stroke="#2C3E50" stroke-width="0.6" />')

    # C-Skala
    r_c = GEOM.c_scale_radius
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
        p1 = polar_to_complex(r_c, deg)
        p2 = polar_to_complex(r_c - f_len * dash, deg)
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" stroke="#2C3E50" stroke-width="0.35" />')
        if f_len >= 4.0:
            pt = polar_to_complex(r_c - 4.5, deg)
            txt = f"{x/100:.1f}" if x < 200 else f"{x//100}" if x % 100 == 0 else f"{x/100:.1f}"
            parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="compass-text" font-size="2.2px">{txt}</text>')

    p_lbl_c = polar_to_complex(r_c - 5.5, 340.0)
    rot_c = calc_readable_rotation(340.0)
    parts.append(f'  <text x="{p_lbl_c.real:.2f}" y="{p_lbl_c.imag:.2f}" font-family="sans-serif" font-weight="bold" font-size="2.6px" fill="#1F618D" text-anchor="middle" dominant-baseline="central" transform="rotate({rot_c:.1f} {p_lbl_c.real:.2f} {p_lbl_c.imag:.2f})">C (ROTOR)</text>')

    # Performance-Nonius
    for pct in [-15, -10, -5, 5]:
        val = 1.0 + (pct / 100.0)
        deg = math.log10(val) * 360.0
        p1 = polar_to_complex(r_c, deg)
        p2 = polar_to_complex(r_c - 3.0, deg)
        col = "#27AE60" if pct > 0 else "#C0392B"
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" stroke="{col}" stroke-width="0.5" />')
        pt = polar_to_complex(r_c - 4.5, deg)
        parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" font-family="sans-serif" font-size="1.8px" font-weight="bold" fill="{col}" text-anchor="middle">{pct:+d}%</text>')

    # S-Sinusskala
    r_s = GEOM.s_scale_radius
    parts.append(f'  <circle cx="0" cy="0" r="{r_s:.2f}" class="grid-line" stroke="#2980B9" stroke-width="0.3" />')
    sin_angles = [
        6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
        22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 45, 50, 55, 60, 70, 80, 90
    ]
    for alpha in sin_angles:
        deg = math.log10(10.0 * math.sin(math.radians(alpha))) * 360.0
        is_labeled = alpha in [6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 35, 40, 50, 60, 70, 90]
        tick_len = 3.2 if is_labeled else 1.8
        p1 = polar_to_complex(r_s, deg)
        p2 = polar_to_complex(r_s - tick_len, deg)
        parts.append(f'  <line x1="{p1.real:.2f}" y1="{p1.imag:.2f}" x2="{p2.real:.2f}" y2="{p2.imag:.2f}" stroke="#2980B9" stroke-width="0.35" />')
        if is_labeled:
            pt = polar_to_complex(r_s - 5.5, deg)
            rot = calc_readable_rotation(deg)
            parts.append(f'  <text x="{pt.real:.2f}" y="{pt.imag:.2f}" class="compass-text" font-size="2.0px" fill="#2980B9" transform="rotate({rot:.1f} {pt.real:.2f} {pt.imag:.2f})">{alpha}°</text>')

    # Titel & Formeln im Zentrum
    parts.append('  <!-- Titel & Nautische Formeln -->')
    parts.append('  <text x="0" y="-45.0" class="awa-label" font-size="2.4px" font-weight="bold">S (SINUS-SKALA FÜR WINDDREIECK)</text>')
    parts.append('  <text x="0" y="-18.0" class="title-text" font-size="3.2px">RÜCKSEITE: RECHENSCHIEBER &amp; S-SKALA</text>')
    parts.append('  <text x="0" y="-14.0" class="sub-text" font-size="2.2px">JPK 1080 TRUE GRIT · GER 7447</text>')
    parts.append('  <text x="0" y="-10.5" class="sub-text" font-size="2.0px" fill="#2980B9">Multiplikation · Division · Distanz/Zeit · Sinussatz</text>')
    parts.append('  <text x="0" y="12.0" class="sub-text" font-size="2.0px">Trennfuge C/D: R = 75.0 mm (Ø 150 mm)</text>')
    parts.append('  <text x="0" y="16.0" font-family="sans-serif" font-style="italic" font-size="2.0px" fill="#2C3E50" text-anchor="middle">Sinussatz: a / sin(α) = b / sin(β) = c / sin(γ)</text>')

    # 3. Zentraler Dreh-Läufer (Acryl mit Haarlinie)
    parts.append('  <!-- 3. Zentraler Dreh-Läufer Rückseite -->')
    p_len = GEOM.pointer_length_back
    w_ptr = 6.0
    rot_cursor = math.log10(10.0 * math.sin(math.radians(cursor_angle_deg))) * 360.0

    path_csr_body = (
        f"M {-w_ptr/2} 0 "
        f"L {-w_ptr/2} {-p_len} "
        f"L {w_ptr/2} {-p_len} "
        f"L {w_ptr/2} 0 Z"
    )
    parts.append(f'  <g transform="rotate({rot_cursor} 0 0)">')
    parts.append(f'    <path d="{path_csr_body}" fill="#EBF5FB" fill-opacity="0.55" stroke="#2980B9" stroke-width="0.5" />')
    parts.append(f'    <line x1="0" y1="0" x2="0" y2="{-p_len:.2f}" stroke="#E74C3C" stroke-width="0.8" />')
    parts.append('  </g>')

    p_annot = polar_to_complex(p_len + 5.0, rot_cursor)
    parts.append(f'  <text x="{p_annot.real:.2f}" y="{p_annot.imag:.2f}" font-family="sans-serif" font-weight="bold" font-size="3.0px" fill="#C0392B" text-anchor="middle" dominant-baseline="central">Läufer: 30° S -&gt; 5.0 (C/D)</text>')

    # 4. Mittelachse
    parts.append('  <!-- 4. Mittelachse / Haltekappe -->')
    parts.append('  <circle cx="0" cy="0" r="5.0" fill="#BDC3C7" stroke="#2C3E50" stroke-width="0.8" />')
    parts.append('  <circle cx="0" cy="0" r="2.2" fill="#E74C3C" stroke="#962D22" stroke-width="0.6" />')

    parts.append('</svg>\n')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


# ==============================================================================
# 6. MASTER BUILD ALL FUNCTION
# ==============================================================================

def generate_all_laser_svgs(polar: PolarData, out_dir: Path) -> List[Path]:
    """
    Generiert den vollständigen Satz aller CAM/Laser-SVGs sowie der
    beiden montierten Komposit-SVGs (Single Source of Truth).
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = [
        # Einzelne Laser-CAM-Dateien
        (out_dir / "laser_seite_a_rotor_vorderseite.svg", lambda p: generate_laser_seite_a_rotor(p, polar)),
        (out_dir / "laser_seite_a_deckel_kompassrose.svg", generate_laser_seite_a_deckel),
        (out_dir / "laser_seite_b_rotor_rueckseite.svg", generate_laser_seite_b_rotor),
        (out_dir / "laser_seite_b_boden_d_skala.svg", generate_laser_seite_b_boden),
        (out_dir / "laser_zentralzeiger.svg", generate_laser_zentralzeiger),
        (out_dir / "laser_zentralzeiger_rueckseite.svg", generate_laser_zentralzeiger_rueckseite),

        # Montierte Komposit-SVGs für 100% WYSIWYG-Rendering
        (out_dir / "laser_seite_a_montiert.svg", lambda p: generate_laser_seite_a_montiert(p, polar, twa_pointer_deg=40.0)),
        (out_dir / "laser_seite_b_montiert.svg", lambda p: generate_laser_seite_b_montiert(p, cursor_angle_deg=30.0)),
    ]

    generated = []
    for filepath, gen_func in files:
        gen_func(filepath)
        generated.append(filepath)

    return generated
