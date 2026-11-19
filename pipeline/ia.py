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
import threading
import time
from pathlib import Path

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
DESCUENTO_LOTES = 0.5  # las peticiones por lotes (Message Batches) cuestan la mitad
_CERROJO = threading.Lock()  # el cine y las noticias van en paralelo con la escena


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

    def sumar(self, tarea: str, modelo: str, uso, busquedas: int = 0, factor: float = 1.0) -> float:
        entrada, salida = PRECIOS.get(modelo, PRECIOS["claude-opus-5-5"])
        leido = getattr(uso, "cache_read_input_tokens", 0) or 0
        escrito = getattr(uso, "cache_creation_input_tokens", 0) or 0
        coste = ((uso.input_tokens or 0) * entrada + leido * entrada * 0.1 + escrito * entrada * 1.25
                 + (uso.output_tokens or 0) * salida) / 1e6 * factor + busquedas * PRECIO_BUSQUEDA_WEB
        with _CERROJO:
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
    peticion = _peticion(modelo, esfuerzo, sistema, mensaje, esquema, max_tokens)
    if "haiku" in modelo:  # Haiku no admite modelo de reserva en el servidor
        respuesta = cli.messages.create(**peticion)
    else:
        respuesta = cli.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **peticion)
    GASTO.sumar(tarea, modelo, respuesta.usage)
    if respuesta.stop_reason in ("refusal", "max_tokens"):
        return None
    texto = next((b.text for b in respuesta.content if b.type == "text"), "")
    return json.loads(texto) if texto else None


def _peticion(modelo: str, esfuerzo: str, sistema: str, mensaje: str, esquema: dict, max_tokens: int) -> dict:
    return dict(
        model=modelo, max_tokens=max_tokens,
        system=[{"type": "text", "text": sistema, "cache_control": {"type": "ephemeral"}}],
        output_config={"effort": esfuerzo, "format": {"type": "json_schema", "schema": esquema}},
        messages=[{"role": "user", "content": mensaje}],
    )


def espera_lotes() -> float:
    """Segundos que una ejecución espera las respuestas de un lote ([lotes] de ia.toml)."""
    if "IA_ESPERA_LOTES_MIN" in os.environ:
        return 60 * float(os.environ["IA_ESPERA_LOTES_MIN"])
    from .ajustes import _leer
    return 60 * float((_leer("ia.toml").get("lotes") or {}).get("espera_maxima_minutos", 20))


