"""
iconos.py
Extrae el ícono de un archivo .exe y lo convierte en PhotoImage de Tkinter.
Funciona solo en Windows. En otros sistemas retorna None silenciosamente.
"""

import os
import tkinter as tk
from PIL import Image, ImageTk

# Caché para no extraer el mismo ícono dos veces
_cache: dict[str, ImageTk.PhotoImage | None] = {}


def obtener_icono_exe(ruta_exe: str, size: int = 20) -> "ImageTk.PhotoImage | None":
    """
    Dado el path completo de un .exe, retorna un PhotoImage con su ícono.
    Si no puede extraerlo, retorna None.
    
    Parámetro size: tamaño en píxeles del ícono (default 20 para listas).
    """
    if ruta_exe in _cache:
        return _cache[ruta_exe]

    icono = _extraer_icono(ruta_exe, size)
    _cache[ruta_exe] = icono
    return icono


def _extraer_icono(ruta_exe: str, size: int) -> "ImageTk.PhotoImage | None":
    if not ruta_exe or not os.path.exists(ruta_exe):
        return None

    # Método 1: win32ui (pywin32) — más confiable
    try:
        import win32ui
        import win32con
        import win32gui

        large, small = win32gui.ExtractIconEx(ruta_exe, 0)
        if not large and not small:
            return None

        hicon = large[0] if large else small[0]

        # Limpiar íconos no usados
        for h in large[1:]:
            win32gui.DestroyIcon(h)
        for h in small:
            win32gui.DestroyIcon(h)

        # Dibujar el ícono en un DC
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc2 = hdc.CreateCompatibleDC()
        hdc2.SelectObject(hbmp)
        hdc2.DrawIcon((0, 0), hicon)
        win32gui.DestroyIcon(hicon)

        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            "RGBA",
            (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
            bmpstr, "raw", "BGRA", 0, 1
        )
        img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    except Exception:
        pass

    # Método 2: icoextract — más simple pero menos compatible
    try:
        import icoextract

        extractor = icoextract.IconExtractor(ruta_exe)
        data = extractor.get_icon()
        if data:
            img = Image.open(data)
            img = img.resize((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
    except Exception:
        pass

    return None


def limpiar_cache():
    """Limpia el caché de íconos (libera memoria)."""
    _cache.clear()