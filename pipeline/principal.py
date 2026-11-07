"""Proceso diario completo. Se ejecuta solo cada mañana en GitHub Actions.

Pasos:
1. Descarga las dos agendas de Open Data BCN y los equipamientos culturales.
2. Une las agendas por identificador y descarta lo ya terminado.
3. Lee (con calma, 1 página cada 10 s) las fichas de la guía que falten o hayan cambiado.
4. Extrae días, horas, precios, duración e idioma del horario.
5. Agrupa las salas por dirección.
6. Clasifica: primero por señales; después, si hay clave, con IA (solo lo nuevo o cambiado).
7. Guarda data/espectaculos.json, data/salas.json y data/informe.json.

Uso:  python -m pipeline.principal [--sin-descarga] [--sin-guia] [--hoy AAAA-MM-DD]
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import time

from . import agendas, clasificar_ia, config, descargar, guia, horario, salas, senales
from .util import guardar_json, leer_json

TIPOS_PUBLICADOS = ("teatro", "magia", "circo", "danza", "evento", "cine")


def _ficha(a: dict, clasif: dict) -> dict:
    g = a.get("guia") or {}
    fuentes = [dict(config.FUENTE_AGENDAS[x], comprobado=a["descargado"]) for x in a["agendas"]]
    if g.get("url") and not g.get("no_disponible"):
        fuentes.append({"nombre": "Ajuntament de Barcelona · Guia BCN (ficha pública)",
                        "url": g["url"], "comprobado": g.get("comprobado")})
    enlaces = g.get("enlaces") or []
    compra = next((e["url"] for e in enlaces if "entrad" in e["tipo"].lower() or "venda" in e["tipo"].lower()), None)
    return {
        "id": a["id"],
        "titulo": a["titulo"],
        "tipo": clasif["tipo"],
        "subtipo": clasif.get("subtipo"),
        "magia": clasif["magia"],
        "confianza": clasif["confianza"],
        "motivo": clasif["motivo"],
        "clasificado_por": clasif["clasificado_por"],
        "descripcion_ca": g.get("descripcion"),
        "organiza": g.get("organiza"),
        "imagen": g.get("imagen"),
        "estado": g.get("estado"),
        "inicio": a["inicio"],
        "fin": a["fin"],
        "fechas_aproximadas": a.get("fechas_aproximadas"),
        "proximas_funciones": a["extraido"]["proximas_funciones"],
        "horario": [f["texto"] for f in a["extraido"]["filas"]],
        "precio": a["extraido"]["precio"],
        "duracion_minutos": a["extraido"]["duracion_minutos"],
        "idiomas": a["extraido"]["idiomas"],
        "sala_id": a.get("sala_id"),
        "sala": a.get("sala"),
        "sala_interior": a.get("sala_interior"),
        "direccion": a["direccion"],
        "coordenadas": a["coordenadas"],
        "telefono": a.get("telefono"),
        "enlace_compra": compra,
        "enlaces": enlaces,
        "agendas": a["agendas"],
        "modificado_origen": a["modificado"],
        "fuentes": fuentes,
        "ficha_guia_leida": bool(g) and not g.get("no_disponible"),
    }


def ejecutar(sin_descarga: bool = False, sin_guia: bool = False, hoy: dt.date | None = None,
             minutos_guia: float | None = None) -> dict:
    hoy = hoy or dt.date.today()
    t0 = time.monotonic()
    informe: dict = {"fecha": hoy.isoformat(), "inicio": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

    # 1. Descargas
    if not sin_descarga:
        informe["descarga"] = descargar.descargar(config.DESCARGAS)
        equipamientos = salas.descargar_equipamientos(config.DESCARGAS)
    else:
        equipamientos = leer_json(config.DESCARGAS / "equipamientos.json", [])
    informe["equipamientos"] = len(equipamientos)

    # 2. Unión
    actividades = agendas.unir(config.DESCARGAS, hoy)
    informe["actividades_vigentes"] = len(actividades)
    informe["por_agenda"] = dict(collections.Counter("+".join(sorted(a["agendas"])) for a in actividades.values()))

    # 3. Fichas de la guía
    cats = salas.categorias_por_lugar(equipamientos)
    prioridad = {i: senales.prioridad_lectura(a, cats.get(salas.clave_lugar(a), set()))
                 for i, a in actividades.items()}
    if not sin_guia:
        informe["guia"] = guia.actualizar(actividades, prioridad, minutos_guia)
    cache_guia = guia.cargar()
    for i, a in actividades.items():
        g = cache_guia.get(i)
        # Usamos la ficha aunque sea de una versión anterior: mejor que nada.
        a["guia"] = g if g and not g.get("no_disponible") else None
        a["descargado"] = hoy.isoformat()

    # 4. Extracción del horario
    for a in actividades.values():
        a["extraido"] = horario.interpretar(a["horario_html"], a["inicio"], a["fin"], hoy)
        a["horario_texto"] = horario.texto_plano(a["horario_html"])
        if a["guia"] and a["guia"].get("descripcion") and not a["extraido"]["idiomas"]:
            a["extraido"]["idiomas"] = horario.leer_idiomas(a["guia"]["descripcion"])

    # 5. Salas
    lugares = salas.agrupar(actividades, equipamientos)

    # 6. Clasificación
    por_senales = {i: senales.analizar(a) for i, a in actividades.items()}
    candidatos = [i for i, r in por_senales.items() if senales.necesita_ia(r)]
    candidatos.sort(key=lambda i: -prioridad[i])
    por_ia, informe["ia"] = clasificar_ia.clasificar(actividades, por_senales, candidatos)
    final = {}
    for i, r in por_senales.items():
        if i in por_ia:
            final[i] = por_ia[i] | {"clasificado_por": "ia", "senales": r["pistas"]}
        else:
            final[i] = r | {"clasificado_por": "señales", "senales": r["pistas"]}

    # 7. Resultados
    fichas = [_ficha(actividades[i], final[i]) for i in sorted(final)
              if final[i]["tipo"] in TIPOS_PUBLICADOS or final[i]["magia"] != "no"]
    usadas = {f["sala_id"] for f in fichas}
    salas_publicadas = {k: v for k, v in lugares.items() if k in usadas}
    for s in salas_publicadas.values():
        s["espectaculos"] = sum(1 for f in fichas if f["sala_id"] == s["id"])
    guardar_json(config.DATOS / "espectaculos.json", fichas, por_lineas=True)
    guardar_json(config.DATOS / "salas.json", salas_publicadas, por_lineas=True)
    # Todas las decisiones (también las de «otro»), para poder revisarlas.
    guardar_json(config.DATOS / "clasificacion.json",
                 {i: {"titulo": actividades[i]["titulo"], **{k: final[i].get(k) for k in
                      ("tipo", "subtipo", "magia", "confianza", "motivo", "clasificado_por")}}
                  for i in final}, por_lineas=True)

    informe["publicadas"] = len(fichas)
    informe["por_tipo"] = dict(collections.Counter(f["tipo"] for f in fichas))
    informe["magia"] = dict(collections.Counter(f["magia"] for f in fichas if f["magia"] != "no"))
    informe["clasificado_por"] = dict(collections.Counter(f["clasificado_por"] for f in fichas))
    informe["salas_con_espectaculos"] = len(salas_publicadas)
    informe["salas_con_nombre"] = sum(1 for s in salas_publicadas.values() if s["nombre"])
    informe["con_precio"] = sum(1 for f in fichas if f["precio"])
    informe["con_enlace_compra"] = sum(1 for f in fichas if f["enlace_compra"])
    informe["con_ficha_guia"] = sum(1 for f in fichas if f["ficha_guia_leida"])
    informe["con_idioma"] = sum(1 for f in fichas if f["idiomas"])
    informe["duracion_minutos"] = round((time.monotonic() - t0) / 60, 1)
    guardar_json(config.DATOS / "informe.json", informe)
    return informe


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sin-descarga", action="store_true", help="usar las descargas que ya hay")
    p.add_argument("--sin-guia", action="store_true", help="no leer fichas nuevas de la guía")
    p.add_argument("--hoy", help="fecha de referencia (AAAA-MM-DD)")
    p.add_argument("--minutos-guia", type=float, help="tiempo máximo leyendo fichas de la guía")
    args = p.parse_args()
    hoy = dt.date.fromisoformat(args.hoy) if args.hoy else None
    informe = ejecutar(args.sin_descarga, args.sin_guia, hoy, args.minutos_guia)
    print(json.dumps(informe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
