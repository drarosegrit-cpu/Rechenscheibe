#!/usr/bin/env python3
"""
config_manager.py - Zentraler parametrischer Geometrie- & Konfigurationsmanager
Projekt: Nautische Rechenscheibe JPK 1080 (GER 7447 - TRUE GRIT)

Aufgabe:
- Lädt die primären Konstruktionsparameter aus `config.json`.
- Berechnet alle abhängigen Maße (Stator, Rotor, Kompassrose, Polaren, C/D/S-Skalen, Zeiger)
  über definierte geometrische Abhängigkeitsregeln konsistent und automatisch.
- Stellt den Generatoren (vector_engine, stl_generator, preview_engine) ein
  zentrales, typsicheres Geometrie- und Layer-Objekt zur Verfügung.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ResolvedGeometry:
    """
    Vollständig aufgelöste geometrische Maße der 180-mm-Sandwich-Rechenscheibe.
    Alle abhängigen Werte werden aus den Basisparametern berechnet.
    """
    # 1. Primäre Radien & Fenstermaße (in mm)
    rotor_radius: float                  # Radius der drehbaren Mittelscheibe / Sichtfenster (z.B. 75.0 mm -> Ø 150 mm)
    stator_rim_width: float              # Radiale Breite des Gehäuserands (z.B. 15.0 mm)
    stator_outer_radius: float           # Gehäuse-Außenradius = rotor_radius + stator_rim_width (90.0 mm -> Ø 180 mm)
    stator_window_radius: float          # Sichtfenster-Ausschnitt = rotor_radius (75.0 mm)

    # 2. Befestigung & Freiräume (in mm)
    screw_nominal_d: float               # Schrauben-Nenndurchmesser (3.0 mm für M3)
    screw_head_d: float                  # Schraubenkopf-Durchmesser (6.0 mm für M3 Senkkopf)
    screw_count: int                     # Anzahl Schrauben (6 Stück)
    screw_pcd_radius: float              # Teilkreis-Radius der Schrauben (88.0 mm -> PCD Ø 176 mm)
    screw_head_inner_limit: float        # Innenkante der Schraubenköpfe (85.0 mm)

    # 3. Ergonomie & Daumen-Bedienung (in mm)
    thumb_tabs_extension: float          # Überstand der 4 Daumen-Tabs über Gehäuserand (3.0 mm)
    thumb_tabs_outer_radius: float       # Außenradius der Tabs (93.0 mm -> Ø 186 mm)
    thumb_tabs_count: int                # Anzahl Tabs (4 Stück bei 45°, 135°, 225°, 315°)
    thumb_tabs_angles: List[float]       # Mittenwinkel der Tabs
    thumb_tabs_arc_deg: float            # Bogenbreite der Tabs (15.0°)

    # 4. Polaren & Aerodynamik (Weg A, in mm)
    polar_norm_ratio: float              # Verhältnis Basislänge L zu Rotorradius (0.85333 -> L = 64.0 mm)
    polar_norm_length: float             # Basislänge OP1 vom Windpol zum Gegenpol P1 (64.0 mm)

    # 5. Skalenradien Vorder- und Rückseite (in mm)
    tactical_rim_width: float            # Breite des Taktikrings am Rotorrand (9.0 mm)
    tactical_rim_inner_radius: float     # Innenradius des Taktikrings (66.0 mm)
    stator_compass_ticks_inner: float    # Innenradius Kompassrose-Teilstriche (75.8 mm)
    stator_compass_ticks_outer: float    # Außenradius Kompassrose-Teilstriche (79.2 mm)
    stator_compass_text_radius: float    # Radius der Gradzahlen (AUSSEN bei 82.5 mm)

    c_scale_radius: float                # C-Skala auf Rotor Rückseite (74.5 mm)
    d_scale_radius: float                # D-Skala auf Stator Boden (75.5 mm)
    s_scale_radius: float                # S-Sinusskala auf Rotor Rückseite (65.0 mm)

    # 6. Dicken, Toleranzen & Zeiger (in mm)
    rotor_thickness: float               # Dicke der Drehscheibe (2.0 mm)
    stator_cover_thickness: float        # Dicke des Gehäusedeckels (2.2 mm)
    stator_base_thickness: float         # Dicke des Gehäusebodens (4.0 mm)
    pointer_thickness: float             # Dicke der Acryl-Zeigerarme (1.4 mm)
    radial_clearance: float              # Laufspiel radial (0.5 mm)
    axial_clearance: float               # Laufspiel axial (0.4 mm)

    axle_pin_nominal_radius: float       # Schaftradius Achsbolzen (1.5 mm -> Ø 3.0 mm)
    axle_hole_radius: float              # Bohrungsradius mit Passungsspiel (1.6 mm -> Ø 3.2 mm)
    axle_pin_total_length: float         # Gesamte Schaftlänge Achsbolzen (8.8 mm)

    pointer_length_front: float          # Länge des Vorderseiten-Zeigers (85.0 mm)
    pointer_length_back: float           # Länge des Rückseiten-Läufers (86.0 mm)


class ConfigManager:
    """
    Verwaltet das Laden und Auflösen der Konfiguration aus `config.json`.
    """
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"
        self.config_path = Path(config_path)
        self.data = self._load_json()
        self.geometry = self._resolve_geometry()

    def _load_json(self) -> Dict[str, Any]:
        """Lädt die JSON-Datei mit Fallback auf Standardwerte."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _resolve_geometry(self) -> ResolvedGeometry:
        """
        Berechnet alle abhängigen Dimensionen aus den Basis-Parametern.
        Gewährleistet mathematische Konsistenz über alle Bauteile.
        """
        bg = self.data["base_geometry"]

        r_rotor = float(bg["rotor_radius_mm"])
        w_stator = float(bg["stator_rim_width_mm"])
        r_stator = r_rotor + w_stator

        screw_nom_d = float(bg["screw_nominal_diameter_mm"])
        screw_head_d = float(bg["screw_head_diameter_mm"])
        screw_pcd_r = r_stator - 2.0
        screw_head_in = screw_pcd_r - (screw_head_d / 2.0)

        tabs_ext = float(bg["thumb_tabs_extension_mm"])
        r_tabs = r_stator + tabs_ext

        norm_ratio = float(bg["polar_norm_ratio"])
        l_polar = r_rotor * norm_ratio

        w_tactical = float(bg["tactical_rim_width_mm"])
        r_tactical_in = r_rotor - w_tactical

        # Stator Kompassrose (Ticks nach innen, Ziffern nach außen)
        r_comp_in = r_rotor + 0.8       # 75.8 mm (knapp außerhalb des Sichtfensters 75.0 mm)
        r_comp_out = r_rotor + 4.2      # 79.2 mm (Ende der 10°-Teilstriche)
        r_comp_txt = r_rotor + 7.5      # 82.5 mm (Mittenradius der Gradbeschriftungen)

        # Rechenschieber Skalen (C, D, S)
        r_c = r_rotor - 0.5             # 74.5 mm
        r_d = r_rotor + 0.5             # 75.5 mm
        r_s = r_rotor - 10.0            # 65.0 mm

        # Dicken & Toleranzen
        t_rotor = float(bg["rotor_thickness_mm"])
        t_cov = float(bg["stator_cover_thickness_mm"])
        t_base = float(bg["stator_base_thickness_mm"])
        t_ptr = float(bg["pointer_thickness_mm"])
        c_rad = float(bg["radial_clearance_mm"])
        c_ax = float(bg["axial_clearance_mm"])

        r_pin = float(bg["axle_pin_nominal_radius_mm"])
        r_hole = float(bg["axle_hole_radius_mm"])
        # Schaftlänge = Boden + Deckel + 2x Zeiger + 2x Axialspiel
        l_pin = t_base + t_cov + (t_ptr * 2.0) + (c_ax * 2.0)

        p_len_front = r_stator - 5.0    # 85.0 mm
        p_len_back = r_stator - 4.0     # 86.0 mm

        return ResolvedGeometry(
            rotor_radius=r_rotor,
            stator_rim_width=w_stator,
            stator_outer_radius=r_stator,
            stator_window_radius=r_rotor,
            screw_nominal_d=screw_nom_d,
            screw_head_d=screw_head_d,
            screw_count=int(bg["screw_count"]),
            screw_pcd_radius=screw_pcd_r,
            screw_head_inner_limit=screw_head_in,
            thumb_tabs_extension=tabs_ext,
            thumb_tabs_outer_radius=r_tabs,
            thumb_tabs_count=int(bg["thumb_tabs_count"]),
            thumb_tabs_angles=[float(a) for a in bg["thumb_tabs_angles_deg"]],
            thumb_tabs_arc_deg=float(bg["thumb_tabs_arc_deg"]),
            polar_norm_ratio=norm_ratio,
            polar_norm_length=l_polar,
            tactical_rim_width=w_tactical,
            tactical_rim_inner_radius=r_tactical_in,
            stator_compass_ticks_inner=r_comp_in,
            stator_compass_ticks_outer=r_comp_out,
            stator_compass_text_radius=r_comp_txt,
            c_scale_radius=r_c,
            d_scale_radius=r_d,
            s_scale_radius=r_s,
            rotor_thickness=t_rotor,
            stator_cover_thickness=t_cov,
            stator_base_thickness=t_base,
            pointer_thickness=t_ptr,
            radial_clearance=c_rad,
            axial_clearance=c_ax,
            axle_pin_nominal_radius=r_pin,
            axle_hole_radius=r_hole,
            axle_pin_total_length=l_pin,
            pointer_length_front=p_len_front,
            pointer_length_back=p_len_back,
        )

    @property
    def layers(self) -> Dict[str, Any]:
        """Gibt alle Laser-/CAM-Layer-Konfigurationen zurück."""
        return self.data.get("laser_layers", {})

    @property
    def tactical(self) -> Dict[str, Any]:
        """Gibt die Taktikring-Parameter (Tack, Gybe, Shift, Bias, AWA) zurück."""
        return self.data.get("tactical_settings", {})

    @property
    def polars(self) -> Dict[str, Any]:
        """Gibt die Polardiagramm-Parameter (Cutoff, Farben, Ratios) zurück."""
        return self.data.get("polar_settings", {})

    @property
    def typography(self) -> Dict[str, Any]:
        """Gibt Schriftart- und Größendefinitionen zurück."""
        return self.data.get("typography", {})

    @property
    def project(self) -> Dict[str, Any]:
        """Gibt Projektmetadaten zurück."""
        return self.data.get("project", {})


# Globale Instanz zum bequemen Importieren
CONFIG = ConfigManager()
GEOM = CONFIG.geometry
