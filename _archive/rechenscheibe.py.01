#!/usr/bin/env python3
"""
rechenscheibe.py - Nautical Rechenscheibe / Tactical Sailing Computer Generator
JPK 1080 (GER 7447) Edition

Generates:
1. 3D-Printable STL files (Stator Base, Rotor Dial, Center Axle Pin)
2. Laser-Engraving DXF files (CAM color-coded for LightBurn / LaserGRBL)
3. High-resolution PNG visual preview

Usage:
    python rechenscheibe.py [--csv GER7447_polars.csv] [--radius 57.5] [--outdir output]
"""

import argparse
import sys
import math
from pathlib import Path
import numpy as np

# Local modules
from polar_parser import PolarData
from config_manager import ConfigManager, ResolvedGeometry
from stl_generator import (
    generate_rotor_stl,
    generate_stator_stl,
    generate_tactical_ruler_stl,
    generate_flush_center_pin_stl,
    generate_awa_pivot_pin_stl
)
from chart_generator import (
    DEFAULT_CONFIG,
    NauticalChart,
    build_rechenscheibe,
    build_ruler_dxf
)
import ezdxf


def export_separated_dxf(source_doc, out_path: Path, include_layers: list):
    """Creates a filtered DXF containing only the specified layers."""
    new_doc = ezdxf.new(source_doc.dxfversion)
    new_msp = new_doc.modelspace()

    # Copy layer definitions
    for name in include_layers:
        if name in source_doc.layers:
            layer = source_doc.layers.get(name)
            new_doc.layers.new(name=name, dxfattribs={"color": layer.color})

    # Copy matching entities
    src_msp = source_doc.modelspace()
    for entity in src_msp:
        if entity.dxf.layer in include_layers:
            new_msp.add_entity(entity.copy())

    new_doc.saveas(str(out_path))


