"""Noticias de teatro, cine, magia y circo (pedido de Uri, 14/11/2026).

1. Se leen los canales RSS públicos de los medios de `ajustes/noticias.toml`.
2. La IA (tarea «noticias», un modelo barato) decide de qué va cada titular y escribe
   un resumen de una frase en castellano y en catalán, con sus palabras (no se copia el
   artículo). Lo que no es teatro, cine, magia o circo no sale.
3. Se escribe `web/public/datos/<ciudad>-noticias.json`: titular, medio, fecha, tema,
   resumen, imagen del medio y enlace al artículo original.

Cada noticia se clasifica una sola vez (caché por enlace). Se guardan las de los
últimos 10 días.
"""

from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import re
import tomllib
import urllib.request

from . import ajustes, config, ia
from .exportar_web import CARPETA_WEB
from .util import guardar_json, huella, leer_json

AGENTE = "CarteleraBarcelona/1.0"
DIAS = 10
TEMAS = ["teatro", "cine", "magia", "circo", "otro"]
ESQUEMA = {
    "type": "object",
    "properties": {"noticias": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "tema": {"type": "string", "enum": TEMAS},
            "resumen_es": {"type": "string"},
            "resumen_ca": {"type": "string"},
        },
        "required": ["id", "tema", "resumen_es", "resumen_ca"], "additionalProperties": False}}},
    "required": ["noticias"], "additionalProperties": False,
}
SISTEMA = (
    "Clasificas titulares de prensa cultural para una app de cartelera de artes escénicas y cine. "
    "Para cada noticia (id, medio, titular y entradilla) decide el tema principal: «teatro» (teatro, "
    "musicales, monólogos, títeres, ópera escenificada no; premios y festivales de teatro sí), «cine» "
    "(películas, estrenos, festivales y premios de cine, actores y directores de cine; las series de "
    "televisión no), «magia» (magos, ilusionismo, mentalismo), «circo» (circo, acrobacias, clown de circo) "
    "u «otro» (todo lo demás: música, libros, arte, series, televisión, política cultural general). "
    "Escribe un resumen neutro de una sola frase (máximo 30 palabras) en castellano y otro en catalán, "
    "con tus palabras y solo con lo que dice el titular y la entradilla: no inventes datos."
)


def _texto(s: str | None) -> str:
    s = re.sub(r"<!\[CDATA\[|\]\]>", "", s or "")
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"\s+", " ", s).strip()


def _campo(item: str, *nombres: str) -> str | None:
    for n in nombres:
        m = re.search(rf"<{n}[^>]*>(.*?)</{n}>", item, re.S)
        if m:
            return m.group(1)
    return None


def _imagen(item: str) -> str | None:
    for pat in (r'<media:content[^>]+url="([^"]+)"', r'<media:thumbnail[^>]+url="([^"]+)"',
                r'<enclosure[^>]+url="([^"]+\.(?:jpe?g|png|webp)[^"]*)"', r'<img[^>]+src="([^"]+)"', r"&lt;img[^&]+src=&quot;([^&]+)&quot;"):
        m = re.search(pat, item)
        if m:
            return html.unescape(m.group(1))
    return None


def leer_canal(fuente: dict, desde: dt.datetime) -> list[dict]:
    try:
        b = urllib.request.urlopen(urllib.request.Request(fuente["url"], headers={"User-Agent": AGENTE}), timeout=30).read()
    except Exception:  # noqa: BLE001 - un medio caído no para los demás
        return []
    texto = b.decode("utf-8", "replace")
    res = []
    for item in re.findall(r"<item[ >].*?</item>|<entry[ >].*?</entry>", texto, re.S):
        titulo = _texto(_campo(item, "title"))
        enlace = _texto(_campo(item, "link")) or (re.search(r'<link[^>]+href="([^"]+)"', item) or [None, None])[1]
        fecha_txt = _texto(_campo(item, "pubDate", "published", "updated", "dc:date"))
        try:
            fecha = email.utils.parsedate_to_datetime(fecha_txt)
        except Exception:  # noqa: BLE001
            try:
                fecha = dt.datetime.fromisoformat(fecha_txt.replace("Z", "+00:00"))
            except Exception:  # noqa: BLE001
                continue
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=dt.timezone.utc)
        if not titulo or not enlace or fecha < desde:
            continue
        res.append({"titulo": titulo, "enlace": enlace.strip(), "fecha": fecha.isoformat(),
                    "medio": fuente["nombre"], "idioma": fuente.get("idioma"),
                    "entradilla": _texto(_campo(item, "description", "summary"))[:400],
                    "imagen": _imagen(item)})
    return res


