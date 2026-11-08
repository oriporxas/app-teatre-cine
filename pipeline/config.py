"""Carpetas del proyecto.

Los ajustes que se pueden cambiar sin programar están en la carpeta ajustes/
(ciudades y modelos de IA). Los ajustes propios de cada fuente de datos están
dentro de su pieza, en pipeline/fuentes/<fuente>/.
"""

from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"
DOCS = RAIZ / "docs"
# Descargas del día: temporales, no se guardan en el repositorio.
DESCARGAS = Path(os.environ.get("CARPETA_DESCARGAS", RAIZ / "descargas"))


def carpeta_ciudad(ciudad: str) -> Path:
    """Resultados de una ciudad: data/ciudades/<ciudad>/."""
    return DATOS / "ciudades" / ciudad


def carpeta_cache(ciudad: str, pieza: str) -> Path:
    """Memoria entre días de una pieza (fuente o tarea de IA) en una ciudad."""
    return carpeta_ciudad(ciudad) / "cache" / pieza
