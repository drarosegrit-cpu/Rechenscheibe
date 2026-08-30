import ezdxf
import cmath
import math
import openpyxl as xls
from functools import wraps
from pathlib import Path
from ezdxf.math import Vec2

# ==========================================
# DECORATORS FÜR GRAD/RADIAN KONVERTIERUNG
# ==========================================

def degrees_input(func):
    """Konvertiert das Winkel-Argument (Grad) automatisch in Radiant für cmath."""
    @wraps(func)
    def wrapper(magnitude, angle_deg):
        return func(magnitude, math.radians(angle_deg))
    return wrapper

def degrees_output(func):
    """Konvertiert den Rückgabewinkel von Radiant zurück in Grad (0-360)."""
    @wraps(func)
    def wrapper(z):
        magnitude, angle_rad = func(z)
        angle_deg = math.degrees(angle_rad) % 360
        return magnitude, angle_deg
    return wrapper

# ==========================================
# KERN-FUNKTIONEN (CMATH WRAPPER)
# ==========================================

@degrees_input
def to_complex(magnitude, angle_rad):
    """Erzeugt komplexe Zahl: Real=Nord, Imag=Ost."""
    return cmath.rect(magnitude, angle_rad)

@degrees_output
def from_complex(z):
    """Gibt (Magnitude, Grad) zurück."""
    return cmath.polar(z)

def z_to_coords(z):
    """Mapping für DXF: X=Osten (Imag), Y=Norden (Real)."""
    return (z.imag, z.real)

# ==========================================
# ZEICHENFUNKTIONEN
# ==========================================

def AddNumbers(modspc, text, z, height, angle, alignment):
    """Fügt Text an einer komplexen Position z ein."""
    pos = z_to_coords(z)
    t = modspc.add_text(text).set_pos(pos, align=alignment)
    t.dxf.style = "OpenSans-Italic"
    t.dxf.height = height
    t.dxf.layer = "Numbers"
    t.dxf.rotation = angle

def PlotLogScales(doc, modspc, radius):
    """Zeichnet die logarithmischen Rechenringe."""
    doc.layers.new(name="InnerRing")
    doc.layers.new(name="OuterRing")

    x = 100 # Startwert (entspricht 1.0)
    dash = 0.5
    
    while x <= 1000:
        # Winkel berechnen: log10(1)=0 -> 0°, log10(10)=1 -> 360°
        angle = math.log10(x/100) * 360
        z_pos = to_complex(radius, angle)
        
        # Skalenstriche (vereinfacht für dieses Beispiel)
        p1 = z_to_coords(z_pos)
        p2 = z_to_coords(to_complex(radius + dash, angle))
        modspc.add_line(p1, p2, dxfattribs={"layer": "OuterRing"})
        
        if x % 100 == 0:
            val_text = str(int(x/100))
            AddNumbers(modspc, val_text, to_complex(radius + 3, angle), 2.5, -angle, "CENTER")
        
        # Inkrement-Logik (vereinfacht)
        x += 10 if x < 200 else 50 if x < 500 else 100

def PlotCompass(modspc, radius):
    """Zeichnet die 360° Kompassrose."""
    doc.layers.new(name="Compass")
    
    for deg in range(0, 360, 1):
        # Tick-Länge variieren
        length = 1.5 if deg % 10 == 0 else 0.7
        
        z_start = to_complex(radius, deg)
        z_end = to_complex(radius - length, deg)
        
        modspc.add_line(z_to_coords(z_start), z_to_coords(z_end), dxfattribs={"layer": "Compass"})
        
        # Beschriftung alle 30 Grad
        if deg % 30 == 0:
            AddNumbers(modspc, str(deg), to_complex(radius - 4, deg), 3.0, -deg, "CENTER")

def PlotPolarSpeed(modspc, excel_path, radius_scale):
    """Lädt Polardaten und zeichnet Performance-Kurven."""
    try:
        wb = xls.load_workbook(excel_path)
        sheet = wb.active
        # Datenbereich: A2 (Winkel) bis H74 (Speeds für verschiedene Windstärken)
        data = sheet["A2":"H74"]
        
        # 7 Listen für 7 Windstärken (z.B. 6, 8, 10, 12, 14, 16, 20 kn)
        curves = [[] for _ in range(7)]
        
        for row in data:
            angle_deg = row[0].value
            if angle_deg is None: continue
            
            for i in range(1, 8):
                speed = row[i].value
                if speed:
                    # Umrechnung in Koordinate via cmath
                    z = to_complex(speed * radius_scale, angle_deg)
                    curves[i-1].append(z_to_coords(z))
        
        for curve_points in curves:
            if curve_points:
                modspc.add_lwpolyline(curve_points, dxfattribs={"layer": "PolarCurves"})
                
    except Exception as e:
        print(f"Fehler beim Laden der Excel-Daten: {e}")

# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    # Datei-Setup
    doc = ezdxf.new('R2018') # Modernere DXF Version
    modspc = doc.modelspace()
    
    # Pfad-Handling via pathlib (modern)
    excel_file = Path.home() / "Documents" / "J125.xlsx"
    
    # Parameter
    BASE_RADIUS = 50
    
    # Zeichnen
    PlotCompass(modspc, BASE_RADIUS)
    PlotLogScales(doc, modspc, BASE_RADIUS + 10)
    
    if excel_file.exists():
        PlotPolarSpeed(modspc, excel_file, radius_scale=2.0)
    else:
        print(f"Hinweis: {excel_file} nicht gefunden. Polarkurven wurden übersprungen.")

    # Speichern
    output_path = "Nautische_Rechenscheibe.dxf"
    doc.saveas(output_path)
    print(f"Datei erfolgreich gespeichert: {output_path}")
