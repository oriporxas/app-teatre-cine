"""Agrupa en salas los lugares que entregan las fuentes (formato común).

No sabe de qué ciudad ni de qué fuente vienen: cada fuente ya ha puesto a
cada actividad un «lugar» con una clave estable (p. ej. la dirección). Aquí
solo se juntan las actividades con la misma clave y se elige el nombre.
"""

from __future__ import annotations

import collections


def consolidar(actividades: list[dict]) -> dict[str, dict]:
    grupos: dict[str, list[dict]] = collections.defaultdict(list)
    for a in actividades:
        if a["lugar"].get("clave"):  # las actividades sin lugar conocido no forman sala
            grupos[a["lugar"]["clave"]].append(a)
    salas = {}
    for clave, lista in grupos.items():
        lugares = [a["lugar"] for a in lista]
        nombres = collections.Counter(l["nombre_casa"] for l in lugares if l.get("nombre_casa"))
        nombre = nombres.most_common(1)[0][0] if nombres else None
        interiores = {l["sala_interior"] for l in lugares if l.get("sala_interior")}
        for l in lugares:
            interiores.update(l.get("salas_interiores_conocidas") or [])
        ejemplo = lugares[0]
        salas[clave] = {
            "id": clave,
            "ciudad": lista[0]["ciudad"],
            "nombre": nombre,
            "nombre_verificado": bool(nombre),
            "salas_interiores": sorted(interiores),
            "ids_origen": sorted({x for l in lugares for x in l.get("ids_origen") or []}),
            "categorias": sorted({x for l in lugares for x in l.get("categorias") or []}),
            "direccion": ejemplo.get("direccion"),
            "coordenadas": ejemplo.get("coordenadas"),
            "actividades": len(lista),
        }
    return salas
