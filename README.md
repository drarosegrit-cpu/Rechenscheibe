# 🧭 Nautische Rechenscheibe & Taktik-Suite – JPK 1080 (GER 7447)

Präzises analoges und digitales Navigations- und Taktiksystem für die Regattayacht **JPK 1080 (*TRUE GRIT*, GER 7447)**.  
Kombiniert die offiziellen **ORC-VPP-Polardaten** (Stand 27.12.2025, Run-ID `249116`) mit:
1. Einer **analogen Rechenscheibe mit Peil-Lineal** für 3D-Druck und Lasergravur.
2. Einem **digitalen Taktik-Bordcomputer** (`tactical_advisor.py`) mit Einzelsegel-Performancevergleich.
3. Einem **GPX-Routen- und VMG-Optimierer** (`route_optimizer.py`) für Regattakurse.
4. Einer **vollparametrischen Geometriesteuerung** über [`config.json`](config.json).

---

## 📑 Inhaltsverzeichnis
1. [Funktionsprinzip der Rechenscheibe](#-funktionsprinzip-der-rechenscheibe)
2. [Komponenten & Dateistruktur](#-komponenten--dateistruktur)
3. [Zentrale Steuerung über config.json](#-zentrale-steuerung-über-configjson)
4. [Hardware-Fertigung (3D-Druck & Lasergravur)](#-hardware-fertigung-3d-druck--lasergravur)
5. [Datenbasis & ORC Digital Twin (249116.slk)](#-datenbasis--orc-digital-twin-249116slk)
6. [CLI-Tools & Software-Module](#-cli-tools--software-module)
7. [Praxis-Bedienungsanleitung auf See](#-praxis-bedienungsanleitung-auf-see)

---

## 📐 Funktionsprinzip der Rechenscheibe

Die Rechenscheibe löst das klassische **nautische Winddreieck** mechanisch und rein optisch – vollkommen unabhängig von Bordelektronik oder Stromversorgung:

$$\vec{V}_{AW} = \vec{V}_{TW} - \vec{V}_{BS}$$

```
                N (0° True Wind)
                     ▲
                     │ \
      Wahrer Wind    │   \  Scheinbarer Wind
       V_TW (100%)   │     \  V_AW (AWS, AWA)
                     │       \
                     ▼         ▼
  (0, -mm_100) ────► Pol 2 ────► Pol 1 (0, 0)
                 (AWA-Drehpunkt)  (Boot / True Heading)
                           ◄──────
                        Bootsgeschwindigkeit V_BS
```

### 1. Das Dual-Center-Prinzip
* **Zentraler Pol $(0, 0)$ (Bootsmittelpunkt & Drehscheibe):**
  * Hier schneiden sich die Bootsachse und die True-Wind-Winkel.
  * Zeigt auf der inneren Drehscheibe die ORC-Polaren für $6, 8, 10, 12, 14, 16, 20, 24\text{ kn}$ Wind.
  * Innere Randschale: $0^\circ \dots 360^\circ$ Kompassrose / Wahrer Windwinkel ($TWA$).
* **Exzentrischer Pol $(0, -Y_{AWA})$ (AWA/AWS-Lager):**
  * Liegt exakt um den Maßstabsfaktor der Windachse nach unten versetzt ($Y = -37.12\text{ mm}$ bei 115 mm Scheibendurchmesser).
  * Hier ist das **taktische Peil-Lineal** drehbar gelagert.
  * Äußere Randschale: $0^\circ \dots 180^\circ$ scheinbarer Windeinfallswinkel ($AWA$), symmetrisch für Steuerbord und Backbord.
  * Fluchtet die Peilkante über die Polarkurve, schneidet sie am Außenrand **exakt den scheinbaren Windwinkel $AWA$** und zeigt auf der gravierten Linealskala die **scheinbare Windstärke $AWS$** an!

### 2. Der integrierte logarithmische Rechenschieber
Auf dem Stator-Außenring befindet sich eine hochpräzise, gegenläufige **logarithmische Doppelskala ($1 \dots 100$)**:
* Ermöglicht im Handumdrehen Multiplikation und Division nach der Formel:
  $$\text{Weg (nm)} = \text{Geschwindigkeit (kn)} \times \text{Zeit (h)}$$
* Berechnung von Restfahrzeiten (ETE/ETA), Distanzen, Stromversatz und Kraftstoffverbrauch ohne Taschenrechner.

---

## 🧭 Komponenten & Dateistruktur

```
Rechenscheibe/
├── config.json               # Zentrale Parametersteuerung (Maße, Toleranzen, Dicken)
├── config_manager.py         # Parametrische Geometriekaskade & Konsistenzprüfung
├── rechenscheibe.py          # Haupt-Generator (erzeugt STLs, DXFs und Preview-PNG)
├── polar_parser.py           # Universeller Parser für SLK-, JSON- und CSV-Polaren
├── chart_generator.py        # CAD/CAM-Vektorgenerator (ezdxf) mit Laserebenen
├── stl_generator.py          # Prozeduraler Binär-STL-Generator für 3D-Druckteile
├── tactical_advisor.py       # Taktischer Bordcomputer mit Einzelsegel-Vergleich
├── route_optimizer.py        # GPX-Routen- und VMG-Kreuz-/Halsen-Optimierer
├── orc_extractor.py          # Konverter für ORC .dxt-Messbriefe und HTML-SpeedGuides
├── data/
│   ├── 249116.slk            # Originale, ungerundete ORC VPP-Rohdaten (TRUE GRIT)
│   ├── ORC_SpeedGuide_...json # Strukturierter Digital Twin Datensatz
│   └── Kursdaten.gpx         # Beispiel-Regattakurs mit Wegpunkten
└── output/                   # Fertigungsfertige 3D- und Laserdateien
    ├── rechenscheibe_stator_basis.stl
    ├── rechenscheibe_rotor_drehscheibe.stl
    ├── rechenscheibe_lineal.stl
    ├── rechenscheibe_achsstift_senkkopf.stl
    ├── rechenscheibe_achsstift_awa.stl
    ├── laser_rotor_drehscheibe.dxf
    ├── laser_stator_aussenring.dxf
    ├── laser_lineal.dxf
    ├── rechenscheibe_komplett.dxf
    └── rechenscheibe_preview.png
```

---

## ⚙️ Zentrale Steuerung über `config.json`

Alle Maße, Passungen, Toleranzen und Schichtdicken sind in **[`config.json`](config.json)** definiert:

```json
{
  "project": {
    "title": "Nautical Rechenscheibe - JPK 1080 (GER 7447 - TRUE GRIT)",
    "polar_file": "data/249116.slk",
    "output_dir": "output"
  },
  "display": {
    "render_sail_layers": false
  },
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

### Die kinematische Abhängigkeitskette
Wird z. B. `outer_radius_mm` auf `75.0` geändert (Großmodell mit $150\text{ mm}$ Durchmesser):
1. **Skalenbandbreite:** Berechnet sich aus Tick-Länge + Textabstand + Schrifthöhe.
2. **Teilkreise:** Stator- und Rotorkanten verschieben sich automatisch nach außen.
3. **Laufspiel:** Rotor-Außenmaß ($R_{rotor} = R_{main} - 0.25\text{ mm}$) und Stator-Tasche ($R_{pocket} = R_{main} + 0.15\text{ mm}$) behalten exakt ihre Passung.
4. **Maßstab der Polaren:** Die True-Wind-Achse wächst proportional mit, damit die Kurven stets die volle Scheibenfläche ausnutzen.
5. **AWA-Drehpunkt & Lineallänge:** Der exzentrische Drehpunkt wandert mit ($Y = -mm\_per\_100pct$), und das Peil-Lineal verlängert sich exakt bis zur Außenkante der Skala!

---

## 🛠️ Hardware-Fertigung (3D-Druck & Lasergravur)

### Schritt 1: 3D-Druck (STL)
Alle 3D-Körper liegen druckfertig im Ordner `output/`:
* `rechenscheibe_stator_basis.stl`: Basiskorpus mit Rand und versenkter Pass-Tasche.
* `rechenscheibe_rotor_drehscheibe.stl`: Drehscheibe mit zentraler M3- und unterer AWA-Bohrung.
* `rechenscheibe_lineal.stl`: 100 mm Peil-Lineal mit Daumengriff und Peilspitze.
* `rechenscheibe_achsstift_senkkopf.stl`: Flacher Zentralstift ($0.7\text{ mm}$ Kopfhöhe), damit das Lineal ungehindert darüber rotieren kann.
* `rechenscheibe_achsstift_awa.stl`: Drehzapfen für das Lineal ($0.6\text{ mm}$ Kopfhöhe).

**Druckempfehlungen:**
* **Material:** Helles PETG oder mattes PLA (Weiß oder Creme) für optimalen Kontrast zur Lasergravur.
* **Infill:** 100% (konzentrisch) für Verzugsfreiheit bei Sonneneinstrahlung im Cockpit.
* **Slicer-Option:** **"Glätten / Ironing"** auf der obersten Schicht aktivieren! Dadurch entsteht eine spiegelglatte Oberfläche, auf der der Laser mit perfektem Fokus gravieren kann.

### Schritt 2: Lasergravur & Zuschnitt (DXF)
Die DXF-Dateien sind für gängige Lasersoftware (LightBurn, LaserGRBL, etc.) nach CAM-Ebenen farbcodiert:
* `laser_rotor_drehscheibe.dxf`: Polaren, AWA-Radialgitter und VMG-Rauten.
* `laser_stator_aussenring.dxf`: 360° Kompassrose, äußere AWA-Gradskala und Rechenschieber.
* `laser_lineal.dxf`: Konturzuschnitt und gravierte AWS/TWS-Linealskala.
* `rechenscheibe_komplett.dxf`: Gesamtzusammenbau zur Kontrolle.

**CAM-Ebenen-Zuordnung:**
| Layer-Name | Farbe | Vorgang | Empfehlung |
| :--- | :--- | :--- | :--- |
| `CUT_OUTLINE` / `CUT_HOLE` | Schwarz / Rot | Durchtrennen (Line / Cut) | Hohe Leistung, langsame Geschwindigkeit |
| `ENGRAVE_POLARS` | Blau | Gravur Polarlinien | Mittlere Leistung, scharfe Linie |
| `ENGRAVE_AWA` | Cyan | Gravur AWA-Gitter | Geringe Leistung / feine Linie |
| `ENGRAVE_VMG` | Rot / Grün | VMG-Zielpunkte | Rautenfüllung oder Marker |
| `ENGRAVE_TEXT` / `ENGRAVE_LOG` | Schwarz | Beschriftung & Skalen | Hochauflösender Scan / Fill |

---

## 📊 Datenbasis & ORC Digital Twin (`249116.slk`)

Das Projekt nutzt die **originalen, ungerundeten Berechnungsdaten** der ORC-Physikengine für die JPK 1080 *TRUE GRIT* (Zertifikats-ID `249116`).

Im Gegensatz zu vereinfachten Polartabellen enthält die Datei **485 diskrete Messpunkte** für alle 8 Windgeschwindigkeiten ($6, 8, 10, 12, 14, 16, 20, 24\text{ kn}$) und trennt die Segelkonfigurationen auf:
* **`Jib` (`#55940`):** UK Sails Carbon J1 (31.68 m²) – reine Vorwind-/Am-Wind-Polare ohne Spinnaker.
* **`AsymCL` (`#180387`):** UK Sails A2 Gennaker (116.03 m²) am festen Bugspriet (Centerline).
* **`AsymPole` (`#180387`):** UK Sails A2 Gennaker am beweglichen Spinnakerbaum.
* **`Sym` (`#62068`):** UK Sails S2 Symmetrischer Spinnaker (115.00 m²) am Spibaum.
* **`BestPerf`:** Die Hüllkurve der optimalen Bootsgeschwindigkeit.

---

## 💻 CLI-Tools & Software-Module

Alle Skripte laufen mit der virtuellen Python-Umgebung:

### 1. Rechenscheibe generieren (`rechenscheibe.py`)
```bash
./.venv/bin/python rechenscheibe.py
```
* **Optionen:**
  * `--sail-layers`: Graviert die Einzelschiffskurven für Fock, Gennaker und Spi auf eigene DXF-Ebenen.
  * `--radius <mm>`: Scheibenaußenradius temporär überschreiben (z. B. `--radius 75.0`).
  * `--no-stl` / `--no-dxf` / `--no-preview`: Einzelne Generierungsschritte überspringen.

### 2. Taktischer Bordcomputer (`tactical_advisor.py`)
Echtzeit-Entscheidungshilfe an Bord für Steuerkurs ($HDG$), Windrichtung ($TWD$) und Windstärke ($TWS$):
```bash
./.venv/bin/python tactical_advisor.py --hdg 235 --twd 345 --tws 16
```
**Ausgabebeispiel:**
```text
========================================================================
  TAKTISCHER BORDCOMPUTER - JPK 1080 (TRUE GRIT / GER 7447)
  Datenbasis: 249116.slk (ORC VPP Digital Twin)
========================================================================
  SITUATION: Kurs 235° | Wind 345° @ 16.0 kn -> TWA: 110.0°
------------------------------------------------------------------------
  [1. VPP SOLL-WERTE (Best Performance)]
    Target Boat Speed (BSP) : 8.61 kn
    Velocity Made Good (VMG): 2.95 kn
    Scheinbarer Wind (AWA)  : 78.2° @ 15.4 kn
    Soll-Krängung (Heel)    : 22.0°
    VPP-Reff-Faktor          : 0.85 (Flat: 0.94)

  [2. GESCHWINDIGKEITS-POTENZIAL NACH SEGELTYP]
    Fock (J1)             : 8.03 kn (Basis ohne Spi)
    Gennaker A2 (Rüssel)  : 8.61 kn (+0.59 kn ggü. Fock)
    Gennaker A2 (Baum)    : 8.44 kn (+0.42 kn ggü. Fock)
    Spinnaker S2 (Baum)   : 8.37 kn (+0.34 kn ggü. Fock)
    Optimal (BestPerf)    : 8.61 kn

  [3. EMPFOHLENE SEGELKONFIGURATION (DOWNWIND)]
    Großsegel: MAIN (Reff 1: -1.66m) (28.6 m²)
    Vorsegel : A3 (Reff: SLU-1.2m/SLE-1.6m) (76.6 m²)
    Status   : Optimale Konfiguration (100% Target Speed)
========================================================================
```

### 3. GPX-Routen- & VMG-Optimierer (`route_optimizer.py`)
Analysiert Regattakurse und entscheidet für jeden Wegpunktabschnitt autonom über VMG-Kreuz-, VMG-Halsen- oder Direktschlag:
```bash
./.venv/bin/python route_optimizer.py --gpx data/Kursdaten.gpx --twd 345 --tws 16
```
* Berechnet effektive Schlagdistanzen, ETE (Estimated Time Enroute) und Segelwechsel für jeden Schenkel.

---

## ⛵ Praxis-Bedienungsanleitung auf See

```
                             [ 0° TWD ]
                                 ▲
                                 │
                     ┌───────────┴───────────┐
                     │ 1. TWS-Kurve wählen   │
                     │    (z. B. 16 kn)      │
                     └───────────┬───────────┘
                                 │
                     ┌───────────▼───────────┐
                     │ 2. TWA einstellen     │
                     │  (Rotor auf Kurs/TWA) │
                     └───────────┬───────────┘
                                 │
                     ┌───────────▼───────────┐
                     │ 3. Lineal an Polare   │
                     │  anlegen -> BSP lesen │
                     └───────────┬───────────┘
                                 │
            ┌────────────────────┴────────────────────┐
            ▼                                         ▼
┌───────────────────────┐                 ┌───────────────────────┐
│ 4. AWA am Rand prüfen │                 │ 5. AWS am Lineal ab-  │
│  (zeigt scheinbaren   │                 │    lesen (Segeltrimm/ │
│   Windwinkel an)      │                 │    Reffentscheidung)  │
└───────────────────────┘                 └───────────────────────┘
```

1. **Windstärke feststellen:** Aktuellen wahren Wind $TWS$ bestimmen (z. B. $16\text{ kn}$).
2. **Kurs ausrichten:** Die innere Drehscheibe drehen, sodass der geplante Kurs oder $TWA$ am Stator abgelesen wird.
3. **Soll-Geschwindigkeit (Target Speed) ablesen:** 
   * Die Peilkante des Lineals an den Schnittpunkt der TWS-Kurve anlegen.
   * Der Abstand vom Zentrum $(0,0)$ liefert direkt den Target-Speed in Knoten.
   * Liegt der Punkt auf einer roten Raute: **Optimaler Upwind-VMG-Kreuzkurs!**
   * Liegt der Punkt auf einer grünen Raute: **Optimaler Downwind-VMG-Halsenkurs!**
4. **Scheinbaren Wind ablesen:** 
   * Die Spitze des Lineals zeigt auf dem Außenring direkt auf den scheinbaren Windwinkel ($AWA$).
   * Die Skala auf dem Lineal zeigt die scheinbare Windstärke ($AWS$) in Knoten an.
5. **Crossover & Segelwahl:**
   * Bei $TWA > 90^\circ$ Gennaker oder Spinnaker klarmachen.
   * Auf tiefen Vorwindkursen ($TWA > 140^\circ$) ist der symmetrische Spinnaker am Baum $0.1 \dots 0.2\text{ kn}$ schneller als der Gennaker am Rüssel.

---

**Entwickelt für:** JPK 1080 *TRUE GRIT* (GER 7447)  
**Lizenz:** Open Source für Rennyachten & Navigator-Crews.
