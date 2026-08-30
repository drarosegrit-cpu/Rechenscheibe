# Nautische Rechenscheibe & Taktik-Suite – JPK 1080 (GER 7447)

Präziser analoger und digitaler Taktik- und Navigationsrechner für die **JPK 1080 (*TRUE GRIT*, GER 7447)**.
Kombiniert die offiziellen ORC-VPP-Polaren (Stand 27.12.2025) für 3D-Druck, Lasergravur, Live-Bordcomputer und GPX-Routenoptimierung.

---

## 🧭 Komponenten der Suite

| Modul / Datei | Funktion |
| :--- | :--- |
| **`config.json`** | **Zentrale Parametersteuerung:** Sämtliche Maße, Maßstäbe, Toleranzen, Dicken und Schriftgrößen sind hier definiert und bauen mathematisch aufeinander auf. |
| **`config_manager.py`** | **Parametrischer Geometriemanager:** Berechnet die abhängigen Maße für Stator, Rotor, Lineal und Achsstifte aus `config.json`. |
| **`rechenscheibe.py`** | **Hauptskript:** Erzeugt die 3D-Druck-Modelle (STL), Laser-Vektoren (DXF) und 300 DPI Vorschaubilder auf Basis von `config.json`. |
| **`tactical_advisor.py`** | **Taktischer Bordcomputer:** Live-Entscheidungshilfe für Kurs ($HDG$), Windrichtung ($TWD$) und Windstärke ($TWS$). Gibt Target-Speed, Soll-Krängung ($Heel$), AWA/AWS und exakte Segel- & Reffempfehlungen aus. |
| **`route_optimizer.py`** | **Routen-Optimierer:** Liest GPX-Regattakurse ein und berechnet für jeden Schenkel VMG-Kreuz-, VMG-Halsen- oder Direkt-Strategie, Soll-Geschwindigkeit, ETE und Segelwechsel. |
| **`orc_extractor.py`** | **Digital Twin Generator:** Wandelt offizielle ORC `.dxt`-Vermessungsdateien und HTML-SpeedGuides in saubere JSON-Datensätze um. |
| **`polar_parser.py`** | Universeller Parser & Spline-Interpolator für JSON- und CSV-Polaren. |
| **`stl_generator.py`** | Prozeduraler Binär-STL-Generator für wasserdichte 3D-Druckkörper. |
| **`chart_generator.py`** | 2D-Vektor-Rendering (ezdxf) mit CAM-Farbcodierung für Laser-Cutter. |

---

## ⚙️ Parametrische Steuerung über `config.json`

Alle Dimensionen der Rechenscheibe sind vollständig voneinander abhängig und können über die Datei **[`config.json`](file:///home/rose/Python_Projects/JPK1080_Analysis/Rechenscheibe/config.json)** angepasst werden:

```json
{
  "dimensions": {
    "outer_radius_mm": 57.5,
    "true_wind_scale_factor": 1.00,
    "rotor_clearance_mm": 0.25,
    "pocket_clearance_mm": 0.15,
    "pin_clearance_mm": 0.10,
    "center_hole_radius_mm": 1.60,
    "awa_hole_radius_mm": 1.30
  },
  "thicknesses": {
    "stator_floor_mm": 1.6,
    "stator_rim_height_mm": 1.8,
    "rotor_disc_mm": 1.8,
    "ruler_arm_mm": 1.2,
    "center_pin_head_thickness_mm": 0.7,
    "awa_pin_head_thickness_mm": 0.6
  },
  "ruler": {
    "width_mm": 6.0,
    "hub_radius_mm": 4.0,
    "thumb_tab_extension_mm": 5.38
  }
}
```
* **Kinematische Kaskade:** Ändert man z. B. `outer_radius_mm` auf `75.0` (150 mm Großmodell), passen sich Skalenteilung, Rotor-Außenmaß, True-Wind-Achse, AWA-Lagerbohrung und die Gesamtlänge des Peil-Lineals vollautomatisch an!

---

## 🛠️ Fertigung der Rechenscheibe: 3D-Druck + Lasergravur

### 1. Schritt: 3D-Druck (STL)
Alle Modelle liegen im Ordner `output/`:
* `rechenscheibe_stator_basis.stl`: Basis mit Außendurchmesser und Pass-Tasche.
* `rechenscheibe_rotor_drehscheibe.stl`: Innere Drehscheibe mit Laufspiel und AWA-Lagerbohrung.
* `rechenscheibe_lineal.stl`: 100 mm Peil-Lineal mit Peilkante am AWA-Pol und Daumengriff.
* `rechenscheibe_achsstift_senkkopf.stl`: Ultraflacher Zentralbolzen (0.7 mm Kopfhöhe).
* `rechenscheibe_achsstift_awa.stl`: Drehzapfen für das Lineal.

### 2. Schritt: Lasergravur (DXF)
* `laser_rotor_drehscheibe.dxf`: Polaren, AWA-Gitter und VMG-Zielmarkierungen.
* `laser_stator_aussenring.dxf`: Duale 360°-Kompassrose & AWA-Außenskala sowie logarithmische Log-Skala.
* `laser_lineal.dxf`: Linealkontur und gravierte AWS/TWS-Skala.
* `rechenscheibe_komplett.dxf`: Gesamtansicht.

---

## 💻 Ausführung & CLI-Beispiele

Alle Befehle werden mit der lokalen virtuellen Umgebung aufgerufen:

### 1. Rechenscheibe generieren (unter Verwendung von config.json):
```bash
./.venv/bin/python rechenscheibe.py
```
*Tipp: Mit `./.venv/bin/python rechenscheibe.py --sail-layers` können die Einzelschiffskurven für Fock, Gennaker (Rüssel) und Spinnaker (Baum) auf separaten DXF-Ebenen für den Laser graviert werden (standardmäßig deaktiviert, um die Scheibe übersichtlich zu halten).*

### 2. Taktischen Berater für aktuellen Wind abfragen:
```bash
./.venv/bin/python tactical_advisor.py --hdg 235 --twd 345 --tws 16
```
*Gibt Soll-Speed ($8.61\text{ kn}$), Krängung ($22.0^\circ$) sowie das exakte Geschwindigkeitspotenzial aller Segel aus (z. B. Fock $8.03\text{ kn}$ vs. Gennaker $8.61\text{ kn}$ [+0.59 kn Vorteil]).*

### 3. GPX-Regattakurs optimieren:
```bash
./.venv/bin/python route_optimizer.py --gpx data/Kursdaten.gpx --twd 345 --tws 16
```
*Berechnet für alle Wegpunkte Distanzen, Kurse, VMG-Schläge, ETE und Segelwechsel auf Basis der hochpräzisen SLK-Daten.*

### 4. Neue ORC-Messbriefe importieren:
```bash
./.venv/bin/python orc_extractor.py --dxt data/neuer_messbrief.dxt --html data/speedguide.html
```
