#!/usr/bin/env python3
"""
route_optimizer.py - Tactical GPX Route Optimizer with VMG Strategy
JPK 1080 (TRUE GRIT / GER 7447)

Imports GPX course routes and calculates for each leg:
1. Bearing & Distance (Haversine formula in nautical miles)
2. True Wind Angle (TWA) and Tack (Port/Starboard)
3. Tactical Strategy: Direct vs. VMG Upwind Tacking vs. VMG Downwind Gybing
4. Optimal Target Speed (BSP) and Velocity Made Good (VMG)
5. Sail Combination: Mainsail reef level and Headsail / Spinnaker choice
6. Estimated Time Enroute (ETE) per leg and total race time

Usage:
    python route_optimizer.py [--gpx data/Kursdaten.gpx] [--twd 345] [--tws 18]
"""

import sys
import math
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Local tactical engine
from tactical_advisor import VppTacticalEngine, SailStrategist
from polar_parser import PolarData
import json


class GeoMath:
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Computes distance in nautical miles between two WGS84 coordinates."""
        r_earth_nm = 3440.065
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
        return r_earth_nm * c

    @staticmethod
    def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Computes initial true bearing in degrees from point 1 to point 2."""
        y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
        x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
            math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lon2 - lon1))
        theta = math.atan2(y, x)
        return (math.degrees(theta) + 360.0) % 360.0


def get_vmg_angles(polars_data: Dict[str, Any], tws: float) -> Tuple[float, float]:
    """
    Calculates the true VMG optimal angles for beat and run by maximizing
    speed * cos(TWA).
    """
    opt_data = polars_data.get("optimal", {}).get("data", []) or polars_data.get("BestPerf", {}).get("data", [])
    if not opt_data:
        return (40.0, 150.0)

    closest_curve = min(opt_data, key=lambda x: abs(x["tws"] - tws))["curve"]

    best_upwind_vmg = -1.0
    best_upwind_angle = 40.0
    best_downwind_vmg = -1.0
    best_downwind_angle = 150.0

    for p in closest_curve:
        twa = p["twa"]
        bsp = p["bsp"]
        if twa < 90:
            vmg = bsp * math.cos(math.radians(twa))
            if vmg > best_upwind_vmg:
                best_upwind_vmg = vmg
                best_upwind_angle = twa
        elif twa > 110:
            vmg = bsp * abs(math.cos(math.radians(twa)))
            if vmg > best_downwind_vmg:
                best_downwind_vmg = vmg
                best_downwind_angle = twa

    return (best_upwind_angle, best_downwind_angle)


def parse_gpx_route(gpx_path: Path) -> List[Tuple[float, float, str]]:
    """Extracts (lat, lon, name) points from a GPX file."""
    tree = ET.parse(gpx_path)
    root = tree.getroot()
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}

    points = []
    # Search rtept or trkpt or wpt
    elements = root.findall(".//gpx:rtept", ns) or root.findall(".//rtept")
    if not elements:
        elements = root.findall(".//gpx:trkpt", ns) or root.findall(".//trkpt")
    if not elements:
        elements = root.findall(".//gpx:wpt", ns) or root.findall(".//wpt")

    for idx, elem in enumerate(elements):
        lat = float(elem.get("lat"))
        lon = float(elem.get("lon"))
        name_elem = elem.find("gpx:name", ns) if 'gpx' in ns else elem.find("name")
        name = name_elem.text.strip() if name_elem is not None and name_elem.text else f"WP{idx+1}"
        points.append((lat, lon, name))

    return points


