"""
tema.py
Define los colores para modo claro y oscuro.
Aplica el tema a todas las ventanas Tkinter abiertas.
"""
import tkinter as tk
from tkinter import ttk

# ── Paletas ───────────────────────────────────────────────────────────────────

TEMAS = {
    "claro": {
        "bg":           "#f5f5f5",
        "bg2":          "#ffffff",
        "fg":           "#1a1a1a",
        "fg2":          "#555555",
        "fg_gris":      "gray",
        "cabecera_bg":  "#0078D4",
        "cabecera_fg":  "#ffffff",
        "btn_cambiar":  "#005a9e",
        "btn_agregar":  "#27ae60",
        "btn_desbloquear": "#e67e22",
        "btn_libre":    "#8e44ad",
        "btn_quitar":   "#c0392b",
        "btn_tema":     "#555555",
        "entry_bg":     "#ffffff",
        "entry_fg":     "#1a1a1a",
        "tabla_bg":     "#ffffff",
        "tabla_fg":     "#1a1a1a",
        "tabla_sel":    "#cce4f7",
        "separador":    "#dddddd",
        "estado_ok":    "#27ae60",
        "row_bloqueado":   "#c0392b",
        "row_desbloqueado": "#27ae60",
        "row_expirando":   "#e67e22",
        "row_libre":       "#8e44ad",
    },
    "oscuro": {
        "bg":           "#1e1e1e",
        "bg2":          "#2d2d2d",
        "fg":           "#e8e8e8",
        "fg2":          "#aaaaaa",
        "fg_gris":      "#888888",
        "cabecera_bg":  "#1a5a8a",
        "cabecera_fg":  "#ffffff",
        "btn_cambiar":  "#0f3d5c",
        "btn_agregar":  "#1e7e45",
        "btn_desbloquear": "#b05a10",
        "btn_libre":    "#5e2a7e",
        "btn_quitar":   "#8e1a1a",
        "btn_tema":     "#888888",
        "entry_bg":     "#3a3a3a",
        "entry_fg":     "#e8e8e8",
        "tabla_bg":     "#2d2d2d",
        "tabla_fg":     "#e8e8e8",
        "tabla_sel":    "#1a4a6a",
        "separador":    "#444444",
        "estado_ok":    "#2ecc71",
        "row_bloqueado":   "#e74c3c",
        "row_desbloqueado": "#2ecc71",
        "row_expirando":   "#f39c12",
        "row_libre":       "#9b59b6",
    },
}

# Tema activo actual
_tema_actual = "claro"


def tema_actual() -> str:
    return _tema_actual


def colores() -> dict:
    return TEMAS[_tema_actual]


def set_tema(nombre: str):
    global _tema_actual
    if nombre in TEMAS:
        _tema_actual = nombre


def aplicar_ttk_style():
    """Aplica el tema a los widgets ttk (Treeview, Scrollbar)."""
    c   = colores()
    sty = ttk.Style()

    sty.theme_use("default")

    sty.configure("Treeview",
                  background=c["tabla_bg"],
                  foreground=c["tabla_fg"],
                  fieldbackground=c["tabla_bg"],
                  rowheight=24,
                  font=("Segoe UI", 10))
    sty.map("Treeview",
            background=[("selected", c["tabla_sel"])],
            foreground=[("selected", c["tabla_fg"])])

    sty.configure("Treeview.Heading",
                  background=c["bg2"],
                  foreground=c["fg"],
                  font=("Segoe UI", 9, "bold"))
    sty.map("Treeview.Heading",
            background=[("active", c["bg2"])])

    sty.configure("Vertical.TScrollbar",
                  background=c["bg2"],
                  troughcolor=c["bg"],
                  arrowcolor=c["fg2"])


def aplicar_a_widget(widget, c: dict):
    """Aplica colores de fondo/frente recursivamente a widgets tk estándar."""
    try:
        clase = widget.winfo_class()
        if clase in ("Frame", "Toplevel", "Tk"):
            widget.configure(bg=c["bg"])
        elif clase == "Label":
            widget.configure(bg=c["bg"], fg=c["fg"])
        elif clase == "Entry":
            widget.configure(bg=c["entry_bg"], fg=c["entry_fg"],
                             insertbackground=c["fg"])
        elif clase == "Button":
            # No tocar botones de colores específicos (agregar, quitar, etc.)
            pass
        elif clase == "Radiobutton":
            widget.configure(bg=c["bg"], fg=c["fg"],
                             selectcolor=c["bg2"],
                             activebackground=c["bg"],
                             activeforeground=c["fg"])
        elif clase == "Checkbutton":
            widget.configure(bg=c["bg"], fg=c["fg"],
                             selectcolor=c["bg2"])
        elif clase == "Spinbox":
            widget.configure(bg=c["entry_bg"], fg=c["entry_fg"],
                             buttonbackground=c["bg2"])
    except Exception:
        pass

    for hijo in widget.winfo_children():
        aplicar_a_widget(hijo, c)