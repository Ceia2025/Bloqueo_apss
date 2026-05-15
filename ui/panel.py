import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading

from config import cargar_config, guardar_config, cargar_tema, guardar_tema
from monitor import Monitor
from ui.dialogo import DialogoDesbloqueo, DialogoDesbloqueoLibre
from ui.iconos import obtener_icono_exe
from ui.login import VentanaContrasena, VentanaLogin
from ui.selector import VentanaSelectorApps
from ui import tema as T

LIBRE = float("inf")


class PanelPrincipal(tk.Frame):
    def __init__(self, parent, hash_guardado: str):
        super().__init__(parent)
        self.hash_guardado   = hash_guardado
        self.pack(fill="both", expand=True)

        self.bloqueadas      = []
        self.desbloqueados   = {}
        self.dialogo_abierto = set()
        self.iconos          = {}

        # Cargar tema guardado
        T.set_tema(cargar_tema())

        self._construir_ui()
        self._aplicar_tema()
        self._cargar_bloqueadas()

        self.monitor = Monitor(
            get_bloqueadas=lambda: [b["exe"] for b in self.bloqueadas],
            get_desbloqueados=lambda: self.desbloqueados,
            on_detectado=lambda exe: self.after(0, self._pedir_desbloqueo, exe),
            on_aviso_expiracion=lambda exe, mins: self.after(
                0, self._mostrar_aviso_expiracion, exe, mins),
            dialogo_abierto=self.dialogo_abierto,
        )

        self._actualizar_tabla_periodico()

    # ── UI ────────────────────────────────────

    def _construir_ui(self):
        c = T.colores()

        # Cabecera
        self.cab = tk.Frame(self, bg=c["cabecera_bg"], padx=16, pady=10)
        self.cab.pack(fill="x")

        self.lbl_titulo = tk.Label(self.cab, text="🛡️ Control de Aplicaciones",
                 font=("Segoe UI", 13, "bold"),
                 bg=c["cabecera_bg"], fg=c["cabecera_fg"])
        self.lbl_titulo.pack(side="left")

        # Botones cabecera (derecha)
        self.btn_tema = tk.Button(self.cab, text="🌙 Modo oscuro",
                  command=self._toggle_tema,
                  bg=c["btn_cambiar"], fg="white", relief="flat",
                  font=("Segoe UI", 9), padx=10)
        self.btn_tema.pack(side="right", padx=(6, 0))

        self.btn_contrasena = tk.Button(self.cab, text="⚙ Cambiar contraseña",
                  command=self._cambiar_contrasena,
                  bg=c["btn_cambiar"], fg="white", relief="flat",
                  font=("Segoe UI", 9), padx=10)
        self.btn_contrasena.pack(side="right")

        # Estado monitor
        self.lbl_monitor = tk.Label(self,
                 text="● Monitor activo — corriendo en bandeja del sistema",
                 font=("Segoe UI", 9), fg=c["estado_ok"], anchor="w")
        self.lbl_monitor.pack(fill="x", padx=14, pady=(6, 0))

        # Tabla
        self.frame_tabla = tk.Frame(self, padx=14, pady=6)
        self.frame_tabla.pack(fill="both", expand=True)

        self.lbl_tabla = tk.Label(self.frame_tabla, text="Aplicaciones restringidas:",
                 font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_tabla.pack(fill="x", pady=(0, 4))

        self.tabla = ttk.Treeview(self.frame_tabla,
                                  columns=("app", "estado", "expira"),
                                  show="tree headings", height=10)
        self.tabla.heading("#0",     text="")
        self.tabla.heading("app",    text="Aplicación (.exe)")
        self.tabla.heading("estado", text="Estado")
        self.tabla.heading("expira", text="Expira en")
        self.tabla.column("#0",      width=30,  minwidth=30, stretch=False, anchor="center")
        self.tabla.column("app",     width=190, minwidth=100)
        self.tabla.column("estado",  width=130, minwidth=100, anchor="center")
        self.tabla.column("expira",  width=120, minwidth=80,  anchor="center")

        self.scroll_tabla = ttk.Scrollbar(self.frame_tabla, orient="vertical",
                               command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=self.scroll_tabla.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        self.scroll_tabla.pack(side="right", fill="y")

        self._actualizar_tags()

        # Botones acción
        self.btn_frame = tk.Frame(self, padx=14, pady=8)
        self.btn_frame.pack(fill="x")

        self.btn_agregar = tk.Button(self.btn_frame, text="➕ Agregar app",
                  command=self._agregar_app,
                  bg=c["btn_agregar"], fg="white", relief="flat",
                  font=("Segoe UI", 10), padx=12, pady=6)
        self.btn_agregar.pack(side="left", padx=(0, 6))

        self.btn_desbloquear = tk.Button(self.btn_frame, text="🔓 Desbloquear",
                  command=self._desbloquear_seleccionada,
                  bg=c["btn_desbloquear"], fg="white", relief="flat",
                  font=("Segoe UI", 10), padx=12, pady=6)
        self.btn_desbloquear.pack(side="left", padx=(0, 6))

        self.btn_libre = tk.Button(self.btn_frame, text="♾ Desbloqueo libre",
                  command=self._desbloqueo_libre,
                  bg=c["btn_libre"], fg="white", relief="flat",
                  font=("Segoe UI", 10), padx=12, pady=6)
        self.btn_libre.pack(side="left", padx=(0, 6))

        self.btn_quitar = tk.Button(self.btn_frame, text="🗑 Quitar",
                  command=self._quitar_app,
                  bg=c["btn_quitar"], fg="white", relief="flat",
                  font=("Segoe UI", 10), padx=12, pady=6)
        self.btn_quitar.pack(side="left")

        self.lbl_info = tk.Label(self,
                 text="ℹ Cerrar esta ventana minimiza a la bandeja. El monitor sigue activo.",
                 font=("Segoe UI", 8), fg=c["fg_gris"], anchor="w")
        self.lbl_info.pack(fill="x", padx=14, pady=(0, 6))

    def _actualizar_tags(self):
        c = T.colores()
        self.tabla.tag_configure("bloqueado",    foreground=c["row_bloqueado"])
        self.tabla.tag_configure("desbloqueado", foreground=c["row_desbloqueado"])
        self.tabla.tag_configure("expirando",    foreground=c["row_expirando"])
        self.tabla.tag_configure("libre",        foreground=c["row_libre"])

    # ── Tema ──────────────────────────────────

    def _toggle_tema(self):
        nuevo = "oscuro" if T.tema_actual() == "claro" else "claro"
        T.set_tema(nuevo)
        guardar_tema(nuevo)
        self._aplicar_tema()

    def _aplicar_tema(self):
        c = T.colores()
        es_oscuro = T.tema_actual() == "oscuro"

        # Actualizar botón tema
        self.btn_tema.config(text="☀️ Modo claro" if es_oscuro else "🌙 Modo oscuro")

        # Aplicar colores a widgets estándar
        T.aplicar_a_widget(self.winfo_toplevel(), c)

        # Actualizar widgets con referencias directas
        self.cab.config(bg=c["cabecera_bg"])
        self.lbl_titulo.config(bg=c["cabecera_bg"], fg=c["cabecera_fg"])
        self.btn_tema.config(bg=c["btn_cambiar"])
        self.btn_contrasena.config(bg=c["btn_cambiar"])
        self.lbl_monitor.config(fg=c["estado_ok"])
        self.lbl_info.config(fg=c["fg_gris"])
        self.btn_agregar.config(bg=c["btn_agregar"])
        self.btn_desbloquear.config(bg=c["btn_desbloquear"])
        self.btn_libre.config(bg=c["btn_libre"])
        self.btn_quitar.config(bg=c["btn_quitar"])

        # Actualizar ttk
        T.aplicar_ttk_style()
        self._actualizar_tags()
        self._refrescar_tabla()

    # ── Datos ─────────────────────────────────

    def _cargar_bloqueadas(self):
        raw = cargar_config().get("apps_bloqueadas", [])
        self.bloqueadas = []
        for item in raw:
            if isinstance(item, dict):
                self.bloqueadas.append(item)
            else:
                self.bloqueadas.append({"exe": item, "ruta": ""})
        self._refrescar_tabla()
        self._lazy_load_iconos()

    def _guardar_bloqueadas(self):
        cfg = cargar_config()
        cfg["apps_bloqueadas"] = self.bloqueadas
        guardar_config(cfg)

    def _lazy_load_iconos(self):
        apps_con_ruta = [b for b in self.bloqueadas if b.get("ruta")]

        def worker():
            for app in apps_con_ruta:
                exe  = app["exe"]
                ruta = app["ruta"]
                if exe in self.iconos:
                    self.after(0, self._aplicar_icono_fila, exe, self.iconos[exe])
                    continue
                foto = obtener_icono_exe(ruta, size=16)
                if foto:
                    self.iconos[exe] = foto
                    self.after(0, self._aplicar_icono_fila, exe, foto)

        threading.Thread(target=worker, daemon=True).start()

    def _aplicar_icono_fila(self, exe: str, foto):
        if self.tabla.exists(exe):
            self.tabla.item(exe, image=foto)

    def _refrescar_tabla(self):
        seleccion = self.tabla.selection()
        for row in self.tabla.get_children():
            self.tabla.delete(row)

        ahora = time.time()
        for app in self.bloqueadas:
            exe = app["exe"]
            exp = self.desbloqueados.get(exe, 0)

            if exp == LIBRE:
                estado = "♾ Libre"
                expira = "Sin límite"
                tag    = "libre"
            elif exp > ahora:
                restante = int(exp - ahora)
                mins, segs = divmod(restante, 60)
                estado = "🔓 Desbloqueado"
                expira = f"{mins}m {segs}s"
                tag    = "expirando" if restante <= 300 else "desbloqueado"
            else:
                estado = "🔒 Bloqueado"
                expira = "—"
                tag    = "bloqueado"

            foto = self.iconos.get(exe)
            if foto:
                self.tabla.insert("", "end", iid=exe, image=foto,
                                  values=(exe, estado, expira), tags=(tag,))
            else:
                self.tabla.insert("", "end", iid=exe,
                                  values=(exe, estado, expira), tags=(tag,))

        # Reaplicar íconos
        for exe, foto in self.iconos.items():
            if self.tabla.exists(exe):
                self.tabla.item(exe, image=foto)

        for item in seleccion:
            if self.tabla.exists(item):
                self.tabla.selection_set(item)

    def _actualizar_tabla_periodico(self):
        self._refrescar_tabla()
        self.after(1000, self._actualizar_tabla_periodico)

    # ── Acciones ──────────────────────────────

    def _agregar_app(self):
        VentanaSelectorApps(self.winfo_toplevel(),
                            self.bloqueadas, self._confirmar_agregar)

    def _confirmar_agregar(self, app: dict):
        exe = app["exe"]
        if exe not in [b["exe"] for b in self.bloqueadas]:
            self.bloqueadas.append(app)
            self._guardar_bloqueadas()
            self._refrescar_tabla()
            self._lazy_load_iconos()
            messagebox.showinfo("Agregada", f"'{exe}' agregada a la lista restringida.")
        else:
            messagebox.showinfo("Ya existe", f"'{exe}' ya está en la lista.")

    def _quitar_app(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una app de la lista.")
            return
        exe = sel[0]
        if messagebox.askyesno("Confirmar", f"¿Quitar '{exe}' de la lista restringida?"):
            self.bloqueadas = [b for b in self.bloqueadas if b["exe"] != exe]
            self.desbloqueados.pop(exe, None)
            self.iconos.pop(exe, None)
            self._guardar_bloqueadas()
            self._refrescar_tabla()

    def _desbloquear_seleccionada(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una app de la lista.")
            return
        self._pedir_desbloqueo(sel[0])

    def _desbloqueo_libre(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una app de la lista.")
            return
        exe = sel[0]

        def tras_verificacion(ok: bool):
            if ok:
                self.desbloqueados[exe] = LIBRE
                self._refrescar_tabla()
                messagebox.showinfo("Desbloqueado",
                    f"'{exe}' desbloqueado sin límite de tiempo.\n"
                    "Para volver a bloquearlo, usa 'Quitar' y agrégalo de nuevo.")
            self.dialogo_abierto.discard(exe)

        DialogoDesbloqueoLibre(self.winfo_toplevel(), exe,
                               self.hash_guardado, tras_verificacion)

    def _pedir_desbloqueo(self, exe: str):
        def tras_desbloqueo(segundos: int):
            if segundos > 0:
                self.desbloqueados[exe] = time.time() + segundos
                self._refrescar_tabla()
                mins  = segundos // 60
                texto = f"{mins // 60}h {mins % 60}min" if mins >= 60 else f"{mins} minutos"
                messagebox.showinfo("Desbloqueado",
                                    f"'{exe}' desbloqueado por {texto}.")
            self.dialogo_abierto.discard(exe)

        DialogoDesbloqueo(self.winfo_toplevel(), exe,
                          self.hash_guardado, tras_desbloqueo)

    def _mostrar_aviso_expiracion(self, exe: str, mins: int):
        messagebox.showwarning(
            "⏰ Aviso de expiración",
            f"'{exe}' se bloqueará en aproximadamente {mins} minuto(s).\n\n"
            "Si necesitas más tiempo, usa 'Desbloquear'."
        )

    def _cambiar_contrasena(self):
        def tras_verificacion(ok):
            if ok:
                VentanaContrasena(self.winfo_toplevel(),
                                  lambda _: None, "Cambiar contraseña")
        VentanaLogin(self.winfo_toplevel(), self.hash_guardado, tras_verificacion)

    def destruir(self):
        self.monitor.detener()