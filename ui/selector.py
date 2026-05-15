import tkinter as tk
from tkinter import messagebox, ttk
import threading
import psutil
import os

from ui.iconos import lazy_load_iconos
from ui import tema as T


def obtener_apps_instaladas() -> list:
    rutas = [
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
    ]
    apps = {}
    for ruta in rutas:
        if not ruta or not os.path.exists(ruta):
            continue
        for raiz, dirs, archivos in os.walk(ruta):
            nivel = raiz.replace(ruta, "").count(os.sep)
            if nivel > 3:
                dirs.clear()
                continue
            for archivo in archivos:
                if archivo.lower().endswith(".exe"):
                    exe = archivo.lower()
                    if exe not in apps:
                        apps[exe] = {
                            "nombre": archivo,
                            "exe": exe,
                            "ruta": os.path.join(raiz, archivo),
                        }
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            nombre = proc.info["name"]
            exe    = nombre.lower()
            ruta   = proc.info.get("exe") or ""
            if exe.endswith(".exe") and exe not in apps:
                apps[exe] = {"nombre": nombre, "exe": exe, "ruta": ruta}
        except Exception:
            pass
    return sorted(apps.values(), key=lambda x: x["nombre"].lower())


class VentanaSelectorApps(tk.Toplevel):
    def __init__(self, parent, bloqueadas_actuales: list, callback):
        super().__init__(parent)
        self.callback   = callback
        self.todas_apps = []
        self.bloqueadas = [b["exe"] if isinstance(b, dict) else b
                           for b in bloqueadas_actuales]
        self.iconos     = {}
        c = T.colores()

        self.title("Agregar aplicación restringida")
        self.resizable(True, True)
        self.configure(bg=c["bg"])
        self.grab_set()
        self._centrar(560, 540)
        self._construir_ui()
        threading.Thread(target=self._cargar_apps, daemon=True).start()

    def _construir_ui(self):
        c = T.colores()

        # Cabecera
        cab = tk.Frame(self, bg=c["cabecera_bg"], pady=14)
        cab.pack(fill="x")
        tk.Label(cab, text="Selecciona una aplicación para restringir",
                 font=("Segoe UI", 12, "bold"),
                 bg=c["cabecera_bg"], fg=c["cabecera_fg"]).pack()
        self.lbl_estado = tk.Label(cab,
                 text="Buscando apps instaladas...",
                 font=("Segoe UI", 9),
                 bg=c["cabecera_bg"], fg=c["cabecera_fg"])
        self.lbl_estado.pack(pady=(2, 0))

        # Búsqueda
        frame_busq = tk.Frame(self, bg=c["bg"], padx=12, pady=8)
        frame_busq.pack(fill="x")
        tk.Label(frame_busq, text="🔍 Buscar:", font=("Segoe UI", 9),
                 bg=c["bg"], fg=c["fg"]).pack(side="left")
        self.var_busq   = tk.StringVar()
        self.entry_busq = tk.Entry(frame_busq, textvariable=self.var_busq,
                                   font=("Segoe UI", 10), width=34,
                                   bg=c["entry_bg"], fg=c["entry_fg"],
                                   insertbackground=c["fg"], relief="flat",
                                   highlightthickness=1,
                                   highlightbackground=c["separador"])
        self.entry_busq.pack(side="left", padx=8, ipady=4)
        self.entry_busq.focus()
        self.entry_busq.bind("<KeyRelease>", self._filtrar)

        # Tabla
        T.aplicar_ttk_style()
        frame_tabla = tk.Frame(self, bg=c["bg"], padx=12)
        frame_tabla.pack(fill="both", expand=True)

        self.tabla = ttk.Treeview(frame_tabla, columns=("nombre",),
                                  show="tree headings", height=16,
                                  selectmode="browse")
        self.tabla.heading("#0",     text="")
        self.tabla.heading("nombre", text="Aplicación")
        self.tabla.column("#0",      width=28, stretch=False, anchor="center")
        self.tabla.column("nombre",  width=480)
        self.tabla.tag_configure("bloqueada", foreground=T.colores()["row_bloqueado"])
        self.tabla.tag_configure("normal",    foreground=T.colores()["tabla_fg"])

        scroll = ttk.Scrollbar(frame_tabla, orient="vertical",
                               command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tabla.bind("<Double-Button-1>", lambda e: self._agregar())

        # Entrada manual
        frame_manual = tk.Frame(self, bg=c["bg"], padx=12, pady=6)
        frame_manual.pack(fill="x")
        tk.Label(frame_manual, text="O escribe el nombre del .exe:",
                 font=("Segoe UI", 9), fg=c["fg_gris"],
                 bg=c["bg"]).pack(side="left")
        self.var_manual = tk.StringVar()
        tk.Entry(frame_manual, textvariable=self.var_manual,
                 font=("Segoe UI", 10), width=22,
                 bg=c["entry_bg"], fg=c["entry_fg"],
                 insertbackground=c["fg"], relief="flat",
                 highlightthickness=1,
                 highlightbackground=c["separador"]).pack(
                     side="left", padx=8, ipady=3)

        # Botones
        btn_frame = tk.Frame(self, bg=c["bg"], pady=10)
        btn_frame.pack()
        tk.Button(btn_frame, text="✅ Agregar seleccionada",
                  command=self._agregar,
                  bg=c["cabecera_bg"], fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=14, pady=6).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancelar", command=self.destroy,
                  bg=c["bg2"], fg=c["fg"], font=("Segoe UI", 10),
                  relief="flat", padx=14, pady=6).pack(side="left", padx=6)

    def _cargar_apps(self):
        apps = obtener_apps_instaladas()
        self.todas_apps = apps
        self.after(0, self._poblar_tabla, apps)
        lazy_load_iconos(apps, size=16,
                         callback_ui=lambda exe, foto: self.after(
                             0, self._aplicar_icono, exe, foto))

    def _poblar_tabla(self, apps):
        for row in self.tabla.get_children():
            self.tabla.delete(row)

        total     = len(self.todas_apps)
        mostrados = len(apps)
        if mostrados < total:
            self.lbl_estado.config(
                text=f"{total} apps — mostrando {mostrados}. Escribe para filtrar.")
        else:
            self.lbl_estado.config(text=f"{total} aplicaciones encontradas.")

        for app in apps:
            exe       = app["exe"]
            bloqueada = exe in self.bloqueadas
            tag       = "bloqueada" if bloqueada else "normal"
            nombre_display = ("🔒 " if bloqueada else "") + app["nombre"]
            self.tabla.insert("", "end", iid=exe,
                              values=(nombre_display,), tags=(tag,))

    def _aplicar_icono(self, exe: str, foto):
        if not self.winfo_exists():
            return
        if self.tabla.exists(exe):
            self.iconos[exe] = foto
            self.tabla.item(exe, image=foto)

    def _filtrar(self, event=None):
        filtro = self.var_busq.get().lower().strip()
        if not filtro:
            self._poblar_tabla(self.todas_apps)
        else:
            resultados = [a for a in self.todas_apps
                          if filtro in a["nombre"].lower()]
            self._poblar_tabla(resultados)
        for exe, foto in self.iconos.items():
            if self.tabla.exists(exe):
                self.tabla.item(exe, image=foto)

    def _agregar(self):
        manual = self.var_manual.get().strip()
        if manual:
            if not manual.lower().endswith(".exe"):
                manual += ".exe"
            self.callback({"exe": manual.lower(), "ruta": ""})
            self.destroy()
            return
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Aviso",
                "Selecciona una app o escribe el nombre.", parent=self)
            return
        exe  = sel[0]
        ruta = next((a["ruta"] for a in self.todas_apps if a["exe"] == exe), "")
        self.callback({"exe": exe, "ruta": ruta})
        self.destroy()

    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")