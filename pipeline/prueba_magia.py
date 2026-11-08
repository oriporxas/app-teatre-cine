"""Genera el informe de una prueba de magia a partir de los datos del día.

Uso: python -m pipeline.prueba_magia [salida.md] [--ciudad barcelona] [--respuestas respuestas.json]

Lista lo que el programa ha detectado, con el motivo de cada decisión, para
que Uri diga qué sobra y qué falta. Sus respuestas se convierten en criterios
generales en docs/clasificacion.md (nunca en excepciones) y se guardan como
datos de evaluación (docs/pruebas/*-respuestas-uri.json): con --respuestas, el
informe mide cuántas decisiones coinciden con lo que dijo Uri.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
from pathlib import Path

from . import config, publico, senales
from .util import leer_json

UMBRAL_DUDA = 0.65


def _fechas(f: dict) -> str:
    ini, fin = f.get("inicio"), f.get("fin")
    if not ini:
        return "sin fechas"
    a = dt.date.fromisoformat(ini).strftime("%d/%m/%Y")
    if not fin or fin == ini:
        return a
    return f"{a} – {dt.date.fromisoformat(fin).strftime('%d/%m/%Y')}"


def _linea(f: dict) -> str:
    lugar = f.get("sala") or "sala sin identificar"
    if f.get("sala_interior"):
        lugar += f" ({f['sala_interior']})"
    enlace = next((x["url"] for x in f.get("fuentes", []) if "guia.barcelona.cat" in x.get("url", "")), None)
    titulo = f"[{f['titulo']}]({enlace})" if enlace else f["titulo"]
    tipo = f["tipo"] + (f" › {f['subtipo']}" if f.get("subtipo") else "")
    extra = "" if f.get("detalle_leido") else " · ⚠️ sin descripción leída todavía"
    destinatarios = publico.etiqueta(f)
    return (f"- **{titulo}** — {lugar} · {_fechas(f)}\n"
            f"  - Tipo: {tipo} · magia: {f['magia']} · seguridad: {round(f['confianza'] * 100)} %{extra}\n"
            + (f"  - Público: {destinatarios}\n" if destinatarios else "")
            + f"  - Motivo: {f['motivo']}")


def comparar(todas: dict, ruta_respuestas: Path) -> tuple[list[str], dict]:
    """Compara las decisiones de hoy con las respuestas de Uri. «incluye» cuenta como «no»
    porque no sale al buscar magia."""
    datos = json.loads(ruta_respuestas.read_text(encoding="utf-8"))
    aciertos, fallos, ausentes = [], [], []
    for e in datos["etiquetas"]:
        c = todas.get(e["id"])
        if c is None:
            ausentes.append(e)
            continue
        obtenido = "no" if c["magia"] == "incluye" else c["magia"]
        (aciertos if obtenido == e["esperado"] else fallos).append((e, c, obtenido))
    total = len(aciertos) + len(fallos)
    por_clase = collections.Counter(e["esperado"] for e, _, _ in aciertos)
    clases = collections.Counter(e["esperado"] for e, _, _ in aciertos + fallos)
    lineas = [
        f"## Comparación con tus respuestas ({ruta_respuestas.name})",
        "",
        f"- **Coinciden {len(aciertos)} de {total}** decisiones con lo que dijiste"
        + (f" ({round(100 * len(aciertos) / total)} %)." if total else "."),
        f"- Espectáculos de magia: {por_clase['principal']} de {clases['principal']} · "
        f"eventos sobre magia: {por_clase['tema']} de {clases['tema']} · "
        f"no son magia: {por_clase['no']} de {clases['no']}.",
    ]
    if ausentes:
        lineas.append(f"- {len(ausentes)} ya no están en la agenda (han terminado) y no se cuentan.")
    lineas += ["", "Las que todavía no coinciden:", ""]
    nombres = {"principal": "espectáculo de magia", "tema": "evento sobre magia", "no": "no es magia"}
    for e, c, obtenido in fallos:
        lineas.append(f"- **{e['titulo']}**: tú dijiste «{nombres[e['esperado']]}», el programa dice "
                      f"«{nombres.get(obtenido, obtenido)}» — {c['motivo']}")
    if not fallos:
        lineas.append("_Ninguna._")
    return lineas, {"coinciden": len(aciertos), "total": total, "no_coinciden": len(fallos)}


def generar(salida: Path, ciudad: str = "barcelona", respuestas: Path | None = None) -> dict:
    carpeta = config.carpeta_ciudad(ciudad)
    fichas = leer_json(carpeta / "espectaculos.json", [])
    todas = leer_json(carpeta / "clasificacion.json", {})
    informe = leer_json(carpeta / "informe.json", {})

    magia = [f for f in fichas if f["magia"] == "principal" and f["confianza"] >= UMBRAL_DUDA]
    incluye = [f for f in fichas if f["magia"] == "incluye" and f["confianza"] >= UMBRAL_DUDA]
    tema = [f for f in fichas if f["magia"] == "tema" and f["confianza"] >= UMBRAL_DUDA]
    dudosos = [f for f in fichas if f["magia"] != "no" and f["confianza"] < UMBRAL_DUDA]
    # Descartados que mencionan magia (para que se vea qué se ha dejado fuera y por qué)
    descartados = []
    ids_dudosos = {f["id"] for f in dudosos}
    por_id = {f["id"]: f for f in fichas}
    suena_a_magia = re.compile(r"\bm[àáa]gi|\bmagic|\bil+usi|\bhipno|\bmentalis|\bprestidigit", re.I)
    for i, c in todas.items():
        if c["magia"] != "no" or i in ids_dudosos:
            continue
        t = senales.minus(c["titulo"])
        if suena_a_magia.search(t) or senales.MAGIA_PERSONA.search(t):
            descartados.append((i, c))
    orden = lambda f: (f.get("inicio") or "", f["titulo"])  # noqa: E731

    por = informe.get("clasificado_por", {})
    lineas = [
        f"# Prueba de magia · {informe.get('fecha', dt.date.today().isoformat())}"
        + (" · medición con tus respuestas" if respuestas else ""),
        "",
        "Lista generada automáticamente por el programa (`python -m pipeline.prueba_magia`) con los "
        "datos de hoy de Open Data BCN y de la guía del Ayuntamiento. **No está retocada a mano.**",
        "",
        "## Cómo se ha hecho",
        "",
        f"- Actividades vigentes en las dos agendas: **{informe.get('actividades_vigentes', '?')}**.",
        f"- Clasificadas como espectáculo o evento del sector: **{informe.get('publicadas', '?')}**.",
        f"- Fichas de la guía leídas (descripción, sala, artista): **{informe.get('con_detalle', '?')}** "
        "de las publicadas. Las demás se han clasificado solo por el título.",
        "- Quién ha decidido: " + (", ".join(f"{k}: {v}" for k, v in por.items()) or "?") + ".",
    ]
    if "señales" in por and "ia" not in por:
        lineas += [
            "- ⚠️ **Todavía no hay clave de la IA**, así que esta prueba usa la primera capa "
            "(«señales»: vocabulario general de magia, formato del título, artista y descripción). "
            "Cuando se active la IA, leerá los mismos criterios y además estas respuestas tuyas.",
        ]
    lineas += [
        f"- «Dudoso» = el programa se ha decidido, pero con una seguridad menor del {round(UMBRAL_DUDA * 100)} %.",
        "",
        f"## 1. Espectáculos de magia ({len(magia)})",
        "",
        "Son los que salen al buscar magia. Cada uno lleva la etiqueta de su tipo de magia.",
        "",
    ]
    for sub in senales.SUBTIPOS_MAGIA:
        grupo = [f for f in magia if (f.get("subtipo") or "magia general") == sub]
        if grupo:
            lineas += [f"### {sub[0].upper() + sub[1:]} ({len(grupo)})", ""]
            lineas += [_linea(f) for f in sorted(grupo, key=orden)] + [""]
    if not magia:
        lineas.append("_Ninguno._")
    lineas += ["", f"## 2. Incluyen magia sin ser de magia ({len(incluye)})", "",
               "Espectáculos de otro tipo (circo, humor, divulgación…) con algún número de magia. "
               "**No salen al buscar magia.**", ""]
    lineas += [_linea(f) for f in sorted(incluye, key=orden)] or ["_Ninguno._"]
    lineas += ["", f"## 3. Eventos sobre magia ({len(tema)})", "",
               "Festivales, talleres y charlas cuyo tema es la magia, separados por tipo de evento y con "
               "el público al que van dirigidos. Los talleres van a «Eventos › formación».", ""]
    por_subtipo = collections.defaultdict(list)
    for f in tema:
        por_subtipo[f.get("subtipo") or "otros"].append(f)
    for sub in sorted(por_subtipo):
        lineas += [f"### {sub[0].upper() + sub[1:]} ({len(por_subtipo[sub])})", ""]
        lineas += [_linea(f) for f in sorted(por_subtipo[sub], key=lambda f: (f.get("edad_minima") or 99, f["titulo"]))] + [""]
    if not tema:
        lineas.append("_Ninguno._")
    lineas += ["", f"## 4. Dudosos ({len(dudosos)})", ""]
    lineas += [_linea(f) for f in sorted(dudosos, key=orden)] or ["_Ninguno._"]
    lineas += ["", f"## 5. Descartados aunque el título suena a magia ({len(descartados)})", "",
               "Para que veas qué se ha dejado fuera y por qué (adjetivos como «màgic», metáforas, "
               "fuentes, rutas…).", ""]
    for i, c in sorted(descartados, key=lambda x: x[1]["titulo"]):
        f = por_id.get(i)
        lugar = f" — {f['sala']}" if f and f.get("sala") else ""
        lineas.append(f"- **{c['titulo']}**{lugar} · tipo: {c['tipo']} — {c['motivo']}")
    if not descartados:
        lineas.append("_Ninguno._")
    if respuestas:
        lineas_cmp, resumen = comparar(todas, respuestas)
        lineas += [""] + lineas_cmp + [""]
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text("\n".join(lineas), encoding="utf-8")
        return {"magia": len(magia), "incluye": len(incluye), "tema": len(tema),
                "dudosos": len(dudosos), "descartados": len(descartados), **resumen}
    lineas += [
        "",
        "## Lo que necesito que me digas (una sola vez)",
        "",
        "1. **¿Sobra alguno** en las listas 1, 2 o 3? Dime cuál y, si puedes, por qué.",
        "2. **¿Falta alguno** que conozcas y esté en cartel en Barcelona estos meses?",
        "3. **Los que «incluyen magia»:** ¿quieres que salgan cuando alguien busque «magia»?",
        "4. **Los dudosos:** ¿qué son? (magia, incluye magia, o nada que ver).",
        "5. **Hipnosis de espectáculo:** ¿cuenta como magia?",
        "",
        "Con tus respuestas ajustaré los criterios generales de `docs/clasificacion.md` "
        "(nunca reglas para un espectáculo concreto) y repetiré la medición.",
        "",
    ]
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text("\n".join(lineas), encoding="utf-8")
    return {"magia": len(magia), "incluye": len(incluye), "tema": len(tema),
            "dudosos": len(dudosos), "descartados": len(descartados)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("salida", nargs="?", type=Path)
    p.add_argument("--ciudad", default="barcelona")
    p.add_argument("--respuestas", type=Path, help="respuestas de Uri para medir la coincidencia")
    args = p.parse_args()
    destino = args.salida or config.DOCS / "pruebas" / f"{dt.date.today().isoformat()}-magia.md"
    print(generar(destino, args.ciudad, args.respuestas))
