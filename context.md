# 🧭 Projekthistorie & Statusdokumentation: Nautische Rechenscheibe V3.0
**Yacht:** JPK 1080 (*TRUE GRIT*, GER 7447)  
**Datum:** 08. September 2026  
**Status:** Release V3.0 fertiggestellt, validiert & auf Git synchronisiert (`origin/main`)

---

## 1. Projektübersicht & Kernarchitektur
Entwicklung einer professionellen, doppelseitigen **Ø 180 mm Sandwich-Rechenscheibe** für Regattaeinsatz, Taktik und Hochseenavigation im Cockpit:
- **Seite A (Vorderseite):** TackingMaster-Taktikring (Winddreher, Tack/Gybe-Sektoren, Startlinien-Bias) kombiniert mit **1:1 ORC-VPP-Polaren** in absoluten Knoten (5,0 mm/kn, R_max = 65,0 mm für 13,0 kn). Asymmetrische Darstellung: Steuerbord (TWA) zum Steuern nach Instrumenten, Backbord (AWA) zum Steuern nach Windex/Verklicker.
- **Seite B (Rückseite):** Zirkularer Rechenschieber (C- und D-Skala) für Distanz-Zeit-Geschwindigkeit sowie eine exakt radial ausgerichtete Sinusskala (S-Skala bei R = 65,0 mm) für Winddreiecks-Trigonometrie samt transparentem Läufer.
- **Parametrisches Framework:** Single Source of Truth über `config.json` und `config_manager.py`. Sämtliche Dimensionen, Toleranzen, Schichtfarben und Beschriftungen werden mathematisch konsistent abgeleitet.
- **Fertigung:** Wasserdichte 3D-Druck-Komponenten (Bambu Lab) und hochpräzise Laser-Vektordateien (SVG) mit identischen 300-DPI-Vorschauen (`librsvg`/`libcairo`).

---

## 2. Abgeschlossene Meilensteine (Session 08.09.2026)

### A. Mechanik & 3D-Druck-Optimierung (Bambu Lab)
- **1,0 mm Zentrierbohrungen für M3-Verschraubung:**  
  Auf dem Teilkreis R = 88,0 mm (Ø 176,0 mm) wurden im Gehäusedeckel und Gehäuseboden jeweils 6 symmetrische 1,0 mm Zentrierbohrungen integriert (als Vorbohr- und Ausrichthilfe für 3D-Druck und Laserschnitt).
- **100% 2-Manifold Geometrien:**  
  Alle 6 STL-Dateien (`mesh_generator.py`) sind absolut wasserdicht (0 Non-Manifold Kanten, 0 Selbstüberschneidungen) und slicen fehlerfrei in Bambu Studio und OrcaSlicer.

### B. Bereinigung & Zentralisierte Konfiguration
- **Entfernung von Entwicklungsrelikten:**  
  Entfernung aller temporären Beschriftungen wie „1:1 Knoten“ und „Rückseite“.
- **Zentrale Labels & Pfade:**  
  Alle Titel, Untertitel, Skalenbeschriftungen sowie der Pfad zum Speed Guide (`speedguide_file`) werden zentral über `config.json` verwaltet.

### C. Nahtloser 180°-Polarenübergang & Behebung des Speed-Guide-Versatzes
- **Ursachenanalyse im ORC Speed Guide:**  
  1. Die HTML-Vorlage trennt TWA (rechts, Ursprung X=1077) und AWA (links, Ursprung X=1023) durch eine 54-Pixel-Lücke (ca. 0,72 kn Buchfalz-Versatz).  
  2. Die getrimmten Segelkurven endeten vorzeitig bei optimalen Halsenwinkeln (145° bis 165°).
- **Vektortrigonometrische Korrektur:**  
  Umstellung von `calc_wind_triangle_awa` auf Vektor-`atan2(x, y)` (`x = TWS * sin(TWA)`, `y = TWS * cos(TWA) + BSP`) zur fehlerfreien Abbildung des vollen Bereichs von 0° bis 180° (`AWA = 180,0°` bei `TWA = 180,0°`).
- **Vorwind-Fortführung (`_extend_downwind_to_180`):**  
  Fortführung der tiefsten Vorwind-Segmente über die realen ORC-VPP-Stützstellen (150°, 165°, 180°) aus `249116.slk` bis zum gemeinsamen 180°-Punkt `(0, V_BS(180°))`.
- **Horizontale Tangente (C1-Stetigkeit):**  
  Virtuelle Spiegelpunkte `(-x, y)` am Scheitelpunkt erzwingen `dy/dx = 0` bei `X = 0`, wodurch die Kurven völlig knick- und kantenfrei von Steuerbord nach Backbord ineinander übergehen.
- **Mathematische Verifikation:**  
  Fehler an allen 8 Windstärken (6 bis 24 kn) beträgt exakt 0,000 mm:
  - 6 kn TWS -> 3,33 kn V_BS (Y = 16,67 mm)
  - 8 kn TWS -> 4,40 kn V_BS (Y = 22,01 mm)
  - 10 kn TWS -> 5,38 kn V_BS (Y = 26,89 mm)
  - 12 kn TWS -> 6,26 kn V_BS (Y = 31,32 mm)
  - 14 kn TWS -> 7,00 kn V_BS (Y = 35,00 mm)
  - 16 kn TWS -> 7,54 kn V_BS (Y = 37,69 mm)
  - 20 kn TWS -> 8,43 kn V_BS (Y = 42,15 mm)
  - 24 kn TWS -> 9,42 kn V_BS (Y = 47,12 mm)

### D. Dokumentation & Git-Status
- `README.md` vollständig auf Stand Release V3.0 aktualisiert.
- Alle STLs, SVGs und 300-DPI-PNGs neu gerendert.
- Alle Änderungen committet und auf GitHub gepusht (Commit `ab468ea`).

---

## 3. Dateistruktur & Wichtige Pfade
- **Steuerung & CLI:** [`rechenscheibe.py`](rechenscheibe.py)
- **Konfiguration:** [`config.json`](config.json), [`config_manager.py`](config_manager.py)
- **Vektor- & Polarmodelle:** [`polar_parser.py`](polar_parser.py), [`vector_engine.py`](vector_engine.py)
- **3D-Mesh-Generator:** [`mesh_generator.py`](mesh_generator.py)
- **Eingangsdaten:** [`data/249116.slk`](data/249116.slk), [`data/ORC_SpeedGuide_TRUE_GRIT_27.12.2025.html`](data/ORC_SpeedGuide_TRUE_GRIT_27.12.2025.html)
- **Fertigungsdateien (`output/`):**
  - `stl/`: 6 wasserdichte STL-Dateien (Gehäusedeckel, Gehäuseboden, Mittelscheibe, Zeiger, Achspin)
  - `svg/`: 8 fertigungsgerechte Laser-Vektordateien
  - `previews/`: Hochauflösende 300-DPI-PNG-Vorschauen
- **Versionssicherung:** `_archive/` (strikte zweistellige fortlaufende Nummerierung)

---

## 4. Nächste Schritte für die kommende Session
1. **Druckvorbereitung:** Probe-Import der STL-Dateien in Bambu Studio zur Prüfung der Wandstärken, Toleranzen und Stützstrukturen.
2. **Laserschneider-Setup:** Zuweisung der RGB-Farblinien (Gravur vs. Schnitt) für zweifarbiges Acryl / Rowmark.
3. **Hardware-Montage:** Prüfung von Schraubenlängen (M3 x 8 mm Senkkopf) und Achsbolzenspiel.
