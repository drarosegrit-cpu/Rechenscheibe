# Technische Konzeption und Spezifikation: Taktischer Regatta-, Winddreieck- und ORC-Performance-Rechner (Ø 180 mm)
## 1. Systemübersicht und Zielsetzung
Das Instrument ist ein analoges, mechanisch gekoppeltes Navigations- und Trimmgerät für den Regatta- und Performance-Einsatz. Es vereint:
1. Einen **Taktikrechner** (Kompassrose vs. Windrichtung zur Bestimmung von Wenden-, Halse- und Bahnmarkenkursen).
2. Ein **geometrisches Fasskreis-Nomogramm** zur direkten Bestimmung des Segeltrimms aus dem scheinbaren Windwinkel $\alpha = \text{AWA}$ über einer festen Basis.
3. Ein zentriertes **ORC-Polardiagramm** zur Visualisierung der Soll-Bootsgeschwindigkeit nach ORC-Messbriefdaten.
4. Einen **logarithmischen Rechenschieber** (C/D-Skala und Performance-%-Skala) auf der Rückseite zur quantitativen Soll-Ist-Geschwindigkeitsanalyse.
Das Gerät wird im 3D-Druck (FDM/SLA) gefertigt und mittels Laserplotter beschriftet und skaliert.
---
## 2. Mechanischer Schichtaufbau (3-Lagen-Kassette)
### 2.1 Führungskonzept
Die Konstruktion verzichtet auf eine zentrale Achsschraube. Die drehbare Mittelscheibe wird über einen umlaufenden Außenbund (Feder) in einer ringförmigen Nut zwischen Gehäusedeckel und Gehäuseboden zentriert und geführt.
### 2.2 Dimensionierung (Nennmaß Ø 180 mm)
* **Gehäusedeckel (Seite A / Oben):**
  * Außendurchmesser: $180{,}0\,\text{mm}$
  * Innenfenster (Sichtbereich): $\varnothing 150{,}0\,\text{mm}$
  * Ringbreite des festen Skalenstegs: $15{,}0\,\text{mm}$
  * Dicke: $2{,}5\,\text{mm}$
  * 6 Senkbohrungen für M3-Schrauben auf Teilkreis $\varnothing 176{,}0\,\text{mm}$
* **Gehäuseboden (Seite B / Unten):**
  * Außendurchmesser: $180{,}0\,\text{mm}$
  * Innenfenster (Sichtbereich): $\varnothing 150{,}0\,\text{mm}$
  * Integrierte Ringnut: Innendurchmesser $173{,}0\,\text{mm}$, Nuttiefe in Z-Richtung $2{,}4\,\text{mm}$
  * 6 Kernlochbohrungen (M3 bzw. Einschmelzgewinde) auf Teilkreis $\varnothing 176{,}0\,\text{mm}$
* **Mittelscheibe (Rotor / Beidseitig opak beschriftet):**
  * Sichtbarer Kernbereich: $\varnothing 150{,}0\,\text{mm}$
  * Führungsbund (Feder): $\varnothing 172{,}0\,\text{mm}$, Dicke $2{,}0\,\text{mm}$
  * 4 symmetrisch angeordnete Rändelsegmente ($30^\circ$ Winkelbreite), die durch radiale Aussparungen des Gehäuses auf einen Durchmesser von $\varnothing 186{,}0\,\text{mm}$ hervorragen ($3\,\text{mm}$ Greifüberstand).
* **Lager- und Fertigungstoleranzen:**
  * Radiales Spiel: $\Delta r = 0{,}5\,\text{mm}$ ($173{,}0\,\text{mm}$ Nut vs. $172{,}0\,\text{mm}$ Bund).
  * Axiales Spiel: $\Delta z = 0{,}4\,\text{mm}$ ($2{,}4\,\text{mm}$ Nuttiefe vs. $2{,}0\,\text{mm}$ Bunddicke).
  * Gravurvertiefung: Beidseitig $0{,}4\,\text{mm}$ plane Absenkung zum Schutz der Lasermarkierung gegen Reibung.
