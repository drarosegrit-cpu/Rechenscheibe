#!/usr/bin/env python3
"""
preview_engine.py - Hochpräzise Single-Source-of-Truth Rendering-Engine (300 DPI)
Projekt: Nautische Rechenscheibe JPK 1080 (GER 7447 - TRUE GRIT)

Architektur:
- Rendert die generierten Laser-/CAM-Vektordateien (SVG) direkt und verlustfrei
  in hochauflösende 300-DPI-PNG-Vorschauen über die Systembibliotheken `librsvg2` und `libcairo`.
- Beseitigt redundanten Matplotlib-Zeichencode vollständig:
  Was im SVG definiert ist, ist zu 100% bit- und pixelidentisch in der PNG-Vorschau (WYSIWYG).
"""

import ctypes
from pathlib import Path
from typing import List, Optional

from config_manager import CONFIG, GEOM
from polar_parser import PolarData
from vector_engine import (
    generate_laser_seite_a_montiert,
    generate_laser_seite_b_montiert,
    generate_laser_seite_a_rotor,
)


# ==============================================================================
# CTYPES BINDINGS ZU LIBRSVG & LIBCAIRO
# ==============================================================================

class RsvgDimensionData(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("em", ctypes.c_double),
        ("ex", ctypes.c_double),
    ]


try:
    _rsvg = ctypes.CDLL("librsvg-2.so.2")
    _cairo = ctypes.CDLL("libcairo.so.2")
    _gobj = ctypes.CDLL("libgobject-2.0.so.0")

    # Funktions-Signaturen definieren
    _rsvg.rsvg_handle_new_from_file.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
    _rsvg.rsvg_handle_new_from_file.restype = ctypes.c_void_p

    _rsvg.rsvg_handle_set_dpi_x_y.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]

    _rsvg.rsvg_handle_get_dimensions.argtypes = [ctypes.c_void_p, ctypes.POINTER(RsvgDimensionData)]

    _rsvg.rsvg_handle_render_cairo.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _rsvg.rsvg_handle_render_cairo.restype = ctypes.c_bool

    _cairo.cairo_image_surface_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
    _cairo.cairo_image_surface_create.restype = ctypes.c_void_p

    _cairo.cairo_create.argtypes = [ctypes.c_void_p]
    _cairo.cairo_create.restype = ctypes.c_void_p

    _cairo.cairo_set_source_rgb.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double]
    _cairo.cairo_paint.argtypes = [ctypes.c_void_p]

    _cairo.cairo_surface_write_to_png.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    _cairo.cairo_surface_write_to_png.restype = ctypes.c_int

    _cairo.cairo_destroy.argtypes = [ctypes.c_void_p]
    _cairo.cairo_surface_destroy.argtypes = [ctypes.c_void_p]
    _gobj.g_object_unref.argtypes = [ctypes.c_void_p]

    RSVG_AVAILABLE = True
except Exception as e:
    RSVG_AVAILABLE = False
    _rsvg_error = e


