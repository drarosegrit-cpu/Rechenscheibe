#!/usr/bin/env python3
"""
orc_extractor.py - ORC DXT & Speed Guide HTML Extractor
JPK 1080 (TRUE GRIT / GER 7447)

Parses:
1. ORC XML Certificate / Input file (.dxt)
   - Boat metadata (Yacht Name, Sail Number, Class, GPH)
   - Rig configuration (P, E, I, J, SPL, TPS, ISP, RM)
   - Full sail inventory with measured dimensions (JL, LPG, SLU, SLE, SFL, SHW)
2. ORC HTML Speed Guide (.html)
   - Polar tables for each sail configuration (Optimal, Headsail, Asymmetric, Symmetric)
   - TWA, BTV, VMG, AWS, AWA, Heel, Reef, Flat across all wind speeds (6-24 kn)

Outputs:
- Rich JSON Digital Twin for tactical navigation, routing, and Rechenscheibe.

Usage:
    python orc_extractor.py --dxt data/ORC_SpeedGuide_TRUE_GRIT_27.12.2025.dxt \
                            --html data/ORC_SpeedGuide_TRUE_GRIT_27.12.2025.html \
                            --out data/ORC_SpeedGuide_TRUE_GRIT_27.12.2025.json
"""

import re
import json
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Any, List


