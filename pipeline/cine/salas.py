"""Los cines de la ciudad, descubiertos solos.

1. Datos abiertos del Ayuntamiento: equipamientos de la categoría «Cinemes», con
   dirección y coordenadas (`equipament-cultura-i-lleure`).
2. La ficha de cada uno en la guía oficial (guia.barcelona.cat) da su web. La guía
   pide 10 segundos entre páginas: se respeta, y las fichas se guardan 30 días.

Sin listas hechas a mano: si abre o cierra un cine, aparece o desaparece solo.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from ..fuentes.open_data_bcn.descargar import CATALOGO, _pedir_con_reintentos
from ..util import guardar_json, leer_json

RECURSO_EQUIPAMIENTOS = "f3721b17-bf9e-4bdd-853c-cb6200e1b442"  # equipament-cultura-i-lleure (CSV en la API)
CATEGORIA = "Cinemes"
GUIA = "https://guia.barcelona.cat/ca/detall/cinema_{id}.html"
DIAS_VALIDEZ = 30
NO_WEBS = re.compile(r"barcelona\.cat|bcn\.cat|facebook|twitter|//x\.com|instagram|youtube|google|tiktok|linkedin|"
                     r"whatsapp|addtoany|t\.me|ciutatrefugi")


def _equipamientos() -> list[dict]:
    q = urllib.parse.urlencode({
        "resource_id": RECURSO_EQUIPAMIENTOS, "limit": 1000,
        "filters": json.dumps({"secondary_filters_name": CATEGORIA}),
        "fields": "register_id,name,addresses_road_name,addresses_start_street_number,addresses_neighborhood_name,"
                  "addresses_district_name,addresses_zip_code,geo_epgs_4326_lat,geo_epgs_4326_lon",
    })
    filas = json.loads(_pedir_con_reintentos(f"{CATALOGO}/datastore_search?{q}"))["result"]["records"]
    vistos: dict[str, dict] = {}
    for f in filas:
        vistos.setdefault(f["register_id"].lstrip("﻿"), f)
    return [{**f, "register_id": k} for k, f in vistos.items()]


def _leer_guia(id_: str) -> dict:
    try:
        r = urllib.request.urlopen(urllib.request.Request(GUIA.format(id=id_)), timeout=40)
        pagina = r.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return {}
    i = pagina.find('<div id="fitxa">')
    j = pagina.find('<div id="registres-relacionats">')
    bloque = pagina[i:j if j > i else None] if i >= 0 else pagina
    webs = [w for w in dict.fromkeys(re.findall(r'href="(https?://[^"]+)"', bloque)) if not NO_WEBS.search(w)]
    titulo = re.search(r"<title>(.*?)</title>", pagina, re.S)
    nombre = html.unescape(titulo.group(1)).split("|")[0].strip() if titulo else None
    return {"web": webs[0] if webs else None, "nombre_guia": nombre}


def nombre_limpio(nombre: str, nombre_guia: str | None) -> str:
    """«Cinemes Renoir *Floridablanca» → «Renoir Floridablanca»; «Sala de Cinema - Ateneu…» → «Ateneu…»."""
    if nombre.lower().startswith("sala de") and nombre_guia and " - " in nombre_guia:
        return nombre_guia.split(" - ", 1)[1].strip()
    base, _, lugar = nombre.partition("*")
    base = re.sub(r"\s+", " ", base).strip()
    sin_prefijo = re.sub(r"^(cinemes|cinema|cines|cine)\s+", "", base, flags=re.I)
    sin_prefijo = re.sub(r"\s+multicines$", "", sin_prefijo, flags=re.I)
    if len(sin_prefijo.split()) == 1:
        # «Cinemes Girona» se queda como está (si no, parece la ciudad); «Cinema Yelmo
        # *La Maquinista» → «Yelmo La Maquinista»
        return f"{sin_prefijo} {lugar.strip()}" if lugar else base
    return sin_prefijo


def cines(carpeta_cache: Path, hoy: dt.date, descargar: bool = True) -> list[dict]:
    ruta = carpeta_cache / "salas.json"
    guardado = leer_json(ruta, {}) or {}
    fecha = guardado.get("fecha")
    if not descargar or (fecha and (hoy - dt.date.fromisoformat(fecha)).days < DIAS_VALIDEZ):
        return guardado.get("cines", [])
    try:
        filas = _equipamientos()
    except Exception:  # noqa: BLE001 - sin datos abiertos hoy: se usan los guardados
        return guardado.get("cines", [])
    antes = {c["id"]: c for c in guardado.get("cines", [])}
    res = []
    for n, f in enumerate(filas):
        id_ = f["register_id"]
        guia = antes.get(id_, {}).get("guia") if id_ in antes else None
        if guia is None:
            guia = _leer_guia(id_)
            time.sleep(10)  # robots.txt de la guía
        calle = " ".join(x for x in (f.get("addresses_road_name"), f.get("addresses_start_street_number")) if x)
        res.append({
            "id": id_,
            "nombre": nombre_limpio(f["name"], guia.get("nombre_guia")),
            "nombre_fuente": f["name"],
            "direccion": calle or None,
            "barrio": f.get("addresses_neighborhood_name"),
            "distrito": f.get("addresses_district_name"),
            "lat": float(f["geo_epgs_4326_lat"]) if f.get("geo_epgs_4326_lat") else None,
            "lon": float(f["geo_epgs_4326_lon"]) if f.get("geo_epgs_4326_lon") else None,
            "web": guia.get("web"),
            "guia": guia,
            "fuente": GUIA.format(id=id_),
        })
    guardar_json(ruta, {"fecha": hoy.isoformat(), "cines": res})
    return res