def render_svg_to_png(svg_path: Path, png_path: Path, dpi: float = 300.0) -> bool:
    """
    Rendert eine SVG-Datei direkt und verlustfrei mit der angegebenen DPI-Zahl in eine PNG-Datei.
    Setzt einen neutralen weißen Hintergrund für beste Druck- und Kontrastwirkung.
    """
    if not RSVG_AVAILABLE:
        raise RuntimeError(f"librsvg/libcairo nicht verfügbar: {_rsvg_error}")

    svg_str = str(svg_path.resolve()).encode("utf-8")
    png_str = str(png_path.resolve()).encode("utf-8")

    # 1. SVG laden
    handle = _rsvg.rsvg_handle_new_from_file(svg_str, None)
    if not handle:
        raise IOError(f"Fehler beim Laden der SVG-Datei: {svg_path}")

    try:
        # 2. DPI-Auflösung setzen
        _rsvg.rsvg_handle_set_dpi_x_y(handle, ctypes.c_double(dpi), ctypes.c_double(dpi))

        # 3. Pixelabmessungen abfragen
        dim = RsvgDimensionData()
        _rsvg.rsvg_handle_get_dimensions(handle, ctypes.byref(dim))
        width, height = dim.width, dim.height

        if width <= 0 or height <= 0:
            width, height = 2400, 2400

        # 4. Cairo-Surface & Context erstellen (ARGB32)
        surface = _cairo.cairo_image_surface_create(0, width, height)
        cr = _cairo.cairo_create(surface)

        # 5. Weißer Hintergrund
        _cairo.cairo_set_source_rgb(cr, ctypes.c_double(1.0), ctypes.c_double(1.0), ctypes.c_double(1.0))
        _cairo.cairo_paint(cr)

        # 6. SVG rendern
        success = _rsvg.rsvg_handle_render_cairo(handle, cr)
        if not success:
            raise RuntimeError(f"Fehler beim Rendern von {svg_path}")

        # 7. Als PNG speichern
        png_path.parent.mkdir(parents=True, exist_ok=True)
        ret = _cairo.cairo_surface_write_to_png(surface, png_str)
        if ret != 0:
            raise IOError(f"Fehler beim Schreiben der PNG-Datei: {png_path} (Status {ret})")

        return True
    finally:
        _cairo.cairo_destroy(cr)
        _cairo.cairo_surface_destroy(surface)
        _gobj.g_object_unref(handle)


# ==============================================================================
# VORSCHAU-GENERATOREN
# ==============================================================================

def render_assembled_montage(
    polar: PolarData,
    outfile: Path,
    twa_pointer_deg: float = 40.0,
    dpi: int = 300
) -> Path:
    """
    Rendert die montierte Gesamtansicht der Vorderseite (Seite A) direkt aus dem SVG.
    """
    svg_dir = outfile.parent.parent / "svg"
    svg_file = svg_dir / "laser_seite_a_montiert.svg"
    generate_laser_seite_a_montiert(svg_file, polar, twa_pointer_deg=twa_pointer_deg)
    render_svg_to_png(svg_file, outfile, dpi=dpi)
    return outfile


def render_assembled_seite_b(
    outfile: Path,
    cursor_angle_deg: float = 30.0,
    dpi: int = 300
) -> Path:
    """
    Rendert die montierte Gesamtansicht der Rückseite (Seite B) direkt aus dem SVG.
    """
    svg_dir = outfile.parent.parent / "svg"
    svg_file = svg_dir / "laser_seite_b_montiert.svg"
    generate_laser_seite_b_montiert(svg_file, cursor_angle_deg=cursor_angle_deg)
    render_svg_to_png(svg_file, outfile, dpi=dpi)
    return outfile


def render_rotor_face(
    polar: PolarData,
    outfile: Path,
    dpi: int = 300
) -> Path:
    """
    Rendert die Detailansicht des Rotors (Vorderseite) direkt aus dem SVG.
    """
    svg_dir = outfile.parent.parent / "svg"
    svg_file = svg_dir / "laser_seite_a_rotor_vorderseite.svg"
    if not svg_file.exists():
        generate_laser_seite_a_rotor(svg_file, polar)
    render_svg_to_png(svg_file, outfile, dpi=dpi)
    return outfile


def render_all_previews(
    polar: PolarData,
    out_dir: Path,
    twa_pointer_deg: float = 40.0,
    dpi: int = 300
) -> List[Path]:
    """
    Rendert alle 3 hochauflösenden 300-DPI-Vorschauen direkt aus den SVGs (Single Source of Truth).
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    f_seite_a = out_dir / "gesamtansicht_seite_a_montiert.png"
    render_assembled_montage(polar, f_seite_a, twa_pointer_deg=twa_pointer_deg, dpi=dpi)

    f_seite_b = out_dir / "gesamtansicht_seite_b_montiert.png"
    render_assembled_seite_b(f_seite_b, dpi=dpi)

    f_rotor = out_dir / "rotor_vorderseite_weg_a.png"
    render_rotor_face(polar, f_rotor, dpi=dpi)

    return [f_seite_a, f_seite_b, f_rotor]
