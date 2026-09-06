#!/usr/bin/env python3
"""
config_manager.py - Parametric Geometry & Consistency Manager
Calculates all derived nautical and mechanical dimensions for the
dual-sided Rechenscheibe:
- Front Side: Polar speed diagram, AWA grid, Compass rose, Central Ratio Pointer
- Back Side : Rotating Logarithmic Slide Rule (Stator outer ring vs Rotor inner ring)
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from polar_parser import PolarData


@dataclass
class ResolvedGeometry:
    # Primary Radii
    r_max: float               # Stator outer radius (mm)
    r_split: float             # Parting line between Stator and Rotor (mm)
    r_rotor: float             # Rotor outer radius with running clearance (mm)
    r_pocket: float            # Stator pocket radius with pocket clearance (mm)
    center_hole_r: float       # Central axle hole radius (mm)

    # Aerodynamic / Vector Math
    max_norm: float            # Max boat speed / TWS ratio (e.g. 1.20)
    mm_per_100pct: float       # Scale in mm for 100% True Wind
    awa_offset_y: float        # Y position of the True Wind foot / AWA origin (mm)
    awa_offset: complex        # Complex coordinate (0, -Y_AWA)

    # Pointer / Central Ruler
    pointer_length: float      # Total length of central pointer from (0,0) (mm)
    pointer_width: float       # Width of pointer arm (mm)
    pointer_hub_r: float       # Hub radius at center (mm)
    pointer_thickness: float   # Thickness of pointer (mm)

    # Thicknesses & 3D Layering
    stator_core_wall: float    # Central separator floor between front and back (mm)
    front_rim_height: float    # Depth of front pocket / rim height (mm)
    back_rim_height: float     # Depth of back pocket / rim height (mm)
    front_rotor_disc: float    # Thickness of front polar disc (mm)
    back_rotor_disc: float     # Thickness of back slide rule disc (mm)

    # Axle Pins
    center_pin_r: float
    center_pin_length: float
    center_pin_head_r: float
    center_pin_head_thickness: float

    # Typography & Ticks
    compass_text_h: float
    compass_tick_maj: float
    compass_tick_min: float
    awa_text_h: float
    awa_tick_maj: float
    awa_tick_min: float
    polar_label_height: float
    grid_label_height: float
    log_text_h: float
    log_tick_maj: float
    log_tick_min: float

    # Display & Layers
    render_sail_layers: bool = False

    # Raw Config
    raw_config: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        """Provides a dictionary interface for chart and stl generators."""
        return {
            "R_MAX": self.r_max,
            "R_SPLIT": self.r_split,
            "R_MAIN": self.r_split,      # Alias for separation radius
            "R_ROTOR": self.r_rotor,
            "R_POCKET": self.r_pocket,
            "HOLE_RADIUS": self.center_hole_r,
            "MAX_NORM": self.max_norm,
            "MM_PER_100PCT": self.mm_per_100pct,
            "AWA_OFFSET": self.awa_offset,
            "AWA_OFFSET_Y": self.awa_offset_y,
            "POINTER_LENGTH": self.pointer_length,
            "POINTER_WIDTH": self.pointer_width,
            "POINTER_HUB_R": self.pointer_hub_r,
            "POINTER_THICKNESS": self.pointer_thickness,
            "STATOR_CORE_WALL": self.stator_core_wall,
            "FRONT_RIM": self.front_rim_height,
            "BACK_RIM": self.back_rim_height,
            "FRONT_ROTOR_THICKNESS": self.front_rotor_disc,
            "BACK_ROTOR_THICKNESS": self.back_rotor_disc,
            "CENTER_PIN_R": self.center_pin_r,
            "CENTER_PIN_LEN": self.center_pin_length,
            "CENTER_PIN_HEAD_R": self.center_pin_head_r,
            "CENTER_PIN_HEAD_THICKNESS": self.center_pin_head_thickness,
            "COMPASS_TEXT_H": self.compass_text_h,
            "COMPASS_TICK_MAJ": self.compass_tick_maj,
            "COMPASS_TICK_MIN": self.compass_tick_min,
            "AWA_TEXT_H": self.awa_text_h,
            "AWA_TICK_MAJ": self.awa_tick_maj,
            "AWA_TICK_MIN": self.awa_tick_min,
            "POLAR_LABEL_HEIGHT": self.polar_label_height,
            "GRID_LABEL_HEIGHT": self.grid_label_height,
            "LOG_TEXT_H": self.log_text_h,
            "LOG_TICK_MAJ": self.log_tick_maj,
            "LOG_TICK_MIN": self.log_tick_min,
            "RENDER_SAIL_LAYERS": self.render_sail_layers,
            "RAW_CONFIG": self.raw_config
        }

    def print_summary(self):
        print("=" * 68)
        print("  DOPPELSEITIGE PARAMETRISCHE RECHENSCHEIBE (config.json)")
        print("=" * 68)
        print(f"  [1] Basiskorpus & Trennfuge:")
        print(f"      - Außenradius (R_MAX)         : {self.r_max:.2f} mm (Ø {self.r_max * 2:.1f} mm)")
        print(f"      - Trennfuge Stator/Rotor      : {self.r_split:.2f} mm")
        print(f"      - Rotor-Außenradius (Laufspiel): {self.r_rotor:.2f} mm")
        print(f"      - Stator-Taschenradius (Spiel) : {self.r_pocket:.2f} mm")
        print(f"  [2] Vorderseite (Taktik & Polaren):")
        print(f"      - Maßstab (100% Windachse)    : {self.mm_per_100pct:.2f} mm")
        print(f"      - AWA/AWS-Pol (Windfußpunkt)  : Y = {self.awa_offset_y:.2f} mm")
        print(f"      - Äußere Skala auf Stator     : 360° Kompassrose (von 0,0)")
        print(f"      - Innere Skala auf Stator     : AWA-Winkel (vom unteren Pol)")
        print(f"  [3] Zentraler Zeiger (Ratio V_BS / TWS):")
        print(f"      - Länge (ab Zentrum)          : {self.pointer_length:.2f} mm")
        print(f"      - Breite / Dicke              : {self.pointer_width:.2f} mm / {self.pointer_thickness:.2f} mm")
        print(f"      - Gravierte Ratio-Skala       : 0.0 bis {self.max_norm:.2f}")
        print(f"  [4] Rückseite (Logarithmischer Rechenschieber):")
        print(f"      - Stator-Außenring (fest)     : Äußere Log-Skala (1 bis 10/100)")
        print(f"      - Rotor-Innenscheibe (drehbar): Innere Log-Skala (1 bis 10/100)")
        print(f"      - Trennkante                  : Genau bei R = {self.r_split:.2f} mm!")
        print(f"  [5] 3D-Druck Stärken & Zentralachse:")
        print(f"      - Stator Trennwand / Randhöhe : {self.stator_core_wall:.2f} mm / {self.front_rim_height:.2f} mm")
        print(f"      - Rotor-Dicke (Front / Back)  : {self.front_rotor_disc:.2f} mm / {self.back_rotor_disc:.2f} mm")
        print(f"      - Zentralstift                : Ø {self.center_pin_r * 2:.2f} mm x {self.center_pin_length:.2f} mm")
        print("=" * 68)


class ConfigManager:
    @staticmethod
    def load(cfg_path: Optional[Path] = None) -> Dict[str, Any]:
        if cfg_path is None:
            cfg_path = Path(__file__).parent / "config.json"
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def resolve(cfg: Dict[str, Any], polar_data: PolarData) -> ResolvedGeometry:
        dim = cfg.get("dimensions", {})
        thk = cfg.get("thicknesses", {})
        ptr = cfg.get("pointer", {})
        scl = cfg.get("scales_and_typography", {})
        disp = cfg.get("display", {})

        r_max = float(dim.get("outer_radius_mm", 57.5))
        r_split = float(dim.get("split_radius_mm", 47.0))
        rotor_clearance = float(dim.get("rotor_clearance_mm", 0.25))
        pocket_clearance = float(dim.get("pocket_clearance_mm", 0.15))
        pin_clearance = float(dim.get("pin_clearance_mm", 0.10))
        center_hole_r = float(dim.get("center_hole_radius_mm", 1.60))

        r_rotor = r_split - rotor_clearance
        r_pocket = r_split + pocket_clearance

        # Max Ratio & Aerodynamic Scale
        max_norm = max(float(ptr.get("max_ratio", 1.20)), getattr(polar_data, "max_ratio", 1.20))
        scale_fac = float(dim.get("true_wind_scale_factor", 1.00))
        mm_per_100pct = (scale_fac * r_rotor) / max_norm
        awa_offset_y = -mm_per_100pct
        awa_offset = complex(0.0, awa_offset_y)

        # Pointer (Central Ruler)
        tab_ext = float(ptr.get("thumb_tab_extension_mm", 4.5))
        pointer_length = r_max + tab_ext
        pointer_width = float(ptr.get("width_mm", 6.0))
        pointer_hub_r = float(ptr.get("hub_radius_mm", 4.5))
        pointer_thk = float(thk.get("pointer_arm_mm", 1.2))

        # Thicknesses
        stator_core = float(thk.get("stator_core_wall_mm", 1.6))
        front_rim = float(thk.get("front_rim_height_mm", 1.8))
        back_rim = float(thk.get("back_rim_height_mm", 1.8))
        front_rotor_thk = float(thk.get("front_rotor_disc_mm", 1.8))
        back_rotor_thk = float(thk.get("back_rotor_disc_mm", 1.8))

        # Central Pin
        center_pin_r = center_hole_r - pin_clearance
        pin_len = pointer_thk + front_rotor_thk + stator_core + back_rotor_thk + 0.4
        pin_head_r = pointer_hub_r
        pin_head_thk = float(thk.get("center_pin_head_thickness_mm", 1.0))

        return ResolvedGeometry(
            r_max=r_max,
            r_split=r_split,
            r_rotor=r_rotor,
            r_pocket=r_pocket,
            center_hole_r=center_hole_r,
            max_norm=max_norm,
            mm_per_100pct=mm_per_100pct,
            awa_offset_y=awa_offset_y,
            awa_offset=awa_offset,
            pointer_length=pointer_length,
            pointer_width=pointer_width,
            pointer_hub_r=pointer_hub_r,
            pointer_thickness=pointer_thk,
            stator_core_wall=stator_core,
            front_rim_height=front_rim,
            back_rim_height=back_rim,
            front_rotor_disc=front_rotor_thk,
            back_rotor_disc=back_rotor_thk,
            center_pin_r=center_pin_r,
            center_pin_length=pin_len,
            center_pin_head_r=pin_head_r,
            center_pin_head_thickness=pin_head_thk,
            compass_text_h=float(scl.get("compass_text_h_mm", 3.2)),
            compass_tick_maj=float(scl.get("compass_tick_maj_mm", 1.6)),
            compass_tick_min=float(scl.get("compass_tick_min_mm", 0.9)),
            awa_text_h=float(scl.get("awa_text_h_mm", 2.8)),
            awa_tick_maj=float(scl.get("awa_tick_maj_mm", 1.4)),
            awa_tick_min=float(scl.get("awa_tick_min_mm", 0.7)),
            polar_label_height=float(scl.get("polar_label_height_mm", 4.5)),
            grid_label_height=float(scl.get("grid_label_height_mm", 3.8)),
            log_text_h=float(scl.get("log_text_h_mm", 3.0)),
            log_tick_maj=float(scl.get("log_tick_maj_mm", 2.0)),
            log_tick_min=float(scl.get("log_tick_min_mm", 1.0)),
            render_sail_layers=bool(disp.get("render_sail_layers", False)),
            raw_config=cfg
        )
