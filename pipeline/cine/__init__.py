"""Cartelera de cine de una ciudad (fase 6, adelantada el 17/11/2026 a petición de Uri).

Pasos:
1. Cines: datos abiertos + su web en la guía oficial (salas.py).
2. Sesiones: se leen de la web de cada cine que lo permite (lectores.py).
3. Proyecciones de la agenda del Ayuntamiento (cinefórums, ciclos en centros cívicos…):
   las actividades que la clasificación marca como «cine».
4. Películas: se juntan las sesiones de todos los cines por película y se completan con
   TMDB (cartel, sinopsis, reparto…) y los premios de Wikidata (tmdb.py).
5. Se escribe `web/public/datos/<ciudad>-cine.json` para la app y el detalle en
   `data/ciudades/<ciudad>/cine.json`.

Solo lo que se sabe: un cine cuya web no deja leer los horarios sale con su dirección y
el enlace a su web («Horarios en su web»), nunca con horarios inventados.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import re

from .. import config
from ..exportar_web import CARPETA_WEB, limpiar_titulo
from ..util import guardar_json, leer_json
from . import lectores, salas, tmdb

DIAS = 14
ATRIBUCION = "This product uses the TMDB API but is not endorsed or certified by TMDB."


def _clave(peli: dict) -> str:
    if peli.get("imdb"):
        return peli["imdb"]
    titulo = tmdb.normalizar(re.sub(r"\s*\[.*?\]\s*", " ", peli.get("titulo") or ""))
    dire = tmdb.normalizar((peli.get("direccion") or [""])[0]).split()[-1:] if peli.get("direccion") else []
    return "t:" + titulo + (":" + dire[0] if dire else "")


def _titulo_bonito(t: str) -> str:
    """«DERSU UZALA (EL CAZADOR) [WILDER CINEMA]» → «Dersu Uzala (El cazador)»."""
    t = re.sub(r"\s*\[.*?\]\s*", " ", t).strip()
    if t.isupper():
        t = t.capitalize()
    return t


def _proyecciones_agenda(ciudad: str, hoy: dt.date, fin: dt.date) -> tuple[list[dict], list[dict]]:
    """Proyecciones de la agenda abierta (tipo «cine») como (cines, sesiones)."""
    fichas = leer_json(config.carpeta_ciudad(ciudad) / "espectaculos.json", []) or []
    cines, sesiones = {}, []
    for f in fichas:
        if f.get("tipo") != "cine" or not f.get("proximas_funciones") or (f.get("confianza") or 0) < 0.6:
            continue
        nombre, artista = limpiar_titulo(f["titulo"])
        coord = f.get("coordenadas") or {}
        id_cine = f"agenda:{f.get('sala_id')}"
        direccion = f.get("direccion") or {}
        cines.setdefault(id_cine, {
            "id": id_cine, "nombre": f.get("sala") or "", "direccion": " ".join(x for x in (direccion.get("calle"), direccion.get("numero")) if x) or None,
            "barrio": direccion.get("barrio"), "lat": coord.get("lat"), "lon": coord.get("lon"), "web": None,
            "tipo": "centro", "fuente": next((x.get("url") for x in f.get("fuentes", []) if x.get("url")), None),
        })
        peli = {"titulo": nombre, "direccion": [artista] if artista else [], "agenda": f["id"],
                "descripcion": {k: v[:900] for k, v in (f.get("descripcion") or {}).items() if v},
                "imagen": f.get("imagen"), "gratis": bool((f.get("precio") or {}).get("gratis"))}
        enlace = next((x.get("url") for x in f.get("fuentes", []) if "guia" in (x.get("url") or "")), None)
        for fn in f["proximas_funciones"]:
            if hoy.isoformat() <= fn["fecha"] <= fin.isoformat():
                sesiones.append({"cine": id_cine, "pelicula": peli, "fecha": fn["fecha"], "hora": fn.get("hora"),
                                 "version": lectores.version(f["titulo"]), "sala": f.get("sala_interior"),
                                 "compra": f.get("enlace_compra") or enlace, "especial": None})
    return list(cines.values()), sesiones


def recoger(ciudad, hoy: dt.date, descargar: bool = True, leer_webs: bool = True) -> dict:
    cache = config.carpeta_cache(ciudad.id, "cine")
    fin = hoy + dt.timedelta(days=DIAS)
    informe: dict = {"fecha": hoy.isoformat(), "cines": {}}
    lista = salas.cines(cache, hoy, descargar)
    sesiones: list[dict] = []
    por_web = collections.defaultdict(list)
    for c in lista:
        if c.get("web"):
            por_web[c["web"].rstrip("/")].append(c["id"])
    for c in lista:
        if leer_webs:
            try:
                ses, como = lectores.leer(c, hoy)
            except Exception as e:  # noqa: BLE001 - una web rara no para los demás cines
                ses, como = [], f"error leyendo su web: {type(e).__name__}"
        else:
            ses, como = [], "sin leer webs hoy"
        ses = [s for s in ses if hoy.isoformat() <= s["fecha"] <= fin.isoformat()]
        c["sesiones"] = len(ses)
        c["lectura"] = como
        informe["cines"][c["nombre"]] = {"sesiones": len(ses), "como": como}
        sesiones += ses
    # Cines que comparten web: si la web publica las sesiones juntas, el otro remite al que las tiene
    for ids in por_web.values():
        con = [i for i in ids if next(c for c in lista if c["id"] == i)["sesiones"]]
        for i in ids:
            c = next(c for c in lista if c["id"] == i)
            if not c["sesiones"] and con:
                c["ver_en"] = con[0]
    cines_agenda, ses_agenda = _proyecciones_agenda(ciudad.id, hoy, fin)
    sesiones += ses_agenda
    informe["sesiones_cines"] = len(sesiones) - len(ses_agenda)
    informe["sesiones_agenda"] = len(ses_agenda)

    # Películas: juntar por película
    pelis: dict[str, dict] = {}
    for s in sesiones:
        p = s["pelicula"]
        k = _clave(p)
        actual = pelis.setdefault(k, {"titulo": p.get("titulo"), "sesiones": []})
        for campo in ("titulo_original", "imdb", "duracion", "anio", "direccion", "agenda", "descripcion", "imagen", "gratis"):
            if p.get(campo) and not actual.get(campo):
                actual[campo] = p[campo]
        actual["sesiones"].append([s["cine"], s["fecha"], s.get("hora"), s.get("version"), s.get("sala"),
                                   s.get("compra"), s.get("especial"), 1 if s.get("compra_directa") else 0])
    informe["tmdb"] = tmdb.enriquecer(pelis, cache, hoy) if descargar or leer_webs else {"aviso": "sin conexión"}
    # La misma película en cines distintos (una web da su código de IMDb y otra no): se junta.
    por_tmdb: dict[int, str] = {}
    for k in list(pelis):
        t = pelis[k].get("tmdb")
        if not t:
            continue
        if t["tmdb"] in por_tmdb:
            destino = pelis[por_tmdb[t["tmdb"]]]
            destino["sesiones"] += pelis.pop(k)["sesiones"]
        else:
            por_tmdb[t["tmdb"]] = k

    # Exportar
    cines_app = []
    for c in lista + cines_agenda:
        if c.get("tipo") != "centro" and not c.get("sesiones") and (
                not c.get("web") or (c.get("nombre_fuente") or "").lower().startswith("sala de")):
            continue  # salas de proyección dentro de otras instituciones, sin sesiones: no aportan nada
        cines_app.append({k: v for k, v in {
            "id": c["id"], "nombre": c["nombre"], "direccion": c.get("direccion"), "barrio": c.get("barrio") or c.get("distrito"),
            "lat": c.get("lat"), "lon": c.get("lon"), "web": c.get("web"), "ver_en": c.get("ver_en"),
            "centro": c.get("tipo") == "centro" or None, "fuente": c.get("fuente"),
        }.items() if v not in (None, "", [])})
    pelis_app = []
    for k, p in pelis.items():
        t = p.get("tmdb") or {}
        sesiones_p = sorted(p["sesiones"], key=lambda s: (s[1], s[2] or "99", s[0]))
        item = {
            "id": f"tmdb-{t['tmdb']}" if t else "p-" + re.sub(r"[^a-z0-9]+", "-", k.lower()).strip("-")[:60],
            "titulo": t.get("titulo") or _titulo_bonito(p["titulo"] or ""),
            "titulo_ca": t.get("titulo_ca"),
            "titulo_original": t.get("titulo_original") or p.get("titulo_original"),
            "anio": int(t["estreno"][:4]) if t.get("estreno") else p.get("anio"),
            "estreno": t.get("estreno"),
            "duracion": t.get("duracion") or p.get("duracion"),
            "generos": t.get("generos"),
            "sinopsis": t.get("sinopsis") or p.get("descripcion"),
            "lema": t.get("lema"),
            "cartel": t.get("cartel") or p.get("imagen"),
            "fondo": t.get("fondo"),
            "trailer": t.get("trailer"),
            "edad": t.get("edad"),
            "nota": t.get("nota_tmdb"),
            "paises": t.get("paises"),
            "idioma_original": t.get("idioma_original"),
            "direccion": t.get("direccion") or [{"nombre": n} for n in p.get("direccion") or []],
            "guion": t.get("guion"),
            "musica": t.get("musica"),
            "reparto": t.get("reparto"),
            "premios": t.get("premios"),
            "tmdb": t.get("tmdb"),
            "imdb": t.get("imdb") or p.get("imdb"),
            "agenda": p.get("agenda"),
            "gratis": p.get("gratis") or None,
            "sesiones": sesiones_p,
        }
        pelis_app.append({k2: v for k2, v in item.items() if v not in (None, "", [], {})})
    pelis_app.sort(key=lambda p: (-len(p["sesiones"]), p["titulo"]))
    salida = {"ciudad": ciudad.ficha(), "actualizado": hoy.isoformat(), "atribucion": ATRIBUCION,
              "cines": cines_app, "peliculas": pelis_app}
    from .. import verificar  # nada sale sin pasar las comprobaciones
    informe["verificacion"] = verificar.cine(ciudad, salida, hoy, DIAS)
    pelis_app = salida["peliculas"]
    # Lo caducado del último mes (Uri, 19/11/2026): películas que ya no tienen sesiones.
    from .. import caducados as cad
    anteriores = (leer_json(CARPETA_WEB / f"{ciudad.id}-cine.json", {}) or {}).get("peliculas", [])
    salida["caducadas"] = cad.actualizar(ciudad, "cine", hoy, anteriores, pelis_app, cad.ultima_sesion, cad.recortar_cine)
    informe["caducadas"] = len(salida["caducadas"])
    CARPETA_WEB.mkdir(parents=True, exist_ok=True)
    (CARPETA_WEB / f"{ciudad.id}-cine.json").write_text(
        json.dumps(salida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    guardar_json(config.carpeta_ciudad(ciudad.id) / "cine.json", salida)
    informe["peliculas"] = len(pelis_app)
    informe["con_tmdb"] = sum(1 for p in pelis_app if p.get("tmdb"))
    informe["con_sesiones_en_cines"] = sum(1 for c in lista if c.get("sesiones"))
    return informe
