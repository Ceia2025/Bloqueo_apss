# 🛡️ Control de Aplicaciones

Programa de control parental para Windows 11 que bloquea aplicaciones
y permite desbloquearlas temporalmente con contraseña maestra.

---

## Estructura del proyecto

```
control_apps/
├── main.py          ← Entrada principal. Maneja login y ventana raíz.
├── config.py        ← Cargar/guardar config y hash de contraseña.
├── monitor.py       ← Lógica de bloqueo. Revisa procesos cada 2 segundos.
├── tray.py          ← Ícono en bandeja del sistema (system tray).
├── README.md
├── .gitignore
└── ui/
    ├── __init__.py  ← Vacío, necesario para que Python reconozca la carpeta.
    ├── panel.py     ← Ventana principal con la tabla de apps bloqueadas.
    ├── login.py     ← Ventanas de login y crear/cambiar contraseña.
    ├── dialogo.py   ← Diálogo de desbloqueo temporal (minutos o hasta hora).
    └── selector.py  ← Buscador de apps instaladas para agregar a la lista.
```

---

## Requisitos

```bash
pip install psutil pystray pillow pywin32
```

---

## Ejecutar (modo desarrollo)

```bash
python main.py
```

## Compilar a .exe

```bash
python -m PyInstaller --onefile --windowed --add-data "ui;ui" main.py
```

El `.exe` quedará en la carpeta `dist/`.
El archivo `control_config.json` se genera automáticamente junto al `.exe` la primera vez.

---

## Guía de modificaciones

### Cambiar el ícono de la bandeja del sistema
**Archivo:** `tray.py` → función `crear_icono_img()`

El ícono se genera con código (Pillow). Para usar un archivo propio:
```python
def crear_icono_img() -> Image.Image:
    return Image.open("mi_icono.png")  # debe estar junto al main.py
```

### Cambiar colores y fuentes de la interfaz
**Archivo:** `ui/panel.py` → método `_construir_ui()`

- Color cabecera azul → busca `bg="#0078D4"`
- Fuente general → busca `font=("Segoe UI", 10)`
- Color filas bloqueadas (rojo) → busca `tag_configure("bloqueado", foreground="#c0392b")`
- Color filas por expirar (naranja) → busca `tag_configure("expirando", ...)`

### Cambiar el tiempo entre revisiones del monitor
**Archivo:** `monitor.py` → constante `INTERVALO_MONITOR`
```python
INTERVALO_MONITOR = 2  # segundos
```

### Cambiar el tiempo de aviso antes de que expire
**Archivo:** `monitor.py` → constante `AVISO_ANTICIPADO`
```python
AVISO_ANTICIPADO = 300  # 300 = 5 minutos
```

### Cambiar el máximo de intentos de contraseña
**Archivo:** `config.py` → constante `MAX_INTENTOS`

### Cambiar el nombre de la aplicación
**Archivo:** `main.py` → constante `APP_TITULO`

### Cambiar las opciones de minutos en el diálogo de desbloqueo
**Archivo:** `ui/dialogo.py`
```python
for mins in [15, 30, 60, 120]:  # agrega o quita valores
```

### Agregar íconos a las apps en la lista (pendiente)
**Archivos:** `ui/selector.py` y `ui/panel.py`
Se puede extraer el ícono del `.exe` usando `icoextract` y mostrarlo
en la tabla. Pendiente de implementar.

---

## Archivos generados (no subir a Git)

- `control_config.json` — contraseña cifrada y lista de apps bloqueadas
- `build/` — archivos temporales de PyInstaller
- `dist/` — ejecutable final
- `*.spec` — configuración de compilación