class OrcExtractor:
    def __init__(self):
        self.data: Dict[str, Any] = {
            "meta": {},
            "data_section": {},
            "user_section": {},
            "rig_configuration": {},
            "sail_inventory": [],
            "polars": {"configurations": {}}
        }
        self._sail_map_by_orc_id = {}

    def _get_field_val(self, element, fieldname, default=None):
        if element is None:
            return default
        for child in element.iter():
            if child.tag.upper().endswith("FIELD"):
                if child.get("fieldname") == fieldname:
                    return child.get("value")
        return default

    def _extract_simple_section(self, root, tag_name):
        section_data = {}
        found_elem = None
        for elem in root.iter():
            if elem.tag.upper().endswith(tag_name.upper()):
                found_elem = elem
                break
        if found_elem is not None:
            for child in found_elem:
                clean_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                val = child.text.strip() if child.text else ""
                section_data[clean_tag] = val
        return section_data

    def parse_dxt(self, dxt_path: Path):
        print(f"[*] Lese DXT-Datei: {dxt_path.name}")
        tree = ET.parse(dxt_path)
        root = tree.getroot()

        self.data["data_section"] = self._extract_simple_section(root, "DATA")
        self.data["user_section"] = self._extract_simple_section(root, "USER")

        inp = None
        for elem in root.iter():
            if elem.tag.upper().endswith("INPUT"):
                inp = elem
                break

        if inp is None:
            print("[ERROR] Kein INPUT-Tag im XML gefunden.")
            return

        # 1. Meta Data
        self.data["meta"] = {
            "boat_name": self._get_field_val(inp, "YachtName", "TRUE GRIT"),
            "sail_number": self._get_field_val(inp, "SailNo", "GER 7447"),
            "type": self._get_field_val(inp, "Class", "JPK 10.80"),
            "gph": float(self._get_field_val(inp, "GPH", "0") or 0.0)
        }

        # 2. Rig Configuration
        def rig_val(key, desc, unit="m"):
            val_str = self._get_field_val(inp, key, "0")
            return {
                "value": float(val_str) if val_str else 0.0,
                "unit": unit,
                "description": desc
            }

        self.data["rig_configuration"] = {
            "p": rig_val("P", "Mainsail hoist"),
            "e": rig_val("E", "Mainsail outer point distance"),
            "i": rig_val("IG", "Height of foretriangle (IG used as I)"),
            "j": rig_val("J", "Base of foretriangle"),
            "spl": rig_val("SPL", "Spinnaker Pole Length"),
            "tps": rig_val("TPS", "Tack Point Sprit"),
            "isp": rig_val("ISP", "Height of spinnaker hoist"),
            "rm_default": rig_val("RMCe", "Righting Moment (Default)", "kgm")
        }

        # 3. Sail Inventory
        inventory = []
        sails_container = None
        for elem in root.iter():
            if elem.tag.upper().endswith("SAILS"):
                sails_container = elem
                break

        if sails_container is not None:
            type_map = {
                "headsail": "HEAD", "jib": "HEAD",
                "main": "MAIN", "mainsail": "MAIN",
                "sym_spin": "SYM", "symmetric": "SYM",
                "asym_spin": "ASYM", "asymmetric": "ASYM"
            }

            for sail_elem in sails_container:
                if not sail_elem.tag.upper().endswith("SAIL"):
                    continue

                raw_code = sail_elem.get("SailCode", "").lower()
                my_type = type_map.get(raw_code, "OTHER")

                for record in sail_elem:
                    if not record.tag.upper().endswith("RECORD"):
                        continue

                    raw_attributes = {}
                    for child in record:
                        if child.tag.upper().endswith("FIELD"):
                            fname = child.get("fieldname")
                            fval = child.get("value")
                            if fname:
                                raw_attributes[fname] = fval

                    area = float(raw_attributes.get("SailArea", 0) or raw_attributes.get("Area", 0))
                    orc_id = raw_attributes.get("SailId", "")
                    name = raw_attributes.get("CopiedFrom", "")
                    if not name:
                        name = raw_attributes.get("Comment", raw_code)

                    internal_id = f"{my_type}_{len(inventory)+1}"
                    sail_entry = {
                        "internal_id": internal_id,
                        "orc_sail_id": orc_id,
                        "type": my_type,
                        "name": name,
                        "area": area,
                        "used_in_polars": False,
                        "attributes": raw_attributes,
                        "measurements": {}
                    }

                    for m in ["JL", "LPG", "SLU", "SLE", "SFL", "SHW", "SMG", "JH", "MGT", "MGU", "MGM", "MGL"]:
                        if m in raw_attributes and raw_attributes[m]:
                            try:
                                key = m.lower()
                                if key == "smg":
                                    key = "shw"
                                sail_entry["measurements"][key] = float(raw_attributes[m])
                            except Exception:
                                pass

                    inventory.append(sail_entry)
                    if orc_id:
                        self._sail_map_by_orc_id[orc_id] = internal_id

        self.data["sail_inventory"] = inventory
        print(f"    -> {len(inventory)} Segel im Inventar gefunden.")

    def parse_html_speed_guide(self, html_path: Path):
        print(f"[*] Lese HTML Speed Guide: {html_path.name}")
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f, 'html.parser')

        containers = soup.find_all("div", class_="polarcontainer")
        print(f"    -> {len(containers)} Polar-Container gefunden.")
        polar_configs = {}

        for container in containers:
            title_div = container.find("div", class_="polarcontainer-title")
            full_title_text = title_div.get_text(" ", strip=True) if title_div else "Unknown"

            config_id = "other"
            is_composite = False

            if "Best Performance" in full_title_text or "Optimal" in full_title_text:
                config_id = "optimal"
                is_composite = True
            elif "Asymmetric" in full_title_text:
                config_id = "asymmetric"
            elif "Symmetric" in full_title_text:
                config_id = "symmetric"
            elif "Headsail" in full_title_text:
                config_id = "headsail"

            base_id = config_id
            counter = 1
            while config_id in polar_configs:
                config_id = f"{base_id}_{counter}"
                counter += 1

            linked_sail_id = None
            id_match = re.search(r"#(\d+)", full_title_text)
            if id_match:
                found_orc_id = f"#{id_match.group(1)}"
                if found_orc_id in self._sail_map_by_orc_id:
                    linked_sail_id = self._sail_map_by_orc_id[found_orc_id]
                    for s in self.data["sail_inventory"]:
                        if s["internal_id"] == linked_sail_id:
                            s["used_in_polars"] = True
                            break

            tables = container.find_all("table", class_="polartable")
            extracted_data = []

            for table in tables:
                caption = table.find("caption")
                if not caption:
                    continue
                tws_match = re.search(r'TWS\s*=\s*(\d+)', caption.get_text())
                if not tws_match:
                    continue
                tws = int(tws_match.group(1))

                rows = table.find_all("tr")
                if not rows:
                    continue

                header_cells = rows[0].find_all("th")
                col_map = {th.get_text().strip().upper(): idx for idx, th in enumerate(header_cells)}

                points_for_tws = []
                for row in rows[1:]:
                    cells = row.find_all("td")
                    if not cells:
                        continue
                    try:
                        def get_val(name, default_idx):
                            idx = col_map.get(name, default_idx)
                            if idx < len(cells):
                                txt = cells[idx].get_text().strip()
                                return float(re.sub(r"[^\d\.]", "", txt))
                            return 0.0

                        twa = get_val("TWA", 0)
                        bsp = get_val("BTV", 1)
                        vmg = get_val("VMG", 2)
                        aws = get_val("AWS", 3)
                        awa = get_val("AWA", 4)
                        heel = get_val("HEEL", 5)
                        reef = get_val("REEF", 6)
                        flat = get_val("FLAT", 7)

                        points_for_tws.append({
                            "twa": twa, "bsp": bsp, "vmg": vmg,
                            "aws": aws, "awa": awa, "heel": heel,
                            "reef": reef, "flat": flat
                        })
                    except ValueError:
                        continue

                if points_for_tws:
                    extracted_data.append({"tws": tws, "curve": points_for_tws})

            if extracted_data:
                polar_configs[config_id] = {
                    "description": full_title_text,
                    "is_composite": is_composite,
                    "linked_sail_internal_id": linked_sail_id,
                    "data": extracted_data
                }

        self.data["polars"]["configurations"] = polar_configs


def main():
    parser = argparse.ArgumentParser(description="ORC DXT & HTML Speed Guide Extractor")
    parser.add_argument("--dxt", type=Path, default=Path(__file__).parent / "data" / "ORC_SpeedGuide_TRUE_GRIT_27.12.2025.dxt")
    parser.add_argument("--html", type=Path, default=Path(__file__).parent / "data" / "ORC_SpeedGuide_TRUE_GRIT_27.12.2025.html")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "data" / "ORC_SpeedGuide_TRUE_GRIT_27.12.2025.json")

    args = parser.parse_args()
    extractor = OrcExtractor()
    extractor.parse_dxt(args.dxt)
    extractor.parse_html_speed_guide(args.html)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(extractor.data, f, indent=2)

    print(f"[*] JSON Digital Twin erfolgreich gespeichert nach: {args.out}")


if __name__ == "__main__":
    main()
