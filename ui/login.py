import tkinter as tk
from tkinter import messagebox
from config import hash_txt, cargar_config, guardar_config, MAX_INTENTOS


class VentanaContrasena(tk.Toplevel):
    """Crear o cambiar contraseña maestra."""

    def __init__(self, parent, callback, titulo="Crear contraseña"):
        super().__init__(parent)
        self.callback = callback
        self.title(titulo)
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._centrar(360, 230)
        self.protocol("WM_DELETE_WINDOW", lambda: self.callback(False))

        tk.Label(self, text=f"🔐 {titulo}",
                 font=("Segoe UI", 11, "bold")).pack(pady=(18, 4))
        tk.Label(self, text="Esta contraseña protege el acceso al panel.",
                 font=("Segoe UI", 9), fg="gray").pack()

        frame = tk.Frame(self, padx=24, pady=10)
        frame.pack(fill="x")
        tk.Label(frame, text="Nueva contraseña:", font=("Segoe UI", 9),
                 anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        self.e1 = tk.Entry(frame, show="●", width=26, font=("Segoe UI", 10))
        self.e1.grid(row=0, column=1, padx=8)
        tk.Label(frame, text="Confirmar:", font=("Segoe UI", 9),
                 anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        self.e2 = tk.Entry(frame, show="●", width=26, font=("Segoe UI", 10))
        self.e2.grid(row=1, column=1, padx=8)

        tk.Button(self, text="Guardar", command=self._guardar,
                  bg="#0078D4", fg="white", font=("Segoe UI", 11),
                  relief="flat", padx=40, pady=8, width=16).pack(pady=10)
        self.e1.focus()
        self.bind("<Return>", lambda e: self._guardar())

    def _guardar(self):
        p1, p2 = self.e1.get(), self.e2.get()
        if not p1:
            messagebox.showwarning("Aviso", "La contraseña no puede estar vacía.", parent=self)
            return
        if p1 != p2:
            messagebox.showerror("Error", "Las contraseñas no coinciden.", parent=self)
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
        self.callback = callback
        self.cerrar_app = cerrar_app
        self.intentos = 0
        self.title("Control de Aplicaciones — Acceso")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._centrar(360, 240)
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

        tk.Label(self, text="🔒 Control de Aplicaciones",
                 font=("Segoe UI", 13, "bold")).pack(pady=(20, 2))
        tk.Label(self, text="Ingresa tu contraseña maestra.",
                 font=("Segoe UI", 9), fg="gray").pack()

        frame = tk.Frame(self, padx=24, pady=12)
        frame.pack(fill="x")
        tk.Label(frame, text="Contraseña:", font=("Segoe UI", 9)).pack(anchor="w")
        self.entry = tk.Entry(frame, show="●", width=30, font=("Segoe UI", 11))
        self.entry.pack(pady=4, ipady=4)
        self.lbl_error = tk.Label(frame, text="", fg="#c0392b", font=("Segoe UI", 9))
        self.lbl_error.pack()

        tk.Button(self, text="Entrar", command=self._verificar,
                  bg="#0078D4", fg="white", font=("Segoe UI", 11),
                  relief="flat", padx=40, pady=8, width=16).pack(pady=10)
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
                self.lbl_error.config(text=f"Contraseña incorrecta. Intentos: {restantes}")
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