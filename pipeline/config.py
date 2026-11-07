"""Ajustes del proceso diario. Todo lo que se puede cambiar está aquí."""

from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"
CACHE = DATOS / "cache"
DESCARGAS = Path(os.environ.get("CARPETA_DESCARGAS", RAIZ / "descargas"))
DOCS = RAIZ / "docs"

# --- Guía del Ayuntamiento (guia.barcelona.cat) -----------------------------
# Su robots.txt pide 10 segundos entre peticiones: lo respetamos siempre.
GUIA_URL = "https://guia.barcelona.cat/ca/detall/{slug}_{id}.html"
GUIA_ESPERA_SEGUNDOS = 10
# Minutos máximos de lectura de páginas por ejecución. En GitHub Actions los
# minutos cuentan para el cupo gratuito (2000 al mes en repositorios privados),
# así que el proceso diario usa poco y el resto se completa en días siguientes.
GUIA_MINUTOS_MAXIMOS = float(os.environ.get("GUIA_MINUTOS_MAXIMOS", "30"))

# --- Equipamientos culturales (para poner nombre a las salas) ----------------
EQUIPAMIENTOS_CONJUNTO = "equipament-cultura-i-lleure"

# --- Clasificación con IA -----------------------------------------------------
# Modelo de Claude. Por defecto el más capaz de uso general; se puede cambiar
# por uno más barato con la variable MODELO_IA (ver docs/clasificacion.md).
MODELO_IA = os.environ.get("MODELO_IA", "claude-opus-5-5")
ESFUERZO_IA = os.environ.get("ESFUERZO_IA", "low")
ESPECTACULOS_POR_PETICION = 10
# Tope de actividades a clasificar con IA en una ejecución (control de coste).
IA_MAXIMO_POR_EJECUCION = int(os.environ.get("IA_MAXIMO_POR_EJECUCION", "2500"))

# Fuentes citadas en cada ficha (principio 4: cada dato con su fuente).
FUENTE_AGENDAS = {
    "activitats": {
        "nombre": "Ajuntament de Barcelona · Open Data BCN · Agenda d'actes i activitats",
        "url": "https://opendata-ajuntament.barcelona.cat/data/ca/dataset/agenda-diaria",
        "licencia": "CC BY 4.0",
    },
    "cultural": {
        "nombre": "Ajuntament de Barcelona · Open Data BCN · Agenda cultural",
        "url": "https://opendata-ajuntament.barcelona.cat/data/ca/dataset/agenda-cultural",
        "licencia": "CC BY 4.0",
    },
}
