"""Lectores de horarios: convierten la web de un cine en sesiones.

Cada lector entiende un tipo de web (el programa de venta que usa el cine), no un cine
concreto: si otro cine usa el mismo programa, se lee solo. Hoy:

- «elqueque» (lo usan, entre otros, Mooby y Verdi): la página lleva los datos de todas
  las salas de la cadena (`window.shops`) o los publica en `/api/get-events`.
- «pillalas» (Renoir): una página por día con las sesiones.

Siempre se respeta robots.txt (ver red.py): si una web no permite a los programas la
dirección donde están los horarios, ese cine sale sin horarios y con el enlace a su web.

Cada sesión: {"pelicula": {...datos de la web...}, "fecha", "hora", "version", "sala", "compra"}.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import unicodedata
import urllib.parse

from . import red

VERSIONES = {  # texto de la web → etiqueta común
    "vose": "VOSE", "vos": "VOSE", "subtitulada a castellano": "VOSE", "subtitulada al castellano": "VOSE",
    "vosc": "VOSC", "subtitulada al catala": "VOSC", "subtitulada en catala": "VOSC",
    "catalan": "Català", "catala": "Català", "cat": "Català",
    "castellano": "Castellano", "espanol": "Castellano", "doblada": "Castellano", "esp": "Castellano",
    "vo": "VO", "version original": "VO", "original": "VO",
}


def _sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()


def version(*textos: str) -> str | None:
    t = _sin_acentos(" ".join(x for x in textos if x))
    if re.search(r"\bvosc\b|subtitulad[ao] (al|en) catal", t):
        return "VOSC"
    if re.search(r"\bvose?\b|subtitulad[ao] (a|al|en) castellano|subtitulada", t):
        return "VOSE"
    if re.search(r"\b(cat|catala|catalan)\b", t) and "original" not in t:
        return "Català"
    if re.search(r"original catalan|original catala", t):
        return "Català"
    if re.search(r"original castellano|version original castellano", t):
        return "Castellano"  # película en castellano (versión original)
    if re.search(r"\bvo\b|\bvosi\b|version original", t):
        return "VO"
    if re.search(r"castellano|espanol|espanyol|doblad|\besp\b", t):
        return "Castellano"
    return None


def _fecha_hora(s: str) -> tuple[str, str]:
    """«20261217150000» o «202611172240» → («2026-12-17», «15:00»)."""
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}", f"{s[8:10]}:{s[10:12]}"


def _palabras(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", _sin_acentos(s)) if len(w) > 2} - {"cinema", "cinemes", "cines", "multicines", "cine", "club"}


# --- elqueque (Mooby, Verdi…) -------------------------------------------------------

def _eventos_elqueque(ev: dict, id_cine: str, base: str) -> list[dict]:
    peli = {
        "titulo": re.sub(r"\s*\((VOSE|VOS|VO|CAT|ESP|VOSC|3D)\)\s*$", "", ev.get("locale_title") or ev.get("name") or "", flags=re.I).strip(),
        "titulo_original": ev.get("name") or ev.get("title_name"),
        "imdb": ev.get("imdbid") or None,
        "duracion": int(ev["runtime"]) if str(ev.get("runtime") or "").isdigit() else None,
        "anio": int(ev["year"]) if str(ev.get("year") or "").isdigit() else None,
    }
    if ev.get("directors"):
        peli["direccion"] = [d[1] for d in ev["directors"] if len(d) > 1]
    v = version(ev.get("version"), ev.get("locale_title"), ev.get("wfeatureversion"), ev.get("wlanguagesubtitles"))
    res = []
    for p in ev.get("performances") or []:
        if not p.get("time"):
            continue
        fecha, hora = _fecha_hora(str(p["time"]))
        res.append({"cine": id_cine, "pelicula": peli, "fecha": fecha, "hora": hora, "version": v,
                    "sala": (p.get("hall_name") or "").title() or None, "compra": base})
    return res


def elqueque(cine: dict) -> list[dict] | None:
    """Mooby (datos dentro de la página) o Verdi (/api/get-events). None si la web no es de este tipo."""
    web = cine.get("web") or ""
    if not web:
        return None
    pagina = red.pedir(web)
    if not pagina:
        return None
    texto = pagina.decode("utf-8", "replace")
    p = urllib.parse.urlsplit(web)
    raiz = f"{p.scheme}://{p.netloc}"
    m = re.search(r"window\.shops\s*=\s*", texto)
    if m:  # Mooby: todas las salas en la misma página
        tiendas, _ = json.JSONDecoder().raw_decode(texto[m.end():])
        ruta = "/" + p.path.strip("/") if p.path.strip("/") else None
        elegida = next((t for t in tiendas.values() if ruta and t.get("slug") == ruta), None)
        if not elegida:
            nombre = _palabras(cine["nombre"])
            elegida = max(tiendas.values(), key=lambda t: len(nombre & _palabras(t.get("name") or "")), default=None)
            if not elegida or not (nombre & _palabras(elegida.get("name") or "")):
                return []
        return [s for ev in elegida.get("events") or [] if not ev.get("coming_soon") or ev.get("performances")
                for s in _eventos_elqueque(ev, cine["id"], web)]
    if "/api/get-" in texto or "elqueque" in texto:  # Verdi: datos en la API pública de la web
        teatros = red.pedir(f"{raiz}/api/get-theaters")
        eventos = red.pedir(f"{raiz}/api/get-events")
        if not teatros or not eventos:
            return []
        try:
            teatros = json.loads(teatros)
            eventos = json.loads(eventos)
        except ValueError:
            return []  # no es la API que esperamos
        teatros = teatros.get("result", teatros) if isinstance(teatros, dict) else teatros
        nombre = _palabras(cine["nombre"])
        # Solo el teatro cuyo nombre contiene todas las palabras del cine: si dos cines comparten
        # web (Verdi y Verdi Park) y la web los publica juntos, las sesiones van al que coincide
        # y el otro remite a él (ver __init__.py).
        teatro = next((t for t in teatros if isinstance(t, dict) and nombre and nombre <= _palabras(t.get("name") or "")), None)
        if not teatro:
            return []
        id_teatro = teatro.get("id")
        res = []
        for ev in (eventos.get("result", []) if isinstance(eventos, dict) else []):
            if ev.get("theater_id") == id_teatro:
                res += _eventos_elqueque(ev, cine["id"], f"{raiz}/cartelera")
        return res
    return None


# --- pillalas (Renoir) --------------------------------------------------------------

def _limpio(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _renoir_dia(texto: str, id_cine: str) -> list[dict]:
    res = []
    for bloque in re.split(r'<!-- Visible en lg y xl -->', texto)[1:]:
        bloque = bloque.split("<!-- end visible en lg y xl -->")[0]
        t = re.search(r'<a href="(/pelicula/[^"]+)">(.*?)</a>', bloque, re.S)
        if not t:
            continue
        smalls = [_limpio(x) for x in re.findall(r"<small[^>]*>(.*?)</small>", bloque, re.S)]
        director = next((s[3:].strip() for s in smalls if s.startswith("de ")), None)
        if director and "," in director:  # «Kurosawa, Akira» → «Akira Kurosawa»
            ap, _, nom = director.partition(",")
            director = f"{nom.strip()} {ap.strip()}"
        dur = next((int(m.group(1)) for s in smalls for m in [re.search(r"Duración (\d+)", s)] if m), None)
        ver = next((s for s in smalls if "Versión" in s or "Doblada" in s or "Catal" in s), "")
        peli = {"titulo": _limpio(t.group(2)), "direccion": [director] if director else [], "duracion": dur}
        for pase in re.findall(r'<div class="pase-cartelera.*?</div>\s*</div>|<div class="pase-cartelera[^"]*">.*?(?=<div class="pase-cartelera|$)', bloque, re.S):
            sala = re.search(r"sala\s*(\d+)", pase)
            for href, hora in re.findall(r'<a href="([^"]+)"[^>]*>\s*(\d{1,2}:\d{2})\s*</a>', pase):
                res.append({"cine": id_cine, "pelicula": peli, "hora": hora, "version": version(ver),
                            "sala": f"Sala {int(sala.group(1))}" if sala else None, "compra": href,
                            "especial": (_limpio(m.group(1)) if (m := re.search(r'pase-cartelera-tag">(.*?)</div>', pase, re.S)) else None)})
    # quitar duplicados exactos
    vistos, unicos = set(), []
    for s in res:
        k = (s["pelicula"]["titulo"], s["hora"], s["sala"])
        if k not in vistos:
            vistos.add(k)
            unicos.append(s)
    return unicos


def pillalas(cine: dict, hoy: dt.date, dias: int = 7) -> list[dict] | None:
    web = cine.get("web") or ""
    if "cinesrenoir" not in web and "pillalas" not in web:
        return None
    p = urllib.parse.urlsplit(web)
    raiz = f"{p.scheme or 'https'}://{p.netloc}"
    portada = red.pedir(raiz + "/")
    if not portada:
        return []
    slugs = set(re.findall(r'/cine/([a-z0-9-]+)/', portada.decode("utf-8", "replace")))
    nombre = _palabras(cine["nombre"])
    slug = max(slugs, key=lambda s: len(nombre & _palabras(s.replace("-", " "))), default=None)
    if not slug or not (nombre & _palabras(slug.replace("-", " "))):
        return []
    res = []
    for d in range(dias):
        fecha = (hoy + dt.timedelta(days=d)).isoformat()
        pagina = red.pedir(f"{raiz}/cine/{slug}/cartelera/?fecha={fecha}")
        if not pagina:
            continue
        for s in _renoir_dia(pagina.decode("utf-8", "replace"), cine["id"]):
            res.append(s | {"fecha": fecha})
    return res


LECTORES = (elqueque,)


def leer(cine: dict, hoy: dt.date) -> tuple[list[dict], str]:
    """Sesiones del cine y cómo se han obtenido («elqueque», «pillalas», «sin horarios: …»)."""
    web = cine.get("web")
    if not web:
        return [], "sin web"
    if not red.permitido(web):
        return [], "su web no permite programas (robots.txt)"
    r = pillalas(cine, hoy)
    if r is not None:
        return r, "pillalas"
    r = elqueque(cine)
    if r is not None:
        return r, "elqueque"
    return [], "sin horarios legibles en su web"
