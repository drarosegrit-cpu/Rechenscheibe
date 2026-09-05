# Projekt-Kontext & Spezifikation: Taktischer Regatta-, Winddreieck- und ORC-Performance-Rechner (180 mm Sandwich-System)
## 1. Executive Summary & Zielsetzung
Ziel ist die Realisierung eines physischen, taktischen Segel- und Trimmrechners für Regatten. Das Instrument kombiniert:
1. **Einen taktischen Regattarechner** (Kompassrose vs. wahre Windrichtung mit optimalen Wende- und Halsewinkeln).
2. **Ein Fasskreis-Nomogramm** zur direkten geometrischen Lösung des scheinbaren Winddreiecks ($\alpha = \text{AWA}$) über einer festen Sehne.
3. **Ein ORC-Polardiagramm** der Ziel-Bootsgeschwindigkeiten für eine J/125 (aus hinterlegten Messbriefdaten).
4. **Einen doppelseitig gekoppelten Rechenschieber** (C/D-Geschwindigkeitsskala und Performance-%-Nonius) auf der Rückseite.
Das Gesamtsystem wird dreilagig aufgebaut (Boden, Rotor, Deckel), im 3D-Druck (FDM/SLA) gefertigt und mit einem Laserplotter beschriftet/graviert.
---
## 2. Mechanische Architektur & Toleranzen
### 2.1 Führungskonzept (Nut-und-Feder Kassettenführung)
* **Zentraler Verzicht:** Keine zentrale Achsschraube/Mittelbolzen, um den Innenbereich für Kurven und geometrische Konstruktionen vollkommen plan und ablesbar zu halten.
* **Führung:** Die drehbare Mittelscheibe (Rotor) besitzt einen umlaufenden Außenbund (Feder), der formschlüssig in einer Ringnut zwischen Gehäusedeckel und Gehäuseboden geführt wird.
* **Bedienung:** Vier symmetrisch angeordnete Rändelsegmente ragen radial aus dem Gehäuse hervor, um ein feinfühliges Drehen mit Daumen und Fingern (auch mit Handschuhen) zu ermöglichen.
### 2.2 Bauteildimensionierung (System 180 mm)
* **Gehäusedeckel (Seite A / Vorderseite - fest):**
  * Außendurchmesser: $180{,}0\,\text{mm}$
  * Innenfenster (Sichtbereich): $\varnothing 150{,}0\,\text{mm}$
  * Fester Skalensteg: Breite $15{,}0\,\text{mm}$
  * Bauteildicke: $2{,}5\,\text{mm}$
  * Befestigung: 6 Senkbohrungen M3 auf Teilkreis $\varnothing 176{,}0\,\text{mm}$
* **Gehäuseboden (Seite B / Rückseite - fest):**
  * Außendurchmesser: $180{,}0\,\text{mm}$
  * Innenfenster (Sichtbereich): $\varnothing 150{,}0\,\text{mm}$
  * Ringnut: Innendurchmesser $173{,}0\,\text{mm}$, Nuttiefe in Z-Richtung $2{,}4\,\text{mm}$
  * Bauteildicke: $4{,}4\,\text{mm}$ gesamt ($2{,}0\,\text{mm}$ Bodensteg + $2{,}4\,\text{mm}$ Nutring)
  * Befestigung: 6 Bohrungen M3 auf Teilkreis $\varnothing 176{,}0\,\text{mm}$ (für Einschmelzgewinde oder Durchgangsmuttern)
* **Mittelscheibe / Rotor (drehbar, beidseitig opak beschriftbar):**
  * Sichtbarer Bereich (beidseitig): $\varnothing 150{,}0\,\text{mm}$
  * Führungsbund (Feder): $\varnothing 172{,}0\,\text{mm}$, Dicke $2{,}0\,\text{mm}$ (Z-Lage: $0{,}2\,\text{mm}$ bis $2{,}2\,\text{mm}$)
  * 4 Rändelsegmente: Breite je $30^\circ$, Außenradius $93{,}0\,\text{mm}$ ($\varnothing 186{,}0\,\text{mm}$, $3{,}0\,\text{mm}$ Greifüberstand)
* **Fertigungstoleranzen:**
  * Radiales Spiel: $\Delta r = 0{,}5\,\text{mm}$ ($173{,}0\,\text{mm}$ Nut vs. $172{,}0\,\text{mm}$ Bund)
  * Axiales Spiel: $\Delta z = 0{,}4\,\text{mm}$ ($2{,}4\,\text{mm}$ Nut vs. $2{,}0\,\text{mm}$ Bund)
  * Vertiefte Gravurzonen: $0{,}4\,\text{mm}$ plane Absenkung zum Schutz der Lasermarkierung gegen Reibverschleiß
