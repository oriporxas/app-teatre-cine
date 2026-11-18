"""Personas del equipo artístico de las obras: foto, a qué se dedican y premios, desde Wikidata
(la base de datos libre de Wikipedia; gratis). Uri, 18/11/2026.

Precisión ante todo: un nombre se da por la misma persona solo si en Wikidata hay **una única**
persona con ese nombre exacto (o alias) que se dedica a las artes escénicas o al audiovisual
(actriz, director, dramaturga, mago, payaso, bailarín…) y es de nacionalidad española. Si hay dos
posibles, o ninguna, no se pone nada. Las compañías y los nombres poco conocidos no suelen estar:
su ficha sale solo con sus obras, como hasta ahora.

Cada nombre se busca una vez y se guarda 30 días. Como mucho 8 minutos al día (al principio tarda
unos días en completarse). Las fotos son de Wikimedia Commons (licencias libres).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from . import config
from .cine.tmdb import _wd
from .util import guardar_json, leer_json, normalizar

DIAS_VALIDEZ = 30
VERSION = 2  # sube cuando cambia la lista de oficios: los nombres se vuelven a buscar
MINUTOS_MAX = 8
ESPANA = "Q29"
# Oficios de la escena y el audiovisual (Wikidata). Solo oficios propios del escenario: «escritor»,
# «cantante» o «compositor» dejaban pasar a tocayos de otros campos (error del 18/11/2026: el
# músico Jordi Cornudella recibió la ficha de un poeta con el mismo nombre).
OFICIOS = {  # comprobados uno a uno en Wikidata el 18/11/2026
    "Q33999",     # actor / actriz
    "Q2259451",   # actor de teatro
    "Q10800557",  # actor de cine
    "Q10798782",  # actor de televisión
    "Q2405480",   # actor de voz
    "Q3387717",   # director de escena
    "Q2526255",   # director de cine
    "Q214917",    # dramaturgo
    "Q487596",    # dramaturgista
    "Q1759246",   # productor teatral
    "Q15855449",  # mago (espectáculo)
    "Q1658894",   # ilusionista
    "Q19805041",  # mentalista
    "Q16746942",  # hipnotizador
    "Q15618890",  # ventrílocuo
    "Q7358",      # payaso
    "Q17307272",  # artista de circo
    "Q11957145",  # acróbata
    "Q3997657",   # trapecista
    "Q10540773",  # malabarista
    "Q19828939",  # contorsionista
    "Q5716684",   # bailarín
    "Q2490358",   # coreógrafo
    "Q245068",    # humorista
    "Q18545066",  # monologuista
    "Q2629392",   # titiritero
    "Q10774753",  # artista de performance
}


def separar(nombres: str) -> list[str]:
    """«Anna Puig, Joan Mas i Laia Font» → [«Anna Puig», «Joan Mas», «Laia Font»] (como la app)."""
    partes = re.split(r"\s*(?:,|;|/|\s+i\s+|\s+y\s+|\s+&\s+)\s*", nombres or "")
    return [p.strip() for p in partes if 3 < len(p.strip()) < 60 and re.match(r"[A-ZÀ-Ý]", p.strip())
            and len(p.split()) <= 6 and len(p.split()) >= 2]


def clave(nombre: str) -> str:
    return normalizar(nombre).replace(" ", "-")


SPARQL = "https://query.wikidata.org/sparql"
AGENTE = "CarteleraBarcelona/1.0 (cartelera de artes escénicas; uso personal)"
POR_LOTE = 40


def _sparql(consulta: str) -> dict | None:
    url = f"{SPARQL}?{urllib.parse.urlencode({'query': consulta, 'format': 'json'})}"
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENTE,
                                                                             "Accept": "application/sparql-results+json"}), timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            espera = int(e.headers.get("Retry-After") or 10) if e.code == 429 else 5 * (intento + 1)
            if espera > 60:  # nos piden parar un buen rato: se sigue nombre a nombre (más lento)
                return None
            time.sleep(espera)
        except Exception:  # noqa: BLE001
            time.sleep(5 * (intento + 1))
    return None


def candidatos_lote(nombres: list[str]) -> dict[str, set[str]] | None:
    """{nombre normalizado: personas de Wikidata con ese nombre exacto (o alias), españolas y de las artes}.
    Una sola consulta para muchos nombres (mucho más rápido que buscarlos uno a uno)."""
    esc = lambda n: n.replace("\\", "").replace('"', '\\"')  # noqa: E731
    valores = " ".join(f'"{esc(n)}"@{l}' for n in nombres for l in ("es", "ca", "en"))
    oficios = " ".join(f"wd:{o}" for o in sorted(OFICIOS))
    consulta = (f"SELECT DISTINCT ?item ?nombre WHERE {{ VALUES ?nombre {{ {valores} }} "
                "?item rdfs:label|skos:altLabel ?nombre . ?item wdt:P31 wd:Q5 . "
                f"FILTER EXISTS {{ ?item wdt:P27 wd:{ESPANA} }} "
                f"FILTER EXISTS {{ VALUES ?o {{ {oficios} }} ?item wdt:P106 ?o }} }}")
    r = _sparql(consulta)
    if r is None:
        return None
    res: dict[str, set[str]] = {}
    for b in r.get("results", {}).get("bindings", []):
        res.setdefault(normalizar(b["nombre"]["value"]), set()).add(b["item"]["value"].rsplit("/", 1)[-1])
    return res


def detalles(qids: list[str]) -> dict[str, dict]:
    """Foto, descripción y Wikipedia de cada persona (de 50 en 50)."""
    res = {}
    for n in range(0, len(qids), 50):
        r = _wd(action="wbgetentities", ids="|".join(qids[n:n + 50]), props="descriptions|claims|sitelinks", languages="es|ca")
        for q, e in ((r or {}).get("entities") or {}).items():
            claims = e.get("claims") or {}
            foto = next((((c.get("mainsnak") or {}).get("datavalue") or {}).get("value") for c in claims.get("P18", [])), None)
            desc = {l: e["descriptions"][l]["value"] for l in ("es", "ca") if l in (e.get("descriptions") or {})}
            sitios = e.get("sitelinks") or {}
            wiki = next((f"https://{l[:2]}.wikipedia.org/wiki/{urllib.parse.quote(sitios[l]['title'].replace(' ', '_'))}"
                         for l in ("eswiki", "cawiki") if l in sitios), None)
            oficios = sorted({((c.get("mainsnak") or {}).get("datavalue") or {}).get("value", {}).get("id") for c in claims.get("P106", [])} - {None})
            res[q] = {"wikidata": q, "descripcion": desc or None, "wikipedia": wiki, "oficios": oficios,
                      "foto": f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(foto.replace(' ', '_'))}?width=300" if foto else None}
    return res


def _buscar(nombre: str) -> dict | None:
    """La ficha de Wikidata de esa persona, o None si no hay una única coincidencia segura."""
    candidatos: list[str] = []
    for idioma in ("es", "ca"):
        r = _wd(action="wbsearchentities", search=nombre, language=idioma, type="item", limit=7)
        if r is None:
            raise RuntimeError("Wikidata no responde")
        candidatos += [x["id"] for x in r.get("search", []) if x.get("id") not in candidatos]
    if not candidatos:
        return {}
    r = _wd(action="wbgetentities", ids="|".join(candidatos[:14]), props="labels|aliases|descriptions|claims|sitelinks",
            languages="es|ca|en")
    if r is None:
        raise RuntimeError("Wikidata no responde")
    buenos = []
    objetivo = normalizar(nombre)
    for q, e in (r.get("entities") or {}).items():
        claims = e.get("claims") or {}
        valores = lambda p: {((c.get("mainsnak") or {}).get("datavalue") or {}).get("value", {}).get("id") for c in claims.get(p, [])}  # noqa: E731
        nombres = {normalizar(v["value"]) for v in (e.get("labels") or {}).values()}
        nombres |= {normalizar(a["value"]) for l in (e.get("aliases") or {}).values() for a in l}
        if "Q5" in valores("P31") and objetivo in nombres and valores("P106") & OFICIOS and ESPANA in valores("P27"):
            buenos.append((q, e))
    if len(buenos) != 1:
        return {}  # ninguna o varias personas posibles: no se adivina
    q, e = buenos[0]
    claims = e.get("claims") or {}
    foto = next((((c.get("mainsnak") or {}).get("datavalue") or {}).get("value") for c in claims.get("P18", [])), None)
    desc = {l: e["descriptions"][l]["value"] for l in ("es", "ca") if l in (e.get("descriptions") or {})}
    sitios = e.get("sitelinks") or {}
    wiki = next((f"https://{l[:2]}.wikipedia.org/wiki/{urllib.parse.quote(sitios[l]['title'].replace(' ', '_'))}"
                 for l in ("eswiki", "cawiki") if l in sitios), None)
    return {
        "wikidata": q,
        "oficios": sorted(valores("P106") - {None}),
        "foto": f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(foto.replace(' ', '_'))}?width=300" if foto else None,
        "descripcion": desc or None,
        "wikipedia": wiki,
    }


def aplicar(ciudad, items: list[dict], informe: dict, leer_webs: bool = True) -> dict:
    """Devuelve {clave del nombre: ficha} para la app (solo las personas encontradas)."""
    from .cine.tmdb import premios as premios_wd
    ruta = config.carpeta_cache(ciudad.id, "personas") / "wikidata.json"
    cache = leer_json(ruta, {}) or {}
    hoy = dt.date.today()
    fin = time.monotonic() + MINUTOS_MAX * 60
    nombres: dict[str, str] = {}
    for it in items:
        for _, gente in it.get("equipo") or []:
            for n in separar(gente):
                nombres.setdefault(clave(n), n)
    inf = {"nombres": len(nombres), "buscados_hoy": 0, "encontrados": 0}
    pendientes = [(k, n) for k, n in nombres.items()
                  if not (cache.get(k) and cache[k].get("v") == VERSION
                          and (hoy - dt.date.fromisoformat(cache[k]["fecha"])).days < DIAS_VALIDEZ)]
    for i in range(0, len(pendientes), POR_LOTE):
        if not leer_webs or time.monotonic() > fin:
            break
        lote = pendientes[i:i + POR_LOTE]
        encontrados = candidatos_lote([n for _, n in lote]) if not inf.get("uno_a_uno") else None
        if encontrados is None:  # la consulta por grupos no va: nombre a nombre, hasta que se acabe el tiempo
            inf["uno_a_uno"] = True
            try:
                for k, n in lote:
                    if time.monotonic() > fin:
                        break
                    cache[k] = {"fecha": hoy.isoformat(), "v": VERSION, "nombre": n, "datos": _buscar(n) or {}}
                    inf["buscados_hoy"] += 1
                    time.sleep(0.5)
            except RuntimeError:
                inf["aviso"] = "Wikidata no responde: el resto, otro día"
                break
            guardar_json(ruta, cache)
            continue
        unicos = {k: next(iter(encontrados[normalizar(n)])) for k, n in lote if len(encontrados.get(normalizar(n), ())) == 1}
        info = detalles(sorted(set(unicos.values())))
        for k, n in lote:  # una sola persona posible: esa; ninguna o varias: nada (no se adivina)
            cache[k] = {"fecha": hoy.isoformat(), "v": VERSION, "nombre": n,
                        "datos": info.get(unicos.get(k), {}) if k in unicos else {}}
        inf["buscados_hoy"] += len(lote)
        guardar_json(ruta, cache)
        time.sleep(1)
    # Las fichas guardadas sin sus oficios (de antes del 18/11/2026) se comprueban otra vez.
    sin_oficios = sorted({r["datos"]["wikidata"] for k, r in cache.items() if k != "_premios"
                          and (r.get("datos") or {}).get("wikidata") and "oficios" not in r["datos"]})
    if sin_oficios and leer_webs:
        nuevos = detalles(sin_oficios)
        for k, r in cache.items():
            q = (r.get("datos") or {}).get("wikidata") if k != "_premios" else None
            if q in nuevos:
                r["datos"] = nuevos[q]
    # Premios de las personas encontradas (la misma lectura de Wikidata que usa el cine).
    qids = [r["datos"]["wikidata"] for r in cache.values() if (r.get("datos") or {}).get("wikidata")]
    cache_premios = cache.setdefault("_premios", {}) if isinstance(cache.get("_premios", {}), dict) else {}
    if leer_webs and qids:
        premios_wd(qids, cache_premios)
    guardar_json(ruta, cache)
    salida = {}
    for k in nombres:
        d = (cache.get(k) or {}).get("datos") or {}
        if d.get("wikidata") and set(d.get("oficios") or []) & OFICIOS:  # solo oficios de escena (ver arriba)
            ficha = {x: v for x, v in d.items() if v and x != "oficios"}
            p = cache_premios.get(f"w{d['wikidata']}")
            if p:
                ficha["premios"] = p
            ficha["fuente"] = f"https://www.wikidata.org/wiki/{d['wikidata']}"
            salida[k] = ficha
    inf["encontrados"] = len(salida)
    informe["personas"] = inf
    return salida
