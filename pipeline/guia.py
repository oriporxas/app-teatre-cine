"""Lee la ficha pública de cada actividad en guia.barcelona.cat.

Por qué: la API de Open Data BCN no trae descripción, nombre de la sala ni
enlace de compra (el fichero completo que sí los trae está bloqueado para
programas; ver docs/fuentes/open-data-bcn.md). La ficha pública de la guía
del Ayuntamiento sí los trae, y su robots.txt permite leerla pidiendo 10
segundos entre página y página.

Cada ficha se lee una vez y se guarda en data/cache/guia.json. Solo se
vuelve a leer si el Ayuntamiento modifica la actividad.
"""

from __future__ import annotations

import html
import re
import time
import urllib.error
import urllib.request

from . import config
from .util import guardar_json, leer_json, limpiar_id, slug

RUTA_CACHE = config.CACHE / "guia.json"


def _limpiar(fragmento: str) -> str:
    t = re.sub(r"<br\s*/?>|</p>|</li>|</div>", "\n", fragmento, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).replace("\xa0", " ")
    lineas = [re.sub(r"[ \t]+", " ", l).strip() for l in t.split("\n")]
    salida = []
    for l in lineas:
        if l and (not salida or salida[-1] != l):  # la guía repite a veces la misma línea
            salida.append(l)
    return "\n".join(salida)


def analizar(pagina: str) -> dict:
    """Extrae los datos útiles de la página HTML de una actividad."""
    datos: dict = {}
    i = pagina.find('<div id="fitxa">')
    j = pagina.find('<div id="registres-relacionats">')
    bloque = pagina[i:j if j > i else None] if i >= 0 else pagina

    # Descripción: los <div class="cos"> antes de las pestañas.
    fin_desc = bloque.find('<div id="contenidor-pestanes"')
    zona_desc = bloque[:fin_desc] if fin_desc > 0 else bloque
    trozos = re.findall(r'<div class="(?:entradeta|cos)">(.*?)</div>', zona_desc, re.S)
    descripcion = "\n".join(t for t in (_limpiar(x) for x in trozos) if t)
    if descripcion:
        m = re.search(r"^\s*(?:Organitza|Organiza)\s*:\s*(.+)$", descripcion, re.M)
        if m:
            datos["organiza"] = m.group(1).strip()
        datos["descripcion"] = descripcion

    img = re.search(r'<div class="img-guia"><img[^>]+src="([^"]+)"', zona_desc)
    if img:
        datos["imagen"] = img.group(1)

    # Sala: el bloque «info-lloc» enlaza a la ficha del equipamiento con su id.
    m = re.search(r'<div class="info-lloc"><h3><a href="[^"]*?_(\d+)\.html">(.*?)</a>', bloque, re.S)
    if m:
        datos["sala_id_guia"] = m.group(1)
        datos["sala"] = _limpiar(m.group(2))
    else:
        m = re.search(r'<dl class="on"><dt[^>]*>On</dt><dd[^>]*>(.*?)</dd>', bloque, re.S)
        if m:
            datos["sala"] = _limpiar(m.group(1))
            idm = re.search(r'_(\d+)\.html', m.group(1))
            if idm:
                datos["sala_id_guia"] = idm.group(1)

    m = re.search(r"<dt>Se celebra a:\s*</dt><dd[^>]*>(.*?)</dd>", bloque, re.S)
    if m:
        datos["se_celebra_a"] = _limpiar(m.group(1)).rstrip(". ").strip()

    # Enlaces web (venta de entradas, web, inscripciones…)
    enlaces = []
    for etiqueta, url in re.findall(
            r'<dt class="notranslate pr">(.*?)</dt><dd class="notranslate pra"><a href="([^"]+)"', bloque, re.S):
        enlaces.append({"tipo": _limpiar(etiqueta).rstrip(": ").strip(), "url": html.unescape(url)})
    if enlaces:
        datos["enlaces"] = enlaces

    m = re.search(r'<p class="status notranslate">(.*?)</p>', bloque, re.S)
    if m and _limpiar(m.group(1)):
        datos["estado"] = _limpiar(m.group(1))  # p. ej. «Cancel·lat», «Ajornat»
    return datos


def _descargar_pagina(url: str) -> str:
    peticion = urllib.request.Request(url)
    with urllib.request.urlopen(peticion, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def actualizar(actividades: dict[str, dict], prioridad: dict[str, float],
               minutos_maximos: float | None = None) -> dict:
    """Lee las fichas que falten o hayan cambiado, de más a menos prioritaria,
    sin pasar del tiempo máximo. Devuelve un informe."""
    minutos_maximos = config.GUIA_MINUTOS_MAXIMOS if minutos_maximos is None else minutos_maximos
    cache: dict = leer_json(RUTA_CACHE, {}) or {}
    # Olvidar fichas de actividades que ya no están en la agenda.
    for id_ in list(cache):
        if id_ not in actividades:
            del cache[id_]
    pendientes = [i for i, a in actividades.items()
                  if cache.get(i, {}).get("modificado_origen") != a.get("modificado")]
    pendientes.sort(key=lambda i: -prioridad.get(i, 0))
    limite = time.monotonic() + minutos_maximos * 60
    leidas = errores = 0
    ultima = 0.0
    for id_ in pendientes:
        if time.monotonic() + config.GUIA_ESPERA_SEGUNDOS > limite:
            break
        espera = config.GUIA_ESPERA_SEGUNDOS - (time.monotonic() - ultima)
        if espera > 0:
            time.sleep(espera)
        a = actividades[id_]
        url = config.GUIA_URL.format(slug=slug(a["titulo"]), id=id_)
        ultima = time.monotonic()
        try:
            datos = analizar(_descargar_pagina(url))
            datos["url"] = url
            datos["comprobado"] = time.strftime("%Y-%m-%d")
            datos["modificado_origen"] = a.get("modificado")
            cache[id_] = datos
            leidas += 1
        except urllib.error.HTTPError as e:
            errores += 1
            if e.code == 404:  # la actividad ya no está publicada en la guía
                cache[id_] = {"no_disponible": True, "url": url, "comprobado": time.strftime("%Y-%m-%d"),
                              "modificado_origen": a.get("modificado")}
            elif e.code in (403, 429):
                break  # el servidor nos pide parar: paramos hasta mañana
        except Exception:  # noqa: BLE001 - red caída, página rara…
            errores += 1
        if leidas % 50 == 0 and leidas:
            guardar_json(RUTA_CACHE, cache, por_lineas=True)  # guardado parcial
    guardar_json(RUTA_CACHE, cache, por_lineas=True)
    return {
        "fichas_en_cache": len(cache),
        "leidas_hoy": leidas,
        "errores": errores,
        "pendientes": max(0, len(pendientes) - leidas),
    }


def cargar() -> dict:
    return leer_json(RUTA_CACHE, {}) or {}


__all__ = ["analizar", "actualizar", "cargar", "limpiar_id"]