---
## 3. Mathematische Geometrie & Skalen-Architektur
### 3.1 Das Winddreieck
$$\vec{v}_{\text{scheinbar}} = \vec{v}_{\text{wahr}} - \vec{v}_{\text{Boot}} \iff \vec{v}_{\text{wahr}} = \vec{v}_{\text{Boot}} + \vec{v}_{\text{scheinbar}}$$
* $\text{SOG}$: Bootsgeschwindigkeit über Grund
* $\text{AWS}$: Scheinbare Windgeschwindigkeit (Apparent Wind Speed)
* $\alpha = \text{AWA}$: Scheinbarer Windwinkel (Windfahne an Mastspitze)
* $\text{TWS}$: Wahre Windgeschwindigkeit (True Wind Speed)
* $\text{TWA}$: Wahrer Windwinkel (True Wind Angle)
### 3.2 Fasskreis-Nomogramm (Weg A, Option 2: Feste Sehne über wahrem Wind)
* **Basissehne:** Wahre Windrichtung als vertikaler Vektor von $(0,0)$ nach $(0, L)$ auf der Nordachse ($L = 50{,}0\,\text{mm}$).
* **Peripheriewinkelsatz:** Alle Bootspositionen mit scheinbarem Windwinkel $\alpha$ liegen auf einem Kreis über der Basis $L$:
  * **Radius:** $R_\alpha = \frac{L}{2 \sin(\alpha)}$
  * **Mittelpunkt:** $x_M = \pm \frac{L}{2} \cot(\alpha), \quad y_M = \frac{L}{2}$ ($+$ für Steuerbord, $-$ für Backbord)
  * **Auflösung:** Kurvenschar von $\alpha = 20^\circ$ bis $150^\circ$ mit Schrittweite $\Delta\alpha = 2{,}5^\circ$
### 3.3 Logarithmische Rechenskalen (Seite B)
Winkelabbildung über vollen Kreis ($360^\circ$ pro Dekade):
* **Geschwindigkeit (C/D):** $\varphi_v = 360^\circ \cdot \log_{10}(v)$
* **Sinus-Skala (S):** $\varphi_\theta = 360^\circ \cdot \log_{10}(\sin(\theta))$ für $\theta \in [6^\circ, 90^\circ]$
* **Performance-%:** $\Delta\varphi = 360^\circ \cdot \log_{10}(1 + \text{Prozent}/100)$
---
## 4. Gravur- & Skalenbelegung
### Seite A: Taktik-, Fasskreis- & Polartrimm-Rechner (Vorderseite)
1. **Fester Gehäusedeckel (Außenring Ø 150 bis 180 mm):**
   * Vollständige $360^\circ$-Kompassrose mit $1^\circ$-Teilung, beziffert alle $30^\circ$.
2. **Mittelscheibe / Rotor (Sichtfenster Ø 150 mm):**
   * **Außenrand:**
     * Roter Taktikpfeil `TRUE WIND` (TWD) bei $0^\circ$.
     * `TACK`-Winkelmarken bei $38{,}0^\circ$ bis $41{,}8^\circ$ beidseitig (optimaler Am-Wind-Wendewinkel).
     * `GYBE`-Winkelmarken bei $142{,}8^\circ$ bis $167{,}5^\circ$ beidseitig (optimaler VMG-Halsewinkel).
   * **Innenfeld:**
     * Vertikale Referenzsehne $L$ des wahren Windes.
     * Symmetrische Schar der Fasskreisbögen ($\Delta\alpha = 2{,}5^\circ$).
     * Vollständige ORC-Polarkurven der J/125 für 9 Windstärken ($4$ bis $24\,\text{kn}$), skaliert mit $4{,}5\,\text{mm/kn}$.
### Seite B: Logarithmischer Performance-Rechner (Rückseite)
1. **Fester Gehäuseboden (Außenring Ø 150 bis 180 mm):**
   * Feste C/D-Logarithmusskala ($1$ bis $10$ bzw. $10$ bis $100\,\text{kn}$).
2. **Mittelscheibe / Rotor (Sichtfenster Ø 150 mm):**
   * Sinus-Skala ($6^\circ$ bis $90^\circ$) am Außenrand.
   * Grüner $100\%$-Target-Indexfluchtzeiger.
   * Prozent-Noniusstriche: $-15\%, -10\%, -5\%, +5\%$.
---
## 5. Vollständige ORC-Polardaten (J/125 Referenzmatrix)

