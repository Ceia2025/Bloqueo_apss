import tkinter as tk
from tkinter import messagebox
import datetime
from config import hash_txt, MAX_INTENTOS

# Valor especial que indica desbloqueo indefinido
DESBLOQUEO_LIBRE = -1


class DialogoDesbloqueo(tk.Toplevel):
    """
    Diálogo de desbloqueo temporal.
    Modos:
      - Por tiempo (15 / 30 / 60 / 120 min)
      - Hasta hora específica (HH:MM)
    Retorna segundos al callback, o DESBLOQUEO_LIBRE (-1) si es libre.
    """

    def __init__(self, parent, app_nombre: str, hash_guardado: str, callback):
        super().__init__(parent)
        self.hash_guardado = hash_guardado
        self.callback      = callback
        self.intentos      = 0
        self.title("Acceso restringido")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._centrar(420, 330)
        self.protocol("WM_DELETE_WINDOW", lambda: self._responder(0))

        tk.Label(self, text="🚫 Aplicación bloqueada",
                 font=("Segoe UI", 12, "bold"), fg="#c0392b").pack(pady=(16, 2))
        tk.Label(self, text=app_nombre,
                 font=("Segoe UI", 10), fg="#555").pack()
        tk.Label(self,
                 text="Ingresa la contraseña maestra para desbloquear.",
                 font=("Segoe UI", 9), fg="gray", wraplength=380).pack(pady=(4, 0))

        frame = tk.Frame(self, padx=24, pady=6)
        frame.pack(fill="x")

        # ── Contraseña
        tk.Label(frame, text="Contraseña:", font=("Segoe UI", 9)).pack(anchor="w")
        self.entry = tk.Entry(frame, show="●", width=34, font=("Segoe UI", 11))
        self.entry.pack(pady=4, ipady=3)

        tk.Frame(frame, height=1, bg="#ddd").pack(fill="x", pady=(4, 6))

        # ── Modo
        self.modo = tk.StringVar(value="minutos")

        # Fila 1: por minutos — opciones más anchas para que quepan
        fila1 = tk.Frame(frame)
        fila1.pack(fill="x", pady=2)
        tk.Radiobutton(fila1, text="Por tiempo:", variable=self.modo,
                       value="minutos", font=("Segoe UI", 9),
                       command=self._actualizar_modo).pack(side="left")
        self.minutos_var  = tk.IntVar(value=30)
        self.frame_mins   = tk.Frame(fila1)
        self.frame_mins.pack(side="left", padx=4)
        for mins in [15, 30, 60, 120]:
            tk.Radiobutton(self.frame_mins, text=f"{mins} min",
                           variable=self.minutos_var, value=mins,
                           font=("Segoe UI", 9), width=6).pack(side="left")

        # Fila 2: hasta hora
        fila2 = tk.Frame(frame)
        fila2.pack(fill="x", pady=2)
        tk.Radiobutton(fila2, text="Hasta las: ", variable=self.modo,
                       value="hora", font=("Segoe UI", 9),
                       command=self._actualizar_modo).pack(side="left")
        self.frame_hora = tk.Frame(fila2)
        self.frame_hora.pack(side="left", padx=4)
        ahora = datetime.datetime.now()
        self.hora_var = tk.StringVar(value=f"{ahora.hour:02d}")
        self.min_var  = tk.StringVar(value=f"{ahora.minute:02d}")
        self.spin_hora = tk.Spinbox(self.frame_hora, from_=0, to=23, width=3,
                                    textvariable=self.hora_var, format="%02.0f",
                                    font=("Segoe UI", 10), state="disabled")
        self.spin_hora.pack(side="left")
        tk.Label(self.frame_hora, text=":", font=("Segoe UI", 10)).pack(side="left")
        self.spin_min = tk.Spinbox(self.frame_hora, from_=0, to=59, width=3,
                                   textvariable=self.min_var, format="%02.0f",
                                   font=("Segoe UI", 10), state="disabled")
        self.spin_min.pack(side="left")
        tk.Label(self.frame_hora, text="(hoy)", font=("Segoe UI", 8),
                 fg="gray").pack(side="left", padx=4)

        self.lbl_error = tk.Label(frame, text="", fg="#c0392b", font=("Segoe UI", 9))
        self.lbl_error.pack(pady=(4, 0))

        # ── Botones
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Desbloquear", command=self._verificar,
                  bg="#27ae60", fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=14, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancelar",
                  command=lambda: self._responder(0),
                  font=("Segoe UI", 10), relief="flat",
                  padx=14, pady=5).pack(side="left", padx=5)

        self.entry.focus()
        self.bind("<Return>", lambda e: self._verificar())

    def _actualizar_modo(self):
        if self.modo.get() == "minutos":
            for w in self.frame_mins.winfo_children():
                w.config(state="normal")
            self.spin_hora.config(state="disabled")
            self.spin_min.config(state="disabled")
        else:
            for w in self.frame_mins.winfo_children():
                w.config(state="disabled")
            self.spin_hora.config(state="normal")
            self.spin_min.config(state="normal")

    def _calcular_segundos(self) -> int:
        if self.modo.get() == "minutos":
            return self.minutos_var.get() * 60
        try:
            h = int(self.hora_var.get())
            m = int(self.min_var.get())
        except ValueError:
            return 0
        ahora   = datetime.datetime.now()
        objetivo = ahora.replace(hour=h, minute=m, second=0, microsecond=0)
        if objetivo <= ahora:
            objetivo += datetime.timedelta(days=1)
        return int((objetivo - ahora).total_seconds())

    def _verificar(self):
        if hash_txt(self.entry.get()) == self.hash_guardado:
            segundos = self._calcular_segundos()
            if segundos <= 0:
                self.lbl_error.config(
                    text="La hora límite ya pasó, elige una hora futura.")
                return
            self._responder(segundos)
        else:
            self.intentos += 1
            self.entry.delete(0, "end")
            if self.intentos >= MAX_INTENTOS:
                self._responder(0)
            else:
                self.lbl_error.config(
                    text=f"Contraseña incorrecta. Intentos: {MAX_INTENTOS - self.intentos}")

    def _responder(self, segundos: int):
        self.destroy()
        self.callback(segundos)

    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")


