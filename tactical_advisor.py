#!/usr/bin/env python3
"""
tactical_advisor.py - Tactical Sailing Advisor & VPP Interpolator
JPK 1080 (TRUE GRIT / GER 7447)

Acts as the tactical on-board intelligence:
1. Interpolates VPP target speed, heel angle, AWA, AWS, and reefing factors for arbitrary conditions.
2. Compares headsail vs. asymmetric spinnaker vs. symmetric spinnaker performance.
3. Simulates virtual reefs for mainsail, jibs, and A3 gennaker using geometric reduction.
4. Determines optimal sail combination and performance check against the VPP envelope.

Usage:
    python tactical_advisor.py --hdg 300 --twd 345 --tws 16
    python tactical_advisor.py --hdg 210 --twd 345 --tws 22
"""

import sys
import json
import copy
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from polar_parser import PolarData


class VppTacticalEngine:
    """
    Interpolates VPP polar performance curves across TWS (wind speed) and TWA (wind angle).
    Handles both optimal performance envelopes and specific sail configurations.
    """
    def __init__(self, polars_data: Dict[str, Any]):
        self.polars = polars_data

    def interpolate_curve(self, curve_data: List[Dict[str, Any]], tws: float, twa: float) -> Optional[Dict[str, float]]:
        if not curve_data:
            return None

        sorted_curves = sorted(curve_data, key=lambda x: x["tws"])
        lower_candidates = [c for c in sorted_curves if c["tws"] <= tws]
        upper_candidates = [c for c in sorted_curves if c["tws"] >= tws]

        lower = lower_candidates[-1] if lower_candidates else sorted_curves[0]
        upper = upper_candidates[0] if upper_candidates else sorted_curves[-1]

        if lower["tws"] == upper["tws"]:
            tws_fac = 0.0
        else:
            tws_fac = (tws - lower["tws"]) / (upper["tws"] - lower["tws"])

        def get_vals_at_twa(curve_points: List[Dict], t_twa: float) -> Dict[str, float]:
            twas = np.array([p["twa"] for p in curve_points])
            keys = ["bsp", "heel", "reef", "flat", "awa", "aws", "vmg"]
            res = {}
            for k in keys:
                vals = np.array([p.get(k, 0.0) for p in curve_points])
                res[k] = float(np.interp(t_twa, twas, vals))
            return res

        vals_low = get_vals_at_twa(lower["curve"], abs(twa))
        vals_high = get_vals_at_twa(upper["curve"], abs(twa))

        final = {}
        for k in vals_low:
            final[k] = vals_low[k] + (vals_high[k] - vals_low[k]) * tws_fac

        return final

    def get_targets(self, tws: float, twa: float) -> Optional[Dict[str, float]]:
        """Returns target performance from the optimal ('Best Performance') envelope."""
        data = self.polars.get("optimal", {}).get("data", []) or self.polars.get("BestPerf", {}).get("data", [])
        return self.interpolate_curve(data, tws, twa)

    def compare_configurations(self, tws: float, twa: float) -> Dict[str, Any]:
        """Compares theoretical boat speeds of Headsail vs. Asymmetric vs. Symmetric."""
        speeds = {}

        # 1. Headsail / Jib
        h_data = self.polars.get("headsail", {}).get("data", []) or self.polars.get("Jib", {}).get("data", [])
        h_res = self.interpolate_curve(h_data, tws, twa)
        speeds['HEAD'] = h_res['bsp'] if h_res else 0.0
        speeds['HEAD_DETAILS'] = h_res

        # 2. Asymmetric Spinnaker Centerline / Rüssel
        a_data = self.polars.get("asymmetric", {}).get("data", []) or self.polars.get("AsymCL", {}).get("data", [])
        a_res = self.interpolate_curve(a_data, tws, twa)
        speeds['ASYM'] = a_res['bsp'] if a_res else 0.0
        speeds['ASYM_CL'] = a_res['bsp'] if a_res else 0.0
        speeds['ASYM_DETAILS'] = a_res

        # 3. Asymmetric Spinnaker Pole / Spibaum
        ap_data = self.polars.get("AsymPole", {}).get("data", [])
        ap_res = self.interpolate_curve(ap_data, tws, twa)
        speeds['ASYM_POLE'] = ap_res['bsp'] if ap_res else 0.0
        speeds['ASYM_POLE_DETAILS'] = ap_res

        # 4. Symmetric Spinnaker Pole / Spibaum
        s_data = self.polars.get("symmetric", {}).get("data", []) or self.polars.get("Sym", {}).get("data", [])
        s_res = self.interpolate_curve(s_data, tws, twa)
        speeds['SYM'] = s_res['bsp'] if s_res else 0.0
        speeds['SYM_DETAILS'] = s_res

        return speeds


