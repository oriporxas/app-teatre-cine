"""Lo caducado del último mes (Uri, 19/11/2026): las obras, películas y eventos que ya han terminado
siguen en la app un mes, con la etiqueta «Caducado» (al buscar y en su apartado). Lo que terminó hace
más de un mes desaparece.

Cada día, al escribir los archivos de la app, se compara con la versión anterior: lo que estaba y ya
no está porque **todas sus funciones o sesiones han pasado** se guarda aquí con la fecha de la última
(`caducado`). Lo que desaparece teniendo aún funciones futuras (p. ej., cancelado o reclasificado) no
se guarda: no ha caducado. Si algo vuelve a tener funciones, sale de esta lista.

La memoria va en `data/ciudades/<ciudad>/caducados_<tipo>.json`, y la lista en los archivos de la app
(`caducados` en la cartelera y `caducadas` en el cine). La app, además, pasa a caducado al momento lo
que termina durante el día.
"""

from __future__ import annotations

import datetime as dt
from typing import Callable

from . import config
from .util import guardar_json, leer_json

DIAS = 30
MAX_FUNCIONES = 5


def ultima_funcion(item: dict) -> str | None:
    return max((f[0] for f in item.get("funciones") or [] if f and f[0]), default=None)


def ultima_sesion(peli: dict) -> str | None:
    return max((s[1] for s in peli.get("sesiones") or [] if len(s) > 1 and s[1]), default=None)


def recortar_escena(item: dict) -> dict:
    """Lo que sale en la app de una obra caducada: sus datos y sus últimas funciones."""
    return {**item, "funciones": (item.get("funciones") or [])[-MAX_FUNCIONES:]}


def recortar_cine(peli: dict) -> dict:
    """De una película caducada se quedan sus datos, sin sesiones."""
    return {k: v for k, v in peli.items() if k != "sesiones"}


def actualizar(ciudad, tipo: str, hoy: dt.date, anteriores: list[dict], actuales: list[dict],
               ultima: Callable[[dict], str | None], recortar: Callable[[dict], dict]) -> list[dict]:
    """Devuelve lo caducado del último mes (lo más reciente primero) y guarda la memoria."""
    ruta = config.carpeta_ciudad(ciudad.id) / f"caducados_{tipo}.json"
    memoria: dict = leer_json(ruta, {}) or {}
    hoy_iso = hoy.isoformat()
    limite = (hoy - dt.timedelta(days=DIAS)).isoformat()
    ids_hoy = {x["id"] for x in actuales}
    for x in anteriores:
        u = ultima(x)
        if x["id"] in ids_hoy or not u or u >= hoy_iso:
            continue  # sigue en cartel, o desapareció con funciones futuras: no ha caducado
        memoria[x["id"]] = recortar(x) | {"caducado": u}
    for i in list(memoria):
        if i in ids_hoy or memoria[i]["caducado"] < limite:
            del memoria[i]  # ha vuelto a cartel, o caducó hace más de un mes: fuera de la app
    guardar_json(ruta, memoria)
    return sorted(memoria.values(), key=lambda x: x["caducado"], reverse=True)
