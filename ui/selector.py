import tkinter as tk
from tkinter import messagebox, ttk
import threading
import psutil
import os

from ui.iconos import obtener_icono_exe


def obtener_apps_instaladas() -> list:
    """
    Busca ejecutables en rutas estándar de Windows.
    Retorna lista de dicts con 'nombre', 'exe' y 'ruta'.
    """
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

    # También incluir procesos activos con su ruta real
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            nombre = proc.info["name"]
            exe = nombre.lower()
            ruta = proc.info.get("exe") or ""
            if exe.endswith(".exe") and exe not in apps:
                apps[exe] = {"nombre": nombre, "exe": exe, "ruta": ruta}
        except Exception:
            pass

    return sorted(apps.values(), key=lambda x: x["nombre"].lower())


class VentanaSelectorApps(tk.Toplevel):
    def __init__(self, parent, bloqueadas_actuales: list, callback):
        super().__init__(parent)
        self.callback = callback
        self.todas_apps = []
        self.bloqueadas = [b.lower() for b in bloqueadas_actuales]
        self.iconos = {}   # exe -> PhotoImage (para que no sea basura por GC)
        self.title("Agregar aplicación restringida")
        self.resizable(True, True)
        self.grab_set()
        self._centrar(560, 520)
        self._construir_ui()
        threading.Thread(target=self._cargar_apps, daemon=True).start()

    def _construir_ui(self):
        tk.Label(self, text="Selecciona una aplicación para restringir",
                 font=("Segoe UI", 11, "bold")).pack(pady=(14, 2))
        self.lbl_estado = tk.Label(self,
                 text="Buscando apps instaladas y procesos activos...",
                 font=("Segoe UI", 9), fg="gray")
        self.lbl_estado.pack()

        # Búsqueda
        frame_busq = tk.Frame(self, padx=12, pady=6)
        frame_busq.pack(fill="x")
        tk.Label(frame_busq, text="🔍 Buscar:", font=("Segoe UI", 9)).pack(side="left")
        self.var_busq = tk.StringVar()
        self.var_busq.trace("w", self._filtrar)
        tk.Entry(frame_busq, textvariable=self.var_busq,
                 font=("Segoe UI", 10), width=32).pack(side="left", padx=6, ipady=3)

        # Tabla con ícono + nombre
        frame_tabla = tk.Frame(self, padx=12)
        frame_tabla.pack(fill="both", expand=True)

        cols = ("icono", "nombre")
        self.tabla = ttk.Treeview(frame_tabla, columns=cols,
                                  show="tree headings", height=16,
                                  selectmode="browse")
        self.tabla.heading("icono", text="")
        self.tabla.heading("nombre", text="Aplicación")
        self.tabla.column("#0", width=0, stretch=False)   # ocultar col árbol
        self.tabla.column("icono", width=30, anchor="center", stretch=False)
        self.tabla.column("nombre", width=460)

        self.tabla.tag_configure("bloqueada", foreground="#c0392b")
        self.tabla.tag_configure("normal", foreground="")

        scroll = ttk.Scrollbar(frame_tabla, orient="vertical",
                               command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tabla.bind("<Double-Button-1>", lambda e: self._agregar())

        # Entrada manual
        frame_manual = tk.Frame(self, padx=12, pady=6)
        frame_manual.pack(fill="x")
        tk.Label(frame_manual, text="O escribe el nombre del .exe:",
                 font=("Segoe UI", 9), fg="gray").pack(side="left")
        self.var_manual = tk.StringVar()
        tk.Entry(frame_manual, textvariable=self.var_manual,
                 font=("Segoe UI", 10), width=22).pack(side="left", padx=6, ipady=2)

        btn_frame = tk.Frame(self, pady=8)
        btn_frame.pack()
        tk.Button(btn_frame, text="✅ Agregar seleccionada", command=self._agregar,
                  bg="#0078D4", fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=14, pady=5).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancelar", command=self.destroy,
                  font=("Segoe UI", 10), relief="flat",
                  padx=14, pady=5).pack(side="left", padx=6)

    # ── Carga de datos ────────────────────────

    def _cargar_apps(self):
        apps = obtener_apps_instaladas()
        self.todas_apps = apps
        self.after(0, self._poblar_tabla, apps)

    def _poblar_tabla(self, apps):
        # Limpiar tabla
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        self.iconos.clear()

        self.lbl_estado.config(text=f"{len(apps)} aplicaciones encontradas.")

        for app in apps:
            exe = app["exe"]
            ruta = app.get("ruta", "")
            bloqueada = exe in self.bloqueadas
            tag = "bloqueada" if bloqueada else "normal"
            nombre_display = ("🔒 " if bloqueada else "") + app["nombre"]

            # Extraer ícono en segundo plano para no bloquear UI
            icono = obtener_icono_exe(ruta, size=18) if ruta else None
            if icono:
                self.iconos[exe] = icono  # mantener referencia
                self.tabla.insert("", "end", iid=exe,
                                  image=icono,
                                  values=("", nombre_display),
                                  tags=(tag,))
            else:
                self.tabla.insert("", "end", iid=exe,
                                  values=("🔷", nombre_display),
                                  tags=(tag,))

    def _filtrar(self, *args):
        filtro = self.var_busq.get().lower()
        self._poblar_tabla([a for a in self.todas_apps
                            if filtro in a["nombre"].lower()])

    # ── Agregar ───────────────────────────────

    def _agregar(self):
        manual = self.var_manual.get().strip()
        if manual:
            if not manual.lower().endswith(".exe"):
                manual += ".exe"
            self.callback(manual.lower())
            self.destroy()
            return

        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Aviso",
                "Selecciona una app de la lista o escribe el nombre.", parent=self)
            return

        exe = sel[0]  # el iid es el nombre del exe
        self.callback(exe)
        self.destroy()

    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")