import tkinter as tk
from tkinter import messagebox
from config import hash_txt, cargar_config, guardar_config, MAX_INTENTOS
from ui import tema as T


def _aplicar_tema_ventana(ventana):
    """Aplica el tema actual a una ventana Toplevel."""
    c = T.colores()
    T.aplicar_a_widget(ventana, c)


class VentanaContrasena(tk.Toplevel):
    """Crear o cambiar contraseña maestra."""

    def __init__(self, parent, callback, titulo="Crear contraseña"):
        super().__init__(parent)
        self.callback = callback
        c = T.colores()
        self.title(titulo)
        self.resizable(False, False)
        self.configure(bg=c["bg"])
        self.grab_set()
        self.lift()
        self.focus_force()
        self._centrar(380, 260)
        self.protocol("WM_DELETE_WINDOW", lambda: self.callback(False))

        # Cabecera
        cab = tk.Frame(self, bg=c["cabecera_bg"], pady=16)
        cab.pack(fill="x")
        tk.Label(cab, text=f"🔐 {titulo}",
                 font=("Segoe UI", 12, "bold"),
                 bg=c["cabecera_bg"], fg=c["cabecera_fg"]).pack()
        tk.Label(cab, text="Esta contraseña protege el acceso al panel.",
                 font=("Segoe UI", 9),
                 bg=c["cabecera_bg"], fg=c["cabecera_fg"]).pack()

        frame = tk.Frame(self, bg=c["bg"], padx=30, pady=14)
        frame.pack(fill="x")

        tk.Label(frame, text="Nueva contraseña:", font=("Segoe UI", 9),
                 bg=c["bg"], fg=c["fg"], anchor="w").grid(
                     row=0, column=0, sticky="w", pady=6)
        self.e1 = tk.Entry(frame, show="●", width=26, font=("Segoe UI", 10),
                           bg=c["entry_bg"], fg=c["entry_fg"],
                           insertbackground=c["fg"], relief="flat",
                           highlightthickness=1, highlightbackground=c["separador"])
        self.e1.grid(row=0, column=1, padx=10, ipady=4)

        tk.Label(frame, text="Confirmar:", font=("Segoe UI", 9),
                 bg=c["bg"], fg=c["fg"], anchor="w").grid(
                     row=1, column=0, sticky="w", pady=6)
        self.e2 = tk.Entry(frame, show="●", width=26, font=("Segoe UI", 10),
                           bg=c["entry_bg"], fg=c["entry_fg"],
                           insertbackground=c["fg"], relief="flat",
                           highlightthickness=1, highlightbackground=c["separador"])
        self.e2.grid(row=1, column=1, padx=10, ipady=4)

        self.lbl_error = tk.Label(self, text="", fg="#e74c3c",
                                  bg=c["bg"], font=("Segoe UI", 9))
        self.lbl_error.pack()

        tk.Button(self, text="Guardar contraseña", command=self._guardar,
                  bg=c["cabecera_bg"], fg="white", font=("Segoe UI", 11),
                  relief="flat", padx=30, pady=10, width=18,
                  activebackground=c["btn_cambiar"],
                  activeforeground="white").pack(pady=12)

        self.e1.focus()
        self.bind("<Return>", lambda e: self._guardar())

    def _guardar(self):
        p1, p2 = self.e1.get(), self.e2.get()
        if not p1:
            messagebox.showwarning("Aviso", "La contraseña no puede estar vacía.", parent=self)
            return
        if p1 != p2:
            self.lbl_error.config(text="Las contraseñas no coinciden.")
            self.e1.delete(0, "end")
            self.e2.delete(0, "end")
            self.e1.focus()
            return
        cfg = cargar_config()
        cfg["password_hash"] = hash_txt(p1)
        guardar_config(cfg)
        messagebox.showinfo("Listo", "✅ Contraseña guardada.", parent=self)
        self.destroy()
        self.callback(True)

    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")


class VentanaLogin(tk.Toplevel):
    """Solicitar contraseña maestra al iniciar."""

    def __init__(self, parent, hash_guardado: str, callback, cerrar_app: bool = False):
        super().__init__(parent)
        self.hash_guardado = hash_guardado
        self.callback      = callback
        self.cerrar_app    = cerrar_app
        self.intentos      = 0
        c = T.colores()

        self.title("Control de Aplicaciones")
        self.resizable(False, False)
        self.configure(bg=c["bg"])
        self.grab_set()
        self.lift()
        self.focus_force()
        self._centrar(380, 280)
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

        # Cabecera con color
        cab = tk.Frame(self, bg=c["cabecera_bg"], pady=20)
        cab.pack(fill="x")
        tk.Label(cab, text="🔒 Control de Aplicaciones",
                 font=("Segoe UI", 14, "bold"),
                 bg=c["cabecera_bg"], fg=c["cabecera_fg"]).pack()
        tk.Label(cab, text="Ingresa tu contraseña maestra para continuar.",
                 font=("Segoe UI", 9),
                 bg=c["cabecera_bg"], fg=c["cabecera_fg"]).pack(pady=(2, 0))

        frame = tk.Frame(self, bg=c["bg"], padx=30, pady=16)
        frame.pack(fill="x")

        tk.Label(frame, text="Contraseña:", font=("Segoe UI", 9),
                 bg=c["bg"], fg=c["fg"]).pack(anchor="w")
        self.entry = tk.Entry(frame, show="●", width=32, font=("Segoe UI", 11),
                              bg=c["entry_bg"], fg=c["entry_fg"],
                              insertbackground=c["fg"], relief="flat",
                              highlightthickness=1,
                              highlightbackground=c["separador"])
        self.entry.pack(pady=6, ipady=5, fill="x")

        self.lbl_error = tk.Label(frame, text="", fg="#e74c3c",
                                  bg=c["bg"], font=("Segoe UI", 9))
        self.lbl_error.pack()

        tk.Button(self, text="Entrar", command=self._verificar,
                  bg=c["cabecera_bg"], fg="white", font=("Segoe UI", 11),
                  relief="flat", padx=30, pady=10, width=18,
                  activebackground=c["btn_cambiar"],
                  activeforeground="white").pack(pady=12)

        self.entry.focus()
        self.bind("<Return>", lambda e: self._verificar())

    def _cancelar(self):
        self.destroy()
        if self.cerrar_app:
            self.master.destroy()
        else:
            self.callback(False)

    def _verificar(self):
        if hash_txt(self.entry.get()) == self.hash_guardado:
            self.destroy()
            self.callback(True)
        else:
            self.intentos += 1
            self.entry.delete(0, "end")
            restantes = MAX_INTENTOS - self.intentos
            if restantes > 0:
                self.lbl_error.config(
                    text=f"Contraseña incorrecta. Intentos restantes: {restantes}")
            else:
                messagebox.showerror("Acceso denegado", "Demasiados intentos. Cerrando.")
                if self.cerrar_app:
                    self.master.destroy()
                else:
                    self.destroy()
                    self.callback(False)

    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")