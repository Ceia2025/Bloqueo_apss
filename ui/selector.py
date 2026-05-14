import tkinter as tk
from tkinter import messagebox
import threading
import psutil
import os


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
                        apps[exe] = {"nombre": archivo, "exe": exe}
    for proc in psutil.process_iter(["name"]):
        try:
            nombre = proc.info["name"]
            exe = nombre.lower()
            if exe.endswith(".exe") and exe not in apps:
                apps[exe] = {"nombre": nombre, "exe": exe}
        except Exception:
            pass
    return sorted(apps.values(), key=lambda x: x["nombre"].lower())


class VentanaSelectorApps(tk.Toplevel):
    def __init__(self, parent, bloqueadas_actuales: list, callback):
        super().__init__(parent)
        self.callback = callback
        self.todas_apps = []
        self.bloqueadas = [b.lower() for b in bloqueadas_actuales]
        self.title("Agregar aplicación restringida")
        self.resizable(True, True)
        self.grab_set()
        self._centrar(520, 500)
        self._construir_ui()
        threading.Thread(target=self._cargar_apps, daemon=True).start()

    def _construir_ui(self):
        tk.Label(self, text="Selecciona una aplicación para restringir",
                 font=("Segoe UI", 11, "bold")).pack(pady=(14, 2))
        tk.Label(self, text="Buscando apps instaladas y procesos activos...",
                 font=("Segoe UI", 9), fg="gray").pack()

        frame_busq = tk.Frame(self, padx=12, pady=6)
        frame_busq.pack(fill="x")
        tk.Label(frame_busq, text="🔍 Buscar:", font=("Segoe UI", 9)).pack(side="left")
        self.var_busq = tk.StringVar()
        self.var_busq.trace("w", self._filtrar)
        tk.Entry(frame_busq, textvariable=self.var_busq,
                 font=("Segoe UI", 10), width=30).pack(side="left", padx=6, ipady=3)

        frame_lista = tk.Frame(self, padx=12)
        frame_lista.pack(fill="both", expand=True)
        scroll = tk.Scrollbar(frame_lista)
        scroll.pack(side="right", fill="y")
        self.listbox = tk.Listbox(frame_lista, font=("Segoe UI", 10),
                                  yscrollcommand=scroll.set, selectmode="single")
        self.listbox.pack(fill="both", expand=True)
        scroll.config(command=self.listbox.yview)
        self.listbox.bind("<Double-Button-1>", lambda e: self._agregar())

        frame_manual = tk.Frame(self, padx=12, pady=6)
        frame_manual.pack(fill="x")
        tk.Label(frame_manual, text="O escribe el nombre del .exe:",
                 font=("Segoe UI", 9), fg="gray").pack(side="left")
        self.var_manual = tk.StringVar()
        tk.Entry(frame_manual, textvariable=self.var_manual,
                 font=("Segoe UI", 10), width=20).pack(side="left", padx=6, ipady=2)

        btn_frame = tk.Frame(self, pady=8)
        btn_frame.pack()
        tk.Button(btn_frame, text="✅ Agregar seleccionada", command=self._agregar,
                  bg="#0078D4", fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=14, pady=5).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancelar", command=self.destroy,
                  font=("Segoe UI", 10), relief="flat", padx=14, pady=5).pack(side="left", padx=6)

    def _cargar_apps(self):
        apps = obtener_apps_instaladas()
        self.todas_apps = apps
        self.after(0, self._poblar_lista, apps)

    def _poblar_lista(self, apps):
        self.listbox.delete(0, "end")
        for app in apps:
            marca = "🔒 " if app["exe"] in self.bloqueadas else "   "
            self.listbox.insert("end", f"{marca}{app['nombre']}")

    def _filtrar(self, *args):
        filtro = self.var_busq.get().lower()
        self._poblar_lista([a for a in self.todas_apps if filtro in a["nombre"].lower()])

    def _agregar(self):
        manual = self.var_manual.get().strip()
        if manual:
            if not manual.lower().endswith(".exe"):
                manual += ".exe"
            self.callback(manual.lower())
            self.destroy()
            return
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una app o escribe el nombre.", parent=self)
            return
        texto = self.listbox.get(sel[0]).strip().lstrip("🔒").strip()
        self.callback(texto.lower())
        self.destroy()

    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")