---
## 3. Mathematische und Geometrische Grundlagen
### 3.1 Das Winddreieck über Grund
Es gilt die Vektorgleichung:
$$\vec{v}_{\text{scheinbar}} = \vec{v}_{\text{wahr}} - \vec{v}_{\text{Boot}}$$
bzw.
$$\vec{v}_{\text{wahr}} = \vec{v}_{\text{Boot}} + \vec{v}_{\text{scheinbar}}$$
* $\text{SOG}$: Geschwindigkeit über Grund (Bootsvektor entlang Schiffslängsachse).
* $\text{AWS}$: Scheinbare Windgeschwindigkeit (Apparent Wind Speed).
* $\alpha = \text{AWA}$: Scheinbarer Windwinkel zur Schiffslängsachse (Windfahne).
* $\text{TWS}$: Wahre Windgeschwindigkeit (True Wind Speed).
* $\beta = \text{TWA}$: Wahrer Windwinkel (True Wind Angle).
### 3.2 Geometrie der Fasskreis-Kurvenschar (Option 2: Feste Sehne über wahrem Wind)
* **Basissehne:** Wahre Windrichtung als Einheitsstrecke $L = 1{,}0$ vom Drehzentrum $W_0 (0,0)$ zum Kopfpunkt $W_1 (0, L)$ entlang der $0^\circ$-Achse.
* **Peripheriewinkelsatz:** Alle Punkte $B(x, y)$, an denen der Winkel zwischen Bootsvektor (nach $W_0$) und scheinbarem Windvektor (von $W_1$) exakt $\alpha$ beträgt, liegen auf einem Fasskreis über $W_0 W_1$.
* **Mittelpunkt des Fasskreises für Winkel $\alpha$:**
  $$x_M = \pm \frac{L}{2} \cot(\alpha), \quad y_M = \frac{L}{2}$$
  *(Plus für Steuerbordbug, Minus für Backbordbug).*
* **Radius des Fasskreises:**
  $$R_\alpha = \frac{L}{2 \sin(\alpha)}$$
* **Schrittweite:** $\Delta\alpha = 2{,}5^\circ$ im Bereich von $20^\circ \le \alpha \le 160^\circ$.
### 3.3 Logarithmische Rechenskalen (C/D- und S-Skala)
Auf der Rückseite gilt für die $360^\circ$-Winkelabbildung einer Dekade ($1$ bis $10$ bzw. $10$ bis $100\,\text{kn}$):
* **Geschwindigkeitsskala:** $\varphi_v = 360^\circ \cdot \log_{10}(v)$
* **Sinusskala:** $\varphi_\theta = 360^\circ \cdot \log_{10}(\sin(\theta))$
* **Prozentskala (Performance):**
  $$\Delta\varphi = 360^\circ \cdot \log_{10}\left(\frac{\text{SOG}}{\text{Target SOG}}\right)$$
  Eine Abweichung von $-5\%$ entspricht $-8{,}0^\circ$, $-10\%$ entspricht $-16{,}5^\circ$, $+5\%$ entspricht $+7{,}6^\circ$.
---
## 4. Skalenbelegung und Gravur-Architektur
### 4.1 Seite A: Taktik- und Trimm-Rechner (Vorderseite)
#### Fester Gehäusedeckel (Außenring Ø 150 bis 180 mm)
* Gravur einer vollständigen **$360^\circ$-Kompassrose**:
  * Hauptteilungen alle $10^\circ$, Mittelteilstriche alle $5^\circ$, Einzelstriche alle $1^\circ$.
  * Bezifferung alle $30^\circ$ ($000^\circ, 030^\circ, 060^\circ, \dots, 330^\circ$).
