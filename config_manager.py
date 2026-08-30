"""
config_manager.py - Parametric Configuration & Kinematic Geometry Manager
Loads `config.json` and computes all mutually dependent dimensions for the
Nautical Rechenscheibe (Stator, Rotor, Tactical Ruler, Axle Pins, Scales).
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

from polar_parser import PolarData


@dataclass
class ResolvedGeometry:
    """All resolved primary and derived dimensions of the Rechenscheibe."""
    # Base Radial Ring Dimensions
    r_max: float
    band_width: float
    r_log_split: float
    r_boundary: float
    r_main: float

    # Tolerances & Clearances
    r_rotor: float
    r_pocket: float
    center_hole_r: float
    awa_hole_r: float

    # Polar & AWA Dynamics
    max_norm: float
    mm_per_100pct: float
    awa_offset_y: float
    awa_offset: complex

    # Tactical Ruler
    ruler_length: float
    ruler_width: float
    ruler_hub_r: float
    ruler_thickness: float

    # Component Thicknesses
    stator_floor_thickness: float
    stator_rim_height: float
    rotor_thickness: float

    # Center Pin
    center_pin_r: float
    center_pin_length: float
    center_pin_head_r: float
    center_pin_head_thickness: float

    # AWA Pin
    awa_pin_r: float
    awa_pin_length: float
    awa_pin_head_r: float
    awa_pin_head_thickness: float

    # Typography & Ticks
    text_height: float
    polar_label_height: float
    grid_label_height: float
    awa_ray_label_size: float
    vmg_label_size: float
    tick_len_major: float
    tick_len_minor: float
    text_gap: float
    grid_label_gap: float

    # Display & Layers
    render_sail_layers: bool = False

    # Raw / Extended Config dict
    raw_config: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        """Provides a dictionary for chart_generator and stl_generator."""
        return {
            "R_MAX": self.r_max,
            "R_LOG_SPLIT": self.r_log_split,
            "R_BOUNDARY": self.r_boundary,
            "R_MAIN": self.r_main,
            "R_ROTOR": self.r_rotor,
            "R_POCKET": self.r_pocket,
            "HOLE_RADIUS": self.center_hole_r,
            "AWA_HOLE_RADIUS": self.awa_hole_r,
            "MM_PER_100PCT": self.mm_per_100pct,
            "AWA_OFFSET": self.awa_offset,
            "MAX_NORM": self.max_norm,
            "RENDER_SAIL_LAYERS": self.render_sail_layers,
            "TEXT_HEIGHT": self.text_height,
            "POLAR_LABEL_HEIGHT": self.polar_label_height,
            "GRID_LABEL_HEIGHT": self.grid_label_height,
            "AWA_RAY_LABEL_SIZE": self.awa_ray_label_size,
            "VMG_LABEL_SIZE": self.vmg_label_size,
            "TICK_LEN_MAJOR": self.tick_len_major,
            "TICK_LEN_MINOR": self.tick_len_minor,
            "TEXT_GAP": self.text_gap,
            "GRID_LABEL_GAP": self.grid_label_gap,
            "LOG_ZONES": self.raw_config.get("log_zones", []),
            "RULER_LENGTH": self.ruler_length,
            "RULER_WIDTH": self.ruler_width,
            "RULER_HUB_R": self.ruler_hub_r,
            "RULER_THICKNESS": self.ruler_thickness,
            "STATOR_FLOOR": self.stator_floor_thickness,
            "STATOR_RIM": self.stator_rim_height,
            "ROTOR_THICKNESS": self.rotor_thickness,
            "CENTER_PIN_R": self.center_pin_r,
            "CENTER_PIN_LEN": self.center_pin_length,
            "CENTER_PIN_HEAD_R": self.center_pin_head_r,
            "CENTER_PIN_HEAD_THICKNESS": self.center_pin_head_thickness,
            "AWA_PIN_R": self.awa_pin_r,
            "AWA_PIN_LEN": self.awa_pin_length,
            "AWA_PIN_HEAD_R": self.awa_pin_head_r,
            "AWA_PIN_HEAD_THICKNESS": self.awa_pin_head_thickness,
        }

    def print_summary(self):
        """Displays a structured overview of the parametric model."""
        print("=" * 65)
        print("  PARAMETRISCHE GEOMETRIE & ABHÄNGIGKEITEN (config.json)")
        print("=" * 65)
        print(f"  [1] Basiskorpus:")
        print(f"      - Außenradius (R_MAX)         : {self.r_max:.2f} mm (Durchmesser {self.r_max * 2:.1f} mm)")
        print(f"      - Skalenband-Breite           : {self.band_width:.2f} mm")
        print(f"      - Rechenschieber-Teilkreis    : {self.r_log_split:.2f} mm")
        print(f"      - Statorkante / Trennlinie    : {self.r_main:.2f} mm")
        print(f"  [2] Rotor & Passung:")
        print(f"      - Rotor-Außenradius (Laufspiel): {self.r_rotor:.2f} mm")
        print(f"      - Stator-Taschenradius (Spiel) : {self.r_pocket:.2f} mm")
        print(f"      - Scheibendicke Rotor / Rand  : {self.rotor_thickness:.2f} mm / {self.stator_rim_height:.2f} mm")
        print(f"  [3] True-Wind-Achse & AWA-Pol:")
        print(f"      - Max. Bootsgeschw.-Ratio     : {self.max_norm:.2f}")
        print(f"      - Maßstab (100% Windachse)    : {self.mm_per_100pct:.2f} mm")
        print(f"      - AWA/AWS-Pol (Drehpunkt)     : Y = {self.awa_offset_y:.2f} mm")
        print(f"  [4] Taktisches Peil-Lineal:")
        print(f"      - Gesamtlänge (ab AWA-Pol)    : {self.ruler_length:.2f} mm")
        print(f"      - Breite / Dicke              : {self.ruler_width:.2f} mm / {self.ruler_thickness:.2f} mm")
        print(f"      - Drehnabe Radius / Bohrung   : {self.ruler_hub_r:.2f} mm / Ø {self.awa_hole_r * 2:.2f} mm")
        print(f"  [5] Achsstifte:")
        print(f"      - Zentralstift (Senkkopf)     : Ø {self.center_pin_r * 2:.2f} mm x {self.center_pin_length:.2f} mm (Kopfhöhe {self.center_pin_head_thickness:.2f} mm)")
        print(f"      - AWA-Drehstift               : Ø {self.awa_pin_r * 2:.2f} mm x {self.awa_pin_length:.2f} mm (Kopfhöhe {self.awa_pin_head_thickness:.2f} mm)")
        print("=" * 65)


class ConfigManager:
    """Loads config.json and resolves all geometric interdependencies."""

    DEFAULT_CONFIG_PATH = Path("config.json")

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Loads configuration from JSON file with fallback defaults."""
        path = Path(config_path) if config_path else cls.DEFAULT_CONFIG_PATH
        if not path.exists():
            raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {path.resolve()}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    @classmethod
    def resolve(cls, cfg: Dict[str, Any], polar_data: PolarData) -> ResolvedGeometry:
        """
        Computes all derived geometric dimensions based on config parameters and polar data.
        Enforces strict kinematic constraints between stator, rotor, ruler, and pins.
        """
        dim = cfg.get("dimensions", {})
        thk = cfg.get("thicknesses", {})
        rul = cfg.get("ruler", {})
        scl = cfg.get("scales_and_typography", {})

        # 1. Base Dimensions
        r_max = float(dim.get("outer_radius_mm", 57.5))
        text_h = float(scl.get("text_height_mm", 3.8))
        tick_maj = float(scl.get("tick_len_major_mm", 1.4))
        tick_min = float(scl.get("tick_len_minor_mm", 0.7))
        text_gap = float(scl.get("text_gap_mm", -0.5))

        # Scale ring width calculation
        effective_text_h = text_h * 0.9
        band_width = tick_maj + text_gap + effective_text_h

        # Concentric scale boundaries
        r_log_split = r_max - band_width
        r_boundary = r_log_split - band_width
        r_main = r_boundary - band_width

        # 2. Tolerances & Clearances
        rotor_clearance = float(dim.get("rotor_clearance_mm", 0.25))
        pocket_clearance = float(dim.get("pocket_clearance_mm", 0.15))
        pin_clearance = float(dim.get("pin_clearance_mm", 0.10))

        r_rotor = r_main - rotor_clearance
        r_pocket = r_main + pocket_clearance

        center_hole_r = float(dim.get("center_hole_radius_mm", 1.60))
        awa_hole_r = float(dim.get("awa_hole_radius_mm", 1.30))

        # 3. True-Wind Scaling & AWA Origin
        scale_factor = float(dim.get("true_wind_scale_factor", 1.00))
        max_norm = float(polar_data.max_ratio)
        mm_per_100pct = (scale_factor * r_main) / max_norm
        awa_offset_y = -mm_per_100pct
        awa_offset = complex(awa_offset_y, 0.0)

        # 4. Thicknesses
        stator_floor = float(thk.get("stator_floor_mm", 1.6))
        stator_rim = float(thk.get("stator_rim_height_mm", 1.8))
        rotor_thk = float(thk.get("rotor_disc_mm", 1.8))
        ruler_thk = float(thk.get("ruler_arm_mm", 1.2))

        center_pin_head_thk = float(thk.get("center_pin_head_thickness_mm", 0.7))
        awa_pin_head_thk = float(thk.get("awa_pin_head_thickness_mm", 0.6))

        # 5. Tactical Ruler Geometry
        ruler_width = float(rul.get("width_mm", 6.0))
        ruler_hub_r = float(rul.get("hub_radius_mm", 4.0))
        thumb_tab_ext = float(rul.get("thumb_tab_extension_mm", 5.38))
        # Ruler length reaches from AWA pivot (y = -mm_per_100pct) across R_MAX plus thumb tab
        ruler_length = round(abs(awa_offset_y) + r_max + thumb_tab_ext, 1)

        # 6. Pins Dimensions
        center_pin_r = round(center_hole_r - pin_clearance, 2)
        center_pin_len = round(stator_floor + rotor_thk + 0.4, 2)
        center_pin_head_r = round(center_hole_r + 1.9, 2)

        awa_pin_r = round(awa_hole_r - pin_clearance, 2)
        awa_pin_len = round(rotor_thk + ruler_thk + 0.2, 2)
        awa_pin_head_r = round(awa_hole_r + 1.7, 2)

        return ResolvedGeometry(
            r_max=r_max,
            band_width=band_width,
            r_log_split=r_log_split,
            r_boundary=r_boundary,
            r_main=r_main,
            r_rotor=r_rotor,
            r_pocket=r_pocket,
            center_hole_r=center_hole_r,
            awa_hole_r=awa_hole_r,
            max_norm=max_norm,
            mm_per_100pct=mm_per_100pct,
            awa_offset_y=awa_offset_y,
            awa_offset=awa_offset,
            ruler_length=ruler_length,
            ruler_width=ruler_width,
            ruler_hub_r=ruler_hub_r,
            ruler_thickness=ruler_thk,
            stator_floor_thickness=stator_floor,
            stator_rim_height=stator_rim,
            rotor_thickness=rotor_thk,
            center_pin_r=center_pin_r,
            center_pin_length=center_pin_len,
            center_pin_head_r=center_pin_head_r,
            center_pin_head_thickness=center_pin_head_thk,
            awa_pin_r=awa_pin_r,
            awa_pin_length=awa_pin_len,
            awa_pin_head_r=awa_pin_head_r,
            awa_pin_head_thickness=awa_pin_head_thk,
            render_sail_layers=bool(cfg.get("display", {}).get("render_sail_layers", False)),
            text_height=text_h,
            polar_label_height=float(scl.get("polar_label_height_mm", 4.5)),
            grid_label_height=float(scl.get("grid_label_height_mm", 4.0)),
            awa_ray_label_size=float(scl.get("awa_ray_label_size_mm", 3.5)),
            vmg_label_size=float(scl.get("vmg_label_size_mm", 3.0)),
            tick_len_major=tick_maj,
            tick_len_minor=tick_min,
            text_gap=text_gap,
            grid_label_gap=float(scl.get("grid_label_gap_mm", 1.0)),
            raw_config=cfg
        )
