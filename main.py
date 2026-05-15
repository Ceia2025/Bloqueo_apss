import tkinter as tk
from config import cargar_config
from tray import Tray
from ui.login import VentanaContrasena, VentanaLogin
from ui.panel import PanelPrincipal

APP_TITULO = "Control de Aplicaciones"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITULO)
        self.geometry("560x480")
        self.withdraw()  # ocultar hasta autenticar

        self.panel = None
        self.tray = Tray(
            on_abrir=lambda: self.after(0, self._restaurar),
            on_salir=self._salir_completo,
        )

        cfg = cargar_config()
        hash_guardado = cfg.get("password_hash")

        if not hash_guardado:
            VentanaContrasena(self, self._tras_login)
        else:
            VentanaLogin(self, hash_guardado, self._tras_login, cerrar_app=True)

    def _tras_login(self, ok: bool):
        if ok:
            self.deiconify()
            self._centrar(560, 480)
            cfg = cargar_config()
            self.panel = PanelPrincipal(self, cfg["password_hash"])
            self.protocol("WM_DELETE_WINDOW", self._minimizar_a_bandeja)
            self.tray.iniciar()
        else:
            self.destroy()

    def _minimizar_a_bandeja(self):
        self.withdraw()
        self.tray.notificar("El monitor sigue activo en segundo plano.")

    def _restaurar(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _salir_completo(self, *args):
        if self.panel:
            self.panel.destruir()
        self.tray.detener()
        self.after(0, self.destroy)

    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")


if __name__ == "__main__":
    app = App()
    app.mainloop()