"""Descarga las dos agendas de Open Data BCN.

Orden de preferencia para cada agenda:
1. Fichero JSON completo (trae descripción, categorías, sala, idiomas y enlaces).
2. Si el servidor lo rechaza, la API oficial de datos (datastore), que trae
   menos campos: sin descripción, sin categorías y sin nombre de sala.

Las direcciones de los ficheros no se escriben a mano: se piden cada vez al
catálogo (CKAN) a partir del nombre del conjunto de datos, por si cambian.
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
    "agenda-diaria": "activitats",  # «Agenda d'activitats i esdeveniments» (principal)
    "agenda-cultural": "cultural",  # «Agenda cultural»
}

TIEMPO_MAXIMO = 300  # segundos por petición


def _pedir(url: str, destino: Path | None = None) -> bytes | None:
    """Hace una petición GET. Si hay destino, guarda en disco y devuelve None."""
    peticion = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    with urllib.request.urlopen(peticion, timeout=TIEMPO_MAXIMO) as respuesta:
        if destino is None:
            return respuesta.read()
        with open(destino, "wb") as f:
            while True:
                trozo = respuesta.read(1 << 20)
                if not trozo:
                    break
                f.write(trozo)
    return None


def _pedir_con_reintentos(url: str, destino: Path | None = None, intentos: int = 4):
    espera = 2
    for n in range(intentos):
        try:
            return _pedir(url, destino)
        except urllib.error.HTTPError as e:
            # Un 403/404 no se arregla reintentando: el servidor dice que no.
            if e.code in (401, 403, 404):
                raise
            if n == intentos - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if n == intentos - 1:
                raise
        time.sleep(espera)
        espera *= 2


def recursos(conjunto: str) -> list[dict]:
    datos = json.loads(_pedir_con_reintentos(f"{CATALOGO}/package_show?id={conjunto}"))
    return datos["result"]["resources"]


def _datastore_completo(recurso_id: str) -> list[dict]:
    """Lee todas las filas de un recurso por la API oficial, por páginas."""
    filas: list[dict] = []
    pagina = 5000
    desde = 0
    while True:
        q = urllib.parse.urlencode({"resource_id": recurso_id, "limit": pagina, "offset": desde})
        datos = json.loads(_pedir_con_reintentos(f"{CATALOGO}/datastore_search?{q}"))
        bloque = datos["result"]["records"]
        filas.extend(bloque)
        desde += len(bloque)
        if not bloque or desde >= datos["result"].get("total", 0):
            break
    return filas


def descargar(carpeta: Path) -> dict:
    """Descarga las dos agendas en `carpeta`. Devuelve un informe de lo hecho."""
    carpeta.mkdir(parents=True, exist_ok=True)
    informe: dict = {"fecha": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "agendas": {}}
    for conjunto, corto in AGENDAS.items():
        res = recursos(conjunto)
        json_res = next((r for r in res if (r.get("format") or "").upper() == "JSON"), None)
        csv_res = next((r for r in res if (r.get("format") or "").upper() == "CSV"), None)
        entrada = {"conjunto": conjunto}
        destino = carpeta / f"{corto}.json"
        try:
            if json_res is None:
                raise RuntimeError("el catálogo no ofrece JSON")
            _pedir_con_reintentos(json_res["url"], destino)
            with open(destino, encoding="utf-8-sig") as f:
                registros = json.load(f)
            if isinstance(registros, dict):
                # Por si algún día viene envuelto en un objeto.
                registros = next(v for v in registros.values() if isinstance(v, list))
            entrada.update(modo="json_completo", registros=len(registros))
        except Exception as e:  # noqa: BLE001 - cualquier fallo -> plan B
            entrada["fallo_json"] = f"{type(e).__name__}: {e}"
            if csv_res is None or not csv_res.get("datastore_active"):
                raise RuntimeError(f"No se pudo descargar {conjunto} de ninguna forma") from e
            filas = _datastore_completo(csv_res["id"])
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(filas, f, ensure_ascii=False)
            entrada.update(modo="api_reducida", registros=len(filas))
        informe["agendas"][corto] = entrada
    with open(carpeta / "informe_descarga.json", "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=2)
    return informe


if __name__ == "__main__":
    carpeta = Path(os.environ.get("CARPETA_DESCARGAS", "descargas"))
    print(json.dumps(descargar(carpeta), ensure_ascii=False, indent=2))
