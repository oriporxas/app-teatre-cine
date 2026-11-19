"""Datos de cada película: TMDB (The Movie Database) y premios de Wikidata.

- TMDB: cartel, imagen de fondo, sinopsis en castellano y catalán, géneros, duración,
  dirección, guion, reparto, tráiler, calificación por edades en España, IMDb y Wikidata.
  La clave es el secreto TMDB_TOKEN («API Read Access Token»). En las sesiones de Claude
  en la nube la pone la red: allí se ejecuta con TMDB_TOKEN=proxy-injected.
  Atribución obligatoria: «This product uses the TMDB API but is not endorsed or
  certified by TMDB» (la app la muestra en «Acerca de»).
- Wikidata (datos abiertos, CC0): premios ganados (P166) y nominaciones (P1411) de la
  película y de su dirección y reparto principal, con el año.
- Identificar bien la película (principio 4): por su código de IMDb cuando la web del cine
  lo da; si no, por título y año, y comprobando que la dirección coincide. Si no hay
  seguridad, la película sale con los datos del cine y sin TMDB.
- Todo se guarda en caché (cache/cine/tmdb.json): cada película se consulta una vez y se
  refresca cada 14 días.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import urllib.error
import re
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from ..util import guardar_json, leer_json

API = "https://api.themoviedb.org/3"
IMAGEN = "https://image.tmdb.org/t/p/{tam}{ruta}"
WIKIDATA = "https://www.wikidata.org/w/api.php"
AGENTE = "CarteleraBarcelona/1.0 (proyecto personal sin animo de lucro)"
DIAS_VALIDEZ = 14
REPARTO = 10


def disponible() -> bool:
    return bool(os.environ.get("TMDB_TOKEN"))


def _get(ruta: str, **params) -> dict | None:
    url = f"{API}{ruta}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.environ.get('TMDB_TOKEN', '')}",
                                               "accept": "application/json", "User-Agent": AGENTE})
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                time.sleep(2 + 3 * intento)
                continue
            if e.code in (401, 403):
                raise RuntimeError("TMDB rechaza la clave (TMDB_TOKEN)") from e
            time.sleep(1 + intento)
        except Exception:  # noqa: BLE001
            time.sleep(1 + intento)
    return None


def normalizar(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"\[.*?\]", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _variantes_titulo(titulo: str) -> list[str]:
    """«DERSU UZALA (EL CAZADOR) [WILDER CINEMA]» → «DERSU UZALA (EL CAZADOR)», «DERSU UZALA»."""
    base = re.sub(r"\s*\[.*?\]\s*", " ", titulo).strip()
    res = [base]
    sin_parentesis = re.sub(r"\s*\(.*?\)\s*", " ", base).strip()
    if sin_parentesis and sin_parentesis != base:
        res.append(sin_parentesis)
    return res


def _palabras_nombres(nombres: list[str]) -> set[str]:
    """Palabras de los nombres (sirve con «Martin McDonagh», «McDonagh, Martin» o «Mcdonagh Martin»)."""
    return {w for n in nombres for w in normalizar(n).split() if len(w) > 2}


def _parecido(a: str, b: str) -> float:
    import difflib
    return difflib.SequenceMatcher(None, normalizar(a), normalizar(b)).ratio()


def identificar(peli: dict, hoy: dt.date) -> int | None:
    """Id de TMDB de la película, solo si es seguro."""
    if peli.get("imdb"):
        r = _get(f"/find/{peli['imdb']}", external_source="imdb_id")
        if r and r.get("movie_results"):
            return r["movie_results"][0]["id"]
    direccion = _palabras_nombres(peli.get("direccion") or [])
    for titulo in _variantes_titulo(peli.get("titulo") or ""):
        r = _get("/search/movie", query=titulo, language="es-ES", region="ES", include_adult="false")
        resultados = (r or {}).get("results", [])[:8]
        candidatos = [m for m in resultados
                      if normalizar(titulo) in (normalizar(m.get("title")), normalizar(m.get("original_title")))]
        if direccion:
            # Con la dirección se acepta un título casi igual («La violinista» / «El violinista»),
            # pero la dirección tiene que coincidir.
            parecidos = [m for m in resultados if m not in candidatos and max(
                _parecido(titulo, m.get("title") or ""), _parecido(titulo, m.get("original_title") or "")) >= 0.8]
            for m in candidatos + parecidos:
                cr = _get(f"/movie/{m['id']}/credits")
                dirs = [c["name"] for c in (cr or {}).get("crew", []) if c.get("job") == "Director"]
                comunes = direccion & _palabras_nombres(dirs)
                if len(comunes) >= 2 or (comunes and len(direccion) <= 2):
                    return m["id"]
            continue
        if not candidatos:
            continue
        # sin dirección: solo si hay un único candidato reciente (estrenado en los últimos 3 años)
        recientes = [m for m in candidatos if (m.get("release_date") or "0")[:4].isdigit()
                     and int((m.get("release_date") or "0")[:4]) >= hoy.year - 3]
        if len(recientes) == 1:
            return recientes[0]["id"]
    return None


def ficha(id_tmdb: int) -> dict | None:
    d = _get(f"/movie/{id_tmdb}", language="es-ES",
             append_to_response="credits,videos,translations,release_dates,external_ids",
             include_video_language="es,ca,en,null")
    if not d:
        return None
    traducciones = {t["iso_639_1"]: t.get("data") or {} for t in (d.get("translations") or {}).get("translations", [])}
    ca = traducciones.get("ca", {})
    en = traducciones.get("en", {})
    creditos = d.get("credits") or {}
    equipo = creditos.get("crew", [])
    videos = [v for v in (d.get("videos") or {}).get("results", []) if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser")]
    videos.sort(key=lambda v: ({"es": 0, "ca": 1, "en": 2}.get(v.get("iso_639_1"), 3), v.get("type") != "Trailer", not v.get("official")))
    edad = None
    for r in (d.get("release_dates") or {}).get("results", []):
        if r.get("iso_3166_1") == "ES":
            edad = next((x.get("certification") for x in r.get("release_dates", []) if x.get("certification")), None)
    persona = lambda c: {"id": c["id"], "nombre": c["name"], **({"foto": IMAGEN.format(tam="w185", ruta=c["profile_path"])} if c.get("profile_path") else {})}  # noqa: E731
    return {
        "tmdb": d["id"],
        "titulo": d.get("title"),
        "titulo_ca": ca.get("title") or None,
        "titulo_original": d.get("original_title"),
        "idioma_original": d.get("original_language"),
        "sinopsis": {k: v for k, v in {"es": d.get("overview"), "ca": ca.get("overview"), "en": en.get("overview")}.items() if v},
        "lema": d.get("tagline") or None,
        "generos": [g["name"] for g in d.get("genres", [])],
        "duracion": d.get("runtime") or None,
        "estreno": d.get("release_date") or None,
        "paises": [p["iso_3166_1"] for p in d.get("production_countries", [])],
        "cartel": IMAGEN.format(tam="w500", ruta=d["poster_path"]) if d.get("poster_path") else None,
        "fondo": IMAGEN.format(tam="w1280", ruta=d["backdrop_path"]) if d.get("backdrop_path") else None,
        "trailer": videos[0]["key"] if videos else None,
        "edad": edad,
        "nota_tmdb": round(d["vote_average"], 1) if d.get("vote_count", 0) >= 50 else None,
        "direccion": [persona(c) for c in equipo if c.get("job") == "Director"],
        "guion": [persona(c) for c in equipo if c.get("job") in ("Screenplay", "Writer", "Novel", "Story")][:4],
        "musica": [persona(c) for c in equipo if c.get("job") == "Original Music Composer"][:2],
        "reparto": [persona(c) | ({"papel": c["character"]} if c.get("character") else {})
                    for c in creditos.get("cast", [])[:REPARTO]],
        "imdb": (d.get("external_ids") or {}).get("imdb_id") or d.get("imdb_id"),
        "wikidata": (d.get("external_ids") or {}).get("wikidata_id"),
    }


def wikidata_personas(ids_tmdb: list[int], cache: dict) -> dict[int, str]:
    """Id de Wikidata de cada persona (desde TMDB)."""
    res = {}
    for i in ids_tmdb:
        clave = f"p{i}"
        if clave not in cache:
            r = _get(f"/person/{i}/external_ids")
            cache[clave] = (r or {}).get("wikidata_id") or ""
        if cache[clave]:
            res[i] = cache[clave]
    return res


_WD_SATURADO = False
CERROJO_WIKIDATA = threading.RLock()


def _wd(**params) -> dict | None:
    """Petición a la API de Wikidata. Si Wikidata pide ir más despacio (429), se espera lo que
    diga y, si sigue saturado, se deja para la próxima ejecución (la caché guarda lo hecho)."""
    with CERROJO_WIKIDATA:  # de una en una, como pide Wikidata (el cine y la escena van en paralelo)
        return _wd_sin_cerrojo(**params)


def _wd_sin_cerrojo(**params) -> dict | None:
    global _WD_SATURADO
    if _WD_SATURADO:
        return None
    url = f"{WIKIDATA}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENTE}), timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                espera = min(int(e.headers.get("Retry-After") or 30), 90)
                time.sleep(espera)
                continue
            time.sleep(2 + 2 * intento)
        except Exception:  # noqa: BLE001
            time.sleep(2 + 2 * intento)
    _WD_SATURADO = True
    return None


def premios(qids: list[str], cache: dict) -> dict[str, list[dict]]:
    """{qid: [{"premio", "anio", "tipo": "ganado"|"nominado", "fuente"}]} desde Wikidata."""
    pendientes = [q for q in dict.fromkeys(qids) if q and f"w{q}" not in cache]
    for n in range(0, len(pendientes), 40):
        lote = pendientes[n:n + 40]
        respuesta = _wd(action="wbgetentities", ids="|".join(lote), props="claims")
        if respuesta is None:
            break  # Wikidata no responde hoy: lo pendiente, otro día
        ents = respuesta.get("entities", {})
        crudo = {}
        for q in lote:
            claims = (ents.get(q) or {}).get("claims", {})
            lista = []
            for prop, tipo in (("P166", "ganado"), ("P1411", "nominado")):
                for c in claims.get(prop, []):
                    v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
                    if not v.get("id"):
                        continue
                    anio = None
                    for qual in (c.get("qualifiers") or {}).get("P585", []):
                        t = ((qual.get("datavalue") or {}).get("value") or {}).get("time", "")
                        if t[1:5].isdigit():
                            anio = int(t[1:5])
                    lista.append({"q": v["id"], "anio": anio, "tipo": tipo})
            crudo[q] = lista
        # nombres de los premios, en castellano (o catalán, o inglés)
        qs_premios = sorted({p["q"] for l in crudo.values() for p in l})
        nombres = {}
        for m in range(0, len(qs_premios), 45):
            ents2 = (_wd(action="wbgetentities", ids="|".join(qs_premios[m:m + 45]), props="labels",
                         languages="es|ca|en") or {}).get("entities", {})
            for qq, e in ents2.items():
                lab = e.get("labels", {})
                nombres[qq] = next((lab[l]["value"] for l in ("es", "ca", "en") if l in lab), None)
        if qs_premios and not nombres:
            break  # sin nombres no se guarda nada: se reintenta otro día
        for q, lista in crudo.items():
            vistos: dict = {}
            for p in lista:
                nombre = re.sub(r"^(Anexo|Annex):\s*", "", nombres.get(p["q"]) or "").strip()
                if not nombre:
                    continue
                clave = (nombre.lower(), p["tipo"], p["anio"])
                sin_anio = (nombre.lower(), p["tipo"], None)
                if p["anio"] is None and any(k[:2] == clave[:2] for k in vistos):
                    continue  # ya está con su año
                vistos.pop(sin_anio, None)
                vistos[clave] = {"premio": nombre[:1].upper() + nombre[1:], "anio": p["anio"], "tipo": p["tipo"]}
            cache[f"w{q}"] = list(vistos.values())
        time.sleep(2)
    return {q: cache.get(f"w{q}", []) for q in qids if q}


def enriquecer(pelis: dict[str, dict], carpeta_cache: Path, hoy: dt.date) -> dict:
    """Añade a cada película (clave interna → datos de la web) su ficha de TMDB y sus premios."""
    ruta = carpeta_cache / "tmdb.json"
    cache = leer_json(ruta, {}) or {}
    informe = {"peliculas": len(pelis), "identificadas": 0, "sin_identificar": []}
    hay_clave = disponible()
    if not hay_clave:
        informe["aviso"] = "sin clave de TMDB: solo se usa lo que ya estaba guardado"
    for clave, peli in pelis.items():
        reg = cache.get(f"i{clave}")
        if hay_clave and (not reg or (hoy - dt.date.fromisoformat(reg["fecha"])).days >= DIAS_VALIDEZ):
            id_ = identificar(peli, hoy)
            datos = ficha(id_) if id_ else None
            reg = {"fecha": hoy.isoformat(), "datos": datos}
            cache[f"i{clave}"] = reg
        if reg and reg["datos"]:
            peli["tmdb"] = reg["datos"]
            informe["identificadas"] += 1
        else:
            informe["sin_identificar"].append(peli.get("titulo"))
    guardar_json(ruta, cache)
    # Premios: película, dirección y las 4 primeras personas del reparto
    personas = {p["id"] for peli in pelis.values() if peli.get("tmdb")
                for p in peli["tmdb"]["direccion"] + peli["tmdb"]["reparto"][:4]}
    qid_persona = wikidata_personas(sorted(personas), cache) if hay_clave else {
        p: cache[f"p{p}"] for p in personas if cache.get(f"p{p}")}
    qids = [peli["tmdb"]["wikidata"] for peli in pelis.values() if peli.get("tmdb") and peli["tmdb"].get("wikidata")]
    todos = premios(qids + list(qid_persona.values()), cache)
    guardar_json(ruta, cache)
    for peli in pelis.values():
        t = peli.get("tmdb")
        if not t:
            continue
        if t.get("wikidata"):
            t["premios"] = todos.get(t["wikidata"], [])
        for p in t["direccion"] + t["reparto"][:4]:
            q = qid_persona.get(p["id"])
            if q:
                p["wikidata"] = q
                p["premios"] = todos.get(q, [])
    informe["con_premios"] = sum(1 for p in pelis.values() if (p.get("tmdb") or {}).get("premios"))
    return informe
