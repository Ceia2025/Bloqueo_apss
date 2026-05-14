import threading
from PIL import Image, ImageDraw
import pystray

APP_TITULO = "Control de Aplicaciones"


def crear_icono_img() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(32, 4), (60, 16), (60, 36), (32, 60), (4, 36), (4, 16)],
                 fill="#0078D4")
    draw.rectangle([24, 30, 40, 44], fill="white")
    draw.arc([26, 22, 38, 34], start=0, end=180, fill="white", width=3)
    return img


class Tray:
    def __init__(self, on_abrir, on_salir):
        self.on_abrir = on_abrir
        self.on_salir = on_salir
        self.icon = None

    def iniciar(self):
        menu = pystray.Menu(
            pystray.MenuItem("Abrir panel", self._abrir, default=True),
            pystray.MenuItem("Salir completamente", self._salir),
        )
        self.icon = pystray.Icon(
            name=APP_TITULO,
            icon=crear_icono_img(),
            title=APP_TITULO,
            menu=menu,
        )
        threading.Thread(target=self.icon.run, daemon=True).start()

    def notificar(self, mensaje: str):
        if self.icon:
            try:
                self.icon.notify(mensaje, APP_TITULO)
            except Exception:
                pass

    def detener(self):
        if self.icon:
            self.icon.stop()

    def _abrir(self, icon=None, item=None):
        self.on_abrir()

    def _salir(self, icon=None, item=None):
        self.on_salir()