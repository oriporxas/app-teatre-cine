"""Descarga las dos agendas de Open Data BCN por su API oficial.

Las direcciones no se escriben a mano: se piden cada vez al catálogo (CKAN)
a partir del nombre del conjunto de datos, por si cambian.

Nota (7/11/2026): el fichero JSON completo de cada agenda (con descripción,
categorías y sala) devuelve «403 Forbidden» a los programas, tanto desde la
nube de Claude como desde GitHub. La API (datastore) sí responde, con menos
campos; lo que falta se completa con la ficha pública de la guía (guia.py).
Cada día se comprueba si el fichero completo vuelve a estar disponible y se
anota en el informe, para enterarnos si lo desbloquean.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CATALOGO = "https://opendata-ajuntament.barcelona.cat/data/api/3/action"

# Conjuntos de datos que usamos (nombre en el catálogo -> nombre corto).
AGENDAS = {
    "agenda-diaria": "activitats",  # «Agenda d'actes i activitats» (la principal)
    "agenda-cultural": "cultural",  # «Agenda cultural»
}

TIEMPO_MAXIMO = 300  # segundos por petición


def _pedir(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url), timeout=TIEMPO_MAXIMO) as respuesta:
        return respuesta.read()


def _pedir_con_reintentos(url: str, intentos: int = 4) -> bytes:
    espera = 2
    for n in range(intentos):
        try:
            return _pedir(url)
        except urllib.error.HTTPError as e:
            # Un 403/404 no se arregla reintentando: el servidor dice que no.
            if e.code in (401, 403, 404) or n == intentos - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if n == intentos - 1:
                raise
        time.sleep(espera)
        espera *= 2
    raise RuntimeError("inalcanzable")


def recursos(conjunto: str) -> list[dict]:
    datos = json.loads(_pedir_con_reintentos(f"{CATALOGO}/package_show?id={conjunto}"))
    return datos["result"]["resources"]


def _datastore_completo(recurso_id: str) -> list[dict]:
    """Lee todas las filas de un recurso por la API oficial, por páginas."""
    filas: list[dict] = []
    desde = 0
    while True:
        q = urllib.parse.urlencode({"resource_id": recurso_id, "limit": 5000, "offset": desde})
        datos = json.loads(_pedir_con_reintentos(f"{CATALOGO}/datastore_search?{q}"))
        bloque = datos["result"]["records"]
        filas.extend(bloque)
        desde += len(bloque)
        if not bloque or desde >= datos["result"].get("total", 0):
            break
    return filas


def _json_completo_disponible(url: str) -> str:
    """Pide solo el principio del fichero completo para saber si lo dejan descargar."""
    try:
        peticion = urllib.request.Request(url, headers={"Range": "bytes=0-1023"})
        with urllib.request.urlopen(peticion, timeout=60) as r:
            r.read(1024)
            return f"disponible ({r.status})"
    except urllib.error.HTTPError as e:
        return f"bloqueado ({e.code})"
    except Exception as e:  # noqa: BLE001
        return f"error ({type(e).__name__})"


def descargar(carpeta: Path) -> dict:
    """Descarga las dos agendas en `carpeta`. Devuelve un informe de lo hecho."""
    carpeta.mkdir(parents=True, exist_ok=True)
    informe: dict = {"fecha": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "agendas": {}}
    for conjunto, corto in AGENDAS.items():
        res = recursos(conjunto)
        csv_res = next((r for r in res if (r.get("format") or "").upper() == "CSV"
                        and r.get("datastore_active")), None)
        json_res = next((r for r in res if (r.get("format") or "").upper() == "JSON"), None)
        if csv_res is None:
            raise RuntimeError(f"El catálogo ya no ofrece la API de {conjunto}")
        filas = _datastore_completo(csv_res["id"])
        with open(carpeta / f"{corto}.json", "w", encoding="utf-8") as f:
            json.dump(filas, f, ensure_ascii=False)
        informe["agendas"][corto] = {
            "conjunto": conjunto,
            "registros": len(filas),
            "fichero_json_completo": _json_completo_disponible(json_res["url"]) if json_res else "no existe",
        }
    return informe


if __name__ == "__main__":
    carpeta = Path(os.environ.get("CARPETA_DESCARGAS", "descargas"))
    print(json.dumps(descargar(carpeta), ensure_ascii=False, indent=2))
