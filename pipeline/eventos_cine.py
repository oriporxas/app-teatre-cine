"""Eventos de cine (Uri, 19/11/2026: «suelen haber bastantes festivales de cine o ceremonias de premios
de cortometrajes»).

La agenda municipal trae muchas actividades de cine: proyecciones sueltas, pero también festivales
(L'Alternativa, Mostra de Films de Dones…), ciclos, cinefórums con coloquio, concursos y galas de
premios, y talleres o charlas sobre cine. Antes, los festivales salían en Cine como si fueran una
película y los talleres no salían. Aquí la IA (modelo barato, por lotes) decide cuáles son **eventos**
y de qué tipo; esos salen como eventos de cine (con su tipo: festival, formación, charla, premios…).
Las proyecciones sueltas siguen en la cartelera de Cine.

Candidatas (sin listas hechas a mano): lo que la clasificación ya dio como cine y lo que menciona el
cine en el título o la descripción (la IA decide; la palabra sola no basta). Cada actividad se pregunta
una vez y solo se vuelve a preguntar si cambia su texto.
"""

from __future__ import annotations

import json
import re

from . import ajustes, config, ia
from .util import guardar_json, huella, leer_json

TIPOS = ["festival", "formación", "conferencia o coloquio", "premios", "convocatoria", "estreno", "proyección", "no es de cine"]
CONFIANZA_MINIMA = 0.7
PISTA = re.compile(r"\b(cine|cinema|film|films|filmoteca|pel[·.]?l[ií]cul|pel[ií]cul|curtmetratg|cortometraj|documental|"
                   r"cinef[oò]rum|projecci|proyecci|audiovisual)", re.I)
ESQUEMA = {
    "type": "object",
    "properties": {"actividades": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "tipo": {"type": "string", "enum": TIPOS},
                       "confianza": {"type": "number"}},
        "required": ["id", "tipo", "confianza"], "additionalProperties": False}}},
    "required": ["actividades"], "additionalProperties": False,
}
SISTEMA = (
    "Te doy actividades de la agenda cultural de una ciudad (título y descripción, a menudo en catalán). "
    "Para cada una, di qué es, mirando lo que describe y no solo las palabras:\n"
    "- «festival»: un festival, muestra, ciclo o maratón de cine (varias proyecciones bajo un mismo nombre).\n"
    "- «formación»: un taller, curso o clase sobre cine o para hacer cine (guion, rodaje, análisis…).\n"
    "- «conferencia o coloquio»: una charla, debate o cinefórum en el que se habla de cine (una proyección "
    "seguida de coloquio también cuenta).\n"
    "- «premios»: una gala o entrega de premios de cine.\n"
    "- «convocatoria»: un concurso o llamada a participar (p. ej., de cortometrajes).\n"
    "- «estreno»: el preestreno o estreno de una película con su equipo.\n"
    "- «proyección»: la proyección de una película sin nada más (no es un evento).\n"
    "- «no es de cine»: si el cine no es lo principal (una exposición, un concierto, un taller de otra cosa…).\n"
    "«confianza» entre 0 y 1. No inventes nada."
)


def _candidatas(actividades: dict[str, dict], final: dict[str, dict]) -> list[str]:
    res = []
    for i, c in final.items():
        a = actividades.get(i) or {}
        texto = f"{a.get('titulo', '')} {(a.get('descripcion') or {}).get('ca', '')[:300]} {(a.get('descripcion') or {}).get('es', '')[:300]}"
        if c.get("tipo") == "cine" or (c.get("tipo") in ("otro", "evento") and c.get("disciplina") in (None, "cine", "otra")
                                       and PISTA.search(texto)):
            res.append(i)
    return res


def revisar(actividades: dict[str, dict], final: dict[str, dict], ciudad, informe: dict) -> None:
    """Marca como eventos de cine (tipo «evento», disciplina «cine») las actividades que lo son."""
    tarea = ajustes.tareas_ia().get("eventos_cine")
    carpeta = config.carpeta_cache(ciudad.id, "ia")
    ruta = carpeta / "eventos_cine.json"
    cache = leer_json(ruta, {}) or {}
    candidatas = _candidatas(actividades, final)
    firma = huella(SISTEMA, tarea.modelo if tarea else "", tarea.esfuerzo if tarea else "")
    entradas, huellas = {}, {}
    for i in candidatas:
        a = actividades[i]
        desc = a.get("descripcion") or {}
        entradas[i] = {"id": i, "titulo": a.get("titulo", ""),
                       "descripcion": (desc.get("ca") or desc.get("es") or next(iter(desc.values()), ""))[:600]}
        huellas[i] = huella(entradas[i], firma)
    pendientes = [i for i in candidatas if cache.get(i, {}).get("huella") != huellas[i]]
    inf = {"candidatas": len(candidatas), "pendientes": len(pendientes), "eventos": 0}
    if pendientes and tarea and tarea.activa and ia.disponible():
        lotes = ia.Lotes("eventos_cine", carpeta)
        en_curso = {i for d in lotes.datos_en_curso() for i in (d or {})}
        nuevos = [i for i in pendientes if i not in en_curso][: tarea.maximo_por_ejecucion]
        peticiones = {}
        for n in range(0, len(nuevos), tarea.por_peticion):
            lote = nuevos[n:n + tarea.por_peticion]
            peticiones[str(n)] = (json.dumps([entradas[i] for i in lote], ensure_ascii=False), {i: huellas[i] for i in lote})
        try:
            if tarea.por_lotes:
                lotes.enviar(None, modelo=tarea.modelo, esfuerzo=tarea.esfuerzo, sistema=SISTEMA, esquema=ESQUEMA,
                             peticiones=peticiones)
                lotes.esperar()
                respuestas = lotes.recogidas
            else:
                cli = ia.cliente()
                respuestas = [(ia.pedir_json(cli, tarea="eventos_cine", modelo=tarea.modelo, esfuerzo=tarea.esfuerzo,
                                             sistema=SISTEMA, mensaje=m, esquema=ESQUEMA), d) for m, d in peticiones.values()]
        except ia.TopeDeGasto as e:
            inf["aviso"], respuestas = str(e), lotes.recogidas
        except Exception as e:  # noqa: BLE001 - sin IA hoy: se pregunta mañana
            inf["error"], respuestas = f"{type(e).__name__}: {str(e)[:150]}", lotes.recogidas
        for r, pedidas in respuestas:
            for x in (r or {}).get("actividades", []):
                # Solo si la actividad sigue igual que cuando se preguntó.
                if x.get("id") in (pedidas or {}) and huellas.get(x["id"]) == pedidas[x["id"]]:
                    cache[x["id"]] = {"huella": huellas[x["id"]], "tipo": x["tipo"],
                                      "confianza": max(0.0, min(1.0, float(x.get("confianza") or 0)))}
        guardar_json(ruta, {k: v for k, v in cache.items() if k in actividades}, por_lineas=True)
    for i in candidatas:
        c = cache.get(i)
        if not c or c.get("huella") != huellas[i] or c["tipo"] in ("proyección", "no es de cine") \
                or c["confianza"] < CONFIANZA_MINIMA:
            continue
        final[i] = final[i] | {"tipo": "evento", "disciplina": "cine", "subtipo": c["tipo"],
                               "confianza": max(final[i].get("confianza") or 0, c["confianza"]),
                               "evento_cine": True}
        inf["eventos"] += 1
    informe.setdefault("ia", {})["eventos_cine"] = inf
