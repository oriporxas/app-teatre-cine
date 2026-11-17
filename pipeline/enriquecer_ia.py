"""La IA completa las fichas de la app (teatro, magia, circo y eventos).

Para cada actividad publicada, con el texto que se ve en la app:
- **Traducción** al otro idioma de la app (la agenda viene casi siempre en catalán).
- **Premios y reconocimientos que cita la descripción** («Premi Max 2024 al millor
  espectacle…»). Principio 4: solo se aceptan si la cita literal está en el texto; si la
  IA devuelve algo que no aparece, se descarta.
- **Temas** de la obra (de 1 a 3, como «familia», «memoria histórica»), solo si la
  descripción los deja claros.

Tarea «traducir» de `ajustes/ia.toml` (modelo barato). Cada ficha se procesa una vez:
la caché guarda el resultado por su texto, y si el texto cambia se vuelve a hacer.
"""

from __future__ import annotations

import json
import re

from . import ajustes, config, ia
from .util import guardar_json, huella, leer_json

IDIOMAS = {"ca": "catalán", "es": "castellano"}
ESQUEMA = {
    "type": "object",
    "properties": {"fichas": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "traduccion": {"type": "string"},
            "premios": {"type": "array", "items": {
                "type": "object",
                "properties": {"premio_es": {"type": "string"}, "premio_ca": {"type": "string"}, "cita": {"type": "string"}},
                "required": ["premio_es", "premio_ca", "cita"], "additionalProperties": False}},
            "temas_es": {"type": "array", "items": {"type": "string"}},
            "temas_ca": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["id", "traduccion", "premios", "temas_es", "temas_ca"], "additionalProperties": False}}},
    "required": ["fichas"], "additionalProperties": False,
}
SISTEMA = (
    "Trabajas para una cartelera de artes escénicas de Barcelona (app en castellano y catalán). "
    "Para cada ficha recibes su id, su título, el idioma de origen, el idioma de destino y la descripción. Devuelve:\n"
    "1. «traduccion»: la descripción completa traducida al idioma de destino, fiel y natural, sin añadir ni quitar "
    "información, conservando los saltos de línea y los nombres propios, títulos de obras y nombres de compañías tal cual.\n"
    "2. «premios»: los premios, nominaciones y reconocimientos que la descripción dice que ha recibido la obra, la "
    "compañía o sus artistas (por ejemplo «Premi Max al millor espectacle 2024», «finalista dels Premis Butaca»). "
    "Para cada uno: el nombre del premio en castellano y en catalán, y «cita»: el fragmento EXACTO de la descripción "
    "original (copiado letra por letra, sin cambiar nada) donde se menciona. Si no se menciona ningún premio, lista vacía. "
    "No incluyas festivales donde solo se ha representado, ni premios que no estén en el texto.\n"
    "3. «temas_es» y «temas_ca»: de 1 a 3 temas principales de la obra en minúsculas y en pocas palabras (por ejemplo "
    "«familia», «memoria histórica», «amor», «salud mental»), solo si la descripción los deja claros; si no, listas vacías. "
    "Usa solo lo que dice el texto: no inventes nada."
)


def _normal(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def aplicar(ciudad, items: list[dict], informe: dict) -> None:
    """Completa `items` (formato de la app) con traducción, premios citados y temas."""
    tarea = ajustes.tareas_ia().get("traducir")
    ruta = config.carpeta_cache(ciudad.id, "ia") / "traducir.json"
    cache = leer_json(ruta, {}) or {}
    origen_por_id, pendientes = {}, []
    for it in items:
        desc = it.get("descripcion") or {}
        if not desc:
            continue
        origen = it.get("idioma_textos") if it.get("idioma_textos") in desc else next(iter(desc))
        destino = "es" if origen == "ca" else "ca"
        firma = huella(it["id"], desc[origen], destino, tarea.modelo if tarea else "")
        origen_por_id[it["id"]] = (origen, destino, firma)
        if cache.get(it["id"], {}).get("firma") != firma:
            pendientes.append(it)
    inf = {"modelo": tarea.modelo if tarea else None, "fichas_con_texto": len(origen_por_id), "pendientes": len(pendientes), "hechas": 0}
    if tarea and tarea.activa and ia.disponible() and pendientes:
        cli = ia.cliente()
        pendientes = pendientes[: tarea.maximo_por_ejecucion]
        for n in range(0, len(pendientes), tarea.por_peticion):
            lote = pendientes[n:n + tarea.por_peticion]
            entrada = [{"id": it["id"], "titulo": it.get("nombre"), "idioma_origen": IDIOMAS[origen_por_id[it["id"]][0]],
                        "idioma_destino": IDIOMAS[origen_por_id[it["id"]][1]],
                        "descripcion": it["descripcion"][origen_por_id[it["id"]][0]]} for it in lote]
            try:
                r = ia.pedir_json(cli, tarea="traducir", modelo=tarea.modelo, esfuerzo=tarea.esfuerzo, sistema=SISTEMA,
                                  mensaje=json.dumps(entrada, ensure_ascii=False), esquema=ESQUEMA, max_tokens=16000)
            except ia.TopeDeGasto as e:
                inf["aviso"] = str(e)
                break
            except Exception as e:  # noqa: BLE001
                inf.setdefault("errores", []).append(f"{type(e).__name__}: {str(e)[:150]}")
                continue
            por_id = {it["id"]: it for it in lote}
            for x in (r or {}).get("fichas", []):
                it = por_id.get(x["id"])
                if not it or not x.get("traduccion"):
                    continue
                origen, destino, firma = origen_por_id[it["id"]]
                texto = _normal(it["descripcion"][origen])
                # Principio 4: un premio solo vale si su cita está, tal cual, en la descripción.
                premios = [{"es": p["premio_es"], "ca": p["premio_ca"], "cita": p["cita"]}
                           for p in x.get("premios", []) if p.get("cita") and _normal(p["cita"]) in texto]
                cache[it["id"]] = {"firma": firma, "destino": destino, "traduccion": x["traduccion"],
                                   "premios": premios,
                                   "temas": {"es": x.get("temas_es", [])[:3], "ca": x.get("temas_ca", [])[:3]}}
                inf["hechas"] += 1
            if (n // tarea.por_peticion) % 10 == 9:
                guardar_json(ruta, cache)
        guardar_json(ruta, cache)
    for it in items:
        c = cache.get(it["id"])
        if not c or it["id"] not in origen_por_id or c.get("firma") != origen_por_id[it["id"]][2]:
            continue
        it["descripcion"] = {**it["descripcion"], c["destino"]: c["traduccion"]}
        it.setdefault("traducido", c["destino"])
        if c["premios"]:
            it["premios"] = c["premios"]
        if c["temas"].get("es"):
            it["temas"] = c["temas"]
    inf["con_traduccion"] = sum(1 for it in items if it.get("traducido"))
    inf["con_premios"] = sum(1 for it in items if it.get("premios"))
    informe["ia_fichas"] = inf
