import hashlib
import json
import os

ARCHIVO_CONFIG = "control_config.json"
MAX_INTENTOS = 3


def hash_txt(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def cargar_config() -> dict:
    if os.path.exists(ARCHIVO_CONFIG):
        with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_config(datos: dict):
    with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)