def main():
    parser = argparse.ArgumentParser(
        description="Parametric Nautical Rechenscheibe Generator (JPK 1080 GER 7447 Edition)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "config.json",
        help="Path to central config.json parameter file (default: config.json)"
    )
    parser.add_argument("--data", type=Path, default=None, help="Override path to ORC JSON or CSV polar file")
    parser.add_argument("--radius", type=float, default=None, help="Override outer radius R_MAX in mm")
    parser.add_argument("--hole", type=float, default=None, help="Override center axle hole radius in mm")
    parser.add_argument("--outdir", type=Path, default=None, help="Override output directory")
    parser.add_argument("--sail-layers", action="store_true", help="Render individual sail polars (Jib, Asym, Sym) on dedicated DXF layers")
    parser.add_argument("--no-stl", action="store_true", help="Skip STL 3D-mesh generation")
    parser.add_argument("--no-dxf", action="store_true", help="Skip DXF laser vector generation")
    parser.add_argument("--no-preview", action="store_true", help="Skip PNG preview generation")

    args = parser.parse_args()

    # 1. Load Central Configuration
    cfg_path = args.config
    if not cfg_path.exists():
        print(f"[ERROR] Konfigurationsdatei {cfg_path} nicht gefunden!")
        sys.exit(1)

    raw_cfg = ConfigManager.load(cfg_path)

    # Apply optional CLI overrides to config
    if args.data is not None:
        raw_cfg.setdefault("project", {})["polar_file"] = str(args.data)
    if args.radius is not None:
        raw_cfg.setdefault("dimensions", {})["outer_radius_mm"] = args.radius
    if args.hole is not None:
        raw_cfg.setdefault("dimensions", {})["center_hole_radius_mm"] = args.hole
    if args.outdir is not None:
        raw_cfg.setdefault("project", {})["output_dir"] = str(args.outdir)
    if args.sail_layers:
        raw_cfg.setdefault("display", {})["render_sail_layers"] = True

    # Output directory
    out_dir_str = raw_cfg.get("project", {}).get("output_dir", "output")
    out_dir = Path(out_dir_str)
    if not out_dir.is_absolute():
        out_dir = Path(__file__).parent / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    polar_file_str = raw_cfg.get("project", {}).get("polar_file", "data/ORC_SpeedGuide_TRUE_GRIT_27.12.2025.json")
    polar_path = Path(polar_file_str)
    if not polar_path.is_absolute():
        polar_path = Path(__file__).parent / polar_path

    if not polar_path.exists():
        print(f"[ERROR] Polardatei {polar_path} nicht gefunden!")
        sys.exit(1)

    # 2. Load Polar Data
    polar_data = PolarData(polar_path)

    # 3. Resolve Geometric Interdependencies
    geo = ConfigManager.resolve(raw_cfg, polar_data)
    geo.print_summary()

    # 4. Generate 3D-Print STL Files
    if not args.no_stl:
        print("\n[*] Erzeuge 3D-Druck-Modelle (STL)...")
        f_stator = generate_stator_stl(
            out_dir / "rechenscheibe_stator_basis.stl",
            r_max=geo.r_max,
            r_pocket=geo.r_pocket,
            r_hole=geo.center_hole_r,
            floor_thickness=geo.stator_floor_thickness,
            rim_height=geo.stator_rim_height
        )
        f_rotor = generate_rotor_stl(
            out_dir / "rechenscheibe_rotor_drehscheibe.stl",
            r_rotor=geo.r_rotor,
            r_center_hole=geo.center_hole_r,
            awa_offset_y=geo.awa_offset_y,
            r_awa_hole=geo.awa_hole_r,
            thickness=geo.rotor_thickness
        )
        f_ruler = generate_tactical_ruler_stl(
            out_dir / "rechenscheibe_lineal.stl",
            length=geo.ruler_length,
            width=geo.ruler_width,
            r_hub=geo.ruler_hub_r,
            r_hole=geo.awa_hole_r,
            thickness=geo.ruler_thickness
        )
        f_center_pin = generate_flush_center_pin_stl(
            out_dir / "rechenscheibe_achsstift_senkkopf.stl",
            r_pin=geo.center_pin_r,
            r_head=geo.center_pin_head_r,
            head_thickness=geo.center_pin_head_thickness,
            pin_length=geo.center_pin_length
        )
        f_awa_pin = generate_awa_pivot_pin_stl(
            out_dir / "rechenscheibe_achsstift_awa.stl",
            r_pin=geo.awa_pin_r,
            r_head=geo.awa_pin_head_r,
            head_thickness=geo.awa_pin_head_thickness,
            pin_length=geo.awa_pin_length
        )
        print(f"    -> [OK] {f_stator.name} (Basisscheibe mit Pass-Tasche)")
        print(f"    -> [OK] {f_rotor.name} (Innenscheibe mit AWA-Bohrung)")
        print(f"    -> [OK] {f_ruler.name} (Drehbares Peil-Lineal am AWA-Pol)")
        print(f"    -> [OK] {f_center_pin.name} (Flacher Senkkopf-Zentralstift)")
        print(f"    -> [OK] {f_awa_pin.name} (Drehstift für AWA-Lineal)")

    # 5. Generate DXF Laser Vectors & Visual Preview
    if not args.no_dxf or not args.no_preview:
        print("\n[*] Berechne Vektorgrafiken und Laser-Ebenen...")
        geo_dict = geo.as_dict()
        chart = NauticalChart(geo_dict)
        build_rechenscheibe(chart, geo_dict, polar_data)

        if not args.no_dxf:
            # 5a. Complete Master DXF
            f_master_dxf = out_dir / "rechenscheibe_komplett.dxf"
            chart.doc.saveas(str(f_master_dxf))
            print(f"    -> [OK] {f_master_dxf.name} (Gesamt-Ansicht)")

            # 5b. Rotor-only DXF
            rotor_layers = [
                "CUT_REFERENCE", "ENGRAVE_AWA", "ENGRAVE_POLARS", "ENGRAVE_TEXT", "ENGRAVE_VMG"
            ]
            if geo.render_sail_layers:
                rotor_layers.extend(["ENGRAVE_POLAR_JIB", "ENGRAVE_POLAR_ASYM", "ENGRAVE_POLAR_SYM"])
            f_rotor_dxf = out_dir / "laser_rotor_drehscheibe.dxf"
            export_separated_dxf(chart.doc, f_rotor_dxf, rotor_layers)
            print(f"    -> [OK] {f_rotor_dxf.name} (Nur Innenscheibe für Lasergravur)")

            # 5c. Stator-only DXF
            f_stator_dxf = out_dir / "laser_stator_aussenring.dxf"
            export_separated_dxf(chart.doc, f_stator_dxf, [
                "CUT_REFERENCE", "ENGRAVE_COMPASS", "ENGRAVE_LOG", "ENGRAVE_TEXT"
            ])
            print(f"    -> [OK] {f_stator_dxf.name} (Nur Außenring für Lasergravur)")

            # 5d. Ruler-only DXF
            f_ruler_dxf = out_dir / "laser_lineal.dxf"
            build_ruler_dxf(
                f_ruler_dxf,
                length=geo.ruler_length,
                width=geo.ruler_width,
                r_hub=geo.ruler_hub_r,
                r_hole=geo.awa_hole_r,
                mm_per_100pct=geo.mm_per_100pct
            )
            print(f"    -> [OK] {f_ruler_dxf.name} (Lineal mit AWS-Skala für Lasergravur/Cut)")

        if not args.no_preview:
            # Visualize the ruler arm on top of the preview chart
            import matplotlib.patches as patches
            preview_cfg = raw_cfg.get("preview", {})
            awa_deg = float(preview_cfg.get("ruler_awa_angle_deg", 28.0))
            dpi_val = int(preview_cfg.get("dpi", 300))

            awa_rad = math.radians(awa_deg)
            r_len = geo.ruler_length - 2.0
            r_w = geo.ruler_width
            p0 = np.array([0.0, geo.awa_offset_y])
            dir_vec = np.array([math.sin(awa_rad), math.cos(awa_rad)])
            norm_vec = np.array([-math.cos(awa_rad), math.sin(awa_rad)])

            p1 = p0 + dir_vec * r_len
            p2 = p1 + norm_vec * r_w
            p3 = p0 + norm_vec * r_w

            ruler_poly = patches.Polygon(
                [p0, p1, p2, p3],
                closed=True,
                facecolor='#ff9800',
                edgecolor='#e65100',
                alpha=0.38,
                linewidth=1.2,
                zorder=20
            )
            chart.ax.add_patch(ruler_poly)
            # Reading edge line (Collinear with pivot)
            chart.ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color='#d50000', linewidth=1.5, linestyle='-', zorder=21)
            chart.ax.plot([p0[0]], [p0[1]], marker='o', markersize=6, color='#d50000', zorder=22)
            # Text note
            lbl_dist = min(75.0, r_len * 0.75)
            lbl_pos = p0 + dir_vec * lbl_dist + norm_vec * (r_w + 3.0)
            chart.ax.text(
                lbl_pos[0], lbl_pos[1],
                f"Tactical Ruler (AWA = {awa_deg:.0f}°)",
                fontsize=9, color='#e65100', fontweight='bold',
                rotation=-awa_deg, ha='center', va='center', zorder=23
            )

            f_preview = out_dir / "rechenscheibe_preview.png"
            chart.fig.savefig(str(f_preview), dpi=dpi_val, bbox_inches='tight', pad_inches=0.05)
            print(f"    -> [OK] {f_preview.name} ({dpi_val} DPI hochauflösende Bildvorschau mit Lineal)")

    print("\n" + "=" * 65)
    print(f"Fertig! Alle Dateien befinden sich im Ordner:")
    print(f"  {out_dir.resolve()}")
    print("=" * 65)


if __name__ == "__main__":
    main()
