import tkinter as tk
from tkinter import messagebox
import time
import datetime
from config import hash_txt, MAX_INTENTOS


class DialogoDesbloqueo(tk.Toplevel):
    """
    Aparece cuando se detecta una app bloqueada.
    Pide contraseña y permite elegir:
      - Desbloquear por X minutos
      - Desbloquear hasta una hora específica (HH:MM)
    Retorna segundos de desbloqueo al callback.
    """

    def __init__(self, parent, app_nombre: str, hash_guardado: str, callback):
        super().__init__(parent)
        self.hash_guardado = hash_guardado
        self.callback = callback
        self.intentos = 0
        self.title("Acceso restringido")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._centrar(380, 340)
        self.protocol("WM_DELETE_WINDOW", lambda: self._responder(0))

        tk.Label(self, text="🚫 Aplicación bloqueada",
                 font=("Segoe UI", 12, "bold"), fg="#c0392b").pack(pady=(16, 2))
        tk.Label(self, text=app_nombre,
                 font=("Segoe UI", 10), fg="#555").pack()
        tk.Label(self,
                 text="Ingresa la contraseña maestra para desbloquear temporalmente.",
                 font=("Segoe UI", 9), fg="gray", wraplength=340).pack(pady=(4, 0))

        frame = tk.Frame(self, padx=24, pady=8)
        frame.pack(fill="x")

        # ── Contraseña
        tk.Label(frame, text="Contraseña:", font=("Segoe UI", 9)).pack(anchor="w")
        self.entry = tk.Entry(frame, show="●", width=32, font=("Segoe UI", 11))
        self.entry.pack(pady=4, ipady=3)

        # ── Modo de desbloqueo (minutos o hasta hora)
        self.modo = tk.StringVar(value="minutos")

        sep = tk.Frame(frame, height=1, bg="#ddd")
        sep.pack(fill="x", pady=(6, 8))

        # Opción 1: por minutos
        fila1 = tk.Frame(frame)
        fila1.pack(fill="x", pady=2)
        tk.Radiobutton(fila1, text="Por tiempo:", variable=self.modo,
                       value="minutos", font=("Segoe UI", 9),
                       command=self._actualizar_modo).pack(side="left")
        self.minutos_var = tk.IntVar(value=30)
        self.frame_mins = tk.Frame(fila1)
        self.frame_mins.pack(side="left", padx=6)
        for mins in [15, 30, 60, 120]:
            tk.Radiobutton(self.frame_mins, text=f"{mins} min",
                           variable=self.minutos_var, value=mins,
                           font=("Segoe UI", 9)).pack(side="left", padx=2)

        # Opción 2: hasta hora límite
        fila2 = tk.Frame(frame)
        fila2.pack(fill="x", pady=2)
        tk.Radiobutton(fila2, text="Hasta las:", variable=self.modo,
                       value="hora", font=("Segoe UI", 9),
                       command=self._actualizar_modo).pack(side="left")

        self.frame_hora = tk.Frame(fila2)
        self.frame_hora.pack(side="left", padx=6)

        ahora = datetime.datetime.now()
        self.hora_var = tk.StringVar(value=f"{ahora.hour:02d}")
        self.min_var = tk.StringVar(value=f"{ahora.minute:02d}")

        self.spin_hora = tk.Spinbox(self.frame_hora, from_=0, to=23, width=3,
                                    textvariable=self.hora_var,
                                    format="%02.0f", font=("Segoe UI", 10),
                                    state="disabled")
        self.spin_hora.pack(side="left")
        tk.Label(self.frame_hora, text=":", font=("Segoe UI", 10)).pack(side="left")
        self.spin_min = tk.Spinbox(self.frame_hora, from_=0, to=59, width=3,
                                   textvariable=self.min_var,
                                   format="%02.0f", font=("Segoe UI", 10),
                                   state="disabled")
        self.spin_min.pack(side="left")
        tk.Label(self.frame_hora, text="(hoy)",
                 font=("Segoe UI", 8), fg="gray").pack(side="left", padx=4)

        self.lbl_error = tk.Label(frame, text="", fg="#c0392b", font=("Segoe UI", 9))
        self.lbl_error.pack(pady=(6, 0))

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Desbloquear", command=self._verificar,
                  bg="#27ae60", fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=16, pady=5).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancelar",
                  command=lambda: self._responder(0),
                  font=("Segoe UI", 10), relief="flat",
                  padx=16, pady=5).pack(side="left", padx=6)

        self.entry.focus()
        self.bind("<Return>", lambda e: self._verificar())

    def _actualizar_modo(self):
        """Habilita/deshabilita controles según el modo seleccionado."""
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
        """Retorna cuántos segundos de desbloqueo corresponden a la selección."""
        if self.modo.get() == "minutos":
            return self.minutos_var.get() * 60
        else:
            # Hasta hora límite
            try:
                h = int(self.hora_var.get())
                m = int(self.min_var.get())
            except ValueError:
                return 0
            ahora = datetime.datetime.now()
            objetivo = ahora.replace(hour=h, minute=m, second=0, microsecond=0)
            if objetivo <= ahora:
                # Ya pasó esa hora hoy → sumar 24h (para mañana)
                objetivo += datetime.timedelta(days=1)
            return int((objetivo - ahora).total_seconds())

    def _verificar(self):
        if hash_txt(self.entry.get()) == self.hash_guardado:
            segundos = self._calcular_segundos()
            if segundos <= 0:
                self.lbl_error.config(text="La hora límite ya pasó, elige una hora futura.")
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