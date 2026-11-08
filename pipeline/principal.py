"""Proceso diario completo (la «recogida»). Se ejecuta solo cada mañana en GitHub Actions.

Para cada ciudad activa de ajustes/ciudades.toml:
1. Cada fuente de esa ciudad recoge sus actividades y las entrega en el
   formato común (pipeline/fuentes/base.py). Cada fuente respeta su propio
   límite de velocidad y solo relee lo nuevo o cambiado.
2. Se juntan las actividades de todas las fuentes.
3. Se clasifican: primero por señales; después, si hay clave, con la IA,
   con el modelo que diga ajustes/ia.toml para cada tarea (y los dudosos
   suben a un modelo superior).
4. Se agrupan las salas.
5. Se guarda data/ciudades/<ciudad>/{espectaculos,salas,clasificacion,informe}.json
   y un índice general en data/indice.json.

Si una fuente falla, esa ciudad conserva los datos de ayer y el error queda
anotado en el informe. Las demás ciudades siguen.

Uso:  python -m pipeline.principal [--ciudad barcelona] [--sin-descarga] [--sin-lectura]
                                   [--minutos-lectura 35] [--hoy AAAA-MM-DD]
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
import time
import traceback

from . import ajustes, clasificar_ia, config, fuentes, publico, salas, senales
from .ajustes import Ciudad
from .fuentes.base import Contexto
from .util import guardar_json

TIPOS_PUBLICADOS = ("teatro", "magia", "circo", "danza", "evento", "cine")


def _ficha(a: dict, clasif: dict, ciudad: Ciudad) -> dict:
    l = a["lugar"]
    h = a["horario"]
    es_formacion = clasif["tipo"] == "evento" and clasif.get("subtipo") == "formación"
    destinatarios = publico.leer(a["titulo"], " ".join((a.get("descripcion") or {}).values()), es_formacion)
    return {
        "id": a["id"],
        "fuente": a["fuente"],
        "id_origen": a["id_origen"],
        "ciudad": ciudad.id,
        "pais": ciudad.pais,
        "zona_horaria": ciudad.zona_horaria,
        "titulo": a["titulo"],
        "idioma_textos": a["idioma_textos"],
        "descripcion": a["descripcion"],
        "tipo": clasif["tipo"],
        "subtipo": clasif.get("subtipo"),
        "magia": clasif["magia"],
        "confianza": clasif["confianza"],
        "motivo": clasif["motivo"],
        "clasificado_por": clasif["clasificado_por"],
        "modelo_ia": clasif.get("modelo"),
        "pistas": clasif.get("senales") or [],
        "publico": destinatarios["publico"],
        "edad_minima": destinatarios["edad_minima"],
        "edad_maxima": destinatarios["edad_maxima"],
        "nivel": destinatarios["nivel"],
        "organiza": a.get("organiza"),
        "imagen": a.get("imagen"),
        "estado": a.get("estado"),
        "inicio": a["inicio"],
        "fin": a["fin"],
        "fechas_aproximadas": a.get("fechas_aproximadas"),
        "proximas_funciones": h["proximas_funciones"],
        "horario": [f["texto"] for f in h["filas"]],
        "precio": h["precio"],
        "duracion_minutos": h["duracion_minutos"],
        "idiomas": h["idiomas"],
        "sala_id": l["clave"],
        "sala": l.get("nombre_casa") or l.get("nombre_en_fuente"),
        "sala_interior": l.get("sala_interior"),
        "direccion": l.get("direccion"),
        "coordenadas": l.get("coordenadas"),
        "telefono": a.get("telefono"),
        "enlace_compra": a.get("enlace_compra"),
        "enlaces": a.get("enlaces") or [],
        "modificado_origen": a.get("modificado_origen"),
        "detalle_leido": a.get("detalle_leido", False),
        "fuentes": a["fuentes"],
        "extra": a.get("extra") or {},
    }


def _clasificar(actividades: dict[str, dict], ciudad: Ciudad, informe: dict) -> dict[str, dict]:
    por_senales = {i: senales.analizar(a) for i, a in actividades.items()}
    candidatos = [i for i, r in por_senales.items() if senales.necesita_ia(r)]
    candidatos.sort(key=lambda i: -(actividades[i].get("prioridad") or 0))
    tareas = ajustes.tareas_ia()
    cache_ia = config.carpeta_cache(ciudad.id, "ia")
    informe["ia"] = {}

    # Tarea 1: clasificar con el modelo base.
    base, informe["ia"]["clasificar"] = clasificar_ia.clasificar(
        actividades, por_senales, candidatos, tareas["clasificar"], cache_ia, ciudad)
    # Tarea 2: los dudosos (poca confianza) suben a un modelo superior.
    revision = tareas["revisar_dudosos"]
    umbral = revision.umbral_confianza if revision.umbral_confianza is not None else 0.7
    dudosos = [i for i in candidatos if i in base and base[i]["confianza"] < umbral]
    revisados, informe["ia"]["revisar_dudosos"] = clasificar_ia.clasificar(
        actividades, por_senales, dudosos, revision, cache_ia, ciudad)

    final = {}
    for i, r in por_senales.items():
        if i in revisados:
            final[i] = revisados[i] | {"clasificado_por": "ia", "revisado": True, "senales": r["pistas"]}
        elif i in base:
            final[i] = base[i] | {"clasificado_por": "ia", "senales": r["pistas"]}
        else:
            final[i] = r | {"clasificado_por": "señales", "senales": r["pistas"]}
    return final


def ejecutar_ciudad(ciudad: Ciudad, descargar: bool = True, leer_webs: bool = True,
                    minutos_lectura: float | None = None, hoy: dt.date | None = None) -> dict:
    hoy = hoy or ciudad.hoy()
    t0 = time.monotonic()
    informe: dict = {"ciudad": ciudad.ficha(), "fecha": hoy.isoformat(),
                     "inicio": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "fuentes": {}, "errores": []}

    # 1. Recoger de cada fuente (piezas independientes)
    actividades: dict[str, dict] = {}
    for nombre in ciudad.fuentes:
        ctx = Contexto(ciudad=ciudad, hoy=hoy,
                       carpeta_descargas=config.DESCARGAS / ciudad.id / nombre,
                       carpeta_cache=config.carpeta_cache(ciudad.id, nombre),
                       descargar=descargar, leer_webs=leer_webs, minutos_lectura=minutos_lectura)
        try:
            resultado = fuentes.cargar(nombre).recoger(ctx)
        except Exception as e:  # noqa: BLE001 - una fuente rota no debe parar las demás
            informe["errores"].append(f"{nombre}: {type(e).__name__}: {e}")
            informe["fuentes"][nombre] = {"error": traceback.format_exc(limit=3)}
            continue
        informe["fuentes"][nombre] = resultado.informe
        # 2. Juntar. Pendiente para cuando haya una 2.ª fuente en la misma ciudad:
        # detectar la misma obra en varias fuentes y dejar una sola ficha (principio 4).
        for a in resultado.actividades:
            actividades[a["id"]] = a

    if informe["errores"]:
        # Mejor los datos de ayer completos que los de hoy a medias.
        informe["aviso"] = "Alguna fuente ha fallado: se conservan los resultados anteriores de esta ciudad."
        guardar_json(config.carpeta_ciudad(ciudad.id) / "informe_fallo.json", informe)
        return informe
    informe["actividades_vigentes"] = len(actividades)

    # 3. Clasificar
    final = _clasificar(actividades, ciudad, informe)

    # 4. Salas y 5. Resultados
    fichas = [_ficha(actividades[i], final[i], ciudad) for i in sorted(final)
              if final[i]["tipo"] in TIPOS_PUBLICADOS or final[i]["magia"] != "no"]
    lugares = salas.consolidar(list(actividades.values()))
    publicadas = collections.Counter(f["sala_id"] for f in fichas)
    salas_publicadas = {k: v | {"espectaculos": publicadas[k]} for k, v in lugares.items() if k in publicadas}

    carpeta = config.carpeta_ciudad(ciudad.id)
    guardar_json(carpeta / "espectaculos.json", fichas, por_lineas=True)
    guardar_json(carpeta / "salas.json", salas_publicadas, por_lineas=True)
    # Todas las decisiones (también las de «otro»), para poder revisarlas.
    guardar_json(carpeta / "clasificacion.json",
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
    informe["con_detalle"] = sum(1 for f in fichas if f["detalle_leido"])
    informe["con_idioma"] = sum(1 for f in fichas if f["idiomas"])
    informe["con_publico"] = sum(1 for f in fichas if f["publico"])
    informe["duracion_minutos"] = round((time.monotonic() - t0) / 60, 1)
    guardar_json(carpeta / "informe.json", informe)
    (carpeta / "informe_fallo.json").unlink(missing_ok=True)
    return informe


def ejecutar(solo: str | None = None, **opciones) -> dict:
    indice = {"actualizado": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "ciudades": {}}
    for ciudad in ajustes.ciudades().values():
        if (solo and ciudad.id != solo) or (not solo and not ciudad.activa):
            continue
        try:
            inf = ejecutar_ciudad(ciudad, **opciones)
        except Exception as e:  # noqa: BLE001
            inf = {"errores": [f"{type(e).__name__}: {e}"], "detalle": traceback.format_exc(limit=5)}
        indice["ciudades"][ciudad.id] = {
            **ciudad.ficha(),
            "fecha": inf.get("fecha"),
            "espectaculos": inf.get("publicadas"),
            "salas": inf.get("salas_con_espectaculos"),
            "errores": inf.get("errores", []),
        }
    if not solo:
        guardar_json(config.DATOS / "indice.json", indice)
    return indice


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ciudad", help="procesar solo esta ciudad (clave de ajustes/ciudades.toml)")
    p.add_argument("--sin-descarga", action="store_true", help="usar las descargas que ya hay")
    p.add_argument("--sin-lectura", "--sin-guia", action="store_true", help="no leer páginas web nuevas")
    p.add_argument("--minutos-lectura", "--minutos-guia", type=float, help="tiempo máximo leyendo webs por fuente")
    p.add_argument("--hoy", help="fecha de referencia (AAAA-MM-DD); por defecto, la de cada ciudad")
    args = p.parse_args()
    indice = ejecutar(args.ciudad, descargar=not args.sin_descarga, leer_webs=not args.sin_lectura,
                      minutos_lectura=args.minutos_lectura,
                      hoy=dt.date.fromisoformat(args.hoy) if args.hoy else None)
    print(json.dumps(indice, ensure_ascii=False, indent=2))
    # Código de salida distinto de 0 si algo falló, para que se vea en GitHub (los datos ya están guardados).
    sys.exit(1 if any(c["errores"] for c in indice["ciudades"].values()) else 0)


if __name__ == "__main__":
    main()
