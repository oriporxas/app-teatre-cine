"""Lee los ajustes de la carpeta ajustes/ (ciudades y modelos de IA).

Los ajustes viven en archivos de texto (TOML) para poder cambiarlos sin
tocar el código. Para pruebas puntuales, cualquier valor de una tarea de IA
se puede sustituir con una variable de entorno, por ejemplo
IA_CLASIFICAR_MODELO=claude-sonnet-5-5.
"""

from __future__ import annotations

import datetime as dt
import os
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from zoneinfo import ZoneInfo

from . import config

RUTA = config.RAIZ / "ajustes"


@dataclass(frozen=True)
class Ciudad:
    id: str
    nombre: str
    pais: str
    zona_horaria: str
    moneda: str
    idiomas: tuple[str, ...]
    fuentes: tuple[str, ...]
    activa: bool = True
    cine: bool = False       # cartelera de cine (pipeline/cine)
    noticias: bool = False   # noticias de teatro, cine y magia (pipeline/noticias.py)

    def hoy(self) -> dt.date:
        """El día que es ahora en esa ciudad (no en el servidor)."""
        return dt.datetime.now(ZoneInfo(self.zona_horaria)).date()

    def ficha(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "pais": self.pais, "zona_horaria": self.zona_horaria,
                "moneda": self.moneda, "idiomas": list(self.idiomas)}


@dataclass(frozen=True)
class TareaIA:
    nombre: str
    modelo: str
    activa: bool = True
    esfuerzo: str = "low"
    por_peticion: int = 10
    maximo_por_ejecucion: int = 1000
    umbral_confianza: float | None = None
    por_lotes: bool = False  # pedir por lotes (mitad de precio; respuestas en minutos, como mucho 24 h)
    extra: dict = field(default_factory=dict)


def _leer(nombre: str) -> dict:
    with open(RUTA / nombre, "rb") as f:
        return tomllib.load(f)


@lru_cache(maxsize=None)
def ciudades() -> dict[str, Ciudad]:
    res = {}
    for id_, d in _leer("ciudades.toml").items():
        ZoneInfo(d["zona_horaria"])  # falla pronto si la zona horaria está mal escrita
        res[id_] = Ciudad(id=id_, nombre=d["nombre"], pais=d["pais"], zona_horaria=d["zona_horaria"],
                          moneda=d["moneda"], idiomas=tuple(d["idiomas"]), fuentes=tuple(d["fuentes"]),
                          activa=d.get("activa", True), cine=d.get("cine", False), noticias=d.get("noticias", False))
    return res


def _convertir(valor: str, ejemplo):
    if isinstance(ejemplo, bool):
        return valor.strip().lower() in ("1", "true", "si", "sí", "yes")
    if isinstance(ejemplo, int):
        return int(valor)
    if isinstance(ejemplo, float):
        return float(valor)
    return valor


@lru_cache(maxsize=None)
def tareas_ia() -> dict[str, TareaIA]:
    res = {}
    conocidos = {"modelo", "activa", "esfuerzo", "por_peticion", "maximo_por_ejecucion", "umbral_confianza", "por_lotes"}
    for nombre, d in _leer("ia.toml").items():
        if "modelo" not in d:
            continue  # secciones que no son tareas (p. ej. [presupuesto])
        d = dict(d)
        for clave in list(conocidos | set(d)):
            var = f"IA_{nombre}_{clave}".upper()
            if var in os.environ:
                d[clave] = _convertir(os.environ[var], d.get(clave, ""))
        res[nombre] = TareaIA(nombre=nombre, **{k: v for k, v in d.items() if k in conocidos},
                              extra={k: v for k, v in d.items() if k not in conocidos})
    return res
