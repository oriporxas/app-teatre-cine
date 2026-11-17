"""Piezas comunes de la IA: cliente, coste de cada petición y freno de gasto.

- Todas las tareas de IA (clasificar, traducir, leer horarios de cine, noticias…)
  pasan por aquí, así el gasto se suma en un solo sitio.
- **Freno de gasto:** si en una ejecución se llega al tope de `ajustes/ia.toml`
  ([presupuesto] maximo_usd_por_ejecucion), las tareas dejan de llamar a la IA y lo
  apuntan en el informe. Lo que no se haya hecho se hace otro día (la caché guarda lo
  ya hecho: nada se paga dos veces).
- El gasto de cada día se guarda en `data/gasto_ia.json` para poder revisarlo.
"""

from __future__ import annotations

import datetime as dt
import json
import os

from . import config
from .util import guardar_json, leer_json

# Precios por millón de tokens (entrada, salida), noviembre de 2026. Leer de la caché cuesta
# el 10 % de la entrada y escribir en ella, el 125 %. La búsqueda web, 10 $ cada 1000.
PRECIOS = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-fable-5-2": (8.00, 40.00),
}
PRECIO_BUSQUEDA_WEB = 10.0 / 1000

RUTA_GASTO = config.RAIZ / "data" / "gasto_ia.json"


class TopeDeGasto(Exception):
    """Se ha llegado al tope de gasto de esta ejecución."""


def clave() -> str | None:
    # En GitHub es el secreto ANTHROPIC_API_KEY; en las sesiones de Claude en la nube, que no
    # pasan variables ANTHROPIC_*, se guarda como CLAVE_IA_CARTELERA.
    return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAVE_IA_CARTELERA")


def disponible() -> bool:
    return bool(clave())


def _tope() -> float:
    if "IA_TOPE_USD" in os.environ:
        return float(os.environ["IA_TOPE_USD"])
    from .ajustes import _leer
    return float((_leer("ia.toml").get("presupuesto") or {}).get("maximo_usd_por_ejecucion", 2.0))


class _Gasto:
    def __init__(self) -> None:
        self.usd = 0.0
        self.por_tarea: dict[str, float] = {}
        self.tope: float | None = None

    def limite(self) -> float:
        if self.tope is None:
            self.tope = _tope()
        return self.tope

    def comprobar(self) -> None:
        if self.usd >= self.limite():
            raise TopeDeGasto(f"tope de gasto de la ejecución alcanzado ({self.usd:.2f} $ de {self.limite():.2f} $)")

    def sumar(self, tarea: str, modelo: str, uso, busquedas: int = 0) -> float:
        entrada, salida = PRECIOS.get(modelo, PRECIOS["claude-opus-5-5"])
        leido = getattr(uso, "cache_read_input_tokens", 0) or 0
        escrito = getattr(uso, "cache_creation_input_tokens", 0) or 0
        coste = ((uso.input_tokens or 0) * entrada + leido * entrada * 0.1 + escrito * entrada * 1.25
                 + (uso.output_tokens or 0) * salida) / 1e6 + busquedas * PRECIO_BUSQUEDA_WEB
        self.usd += coste
        self.por_tarea[tarea] = self.por_tarea.get(tarea, 0.0) + coste
        return coste

    def guardar(self) -> None:
        """Suma el gasto de esta ejecución al registro diario (data/gasto_ia.json)."""
        if not self.usd:
            return
        registro = leer_json(RUTA_GASTO, {}) or {}
        dia = registro.setdefault(dt.date.today().isoformat(), {"usd": 0.0, "por_tarea": {}})
        dia["usd"] = round(dia["usd"] + self.usd, 4)
        for t, v in self.por_tarea.items():
            dia["por_tarea"][t] = round(dia["por_tarea"].get(t, 0.0) + v, 4)
        guardar_json(RUTA_GASTO, registro)
        self.usd, self.por_tarea = 0.0, {}


GASTO = _Gasto()


def cliente():
    import anthropic
    # La dirección se fija: en algunos entornos ANTHROPIC_BASE_URL apunta a otro servicio.
    return anthropic.Anthropic(api_key=clave(), base_url="https://api.anthropic.com", max_retries=4)


def pedir_json(cli, *, tarea: str, modelo: str, esfuerzo: str, sistema: str, mensaje: str, esquema: dict,
               max_tokens: int = 16000) -> dict | None:
    """Una petición con respuesta en JSON validado por el esquema. Devuelve None si la IA no responde
    (rechazo o respuesta cortada). Lanza TopeDeGasto si ya no queda presupuesto."""
    GASTO.comprobar()
    peticion = dict(
        model=modelo, max_tokens=max_tokens,
        system=[{"type": "text", "text": sistema, "cache_control": {"type": "ephemeral"}}],
        output_config={"effort": esfuerzo, "format": {"type": "json_schema", "schema": esquema}},
        messages=[{"role": "user", "content": mensaje}],
    )
    if "haiku" in modelo:  # Haiku no admite modelo de reserva en el servidor
        respuesta = cli.messages.create(**peticion)
    else:
        respuesta = cli.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **peticion)
    GASTO.sumar(tarea, modelo, respuesta.usage)
    if respuesta.stop_reason in ("refusal", "max_tokens"):
        return None
    texto = next((b.text for b in respuesta.content if b.type == "text"), "")
    return json.loads(texto) if texto else None
