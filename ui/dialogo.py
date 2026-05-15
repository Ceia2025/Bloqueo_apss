import tkinter as tk
from tkinter import messagebox
import datetime
from config import hash_txt, MAX_INTENTOS
from ui import tema as T

DESBLOQUEO_LIBRE = -1


class DialogoDesbloqueo(tk.Toplevel):
    def __init__(self, parent, app_nombre: str, hash_guardado: str, callback):
        super().__init__(parent)
        self.hash_guardado = hash_guardado
        self.callback      = callback
        self.intentos      = 0
        c = T.colores()

        self.title("Acceso restringido")
        self.resizable(False, False)
        self.configure(bg=c["bg"])
        self.grab_set()
        self.lift()
        self.focus_force()
        self._centrar(420, 340)
        self.protocol("WM_DELETE_WINDOW", lambda: self._responder(0))

        # Cabecera
        cab = tk.Frame(self, bg="#c0392b", pady=14)
        cab.pack(fill="x")
        tk.Label(cab, text="🚫 Aplicación bloqueada",
                 font=("Segoe UI", 12, "bold"),
                 bg="#c0392b", fg="white").pack()
        tk.Label(cab, text=app_nombre,
                 font=("Segoe UI", 10),
                 bg="#c0392b", fg="white").pack(pady=(2, 0))

        frame = tk.Frame(self, bg=c["bg"], padx=24, pady=8)
        frame.pack(fill="x")

        tk.Label(frame, text="Ingresa la contraseña maestra para desbloquear.",
                 font=("Segoe UI", 9), fg=c["fg_gris"],
                 bg=c["bg"], wraplength=360).pack(pady=(0, 8))

        # Contraseña
        tk.Label(frame, text="Contraseña:", font=("Segoe UI", 9),
                 bg=c["bg"], fg=c["fg"]).pack(anchor="w")
        self.entry = tk.Entry(frame, show="●", width=36, font=("Segoe UI", 11),
                              bg=c["entry_bg"], fg=c["entry_fg"],
                              insertbackground=c["fg"], relief="flat",
                              highlightthickness=1,
                              highlightbackground=c["separador"])
        self.entry.pack(pady=4, ipady=4, fill="x")

        tk.Frame(frame, height=1, bg=c["separador"]).pack(fill="x", pady=(8, 6))

        # Modo
        self.modo = tk.StringVar(value="minutos")

        fila1 = tk.Frame(frame, bg=c["bg"])
        fila1.pack(fill="x", pady=2)
        tk.Radiobutton(fila1, text="Por tiempo:", variable=self.modo,
                       value="minutos", font=("Segoe UI", 9),
                       bg=c["bg"], fg=c["fg"], selectcolor=c["bg2"],
                       activebackground=c["bg"], activeforeground=c["fg"],
                       command=self._actualizar_modo).pack(side="left")
        self.minutos_var  = tk.IntVar(value=30)
        self.frame_mins   = tk.Frame(fila1, bg=c["bg"])
        self.frame_mins.pack(side="left", padx=4)
        for mins in [15, 30, 60, 120]:
            tk.Radiobutton(self.frame_mins, text=f"{mins} min",
                           variable=self.minutos_var, value=mins,
                           font=("Segoe UI", 9), width=6,
                           bg=c["bg"], fg=c["fg"], selectcolor=c["bg2"],
                           activebackground=c["bg"],
                           activeforeground=c["fg"]).pack(side="left")

        fila2 = tk.Frame(frame, bg=c["bg"])
        fila2.pack(fill="x", pady=2)
        tk.Radiobutton(fila2, text="Hasta las: ", variable=self.modo,
                       value="hora", font=("Segoe UI", 9),
                       bg=c["bg"], fg=c["fg"], selectcolor=c["bg2"],
                       activebackground=c["bg"], activeforeground=c["fg"],
                       command=self._actualizar_modo).pack(side="left")
        self.frame_hora = tk.Frame(fila2, bg=c["bg"])
        self.frame_hora.pack(side="left", padx=4)
        ahora = datetime.datetime.now()
        self.hora_var = tk.StringVar(value=f"{ahora.hour:02d}")
        self.min_var  = tk.StringVar(value=f"{ahora.minute:02d}")
        self.spin_hora = tk.Spinbox(self.frame_hora, from_=0, to=23, width=3,
                                    textvariable=self.hora_var, format="%02.0f",
                                    font=("Segoe UI", 10), state="disabled",
                                    bg=c["entry_bg"], fg=c["entry_fg"],
                                    buttonbackground=c["bg2"])
        self.spin_hora.pack(side="left")
        tk.Label(self.frame_hora, text=":", font=("Segoe UI", 10),
                 bg=c["bg"], fg=c["fg"]).pack(side="left")
        self.spin_min = tk.Spinbox(self.frame_hora, from_=0, to=59, width=3,
                                   textvariable=self.min_var, format="%02.0f",
                                   font=("Segoe UI", 10), state="disabled",
                                   bg=c["entry_bg"], fg=c["entry_fg"],
                                   buttonbackground=c["bg2"])
        self.spin_min.pack(side="left")
        tk.Label(self.frame_hora, text="(hoy)", font=("Segoe UI", 8),
                 fg=c["fg_gris"], bg=c["bg"]).pack(side="left", padx=4)

        self.lbl_error = tk.Label(frame, text="", fg="#e74c3c",
                                  bg=c["bg"], font=("Segoe UI", 9))
        self.lbl_error.pack(pady=(4, 0))

        btn_frame = tk.Frame(self, bg=c["bg"])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Desbloquear", command=self._verificar,
                  bg="#27ae60", fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=16, pady=6).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancelar",
                  command=lambda: self._responder(0),
                  bg=c["bg2"], fg=c["fg"], font=("Segoe UI", 10),
                  relief="flat", padx=16, pady=6).pack(side="left", padx=6)

        self.entry.focus()
        self.bind("<Return>", lambda e: self._verificar())

    def _actualizar_modo(self):
        estado_mins = "normal" if self.modo.get() == "minutos" else "disabled"
        estado_hora = "disabled" if self.modo.get() == "minutos" else "normal"
        for w in self.frame_mins.winfo_children():
            w.config(state=estado_mins)
        self.spin_hora.config(state=estado_hora)
        self.spin_min.config(state=estado_hora)

    def _calcular_segundos(self) -> int:
        if self.modo.get() == "minutos":
            return self.minutos_var.get() * 60
        try:
            h = int(self.hora_var.get())
            m = int(self.min_var.get())
        except ValueError:
            return 0
        ahora    = datetime.datetime.now()
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
    def __init__(self, parent, app_nombre: str, hash_guardado: str, callback):
        super().__init__(parent)
        self.hash_guardado = hash_guardado
        self.callback      = callback
        self.intentos      = 0
        c = T.colores()

        self.title("Desbloqueo libre")
        self.resizable(False, False)
        self.configure(bg=c["bg"])
        self.grab_set()
        self.lift()
        self.focus_force()
        self._centrar(380, 260)
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

        # Cabecera
        cab = tk.Frame(self, bg="#8e44ad", pady=14)
        cab.pack(fill="x")
        tk.Label(cab, text="♾ Desbloqueo libre",
                 font=("Segoe UI", 12, "bold"),
                 bg="#8e44ad", fg="white").pack()
        tk.Label(cab, text=app_nombre,
                 font=("Segoe UI", 10),
                 bg="#8e44ad", fg="white").pack(pady=(2, 0))

        frame = tk.Frame(self, bg=c["bg"], padx=30, pady=12)
        frame.pack(fill="x")

        tk.Label(frame,
                 text="La app quedará desbloqueada hasta que la bloquees manualmente.",
                 font=("Segoe UI", 9), fg=c["fg_gris"],
                 bg=c["bg"], wraplength=320).pack(pady=(0, 10))

        tk.Label(frame, text="Contraseña maestra:", font=("Segoe UI", 9),
                 bg=c["bg"], fg=c["fg"]).pack(anchor="w")
        self.entry = tk.Entry(frame, show="●", width=32, font=("Segoe UI", 11),
                              bg=c["entry_bg"], fg=c["entry_fg"],
                              insertbackground=c["fg"], relief="flat",
                              highlightthickness=1,
                              highlightbackground=c["separador"])
        self.entry.pack(pady=6, ipady=4, fill="x")

        self.lbl_error = tk.Label(frame, text="", fg="#e74c3c",
                                  bg=c["bg"], font=("Segoe UI", 9))
        self.lbl_error.pack()

        btn_frame = tk.Frame(self, bg=c["bg"])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Desbloquear sin límite",
                  command=self._verificar,
                  bg="#8e44ad", fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=14, pady=6).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancelar",
                  command=self._cancelar,
                  bg=c["bg2"], fg=c["fg"], font=("Segoe UI", 10),
                  relief="flat", padx=14, pady=6).pack(side="left", padx=5)

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