"""Lector de webs de salas: la programación de las salas que no publican en la agenda municipal.

Pedido de Uri (17/11/2026): que no se escape ninguna sala. La auditoría de cobertura
(`pipeline/cobertura.py`) dice cada día qué teatros de la lista oficial no tienen nada en
nuestras fuentes. Esta fuente lee la web oficial de cada uno y saca sus funciones.

Cómo (sin listas hechas a mano: las salas salen de la auditoría y su web, de la guía oficial):
1. Salas: las de `cobertura.json` (la auditoría del día anterior) de tipo teatro, menos centros
   educativos (escuelas, institutos, facultades: no tienen programación pública).
2. Web: la ficha de la sala en la guía oficial (guia.barcelona.cat, 10 s entre páginas, 30 días).
3. Páginas: la portada de la web y, como mucho, dos páginas de programación enlazadas desde ella
   («programació», «cartellera», «agenda», «espectacles»…). Siempre respetando robots.txt; si la web
   no quiere que su contenido pase por una IA (bloquea GPTBot, ClaudeBot…), no se lee.
4. La IA (tarea «leer_webs» de `ajustes/ia.toml`, modelo barato) extrae las obras y, de cada dato,
   la **cita literal** de la página. Solo se vuelve a pedir si el texto de la página cambia.
5. Verificación (principio 4), sin fiarse de la IA:
   - el título tiene que estar en la página;
   - cada función: su cita está en la página y contiene el día, el mes (y la hora, si la hay)
     de la fecha que da la IA; si la cita trae año, tiene que coincidir;
   - el precio lo lee nuestro programa de la cita (`horario.leer_precios`), no la IA;
   - el enlace tiene que ser uno de los enlaces de la página; la descripción, un trozo literal.
   Lo que no pasa, no sale.

Las actividades salen en el formato común (`fuentes/base.py`) y siguen el camino de todas:
clasificación, verificador y app.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import time
import urllib.parse

from ... import ajustes, config, ia
from ...cine import red
from ...horario import leer_dias, leer_horas, leer_precios
from ...util import guardar_json, huella, leer_json, normalizar
from ..base import Contexto, Resultado, id_global

NOMBRE = "webs_salas"
DESCRIPCION = "Programación de la web oficial de las salas que no salen en la agenda municipal (IA con citas comprobadas)."

GUIA = "https://guia.barcelona.cat/ca/detall/equipament_{id}.html"
DIAS_GUIA = 30
NO_WEBS = re.compile(r"barcelona\.cat|bcn\.cat|gencat\.cat|facebook|twitter|//x\.com|instagram|youtube|google|tiktok|"
                     r"linkedin|whatsapp|addtoany|t\.me|wikipedia")
EDUCATIVOS = re.compile(r"\b(centre educatiu|escola|escuela|institut|instituto|facultat|universitat|col·legi|colegio|"
                        r"conservatori|school)\b", re.I)
PROGRAMACION = re.compile(r"programaci|cartell|cartelera|agenda|espectacl|espectácul|espectacul|temporada|calendari|"
                          r"events?\b|funcions|shows?\b|obres", re.I)
MAX_TEXTO = 30000
VERSION = 2  # al cambiar las instrucciones o el esquema, se vuelve a leer cada página con la IA
RANGO = re.compile(r"\b(del?|desde|entre)\s+(el\s+)?\d{1,2}\b.{0,25}\b(al|a|fins al|fins el|hasta el|hasta|y el|i el)\s+(el\s+)?\d{1,2}\b"
                   r"|\b(fins|hasta|until)\s+(al|el|the)?\s*\d{1,2}\b|(?<![\d:.])\d{1,2}\s*[-–]\s*\d{1,2}\s+(de\s+|d')?[a-z]{3}", re.I)
MESES = {
    1: ("gen", "ene", "jan"), 2: ("feb",), 3: ("mar",), 4: ("abr", "apr"), 5: ("mai", "may"), 6: ("jun", "juny"),
    7: ("jul",), 8: ("ago", "agost", "aug"), 9: ("set", "sep"), 10: ("oct", "octu"), 11: ("nov",), 12: ("des", "dic", "dec"),
}

ESQUEMA = {
    "type": "object",
    "properties": {"obras": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "titulo": {"type": "string"},
            "cita_titulo": {"type": "string"},
            "descripcion": {"type": "string"},
            "funciones": {"type": "array", "items": {
                "type": "object",
                "properties": {"fecha": {"type": "string"}, "hora": {"type": "string"}, "cita": {"type": "string"}},
                "required": ["fecha", "hora", "cita"], "additionalProperties": False}},
            "periodo": {"type": "object", "properties": {
                "inicio": {"type": "string"}, "fin": {"type": "string"}, "cita": {"type": "string"},
                "cita_horario": {"type": "string"}},
                "required": ["inicio", "fin", "cita", "cita_horario"], "additionalProperties": False},
            "cita_lugar": {"type": "string"},
            "cita_precio": {"type": "string"},
            "enlace": {"type": "string"},
            "idioma": {"type": "string", "enum": ["ca", "es", "en", "otro"]},
        },
        "required": ["titulo", "cita_titulo", "descripcion", "funciones", "periodo", "cita_lugar", "cita_precio", "enlace",
                     "idioma"],
        "additionalProperties": False}}},
    "required": ["obras"], "additionalProperties": False,
}
SISTEMA = (
    "Lees la web oficial de una sala de espectáculos de {ciudad} y extraes su programación: las obras, espectáculos o "
    "actividades que se hacen EN ESA SALA con fecha concreta a partir de hoy ({hoy}). Nada de lo que no esté escrito en "
    "el texto: no deduzcas fechas, horas ni precios. Para cada obra devuelve:\n"
    "- «titulo»: el título tal cual; «cita_titulo»: el fragmento del texto donde aparece, copiado letra por letra.\n"
    "- «descripcion»: un fragmento literal del texto que describa la obra (máximo 600 caracteres), o vacío.\n"
    "- «funciones»: cada función con «fecha» (AAAA-MM-DD), «hora» (HH:MM, o vacío si no se dice) y «cita»: el fragmento "
    "literal del texto donde se leen el día y el mes (y la hora). Si el mes está en otra parte (por ejemplo, en un "
    "encabezado), la cita son los dos fragmentos literales unidos con « … ». Solo días concretos de función: un periodo "
    "(«del 19 al 29 de novembre», «fins al 30 de desembre») NO son funciones de su primer y último día.\n"
    "- «periodo»: si la web da un periodo, «inicio» y «fin» (AAAA-MM-DD), «cita» (el fragmento literal del periodo) y "
    "«cita_horario» (el fragmento literal con los días de la semana y la hora, p. ej. «De dijous a dissabte a les 20 h»; "
    "vacío si no lo dice). Si no hay periodo, todo vacío.\n"
    "- «cita_lugar»: si la web tiene varias salas o locales, el fragmento literal que dice en cuál es esta obra; si no, vacío.\n"
    "- «cita_precio»: el fragmento literal con el precio, o vacío.\n"
    "- «enlace»: la dirección (las que van entre corchetes en el texto) de la página o la compra de esa obra, o vacío.\n"
    "- «idioma»: el idioma del texto de esa obra (ca, es, en u otro).\n"
    "No incluyas obras de otras salas, cursos o talleres sin fecha, ni noticias. Si no hay programación, lista vacía."
)


# --- Texto de una página web, con los enlaces entre corchetes ----------------------------------

def texto_pagina(pagina: str, base: str) -> tuple[str, set[str]]:
    p = re.sub(r"<(script|style|noscript|svg|nav|footer|header)\b.*?</\1>", " ", pagina, flags=re.S | re.I)
    enlaces: set[str] = set()

    def enlace(m):
        url = urllib.parse.urljoin(base, html.unescape(m.group(1)).strip())
        texto = re.sub(r"<[^>]+>", " ", m.group(2))
        if url.startswith("http"):
            enlaces.add(url)
            return f" {texto} [{url}] "
        return f" {texto} "
    p = re.sub(r"<a\b[^>]*?href=[\"']([^\"'#][^\"']*)[\"'][^>]*>(.*?)</a>", enlace, p, flags=re.S | re.I)
    p = re.sub(r"<(br|/p|/div|/li|/h\d|/tr)\b[^>]*>", "\n", p, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", p))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\s*\n\s*", "\n", t).strip()
    return t, enlaces


# --- Verificación de lo que dice la IA ---------------------------------------------------------

def esta(fragmento: str, texto_norm: str) -> bool:
    """¿Está el fragmento (o cada uno de sus trozos unidos con «…») en el texto de la página?"""
    trozos = [normalizar(x) for x in re.split(r"…|\.\.\.", fragmento or "") if normalizar(x)]
    return bool(trozos) and all(t in texto_norm for t in trozos)


def fecha_en_cita(fecha: dt.date, cita: str) -> bool:
    """La cita contiene el día y el mes de la fecha (y, si trae año, el mismo)."""
    c = normalizar(cita)
    numeros = re.findall(r"\d+", c)
    anyos = [int(n) for n in numeros if len(n) == 4]
    if anyos and fecha.year not in anyos:
        return False
    if re.search(rf"(?<!\d)0?{fecha.day}\s*[/.-]\s*0?{fecha.month}(?!\d)", cita):  # «21/11», «21.11»
        return True
    if str(fecha.day) not in [n.lstrip("0") or "0" for n in numeros]:
        return False
    palabras = re.findall(r"[a-z]+", c)
    return any(p.startswith(m) for p in palabras for m in MESES[fecha.month])


def hora_en_cita(hora: str, cita: str) -> bool:
    h, m = hora.split(":")
    h2 = str(int(h))
    patron = rf"(?<!\d)0?{h2}\s*(?:[:.h']\s*{m}|h\b|\s*hores|\s*horas)" if m == "00" else rf"(?<!\d)0?{h2}\s*[:.h']\s*{m}"
    return bool(re.search(patron, cita.lower()))


def _funciones_de_periodo(per: dict, t: str, hoy: dt.date) -> list[dict]:
    """Funciones de un periodo («del 19 al 29 de novembre» + «de dijous a dissabte a les 20 h»), calculadas por
    nuestro programa a partir del texto literal; si la web no dice qué días, ninguna."""
    try:
        ini, fin = dt.date.fromisoformat(per.get("inicio", "")), dt.date.fromisoformat(per.get("fin", ""))
    except ValueError:
        return []
    cita, cita_h = per.get("cita") or "", per.get("cita_horario") or ""
    if not (ini <= fin <= hoy + dt.timedelta(days=400)) or (fin - ini).days > 200 or not esta(cita, t) \
            or not fecha_en_cita(ini, cita) or not fecha_en_cita(fin, cita) or not cita_h or not esta(cita_h, t):
        return []
    dias = leer_dias(cita_h, ini, fin)
    horas = leer_horas(cita_h)
    hora = horas[0]["inicio"] if len(horas) == 1 else None  # varias horas: no se sabe cuál va con cada día
    fechas = {dt.date.fromisoformat(x) for x in dias["fechas"]}
    d = max(ini, hoy)
    while d <= fin and dias["semana"]:
        if d.weekday() in dias["semana"]:
            fechas.add(d)
        d += dt.timedelta(days=1)
    excluidas = {dt.date.fromisoformat(x) for x in dias["excepto"]}
    return [{"fecha": x.isoformat(), "hora": hora, "cita": f"{cita} … {cita_h}"}
            for x in sorted(fechas - excluidas) if ini <= x <= fin and x >= hoy]


def verificar_obra(o: dict, texto: str, enlaces: set[str], hoy: dt.date) -> dict | None:
    t = normalizar(texto)
    titulo = (o.get("titulo") or "").strip()
    if not titulo or not esta(o.get("cita_titulo", ""), t) or normalizar(titulo) not in t:
        return None
    funciones = []
    for f in o.get("funciones") or []:
        try:
            fecha = dt.date.fromisoformat(f.get("fecha", ""))
        except ValueError:
            continue
        cita = f.get("cita") or ""
        if not (hoy <= fecha <= hoy + dt.timedelta(days=400)) or not esta(cita, t) or not fecha_en_cita(fecha, cita):
            continue
        if RANGO.search(normalizar(cita)):  # «del 19 al 29»: es un periodo, no dos funciones
            continue
        hora = f.get("hora") or ""
        hora = hora if re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", hora) and hora_en_cita(hora, cita) else None
        funciones.append({"fecha": fecha.isoformat(), "hora": hora, "cita": cita})
    funciones += _funciones_de_periodo(o.get("periodo") or {}, t, hoy)
    funciones = limpiar_funciones(funciones)
    if not funciones:
        return None
    cita_precio = o.get("cita_precio") or ""
    precio = leer_precios(cita_precio) if cita_precio and esta(cita_precio, t) else None
    desc = o.get("descripcion") or ""
    cita_lugar = o.get("cita_lugar") or ""
    return {
        "titulo": titulo,
        "descripcion": desc if desc and esta(desc, t) else "",
        "funciones": funciones,
        "precio": precio,
        "texto_precio": cita_precio if precio else "",
        "enlace": o.get("enlace") if o.get("enlace") in enlaces else None,
        "idioma": o.get("idioma") if o.get("idioma") in ("ca", "es", "en") else None,
        "lugar": cita_lugar if cita_lugar and esta(cita_lugar, t) else "",
    }


def limpiar_funciones(funciones: list[dict]) -> list[dict]:
    """Sin repetir; el mismo día con hora y sin hora es una sola función (la que tiene hora)."""
    con_hora = {f["fecha"] for f in funciones if f.get("hora")}
    unicas = {(f["fecha"], f.get("hora") or ""): f for f in funciones if f.get("hora") or f["fecha"] not in con_hora}
    return sorted(unicas.values(), key=lambda f: (f["fecha"], f.get("hora") or ""))


def propias(nombre: str, otros: list[str]) -> set[str]:
    """Palabras del nombre de una sala que no tienen las otras salas con la misma web
    («The Comedy Clubhouse *Canvis Nous» frente a «… *Laietana & Nikki's» → {canvis, nous})."""
    comunes = set().union(*(set(normalizar(x).split()) for x in otros)) if otros else set()
    return {w for w in normalizar(nombre).split() if len(w) > 2 and w not in comunes}


# --- La fuente -----------------------------------------------------------------------------------

def _web_de(sala: dict, cache: dict, hoy: dt.date, leer: bool) -> str | None:
    reg = cache.get(sala["id"])
    if reg and (hoy - dt.date.fromisoformat(reg["fecha"])).days < DIAS_GUIA:
        return reg.get("web")
    if not leer:
        return reg.get("web") if reg else None
    b = red.pedir(GUIA.format(id=sala["id"]), timeout=40)
    pagina = b.decode("utf-8", "replace") if b else ""
    i, j = pagina.find('<div id="fitxa">'), pagina.find('<div id="registres-relacionats">')
    bloque = pagina[i:j if j > i else None] if i >= 0 else pagina
    webs = [w for w in dict.fromkeys(re.findall(r'href="(https?://[^"]+)"', bloque)) if not NO_WEBS.search(w)]
    cache[sala["id"]] = {"fecha": hoy.isoformat(), "web": webs[0] if webs else None}
    return cache[sala["id"]]["web"]


def _paginas(web: str) -> list[tuple[str, str, set[str]]]:
    """(dirección, texto, enlaces) de la portada y hasta dos páginas de programación."""
    if not red.permite_ia(web):
        return []
    b = red.pedir(web, timeout=30)
    if not b:
        return []
    portada = b.decode("utf-8", "replace")
    texto, enlaces = texto_pagina(portada, web)
    res = [(web, texto, enlaces)]
    raiz = urllib.parse.urlsplit(web).netloc.removeprefix("www.")
    candidatas = []
    for m in re.finditer(r"<a\b[^>]*?href=[\"']([^\"'#][^\"']*)[\"'][^>]*>(.*?)</a>", portada, re.S | re.I):
        url = urllib.parse.urljoin(web, html.unescape(m.group(1)).strip())
        txt = re.sub(r"<[^>]+>", " ", m.group(2))
        if url.startswith("http") and urllib.parse.urlsplit(url).netloc.removeprefix("www.") == raiz \
                and PROGRAMACION.search(f"{urllib.parse.urlsplit(url).path} {txt}") and url.rstrip("/") != web.rstrip("/"):
            candidatas.append(url)
    for url in list(dict.fromkeys(candidatas))[:2]:
        b = red.pedir(url, timeout=30) if red.permite_ia(url) else None
        if b:
            t, e = texto_pagina(b.decode("utf-8", "replace"), url)
            res.append((url, t, e))
    return res


def recoger(ctx: Contexto) -> Resultado:
    ciudad = ctx.ciudad
    cobertura = leer_json(config.carpeta_ciudad(ciudad.id) / "cobertura.json", {}) or {}
    salas = [s for s in cobertura.get("sin_actividades_detalle", [])
             if "teatro" in s.get("tipo", []) and s.get("id") and not EDUCATIVOS.search(s.get("nombre") or "")]
    ruta_guia = ctx.carpeta_cache / "webs.json"
    ruta_ia = ctx.carpeta_cache / "extracciones.json"
    cache_guia = leer_json(ruta_guia, {}) or {}
    cache_ia = leer_json(ruta_ia, {}) or {}
    tarea = ajustes.tareas_ia().get("leer_webs")
    fin = time.monotonic() + 60 * min(ctx.minutos_lectura or 15, 15)
    inf = {"salas_sin_agenda": len(salas), "con_web": 0, "paginas": 0, "leidas_ia": 0, "obras": 0, "descartadas": 0,
           "funciones": 0}
    actividades = []
    # Salas que comparten web (dos locales de la misma compañía): cada obra solo va a la sala que la
    # página nombra; si la página no lo dice, no se puede saber y no sale.
    webs_de = {s["id"]: _web_de(s, cache_guia, ctx.hoy, ctx.leer_webs) for s in salas}
    dominio = lambda u: urllib.parse.urlsplit(u or "").netloc.removeprefix("www.")  # noqa: E731
    por_dominio: dict[str, list[str]] = {}
    for s in salas:
        if webs_de.get(s["id"]):
            por_dominio.setdefault(dominio(webs_de[s["id"]]), []).append(s["nombre"])
    for s in salas:
        if time.monotonic() > fin:
            inf["aviso"] = "sin tiempo: el resto, mañana"
            break
        web = webs_de.get(s["id"])
        if not web:
            continue
        compartida = [n for n in por_dominio.get(dominio(web), []) if n != s["nombre"]]
        mias = propias(s["nombre"], compartida) if compartida else set()
        inf["con_web"] += 1
        paginas = _paginas(web) if ctx.leer_webs else []
        if not paginas:  # sin conexión o la web no responde hoy: lo de la última lectura
            paginas = [(k.split("|", 1)[1], r.get("texto", ""), set(r.get("enlaces", [])))
                       for k, r in cache_ia.items() if k.startswith(f"{s['id']}|")]
        for url, texto, enlaces in paginas:
            inf["paginas"] += 1
            clave = f"{s['id']}|{url}"
            firma = huella(texto[:MAX_TEXTO], tarea.modelo if tarea else "", VERSION)
            reg = cache_ia.get(clave)
            if (not reg or reg.get("firma") != firma) and tarea and tarea.activa and ia.disponible() and texto.strip():
                try:
                    r = ia.pedir_json(ia.cliente(), tarea="leer_webs", modelo=tarea.modelo, esfuerzo=tarea.esfuerzo,
                                      sistema=SISTEMA.format(ciudad=ciudad.nombre, hoy=ctx.hoy.isoformat()),
                                      mensaje=f"Sala: {s['nombre']}\nPágina: {url}\n\n{texto[:MAX_TEXTO]}",
                                      esquema=ESQUEMA, max_tokens=12000)
                    reg = {"firma": firma, "fecha": ctx.hoy.isoformat(), "obras": (r or {}).get("obras", []),
                           "texto": texto[:MAX_TEXTO], "enlaces": sorted(enlaces)}
                    cache_ia[clave] = reg
                    inf["leidas_ia"] += 1
                    guardar_json(ruta_ia, cache_ia)
                except ia.TopeDeGasto as e:
                    inf["aviso"] = str(e)
                    break
                except Exception as e:  # noqa: BLE001
                    inf.setdefault("errores", []).append(f"{url}: {type(e).__name__}: {str(e)[:120]}")
                    continue
            if not reg:
                continue
            obras = [v for v in (verificar_obra(o, reg.get("texto", texto), set(reg.get("enlaces", enlaces)), ctx.hoy)
                                 for o in reg.get("obras", []))]
            inf["descartadas"] += sum(1 for v in obras if not v)
            obras = [v for v in obras if v]
            # Un enlace que sirve para varias obras es la lista de la web, no la página de la obra.
            usos: dict[str, int] = {}
            for v in obras:
                if v["enlace"]:
                    usos[v["enlace"]] = usos.get(v["enlace"], 0) + 1
            for v in obras:
                if v["enlace"] and (usos[v["enlace"]] > 1 or v["enlace"].rstrip("/") == url.rstrip("/")):
                    v["enlace"] = None
                if compartida and not (mias and mias & set(normalizar(v["lugar"]).split())):
                    inf["web_compartida"] = inf.get("web_compartida", 0) + 1
                    continue
                actividades.append(_actividad(v, s, url, ciudad, ctx.hoy))
    guardar_json(ruta_guia, cache_guia)
    # Una sola ficha por obra: la misma obra en dos páginas de la misma sala, o con el título alargado
    # («Con vista al mar» y «Con vista al mar - Segona temporada»), se junta en una.
    juntas: dict[str, dict] = {}
    for a in sorted(actividades, key=lambda a: len(a["titulo"])):
        t = normalizar(a["titulo"])
        igual = next((j for j in juntas.values() if j["lugar"]["clave"] == a["lugar"]["clave"]
                      and (normalizar(j["titulo"]) == t or t.startswith(normalizar(j["titulo"]) + " "))), None)
        if igual:
            igual["horario"]["proximas_funciones"] = limpiar_funciones(igual["horario"]["proximas_funciones"]
                                                                        + a["horario"]["proximas_funciones"])
            igual["fin"] = max(igual["fin"], a["fin"])
            igual["extra"]["citas"] += a["extra"]["citas"]
            for campo in ("enlace_compra",):
                igual[campo] = igual.get(campo) or a.get(campo)
        else:
            juntas[a["id"]] = a
    for a in juntas.values():
        a["horario"]["proximas_funciones"] = [{"fecha": f["fecha"], "hora": f.get("hora")} for f in a["horario"]["proximas_funciones"]]
    inf["obras"] = len(juntas)
    inf["funciones"] = sum(len(a["horario"]["proximas_funciones"]) for a in juntas.values())
    return Resultado(actividades=list(juntas.values()), informe=inf)


def _actividad(v: dict, s: dict, url: str, ciudad, hoy: dt.date) -> dict:
    fechas = [f["fecha"] for f in v["funciones"]]
    id_origen = huella(s["id"], normalizar(v["titulo"]))[:16]
    texto_horario = "\n".join(f["cita"] for f in v["funciones"])
    return {
        "id": id_global(NOMBRE, id_origen), "fuente": NOMBRE, "id_origen": id_origen, "ciudad": ciudad.id,
        "titulo": v["titulo"], "idioma_textos": v["idioma"] or ciudad.idiomas[0],
        "descripcion": {(v["idioma"] or ciudad.idiomas[0]): v["descripcion"]} if v["descripcion"] else {},
        "inicio": min(fechas), "fin": max(fechas),
        "horario": {
            "filas": [{"texto": {"dias": texto_horario, **({"precios": v["texto_precio"]} if v["texto_precio"] else {})}}],
            "proximas_funciones": [{"fecha": f["fecha"], "hora": f.get("hora")} for f in v["funciones"]],
            "precio": {**v["precio"], "moneda": ciudad.moneda} if v["precio"] else None,
            "duracion_minutos": None, "idiomas": [],
        },
        "horario_texto": texto_horario + (f"\nPrecio: {v['texto_precio']}" if v["texto_precio"] else ""),
        "lugar": {
            "clave": f"{ciudad.id}:{s['clave']}", "nombre_en_fuente": s["nombre"], "nombre_casa": s["nombre"],
            "sala_interior": None, "tipo_de_lugar": "teatro",
            "direccion": {"calle": s.get("calle"), "numero": s.get("numero"), "codigo_postal": s.get("codigo_postal"),
                          "barrio": s.get("barrio"), "distrito": s.get("distrito"), "municipio": ciudad.nombre},
            "coordenadas": {"lat": s["lat"], "lon": s["lon"]} if s.get("lat") and s.get("lon") else None,
            "ids_origen": [s["id"]], "categorias": ["Teatres"],
        },
        "enlaces": [{"tipo": "Web", "url": url}],
        "enlace_compra": v["enlace"],
        "detalle_leido": True,
        "fuentes": [{"nombre": f"{s['nombre']} (web oficial)", "url": url, "comprobado": hoy.isoformat()}],
        "extra": {"citas": [f["cita"] for f in v["funciones"]]},
    }
