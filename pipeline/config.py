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


# Actualización rápida del mediodía (Uri, 19/11/2026): lo nuevo de la agenda tiene que salir enseguida,
# pero la tarea no puede pasar de unos minutos (GitHub da 2.000 minutos al mes). Con RAPIDA, cada pieza
# que lee webs (compra, fichas de obra, personas, webs de salas) trabaja como mucho 2 minutos: lo nuevo
# va primero y el resto lo hace la de la mañana.
RAPIDA = False
MINUTOS_RAPIDA = 2


def tope_minutos(normal: float) -> float:
    """Minutos que puede trabajar una pieza en esta ejecución."""
    return min(normal, MINUTOS_RAPIDA) if RAPIDA else normal


def carpeta_ciudad(ciudad: str) -> Path:
    """Resultados de una ciudad: data/ciudades/<ciudad>/."""
    return DATOS / "ciudades" / ciudad


def carpeta_cache(ciudad: str, pieza: str) -> Path:
    """Memoria entre días de una pieza (fuente o tarea de IA) en una ciudad."""
    return carpeta_ciudad(ciudad) / "cache" / pieza