class SailStrategist:
    """
    Manages the boat's sail inventory, models reefed sails with geometry,
    and solves the optimal sail selection based on TWA and TWS.
    """
    def __init__(self, sail_inventory: List[Dict], rig_config: Dict, main_reef_drops: Tuple[float, float] = (1.66, 4.11)):
        self.inventory = copy.deepcopy(sail_inventory)
        self.rig_p = float(rig_config.get("p", {}).get("value", 13.98) or 13.98)
        self.reef_drops = main_reef_drops

        self.max_jib_area = 0.0
        self.max_main_area = 0.0
        self.max_spi_area = 0.0
        self.active_main = None

        self._analyze_inventory()
        self._generate_virtual_jib_reefs()
        self._generate_virtual_main_reefs()
        self._generate_virtual_spi_reefs()
        self._classify_spinnakers()

    def _analyze_inventory(self):
        for s in self.inventory:
            area = s.get("area", 0)
            stype = s.get("type", "")
            if stype == "HEAD":
                self.max_jib_area = max(self.max_jib_area, area)
            elif stype in ["SYM", "ASYM"]:
                self.max_spi_area = max(self.max_spi_area, area)
            elif stype == "MAIN":
                if area > self.max_main_area:
                    self.max_main_area = area
                if s.get("attributes", {}).get("Active") == "1":
                    self.active_main = s

        if not self.active_main and self.max_main_area > 0:
            mains = [s for s in self.inventory if s.get("type") == "MAIN"]
            if mains:
                self.active_main = max(mains, key=lambda x: x.get("area", 0))

    def _generate_virtual_jib_reefs(self):
        reff_config = {"#60273": 1.25, "#62013": 1.06}
        new_sails = []

        for s in self.inventory:
            if s.get("orc_sail_id") in reff_config:
                reduction = reff_config[s["orc_sail_id"]]
                m = s.get("measurements", {})
                attr = s.get("attributes", {})
                jl = float(m.get("jl", 0) or attr.get("JIBLUFF", 0) or attr.get("HLU", 0) or 0)
                lpg = float(m.get("lpg", 0) or attr.get("LPG", 0) or attr.get("HLP", 0) or 0)

                if jl > 0 and lpg > 0:
                    width_at_cut = lpg * (1 - (reduction / jl))
                    removed_area = reduction * (lpg + width_at_cut) / 2.0
                    new_area = s.get("area", 0) - removed_area

                    v = copy.deepcopy(s)
                    v["internal_id"] += "_REEF"
                    v["name"] = f"{s.get('name')} (Reff -{reduction}m)"
                    v["area"] = new_area
                    v["is_virtual"] = True
                    v["strategy_type"] = "HEAD_REEF"
                    v["parent_area"] = s.get("area", 0)
                    new_sails.append(v)
        self.inventory.extend(new_sails)

    def _generate_virtual_main_reefs(self):
        if not self.active_main or self.rig_p == 0:
            return

        m_area = self.active_main.get("area", 0)
        new_sails = []

        for i, drop in enumerate(self.reef_drops, 1):
            if drop >= self.rig_p:
                continue
            e_approx = 2 * m_area / self.rig_p
            width_at_cut = e_approx * (1 - (drop / self.rig_p))
            removed = drop * (e_approx + width_at_cut) / 2.0

            v = copy.deepcopy(self.active_main)
            v["internal_id"] += f"_R{i}"
            v["name"] = f"MAIN (Reff {i}: -{drop:.2f}m)"
            v["area"] = m_area - removed
            v["is_virtual"] = True
            v["strategy_type"] = "MAIN_REEF"
            v["parent_area"] = m_area
            new_sails.append(v)

        self.inventory.extend(new_sails)

    def _generate_virtual_spi_reefs(self):
        target_orc_id = "#62037"
        new_sails = []

        for s in self.inventory:
            if s.get("orc_sail_id") == target_orc_id:
                orig_area = s.get("area", 0)
                m = s.get("measurements", {})
                sfl = float(m.get("sfl", 0) or m.get("asf", 0) or 7.62)
                avg_drop = 1.40
                removed_strip_area = sfl * avg_drop
                new_area = orig_area - removed_strip_area

                v = copy.deepcopy(s)
                v["internal_id"] += "_REEF"
                v["name"] = "A3 (Reff: SLU-1.2m/SLE-1.6m)"
                v["area"] = new_area
                v["is_virtual"] = True
                v["strategy_type"] = "REACHER"
                v["parent_area"] = orig_area
                new_sails.append(v)

        self.inventory.extend(new_sails)

    def _classify_spinnakers(self):
        for s in self.inventory:
            if s.get("type") in ["SYM", "ASYM"]:
                m = s.get("measurements", {})
                shw = float(m.get("shw", 0) or m.get("amg", 0) or 0)
                sfl = float(m.get("sfl", 0) or m.get("asf", 0) or 0)
                if sfl > 0:
                    s["strategy_type"] = "REACHER" if (shw / sfl) < 0.75 else "RUNNER"

    def determine_best_config(self, twa: float, tws: float, comparison_speeds: Dict[str, float], reef_factor: float) -> Dict[str, Any]:
        abs_twa = abs(twa)
        speed_head = comparison_speeds.get("HEAD", 0)
        speed_asym = comparison_speeds.get("ASYM", 0)
        speed_sym = comparison_speeds.get("SYM", 0)
        max_spi_speed = max(speed_asym, speed_sym)

        mode = "UPWIND"
        use_spi = False

        if abs_twa > 60:
            if max_spi_speed > (speed_head + 0.2):
                mode = "DOWNWIND"
                use_spi = True

        mains = [self.active_main] + [s for s in self.inventory if s.get("strategy_type") == "MAIN_REEF"]
        mains = [m for m in mains if m is not None]
        target_main = self.max_main_area * reef_factor
        best_main = min(mains, key=lambda m: abs(m.get("area", 0) - target_main)) if mains else None

        best_front = None
        if not use_spi:
            jibs = [s for s in self.inventory if s.get("type") == "HEAD" or s.get("strategy_type") == "HEAD_REEF"]
            target_jib = self.max_jib_area * reef_factor
            if jibs:
                best_front = min(jibs, key=lambda j: abs(j.get("area", 0) - target_jib))
                if reef_factor > 0.98:
                    if best_main and best_main.get("is_virtual"):
                        best_main = self.active_main
                    if best_front.get("is_virtual"):
                        pid = best_front["internal_id"].split("_REEF")[0]
                        best_front = next((x for x in jibs if x["internal_id"] == pid), best_front)
        else:
            needed_type = "RUNNER" if abs_twa > 130 else "REACHER"
            if speed_sym > speed_asym + 0.2:
                needed_type = "SYM"

            candidates = []
            if needed_type == "SYM":
                candidates = [s for s in self.inventory if s.get("type") == "SYM"]
            else:
                candidates = [s for s in self.inventory if s.get("strategy_type") == needed_type]

            if not candidates:
                candidates = [s for s in self.inventory if s.get("type") in ["SYM", "ASYM"]]

            if candidates:
                candidates.sort(key=lambda x: x.get("area", 0), reverse=True)
                if tws > 20 and len(candidates) > 1:
                    best_front = candidates[-1]
                else:
                    best_front = candidates[0]

        return {
            'main': best_main,
            'head': best_front,
            'mode': mode,
            'speed_potential': max_spi_speed if use_spi else speed_head
        }


