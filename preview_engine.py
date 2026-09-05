"""
preview_engine.py - High-Resolution (300 DPI) Rendering Engine for Rechenscheibe V1.0
JPK 1080 (GER 7447 - TRUE GRIT)

Generates:
1. gesamtansicht_seite_a_montiert.png - Fully assembled Sandwich Cassette preview (Side A)
   (Outer Stator with 360° Compass Rose, 6x M3 Screws, 4 Thumb Tabs, Inner Rotor & Pointer)
2. gesamtansicht_seite_b_montiert.png - Fully assembled Sandwich Cassette preview (Side B)
   (Outer Stator with D-Scale, Inner Rotor with C-Scale, S-Sinus Scale, Nonius & Hub)
3. rotor_vorderseite_weg_a.png - High-resolution detailed view of Front Rotor Face
"""

import math
from pathlib import Path
from typing import Tuple, List, Optional
import numpy as np
import matplotlib.pyplot as plt
from polar_parser import PolarData, catmull_rom_spline
from vector_engine import (
    find_circle_intersection,
    clip_polyline_to_circle,
    find_ray_spline_intersection
)


def polar_to_cart(r: float, deg: float) -> Tuple[float, float]:
    """0° is North (12 o'clock, +Y in preview plotting), clockwise."""
    rad = math.radians(deg)
    return r * math.sin(rad), r * math.cos(rad)


def calc_readable_rotation(deg: float) -> float:
    """Standard nautical drafting text rotation: keeps text upright and readable."""
    deg_norm = deg % 360.0
    if 90.0 < deg_norm < 270.0:
        return -deg_norm + 180.0
    else:
        return -deg_norm


