"""Auditoría de cobertura: ¿se nos escapa alguna sala, algún cine?

Cada día se compara la **lista oficial de equipamientos** de la ciudad (en Barcelona, el conjunto
abierto «equipament-cultura-i-lleure»: teatros, auditorios y cines) con lo que la app tiene:
- salas oficiales con actividades en la cartelera (cubiertas),
- salas oficiales **sin ninguna actividad** en nuestras fuentes (posibles huecos: cerradas, sin
  programación o que no publican en la agenda municipal),
- cines con horarios y cines sin horarios (y por qué: su web no lo permite, no responde…).

El resultado (`data/ciudades/<ciudad>/cobertura.json`) dice dónde hay que añadir fuentes. Es la
lista de trabajo para el siguiente paso de la visión: que la IA lea la web de cada sala sin datos
(ver docs/veracidad.md). Sin listas hechas a mano: todo sale de los datos oficiales.
"""

from __future__ import annotations

import collections
import datetime as dt

from . import config
from .util import guardar_json, leer_json

CATEGORIAS = {"Teatres": "teatro", "Auditoris": "auditorio", "Cinemes": "cine"}
FUENTE_WEBS = "webs_salas"


def auditar(ciudad, equipamientos: list[dict] | None, actividades: list[dict], cine_informe: dict | None = None) -> dict:
    """Devuelve el resumen y guarda el detalle. `actividades`: todas las del día (también las no publicadas)."""
    if not equipamientos:
        ruta = config.DESCARGAS / ciudad.id / "open_data_bcn" / "equipamientos.json"
        equipamientos = leer_json(ruta, []) or []
    con_actividad: collections.Counter = collections.Counter()
    for a in actividades:
        if a.get("fuente") == FUENTE_WEBS:  # lo que lee el lector de webs no cuenta: si no, la sala saldría
            continue                        # «cubierta» y al día siguiente se dejaría de leer su web
        d = a.get("direccion") or (a.get("lugar") or {}).get("direccion") or {}
        clave = a.get("sala_id") or (a.get("lugar") or {}).get("clave")  # «barcelona:via268003-450»
        if clave:
            con_actividad[str(clave).rsplit(":", 1)[-1]] += 1
        elif d.get("via_id") and d.get("numero"):
            con_actividad[f"via{d['via_id']}-{d['numero']}"] += 1
    salas: dict[str, dict] = {}
    for e in equipamientos:
        tipo = CATEGORIAS.get(e.get("categoria") or "")
        if not tipo or not (e.get("via_id") and e.get("numero")):
            continue
        clave = f"via{e['via_id']}-{e['numero']}"
        s = salas.setdefault(clave, {"nombre": e.get("pertenece_a") or e.get("nombre"), "tipos": set(), "id": e.get("id"),
                                     **{k: e.get(k) for k in ("calle", "numero", "barrio", "distrito", "codigo_postal", "lat", "lon")}})
        s["tipos"].add(tipo)
    cubiertas, huecos = [], []
    for clave, s in salas.items():
        fila = {"nombre": s["nombre"], "tipo": sorted(s["tipos"]), "clave": clave, "actividades": con_actividad.get(clave, 0),
                **{k: s[k] for k in ("id", "calle", "numero", "barrio", "distrito", "codigo_postal", "lat", "lon") if s.get(k)}}
        (cubiertas if fila["actividades"] else huecos).append(fila)
    huecos.sort(key=lambda x: (x["tipo"], x["nombre"] or ""))
    resumen = {
        "fecha": dt.date.today().isoformat(),
        "salas_oficiales": len(salas),
        "con_actividades": len(cubiertas),
        "sin_actividades": len(huecos),
        "por_tipo": {t: {"oficiales": sum(1 for s in salas.values() if t in s["tipos"]),
                         "sin_actividades": sum(1 for h in huecos if t in h["tipo"])} for t in CATEGORIAS.values()},
    }
    if cine_informe and cine_informe.get("cines"):
        cines = cine_informe["cines"]
        resumen["cines_con_horarios"] = sorted(n for n, v in cines.items() if isinstance(v, dict) and v.get("sesiones"))
        resumen["cines_sin_horarios"] = {n: (v.get("motivo") or v.get("como") or "sin horarios") if isinstance(v, dict) else str(v)
                                         for n, v in cines.items() if not (isinstance(v, dict) and v.get("sesiones"))}
    guardar_json(config.carpeta_ciudad(ciudad.id) / "cobertura.json", {**resumen, "sin_actividades_detalle": huecos})
    return resumen