def get_tactical_advice(hdg: float, twd: float, tws: float, data_path: Path, main_drops: Tuple[float, float] = (1.66, 4.11)):
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
            data = json.load(f)
        inventory = data.get("sail_inventory", [])
        rig = data.get("rig_configuration", {})
        polars = data.get("polars", {}).get("configurations", {})

    strategist = SailStrategist(inventory, rig, main_drops)
    engine = VppTacticalEngine(polars)

    diff = (twd - hdg) % 360
    twa = 360 - diff if diff > 180 else diff

    targets = engine.get_targets(tws, twa)
    if not targets:
        print("[ERROR] Keine VPP-Zieldaten für diese Bedingungen gefunden.")
        return

    speeds = engine.compare_configurations(tws, twa)
    rec = strategist.determine_best_config(twa, tws, speeds, targets.get("reef", 1.0))

    # Print Formatted Tactical Dashboard
    source_label = data_path.name
    print("\n" + "=" * 72)
    print(f"  TAKTISCHER BORDCOMPUTER - JPK 1080 (TRUE GRIT / GER 7447)")
    print(f"  Datenbasis: {source_label} (ORC VPP Digital Twin)")
    print("=" * 72)
    print(f"  SITUATION: Kurs {hdg:.0f}° | Wind {twd:.0f}° @ {tws:.1f} kn -> TWA: {twa:.1f}°")
    print("-" * 72)

    print(f"  [1. VPP SOLL-WERTE (Best Performance)]")
    print(f"    Target Boat Speed (BSP) : {targets['bsp']:.2f} kn")
    print(f"    Velocity Made Good (VMG): {targets['vmg']:.2f} kn")
    print(f"    Scheinbarer Wind (AWA)  : {targets['awa']:.1f}° @ {targets['aws']:.1f} kn")
    print(f"    Soll-Krängung (Heel)    : {targets['heel']:.1f}°")
    print(f"    VPP-Reff-Faktor          : {targets['reef']:.2f} (Flat: {targets['flat']:.2f})")

    print(f"\n  [2. GESCHWINDIGKEITS-POTENZIAL NACH SEGELTYP]")
    head_spd = speeds.get('HEAD', 0.0)
    print(f"    Fock (J1)             : {head_spd:.2f} kn (Basis ohne Spi)")

    asym_cl = speeds.get('ASYM_CL', 0.0)
    if asym_cl > 0:
        d_asym = asym_cl - head_spd
        print(f"    Gennaker A2 (Rüssel)  : {asym_cl:.2f} kn ({d_asym:+.2f} kn ggü. Fock)")

    asym_pole = speeds.get('ASYM_POLE', 0.0)
    if asym_pole > 0:
        d_ap = asym_pole - head_spd
        print(f"    Gennaker A2 (Baum)    : {asym_pole:.2f} kn ({d_ap:+.2f} kn ggü. Fock)")

    sym_spd = speeds.get('SYM', 0.0)
    if sym_spd > 0:
        d_sym = sym_spd - head_spd
        print(f"    Spinnaker S2 (Baum)   : {sym_spd:.2f} kn ({d_sym:+.2f} kn ggü. Fock)")

    print(f"    Optimal (BestPerf)    : {targets['bsp']:.2f} kn")

    print(f"\n  [3. EMPFOHLENE SEGELKONFIGURATION ({rec['mode']})]")
    if rec['main']:
        print(f"    Großsegel: {rec['main']['name']} ({rec['main']['area']:.1f} m²)")
    if rec['head']:
        print(f"    Vorsegel : {rec['head']['name']} ({rec['head']['area']:.1f} m²)")

    diff_speed = rec['speed_potential'] - targets['bsp']
    if abs(diff_speed) < 0.1:
        perf_status = "Optimale Konfiguration (100% Target Speed)"
    elif diff_speed < -0.1:
        perf_status = f"{abs(diff_speed):.2f} kn unter absolutem Optimum"
    else:
        perf_status = f"{diff_speed:+.2f} kn über theoretischem Optimum"
    print(f"    Status   : {perf_status}")
    print("=" * 72 + "\n")


