"""Fuente: Ajuntament de Barcelona (Open Data BCN + Guia BCN).

1. Descarga las dos agendas por la API oficial y las une por identificador.
2. Descarga la lista oficial de equipamientos culturales (nombres de salas).
3. Lee, con su límite de velocidad, las fichas públicas de la guía que falten
   o hayan cambiado (descripción, sala, enlaces).
4. Entiende el horario (días, horas, precios) y asigna cada actividad a su sala.
5. Lo entrega todo en el formato común de pipeline/fuentes/base.py.

Notas técnicas: docs/fuentes/open-data-bcn.md
"""

from __future__ import annotations

import collections

from ... import horario, senales
from ...util import leer_json
from ..base import Contexto, Resultado, id_global
from . import agendas, descargar, guia, lugares

NOMBRE = "open_data_bcn"
DESCRIPCION = "Agendas de Open Data BCN y fichas públicas de guia.barcelona.cat"
IDIOMA_TEXTOS = "ca"

CITAS = {
    "activitats": {
        "nombre": "Ajuntament de Barcelona · Open Data BCN · Agenda d'actes i activitats",
        "url": "https://opendata-ajuntament.barcelona.cat/data/ca/dataset/agenda-diaria",
        "licencia": "CC BY 4.0",
    },
    "cultural": {
        "nombre": "Ajuntament de Barcelona · Open Data BCN · Agenda cultural",
        "url": "https://opendata-ajuntament.barcelona.cat/data/ca/dataset/agenda-cultural",
        "licencia": "CC BY 4.0",
    },
}


def _comun(a: dict, ctx: Contexto, prioridad: float) -> dict:
    """Pasa una actividad de esta fuente al formato común."""
    g = a.get("guia") or {}
    extraido = horario.interpretar(a["horario_html"], a["inicio"], a["fin"], ctx.hoy)
    if extraido["precio"]:
        extraido["precio"]["moneda"] = ctx.ciudad.moneda
    if g.get("descripcion") and not extraido["idiomas"]:
        extraido["idiomas"] = horario.leer_idiomas(g["descripcion"])
    citas = [dict(CITAS[x], comprobado=ctx.hoy.isoformat()) for x in a["agendas"]]
    if g.get("url"):
        citas.append({"nombre": "Ajuntament de Barcelona · Guia BCN (ficha pública)",
                      "url": g["url"], "comprobado": g.get("comprobado")})
    enlaces = g.get("enlaces") or []
    compra = next((e["url"] for e in enlaces if "entrad" in e["tipo"].lower() or "venda" in e["tipo"].lower()), None)
    return {
        "id": id_global(NOMBRE, a["id"]),
        "fuente": NOMBRE,
        "id_origen": a["id"],
        "ciudad": ctx.ciudad.id,
        "titulo": a["titulo"],
        "idioma_textos": IDIOMA_TEXTOS,
        "descripcion": {IDIOMA_TEXTOS: g["descripcion"]} if g.get("descripcion") else {},
        "organiza": g.get("organiza"),
        "imagen": g.get("imagen"),
        "estado": g.get("estado"),
        "inicio": a["inicio"],
        "fin": a["fin"],
        "fechas_aproximadas": a.get("fechas_aproximadas"),
        "horario": extraido,
        "horario_texto": horario.texto_plano(a["horario_html"]),
        "lugar": a["lugar"],
        "telefono": a.get("telefono"),
        "enlaces": enlaces,
        "enlace_compra": compra,
        "modificado_origen": a["modificado"],
        "detalle_leido": bool(g),
        "prioridad": prioridad,
        "fuentes": citas,
        "extra": {"agendas": a["agendas"]},
    }


def recoger(ctx: Contexto) -> Resultado:
    informe: dict = {}
    if ctx.descargar:
        informe["descarga"] = descargar.descargar(ctx.carpeta_descargas)
        equipamientos = lugares.descargar_equipamientos(ctx.carpeta_descargas)
    else:
        equipamientos = leer_json(ctx.carpeta_descargas / "equipamientos.json", [])
    informe["equipamientos"] = len(equipamientos)

    actividades = agendas.unir(ctx.carpeta_descargas, ctx.hoy)
    informe["actividades_vigentes"] = len(actividades)
    informe["por_agenda"] = dict(collections.Counter("+".join(sorted(a["agendas"])) for a in actividades.values()))

    # Fichas de la guía: primero las más prometedoras (espectáculos, lugares escénicos…).
    cats = lugares.categorias_por_lugar(equipamientos)
    prioridad = {i: senales.prioridad_lectura(a, cats.get(lugares.clave_lugar(a), set()))
                 for i, a in actividades.items()}
    ruta_guia = ctx.carpeta_cache / "guia.json"
    if ctx.leer_webs:
        informe["guia"] = guia.actualizar(actividades, prioridad, ruta_guia, ctx.minutos_lectura)
    cache_guia = guia.cargar(ruta_guia)
    for i, a in actividades.items():
        g = cache_guia.get(i)
        # Usamos la ficha aunque sea de una versión anterior: mejor que nada.
        a["guia"] = g if g and not g.get("no_disponible") else None

    lugares.asignar(actividades, equipamientos, ctx.ciudad.id)
    return Resultado([_comun(a, ctx, prioridad[i]) for i, a in actividades.items()], informe)
