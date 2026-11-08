"""Fuentes de datos. Cada subcarpeta es una pieza independiente (ver base.py).

Fuentes disponibles:
- open_data_bcn: agendas del Ayuntamiento de Barcelona + fichas de guia.barcelona.cat
"""

from __future__ import annotations

import importlib
from types import ModuleType


def cargar(nombre: str) -> ModuleType:
    """Devuelve el módulo de la fuente `nombre` (p. ej. "open_data_bcn")."""
    modulo = importlib.import_module(f"{__name__}.{nombre}")
    if getattr(modulo, "NOMBRE", None) != nombre or not callable(getattr(modulo, "recoger", None)):
        raise RuntimeError(f"La fuente «{nombre}» no cumple lo que pide pipeline/fuentes/base.py")
    return modulo