def recoger(ciudad, hoy: dt.date) -> dict:
    with open(config.RAIZ / "ajustes" / "noticias.toml", "rb") as f:
        fuentes = (tomllib.load(f).get(ciudad.id) or {}).get("fuentes", [])
    informe = {"medios": len(fuentes), "leidas": 0, "clasificadas_hoy": 0, "publicadas": 0}
    if not fuentes:
        return informe
    desde = dt.datetime.combine(hoy - dt.timedelta(days=DIAS), dt.time(), tzinfo=dt.timezone.utc)
    todas: dict[str, dict] = {}
    for fuente in fuentes:
        for n in leer_canal(fuente, desde):
            todas.setdefault(n["enlace"], n)
    informe["leidas"] = len(todas)
    ruta_cache = config.carpeta_cache(ciudad.id, "noticias") / "clasificacion.json"
    cache = {k: v for k, v in (leer_json(ruta_cache, {}) or {}).items() if k in todas}
    tarea = ajustes.tareas_ia().get("noticias")
    pendientes = [k for k in todas if k not in cache]
    if tarea and tarea.activa and ia.disponible() and pendientes:
        cli = ia.cliente()
        pendientes = pendientes[: tarea.maximo_por_ejecucion]
        for n in range(0, len(pendientes), tarea.por_peticion):
            lote = pendientes[n:n + tarea.por_peticion]
            entrada = [{"id": huella(k)[:12], "medio": todas[k]["medio"], "titular": todas[k]["titulo"],
                        "entradilla": todas[k]["entradilla"][:300]} for k in lote]
            por_id = {huella(k)[:12]: k for k in lote}
            try:
                r = ia.pedir_json(cli, tarea="noticias", modelo=tarea.modelo, esfuerzo=tarea.esfuerzo, sistema=SISTEMA,
                                  mensaje=json.dumps(entrada, ensure_ascii=False), esquema=ESQUEMA)
            except ia.TopeDeGasto as e:
                informe["aviso"] = str(e)
                break
            except Exception as e:  # noqa: BLE001
                informe.setdefault("errores", []).append(f"{type(e).__name__}: {str(e)[:150]}")
                continue
            for x in (r or {}).get("noticias", []):
                if x["id"] in por_id:
                    cache[por_id[x["id"]]] = {"tema": x["tema"], "resumen": {"es": x["resumen_es"], "ca": x["resumen_ca"]}}
                    informe["clasificadas_hoy"] += 1
        guardar_json(ruta_cache, cache)
    salida = []
    for k, n in todas.items():
        c = cache.get(k)
        if not c or c["tema"] not in ("teatro", "cine", "magia", "circo"):
            continue
        salida.append({k2: v for k2, v in {
            "titulo": n["titulo"], "enlace": n["enlace"], "medio": n["medio"], "fecha": n["fecha"],
            "idioma": n["idioma"], "tema": c["tema"], "resumen": c["resumen"], "imagen": n["imagen"],
        }.items() if v})
    salida.sort(key=lambda n: n["fecha"], reverse=True)
    informe["publicadas"] = len(salida)
    informe["por_tema"] = {t: sum(1 for n in salida if n["tema"] == t) for t in ("teatro", "cine", "magia", "circo")}
    CARPETA_WEB.mkdir(parents=True, exist_ok=True)
    (CARPETA_WEB / f"{ciudad.id}-noticias.json").write_text(
        json.dumps({"actualizado": hoy.isoformat(), "noticias": salida}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    return informe