| Parameter / TWA | 4 kn | 6 kn | 8 kn | 10 kn | 12 kn | 14 kn | 16 kn | 20 kn | 24 kn |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Beat Angle** | $41{,}8^\circ$ | $41{,}8^\circ$ | $40{,}0^\circ$ | $38{,}5^\circ$ | $38{,}0^\circ$ | $37{,}7^\circ$ | $38{,}1^\circ$ | $38{,}4^\circ$ | $39{,}8^\circ$ |
| **Beat VMG** | $2{,}70$ | $3{,}70$ | $4{,}44$ | $4{,}83$ | $5{,}01$ | $5{,}12$ | $5{,}19$ | $5{,}24$ | $5{,}12$ |
| **Target Beat Speed** | $3{,}62$ | $4{,}96$ | $5{,}80$ | $6{,}17$ | $6{,}36$ | $6{,}47$ | $6{,}60$ | $6{,}69$ | $6{,}66$ |
| **52°** | $4{,}14$ | $5{,}55$ | $6{,}50$ | $6{,}96$ | $7{,}15$ | $7{,}26$ | $7{,}34$ | $7{,}42$ | $7{,}38$ |
| **60°** | $4{,}37$ | $5{,}80$ | $6{,}73$ | $7{,}18$ | $7{,}38$ | $7{,}49$ | $7{,}57$ | $7{,}65$ | $7{,}65$ |
| **75°** | $4{,}52$ | $5{,}96$ | $6{,}87$ | $7{,}36$ | $7{,}64$ | $7{,}80$ | $7{,}92$ | $8{,}08$ | $8{,}16$ |
| **90°** | $4{,}48$ | $5{,}94$ | $6{,}88$ | $7{,}34$ | $7{,}71$ | $7{,}99$ | $8{,}21$ | $8{,}52$ | $8{,}70$ |
| **110°** | $4{,}55$ | $6{,}11$ | $7{,}18$ | $7{,}71$ | $8{,}00$ | $8{,}26$ | $8{,}49$ | $8{,}89$ | $9{,}21$ |
| **120°** | $4{,}42$ | $6{,}00$ | $7{,}11$ | $7{,}72$ | $8{,}20$ | $8{,}54$ | $8{,}83$ | $9{,}38$ | $9{,}94$ |
| **135°** | $3{,}82$ | $5{,}36$ | $6{,}61$ | $7{,}40$ | $7{,}94$ | $8{,}47$ | $9{,}03$ | $10{,}38$ | $11{,}69$ |
| **150°** | $3{,}23$ | $4{,}55$ | $5{,}68$ | $6{,}65$ | $7{,}36$ | $7{,}87$ | $8{,}38$ | $9{,}56$ | $11{,}93$ |
| **Run VMG** | $2{,}79$ | $3{,}94$ | $4{,}92$ | $5{,}76$ | $6{,}49$ | $7{,}07$ | $7{,}55$ | $8{,}49$ | $10{,}33$ |
| **Gybe Angle** | $142{,}8^\circ$ | $142{,}8^\circ$ | $146{,}6^\circ$ | $149{,}8^\circ$ | $157{,}6^\circ$ | $164{,}8^\circ$ | $167{,}5^\circ$ | $165{,}5^\circ$ | $143{,}6^\circ$ |

---
## 6. Vorgaben für die Pipeline (STL & SVG Artefakte)
### 6.1 CAD / 3D-Druck (STL-Dateien)
* `gehaeuse_deckel.stl`: Oberer Haltering mit $2{,}5\,\text{mm}$ Wandstärke, 6 Senkbohrungen M3.
* `gehaeuse_boden.stl`: Unterer Ring mit integrierter Nut ($173{,}0\,\text{mm} \times 2{,}4\,\text{mm}$), 6 M3-Gewindebohrungen.
* `mittelscheibe_rotor.stl`: Drehkörper mit Bund ($\varnothing 172{,}0\,\text{mm} \times 2{,}0\,\text{mm}$) und 4 Rändelsegmenten ($\varnothing 186{,}0\,\text{mm}$).
### 6.2 Laserplotter (SVG-Dateien, maßhaltig 1:1 in Millimetern)
* `laser_seite_a_deckel_kompass.svg`: $360^\circ$-Kompassrose für den Deckelring.
* `laser_seite_a_rotor_polare_fasskreise.svg`: Fasskreise, Polarkurven und Taktik-Pfeile für den Rotor (Vorderseite).
* `laser_seite_b_boden_logskala.svg`: Logarithmische C/D-Skala für den Gehäuseboden.
* `laser_seite_b_rotor_sinus_performance.svg`: Sinusskala und Nonius für den Rotor (Rückseite).
* **Farbkonventionen:**
  * `#FF0000` (Rot, $0{,}15\,\text{mm}$): Vektorschnitt (Ausschneiden / Bohrungen).
  * `#000000` (Schwarz, $0{,}25\,\text{mm}$): Feine Vektorgravur (Skalenstriche, Ziffern).
  * `#2C3E50` / `#C0392B` (Farbig): Sondergravuren (ORC-Kurven, Taktik-Markierungen).
