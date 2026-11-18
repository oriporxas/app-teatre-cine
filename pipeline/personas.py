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
import re
import time
import urllib.parse

from . import config
from .cine.tmdb import _wd
from .util import guardar_json, leer_json, normalizar

DIAS_VALIDEZ = 30
MINUTOS_MAX = 8
ESPANA = "Q29"
# Profesiones de las artes escénicas y el audiovisual (Wikidata).
OFICIOS = {
    "Q33999", "Q2259451", "Q10800557", "Q10798782", "Q2405480", "Q3387717", "Q2526255", "Q3455803", "Q214917",
    "Q28389", "Q487596", "Q148401", "Q1528185", "Q10301125", "Q2401741", "Q14469390", "Q5716684", "Q2490358",
    "Q245068", "Q18545066", "Q177220", "Q36834", "Q2629392", "Q1281618", "Q1415090", "Q3282637", "Q1414443",
    "Q947873", "Q13235160", "Q2722764", "Q17351648", "Q15212951", "Q36180", "Q1930187",
}


def separar(nombres: str) -> list[str]:
    """«Anna Puig, Joan Mas i Laia Font» → [«Anna Puig», «Joan Mas», «Laia Font»] (como la app)."""
    partes = re.split(r"\s*(?:,|;|/|\s+i\s+|\s+y\s+|\s+&\s+)\s*", nombres or "")
    return [p.strip() for p in partes if 3 < len(p.strip()) < 60 and re.match(r"[A-ZÀ-Ý]", p.strip())
            and len(p.split()) <= 6 and len(p.split()) >= 2]


def clave(nombre: str) -> str:
    return normalizar(nombre).replace(" ", "-")


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
    for k, n in nombres.items():
        reg = cache.get(k)
        if reg and (hoy - dt.date.fromisoformat(reg["fecha"])).days < DIAS_VALIDEZ:
            continue
        if not leer_webs or time.monotonic() > fin:
            continue
        try:
            datos = _buscar(n)
        except RuntimeError:
            inf["aviso"] = "Wikidata no responde: el resto, otro día"
            break
        cache[k] = {"fecha": hoy.isoformat(), "nombre": n, "datos": datos or {}}
        inf["buscados_hoy"] += 1
        if inf["buscados_hoy"] % 25 == 0:
            guardar_json(ruta, cache)
        time.sleep(0.5)
    # Premios de las personas encontradas (la misma lectura de Wikidata que usa el cine).
    qids = [r["datos"]["wikidata"] for r in cache.values() if (r.get("datos") or {}).get("wikidata")]
    cache_premios = cache.setdefault("_premios", {}) if isinstance(cache.get("_premios", {}), dict) else {}
    if leer_webs and qids:
        premios_wd(qids, cache_premios)
    guardar_json(ruta, cache)
    salida = {}
    for k in nombres:
        d = (cache.get(k) or {}).get("datos") or {}
        if d.get("wikidata"):
            ficha = {x: v for x, v in d.items() if v}
            p = cache_premios.get(f"w{d['wikidata']}")
            if p:
                ficha["premios"] = p
            ficha["fuente"] = f"https://www.wikidata.org/wiki/{d['wikidata']}"
            salida[k] = ficha
    inf["encontrados"] = len(salida)
    informe["personas"] = inf
    return salida
