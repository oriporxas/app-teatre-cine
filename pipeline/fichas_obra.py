"""Ficha completa de cada obra desde su página oficial en la web de la sala (Uri, 18/11/2026:
«quiero el mismo nivel de información que en el cine»).

Para cada obra con página propia (`pagina_obra`, la encuentra `compra.py`):
- **Cartel**: la imagen que la propia página declara como suya (`og:image`). Si la misma imagen
  sale en páginas de obras distintas de la misma web, es el logotipo de la sala: no vale.
- **Equipo artístico, duración y premios**: la IA (tarea «fichas_obra» de `ajustes/ia.toml`, modelo
  barato) los copia de la página con la **cita literal**; el programa comprueba que cada cita está
  en la página, que cada nombre está en su cita y que los minutos están en la suya. Lo que no pasa,
  no sale (principio 4).
- Solo se completa lo que falta: el texto, las fechas y los precios siguen siendo los de la agenda.

Se respeta robots.txt (y si la web no quiere que su contenido pase por una IA, solo se toma el
cartel). Cada página se lee una vez y se vuelve a pedir a la IA solo si cambia.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import time
import urllib.parse

from . import ajustes, config, ia
from .cine import red
from .util import guardar_json, huella, leer_json, normalizar

DIAS_VALIDEZ = 14
MINUTOS_MAX = 8
MAX_TEXTO = 20000
VERSION = 1
IMAGEN = re.compile(r"\.(jpe?g|png|webp)(\?|$)", re.I)

ESQUEMA = {
    "type": "object",
    "properties": {
        "es_la_obra": {"type": "boolean"},
        "equipo": {"type": "array", "items": {
            "type": "object",
            "properties": {"papel": {"type": "string"}, "personas": {"type": "string"}, "cita": {"type": "string"}},
            "required": ["papel", "personas", "cita"], "additionalProperties": False}},
        "duracion_minutos": {"type": "integer"},
        "cita_duracion": {"type": "string"},
        "premios": {"type": "array", "items": {
            "type": "object",
            "properties": {"premio_es": {"type": "string"}, "premio_ca": {"type": "string"}, "cita": {"type": "string"}},
            "required": ["premio_es", "premio_ca", "cita"], "additionalProperties": False}},
    },
    "required": ["es_la_obra", "equipo", "duracion_minutos", "cita_duracion", "premios"],
    "additionalProperties": False,
}
SISTEMA = (
    "Lees la página web oficial de una obra (teatro, magia o circo) en la web de su sala. Te doy el título de la obra. "
    "Responde SOLO con lo que está escrito en el texto, copiando las citas letra por letra:\n"
    "- «es_la_obra»: true si la página trata de esa obra; si no, false y lo demás vacío.\n"
    "- «equipo»: la ficha artística: cada papel tal como lo escribe la página (Dirección, Dramaturgia, Intérpretes, "
    "Reparto, Escenografía, Iluminación, Música, Coreografía, Producción…), las «personas» (o compañías) de ese papel "
    "tal cual, separadas por comas, y la «cita»: el fragmento literal donde aparecen. Si no hay ficha artística, vacío.\n"
    "- «duracion_minutos» y «cita_duracion»: la duración si la página la dice (en minutos), con su cita; si no, 0 y vacío.\n"
    "- «premios»: premios, nominaciones o reconocimientos que la página dice que ha recibido ESTA obra, su compañía o "
    "sus artistas, en castellano y en catalán, con la cita literal. No incluyas premios sin nombre, de la obra original "
    "en que se basa ni de personas de las que trata. Si no hay, vacío.\n"
    "No inventes nada."
)


def _imagen_propia(pagina: str, base: str) -> str | None:
    for patron in (r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)',
                   r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                   r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)'):
        m = re.search(patron, pagina, re.I)
        if m:
            url = urllib.parse.urljoin(base, html.unescape(m.group(1)).strip())
            if url.startswith("https://") and IMAGEN.search(url) and not re.search(r"logo|favicon|icon", url, re.I):
                return url
    return None


def verificar(r: dict, texto: str) -> dict:
    """Lo que dice la IA, contrastado con el texto de la página."""
    from .fuentes.webs_salas import esta
    t = normalizar(texto)
    if not r or not r.get("es_la_obra"):
        return {}
    equipo = []
    for x in r.get("equipo") or []:
        papel, personas, cita = (x.get("papel") or "").strip(), (x.get("personas") or "").strip(), x.get("cita") or ""
        nombres = [n.strip() for n in re.split(r",|;| i | y ", personas) if n.strip()]
        if papel and nombres and esta(cita, t) and all(normalizar(n) in normalizar(cita) for n in nombres):
            equipo.append([papel[:1].upper() + papel[1:].rstrip(":"), ", ".join(nombres)])
    dur = r.get("duracion_minutos") or 0
    cita_d = r.get("cita_duracion") or ""
    duracion = dur if 5 <= dur <= 600 and esta(cita_d, t) and str(dur) in re.findall(r"\d+", cita_d) else None
    if duracion is None and 60 <= dur <= 600 and esta(cita_d, t):  # «1 h 30 min», «2 hores»
        h, m = divmod(dur, 60)
        nums = re.findall(r"\d+", cita_d)
        duracion = dur if str(h) in nums and (m == 0 or str(m) in nums) else None
    premios = [{"es": p["premio_es"], "ca": p["premio_ca"], "cita": p["cita"], "origen": "web"} for p in r.get("premios") or []
               if p.get("cita") and esta(p["cita"], t) and p.get("premio_es")]
    return {"equipo": equipo, "duracion": duracion, "premios": premios}


def aplicar(ciudad, items: list[dict], informe: dict, leer_webs: bool = True) -> None:
    from .fuentes.webs_salas import texto_pagina
    ruta = config.carpeta_cache(ciudad.id, "fichas_obra") / "paginas.json"
    cache = leer_json(ruta, {}) or {}
    tarea = ajustes.tareas_ia().get("fichas_obra")
    hoy = dt.date.today()
    fin = time.monotonic() + MINUTOS_MAX * 60
    inf = {"con_pagina": 0, "leidas_hoy": 0, "ia_hoy": 0, "cartel_nuevo": 0, "equipo_nuevo": 0, "equipo_ampliado": 0,
           "duracion_nueva": 0, "premios_nuevos": 0}
    for it in items:
        url = it.get("pagina_obra")
        if not url or it.get("tipo") == "eventos":
            continue
        inf["con_pagina"] += 1
        reg = cache.get(url)
        caducado = not reg or (hoy - dt.date.fromisoformat(reg["fecha"])).days >= DIAS_VALIDEZ
        if caducado and leer_webs and time.monotonic() < fin:
            b = red.pedir(url, timeout=25)
            if b:
                pagina = b.decode("utf-8", "replace")
                texto, _ = texto_pagina(pagina, url)
                texto = texto[:MAX_TEXTO]
                firma = huella(texto, tarea.modelo if tarea else "", VERSION)
                nuevo = {"fecha": hoy.isoformat(), "imagen": _imagen_propia(pagina, url), "firma": firma,
                         "datos": (reg or {}).get("datos") if (reg or {}).get("firma") == firma else None}
                if nuevo["datos"] is None and tarea and tarea.activa and ia.disponible() and red.permite_ia(url) and texto.strip():
                    try:
                        r = ia.pedir_json(ia.cliente(), tarea="fichas_obra", modelo=tarea.modelo, esfuerzo=tarea.esfuerzo,
                                          sistema=SISTEMA, mensaje=f"Obra: {it.get('nombre')}\nPágina: {url}\n\n{texto}",
                                          esquema=ESQUEMA, max_tokens=4000)
                        nuevo["datos"] = verificar(r or {}, texto)
                        inf["ia_hoy"] += 1
                    except ia.TopeDeGasto as e:
                        inf["aviso"] = str(e)
                        fin = 0
                    except Exception as e:  # noqa: BLE001
                        inf.setdefault("errores", []).append(f"{url}: {type(e).__name__}: {str(e)[:100]}")
                reg = cache[url] = nuevo
                inf["leidas_hoy"] += 1
                if inf["leidas_hoy"] % 20 == 0:
                    guardar_json(ruta, cache)
    guardar_json(ruta, cache)
    # El logotipo de una sala sale en todas sus obras: una imagen repetida en obras distintas no es un cartel.
    usos: dict[str, set] = {}
    for it in items:
        img = (cache.get(it.get("pagina_obra") or "") or {}).get("imagen")
        if img:
            usos.setdefault(img, set()).add(normalizar(it.get("nombre") or ""))
    for it in items:
        url = it.get("pagina_obra")
        reg = cache.get(url or "")
        if not reg:
            continue
        img = reg.get("imagen")
        if img and not it.get("imagen") and len(usos.get(img, ())) == 1:
            it["imagen"] = img
            inf["cartel_nuevo"] += 1
        d = reg.get("datos") or {}
        if d.get("equipo"):
            if not it.get("equipo"):
                it["equipo"] = d["equipo"]
                inf["equipo_nuevo"] += 1
            else:  # se añaden los papeles que la agenda no traía
                ya = {normalizar(p) for p, _ in it["equipo"]}
                extra = [x for x in d["equipo"] if normalizar(x[0]) not in ya]
                if extra:
                    it["equipo"] = it["equipo"] + extra
                    inf["equipo_ampliado"] += 1
        if d.get("duracion") and not it.get("duracion"):
            it["duracion"] = d["duracion"]
            inf["duracion_nueva"] += 1
        if d.get("premios"):
            vistos = {normalizar(p.get("cita", "")) for p in it.get("premios") or []}
            nuevos = [p for p in d["premios"] if normalizar(p["cita"]) not in vistos]
            if nuevos:
                it["premios"] = (it.get("premios") or []) + nuevos
                inf["premios_nuevos"] += 1
        if d or img:
            it["ficha_fuente"] = url
    informe["fichas_obra"] = inf
