"""Une las dos agendas de Open Data BCN en una sola lista de actividades.

Cada actividad tiene el mismo identificador (register_id) en las dos agendas,
así que se unen por ese identificador: una actividad que aparece en ambas es
una sola ficha que recuerda en qué agendas está.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from ...util import limpiar_id


def _titulo(nombre: str) -> str:
    t = (nombre or "").strip()
    if len(t) > 1 and t[0] == t[-1] == '"' and t.count('"') == 2:
        t = t[1:-1]
    return " ".join(t.split())


def _cp(valor) -> str | None:
    v = str(valor or "").strip()
    return v.zfill(5) if v.isdigit() else (v or None)


def _numero(valor) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def desde_fila(fila: dict) -> dict:
    """Convierte una fila de la API (datastore) en nuestra forma de actividad."""
    lat, lon = _numero(fila.get("geo_epgs_4326_lat")), _numero(fila.get("geo_epgs_4326_lon"))
    telefono = None
    if fila.get("values_value"):
        telefono = {
            "tipo": fila.get("values_attribute_name") or None,
            "valor": fila.get("values_value"),
            "nota": fila.get("values_description") or None,
        }
    return {
        "id": limpiar_id(fila.get("register_id")),
        "titulo": _titulo(fila.get("name")),
        "creado": fila.get("created") or None,
        "modificado": fila.get("modified") or None,
        "inicio": (fila.get("start_date") or "")[:10] or None,
        "fin": (fila.get("end_date") or "")[:10] or None,
        "fechas_aproximadas": fila.get("estimated_dates") or None,
        "direccion": {
            "via_id": str(fila.get("addresses_road_id") or "") or None,
            "calle": fila.get("addresses_road_name") or None,
            "numero": str(fila.get("addresses_start_street_number") or "") or None,
            "numero_fin": str(fila.get("addresses_end_street_number") or "") or None,
            "codigo_postal": _cp(fila.get("addresses_zip_code")),
            "barrio": fila.get("addresses_neighborhood_name") or None,
            "distrito": fila.get("addresses_district_name") or None,
            "municipio": (fila.get("addresses_town") or "").title() or None,
        },
        "coordenadas": {"lat": lat, "lon": lon} if lat and lon else None,
        "horario_html": fila.get("timetable") or "",
        "telefono": telefono,
        "agendas": [],
    }


def unir(carpeta: Path, hoy: dt.date | None = None) -> dict[str, dict]:
    """Lee las dos agendas descargadas y devuelve {id: actividad} sin las ya terminadas."""
    hoy = hoy or dt.date.today()
    actividades: dict[str, dict] = {}
    for corto in ("activitats", "cultural"):
        ruta = carpeta / f"{corto}.json"
        with open(ruta, encoding="utf-8-sig") as f:
            filas = json.load(f)
        for fila in filas:
            a = desde_fila(fila)
            if not a["id"]:
                continue
            previa = actividades.get(a["id"])
            if previa is None:
                actividades[a["id"]] = a
                previa = a
            elif (a["modificado"] or "") > (previa["modificado"] or ""):
                # Nos quedamos con la versión más reciente, conservando las agendas.
                a["agendas"] = previa["agendas"]
                actividades[a["id"]] = a
                previa = a
            if corto not in previa["agendas"]:
                previa["agendas"].append(corto)
    hoy_txt = hoy.isoformat()
    return {i: a for i, a in actividades.items()
            if (a["fin"] or a["inicio"] or "9999-12-31") >= hoy_txt}
