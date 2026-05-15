"""
iconos.py
Extrae íconos de .exe usando win32gui (pywin32).
Diseñado para lazy loading: carga en segundo plano sin bloquear la UI.
"""
import threading
import win32gui
import win32ui
import win32con
from PIL import Image, ImageTk

# Caché global: ruta -> PhotoImage
_cache: dict = {}
_cache_lock = threading.Lock()


def _hicon_a_photoimage(hicon, size: int) -> "ImageTk.PhotoImage | None":
    """Convierte un HICON de Windows en PhotoImage de Tkinter."""
    try:
        # Crear DC y bitmap compatibles
        hdc      = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hdc_mem  = hdc.CreateCompatibleDC()
        hbmp     = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc_mem.SelectObject(hbmp)

        # Fondo blanco
        hdc_mem.FillSolidRect((0, 0, 32, 32), 0x00FFFFFF)

        # Dibujar ícono
        win32gui.DrawIconEx(hdc_mem.GetHandleOutput(), 0, 0,
                            hicon, 32, 32, 0, None, win32con.DI_NORMAL)

        # Convertir a PIL
        bmpinfo = hbmp.GetInfo()
        bmpstr  = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            "RGBA",
            (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
            bmpstr, "raw", "BGRA", 0, 1
        )
        img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    except Exception:
        return None
    finally:
        try:
            win32gui.DestroyIcon(hicon)
        except Exception:
            pass



def obtener_icono_exe(ruta: str, size: int = 16) -> "ImageTk.PhotoImage | None":
    """
    Extrae el ícono de un .exe y retorna PhotoImage.
    Usa caché para no repetir extracción.
    """
    if not ruta:
        return None

    clave = f"{ruta}_{size}"
    with _cache_lock:
        if clave in _cache:
            return _cache[clave]

    try:
        # Extraer ícono grande (índice 0)
        large, small = win32gui.ExtractIconEx(ruta, 0)

        hicon = None
        if large:
            hicon = large[0]
            # Destruir los que no usamos
            for h in large[1:]:
                win32gui.DestroyIcon(h)
        if small:
            for h in small:
                if hicon and h != hicon:
                    win32gui.DestroyIcon(h)
                elif not hicon:
                    hicon = h

        if not hicon:
            return None

        foto = _hicon_a_photoimage(hicon, size)

        with _cache_lock:
            _cache[clave] = foto

        return foto

    except Exception:
        return None


def lazy_load_iconos(apps: list, size: int, callback_ui):
    """
    Carga íconos en segundo plano de a uno (lazy loading).
    Por cada ícono listo llama callback_ui(exe, PhotoImage) en el hilo de fondo.
    El caller debe usar .after(0, ...) para actualizar la UI desde el hilo principal.

    apps        → lista de dicts con 'exe' y 'ruta'
    size        → tamaño en píxeles
    callback_ui → función(exe, foto) que se llama cuando el ícono está listo
    """
    def worker():
        for app in apps:
            ruta = app.get("ruta", "")
            exe  = app.get("exe", "")
            if not ruta or not exe:
                continue
            foto = obtener_icono_exe(ruta, size)
            if foto:
                callback_ui(exe, foto)

    threading.Thread(target=worker, daemon=True).start()


def limpiar_cache():
    with _cache_lock:
        _cache.clear()