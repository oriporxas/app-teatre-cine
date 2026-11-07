"""Pequeñas herramientas compartidas."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path


def limpiar_id(valor) -> str:
    """Los identificadores del Ayuntamiento llegan a veces con un carácter invisible (BOM)."""
    return str(valor or "").replace("﻿", "").strip()


def sin_acentos(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, sin signos raros: para comparar textos."""
    t = sin_acentos(texto).lower().replace("l·l", "ll").replace("l.l", "ll")
    t = re.sub(r"[^a-z0-9€]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def slug(texto: str) -> str:
    return normalizar(texto).replace(" ", "-")[:80] or "activitat"


def huella(*partes) -> str:
    """Resumen corto de un contenido: si cambia el contenido, cambia la huella."""
    h = hashlib.sha256()
    for p in partes:
        h.update(json.dumps(p, ensure_ascii=False, sort_keys=True).encode())
    return h.hexdigest()[:16]


def leer_json(ruta: Path, defecto=None):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return defecto


def guardar_json(ruta: Path, datos, por_lineas: bool = False) -> None:
    """Guarda JSON. `por_lineas` escribe un elemento por línea (cambios pequeños en git)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        if por_lineas and isinstance(datos, dict):
            f.write("{\n")
            claves = sorted(datos)
            for i, k in enumerate(claves):
                coma = "," if i < len(claves) - 1 else ""
                f.write(f"{json.dumps(k, ensure_ascii=False)}: "
                        f"{json.dumps(datos[k], ensure_ascii=False, sort_keys=True)}{coma}\n")
            f.write("}\n")
        elif por_lineas and isinstance(datos, list):
            f.write("[\n")
            for i, x in enumerate(datos):
                coma = "," if i < len(datos) - 1 else ""
                f.write(json.dumps(x, ensure_ascii=False, sort_keys=True) + coma + "\n")
            f.write("]\n")
        else:
            json.dump(datos, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
    tmp.replace(ruta)
