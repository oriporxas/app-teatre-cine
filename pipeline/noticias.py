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
AMBITOS = ["barcelona", "espana", "mundo"]
MAXIMO_APP = 600  # noticias que se guardan para la app (las más recientes)
ESQUEMA = {
    "type": "object",
    "properties": {"noticias": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "tema": {"type": "string", "enum": TEMAS},
            "evento": {"type": "boolean"},
            "ambito": {"type": "string", "enum": AMBITOS},
            "titulo_es": {"type": "string"},
            "titulo_ca": {"type": "string"},
            "resumen_es": {"type": "string"},
            "resumen_ca": {"type": "string"},
        },
        "required": ["id", "tema", "evento", "ambito", "titulo_es", "titulo_ca", "resumen_es", "resumen_ca"],
        "additionalProperties": False}}},
    "required": ["noticias"], "additionalProperties": False,
}
SISTEMA = (
    "Clasificas titulares de prensa cultural para una app de cartelera de artes escénicas y cine. "
    "Para cada noticia (id, medio, titular y entradilla) decide el tema principal: «teatro» (teatro, "
    "musicales, monólogos, títeres, ópera escenificada no; premios y festivales de teatro sí), «cine» "
    "(películas, estrenos, festivales y premios de cine, actores y directores de cine; las series de "
    "televisión no), «magia» (magos, ilusionismo, mentalismo), «circo» (circo, acrobacias, clown de circo) "
    "u «otro» (todo lo demás: música, libros, arte, danza, series, televisión, política cultural general). "
    "«evento»: true solo si la noticia trata de un evento concreto de ese tema: festival, muestra o ciclo, gala o "
    "entrega de premios, feria, convención o congreso, taller o curso; false para estrenos, críticas, entrevistas, "
    "obituarios y noticias del sector. "
    "«ambito»: de dónde es lo que cuenta la noticia: «barcelona» (Barcelona o Cataluña), «espana» (el resto de España) "
    "o «mundo» (fuera de España). Te doy el ámbito del medio como pista, pero manda el contenido. "
    "«titulo_es» y «titulo_ca»: el titular en castellano y en catalán (traducido fielmente si está en otro idioma; "
    "si ya está en ese idioma, igual). "
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
    from .cine import red  # respeta robots.txt y las pausas de cada web
    b = red.pedir(fuente["url"], timeout=30)
    if not b:  # medio caído o que no deja leer su canal: no para los demás
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
                    "medio": fuente["nombre"], "idioma": fuente.get("idioma"), "ambito": fuente.get("ambito"),
                    "entradilla": _texto(_campo(item, "description", "summary"))[:400],
                    "imagen": _imagen(item)})
    return res


def _anotar(cache: dict, r: dict | None, por_id: dict[str, str]) -> int:
    """Guarda en la caché lo que la IA dice de cada noticia. Devuelve cuántas."""
    n = 0
    for x in (r or {}).get("noticias", []):
        if x.get("id") in por_id:
            cache[por_id[x["id"]]] = {"tema": x["tema"], "evento": bool(x.get("evento")), "ambito": x.get("ambito"),
                                      "titulo": {"es": x.get("titulo_es"), "ca": x.get("titulo_ca")},
                                      "resumen": {"es": x["resumen_es"], "ca": x["resumen_ca"]}}
            n += 1
    return n


def _entrada(k: str, n: dict) -> dict:
    return {"id": huella(k)[:12], "medio": n["medio"], "ambito_del_medio": n.get("ambito"),
            "titular": n["titulo"], "entradilla": n["entradilla"][:300]}


def _por_lotes(tarea, todas: dict, pendientes: list[str], cache: dict, carpeta, informe: dict) -> None:
    """Las noticias nuevas, por lotes (mitad de precio). Si la respuesta llega otro día, se usa igual:
    una noticia no cambia."""
    lotes = ia.Lotes("noticias", carpeta)
    en_curso = {k for d in lotes.datos_en_curso() for k in (d or {}).values()}
    nuevas = [k for k in pendientes if k not in en_curso][: tarea.maximo_por_ejecucion]
    peticiones = {}
    for n in range(0, len(nuevas), tarea.por_peticion):
        lote = nuevas[n:n + tarea.por_peticion]
        peticiones[str(n)] = (json.dumps([_entrada(k, todas[k]) for k in lote], ensure_ascii=False),
                              {huella(k)[:12]: k for k in lote})
    try:
        lotes.enviar(None, modelo=tarea.modelo, esfuerzo=tarea.esfuerzo, sistema=SISTEMA, esquema=ESQUEMA,
                     peticiones=peticiones)
        lotes.esperar()
    except ia.TopeDeGasto as e:
        informe["aviso"] = str(e)
    except Exception as e:  # noqa: BLE001 - sin lotes hoy: las noticias nuevas se piden mañana
        informe.setdefault("errores", []).append(f"lotes: {type(e).__name__}: {str(e)[:150]}")
    for r, por_id in lotes.recogidas:
        informe["clasificadas_hoy"] += _anotar(cache, r, por_id or {})
    informe["lotes"] = {k: v for k, v in lotes.informe.items() if k in ("enviadas", "recogidas", "en_curso", "repetidas_normal", "errores")}


