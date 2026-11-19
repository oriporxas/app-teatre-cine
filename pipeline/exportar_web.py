"""Prepara la cartelera de cada ciudad para la app (fase 2).

Cada noche, después de la recogida, se escribe un archivo por ciudad
(web/public/datos/<ciudad>.json) con lo que la app necesita para buscar y
mostrar fichas, y un índice de ciudades (web/public/datos/ciudades.json).
El móvil descarga el archivo de su ciudad y busca dentro: es rápido, se puede
servir gratis y el coste no crece con las búsquedas.

Decisiones de Uri que se aplican aquí (brief, 8/11/2026):
- Funciones (teatro, magia, circo) y eventos van separados; la danza y el cine
  no están en la app por ahora.
- En magia solo salen los espectáculos cuya razón principal es la magia.
- Solo se muestra lo que se sabe: los campos desconocidos no se envían.
"""

from __future__ import annotations

import datetime as dt
import json
import re

from . import config, equipo
from .util import guardar_json, leer_json

CARPETA_WEB = config.RAIZ / "web" / "public" / "datos"
TIPOS_APP = {"teatro": "teatro", "magia": "magia", "circo": "circo", "evento": "eventos"}
# Por ahora la app es solo de teatro, magia y circo (Uri, 8/11/2026): los eventos (talleres,
# festivales, charlas…) solo salen si son de una de esas disciplinas o sobre magia.
DISCIPLINAS_APP = ("teatro", "magia", "circo", "clown", "cine")  # cine: eventos de cine (Uri, 19/11/2026)
# Teatro musical (Uri, 9/11/2026): sale dentro de teatro con la etiqueta «Musical», pero solo si
# es seguro que es teatro musical (lo dice el título, una etiqueta o una frase; o la IA). Para
# volver a dejarlos fuera de la app, basta con poner False.
MUSICALES_EN_TEATRO = True
# Lo dudoso (poca confianza) no se publica: espera a que la IA lo lea.
CONFIANZA_MINIMA = 0.6
LARGO_DESCRIPCION = 900

_COMILLAS = (r'"(.+?)"', r"“(.+?)”", r"«(.+?)»", r'["“](.+?)["”]', r"(?<![A-Za-zÀ-ÿ])['‘](.+?)['’](?![A-Za-zÀ-ÿ])")
# El artista va justo después del título entre comillas: «"Strafalari", a càrrec del Mag Lari».
_ARTISTA = re.compile(r"^(?:a càrrec d(?:e la |e l['’]|el |e |['’]en |els |['’])|amb (?:la |el |l['’])?|"
                      r"per (?:la |el )?)(.+)$", re.I)
# Con un simple «de» o «d'» solo si sigue un nombre propio: «de Bea Prova», no «D'aquí surten…».
_ARTISTA_DE = re.compile(r"^(?:de (?:la |l['’])?|d['’])([A-ZÀ-Ý].+)$", re.I)
# Lo que puede ir delante del título entre comillas sin formar parte del nombre.
_ANTES_DEL_NOMBRE = re.compile(r"\b(espectacle|espectáculo|teatre|teatro|taller|curs|curso|circ|circo|musical|dansa|danza|"
                               r"monòleg|monólogo|obra|show|familiar|infantil|activitat|presenta|concert)\W*$", re.I)
_NOU = re.compile(r"\s*\*+\s*(nou|nova|nuevo|nueva|new)\s*\*+\s*", re.I)
_FORMATO = re.compile(r"^(Espectacle( de \w+)?( familiar| infantil| musical)?|Teatre( familiar| infantil)?|Monòleg|"
                      r"Taller( infantil| per a adults)?|Curs|Circ|Musical( familiar)?|Dansa)(?![\wÀ-ÿ])\s*[:,]?\s*", re.I)


def limpiar_titulo(titulo: str) -> tuple[str, str | None]:
    """«Espectacle de màgia "Strafalari", a càrrec del Mag Lari» -> («Strafalari», «Mag Lari»)."""
    t = _NOU.sub(" ", titulo or "").strip()
    for patron in _COMILLAS:
        m = re.search(patron, t)
        if m:
            antes = t[:m.start()].strip(" ,.:-")
            # «Homenatge '50 anys de "Carrie"…»: lo de delante es parte del nombre; se deja entero.
            if antes and len(antes.split()) > 3 and not _ANTES_DEL_NOMBRE.search(antes):
                break
            nombre = m.group(1).strip()
            resto = t[m.end():].strip(" ,.:-")
            a = _ARTISTA.match(resto) or _ARTISTA_DE.match(resto)
            if a and a.re is _ARTISTA_DE and not a.group(1)[0].isupper():
                a = None
            return nombre, (a.group(1).strip(" ,.'’\"") if a else None)
    sin_formato = _FORMATO.sub("", t).strip(" '\"“”«»‘’")
    return (sin_formato or t), None


def _resumen(texto: str | None) -> str | None:
    d = " ".join((texto or "").split())
    if not d:
        return None
    if len(d) <= LARGO_DESCRIPCION:
        return d
    corte = d[:LARGO_DESCRIPCION]
    punto = max(corte.rfind(". "), corte.rfind("! "), corte.rfind("? "))
    return corte[:punto + 1] if punto > 300 else corte.rsplit(" ", 1)[0] + "…"


def _sin_vacios(d: dict) -> dict:
    """Quita lo que no se sabe (principio: solo se muestra lo que se sabe)."""
    return {k: v for k, v in d.items() if v not in (None, "", [], {}, False) or k == "id"}