def optimize_route(gpx_path: Path, data_path: Path, twd: float, tws: float, main_drops: Tuple[float, float] = (1.66, 4.11)):
    is_slk = data_path.suffix.lower() == ".slk"
    if is_slk:
        p_obj = PolarData(data_path)
        polars = {}
        for s_name, tws_dict in p_obj.sail_polars.items():
            curve_list = []
            for tws_k in sorted(tws_dict.keys()):
                curve_list.append({"tws": tws_k, "curve": tws_dict[tws_k]})
            polars[s_name] = {"data": curve_list}

        json_meta_path = data_path.parent / "ORC_SpeedGuide_TRUE_GRIT_27.12.2025.json"
        if json_meta_path.exists():
            with open(json_meta_path, "r", encoding="utf-8") as f:
                j_meta = json.load(f)
            inventory = j_meta.get("sail_inventory", [])
            rig = j_meta.get("rig_configuration", {})
        else:
            inventory = []
            rig = {}
    else:
        with open(data_path, "r", encoding="utf-8") as f:
            orc_data = json.load(f)
        inventory = orc_data.get("sail_inventory", [])
        rig = orc_data.get("rig_configuration", {})
        polars = orc_data.get("polars", {}).get("configurations", {})

    strategist = SailStrategist(inventory, rig, main_drops)
    engine = VppTacticalEngine(polars)

    waypoints = parse_gpx_route(gpx_path)
    if len(waypoints) < 2:
        print(f"[ERROR] GPX-Datei {gpx_path} enthält weniger als 2 Wegpunkte.")
        return

    beat_angle, gybe_angle = get_vmg_angles(polars, tws)

    print("=" * 95)
    print(f"  ROUTEN-OPTIMIERER MIT VMG-STRATEGIE - JPK 1080 (TRUE GRIT / GER 7447)")
    print(f"  Datenbasis: {data_path.name}")
    print("=" * 95)
    print(f"  WETTER: Windrichtung {twd:.0f}° | Windstärke {tws:.1f} kn")
    print(f"  VMG-OPTIMA BEI {tws:.0f} KN: Beat Angle = {beat_angle:.1f}° | Gybe Angle = {gybe_angle:.1f}°")
    print("-" * 95)
    print(f"  {'Leg':<4} | {'Von -> Nach':<20} | {'Dist':<7} | {'HDG':<5} | {'TWA':<6} | {'Strategie':<9} | {'Target':<7} | {'ETE':<7} | Segelwahl")
    print("  " + "-" * 91)

    total_dist = 0.0
    total_time_hours = 0.0

    for i in range(len(waypoints) - 1):
        lat1, lon1, name1 = waypoints[i]
        lat2, lon2, name2 = waypoints[i+1]

        dist_nm = GeoMath.haversine_distance(lat1, lon1, lat2, lon2)
        hdg = GeoMath.calculate_bearing(lat1, lon1, lat2, lon2)

        diff = (twd - hdg) % 360
        geo_twa = 360 - diff if diff > 180 else diff
        tack = "BB" if diff > 180 else "Stb"

        # Determine sailing strategy:
        # If the course is closer to the wind than the optimal beat angle -> VMG Tacking required!
        # If the course is deeper than the optimal gybe angle -> VMG Gybing required!
        if abs(geo_twa) < beat_angle:
            strategy = "VMG Kreuz"
            sailed_twa = beat_angle
            # Sailing distance increases when tacking: dist / cos(bearing - course)
            angle_off = math.radians(beat_angle - abs(geo_twa))
            eff_dist = dist_nm / math.cos(angle_off) if math.cos(angle_off) > 0.1 else dist_nm * 1.4
        elif abs(geo_twa) > gybe_angle:
            strategy = "VMG Halse"
            sailed_twa = gybe_angle
            angle_off = math.radians(abs(geo_twa) - gybe_angle)
            eff_dist = dist_nm / math.cos(angle_off) if math.cos(angle_off) > 0.1 else dist_nm * 1.2
        else:
            strategy = "Direkt"
            sailed_twa = abs(geo_twa)
            eff_dist = dist_nm

        targets = engine.get_targets(tws, sailed_twa)
        comp_speeds = engine.compare_configurations(tws, sailed_twa)

        if targets:
            bsp = targets["bsp"]
            rec = strategist.determine_best_config(sailed_twa, tws, comp_speeds, targets.get("reef", 1.0))
            m_name = rec['main']['name'] if rec['main'] else "MAIN"
            h_name = rec['head']['name'] if rec['head'] else "HEAD"

            time_hours = eff_dist / bsp if bsp > 0 else 0.0
            total_dist += dist_nm
            total_time_hours += time_hours

            mins = int(time_hours * 60)
            ete_str = f"{mins // 60:02d}h {mins % 60:02d}m"

            leg_str = f"{name1[:9]}->{name2[:9]}"
            twa_str = f"{geo_twa:.0f}° {tack}"
            print(f"  {i+1:<4} | {leg_str:<20} | {dist_nm:5.2f} nm | {hdg:03.0f}° | {twa_str:<6} | {strategy:<9} | {bsp:4.2f} kn | {ete_str:<7} | {m_name} + {h_name}")

    total_mins = int(total_time_hours * 60)
    print("  " + "-" * 91)
    print(f"  GESAMT: Distanz: {total_dist:.2f} nm | Voraussichtliche Gesamtzeit: {total_mins // 60:02d}h {total_mins % 60:02d}m")
    print("=" * 95 + "\n")


def main():
    default_data = Path(__file__).parent / "data" / "249116.slk"
    if not default_data.exists():
        default_data = Path(__file__).parent / "data" / "ORC_SpeedGuide_TRUE_GRIT_27.12.2025.json"

    parser = argparse.ArgumentParser(description="GPX Tactical Route Optimizer with VMG Strategy")
    parser.add_argument("--gpx", type=Path, default=Path(__file__).parent / "data" / "Kursdaten.gpx", help="Path to GPX file")
    parser.add_argument("--data", "--json", dest="data", type=Path, default=default_data, help="Path to ORC SLK or JSON polar file")
    parser.add_argument("--twd", type=float, default=345.0, help="True Wind Direction in degrees")
    parser.add_argument("--tws", type=float, default=16.0, help="True Wind Speed in knots")

    args = parser.parse_args()
    if not args.gpx.exists():
        print(f"[ERROR] GPX-Datei {args.gpx} nicht gefunden.")
        sys.exit(1)
    if not args.data.exists():
        print(f"[ERROR] Datendatei {args.data} nicht gefunden.")
        sys.exit(1)

    optimize_route(args.gpx, args.data, args.twd, args.tws)


if __name__ == "__main__":
    main()
