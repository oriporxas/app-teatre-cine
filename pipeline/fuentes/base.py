"""Lo que tiene que cumplir cada fuente de datos.

Cada fuente es una carpeta dentro de pipeline/fuentes/ con un archivo
__init__.py que define:

    NOMBRE = "mi_fuente"            # igual que el nombre de la carpeta
    DESCRIPCION = "…"
    def recoger(ctx: Contexto) -> Resultado: …

`recoger` hace todo lo propio de esa fuente (descargar, leer webs con su
límite de velocidad, entender su formato) y devuelve las actividades en el
FORMATO COMÚN de abajo. El resto del programa (clasificación, salas,
resultados) solo conoce este formato, así que añadir o quitar una fuente no
obliga a tocar nada más: basta con nombrarla en ajustes/ciudades.toml.

FORMATO COMÚN DE UNA ACTIVIDAD (un dict):

    id                 "open_data_bcn:99400781427"  único en el mundo: fuente + id de origen
    fuente, id_origen  "open_data_bcn", "99400781427"
    ciudad             "barcelona" (clave de ajustes/ciudades.toml)
    titulo             texto tal como lo publica la fuente
    idioma_textos      idioma de los textos de origen ("ca", "es", "en"…)
    descripcion        {"ca": "…"}: textos por idioma (las traducciones se añaden después)
    organiza, imagen, estado          (opcionales)
    inicio, fin        fechas locales de la ciudad, "AAAA-MM-DD"
    fechas_aproximadas texto, si la fuente no da fechas exactas
    horario            {"filas", "proximas_funciones" [{fecha, hora} en hora local],
                        "precio" {minimo, maximo, gratis, moneda…}, "duracion_minutos", "idiomas"}
    horario_texto      el horario en texto plano (para la IA)
    lugar              {"clave": "<ciudad>:<algo estable, p. ej. la dirección>" (None si no se sabe),
                        "nombre_en_fuente", "sala_interior", "tipo_de_lugar",
                        "direccion" {calle, numero, codigo_postal, barrio, distrito, municipio},
                        "coordenadas" {lat, lon}, "ids_origen", "categorias",
                        "nombre_casa" (nombre de la sala o equipamiento principal, si se sabe)}
    telefono, enlaces [{tipo, url}], enlace_compra
    modificado_origen  última modificación según la fuente (para releer solo lo cambiado)
    detalle_leido      True si ya se tiene la descripción completa
    prioridad          número: cuanto más alto, antes se revisa (opcional)
    fuentes            [{nombre, url, licencia?, comprobado}]: de dónde sale cada dato (principio 4)
    extra              datos propios de la fuente que no forman parte del formato común
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

from ..ajustes import Ciudad


@dataclass
class Contexto:
    ciudad: Ciudad
    hoy: dt.date
    carpeta_descargas: Path      # archivos temporales del día (no se guardan en el repositorio)
    carpeta_cache: Path          # memoria de esta fuente entre días (sí se guarda)
    descargar: bool = True       # False = usar las descargas que ya hay
    leer_webs: bool = True       # False = no leer páginas nuevas (solo lo que hay en caché)
    minutos_lectura: float | None = None  # tiempo máximo leyendo webs en esta ejecución


@dataclass
class Resultado:
    actividades: list[dict]
    informe: dict = field(default_factory=dict)


def id_global(fuente: str, id_origen: str) -> str:
    return f"{fuente}:{id_origen}"
