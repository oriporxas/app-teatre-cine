"""Lugares de Barcelona: a qué sala pertenece cada actividad.

Esto es propio de esta fuente (usa los códigos de calle del Ayuntamiento y su
lista de equipamientos). El resultado se entrega en el formato común
(«lugar»), y pipeline/salas.py lo agrupa sin saber de qué ciudad es.

Sin listas hechas a mano: las salas salen de los propios datos.
- La clave de cada sala es su dirección (código de calle del Ayuntamiento +
  número). Así «Teatreneu - Sala Cafè Teatre» y «Teatreneu - Sala Xavier
  Fàbregas» quedan dentro de la misma sala, cada una como sala interior.
- El nombre sale de la ficha de la guía y del conjunto de datos abierto de
  equipamientos culturales del Ayuntamiento, que dice qué sala pertenece a
  qué equipamiento («institution_name»).
"""

from __future__ import annotations

import collections
import json
import urllib.parse
from pathlib import Path

from ...util import limpiar_id, normalizar
from .descargar import CATALOGO, _pedir_con_reintentos, recursos

EQUIPAMIENTOS_CONJUNTO = "equipament-cultura-i-lleure"


def descargar_equipamientos(carpeta: Path) -> list[dict]:
    """Descarga la lista de equipamientos de cultura y ocio por la API oficial."""
    res = recursos(EQUIPAMIENTOS_CONJUNTO)
    csv = next(r for r in res if (r.get("format") or "").upper() == "CSV" and r.get("datastore_active"))
    filas, desde = [], 0
    while True:
        q = urllib.parse.urlencode({"resource_id": csv["id"], "limit": 5000, "offset": desde})
        datos = json.loads(_pedir_con_reintentos(f"{CATALOGO}/datastore_search?{q}"))
        bloque = datos["result"]["records"]
        filas += bloque
        desde += len(bloque)
        if not bloque or desde >= datos["result"]["total"]:
            break
    equip = [{
        "id": limpiar_id(f.get("register_id")),
        "nombre": (f.get("name") or "").strip(),
        "pertenece_a": (f.get("institution_name") or "").strip() or None,
        "categoria": f.get("secondary_filters_name") or None,
        "via_id": str(f.get("addresses_road_id") or "") or None,
        "numero": str(f.get("addresses_start_street_number") or "") or None,
    } for f in filas]
    carpeta.mkdir(parents=True, exist_ok=True)
    with open(carpeta / "equipamientos.json", "w", encoding="utf-8") as f:
        json.dump(equip, f, ensure_ascii=False)
    return equip


def clave_lugar(a: dict) -> str:
    d = a.get("direccion") or {}
    if d.get("via_id") and d.get("numero"):
        return f"via{d['via_id']}-{d['numero']}"
    c = a.get("coordenadas")
    if c:
        return f"geo{c['lat']:.4f},{c['lon']:.4f}"
    if d.get("calle"):
        return "calle-" + normalizar(d["calle"]).replace(" ", "-")
    return "sin-direccion"


def categorias_por_lugar(equipamientos: list[dict]) -> dict[str, set[str]]:
    """{clave de dirección: categorías de los equipamientos que hay allí}."""
    res: dict[str, set[str]] = collections.defaultdict(set)
    for e in equipamientos:
        if e["via_id"] and e["numero"] and e["categoria"]:
            res[f"via{e['via_id']}-{e['numero']}"].add(e["categoria"])
    return res


def _partir(nombre: str) -> tuple[str, str | None]:
    """«Teatreneu Multisales - Sala Cafè Teatre» -> («Teatreneu Multisales», «Sala Cafè Teatre»)."""
    if " - " in nombre:
        base, interior = nombre.split(" - ", 1)
        return base.strip(), interior.strip()
    return nombre.strip(), None


def asignar(actividades: dict[str, dict], equipamientos: list[dict], ciudad: str) -> None:
    """Anota en cada actividad su lugar («lugar», en el formato común de base.py)."""
    por_direccion = collections.defaultdict(list)
    por_id = {}
    for e in equipamientos:
        if e["via_id"] and e["numero"]:
            por_direccion[f"via{e['via_id']}-{e['numero']}"].append(e)
        por_id[e["id"]] = e

    grupos = collections.defaultdict(list)
    for a in actividades.values():
        grupos[clave_lugar(a)].append(a)

    for clave, lista in grupos.items():
        equip = por_direccion.get(clave, [])
        nombres_base = collections.Counter()
        interiores = set()
        for a in lista:
            g = a.get("guia") or {}
            if g.get("sala"):
                base, interior = _partir(g["sala"])
                e = por_id.get(g.get("sala_id_guia") or "")
                if e and e.get("pertenece_a"):
                    # La lista de equipamientos dice a qué casa pertenece esta sala.
                    base, interior = e["pertenece_a"], e["nombre"] if normalizar(e["nombre"]) != normalizar(e["pertenece_a"]) else interior
                nombres_base[base] += 1
                if interior:
                    interiores.add(interior)
        if not nombres_base and equip:
            padres = collections.Counter(e["pertenece_a"] for e in equip if e["pertenece_a"])
            if padres:
                nombres_base[padres.most_common(1)[0][0]] += 1
            else:
                cultura = [e for e in equip if e["categoria"]]
                nombres_base[(cultura or equip)[0]["nombre"]] += 1
        nombre = nombres_base.most_common(1)[0][0] if nombres_base else None
        for e in equip:
            if nombre and e.get("pertenece_a") and normalizar(e["pertenece_a"]) == normalizar(nombre) \
                    and normalizar(e["nombre"]) != normalizar(nombre):
                interiores.add(e["nombre"])
        categorias = sorted({e["categoria"] for e in equip if e["categoria"]})
        for a in lista:
            g = a.get("guia") or {}
            _, interior = _partir(g.get("sala") or "")
            e = por_id.get(g.get("sala_id_guia") or "")
            if e and e.get("pertenece_a") and normalizar(e["nombre"]) != normalizar(e["pertenece_a"]):
                interior = e["nombre"]
            d = a.get("direccion") or {}
            a["lugar"] = {
                # Sin dirección no hay forma fiable de saber la sala: se deja sin asignar.
                "clave": f"{ciudad}:{clave}" if clave != "sin-direccion" else None,
                "nombre_casa": nombre,
                "nombre_en_fuente": g.get("sala"),
                "sala_interior": interior,
                "salas_interiores_conocidas": sorted(interiores),
                "tipo_de_lugar": g.get("se_celebra_a"),
                "direccion": {k: d.get(k) for k in ("calle", "numero", "codigo_postal", "barrio", "distrito", "municipio")},
                "coordenadas": a.get("coordenadas"),
                "ids_origen": [g["sala_id_guia"]] if g.get("sala_id_guia") else [],
                "categorias": categorias,
            }


def buscar_por_nombre(salas: dict[str, dict], equipamientos: list[dict], texto: str) -> dict:
    """Para comprobar salas concretas (p. ej. las que el brief no encontró)."""
    t = normalizar(texto)
    en_agenda = [s for s in salas.values()
                 if s["nombre"] and t in normalizar(s["nombre"])
                 or any(t in normalizar(x) for x in s["salas_interiores"])]
    en_equip = [e for e in equipamientos if t in normalizar(e["nombre"]) or t in normalizar(e["pertenece_a"] or "")]
    return {"en_agenda": en_agenda, "en_equipamientos": en_equip}