#### Rotierende Mittelscheibe (Sichtfenster Ø 150 mm)
* **Außenrand ($\varnothing 142$ bis $150\,\text{mm}$):**
  * Taktischer Windpfeil **TRUE WIND** bei $0^\circ$.
  * **Beat Angle Indikatoren (Upwind Target Marks):** Markierungen bei $37{,}7^\circ$ bis $41{,}8^\circ$ beidseitig (Stb/Bb).
  * **Gybe Angle Indikatoren (Downwind VMG Marks):** Markierungen bei $142{,}8^\circ$ bis $167{,}5^\circ$ beidseitig (Stb/Bb).
* **Zentralbereich ($\varnothing 0$ bis $140\,\text{mm}$):**
  * **ORC-Polarkurven** für die 9 Windstärken ($4, 6, 8, 10, 12, 14, 16, 20, 24\,\text{kn}$).
  * **Fasskreis-Kurvenschar** mit $\Delta\alpha = 2{,}5^\circ$, hervorgehoben alle $10^\circ$.
### 4.2 Seite B: Logarithmischer Performance-Rechner (Rückseite)
#### Fester Gehäuseboden (Außenring Ø 150 bis 180 mm)
* Feste logarithmische **C/D-Geschwindigkeitsskala** für Knoten:
  * Bereich: $1$ bis $30\,\text{kn}$ (bzw. $1$ bis $10$ mit Dekadenumrechnung).
#### Rotierende Mittelscheibe (Sichtfenster Ø 150 mm)
* **Sinusskala (S-Skala):** Winkel von $6^\circ$ bis $90^\circ$.
* **Performance-%-Nonius:**
  * $100\%$-Indexmarke (fluchtend mit der Soll-Geschwindigkeit).
  * Abweichungsstriche für $-15\%, -10\%, -5\%, 0\%, +5\%$.
---
## 5. Eingebundene ORC-Leistungsdaten (Referenztabelle)
Die folgenden Messbriefdaten liegen den Polarkurven und Taktikmarken zugrunde:

| Parameter / TWA | 4 kn | 6 kn | 8 kn | 10 kn | 12 kn | 14 kn | 16 kn | 20 kn | 24 kn |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Beat Angle** | $41{,}8^\circ$ | $41{,}8^\circ$ | $40{,}0^\circ$ | $38{,}5^\circ$ | $38{,}0^\circ$ | $37{,}7^\circ$ | $38{,}1^\circ$ | $38{,}4^\circ$ | $39{,}8^\circ$ |
| **Beat VMG** | $2{,}70$ | $3{,}70$ | $4{,}44$ | $4{,}83$ | $5{,}01$ | $5{,}12$ | $5{,}19$ | $5{,}24$ | $5{,}12$ |
| **Target Beat Speed** | $3{,}62$ | $4{,}96$ | $5{,}80$ | $6{,}17$ | $6{,}36$ | $6{,}47$ | $6{,}60$ | $6{,}69$ | $6{,}66$ |
| **$52^\circ$** | $4{,}14$ | $5{,}55$ | $6{,}50$ | $6{,}96$ | $7{,}15$ | $7{,}26$ | $7{,}34$ | $7{,}42$ | $7{,}38$ |
| **$60^\circ$** | $4{,}37$ | $5{,}80$ | $6{,}73$ | $7{,}18$ | $7{,}38$ | $7{,}49$ | $7{,}57$ | $7{,}65$ | $7{,}65$ |
| **$75^\circ$** | $4{,}52$ | $5{,}96$ | $6{,}87$ | $7{,}36$ | $7{,}64$ | $7{,}80$ | $7{,}92$ | $8{,}08$ | $8{,}16$ |
| **$90^\circ$** | $4{,}48$ | $5{,}94$ | $6{,}88$ | $7{,}34$ | $7{,}71$ | $7{,}99$ | $8{,}21$ | $8{,}52$ | $8{,}70$ |
| **$110^\circ$** | $4{,}55$ | $6{,}11$ | $7{,}18$ | $7{,}71$ | $8{,}00$ | $8{,}26$ | $8{,}49$ | $8{,}89$ | $9{,}21$ |
| **$120^\circ$** | $4{,}42$ | $6{,}00$ | $7{,}11$ | $7{,}72$ | $8{,}20$ | $8{,}54$ | $8{,}83$ | $9{,}38$ | $9{,}94$ |
| **$135^\circ$** | $3{,}82$ | $5{,}36$ | $6{,}61$ | $7{,}40$ | $7{,}94$ | $8{,}47$ | $9{,}03$ | $10{,}38$ | $11{,}69$ |
| **$150^\circ$** | $3{,}23$ | $4{,}55$ | $5{,}68$ | $6{,}65$ | $7{,}36$ | $7{,}87$ | $8{,}38$ | $9{,}56$ | $11{,}93$ |
| **Run VMG** | $2{,}79$ | $3{,}94$ | $4{,}92$ | $5{,}76$ | $6{,}49$ | $7{,}07$ | $7{,}55$ | $8{,}49$ | $10{,}33$ |
| **Gybe Angle** | $142{,}8^\circ$ | $142{,}8^\circ$ | $146{,}6^\circ$ | $149{,}8^\circ$ | $157{,}6^\circ$ | $164{,}8^\circ$ | $167{,}5^\circ$ | $165{,}5^\circ$ | $143{,}6^\circ$ |

