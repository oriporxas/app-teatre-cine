"""Prueba de los modelos de IA antes de activarla (brief: «Visión a largo plazo»).

Clasifica con cada modelo (y nivel de esfuerzo) las mismas actividades y compara:
- A) las 55 respuestas de Uri a la prueba de magia (aciertos sobre 55);
- B) una muestra de casos difíciles para las reglas (dudosos, musicales, danza,
  clown…): no hay respuesta «correcta» guardada, así que se mide en qué coinciden
  los modelos y se listan los desacuerdos para que Uri los juzgue;
y el coste de cada uno: el de la prueba, el de clasificar la primera vez toda la
cartelera y el de cada mes (solo lo nuevo), con y sin procesamiento por lotes.

Uso:  python -m pipeline.comparar_modelos salida.md [--configs haiku:low,opus:low] [--muestra 40] [--sin-ia]
Con --sin-ia solo prepara las actividades y estima el tamaño (no gasta nada).
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import time
from pathlib import Path

from . import ajustes, clasificar_ia, config, fuentes, senales
from .ajustes import TareaIA
from .fuentes.base import Contexto

# Precio por millón de tokens (entrada, salida), según la referencia de la API (oct. 2026).
# Leer de la caché cuesta el 10 % de la entrada y escribir en ella, el 125 %.
PRECIOS = {"claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.00, 10.00), "claude-opus-5-5": (4.00, 20.00)}
NOMBRES = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
CONFIGS = "haiku:low,haiku:medium,sonnet:low,sonnet:medium,opus:low,opus:medium"
NUEVAS_AL_DIA = 150  # actividades nuevas o cambiadas al día que pasarían por la IA (aprox.)


def _coste(modelo: str, inf: dict) -> float:
    pe, ps = PRECIOS[modelo]
    return (inf["tokens_entrada"] * pe + inf["tokens_cache"] * pe * 0.1
            + inf.get("tokens_cache_escritura", 0) * pe * 1.25 + inf["tokens_salida"] * ps) / 1e6


def _actividades(ciudad, hoy) -> dict[str, dict]:
    ctx = Contexto(ciudad=ciudad, hoy=hoy, carpeta_descargas=config.DESCARGAS / ciudad.id / "open_data_bcn",
                   carpeta_cache=config.carpeta_cache(ciudad.id, "open_data_bcn"), descargar=False, leer_webs=False)
    return {a["id"]: a for a in fuentes.cargar("open_data_bcn").recoger(ctx).actividades}


def _muestra_dificil(senal: dict, excluir: set[str], n: int) -> list[str]:
    """Casos en los que las reglas dudan o que la app decidió hace poco (musical, danza, clown…)."""
    def dificil(r: dict) -> bool:
        return senales.necesita_ia(r) and (r["confianza"] < 0.7 or r["tipo"] in ("musical", "danza")
                                           or r.get("subtipo") == "clown" or r.get("disciplina") in ("danza", "musical", "música"))
    ids = [i for i, r in senal.items() if i not in excluir and dificil(r)]
    ids.sort(key=lambda i: hashlib.sha1(i.encode()).hexdigest())  # muestra fija, sin elegir a mano
    return ids[:n]


def ejecutar(salida: Path, configs: str, muestra: int, sin_ia: bool) -> dict:
    ciudad = ajustes.ciudades()["barcelona"]
    hoy = ciudad.hoy()
    actividades = _actividades(ciudad, hoy)
    senal = {i: senales.analizar(a) for i, a in actividades.items()}
    respuestas = json.loads((config.DOCS / "pruebas" / "2026-11-08-respuestas-uri.json").read_text(encoding="utf-8"))
    etiquetas = [e for e in respuestas["etiquetas"] if e["id"] in actividades]
    ids_a = [e["id"] for e in etiquetas]
    ids_b = _muestra_dificil(senal, set(ids_a), muestra)
    candidatas = [i for i, r in senal.items() if senales.necesita_ia(r)]
    resumen = {"actividades": len(actividades), "A": len(ids_a), "A_sin_actividad": len(respuestas["etiquetas"]) - len(ids_a),
               "B": len(ids_b), "candidatas_ia": len(candidatas)}
    if sin_ia:
        caracteres = sum(len(json.dumps(clasificar_ia._entrada(actividades[i], senal[i]), ensure_ascii=False))
                         for i in ids_a + ids_b)
        resumen["tokens_entrada_aprox"] = caracteres // 3 + len(clasificar_ia.criterios()) // 3
        return resumen
    if not clasificar_ia.disponible():
        raise SystemExit("Falta la clave de la IA (ANTHROPIC_API_KEY).")

    carpeta = config.carpeta_cache(ciudad.id, "ia") / "pruebas"
    resultados: dict[str, dict] = {}
    for cfg in configs.split(","):
        corto, esfuerzo = cfg.split(":")
        modelo = NOMBRES[corto]
        tarea = TareaIA(nombre=f"prueba-{corto}-{esfuerzo}", modelo=modelo, esfuerzo=esfuerzo,
                        por_peticion=10, maximo_por_ejecucion=10000)
        t0 = time.monotonic()
        res, inf = clasificar_ia.clasificar(actividades, senal, ids_a + ids_b, tarea, carpeta, ciudad)
        inf["segundos"] = round(time.monotonic() - t0, 1)
        inf["coste"] = _coste(modelo, inf)
        resultados[cfg] = {"modelo": modelo, "esfuerzo": esfuerzo, "res": res, "inf": inf}

    # --- A) Aciertos con las respuestas de Uri («incluye» cuenta como «no»)
    def relacion(r: dict | None) -> str | None:
        if not r:
            return None
        return "no" if r["magia"] == "incluye" else r["magia"]

    filas = []
    for cfg, d in resultados.items():
        fallos = [(e, relacion(d["res"].get(e["id"]))) for e in etiquetas if relacion(d["res"].get(e["id"])) != e["esperado"]]
        d["fallos"] = fallos
        enviadas = max(1, d["inf"]["enviadas"])
        # Coste de una actividad, con lo que se pagó de verdad en la prueba (solo las enviadas)
        por_actividad = d["inf"]["coste"] / enviadas if d["inf"]["enviadas"] else 0.0
        d["por_actividad"] = por_actividad
        filas.append((cfg, len(etiquetas) - len(fallos), por_actividad, d))

    # Estrategia de dos pasos: el barato decide y lo dudoso (confianza < 0,7) lo revisa el mejor
    combinadas = []
    baratos = [c for c in resultados if c.startswith("haiku")]
    caros = [c for c in resultados if c.startswith("opus")] + [c for c in resultados if c.startswith("sonnet")]
    for b in baratos:
        for c in caros:
            rb, rc = resultados[b]["res"], resultados[c]["res"]
            dudosos = [i for i in ids_a + ids_b if rb.get(i) and rb[i]["confianza"] < 0.7]
            final = {i: (rc.get(i) if i in dudosos else rb.get(i)) for i in ids_a + ids_b}
            aciertos = sum(1 for e in etiquetas if relacion(final.get(e["id"])) == e["esperado"])
            parte = len(dudosos) / max(1, len(ids_a + ids_b))
            coste = resultados[b]["por_actividad"] + parte * resultados[c]["por_actividad"]
            combinadas.append((f"{b} + {c} (dudosos)", aciertos, coste, parte))

    # --- B) Coincidencias entre modelos en los casos difíciles
    def etiqueta(r: dict | None) -> str:
        if not r:
            return "—"
        t = r["tipo"] + (f" › {r['subtipo']}" if r.get("subtipo") else "") + (f" [{r['disciplina']}]" if r.get("disciplina") else "")
        return t + (f" · magia {r['magia']}" if r["magia"] != "no" else "")

    desacuerdos = []
    for i in ids_b:
        decisiones = {cfg: etiqueta(d["res"].get(i)) for cfg, d in resultados.items()}
        tipos = {cfg: (d["res"].get(i) or {}).get("tipo") for cfg, d in resultados.items()}
        if len(set(tipos.values())) > 1:
            desacuerdos.append((i, decisiones))

    # --- Informe
    nuevas_mes = NUEVAS_AL_DIA * 30
    L = [f"# Prueba de los modelos de IA ({hoy.isoformat()})", "",
         "Cada modelo clasifica las mismas actividades con los mismos criterios (`docs/clasificacion.md`).",
         f"A) Las **{len(etiquetas)} respuestas de Uri** de la prueba de magia. "
         f"B) **{len(ids_b)} casos difíciles** para las reglas (dudosos, musicales, danza, clown…), elegidos al azar de forma fija.", "",
         "## Resultados", "",
         "| Modelo y esfuerzo | Aciertos (de 55) | Coste de la prueba | Por actividad | Primera vez (toda la cartelera) | Al mes (lo nuevo) | Al mes por lotes (−50 %) | Tiempo |",
         "|---|---|---|---|---|---|---|---|"]
    for cfg, aciertos, pa, d in filas:
        L.append(f"| {cfg} | {aciertos} | {d['inf']['coste']:.3f} $ | {pa * 1000:.2f} $ / 1000 | "
                 f"{pa * len(candidatas):.2f} $ | {pa * nuevas_mes:.2f} $ | {pa * nuevas_mes / 2:.2f} $ | {d['inf']['segundos']} s |")
    if combinadas:
        L += ["", "### Dos pasos: el modelo barato decide y el bueno revisa lo dudoso", "",
              "| Combinación | Aciertos (de 55) | Por actividad | Al mes por lotes | Parte revisada |", "|---|---|---|---|---|"]
        for nombre, aciertos, coste, parte in combinadas:
            L.append(f"| {nombre} | {aciertos} | {coste * 1000:.2f} $ / 1000 | {coste * nuevas_mes / 2:.2f} $ | {parte:.0%} |")
    L += ["", f"Supuestos: {len(candidatas)} actividades pasan por la IA la primera vez; después, unas {NUEVAS_AL_DIA} "
          "nuevas o cambiadas al día. Precios por millón de tokens: Haiku 5.5 0,10 $ / 0,50 $; Sonnet 5.5 2 $ / 10 $; "
          "Opus 5.5 4 $ / 20 $. Los lotes nocturnos cuestan la mitad.", "", "## Fallos en las respuestas de Uri", ""]
    for cfg, d in resultados.items():
        if d["fallos"]:
            L.append(f"**{cfg}:** " + "; ".join(f"{e['titulo']} (Uri: {e['esperado']}, modelo: {o or 'sin respuesta'})" for e, o in d["fallos"]))
        else:
            L.append(f"**{cfg}:** ninguno.")
    L += ["", f"## Casos difíciles en los que los modelos no coinciden en el tipo ({len(desacuerdos)} de {len(ids_b)})", ""]
    if desacuerdos:
        L.append("| Actividad | " + " | ".join(resultados) + " |")
        L.append("|---|" + "---|" * len(resultados))
        for i, dec in desacuerdos:
            L.append(f"| {actividades[i]['titulo'][:70]} | " + " | ".join(dec[c] for c in resultados) + " |")
    salida.write_text("\n".join(L) + "\n", encoding="utf-8")
    resumen.update({cfg: {"aciertos": a, "coste_prueba": round(d["inf"]["coste"], 4), "por_1000": round(pa * 1000, 3)}
                    for cfg, a, pa, d in filas})
    resumen["desacuerdos_B"] = len(desacuerdos)
    return resumen


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("salida", type=Path, nargs="?", default=Path("docs/pruebas/prueba-modelos.md"))
    p.add_argument("--configs", default=CONFIGS, help=f"modelo:esfuerzo separados por comas (por defecto {CONFIGS})")
    p.add_argument("--muestra", type=int, default=40, help="casos difíciles (B)")
    p.add_argument("--sin-ia", action="store_true", help="solo preparar y estimar, sin llamar a la IA")
    a = p.parse_args()
    print(json.dumps(ejecutar(a.salida, a.configs, a.muestra, a.sin_ia), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
