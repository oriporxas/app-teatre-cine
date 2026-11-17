"""Verificador: ninguna ficha sale en la app sin pasar estas comprobaciones.

Principio 4 (precisión) hecho programa. Antes de escribir el archivo de la app, cada dato
sensible se contrasta con el texto de la fuente o con reglas de sentido común. Lo que no pasa:
- **no se enseña** (mejor un recuadro de menos que un dato falso), y
- **queda anotado** en `data/ciudades/<ciudad>/verificacion.json` (informe diario de anomalías),
  con el motivo, para que cada error encontrado se convierta en una regla o una prueba nueva.

Nada depende de que alguien lo revise (principio 1): el informe sirve para mejorar el programa,
no para corregir datos a mano.

Comprobaciones (cada una nació de un error real o de un riesgo claro):
- Precio: cada importe tiene que estar escrito tal cual en el texto de precios de la fuente
  (error del 17/11/2026: «24.95 €» salía como «95 €»). Mínimo ≤ máximo, y menos de 1.000 €.
- Funciones: fechas reales, dentro del periodo que da la fuente; horas válidas. Una hora entre
  las 2:00 y las 7:59 es casi seguro un error de lectura: se quita la hora (sale «por confirmar»).
- Lugar: el nombre de la sala no puede ser el de la ciudad («Barcelona» no es una sala); las
  coordenadas tienen que caer dentro de la ciudad (si no, no sale el punto en el mapa).
- Equipo artístico: cada nombre tiene que estar en la descripción de la fuente.
- Premios citados: la cita tiene que estar en la descripción.
- Duración (5 a 600 minutos) y edades (0 a 99) razonables.
- Enlaces: solo direcciones web completas (http/https).
- Fichas repetidas: mismo título en la misma sala → se avisa (una sola ficha por obra).
- Cine: sesiones con fecha dentro de la ventana, hora válida y cine conocido.
"""

from __future__ import annotations

import collections
import datetime as dt
import re

from . import config
from .horario import aparece
from .util import guardar_json, normalizar

HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _texto_precios(f: dict) -> str:
    return " ".join(" ".join(x for x in (fila.get("precios"), fila.get("observaciones")) if x) for fila in f.get("horario") or [])


def _fecha(x) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(x)[:10])
    except ValueError:
        return None


class Registro:
    def __init__(self):
        self.anomalias: list[dict] = []
        self.cuenta: collections.Counter = collections.Counter()

    def anotar(self, regla: str, item: dict | None, detalle: str, accion: str):
        self.cuenta[regla] += 1
        if len(self.anomalias) < 400:
            self.anomalias.append({"regla": regla, "id": (item or {}).get("id"), "titulo": (item or {}).get("nombre"),
                                   "detalle": detalle[:200], "accion": accion})


def caja_ciudad(mapa: dict | None) -> tuple[float, float, float, float] | None:
    """(lat mín, lat máx, lon mín, lon máx) de la ciudad, a partir de su mapa de distritos."""
    pts = [p for a in (mapa or {}).get("areas", []) for anillo in a.get("anillos", []) for p in anillo]
    if not pts:
        return None
    lons, lats = [p[0] for p in pts], [p[1] for p in pts]
    m = 0.01  # unos 1.000 m de margen
    return min(lats) - m, max(lats) + m, min(lons) - m, max(lons) + m


