#!/usr/bin/env python3
"""
rechenscheibe.py - Master Software Suite for Dual-Sided Nautical Rechenscheibe V1.0
Yacht: JPK 1080 (GER 7447 - TRUE GRIT)

Architecture:
- 180 mm Sandwich-Kassette (Top Stator Ring, Bottom Stator Base, Rotating Disc, Central Pointer, Axle Pin)
- Seite A (Vorderseite): Weg A Normierte Polaren (L=64 mm), TackingMaster Taktikring (TWD, Shift/Lift, Tack/Gybe, Start Line Bias), Fasskreise
- Seite B (Rückseite): Zirkularer Rechenschieber (C-Skala, D-Skala, S-Sinusskala, Performance-Nonius)

Generates:
1. Watertight 3D Printable STL models (output/stl/)
2. CAM / Laser-ready Vector SVG files (output/svg/)
3. High-resolution 300 DPI preview renders (output/previews/)
"""

import sys
import argparse
from pathlib import Path

from polar_parser import PolarData
from stl_generator import generate_all_stl_models
from vector_engine import generate_all_laser_svgs
from preview_engine import render_all_previews


def format_file_size(filepath: Path) -> str:
    """Returns human-readable file size."""
    try:
        size = filepath.stat().st_size
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        elif size >= 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size} B"
    except Exception:
        return "N/A"


def main():
    parser = argparse.ArgumentParser(
        description="Master Generator Suite: 180 mm Sandwich Rechenscheibe JPK 1080 (GER 7447 Edition V1.0)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate everything: 3D STL models, 2D Laser SVGs, and 300 DPI previews (default if none specified)"
    )
    parser.add_argument(
        "--stl",
        action="store_true",
        help="Generate 3D-printable watertight STL models into output/stl/"
    )
    parser.add_argument(
        "--svg",
        action="store_true",
        help="Generate laser cut/engrave CAM SVG files into output/svg/"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Render 300 DPI high-resolution PNG previews into output/previews/"
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).parent / "data" / "249116.slk",
        help="Path to ORC polar SLK file (default: data/249116.slk)"
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(__file__).parent / "output",
        help="Root output directory (default: output)"
    )
    parser.add_argument(
        "--twa",
        type=float,
        default=40.0,
        help="Pointer True Wind Angle for preview overlay in degrees (default: 40.0)"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution in DPI for PNG preview generation (default: 300)"
    )

    args = parser.parse_args()

    # Default to generating all if no specific subsystem is selected
    run_all = args.all or (not args.stl and not args.svg and not args.preview)
    run_stl = run_all or args.stl
    run_svg = run_all or args.svg
    run_preview = run_all or args.preview

    # Validate polar data file
    polar_path = args.data
    if not polar_path.is_absolute():
        polar_path = Path(__file__).parent / polar_path

    if not polar_path.exists():
        print(f"[FEHLER] Polardatei nicht gefunden: {polar_path}")
        sys.exit(1)

    out_dir = args.outdir
    if not out_dir.is_absolute():
        out_dir = Path(__file__).parent / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(" NAUTISCHE RECHENSCHEIBE V1.0 - JPK 1080 (GER 7447 - TRUE GRIT)")
    print(" 180 mm Sandwich-Kassette · TackingMaster · ORC Polaren · Rechenschieber")
    print("=" * 72)
    print(f"[*] Polardaten:    {polar_path.name}")
    print(f"[*] Zielordner:    {out_dir}")

    # Load Polar Data
    print("\n[1/4] Lade und analysiere ORC-Polardaten...")
    polar = PolarData(polar_path)
    print(f"      -> {len(polar.tws_list)} Windstärken geladen: {', '.join(str(int(w)) + 'kt' for w in polar.tws_list)}")
    print(f"      -> VMG Targets: Upwind Beat {polar.vmg_targets[0]['beat_angle']:.1f}° bis {polar.vmg_targets[-1]['beat_angle']:.1f}°")
    print(f"      -> Segel-Polaren: {', '.join(polar.sail_polars.keys())}")

    # 1. STL 3D-Druck Modellerzeugung
    if run_stl:
        print("\n[2/4] Generiere wasserdichte 3D-Druck-Modelle (STL)...")
        stl_dir = out_dir / "stl"
        stl_files = generate_all_stl_models(stl_dir)
        for stl_path in stl_files:
            size_str = format_file_size(stl_path)
            print(f"      -> [OK] stl/{stl_path.name:<28} ({size_str})")

    # 2. SVG Laser- und CAM-Vektorgrafiken
    if run_svg:
        print("\n[3/4] Generiere fertigungsgerechte Laser-Vektordateien (SVG)...")
        svg_dir = out_dir / "svg"
        svg_files = generate_all_laser_svgs(polar, svg_dir)
        for svg_path in svg_files:
            size_str = format_file_size(svg_path)
            print(f"      -> [OK] svg/{svg_path.name:<32} ({size_str})")

    # 3. Hochauflösende 300 DPI Previews
    if run_preview:
        print(f"\n[4/4] Rendere hochauflösende Vorschauen ({args.dpi} DPI)...")
        prev_dir = out_dir / "previews"
        prev_files = render_all_previews(polar, prev_dir, twa_pointer_deg=args.twa, dpi=args.dpi)
        for prev_path in prev_files:
            size_str = format_file_size(prev_path)
            print(f"      -> [OK] previews/{prev_path.name:<34} ({size_str})")

    print("\n" + "=" * 72)
    print(" [FERTIG] Release V1.0 erfolgreich generiert!")
    print(f" Speicherort: {out_dir}")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