def main():
    default_data = Path(__file__).parent / "data" / "249116.slk"
    if not default_data.exists():
        default_data = Path(__file__).parent / "data" / "ORC_SpeedGuide_TRUE_GRIT_27.12.2025.json"

    parser = argparse.ArgumentParser(description="Tactical Sailing Advisor for JPK 1080 (GER 7447)")
    parser.add_argument("--hdg", type=float, default=300.0, help="Compass Heading (0-360°)")
    parser.add_argument("--twd", type=float, default=345.0, help="True Wind Direction (0-360°)")
    parser.add_argument("--tws", type=float, default=18.0, help="True Wind Speed in knots")
    parser.add_argument("--data", "--json", dest="data", type=Path, default=default_data, help="Path to ORC SLK or JSON polar file")
    parser.add_argument("--reef1", type=float, default=1.66, help="Main reef 1 drop in meters")
    parser.add_argument("--reef2", type=float, default=4.11, help="Main reef 2 drop in meters")

    args = parser.parse_args()
    if not args.data.exists():
        print(f"[ERROR] Datei {args.data} nicht gefunden.")
        sys.exit(1)

    get_tactical_advice(args.hdg, args.twd, args.tws, args.data, (args.reef1, args.reef2))


if __name__ == "__main__":
    main()