def escena(ciudad, items: list[dict], fichas: list[dict], mapa: dict | None, hoy: dt.date) -> dict:
    """Comprueba y corrige `items` (formato de la app). Devuelve el resumen del día."""
    reg = Registro()
    por_id = {f["id"]: f for f in fichas}
    caja = caja_ciudad(mapa)
    nombre_ciudad = normalizar(ciudad.nombre if hasattr(ciudad, "nombre") else str(ciudad))
    vistos: dict[tuple[str, str], str] = {}
    for it in items:
        f = por_id.get(it["id"]) or {}
        # --- Precio ---
        if it.get("precio_min") is not None:
            texto = _texto_precios(f)
            malos = [v for v in {it.get("precio_min"), it.get("precio_max")} if v is not None and not aparece(v, texto)]
            if malos or (it.get("precio_max") is not None and it["precio_max"] < it["precio_min"]) or it["precio_min"] >= 1000:
                reg.anotar("precio", it, f"{it.get('precio_min')}–{it.get('precio_max')} no está en «{texto[:120]}»", "precio oculto")
                it.pop("precio_min", None)
                it.pop("precio_max", None)
        # --- Funciones ---
        ini, fin = _fecha(f.get("inicio")), _fecha(f.get("fin")) or _fecha(f.get("inicio"))
        buenas = []
        for fn in it.get("funciones") or []:
            d = _fecha(fn[0])
            if not d:
                reg.anotar("fecha", it, f"fecha ilegible {fn[0]!r}", "función quitada")
                continue
            if ini and fin and not (ini <= d <= fin):
                reg.anotar("fecha", it, f"{fn[0]} fuera del periodo {ini}–{fin}", "función quitada")
                continue
            if len(fn) > 1 and fn[1]:
                if not HORA.match(fn[1]):
                    reg.anotar("hora", it, f"hora ilegible {fn[1]!r}", "hora quitada")
                    fn = [fn[0]]
                elif "02:00" <= fn[1] < "08:00":
                    reg.anotar("hora", it, f"hora improbable {fn[1]} el {fn[0]}", "hora quitada")
                    fn = [fn[0]]
            buenas.append(fn)
        it["funciones"] = buenas
        # --- Lugar ---
        if it.get("sala") and normalizar(it["sala"]) == nombre_ciudad:
            reg.anotar("sala", it, f"la sala se llama como la ciudad ({it['sala']})", "nombre de sala oculto")
            it.pop("sala", None)
        if caja and it.get("lat") is not None and it.get("lon") is not None:
            if not (caja[0] <= it["lat"] <= caja[1] and caja[2] <= it["lon"] <= caja[3]):
                reg.anotar("ubicacion", it, f"({it['lat']}, {it['lon']}) fuera de la ciudad", "punto del mapa oculto")
                it.pop("lat", None)
                it.pop("lon", None)
        # --- Equipo artístico y premios: tienen que estar en la descripción de la fuente ---
        # (la ficha artística puede venir también en el título: «…, a càrrec de Cia. X»)
        desc = normalizar(" ".join([f.get("titulo") or "", *(f.get("descripcion") or {}).values()]))
        if it.get("equipo"):
            bien = []
            for papel, personas in it["equipo"]:
                if normalizar(personas) and normalizar(personas) in desc:
                    bien.append([papel, personas])
                else:
                    reg.anotar("equipo", it, f"«{papel}: {personas}» no está en la descripción", "línea del equipo oculta")
            it["equipo"] = bien
            if not bien:
                it.pop("equipo")
        if it.get("premios"):
            bien = [p for p in it["premios"] if normalizar(p.get("cita", "")) in desc]
            if len(bien) < len(it["premios"]):
                reg.anotar("premio", it, f"{len(it['premios']) - len(bien)} citas no encontradas", "premio oculto")
            if bien:
                it["premios"] = bien
            else:
                it.pop("premios")
        # --- Duración, edades, enlaces ---
        if it.get("duracion") is not None and not (5 <= it["duracion"] <= 600):
            reg.anotar("duracion", it, f"{it['duracion']} minutos", "duración oculta")
            it.pop("duracion")
        for campo in ("edad_min", "edad_max"):
            if it.get(campo) is not None and not (0 <= it[campo] <= 99):
                reg.anotar("edad", it, f"{campo}={it[campo]}", "edad oculta")
                it.pop(campo)
        for campo in ("compra", "compra_sala", "fuente_url", "imagen"):
            if it.get(campo) and not re.match(r"https?://[^\s/]+\.[^\s]+$", it[campo]):
                reg.anotar("enlace", it, f"{campo}: {it[campo][:80]}", "enlace oculto")
                it.pop(campo)
                if campo == "compra":
                    it.pop("compra_tipo", None)
        # --- Una sola ficha por obra ---
        clave = (normalizar(it.get("nombre") or ""), it.get("sala_id") or "")
        if clave[0] and clave[1]:
            if clave in vistos and vistos[clave] != it["id"]:
                reg.anotar("repetida", it, f"mismo título y sala que {vistos[clave]}", "aviso")
            vistos.setdefault(clave, it["id"])
    # Sin ninguna función futura, la ficha no sale (no se puede ir a verla).
    antes = len(items)
    items[:] = [it for it in items if any(fn[0] >= hoy.isoformat() for fn in it["funciones"])]
    if len(items) < antes:
        reg.cuenta["sin_funciones"] += antes - len(items)
    return _guardar(ciudad, "escena", reg, len(items))


def cine(ciudad, datos: dict, hoy: dt.date, dias: int) -> dict:
    """Comprueba las sesiones de cine (formato de la app) y quita las imposibles."""
    reg = Registro()
    cines = {c["id"] for c in datos.get("cines", [])}
    nombre_ciudad = normalizar(ciudad.nombre if hasattr(ciudad, "nombre") else str(ciudad))
    for c in datos.get("cines", []):
        if normalizar(c.get("nombre") or "") == nombre_ciudad:  # «Barcelona» no es un cine
            reg.anotar("sala", {"id": c["id"], "nombre": c.get("nombre")}, "el lugar se llama como la ciudad", "se usa la dirección")
            if c.get("direccion"):
                c["nombre"] = c["direccion"]
            else:
                c.pop("nombre", None)
    fin = (hoy + dt.timedelta(days=dias)).isoformat()
    for p in datos.get("peliculas", []):
        if not (p.get("titulo") or "").strip():
            reg.anotar("pelicula", {"id": p.get("id")}, "película sin título", "película quitada")
            p["sesiones"] = []
        bien = []
        for s in p.get("sesiones", []):
            if s[0] not in cines:
                reg.anotar("cine", {"id": p["id"], "nombre": p.get("titulo")}, f"cine desconocido {s[0]}", "sesión quitada")
            elif not (_fecha(s[1]) and hoy.isoformat() <= s[1] <= fin):
                reg.anotar("fecha", {"id": p["id"], "nombre": p.get("titulo")}, f"sesión el {s[1]}", "sesión quitada")
            elif s[2] and not HORA.match(s[2]):
                reg.anotar("hora", {"id": p["id"], "nombre": p.get("titulo")}, f"hora {s[2]!r}", "sesión quitada")
            else:
                bien.append(s)
        p["sesiones"] = bien
    datos["peliculas"] = [p for p in datos.get("peliculas", []) if p.get("sesiones")]
    return _guardar(ciudad, "cine", reg, len(datos["peliculas"]))


def _guardar(ciudad, parte: str, reg: Registro, publicadas: int) -> dict:
    cid = ciudad.id if hasattr(ciudad, "id") else str(ciudad)
    ruta = config.carpeta_ciudad(cid) / "verificacion.json"
    from .util import leer_json
    todo = leer_json(ruta, {}) or {}
    todo[parte] = {"fecha": dt.date.today().isoformat(), "publicadas": publicadas,
                   "corregidas_por_regla": dict(reg.cuenta), "anomalias": reg.anomalias}
    guardar_json(ruta, todo)
    return {"publicadas": publicadas, "corregidas_por_regla": dict(reg.cuenta)}