def recoger(ciudad, hoy: dt.date) -> dict:
    with open(config.RAIZ / "ajustes" / "noticias.toml", "rb") as f:
        fuentes = (tomllib.load(f).get(ciudad.id) or {}).get("fuentes", [])
    informe = {"medios": len(fuentes), "leidas": 0, "clasificadas_hoy": 0, "publicadas": 0}
    if not fuentes:
        return informe
    todas: dict[str, dict] = {}
    por_medio: dict[str, int] = {}
    for fuente in fuentes:
        desde = dt.datetime.combine(hoy - dt.timedelta(days=int(fuente.get("dias", DIAS))), dt.time(), tzinfo=dt.timezone.utc)
        leidas = leer_canal(fuente, desde)
        por_medio[fuente["url"]] = len(leidas)
        for n in leidas:
            todas.setdefault(n["enlace"], n)
    informe["por_canal"] = por_medio
    informe["leidas"] = len(todas)
    ruta_cache = config.carpeta_cache(ciudad.id, "noticias") / "clasificacion.json"
    # Las clasificadas antes de existir «evento» se vuelven a clasificar (una vez).
    # Las clasificadas antes de existir «ambito» se vuelven a clasificar (una vez).
    cache = {k: v for k, v in (leer_json(ruta_cache, {}) or {}).items() if k in todas and "ambito" in v}
    tarea = ajustes.tareas_ia().get("noticias")
    pendientes = [k for k in todas if k not in cache]
    if tarea and tarea.activa and ia.disponible() and tarea.por_lotes:
        _por_lotes(tarea, todas, pendientes, cache, ruta_cache.parent, informe)
        guardar_json(ruta_cache, cache)
    elif tarea and tarea.activa and ia.disponible() and pendientes:
        cli = ia.cliente()
        pendientes = pendientes[: tarea.maximo_por_ejecucion]
        for n in range(0, len(pendientes), tarea.por_peticion):
            lote = pendientes[n:n + tarea.por_peticion]
            entrada = [_entrada(k, todas[k]) for k in lote]
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
            informe["clasificadas_hoy"] += _anotar(cache, r, por_id)
        guardar_json(ruta_cache, cache)
    salida = []
    for k, n in todas.items():
        c = cache.get(k)
        if not c or c["tema"] not in ("teatro", "cine", "magia", "circo"):
            continue
        salida.append({k2: v for k2, v in {
            "titulo": n["titulo"], "enlace": n["enlace"], "medio": n["medio"], "fecha": n["fecha"],
            "idioma": n["idioma"], "tema": c["tema"], "evento": c.get("evento"), "ambito": c.get("ambito") or n.get("ambito"),
            "titulos": {k3: v3 for k3, v3 in (c.get("titulo") or {}).items() if v3 and v3 != n["titulo"]} or None,
            "resumen": c["resumen"], "imagen": n["imagen"],
        }.items() if v})
    salida.sort(key=lambda n: n["fecha"], reverse=True)
    salida = salida[:MAXIMO_APP]
    informe["publicadas"] = len(salida)
    informe["por_tema"] = {t: sum(1 for n in salida if n["tema"] == t) for t in ("teatro", "cine", "magia", "circo")}
    informe["eventos"] = sum(1 for n in salida if n.get("evento"))
    informe["por_ambito"] = {a: sum(1 for n in salida if n.get("ambito") == a) for a in AMBITOS}
    CARPETA_WEB.mkdir(parents=True, exist_ok=True)
    (CARPETA_WEB / f"{ciudad.id}-noticias.json").write_text(
        json.dumps({"actualizado": hoy.isoformat(), "noticias": salida}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    return informe
