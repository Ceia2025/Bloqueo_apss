import time
import threading
import psutil

INTERVALO_MONITOR = 2   # segundos entre revisiones
AVISO_ANTICIPADO = 300  # avisar 5 minutos (300 seg) antes de expirar


def matar_todos(nombre_exe: str):
    """
    Mata TODOS los procesos que coincidan con nombre_exe.
    Necesario para navegadores como Brave/Chrome que usan múltiples procesos.
    """
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if proc.info["name"].lower() == nombre_exe:
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


class Monitor:
    def __init__(self, get_bloqueadas, get_desbloqueados,
                 on_detectado, on_aviso_expiracion, dialogo_abierto):
        """
        get_bloqueadas       → función que retorna lista de exe bloqueados
        get_desbloqueados    → función que retorna dict {exe: timestamp_expiracion}
        on_detectado         → callback(exe) cuando se detecta proceso bloqueado
        on_aviso_expiracion  → callback(exe, minutos_restantes) para avisar antes de expirar
        dialogo_abierto      → set compartido para evitar doble diálogo
        """
        self.get_bloqueadas = get_bloqueadas
        self.get_desbloqueados = get_desbloqueados
        self.on_detectado = on_detectado
        self.on_aviso_expiracion = on_aviso_expiracion
        self.dialogo_abierto = dialogo_abierto
        self.activo = True

        # Rastrear para qué apps ya se envió el aviso de 5 min
        self._aviso_enviado = set()

        self._hilo = threading.Thread(target=self._loop, daemon=True)
        self._hilo.start()

    def _loop(self):
        while self.activo:
            try:
                self._revisar()
            except Exception:
                pass
            time.sleep(INTERVALO_MONITOR)

    def _revisar(self):
        ahora = time.time()
        bloqueadas = self.get_bloqueadas()
        desbloqueados = self.get_desbloqueados()

        # Set de procesos activos
        procesos_activos = set()
        for proc in psutil.process_iter(["name"]):
            try:
                procesos_activos.add(proc.info["name"].lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        for exe in bloqueadas:
            exp = desbloqueados.get(exe, 0)

            # ── App desbloqueada temporalmente
            if exp > ahora:
                restante = exp - ahora

                # Aviso de 5 minutos antes de que expire
                if restante <= AVISO_ANTICIPADO and exe not in self._aviso_enviado:
                    self._aviso_enviado.add(exe)
                    mins = int(restante // 60)
                    self.on_aviso_expiracion(exe, mins if mins > 0 else 1)

                # Limpiar aviso si se volvió a desbloquear con más tiempo
                if restante > AVISO_ANTICIPADO and exe in self._aviso_enviado:
                    self._aviso_enviado.discard(exe)

                continue  # no bloquear todavía

            # ── App bloqueada — si está corriendo, matarla
            self._aviso_enviado.discard(exe)  # resetear aviso para próxima vez

            if exe not in procesos_activos:
                continue

            if exe not in self.dialogo_abierto:
                self.dialogo_abierto.add(exe)
                matar_todos(exe)
                self.on_detectado(exe)

    def detener(self):
        self.activo = False