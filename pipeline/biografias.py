"""Fichas de las personas del cine y del teatro (Uri, 19/11/2026: «sigo sin ver los datos de las
personas del reparto de muchas obras de teatro o cine»).

Para cada persona del reparto, la dirección y el guion de las películas en cartel, y del equipo
artístico de las obras de teatro, magia y circo: foto, oficio, cuándo y dónde nació, una biografía
breve, por qué es conocida (sus trabajos más vistos) y enlaces a Wikipedia y TMDB.

Fuentes (gratis, con atribución en la app):
- **TMDB** (base de datos de cine y televisión): foto, oficio, nacimiento, biografía y trabajos.
- **Wikidata**: descripción breve en castellano y catalán, y el enlace a la Wikipedia.
  (Los textos de la Wikipedia no se copian: su servicio para programas no admite este uso desde
  aquí. La app enlaza al artículo.)

Precisión (principio 4):
- **Cine:** la persona es la que TMDB da en los créditos de la película. No se adivina nada.
- **Teatro:** un nombre se da por una persona de TMDB solo si:
  1. Wikidata ya la identificó (`personas.py`) y da su número de TMDB; o
  2. en TMDB hay **una sola** persona con ese nombre exacto, con trabajos y con un oficio que encaja
     con su papel en la obra (intérprete ↔ actuación, dirección ↔ dirección, texto ↔ guion), tiene
     relación con el país de la ciudad (nació allí o es conocida por obras en sus idiomas) y en
     Wikidata no hay varias personas con ese nombre (si las hay, es un nombre común: no se adivina).
  Si algo no encaja, la persona sale como hasta ahora: con su nombre y sus obras.

Se guarda en archivos aparte (`web/public/datos/<ciudad>-personas-<n>.json`, 16 trozos) que la app
solo descarga al abrir la ficha de una persona. Cada dato se renueva cada 60 días; cada nombre de
teatro se vuelve a buscar cada 30. Como mucho 8 minutos al día (2 en la actualización rápida).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
import unicodedata

from . import config, personas
from .cine import tmdb
from .util import guardar_json, leer_json, normalizar

DIAS_DATOS = 60
DIAS_BUSQUEDA = 30
MINUTOS_MAX = 8
TROZOS = 16
MAX_BIO = 700
MAX_CONOCIDA = 6
VERSION = 1
CARPETA_WEB = config.RAIZ / "web" / "public" / "datos"

# Oficio de TMDB que encaja con cada grupo de papeles de personas.PAPELES (mismo orden: intérpretes,
# dirección, texto, coreografía, producción). La coreografía no tiene oficio propio en TMDB.
DEPARTAMENTOS = ["Acting", "Directing", "Writing", None, "Production"]
# Cómo aparece cada país en el lugar de nacimiento de TMDB (en inglés, y a veces en el idioma local).
PAISES = {"ES": ("spain", "espana", "espanya", "espagne")}


def slug(nombre: str) -> str:
    """La misma clave que la app (web/src/Buscar.tsx: `n-${slug(nombre)}`)."""
    s = "".join(c for c in unicodedata.normalize("NFD", nombre or "") if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def trozo(clave: str) -> int:
    """En qué archivo va cada persona (la app hace la misma cuenta)."""
    return sum(ord(c) for c in clave) % TROZOS


def _bio(texto: str | None) -> str | None:
    """La biografía, cortada por una frase si es larga."""
    t = re.sub(r"\s+", " ", texto or "").strip()
    if len(t) <= MAX_BIO:
        return t or None
    corte = t.rfind(". ", 0, MAX_BIO)
    return (t[:corte + 1] if corte > 200 else t[:MAX_BIO].rsplit(" ", 1)[0] + "…")


def _conocida(creditos: dict) -> list[list]:
    """Sus trabajos más vistos: [[título, año, «película»|«serie», papel o personaje]]."""
    vistos, res = set(), []
    todos = [(c, c.get("character") or "") for c in creditos.get("cast", [])] + \
            [(c, c.get("job") or "") for c in creditos.get("crew", []) if c.get("job") in ("Director", "Screenplay", "Writer")]
    for c, papel in sorted(todos, key=lambda x: -(x[0].get("vote_count") or 0)):
        titulo = c.get("title") or c.get("name")
        if not titulo or titulo in vistos or (c.get("vote_count") or 0) < 3:
            continue
        vistos.add(titulo)
        anio = (c.get("release_date") or c.get("first_air_date") or "")[:4]
        res.append([titulo, int(anio) if anio.isdigit() else None, "serie" if c.get("media_type") == "tv" else "pelicula",
                    papel[:60]])
        if len(res) >= MAX_CONOCIDA:
            break
    return res


def detalles_tmdb(id_: int) -> dict | None:
    """Ficha de una persona en TMDB (una o dos peticiones)."""
    d = tmdb._get(f"/person/{id_}", language="es-ES", append_to_response="combined_credits,external_ids")
    if not d:
        return None
    bio, idioma = _bio(d.get("biography")), "es"
    if not bio:
        for idioma in ("ca", "en"):
            otra = tmdb._get(f"/person/{id_}", language={"ca": "ca-ES", "en": "en-US"}[idioma]) or {}
            bio = _bio(otra.get("biography"))
            if bio:
                break
    datos = {
        "tmdb": id_, "nombre": d.get("name"),
        "foto": tmdb.IMAGEN.format(tam="w185", ruta=d["profile_path"]) if d.get("profile_path") else None,
        "oficio": d.get("known_for_department"),
        "nacimiento": d.get("birthday"), "muerte": d.get("deathday"), "lugar": d.get("place_of_birth"),
        "bio": {idioma: bio} if bio else None,
        "conocida": _conocida(d.get("combined_credits") or {}),
        "wikidata": (d.get("external_ids") or {}).get("wikidata_id"),
    }
    return {k: v for k, v in datos.items() if v not in (None, [], {})}


def _encaja(papeles: set[str], departamento: str | None) -> bool:
    for (patron, _), dep in zip(personas.PAPELES, DEPARTAMENTOS):
        if dep and dep == departamento and any(patron.search(normalizar(p)) for p in papeles):
            return True
    return False


def _del_pais(datos: dict, idiomas_conocida: set[str], ciudad) -> bool:
    lugar = normalizar(datos.get("lugar") or "")
    return any(p in lugar for p in PAISES.get(ciudad.pais, ())) or bool(idiomas_conocida & set(ciudad.idiomas))


def buscar_escena(nombre: str, papeles: set[str], ciudad) -> tuple[int | None, str, dict | None]:
    """(número de TMDB, motivo, ficha) de una persona de teatro, o (None, motivo, None) si no es seguro."""
    r = tmdb._get("/search/person", query=nombre, language="es-ES")
    if r is None:
        raise RuntimeError("TMDB no responde")
    objetivo = normalizar(nombre)
    exactos = [x for x in r.get("results", []) if normalizar(x.get("name", "")) == objetivo]
    validos = [x for x in exactos if x.get("known_for") and _encaja(papeles, x.get("known_for_department"))]
    if len(validos) != 1:
        return None, "ninguna" if not validos else "varias", None
    x = validos[0]
    datos = detalles_tmdb(x["id"]) or {}
    if not _del_pais(datos, {k.get("original_language") for k in x.get("known_for", [])}, ciudad):
        return None, "otro país", None
    humanos = personas.humanos_con_nombre(nombre)
    if humanos is None:
        return None, "sin comprobar", None  # Wikidata no responde: se vuelve a mirar otro día
    if humanos > 1:
        return None, "nombre común", None
    return x["id"], "ok", datos


def aplicar(ciudad, informe: dict, leer_webs: bool = True) -> dict:
    escena = leer_json(CARPETA_WEB / f"{ciudad.id}.json", {}) or {}
    cine = leer_json(CARPETA_WEB / f"{ciudad.id}-cine.json", {}) or {}
    ruta = config.carpeta_cache(ciudad.id, "biografias") / "personas.json"
    cache = leer_json(ruta, {}) or {}
    datos_tmdb: dict = cache.setdefault("tmdb", {})
    busquedas: dict = cache.setdefault("busqueda", {})
    wd: dict = cache.setdefault("wikidata", {})
    hoy = dt.date.today()
    fin = time.monotonic() + config.tope_minutos(MINUTOS_MAX) * 60
    inf = {"cine": 0, "escena_nombres": 0, "escena_encontradas": 0, "leidas_hoy": 0, "buscadas_hoy": 0}
    viejo = lambda reg, dias: not reg or (hoy - dt.date.fromisoformat(reg["fecha"])).days >= dias  # noqa: E731
    puede = leer_webs and tmdb.disponible()

    def ficha(id_: int) -> dict | None:
        reg = datos_tmdb.get(str(id_))
        if viejo(reg, DIAS_DATOS) and puede and time.monotonic() < fin:
            d = detalles_tmdb(id_)
            if d is not None:
                reg = datos_tmdb[str(id_)] = {"fecha": hoy.isoformat(), "datos": d}
                inf["leidas_hoy"] += 1
                time.sleep(0.05)
        return (reg or {}).get("datos")

    salida: dict[str, dict] = {}
    # 1. Cine: las personas de los créditos de cada película.
    gente_cine: dict[int, str] = {}
    for p in cine.get("peliculas", []):
        for lista in ("direccion", "guion", "reparto"):
            for x in p.get(lista) or []:
                if x.get("id"):
                    gente_cine.setdefault(int(x["id"]), x.get("nombre", ""))
    inf["cine"] = len(gente_cine)
    for id_ in gente_cine:
        d = ficha(id_)
        if d:
            salida[f"t{id_}"] = d

    # 2. Teatro: los nombres del equipo artístico, con su papel.
    papeles: dict[str, set[str]] = {}
    nombres: dict[str, str] = {}
    for e in escena.get("espectaculos", []):
        for papel, gente in e.get("equipo") or []:
            for n in personas.separar(gente):
                k = slug(n)
                nombres.setdefault(k, n)
                papeles.setdefault(k, set()).add(papel)
    inf["escena_nombres"] = len(nombres)
    wikidata_escena = {k: v for k, v in (escena.get("personas") or {}).items()}  # clave de personas.py
    for k, n in nombres.items():
        reg = busquedas.get(k)
        if (viejo(reg, DIAS_BUSQUEDA) or (reg or {}).get("v") != VERSION) and puede and time.monotonic() < fin:
            try:
                id_, motivo, d = buscar_escena(n, papeles[k], ciudad)
            except RuntimeError:
                inf["aviso"] = "TMDB no responde: el resto, otro día"
                puede = False
                continue
            inf["buscadas_hoy"] += 1
            if motivo != "sin comprobar":
                reg = busquedas[k] = {"fecha": hoy.isoformat(), "v": VERSION, "nombre": n, "tmdb": id_, "motivo": motivo}
            if d:
                datos_tmdb[str(id_)] = {"fecha": hoy.isoformat(), "datos": d}
            time.sleep(0.05)
        id_ = (reg or {}).get("tmdb")
        d = ficha(id_) if id_ else None
        w = wikidata_escena.get(personas.clave(n))
        if d or w:
            ficha_ = dict(d or {"nombre": n})
            if w:  # lo que ya sabe Wikidata (personas.py): descripción y Wikipedia
                ficha_.setdefault("wikidata", w.get("wikidata"))
                if w.get("descripcion"):
                    ficha_["descripcion"] = w["descripcion"]
                if w.get("wikipedia"):
                    ficha_["wikipedia"] = w["wikipedia"]
            salida[f"n-{k}"] = ficha_
            inf["escena_encontradas"] += 1

    # 3. Descripción breve y Wikipedia desde Wikidata, para quien la tenga (de 50 en 50).
    qids = sorted({f["wikidata"] for f in salida.values() if f.get("wikidata")})
    pendientes = [q for q in qids if viejo(wd.get(q), DIAS_DATOS)]
    if pendientes and leer_webs and time.monotonic() < fin:
        for q, info in personas.detalles(pendientes).items():
            wd[q] = {"fecha": hoy.isoformat(), "descripcion": info.get("descripcion"), "wikipedia": info.get("wikipedia")}
    for f in salida.values():
        info = wd.get(f.get("wikidata") or "")
        if info:
            f.setdefault("descripcion", info.get("descripcion"))
            f.setdefault("wikipedia", info.get("wikipedia"))
        for x in [x for x, v in f.items() if v in (None, [], {})]:
            del f[x]
    guardar_json(ruta, cache)

    # 4. Archivos de la app, en trozos (la app descarga solo el de la persona que abre).
    trozos: list[dict] = [{} for _ in range(TROZOS)]
    for clave_, f in salida.items():
        trozos[trozo(clave_)][clave_] = f
    CARPETA_WEB.mkdir(parents=True, exist_ok=True)
    for n, t in enumerate(trozos):
        (CARPETA_WEB / f"{ciudad.id}-personas-{n}.json").write_text(
            json.dumps({"actualizado": hoy.isoformat(), "personas": t}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
    inf["con_ficha"] = len(salida)
    informe["biografias"] = inf
    return inf