class Lotes:
    """Peticiones a la IA por lotes (Message Batches de Anthropic): cuestan **la mitad**, pero la IA
    las contesta cuando tiene hueco: casi siempre en unos minutos y, como mucho, en 24 horas.

    Uso (una tarea, p. ej. «noticias»):
        lotes = Lotes("noticias", carpeta)      # recoge lo que dejaron pendiente ejecuciones anteriores
        en_curso = lotes.datos_en_curso()       # lo que la IA aún está contestando: no se vuelve a pedir
        lotes.enviar(cli, modelo=..., esfuerzo=..., sistema=..., esquema=..., peticiones={id: (mensaje, datos)})
        lotes.esperar()                         # como mucho [lotes] espera_maxima_minutos
        for respuesta, datos in lotes.recogidas: ...
        lotes.guardar()

    - `datos` es lo que quien llama necesita para usar cada respuesta (qué obras o noticias son, con
      qué versión del texto se pidió) y se guarda con el lote, por si la respuesta llega otro día.
    - Si la IA rechaza una petición (filtro de seguridad) o falla el servidor, esa petición se repite al
      momento por la vía normal, que tiene modelo de reserva.
    - Si al acabar la espera la IA aún no ha contestado algo, se cancela esa parte del lote (lo que no
      se ha procesado no se cobra) y se pregunta al momento por la vía normal (Uri, 19/11/2026: «lo nuevo
      tiene que detectarse rápido»). Así nada queda para horas después y nada se paga dos veces.
    - Si la ejecución se corta a medias, el lote queda en `carpeta/lotes_<tarea>.json` y lo recoge la
      siguiente.
    """

    def __init__(self, tarea: str, carpeta: Path, cli=None) -> None:
        self.tarea = tarea
        self.ruta = Path(carpeta) / f"lotes_{tarea}.json"
        self.cli = cli
        self.recogidas: list[tuple[dict | None, object]] = []
        self._rescatando = False
        self.informe = {"enviadas": 0, "recogidas": 0, "repetidas_normal": 0, "en_curso": 0, "canceladas": 0, "errores": 0,
                        "tokens_entrada": 0, "tokens_salida": 0, "tokens_cache": 0, "tokens_cache_escritura": 0}
        self.pendientes: list[dict] = (leer_json(self.ruta, {}) or {}).get("lotes", [])
        if self.pendientes and disponible():
            self._revisar()

    # -- lo que la IA aún está contestando
    def datos_en_curso(self) -> list:
        return [p["datos"] for lote in self.pendientes for p in lote["peticiones"].values()]

    def _cliente(self):
        if self.cli is None:
            self.cli = cliente()
        return self.cli

    def enviar(self, cli, *, modelo: str, esfuerzo: str, sistema: str, esquema: dict,
               peticiones: dict[str, tuple[str, object]], max_tokens: int = 16000) -> None:
        """Envía un lote nuevo. Lanza TopeDeGasto si ya no queda presupuesto en esta ejecución."""
        if not peticiones:
            return
        self.cli = cli or self.cli
        GASTO.comprobar()
        from .util import huella
        cuerpo, guardadas = [], {}
        for clave_, (mensaje, datos) in peticiones.items():
            cid = huella(self.tarea, modelo, esfuerzo, sistema, mensaje)  # 16 cifras hexadecimales
            if cid in guardadas:
                continue
            guardadas[cid] = {"mensaje": mensaje, "datos": datos}
            cuerpo.append({"custom_id": cid, "params": _peticion(modelo, esfuerzo, sistema, mensaje, esquema, max_tokens)})
        lote = self._cliente().messages.batches.create(requests=cuerpo)
        self.pendientes.append({"id": lote.id, "creado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                "modelo": modelo, "esfuerzo": esfuerzo, "sistema": sistema, "esquema": esquema,
                                "max_tokens": max_tokens, "peticiones": guardadas})
        self.informe["enviadas"] += len(cuerpo)
        self.guardar()  # si la ejecución se corta, el lote no se pierde

    def esperar(self, segundos: float | None = None, rescatar: bool = True) -> None:
        """Espera a que terminen los lotes pendientes, como mucho `segundos`. Si después queda algo y
        `rescatar`, se cancela y se pregunta por la vía normal (sin esperar a otra ejecución)."""
        fin = time.monotonic() + (espera_lotes() if segundos is None else segundos)
        pausa = 10.0
        while self.pendientes and time.monotonic() < fin:
            time.sleep(min(pausa, max(0.0, fin - time.monotonic())))
            pausa = min(pausa * 1.5, 60.0)
            self._revisar()
        if self.pendientes and rescatar and disponible():
            self._rescatar()
        self.informe["en_curso"] = sum(len(l["peticiones"]) for l in self.pendientes)
        self.guardar()

    def _rescatar(self) -> None:
        """Cancela lo que la IA aún no ha contestado y lo pide por la vía normal."""
        cli = self._cliente()
        for lote in self.pendientes:
            try:
                cli.messages.batches.cancel(lote["id"])
            except Exception as e:  # noqa: BLE001 - si ya había terminado, se recoge igual
                self.informe.setdefault("detalles", []).append(f"cancelar: {type(e).__name__}: {str(e)[:100]}")
        self._rescatando = True
        fin = time.monotonic() + 180  # cancelar tarda poco: lo ya contestado se recoge y se paga a mitad
        while self.pendientes and time.monotonic() < fin:
            time.sleep(5)
            self._revisar()
        self._rescatando = False

    def guardar(self) -> None:
        guardar_json(self.ruta, {"lotes": self.pendientes})

    # -- recoger
    def _revisar(self) -> None:
        cli = self._cliente()
        quedan = []
        for lote in self.pendientes:
            try:
                estado = cli.messages.batches.retrieve(lote["id"])
            except Exception as e:  # noqa: BLE001 - sin respuesta: se mira en la próxima vuelta
                self.informe.setdefault("detalles", []).append(f"{type(e).__name__}: {str(e)[:120]}")
                quedan.append(lote)
                continue
            if estado.processing_status != "ended":
                creado = dt.datetime.fromisoformat(lote["creado"])
                if dt.datetime.now(dt.timezone.utc) - creado < dt.timedelta(hours=30):
                    quedan.append(lote)
                continue  # más de 30 horas: caducado; sus peticiones se vuelven a pedir
            self._recoger(cli, lote)
        self.pendientes = quedan

    def _recoger(self, cli, lote: dict) -> None:
        for r in cli.messages.batches.results(lote["id"]):
            p = lote["peticiones"].get(r.custom_id)
            if p is None:
                continue
            tipo = r.result.type
            if tipo == "succeeded":
                msg = r.result.message
                GASTO.sumar(self.tarea, lote["modelo"], msg.usage, factor=DESCUENTO_LOTES)
                u = msg.usage
                self.informe["tokens_entrada"] += u.input_tokens or 0
                self.informe["tokens_salida"] += u.output_tokens or 0
                self.informe["tokens_cache"] += getattr(u, "cache_read_input_tokens", 0) or 0
                self.informe["tokens_cache_escritura"] += getattr(u, "cache_creation_input_tokens", 0) or 0
                if msg.stop_reason == "refusal":
                    self._normal(cli, lote, p)
                    continue
                texto = next((b.text for b in msg.content if b.type == "text"), "")
                try:
                    respuesta = json.loads(texto) if texto and msg.stop_reason != "max_tokens" else None
                except json.JSONDecodeError:
                    respuesta = None
                if respuesta is None:
                    self.informe["errores"] += 1
                self.recogidas.append((respuesta, p["datos"]))
                self.informe["recogidas"] += 1
            elif tipo == "errored" and getattr(r.result.error, "type", "") != "invalid_request":
                self._normal(cli, lote, p)  # fallo del servidor: se repite ahora
            elif tipo in ("canceled", "expired") and self._rescatando:
                self.informe["canceladas"] += 1
                self._normal(cli, lote, p)  # no llegó a tiempo: se pregunta ahora por la vía normal
            else:  # petición mal formada, cancelada o caducada: se vuelve a pedir otro día
                self.informe["errores"] += 1
                self.informe.setdefault("detalles", []).append(f"{r.custom_id}: {tipo}")

    def _normal(self, cli, lote: dict, p: dict) -> None:
        """La misma petición por la vía normal (precio completo, con modelo de reserva)."""
        try:
            respuesta = pedir_json(cli, tarea=self.tarea, modelo=lote["modelo"], esfuerzo=lote["esfuerzo"],
                                   sistema=lote["sistema"], mensaje=p["mensaje"], esquema=lote["esquema"],
                                   max_tokens=lote["max_tokens"])
        except TopeDeGasto:
            return  # se pedirá otro día
        except Exception as e:  # noqa: BLE001
            self.informe["errores"] += 1
            self.informe.setdefault("detalles", []).append(f"{type(e).__name__}: {str(e)[:120]}")
            return
        self.informe["repetidas_normal"] += 1
        self.recogidas.append((respuesta, p["datos"]))
