"""Genera el informe de una prueba de magia a partir de los datos del día.

Uso: python -m pipeline.prueba_magia [ruta_de_salida.md] [ciudad]

Lista lo que el programa ha detectado, con el motivo de cada decisión, para
que Uri diga qué sobra y qué falta. Sus respuestas se convierten en criterios
generales en docs/clasificacion.md (nunca en excepciones).
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

from . import config, senales
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
    return (f"- **{titulo}** — {lugar} · {_fechas(f)}\n"
            f"  - Tipo: {tipo} · magia: {f['magia']} · seguridad: {round(f['confianza'] * 100)} %{extra}\n"
            f"  - Motivo: {f['motivo']}")


def generar(salida: Path, ciudad: str = "barcelona") -> dict:
    carpeta = config.carpeta_ciudad(ciudad)
    fichas = leer_json(carpeta / "espectaculos.json", [])
    todas = leer_json(carpeta / "clasificacion.json", {})
    informe = leer_json(carpeta / "informe.json", {})

    magia = [f for f in fichas if f["magia"] == "principal" and f["confianza"] >= UMBRAL_DUDA]
    incluye = [f for f in fichas if f["magia"] == "incluye" and f["confianza"] >= UMBRAL_DUDA]
    tema = [f for f in fichas if f["magia"] == "tema" and f["confianza"] >= UMBRAL_DUDA]
    dudosos = [f for f in fichas if f["magia"] != "no" and f["confianza"] < UMBRAL_DUDA]
    # También los espectáculos donde solo hay palabras ambiguas de magia y poca seguridad.
    dudosos += [f for f in fichas if f["magia"] == "no" and f["confianza"] <= 0.6
                and f["tipo"] in ("teatro", "circo", "danza")
                and any(p.startswith("solo palabras ambiguas de magia en el título") for p in f.get("pistas", []))]
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
        f"# Prueba de magia · {informe.get('fecha', dt.date.today().isoformat())}",
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
    ]
    lineas += [_linea(f) for f in sorted(magia, key=orden)] or ["_Ninguno._"]
    lineas += ["", f"## 2. Incluyen magia sin ser de magia ({len(incluye)})", "",
               "Espectáculos de otro tipo (circo, humor, variedades, teatro…) con números de magia.", ""]
    lineas += [_linea(f) for f in sorted(incluye, key=orden)] or ["_Ninguno._"]
    lineas += ["", f"## 3. Eventos sobre magia ({len(tema)})", "",
               "Festivales, talleres y charlas cuyo tema es la magia. Los talleres van a «Eventos › formación».", ""]
    lineas += [_linea(f) for f in sorted(tema, key=orden)] or ["_Ninguno._"]
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
    hoy = dt.date.today().isoformat()
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else config.DOCS / "pruebas" / f"{hoy}-magia.md"
    print(generar(destino, sys.argv[2] if len(sys.argv) > 2 else "barcelona"))
