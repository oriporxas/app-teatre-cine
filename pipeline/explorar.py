"""Herramienta de desarrollo: resume la estructura de las agendas descargadas.

No forma parte del proceso diario; sirve para entender los datos y escribir
las notas técnicas de docs/fuentes/open-data-bcn.md.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path


def corto(v, n=240):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


def resumir(ruta: Path) -> None:
    with open(ruta, encoding="utf-8-sig") as f:
        datos = json.load(f)
    print(f"\n===== {ruta.name}: {type(datos).__name__}, {len(datos)} registros")
    if not datos:
        return
    claves = collections.Counter(k for r in datos for k in r)
    print("Campos:", dict(claves))
    print("Ejemplo:")
    for k, v in datos[0].items():
        print(f"  {k}: {corto(v)}")

    def contar(campo, sub="name", top=120):
        c = collections.Counter()
        for r in datos:
            v = r.get(campo) or []
            if isinstance(v, dict):
                v = [v]
            for x in v:
                if isinstance(x, dict):
                    c[str(x.get(sub) or x.get("full_path") or x)[:90]] += 1
                else:
                    c[str(x)[:90]] += 1
        print(f"\n-- {campo}.{sub} ({len(c)} distintos)")
        for nombre, n in c.most_common(top):
            print(f"  {n:5}  {nombre}")

    for campo in ("classifications_data", "secondary_filters_data"):
        if campo in claves:
            contar(campo)
            ej = next((r[campo] for r in datos if r.get(campo)), None)
            print("  ejemplo:", corto(ej, 700))
    for campo in ("values", "tickets_data", "languages_data", "entity_types_data",
                  "from_relationships", "to_relationships", "is_section_of_data",
                  "sections_data", "addresses", "warnings", "image_data"):
        if campo in claves:
            ej = next((r[campo] for r in datos if r.get(campo)), None)
            print(f"\n-- ejemplo {campo}: {corto(ej, 900)}")
    if "values" in claves:
        contar("values", "attribute_name", 40)
    for campo in ("core_type_name", "type_name", "status_name", "event_status_name", "periode_name"):
        if campo in claves:
            print(f"\n-- {campo}:", collections.Counter(str(r.get(campo)) for r in datos).most_common(15))
    # Pistas de magia para la exploración (solo informativo)
    print("\n-- registros con 'màgi' o 'mag ' en el nombre o en categorías:")
    for r in datos:
        texto = (r.get("name") or "") + " " + json.dumps(r.get("classifications_data") or "", ensure_ascii=False)
        t = texto.lower()
        if "màgi" in t or "magia" in t or " mag " in t or "il·lusion" in t:
            print("  ", r.get("register_id"), "|", (r.get("name") or "")[:80])


if __name__ == "__main__":
    for ruta in sys.argv[1:]:
        resumir(Path(ruta))