---
## 6. Bedienungsabläufe an Bord
### 6.1 Taktischer Kursabgleich (Pre-Start / Upwind)
1. Die gemessene wahre Windrichtung (TWD, z. B. $240^\circ$) wird eingestellt, indem der Pfeil **TRUE WIND** der Mittelscheibe auf $240^\circ$ der festen Kompassrose gedreht wird.
2. Der Steuerkurs am Wind auf Steuerbordbug wird an der Beat-Marke abgelesen: $240^\circ + 38^\circ = 278^\circ$.
3. Der Kurs nach einer Wende auf Backbordbug steht direkt an der gegenüberliegenden Beat-Marke: $240^\circ - 38^\circ = 202^\circ$.
4. Dreht der Wind (z. B. auf $245^\circ$), wird die Scheibe um $5^\circ$ nachgeführt; alle neuen Anliegelinien zu Luv- und Leetonnen sind sofort ersichtlich.
### 6.2 Performance- und Trimmkontrolle (Szenario 2)
1. Der Steuermann hält das Schiff nach Windfahne auf scheinbarem Windwinkel $\alpha = 38^\circ$.
2. Der Navigator blickt auf den $38^\circ$-Fasskreisbogen und sucht den Schnittpunkt mit der aktuellen Windkurve (z. B. $12\,\text{kn}$).
3. **Ergebnis:** Die Soll-Geschwindigkeit beträgt $6{,}36\,\text{kn}$.
4. Auf Seite B wird die $100\%$-Marke auf $6{,}36\,\text{kn}$ gelegt. Der tatsächliche GPS-Wert ($6{,}0\,\text{kn}$) zeigt direkt auf der Prozentskala: **$-5{,}7\%$ Unterperformance**.
---
## 7. Fertigungsspezifikation
### 7.1 3D-Druck (FDM / SLA)
* **Material:** PETG, ASA oder ABS (UV- und salzwasserbeständig, formstabil bis $>70^\circ\text{C}$).
* **Schichthöhe:** $0{,}15\,\text{mm}$ bis $0{,}20\,\text{mm}$ (Glättung der Skalenbetten per "Ironing" / Bügeln empfohlen).
* **Infill:** Mindestens $30\%$ gyroidal für hohe Verwindungssteifigkeit.
* **Farbe:** Helles Weiß oder Hellgrau als Kontrastgrund für die Lasergravur.
### 7.2 Laserbeschriftung (CO2- oder Faserlaser)
* **Farbcodierung in den Vektordateien (SVG):**
  * `Rot (#FF0000)`: Vektorschnitt (Cut lines).
  * `Schwarz (#000000)`: Feine Liniengravur (Skalenstriche, Fasskreise, Ziffern).
  * `Blau (#0000FF)`: Vektor-Schraffur / Ausfüllung (ORC-Kurven, Pfeile).
