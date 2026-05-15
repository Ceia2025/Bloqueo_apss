import tkinter as tk
from tkinter import ttk, messagebox
import time
import psutil
import os

from config import cargar_config, guardar_config
from monitor import Monitor
from ui.dialogo import DialogoDesbloqueo
from ui.iconos import obtener_icono_exe
from ui.login import VentanaContrasena, VentanaLogin
from ui.selector import VentanaSelectorApps


def _buscar_ruta_exe(exe: str) -> str:
    """Busca la ruta completa de un exe en los procesos activos."""
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            if proc.info["name"].lower() == exe:
                ruta = proc.info.get("exe") or ""
                if ruta and os.path.exists(ruta):
                    return ruta
        except Exception:
            pass
    return ""


class PanelPrincipal(tk.Frame):
    def __init__(self, parent, hash_guardado: str):
        super().__init__(parent)
        self.hash_guardado = hash_guardado
        self.pack(fill="both", expand=True)

        self.bloqueadas    = []
        self.desbloqueados = {}
        self.dialogo_abierto = set()
        self.iconos        = {}   # exe -> PhotoImage
        self.rutas_exe     = {}   # exe -> ruta completa

        self._construir_ui()
        self._cargar_bloqueadas()

        self.monitor = Monitor(
            get_bloqueadas=lambda: self.bloqueadas,
            get_desbloqueados=lambda: self.desbloqueados,
            on_detectado=lambda exe: self.after(0, self._pedir_desbloqueo, exe),
            on_aviso_expiracion=lambda exe, mins: self.after(
                0, self._mostrar_aviso_expiracion, exe, mins),
            dialogo_abierto=self.dialogo_abierto,
        )

        self._actualizar_tabla_periodico()

    # ── UI ────────────────────────────────────

    def _construir_ui(self):
        cab = tk.Frame(self, bg="#0078D4", padx=16, pady=10)
        cab.pack(fill="x")
        tk.Label(cab, text="🛡️ Control de Aplicaciones",
                 font=("Segoe UI", 13, "bold"),
                 bg="#0078D4", fg="white").pack(side="left")
        tk.Button(cab, text="⚙ Cambiar contraseña",
                  command=self._cambiar_contrasena,
                  bg="#005a9e", fg="white", relief="flat",
                  font=("Segoe UI", 9), padx=10).pack(side="right")

        tk.Label(self,
                 text="● Monitor activo — corriendo en bandeja del sistema",
                 font=("Segoe UI", 9), fg="#27ae60", anchor="w").pack(
                     fill="x", padx=14, pady=(6, 0))

        frame_tabla = tk.Frame(self, padx=14, pady=6)
        frame_tabla.pack(fill="both", expand=True)
        tk.Label(frame_tabla, text="Aplicaciones restringidas:",
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", pady=(0, 4))

        self.tabla = ttk.Treeview(frame_tabla,
                                  columns=("app", "estado", "expira"),
                                  show="tree headings", height=12)
        self.tabla.heading("#0",      text="")
        self.tabla.heading("app",     text="Aplicación (.exe)")
        self.tabla.heading("estado",  text="Estado")
        self.tabla.heading("expira",  text="Expira en")
        self.tabla.column("#0",       width=28, stretch=False, anchor="center")
        self.tabla.column("app",      width=195)
        self.tabla.column("estado",   width=120, anchor="center")
        self.tabla.column("expira",   width=110, anchor="center")

        scroll = ttk.Scrollbar(frame_tabla, orient="vertical",
                               command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tabla.tag_configure("bloqueado",   foreground="#c0392b")
        self.tabla.tag_configure("desbloqueado", foreground="#27ae60")
        self.tabla.tag_configure("expirando",   foreground="#e67e22")

        btn_frame = tk.Frame(self, padx=14, pady=8)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="➕ Agregar app",
                  command=self._agregar_app,
                  bg="#27ae60", fg="white", relief="flat",
                  font=("Segoe UI", 10), padx=14, pady=6).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="🔓 Desbloquear seleccionada",
                  command=self._desbloquear_seleccionada,
                  bg="#e67e22", fg="white", relief="flat",
                  font=("Segoe UI", 10), padx=14, pady=6).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="🗑 Quitar seleccionada",
                  command=self._quitar_app,
                  bg="#c0392b", fg="white", relief="flat",
                  font=("Segoe UI", 10), padx=14, pady=6).pack(side="left")

        tk.Label(self,
                 text="ℹ Cerrar esta ventana minimiza a la bandeja. El monitor sigue activo.",
                 font=("Segoe UI", 8), fg="gray", anchor="w").pack(
                     fill="x", padx=14, pady=(0, 6))

    # ── Datos ─────────────────────────────────

    def _cargar_bloqueadas(self):
        self.bloqueadas = cargar_config().get("apps_bloqueadas", [])
        self._refrescar_tabla()
        # Cargar íconos en segundo plano para las apps ya en la lista
        self._cargar_iconos_lista()

    def _guardar_bloqueadas(self):
        cfg = cargar_config()
        cfg["apps_bloqueadas"] = self.bloqueadas
        guardar_config(cfg)

    def _cargar_iconos_lista(self):
        """Intenta cargar íconos de las apps bloqueadas en segundo plano."""
        import threading

        def worker():
            for exe in list(self.bloqueadas):
                if exe in self.iconos:
                    continue
                ruta = self.rutas_exe.get(exe) or _buscar_ruta_exe(exe)
                if ruta:
                    self.rutas_exe[exe] = ruta
                    foto = obtener_icono_exe(ruta, size=16)
                    if foto:
                        self.iconos[exe] = foto
                        # Actualizar fila si existe
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
        for exe in self.bloqueadas:
            exp = self.desbloqueados.get(exe, 0)
            if exp > ahora:
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

    def _confirmar_agregar(self, exe: str):
        if exe not in self.bloqueadas:
            self.bloqueadas.append(exe)
            self._guardar_bloqueadas()
            self._refrescar_tabla()
            self._cargar_iconos_lista()
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
            self.bloqueadas.remove(exe)
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
            "Si necesitas más tiempo, usa 'Desbloquear seleccionada'."
        )

    def _cambiar_contrasena(self):
        def tras_verificacion(ok):
            if ok:
                VentanaContrasena(self.winfo_toplevel(),
                                  lambda _: None, "Cambiar contraseña")
        VentanaLogin(self.winfo_toplevel(), self.hash_guardado, tras_verificacion)

    def destruir(self):
        self.monitor.detener()