"""Ficha del mago o la maga de cada espectáculo de magia: trayectoria y premios con fuente.

Pedido en el brief («Ficha según el tipo → Magia»: el mago, su trayectoria y todos sus premios
y reconocimientos, cada uno explicado y con su fuente). La IA (tarea «fichas_personas» de
`ajustes/ia.toml`) busca en internet y resume.

Principio 4 (precisión): cada premio tiene que venir con la dirección de la página donde se
dice, y esa dirección tiene que estar entre las páginas que la búsqueda ha devuelto de verdad.
Si no, el premio se descarta. Si no se encuentra nada fiable, la ficha no sale.

Cada artista se busca una vez y se guarda 60 días (cache/ia/fichas_personas.json).
"""

from __future__ import annotations

import datetime as dt
import json
import re

from . import ajustes, config, ia
from .util import guardar_json, leer_json

DIAS_VALIDEZ = 60
SISTEMA = (
    "Eres documentalista de una cartelera de artes escénicas de Barcelona. Te dan el nombre de un mago, maga, "
    "mentalista o ilusionista (o de su espectáculo) que actúa ahora en Barcelona. Busca en la web información "
    "verificable sobre esa persona: quién es, su trayectoria y los premios o reconocimientos de magia que ha recibido "
    "(por ejemplo, premios FISM, Mandrake d'Or, premios nacionales de magia, Merlin, Varita Mágica…). "
    "Asegúrate de que hablas de la misma persona (mismo nombre artístico y dedicada a la magia). "
    "Usa solo lo que digan las páginas encontradas; no inventes nada. "
    "Termina tu respuesta con un único bloque JSON, sin nada después, con esta forma exacta: "
    '{"encontrado": true|false, "nombre": "nombre artístico", "trayectoria_es": "2 o 3 frases", '
    '"trayectoria_ca": "las mismas frases en catalán", "premios": [{"premio": "nombre del premio", "anio": 2019 o null, '
    '"fuente": "URL exacta de la página que lo dice"}], "fuentes": ["URL de las páginas usadas"]}. '
    "Si no encuentras información fiable de esa persona, devuelve {\"encontrado\": false}."
)


def _json_final(texto: str) -> dict | None:
    i = texto.rfind("{\"encontrado\"")
    if i < 0:
        i = texto.rfind("{")
    while i >= 0:
        try:
            return json.JSONDecoder().raw_decode(texto[i:])[0]
        except ValueError:
            i = texto.rfind("{", 0, i)
    return None


def buscar(cli, tarea, nombre: str, espectaculo: str) -> tuple[dict | None, int]:
    mensajes = [{"role": "user", "content": f"Artista: {nombre}\nEspectáculo en cartel: {espectaculo}"}]
    urls: set[str] = set()
    textos: list[str] = []
    busquedas = 0
    for _ in range(3):  # la búsqueda puede pausar el turno (pause_turn): se continúa
        ia.GASTO.comprobar()
        r = cli.beta.messages.create(
            model=tarea.modelo, max_tokens=8000, system=SISTEMA, messages=mensajes,
            output_config={"effort": tarea.esfuerzo},
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 3}],
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        )
        n = getattr(getattr(r.usage, "server_tool_use", None), "web_search_requests", 0) or 0
        busquedas += n
        ia.GASTO.sumar(tarea.nombre, tarea.modelo, r.usage, busquedas=n)
        for b in r.content:
            if b.type == "web_search_tool_result" and isinstance(b.content, list):
                urls.update(x.url for x in b.content if getattr(x, "url", None))
            elif b.type == "text":
                textos.append(b.text)
        if r.stop_reason != "pause_turn":
            break
        mensajes = mensajes + [{"role": "assistant", "content": r.content}]
    datos = _json_final("\n".join(textos))
    if not datos or not datos.get("encontrado"):
        return None, busquedas
    norm = lambda u: re.sub(r"[#?].*$", "", (u or "").rstrip("/"))  # noqa: E731
    vistas = {norm(u) for u in urls}
    premios, vistos_p = [], set()
    for p in datos.get("premios") or []:
        clave = (str(p.get("premio", "")).lower().strip(), p.get("anio"))
        if p.get("premio") and norm(p.get("fuente")) in vistas and clave not in vistos_p:
            vistos_p.add(clave)
            premios.append(p)
    fuentes = [u for u in datos.get("fuentes") or [] if norm(u) in vistas][:6]
    if not fuentes and not premios:
        return None, busquedas  # sin ninguna fuente comprobable no se publica nada
    return {
        "nombre": datos.get("nombre") or nombre,
        "trayectoria": {k: v for k, v in {"es": datos.get("trayectoria_es"), "ca": datos.get("trayectoria_ca")}.items() if v},
        "premios": [{"premio": p["premio"], "anio": p.get("anio"), "fuente": p["fuente"]} for p in premios],
        "fuentes": fuentes,
    }, busquedas


def aplicar(ciudad, items: list[dict], informe: dict) -> None:
    """Añade «artista_ficha» a los espectáculos de magia de la app."""
    tarea = ajustes.tareas_ia().get("fichas_personas")
    ruta = config.carpeta_cache(ciudad.id, "ia") / "fichas_personas.json"
    cache = leer_json(ruta, {}) or {}
    hoy = dt.date.today()
    magia = [it for it in items if it.get("tipo") == "magia"]
    inf = {"espectaculos_magia": len(magia), "buscados_hoy": 0, "con_ficha": 0}
    for it in magia:
        nombre = it.get("artista") or it.get("nombre")
        clave = re.sub(r"\W+", " ", nombre.lower()).strip()
        reg = cache.get(clave)
        caducado = not reg or (hoy - dt.date.fromisoformat(reg["fecha"])).days >= DIAS_VALIDEZ
        if caducado and tarea and tarea.activa and ia.disponible():
            try:
                ficha, n = buscar(ia.cliente(), tarea, nombre, it.get("nombre", ""))
                reg = {"fecha": hoy.isoformat(), "ficha": ficha, "busquedas": n}
                cache[clave] = reg
                inf["buscados_hoy"] += 1
                guardar_json(ruta, cache)
            except ia.TopeDeGasto as e:
                inf["aviso"] = str(e)
                break
            except Exception as e:  # noqa: BLE001
                inf.setdefault("errores", []).append(f"{type(e).__name__}: {str(e)[:150]}")
        if reg and reg.get("ficha"):
            ficha = dict(reg["ficha"])
            vistos_p: set = set()
            ficha["premios"] = [x for x in ficha.get("premios", [])
                                if not ((x["premio"].lower(), x.get("anio")) in vistos_p or vistos_p.add((x["premio"].lower(), x.get("anio"))))]
            it["artista_ficha"] = ficha
            inf["con_ficha"] += 1
    informe["fichas_personas"] = inf
