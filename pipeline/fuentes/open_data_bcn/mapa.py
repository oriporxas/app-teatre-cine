"""Contorno de los distritos de Barcelona, para dibujar el mapa de la app.

Sale de los datos abiertos del Ayuntamiento (conjunto «20170706-districtes-barris»,
por la API oficial). Así el mapa no depende de servicios de mapas de terceros:
funciona sin conexión y no comparte con nadie dónde está quien lo mira.
Los distritos casi nunca cambian: se descarga una vez y se renueva cada 90 días.
"""

from __future__ import annotations

import datetime as dt
import math
import re
from pathlib import Path

from ...util import guardar_json, leer_json
from . import descargar

CONJUNTO = "20170706-districtes-barris"
RECURSO = "BarcelonaCiutat_Districtes.csv"
DIAS_VALIDO = 90
TOLERANCIA_METROS = 25  # simplificación del contorno: invisible en un móvil y el archivo pesa poco


def _anillos(wkt: str) -> list[list[tuple[float, float]]]:
    """POLYGON / MULTIPOLYGON en texto -> lista de anillos [(lon, lat), …]."""
    anillos = []
    for trozo in re.findall(r"\(([^()]+)\)", wkt):
        puntos = [tuple(float(x) for x in par.split()[:2]) for par in trozo.split(",")]
        if len(puntos) >= 4:
            anillos.append(puntos)
    return anillos


def _simplificar(puntos: list[tuple[float, float]], tolerancia: float) -> list[tuple[float, float]]:
    """Douglas-Peucker en metros aproximados. Un anillo cerrado (primer punto = último) se parte
    por su punto más lejano, porque un tramo de longitud cero no sirve de referencia."""
    if len(puntos) < 3:
        return puntos
    if puntos[0] == puntos[-1]:
        x0, y0 = puntos[0]
        k = max(range(len(puntos)), key=lambda i: (puntos[i][0] - x0) ** 2 + (puntos[i][1] - y0) ** 2)
        if 0 < k < len(puntos) - 1:
            return _simplificar(puntos[:k + 1], tolerancia)[:-1] + _simplificar(puntos[k:], tolerancia)
    lat0 = math.radians(puntos[0][1])
    xy = [(lon * 111320 * math.cos(lat0), lat * 110540) for lon, lat in puntos]
    guardar = [False] * len(puntos)
    guardar[0] = guardar[-1] = True
    pila = [(0, len(puntos) - 1)]
    while pila:
        i, j = pila.pop()
        (x1, y1), (x2, y2) = xy[i], xy[j]
        dx, dy = x2 - x1, y2 - y1
        largo = math.hypot(dx, dy) or 1e-9
        peor, k_peor = 0.0, -1
        for k in range(i + 1, j):
            d = abs(dy * (xy[k][0] - x1) - dx * (xy[k][1] - y1)) / largo
            if d > peor:
                peor, k_peor = d, k
        if peor > tolerancia:
            guardar[k_peor] = True
            pila += [(i, k_peor), (k_peor, j)]
    return [p for p, g in zip(puntos, guardar) if g]


def obtener(carpeta_cache: Path, hoy: dt.date) -> dict | None:
    """Los distritos (de la caché si son recientes). None si no se pueden obtener."""
    ruta = carpeta_cache / "mapa.json"
    guardado = leer_json(ruta, None)
    if guardado and (hoy - dt.date.fromisoformat(guardado["fecha"])).days < DIAS_VALIDO:
        return guardado
    try:
        recurso = next(r for r in descargar.recursos(CONJUNTO) if r["name"] == RECURSO)
        filas = descargar._datastore_completo(recurso["id"])
    except Exception:  # noqa: BLE001 - sin mapa nuevo, vale el de antes (o ninguno)
        return guardado
    areas = []
    for f in sorted(filas, key=lambda f: int(f.get("Codi_Districte") or 0)):
        anillos = [[[round(lon, 5), round(lat, 5)] for lon, lat in _simplificar(a, TOLERANCIA_METROS)]
                   for a in _anillos(f.get("geometria_wgs84") or "")]
        if anillos:
            areas.append({"nombre": f.get("nom_districte"), "anillos": anillos})
    mapa = {"fecha": hoy.isoformat(), "tipo": "distritos", "areas": areas,
            "fuente": "Ajuntament de Barcelona, Open Data BCN («Districtes i barris»), CC BY 4.0"}
    guardar_json(ruta, mapa)
    return mapa
