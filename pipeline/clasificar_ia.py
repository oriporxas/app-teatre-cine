"""Segunda capa de clasificación: la IA de Claude decide el tipo.

- Los criterios se leen de docs/clasificacion.md (entre las marcas
  «criterios:inicio» y «criterios:fin»). Si se mejoran los criterios, la IA
  los usa al día siguiente y vuelve a clasificar lo afectado.
- Solo se envían actividades nuevas o modificadas: cada resultado se guarda
  en data/cache/clasificacion_ia.json con una «huella» de lo que se le
  enseñó a la IA. Si la huella no cambia, no se vuelve a pagar.
- Si no hay clave (ANTHROPIC_API_KEY), esta capa no hace nada y la app usa
  la clasificación por señales.
"""

from __future__ import annotations

import json
import os
import re
import time

from . import config
from .util import guardar_json, huella, leer_json

RUTA_CACHE = config.CACHE / "clasificacion_ia.json"
TIPOS = ["teatro", "magia", "circo", "danza", "evento", "cine", "otro"]
RELACION_MAGIA = ["principal", "incluye", "tema", "no"]

ESQUEMA = {
    "type": "object",
    "properties": {
        "clasificaciones": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "tipo": {"type": "string", "enum": TIPOS},
                    "subtipo": {"type": "string"},
                    "magia": {"type": "string", "enum": RELACION_MAGIA},
                    "confianza": {"type": "number"},
                    "motivo": {"type": "string"},
                },
                "required": ["id", "tipo", "subtipo", "magia", "confianza", "motivo"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["clasificaciones"],
    "additionalProperties": False,
}


def criterios() -> str:
    texto = (config.DOCS / "clasificacion.md").read_text(encoding="utf-8")
    m = re.search(r"<!--\s*criterios:inicio\s*-->(.*?)<!--\s*criterios:fin\s*-->", texto, re.S)
    if not m:
        raise RuntimeError("docs/clasificacion.md no tiene las marcas de criterios")
    return m.group(1).strip()


def instrucciones() -> str:
    return (
        "Clasificas actividades de la agenda de Barcelona para un directorio de artes escénicas "
        "(teatro, magia, circo y eventos del sector). Recibirás varias actividades en JSON, con textos "
        "en catalán. Para cada una decide el tipo siguiendo estos criterios, que son la única regla "
        "válida:\n\n"
        f"{criterios()}\n\n"
        "Formato de respuesta: un objeto por actividad, con el mismo «id». «subtipo» es una etiqueta "
        "breve en castellano (vacía si no aplica). «confianza» va de 0 a 1 y dice lo segura que es la "
        "decisión: decide siempre, aunque dudes, y baja la confianza. «motivo» es una frase breve en "
        "castellano que explique la decisión citando la pista que la justifica (título, descripción, "
        "sala o artista). Usa solo lo que dicen los datos: no inventes artistas ni premios."
    )


def _entrada(a: dict, senal: dict) -> dict:
    g = a.get("guia") or {}
    desc = (g.get("descripcion") or "").strip()
    if len(desc) > 1800:
        desc = desc[:1800] + "…"
    return {
        "id": a["id"],
        "titulo": a["titulo"],
        "descripcion": desc or None,
        "sala": g.get("sala") or a.get("sala"),
        "tipo_de_lugar": g.get("se_celebra_a"),
        "organiza": g.get("organiza"),
        "horario": (a.get("horario_texto") or "")[:500] or None,
        "fechas": f"{a.get('inicio')} → {a.get('fin')}",
        "pistas_automaticas": senal.get("pistas"),
    }


def disponible() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def clasificar(actividades: dict[str, dict], senales_por_id: dict[str, dict],
               candidatos: list[str]) -> tuple[dict[str, dict], dict]:
    """Clasifica con IA los candidatos que no estén ya en caché.
    Devuelve ({id: resultado}, informe)."""
    cache: dict = leer_json(RUTA_CACHE, {}) or {}
    for id_ in list(cache):
        if id_ not in actividades:
            del cache[id_]
    informe = {"modelo": config.MODELO_IA, "disponible": disponible(), "enviadas": 0,
               "errores": 0, "tokens_entrada": 0, "tokens_salida": 0, "tokens_cache": 0}
    sistema = instrucciones() if disponible() else ""
    firma = huella(sistema, config.MODELO_IA, config.ESFUERZO_IA)
    entradas = {i: _entrada(actividades[i], senales_por_id[i]) for i in candidatos}
    huellas = {i: huella(e, firma) for i, e in entradas.items()}
    pendientes = [i for i in candidatos if cache.get(i, {}).get("huella") != huellas[i]]
    informe["pendientes_antes"] = len(pendientes)

    if disponible() and pendientes:
        import anthropic  # solo hace falta si hay clave

        cliente = anthropic.Anthropic(max_retries=4)
        pendientes = pendientes[: config.IA_MAXIMO_POR_EJECUCION]
        for n in range(0, len(pendientes), config.ESPECTACULOS_POR_PETICION):
            lote = pendientes[n:n + config.ESPECTACULOS_POR_PETICION]
            mensaje = json.dumps([entradas[i] for i in lote], ensure_ascii=False)
            try:
                peticion = dict(
                    model=config.MODELO_IA,
                    max_tokens=16000,
                    system=[{"type": "text", "text": sistema, "cache_control": {"type": "ephemeral"}}],
                    output_config={
                        "effort": config.ESFUERZO_IA,
                        "format": {"type": "json_schema", "schema": ESQUEMA},
                    },
                    messages=[{"role": "user", "content": mensaje}],
                )
                if "haiku" in config.MODELO_IA:
                    respuesta = cliente.messages.create(**peticion)
                else:
                    # Si un filtro de seguridad rechazara la petición, el servidor la
                    # repite con el modelo de reserva recomendado.
                    respuesta = cliente.beta.messages.create(
                        betas=["server-side-fallback-2026-07-01"], fallbacks="default", **peticion)
                uso = respuesta.usage
                informe["tokens_entrada"] += uso.input_tokens or 0
                informe["tokens_salida"] += uso.output_tokens or 0
                informe["tokens_cache"] += getattr(uso, "cache_read_input_tokens", 0) or 0
                if respuesta.stop_reason in ("refusal", "max_tokens"):
                    informe["errores"] += 1
                    continue
                texto = next(b.text for b in respuesta.content if b.type == "text")
                for r in json.loads(texto)["clasificaciones"]:
                    if r["id"] not in huellas:
                        continue
                    r["confianza"] = max(0.0, min(1.0, float(r["confianza"])))
                    r["subtipo"] = r.get("subtipo") or None
                    cache[r["id"]] = {"huella": huellas[r["id"]], "resultado": r,
                                      "modelo": config.MODELO_IA, "fecha": time.strftime("%Y-%m-%d")}
                informe["enviadas"] += len(lote)
            except anthropic.AuthenticationError:
                informe["errores"] += 1
                informe["aviso"] = "La clave de la IA no es válida."
                break
            except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APIStatusError) as e:
                informe["errores"] += 1
                informe.setdefault("detalles", []).append(f"{type(e).__name__}: {str(e)[:200]}")
                if isinstance(e, anthropic.BadRequestError):
                    break  # algo en la petición está mal: no insistir hoy
            except (json.JSONDecodeError, KeyError, StopIteration) as e:
                informe["errores"] += 1
                informe.setdefault("detalles", []).append(f"respuesta ilegible: {e}")
            if (n // config.ESPECTACULOS_POR_PETICION) % 20 == 19:
                guardar_json(RUTA_CACHE, cache, por_lineas=True)
        guardar_json(RUTA_CACHE, cache, por_lineas=True)
    elif cache:
        guardar_json(RUTA_CACHE, cache, por_lineas=True)

    resultados = {i: cache[i]["resultado"] | {"modelo": cache[i]["modelo"]}
                  for i in candidatos if cache.get(i, {}).get("huella") == huellas[i]}
    informe["pendientes_despues"] = len([i for i in candidatos if i not in resultados])
    return resultados, informe