class DialogoDesbloqueoLibre(tk.Toplevel):
    """
    Desbloqueo sin límite de tiempo. Solo pide contraseña.
    Retorna True al callback si la contraseña es correcta.
    """

    def __init__(self, parent, app_nombre: str, hash_guardado: str, callback):
        super().__init__(parent)
        self.hash_guardado = hash_guardado
        self.callback      = callback
        self.intentos      = 0
        self.title("Desbloqueo libre")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._centrar(360, 220)
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

        tk.Label(self, text="🔓 Desbloqueo libre",
                 font=("Segoe UI", 12, "bold"), fg="#e67e22").pack(pady=(16, 2))
        tk.Label(self, text=app_nombre,
                 font=("Segoe UI", 10), fg="#555").pack()
        tk.Label(self,
                 text="La app quedará desbloqueada hasta que la bloquees manualmente.",
                 font=("Segoe UI", 9), fg="gray", wraplength=320).pack(pady=(4, 0))

        frame = tk.Frame(self, padx=24, pady=10)
        frame.pack(fill="x")
        tk.Label(frame, text="Contraseña maestra:", font=("Segoe UI", 9)).pack(anchor="w")
        self.entry = tk.Entry(frame, show="●", width=32, font=("Segoe UI", 11))
        self.entry.pack(pady=4, ipady=3)
        self.lbl_error = tk.Label(frame, text="", fg="#c0392b", font=("Segoe UI", 9))
        self.lbl_error.pack()

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Desbloquear sin límite",
                  command=self._verificar,
                  bg="#e67e22", fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=14, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancelar",
                  command=self._cancelar,
                  font=("Segoe UI", 10), relief="flat",
                  padx=14, pady=5).pack(side="left", padx=5)

        self.entry.focus()
        self.bind("<Return>", lambda e: self._verificar())

    def _cancelar(self):
        self.destroy()
        self.callback(False)

    def _verificar(self):
        if hash_txt(self.entry.get()) == self.hash_guardado:
            self.destroy()
            self.callback(True)
        else:
            self.intentos += 1
            self.entry.delete(0, "end")
            if self.intentos >= MAX_INTENTOS:
                self.destroy()
                self.callback(False)
            else:
                self.lbl_error.config(
                    text=f"Contraseña incorrecta. Intentos: {MAX_INTENTOS - self.intentos}")

    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")