def render_assembled_montage(
    polar: PolarData,
    outfile: Path,
    twa_pointer_deg: float = 40.0,
    wind_direction_compass: float = 0.0,
    dpi: int = 300
):
    """
    Renders the fully assembled Rechenscheibe V1.0 (Side A):
    - Outer Stator (Ø 180 mm) with full 360° Compass Rose & 6 M3 countersunk screws
    - 4 knurled thumb tabs protruding at 45°, 135°, 225°, 315° (Ø 186 mm)
    - Rotor window (Ø 150 mm) with TackingMaster tactical rim, JPK 1080 Polars & Fasskreise
    - Central Pointer arm set to twa_pointer_deg
    """
    fig, ax = plt.subplots(figsize=(11, 11), dpi=dpi)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-100, 100)
    ax.set_ylim(-100, 100)

    # 1. Outer 4 Thumb Tabs (Ø 186 mm, r = 93 mm)
    r_tab = 93.0
    r_casing = 90.0
    for tab_center in [45.0, 135.0, 225.0, 315.0]:
        th = np.linspace(math.radians(tab_center - 15.0), math.radians(tab_center + 15.0), 30)
        xs = list(r_tab * np.sin(th)) + list(r_casing * np.sin(th[::-1]))
        ys = list(r_tab * np.cos(th)) + list(r_casing * np.cos(th[::-1]))
        ax.fill(xs, ys, color="#D5D8DC", ec="#7F8C8D", lw=0.8, zorder=1)
        # Knurling ridges
        for k_deg in np.linspace(tab_center - 12.0, tab_center + 12.0, 7):
            x1, y1 = polar_to_cart(r_casing + 0.5, k_deg)
            x2, y2 = polar_to_cart(r_tab - 0.5, k_deg)
            ax.plot([x1, x2], [y1, y2], color="#7F8C8D", lw=0.6, zorder=2)

    # 2. Outer Stator Ring (Ø 150 to Ø 180 mm)
    stator_outer = plt.Circle((0, 0), 90.0, color="#EAEDED", ec="#2C3E50", lw=1.5, zorder=3)
    ax.add_patch(stator_outer)
    rotor_pocket = plt.Circle((0, 0), 75.0, color="#FFFFFF", ec="#2C3E50", lw=1.2, zorder=4)
    ax.add_patch(rotor_pocket)

    # 6 M3 Countersunk Screws on PCD Ø 176 mm (r = 88 mm)
    for i in range(6):
        s_deg = i * 60.0
        sx, sy = polar_to_cart(88.0, s_deg)
        screw_head = plt.Circle((sx, sy), 3.0, color="#BDC3C7", ec="#7F8C8D", lw=0.7, zorder=5)
        ax.add_patch(screw_head)
        # Hex socket / slot
        ax.plot([sx - 1.2, sx + 1.2], [sy, sy], color="#2C3E50", lw=0.6, zorder=6)
        ax.plot([sx, sx], [sy - 1.2, sy + 1.2], color="#2C3E50", lw=0.6, zorder=6)

    # 360° Compass Rose on Stator Ring (r in [76.0, 88.0])
    for deg in range(360):
        is_10 = (deg % 10 == 0)
        is_5 = (deg % 5 == 0)
        t_len = 3.5 if is_10 else (2.0 if is_5 else 1.0)
        x1, y1 = polar_to_cart(86.5, deg)
        x2, y2 = polar_to_cart(86.5 - t_len, deg)
        ax.plot([x1, x2], [y1, y2], color="#2C3E50", lw=0.6 if is_10 else 0.3, zorder=5)

        if is_10:
            xt, yt = polar_to_cart(80.5, deg)
            lbl = f"{deg:03d}°" if deg > 0 else "000°"
            rot = calc_readable_rotation(deg)
            ax.text(xt, yt, lbl, color="#2C3E50", fontsize=4.2, fontweight="bold", ha="center", va="center", rotation=rot, zorder=6)

    # 3. ROTOR (Ø 150 mm) - TackingMaster Rim & Polars
    # TRUE WIND Arrow
    ax.annotate(
        "TRUE WIND", xy=(0, 74.5), xytext=(0, 67.5),
        arrowprops=dict(facecolor="#C0392B", edgecolor="#962D22", width=3.0, headwidth=8.0),
        ha="center", va="center", fontsize=7.5, fontweight="bold", color="#C0392B", zorder=12
    )
    ax.text(0, 64.5, "◄ PORT LIFT | STBD LIFT ►", color="#27AE60", fontsize=5.0, fontweight="bold", ha="center", va="center", zorder=12)

    # Shift Ticks
    for s in [1, -1]:
        for shift_deg in [5.0, 10.0, 15.0]:
            d = shift_deg * s
            x1, y1 = polar_to_cart(75.0, d)
            x2, y2 = polar_to_cart(72.8, d)
            ax.plot([x1, x2], [y1, y2], color="#2C3E50", lw=0.8, zorder=7)
            xt, yt = polar_to_cart(71.2, d)
            ax.text(xt, yt, f"{int(shift_deg)}°", color="#2C3E50", fontsize=4.5, ha="center", va="center", zorder=8)
        tx, ty = polar_to_cart(67.8, 11.5 * s)
        txt = "LIFT ▶" if s > 0 else "◀ LIFT"
        ax.text(tx, ty, txt, color="#27AE60", fontsize=5.0, fontweight="bold", ha="center", va="center", rotation=-11.5*s, zorder=12)

    # TACK Sectors (38° to 42°)
    for s in [1, -1]:
        th = [math.radians(a * s) for a in [38.0, 42.0, 42.0, 38.0]]
        r = [66.0, 66.0, 75.0, 75.0]
        xs = [ri * math.sin(ti) for ri, ti in zip(r, th)]
        ys = [ri * math.cos(ti) for ri, ti in zip(r, th)]
        c_fill = "#2ECC71" if s > 0 else "#E74C3C"
        c_edge = "#27AE60" if s > 0 else "#C0392B"
        ax.fill(xs, ys, color=c_fill, alpha=0.35, ec=c_edge, lw=0.8, zorder=7)
        tx, ty = polar_to_cart(70.5, 40.0 * s)
        lbl_tack = "STBD TACK 40°" if s > 0 else "PORT TACK 40°"
        ax.text(tx, ty, lbl_tack, color=c_edge, fontsize=5.2, fontweight="bold", ha="center", va="center", rotation=-40*s, zorder=12)

    # Start Line Bias System (+-90°)
    for s in [1, -1]:
        base_angle = 90.0 * s
        x_in, y_in = polar_to_cart(66.0, base_angle)
        x_out, y_out = polar_to_cart(75.0, base_angle)
        ax.plot([x_in, x_out], [y_in, y_out], color="#2980B9", lw=2.0, zorder=8)

        for b_deg in [5.0, 10.0, 15.0]:
            for s_sgn in [1, -1]:
                b_ang = base_angle + (b_deg * s_sgn)
                x1, y1 = polar_to_cart(75.0, b_ang)
                x2, y2 = polar_to_cart(72.8, b_ang)
                ax.plot([x1, x2], [y1, y2], color="#2980B9", lw=0.8, zorder=7)
                xt, yt = polar_to_cart(71.2, b_ang)
                ax.text(xt, yt, f"{int(b_deg)}°", color="#2980B9", fontsize=4.5, ha="center", va="center", zorder=8)

        tx, ty = polar_to_cart(70.5, base_angle)
        line_name = "BOAT END (RC)" if s > 0 else "PIN END"
        rot_name = -90.0 if s > 0 else 90.0
        ax.text(
            tx, ty, line_name, color="#2980B9", fontsize=5.2, fontweight="bold",
            ha="center", va="center", rotation=rot_name, zorder=12,
            bbox=dict(boxstyle="round,pad=0.25", fc="#FFFFFF", ec="#2980B9", lw=0.6)
        )

        up_ang = base_angle - (9.5 * s)
        tx_up, ty_up = polar_to_cart(67.5, up_ang)
        fav_up = "▲ BOAT FAV" if s > 0 else "PIN FAV ▲"
        ax.text(tx_up, ty_up, fav_up, color="#27AE60", fontsize=4.5, fontweight="bold", ha="center", va="center", rotation=-up_ang, zorder=12)

        down_ang = base_angle + (9.5 * s)
        tx_down, ty_down = polar_to_cart(67.5, down_ang)
        fav_down = "PIN FAV ▼" if s > 0 else "▼ BOAT FAV"
        ax.text(tx_down, ty_down, fav_down, color="#C0392B", fontsize=4.5, fontweight="bold", ha="center", va="center", rotation=-down_ang, zorder=12)

    # GYBE Sectors (145° to 165°)
    for s in [1, -1]:
        th = [math.radians(a * s) for a in [145.0, 165.0, 165.0, 145.0]]
        r = [66.0, 66.0, 75.0, 75.0]
        xs = [ri * math.sin(ti) for ri, ti in zip(r, th)]
        ys = [ri * math.cos(ti) for ri, ti in zip(r, th)]
        c_fill = "#2ECC71" if s > 0 else "#E74C3C"
        c_edge = "#27AE60" if s > 0 else "#C0392B"
        ax.fill(xs, ys, color=c_fill, alpha=0.25, ec=c_edge, lw=0.8, zorder=7)
        tx, ty = polar_to_cart(70.5, 155.0 * s)
        lbl_gybe = "STBD GYBE 155°" if s > 0 else "PORT GYBE 155°"
        ax.text(tx, ty, lbl_gybe, color=c_edge, fontsize=5.0, fontweight="bold", ha="center", va="center", rotation=25*s, zorder=12)

    # Free Sector Compass Ticks
    for deg in range(10, 180, 5):
        if deg <= 18 or (36 <= deg <= 44) or (73 <= deg <= 107) or (143 <= deg <= 167) or deg >= 177:
            continue
        for s in [1, -1]:
            d = deg * s
            is_30 = (deg % 30 == 0)
            l = 3.0 if is_30 else 1.5
            x1, y1 = polar_to_cart(75.0, d)
            x2, y2 = polar_to_cart(75.0 - l, d)
            ax.plot([x1, x2], [y1, y2], color="#2C3E50", lw=0.6, zorder=7)
            if is_30:
                xt, yt = polar_to_cart(69.0, d)
                ax.text(xt, yt, f"{deg}°", color="#2C3E50", fontsize=6.0, fontweight="bold", ha="center", va="center", zorder=8)

    # Titles
    ax.text(0, 46.0, "WEG A: NORMIERTE POLAREN (RATIO)", fontsize=8.0, fontweight="bold", color="#2C3E50", ha="center", va="center", zorder=12)
    ax.text(0, 42.5, "Windpol (0,0) | L = 64 mm | JPK 1080 TRUE GRIT", fontsize=5.8, color="#7F8C8D", ha="center", va="center", zorder=12)
    ax.text(0, 39.5, "Taktik: TWD · Shift/Lift · Tack · Start Line Bias · Gybe", fontsize=4.8, color="#2980B9", ha="center", va="center", zorder=12)

    # Ratio concentric circles
    L = 64.0
    for ratio in [0.2, 0.4, 0.6, 0.8, 1.0]:
        r = ratio * L
        c = plt.Circle((0, 0), r, color="#E0E0E0", fill=False, lw=0.6, ls="--", zorder=5)
        ax.add_patch(c)
        ax.text(r - 1.0, 1.8, f"{ratio:.1f}", color="#95A5A6", fontsize=5.0, ha="right", va="center", zorder=6)

    # Baseline
    ax.plot([0, 0], [0, -L], color="#C0392B", lw=1.5, zorder=8)
    ax.scatter([0], [-L], color="#C0392B", s=20, zorder=9)
    ax.text(0, -L - 2.5, "P1 (180°)", color="#C0392B", fontsize=5.5, fontweight="bold", ha="center", va="top", zorder=10)
    ax.text(0, 7.2, "Windpol (0,0)", color="#C0392B", fontsize=5.5, fontweight="bold", ha="center", va="bottom", zorder=22)

    # Fasskreise (lower half)
    r_clip = 65.2
    awa_angles = [25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 75.0, 90.0, 110.0, 135.0, 155.0]
    for alpha in awa_angles:
        rad = math.radians(alpha)
        sin_a = math.sin(rad)
        cos_a = math.cos(rad)
        if sin_a == 0:
            continue
        r_c = L / (2.0 * sin_a)
        ym = -L / 2.0
        xc_stb = (L / 2.0) * (cos_a / sin_a)
        thetas = np.linspace(-math.radians(180.0 - alpha), math.radians(180.0 - alpha), 90)
        raw_stb = [(xc_stb + r_c * math.cos(t), ym + r_c * math.sin(t)) for t in thetas]

        for s in [1, -1]:
            pts_side = [(s * p[0], p[1]) for p in raw_stb]
            for sub in clip_polyline_to_circle(pts_side, r_clip):
                if len(sub) >= 2:
                    xs, ys = zip(*sub)
                    ax.plot(xs, ys, color="#2980B9", lw=0.45, ls="--", alpha=0.7, zorder=5)

    # Polars JPK 1080
    colors = ["#1F618D", "#2980B9", "#2471A3", "#17A589", "#138D75", "#D4AC0D", "#CA6F1E", "#922B21"]
    crossover_stb, crossover_bb = [], []

    for idx, tws in enumerate(polar.tws_list):
        col = colors[idx % len(colors)]
        curve = polar.curves_raw[idx]
        pts_complex = [complex((pt["bsp"] / tws) * L * math.sin(math.radians(pt["twa"])), (pt["bsp"] / tws) * L * math.cos(math.radians(pt["twa"]))) for pt in curve]
        smooth_pts = catmull_rom_spline(pts_complex, num_points=12)

        stb_pts = [(p.real, p.imag) for p in smooth_pts]
        bb_pts = [(-p.real, p.imag) for p in smooth_pts]

        for s_pts in [stb_pts, bb_pts]:
            for sub in clip_polyline_to_circle(s_pts, r_clip):
                if len(sub) >= 2:
                    xs, ys = zip(*sub)
                    ax.plot(xs, ys, color=col, lw=1.0, zorder=8)

        # Targets
        tgt = polar.vmg_targets[idx]
        beat_r = (tgt["beat_sog"] / tws) * L
        bx, by = polar_to_cart(beat_r, tgt["beat_angle"])
        ax.scatter([bx, -bx], [by, by], color="#E74C3C", edgecolors="#962D22", marker="D", s=18, zorder=11)

        run_r = (tgt["run_sog"] / tws) * L
        rx, ry = polar_to_cart(run_r, tgt["gybe_angle"])
        ax.scatter([rx, -rx], [ry, ry], color="#2ECC71", edgecolors="#27AE60", marker="D", s=18, zorder=11)

        # Crossover point
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
            inter = find_ray_spline_intersection(cross_twa, smooth_pts, sign_y=1.0)
            if inter:
                cx, cy = inter
                crossover_stb.append((cx, cy))
                crossover_bb.append((-cx, cy))
                ax.scatter([cx, -cx], [cy, cy], color="#9B59B6", edgecolors="#8E44AD", marker="^", s=24, zorder=11)

    if len(crossover_stb) >= 2:
        xs, ys = zip(*crossover_stb)
        ax.plot(xs, ys, color="#8E44AD", lw=0.9, ls="--", zorder=10)
        xs_bb, ys_bb = zip(*crossover_bb)
        ax.plot(xs_bb, ys_bb, color="#8E44AD", lw=0.9, ls="--", zorder=10)

    # 4. OVERLAID CENTRAL POINTER (Zeigerarm)
    p_len = 86.0
    p_rad = math.radians(twa_pointer_deg)
    cos_p = math.cos(p_rad)
    sin_p = math.sin(p_rad)

    # Reading edge along ray from (0,0) to p_len
    px_tip, py_tip = p_len * sin_p, p_len * cos_p
    # Transparent acrylic pointer body
    w_ptr = 6.0
    nx, ny = -cos_p * w_ptr, sin_p * w_ptr

    ptr_poly_x = [0.0, px_tip, px_tip + nx, nx]
    ptr_poly_y = [0.0, py_tip, py_tip + ny, ny]
    ax.fill(ptr_poly_x, ptr_poly_y, color="#EBF5FB", alpha=0.55, ec="#2980B9", lw=0.9, zorder=15)
    # Red hairline reading edge
    ax.plot([0, px_tip], [0, py_tip], color="#E74C3C", lw=1.0, zorder=16)

    # Center Hub & Pin
    hub = plt.Circle((0, 0), 5.0, color="#BDC3C7", ec="#2C3E50", lw=1.0, zorder=18)
    ax.add_patch(hub)
    pin = plt.Circle((0, 0), 2.2, color="#E74C3C", ec="#962D22", lw=0.8, zorder=19)
    ax.add_patch(pin)

    # Pointer legend annotation
    lbl_px, lbl_py = polar_to_cart(p_len + 5.0, twa_pointer_deg)
    ax.text(lbl_px, lbl_py, f"Zeiger: TWA {twa_pointer_deg:.0f}°", color="#C0392B", fontsize=5.8, fontweight="bold", ha="center", va="center", zorder=20)

    outfile.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outfile, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def render_assembled_seite_b(
    outfile: Path,
    dpi: int = 300
):
    """
    Renders the fully assembled Rechenscheibe V1.0 (Side B - Rechenschieber):
    - Outer Stator Base Ring (Ø 150 to Ø 180 mm) with Logarithmic D-Scale & 6 M3 Screws
    - 4 knurled thumb tabs protruding at 45°, 135°, 225°, 315° (Ø 186 mm)
    - Rotor window (Ø 150 mm) with C-Scale, S-Sinus Scale (r=48 mm), and Performance Nonius
    - Hairline sliding interface between Stator and Rotor at r = 75.0 mm
    """
    fig, ax = plt.subplots(figsize=(11, 11), dpi=dpi)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-100, 100)
    ax.set_ylim(-100, 100)

    # 1. Outer 4 Thumb Tabs (Ø 186 mm, r = 93 mm)
    r_tab = 93.0
    r_casing = 90.0
    for tab_center in [45.0, 135.0, 225.0, 315.0]:
        th = np.linspace(math.radians(tab_center - 15.0), math.radians(tab_center + 15.0), 30)
        xs = list(r_tab * np.sin(th)) + list(r_casing * np.sin(th[::-1]))
        ys = list(r_tab * np.cos(th)) + list(r_casing * np.cos(th[::-1]))
        ax.fill(xs, ys, color="#D5D8DC", ec="#7F8C8D", lw=0.8, zorder=1)
        for k_deg in np.linspace(tab_center - 12.0, tab_center + 12.0, 7):
            x1, y1 = polar_to_cart(r_casing + 0.5, k_deg)
            x2, y2 = polar_to_cart(r_tab - 0.5, k_deg)
            ax.plot([x1, x2], [y1, y2], color="#7F8C8D", lw=0.6, zorder=2)

    # 2. Outer Stator Ring (Ø 150 to Ø 180 mm)
    stator_outer = plt.Circle((0, 0), 90.0, color="#EAEDED", ec="#2C3E50", lw=1.5, zorder=3)
    ax.add_patch(stator_outer)
    rotor_pocket = plt.Circle((0, 0), 75.0, color="#FAFAFA", ec="#2C3E50", lw=1.2, zorder=4)
    ax.add_patch(rotor_pocket)

    # 6 M3 Countersunk Screws on PCD Ø 176 mm (r = 88 mm)
    for i in range(6):
        s_deg = i * 60.0
        sx, sy = polar_to_cart(88.0, s_deg)
        screw_head = plt.Circle((sx, sy), 3.0, color="#BDC3C7", ec="#7F8C8D", lw=0.7, zorder=5)
        ax.add_patch(screw_head)
        ax.plot([sx - 1.2, sx + 1.2], [sy, sy], color="#2C3E50", lw=0.6, zorder=6)
        ax.plot([sx, sx], [sy - 1.2, sy + 1.2], color="#2C3E50", lw=0.6, zorder=6)

    # D-Scale on Stator Ring (r in [75.5, 83.0])
    r_d = 75.5
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
        f_len = 4.2 if (x in [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000]) else (2.5 if x % 10 == 0 else 1.5)

        x1, y1 = polar_to_cart(r_d, deg)
        x2, y2 = polar_to_cart(r_d + f_len, deg)
        ax.plot([x1, x2], [y1, y2], color="#2C3E50", lw=0.7 if f_len > 3.0 else 0.35, zorder=7)

        if f_len >= 4.0:
            xt, yt = polar_to_cart(r_d + 6.0, deg)
            txt = f"{x/100:.1f}" if x < 200 else f"{x//100}" if x % 100 == 0 else f"{x/100:.1f}"
            rot = calc_readable_rotation(deg)
            ax.text(xt, yt, txt, color="#2C3E50", fontsize=4.2, fontweight="bold", ha="center", va="center", rotation=rot, zorder=8)

    # Label D (Stator) placed clearly at 11 o'clock (335°)
    ldx, ldy = polar_to_cart(84.0, 340.0)
    ax.text(ldx, ldy, "D (STATOR)", color="#1F618D", fontsize=5.5, fontweight="bold", ha="center", va="center", rotation=calc_readable_rotation(340.0), zorder=9)

    # 3. ROTOR (Ø 150 mm)
    # C-Scale on Rotor (r in [70.5, 74.5])
    r_c = 74.5
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
        f_len = 4.2 if (x in [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000]) else (2.5 if x % 10 == 0 else 1.5)

        x1, y1 = polar_to_cart(r_c, deg)
        x2, y2 = polar_to_cart(r_c - f_len, deg)
        ax.plot([x1, x2], [y1, y2], color="#2C3E50", lw=0.7 if f_len > 3.0 else 0.35, zorder=7)

        if f_len >= 4.0:
            xt, yt = polar_to_cart(r_c - 6.2, deg)
            txt = f"{x/100:.1f}" if x < 200 else f"{x//100}" if x % 100 == 0 else f"{x/100:.1f}"
            rot = calc_readable_rotation(deg)
            ax.text(xt, yt, txt, color="#2C3E50", fontsize=4.2, fontweight="bold", ha="center", va="center", rotation=rot, zorder=8)

    # Label C (Rotor) placed clearly at 11 o'clock (340°)
    lcx, lcy = polar_to_cart(65.5, 340.0)
    ax.text(lcx, lcy, "C (ROTOR)", color="#1F618D", fontsize=5.5, fontweight="bold", ha="center", va="center", rotation=calc_readable_rotation(340.0), zorder=9)

    # Performance Nonius at 1.0 (0°)
    for pct in [-15, -10, -5, 5]:
        deg = math.log10(1.0 + pct / 100.0) * 360.0
        x1, y1 = polar_to_cart(r_c, deg)
        x2, y2 = polar_to_cart(r_c - 3.5, deg)
        col = "#27AE60" if pct > 0 else "#C0392B"
        ax.plot([x1, x2], [y1, y2], color=col, lw=1.0, zorder=9)
        xt, yt = polar_to_cart(r_c - 5.5, deg)
        lbl = f"{pct:+d}%"
        ax.text(xt, yt, lbl, color=col, fontsize=3.6, fontweight="bold", ha="center", va="center", zorder=10)

    # S-Scale (Sinus) at r = 48.0 mm
    r_s = 48.0
    c_s = plt.Circle((0, 0), r_s, color="#BDC3C7", fill=False, lw=0.7, ls="--", zorder=6)
    ax.add_patch(c_s)

    s_labeled = [6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 50.0, 60.0, 70.0, 90.0]
    for alpha_int in range(60, 901, 5):
        alpha = alpha_int / 10.0
        val = 10.0 * math.sin(math.radians(alpha))
        if val <= 0:
            continue
        deg = math.log10(val) * 360.0

        is_maj = alpha in s_labeled
        t_len = 3.2 if is_maj else 1.6
        x1, y1 = polar_to_cart(r_s, deg)
        x2, y2 = polar_to_cart(r_s + t_len, deg)
        ax.plot([x1, x2], [y1, y2], color="#2980B9", lw=0.7 if is_maj else 0.35, zorder=7)

        if is_maj:
            xt, yt = polar_to_cart(r_s + 5.2, deg)
            rot = calc_readable_rotation(deg)
            ax.text(xt, yt, f"{int(alpha)}°", color="#2980B9", fontsize=3.8, fontweight="bold", ha="center", va="center", rotation=rot, zorder=8)

    # S-Scale Title located cleanly inside S-circle
    ax.text(0, 35.0, "S (SINUS-SKALA FÜR WINDDREIECK)", color="#2980B9", fontsize=5.2, fontweight="bold", ha="center", va="center", zorder=10)

    # Center Titles & Information
    ax.text(0, 18.0, "RÜCKSEITE: RECHENSCHIEBER & S-SKALA", fontsize=7.5, fontweight="bold", color="#2C3E50", ha="center", va="center", zorder=12)
    ax.text(0, 14.0, "JPK 1080 TRUE GRIT · GER 7447", fontsize=5.8, color="#7F8C8D", ha="center", va="center", zorder=12)
    ax.text(0, 10.5, "Multiplikation · Division · Distanz/Zeit · Sinussatz", fontsize=4.8, color="#2980B9", ha="center", va="center", zorder=12)
    ax.text(0, -12.0, "Trennfuge C/D: R = 75.0 mm (Ø 150 mm)", fontsize=5.0, color="#7F8C8D", ha="center", va="center", zorder=12)
    ax.text(0, -16.0, "Sinussatz: a / sin(α) = b / sin(β) = c / sin(γ)", fontsize=4.6, color="#2C3E50", fontstyle="italic", ha="center", va="center", zorder=12)

    # Center Hub & Pin
    hub = plt.Circle((0, 0), 5.0, color="#BDC3C7", ec="#2C3E50", lw=1.0, zorder=18)
    ax.add_patch(hub)
    pin = plt.Circle((0, 0), 2.2, color="#2C3E50", ec="#1A252F", lw=0.8, zorder=19)
    ax.add_patch(pin)

    outfile.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outfile, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def render_rotor_face(
    polar: PolarData,
    outfile: Path,
    dpi: int = 300
):
    """
    Renders high-resolution detail of the Front Rotor Face (Ø 150 mm).
    """
    fig, ax = plt.subplots(figsize=(10, 10), dpi=dpi)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-80, 80)
    ax.set_ylim(-80, 80)

    # Rotor Disc Background
    disc = plt.Circle((0, 0), 75.0, color="#FFFFFF", ec="#2C3E50", lw=1.5, zorder=1)
    ax.add_patch(disc)

    # TRUE WIND Arrow
    ax.annotate(
        "TRUE WIND", xy=(0, 74.5), xytext=(0, 67.5),
        arrowprops=dict(facecolor="#C0392B", edgecolor="#962D22", width=3.0, headwidth=8.0),
        ha="center", va="center", fontsize=7.5, fontweight="bold", color="#C0392B", zorder=12
    )
    ax.text(0, 64.5, "◄ PORT LIFT | STBD LIFT ►", color="#27AE60", fontsize=5.0, fontweight="bold", ha="center", va="center", zorder=12)

    # Shift Ticks
    for s in [1, -1]:
        for shift_deg in [5.0, 10.0, 15.0]:
            d = shift_deg * s
            x1, y1 = polar_to_cart(75.0, d)
            x2, y2 = polar_to_cart(72.8, d)
            ax.plot([x1, x2], [y1, y2], color="#2C3E50", lw=0.8, zorder=7)
            xt, yt = polar_to_cart(71.2, d)
            ax.text(xt, yt, f"{int(shift_deg)}°", color="#2C3E50", fontsize=4.5, ha="center", va="center", zorder=8)
        tx, ty = polar_to_cart(67.8, 11.5 * s)
        txt = "LIFT ▶" if s > 0 else "◀ LIFT"
        ax.text(tx, ty, txt, color="#27AE60", fontsize=5.0, fontweight="bold", ha="center", va="center", rotation=-11.5*s, zorder=12)

    # TACK Sectors (38° to 42°)
    for s in [1, -1]:
        th = [math.radians(a * s) for a in [38.0, 42.0, 42.0, 38.0]]
        r = [66.0, 66.0, 75.0, 75.0]
        xs = [ri * math.sin(ti) for ri, ti in zip(r, th)]
        ys = [ri * math.cos(ti) for ri, ti in zip(r, th)]
        c_fill = "#2ECC71" if s > 0 else "#E74C3C"
        c_edge = "#27AE60" if s > 0 else "#C0392B"
        ax.fill(xs, ys, color=c_fill, alpha=0.35, ec=c_edge, lw=0.8, zorder=7)
        tx, ty = polar_to_cart(70.5, 40.0 * s)
        lbl_tack = "STBD TACK 40°" if s > 0 else "PORT TACK 40°"
        ax.text(tx, ty, lbl_tack, color=c_edge, fontsize=5.2, fontweight="bold", ha="center", va="center", rotation=-40*s, zorder=12)

    # Start Line Bias System (+-90°)
    for s in [1, -1]:
        base_angle = 90.0 * s
        x_in, y_in = polar_to_cart(66.0, base_angle)
        x_out, y_out = polar_to_cart(75.0, base_angle)
        ax.plot([x_in, x_out], [y_in, y_out], color="#2980B9", lw=2.0, zorder=8)

        for b_deg in [5.0, 10.0, 15.0]:
            for s_sgn in [1, -1]:
                b_ang = base_angle + (b_deg * s_sgn)
                x1, y1 = polar_to_cart(75.0, b_ang)
                x2, y2 = polar_to_cart(72.8, b_ang)
                ax.plot([x1, x2], [y1, y2], color="#2980B9", lw=0.8, zorder=7)
                xt, yt = polar_to_cart(71.2, b_ang)
                ax.text(xt, yt, f"{int(b_deg)}°", color="#2980B9", fontsize=4.5, ha="center", va="center", zorder=8)

        tx, ty = polar_to_cart(70.5, base_angle)
        line_name = "BOAT END (RC)" if s > 0 else "PIN END"
        rot_name = -90.0 if s > 0 else 90.0
        ax.text(
            tx, ty, line_name, color="#2980B9", fontsize=5.2, fontweight="bold",
            ha="center", va="center", rotation=rot_name, zorder=12,
            bbox=dict(boxstyle="round,pad=0.25", fc="#FFFFFF", ec="#2980B9", lw=0.6)
        )

        up_ang = base_angle - (9.5 * s)
        tx_up, ty_up = polar_to_cart(67.5, up_ang)
        fav_up = "▲ BOAT FAV" if s > 0 else "PIN FAV ▲"
        ax.text(tx_up, ty_up, fav_up, color="#27AE60", fontsize=4.5, fontweight="bold", ha="center", va="center", rotation=-up_ang, zorder=12)

        down_ang = base_angle + (9.5 * s)
        tx_down, ty_down = polar_to_cart(67.5, down_ang)
        fav_down = "PIN FAV ▼" if s > 0 else "▼ BOAT FAV"
        ax.text(tx_down, ty_down, fav_down, color="#C0392B", fontsize=4.5, fontweight="bold", ha="center", va="center", rotation=-down_ang, zorder=12)

    # GYBE Sectors (145° to 165°)
    for s in [1, -1]:
        th = [math.radians(a * s) for a in [145.0, 165.0, 165.0, 145.0]]
        r = [66.0, 66.0, 75.0, 75.0]
        xs = [ri * math.sin(ti) for ri, ti in zip(r, th)]
        ys = [ri * math.cos(ti) for ri, ti in zip(r, th)]
        c_fill = "#2ECC71" if s > 0 else "#E74C3C"
        c_edge = "#27AE60" if s > 0 else "#C0392B"
        ax.fill(xs, ys, color=c_fill, alpha=0.25, ec=c_edge, lw=0.8, zorder=7)
        tx, ty = polar_to_cart(70.5, 155.0 * s)
        lbl_gybe = "STBD GYBE 155°" if s > 0 else "PORT GYBE 155°"
        ax.text(tx, ty, lbl_gybe, color=c_edge, fontsize=5.0, fontweight="bold", ha="center", va="center", rotation=25*s, zorder=12)

    # Free Sector Compass Ticks
    for deg in range(10, 180, 5):
        if deg <= 18 or (36 <= deg <= 44) or (73 <= deg <= 107) or (143 <= deg <= 167) or deg >= 177:
            continue
        for s in [1, -1]:
            d = deg * s
            is_30 = (deg % 30 == 0)
            l = 3.0 if is_30 else 1.5
            x1, y1 = polar_to_cart(75.0, d)
            x2, y2 = polar_to_cart(75.0 - l, d)
            ax.plot([x1, x2], [y1, y2], color="#2C3E50", lw=0.6, zorder=7)
            if is_30:
                xt, yt = polar_to_cart(69.0, d)
                ax.text(xt, yt, f"{deg}°", color="#2C3E50", fontsize=6.0, fontweight="bold", ha="center", va="center", zorder=8)

    # Titles
    ax.text(0, 46.0, "WEG A: NORMIERTE POLAREN (RATIO)", fontsize=8.0, fontweight="bold", color="#2C3E50", ha="center", va="center", zorder=12)
    ax.text(0, 42.5, "Windpol (0,0) | L = 64 mm | JPK 1080 TRUE GRIT", fontsize=5.8, color="#7F8C8D", ha="center", va="center", zorder=12)
    ax.text(0, 39.5, "Taktik: TWD · Shift/Lift · Tack · Start Line Bias · Gybe", fontsize=4.8, color="#2980B9", ha="center", va="center", zorder=12)

    # Ratio concentric circles
    L = 64.0
    for ratio in [0.2, 0.4, 0.6, 0.8, 1.0]:
        r = ratio * L
        c = plt.Circle((0, 0), r, color="#E0E0E0", fill=False, lw=0.6, ls="--", zorder=5)
        ax.add_patch(c)
        ax.text(r - 1.0, 1.8, f"{ratio:.1f}", color="#95A5A6", fontsize=5.0, ha="right", va="center", zorder=6)

    # Baseline
    ax.plot([0, 0], [0, -L], color="#C0392B", lw=1.5, zorder=8)
    ax.scatter([0], [-L], color="#C0392B", s=20, zorder=9)
    ax.text(0, -L - 2.5, "P1 (180°)", color="#C0392B", fontsize=5.5, fontweight="bold", ha="center", va="top", zorder=10)
    ax.text(0, 7.2, "Windpol (0,0)", color="#C0392B", fontsize=5.5, fontweight="bold", ha="center", va="bottom", zorder=22)

    # Fasskreise (lower half)
    r_clip = 65.2
    awa_angles = [25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 75.0, 90.0, 110.0, 135.0, 155.0]
    for alpha in awa_angles:
        rad = math.radians(alpha)
        sin_a = math.sin(rad)
        cos_a = math.cos(rad)
        if sin_a == 0:
            continue
        r_c = L / (2.0 * sin_a)
        ym = -L / 2.0
        xc_stb = (L / 2.0) * (cos_a / sin_a)
        thetas = np.linspace(-math.radians(180.0 - alpha), math.radians(180.0 - alpha), 90)
        raw_stb = [(xc_stb + r_c * math.cos(t), ym + r_c * math.sin(t)) for t in thetas]

        for s in [1, -1]:
            pts_side = [(s * p[0], p[1]) for p in raw_stb]
            for sub in clip_polyline_to_circle(pts_side, r_clip):
                if len(sub) >= 2:
                    xs, ys = zip(*sub)
                    ax.plot(xs, ys, color="#2980B9", lw=0.45, ls="--", alpha=0.7, zorder=5)

    # Polars JPK 1080
    colors = ["#1F618D", "#2980B9", "#2471A3", "#17A589", "#138D75", "#D4AC0D", "#CA6F1E", "#922B21"]
    crossover_stb, crossover_bb = [], []

    for idx, tws in enumerate(polar.tws_list):
        col = colors[idx % len(colors)]
        curve = polar.curves_raw[idx]
        pts_complex = [complex((pt["bsp"] / tws) * L * math.sin(math.radians(pt["twa"])), (pt["bsp"] / tws) * L * math.cos(math.radians(pt["twa"]))) for pt in curve]
        smooth_pts = catmull_rom_spline(pts_complex, num_points=12)

        stb_pts = [(p.real, p.imag) for p in smooth_pts]
        bb_pts = [(-p.real, p.imag) for p in smooth_pts]

        for s_pts in [stb_pts, bb_pts]:
            for sub in clip_polyline_to_circle(s_pts, r_clip):
                if len(sub) >= 2:
                    xs, ys = zip(*sub)
                    ax.plot(xs, ys, color=col, lw=1.0, zorder=8)

        # Targets
        tgt = polar.vmg_targets[idx]
        beat_r = (tgt["beat_sog"] / tws) * L
        bx, by = polar_to_cart(beat_r, tgt["beat_angle"])
        ax.scatter([bx, -bx], [by, by], color="#E74C3C", edgecolors="#962D22", marker="D", s=18, zorder=11)

        run_r = (tgt["run_sog"] / tws) * L
        rx, ry = polar_to_cart(run_r, tgt["gybe_angle"])
        ax.scatter([rx, -rx], [ry, ry], color="#2ECC71", edgecolors="#27AE60", marker="D", s=18, zorder=11)

        # Crossover point
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
            inter = find_ray_spline_intersection(cross_twa, smooth_pts, sign_y=1.0)
            if inter:
                cx, cy = inter
                crossover_stb.append((cx, cy))
                crossover_bb.append((-cx, cy))
                ax.scatter([cx, -cx], [cy, cy], color="#9B59B6", edgecolors="#8E44AD", marker="^", s=24, zorder=11)

    if len(crossover_stb) >= 2:
        xs, ys = zip(*crossover_stb)
        ax.plot(xs, ys, color="#8E44AD", lw=0.9, ls="--", zorder=10)
        xs_bb, ys_bb = zip(*crossover_bb)
        ax.plot(xs_bb, ys_bb, color="#8E44AD", lw=0.9, ls="--", zorder=10)

    # Center Hub & Pin
    hub = plt.Circle((0, 0), 5.0, color="#BDC3C7", ec="#2C3E50", lw=1.0, zorder=18)
    ax.add_patch(hub)
    pin = plt.Circle((0, 0), 1.6, color="#2C3E50", ec="#1A252F", lw=0.8, zorder=19)
    ax.add_patch(pin)

    outfile.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outfile, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def render_all_previews(
    polar: PolarData,
    out_dir: Path,
    twa_pointer_deg: float = 40.0,
    dpi: int = 300
) -> List[Path]:
    """Renders all 3 high-resolution previews into out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    f_seite_a = out_dir / "gesamtansicht_seite_a_montiert.png"
    render_assembled_montage(polar, f_seite_a, twa_pointer_deg=twa_pointer_deg, dpi=dpi)

    f_seite_b = out_dir / "gesamtansicht_seite_b_montiert.png"
    render_assembled_seite_b(f_seite_b, dpi=dpi)

    f_rotor_face = out_dir / "rotor_vorderseite_weg_a.png"
    render_rotor_face(polar, f_rotor_face, dpi=dpi)

    return [f_seite_a, f_seite_b, f_rotor_face]