def _item(f: dict) -> dict | None:
    generos = f.get("generos") or []
    if f["tipo"] == "musical" and MUSICALES_EN_TEATRO and "musical" in generos:
        f = f | {"tipo": "teatro"}
    if not MUSICALES_EN_TEATRO and "musical" in generos:
        return None
    tipo = TIPOS_APP.get(f["tipo"])
    if tipo is None or not f["proximas_funciones"] or (f.get("confianza") or 0) < CONFIANZA_MINIMA:
        return None
    if tipo == "eventos" and f.get("disciplina") not in DISCIPLINAS_APP and f.get("magia") != "tema":
        return None
    textos = {k: v for k, v in (f.get("descripcion") or {}).items() if v}
    creditos = [] if tipo == "eventos" else next(
        (c for c in (equipo.leer(v, f["titulo"]) for v in list(textos.values()) or [""]) if c), [])
    nombre, artista = limpiar_titulo(f["titulo"])
    precio = f.get("precio") or {}
    direccion = f.get("direccion") or {}
    coord = f.get("coordenadas") or {}
    fuente = next((x for x in f["fuentes"] if "guia" in x.get("url", "")), f["fuentes"][0])
    return _sin_vacios({
        "id": f["id"],
        "nombre": nombre,
        "artista": artista,
        "tipo": tipo,
        "subtipo": f.get("subtipo"),
        "generos": generos if tipo == "teatro" else None,
        "tema_magia": f.get("magia") == "tema",
        "disciplina": ("magia" if f.get("magia") == "tema" else f.get("disciplina")) if tipo == "eventos" else None,
        "sala": f.get("sala"),
        "sala_interior": f.get("sala_interior"),
        "sala_id": f.get("sala_id"),
        "barrio": direccion.get("barrio"),
        "direccion": " ".join(x for x in (direccion.get("calle"), direccion.get("numero")) if x) or None,
        "lat": coord.get("lat"),
        "lon": coord.get("lon"),
        # Todas las funciones (el calendario de la app llega a dos años vista).
        "funciones": [[x["fecha"], x["hora"]] if x.get("hora") else [x["fecha"]] for x in f["proximas_funciones"]],
        "precio_min": precio.get("minimo"),
        "precio_max": precio.get("maximo"),
        "gratis": bool(precio.get("gratis")),
        "publico": f.get("publico"),
        "edad_min": f.get("edad_minima"),
        "edad_max": f.get("edad_maxima"),
        "nivel": f.get("nivel"),
        "duracion": f.get("duracion_minutos"),
        "idiomas": f.get("idiomas"),
        "descripcion": {k: _resumen(equipo.sin_creditos(v) if creditos else v) for k, v in textos.items()},
        "equipo": creditos,
        "idioma_textos": f.get("idioma_textos"),
        "compra": f.get("enlace_compra"),
        "imagen": f.get("imagen"),
        "fuente": fuente["nombre"].replace("Ajuntament de Barcelona · ", ""),
        "fuente_url": fuente.get("url"),
        "comprobado": fuente.get("comprobado"),
    })


def exportar(ciudad, informe: dict, mapa: dict | None = None, leer_webs: bool = True) -> dict:
    """Escribe el archivo de la ciudad (y su mapa, si la fuente lo da) y actualiza el índice."""
    if mapa:
        CARPETA_WEB.mkdir(parents=True, exist_ok=True)
        (CARPETA_WEB / f"{ciudad.id}-mapa.json").write_text(
            json.dumps({k: mapa[k] for k in ("areas", "fuente")}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
    fichas = leer_json(config.carpeta_ciudad(ciudad.id) / "espectaculos.json", [])
    items = [i for i in (_item(f) for f in fichas) if i]
    from . import enriquecer_ia  # traducción, premios citados y temas (IA)
    enriquecer_ia.aplicar(ciudad, items, informe)
    from . import fichas_personas  # trayectoria y premios (con fuente) de los magos
    fichas_personas.aplicar(ciudad, items, informe)
    from . import compra  # página de la obra en la web de la sala, en vez de su portada
    compra.aplicar(ciudad, items, informe, leer_webs=leer_webs)
    # Verificador: nada sale en la app sin pasar las comprobaciones (pipeline/verificar.py).
    from . import verificar
    mapa_ciudad = mapa or leer_json(CARPETA_WEB / f"{ciudad.id}-mapa.json", None)
    hoy = dt.date.fromisoformat(informe["fecha"]) if informe.get("fecha") else dt.date.today()
    informe["verificacion"] = verificar.escena(ciudad, items, fichas, mapa_ciudad, hoy)
    # Ficha completa desde la página oficial de cada obra (comprueba cada dato con su cita) y, de las
    # personas del equipo, foto y premios de Wikidata.
    from . import fichas_obra, personas
    fichas_obra.aplicar(ciudad, items, informe, leer_webs=leer_webs)
    personas_app = personas.aplicar(ciudad, items, informe, leer_webs=leer_webs)
    items.sort(key=lambda i: (i["funciones"][0][0], (i["funciones"][0] + [""])[1]))
    datos = {
        "ciudad": ciudad.ficha(),
        "actualizado": informe.get("fecha"),
        "licencia": "Datos: Ajuntament de Barcelona (Open Data BCN y Guia BCN), CC BY 4.0",
        "espectaculos": items,
        "personas": personas_app,
    }
    # Compacto (sin espacios): es lo que descarga el móvil.
    ruta = CARPETA_WEB / f"{ciudad.id}.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(ruta)
    indice = leer_json(CARPETA_WEB / "ciudades.json", {}) or {}
    indice[ciudad.id] = {**ciudad.ficha(), "actualizado": informe.get("fecha"), "espectaculos": len(items)}
    guardar_json(CARPETA_WEB / "ciudades.json", indice)
    return {"espectaculos_app": len(items), **{k: informe[k] for k in ("ia_fichas", "fichas_personas", "compra", "verificacion", "fichas_obra", "personas") if k in informe}}
