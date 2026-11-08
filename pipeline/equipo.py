"""Equipo artístico de un espectáculo, leído de su ficha artística.

Muchas descripciones de la agenda acaban con la ficha artística, una línea por
papel: «Direcció: …», «Intèrprets: …», «Escenografia: …». Aquí se recogen solo
esas líneas etiquetadas (principio 4: nada se deduce ni se inventa). Si la
descripción no trae ficha artística, no hay equipo y la app no muestra el
apartado.
"""

from __future__ import annotations

import re

from .util import normalizar

# Raíces (sin acentos, en minúscula) de los papeles de una ficha artística.
PAPELES = (
    "direcc", "dramaturg", "autor", "text", "guio", "guion", "interpret", "repartiment", "reparto",
    "creacio", "creacion", "idea", "companyia", "compania", "adaptacio", "adaptacion", "traduccio",
    "traduccion", "music", "composicio", "composicion", "espai sonor", "espacio sonoro", "so", "coreograf",
    "moviment", "movimiento", "escenograf", "espai escenic", "espacio escenico", "vestuari", "vestuario",
    "illuminacio", "il luminacio", "iluminacion", "llums", "luces", "video", "visuals", "caracteritzacio",
    "caracterizacion", "titell", "titere", "marionet", "produccio", "produccion", "coproduccio",
    "coproduccion", "mirada externa", "assessor", "asesor", "ajudant", "ayudant", "regidoria", "cant",
    "veu", "voz", "piano", "guitarra", "actor", "actriu", "actriz", "elenc", "elenco", "dramatur",
)
# Etiquetas que llevan dos puntos pero no son del equipo artístico.
NO_SON_PAPELES = ("professor", "tallerista", "edat", "durada", "organitza", "suport", "col laboracio",
                  "agraiment", "observacio", "idioma", "lloc", "genere", "public", "premsa", "distribucio",
                  "atencio", "responsable", "imparteix", "preu", "horari", "data", "inscripcio", "fotografia",
                  "disseny grafic", "a carrec")
# Los papeles principales van primero (brief: dirección, dramaturgia, intérpretes).
ORDEN = (("direcc",), ("dramatur", "autor", "text", "guio", "guion", "creacio", "creacion", "idea", "adaptacio"),
         ("interpret", "repartiment", "reparto", "actor", "actriu", "actriz", "elenc"), ("companyia", "compania"))

_LINEA = re.compile(r"^\s*([A-Za-zÀ-ÿ·.'’ /]{2,45}?)\s*:\s*(\S.*?)\s*$")
_ROLES_EN_MAYUSCULAS = re.compile(r"\s+([A-ZÀ-Ý][A-ZÀ-Ý·.'’]+(?:\s+[A-ZÀ-Ý·.'’]+)*)\s+(?=[A-ZÀ-Ý][a-zà-ÿ])")


def _norm(etiqueta: str) -> str:
    t = re.sub(r"il\W*lumin", "illumin", etiqueta.lower())
    return normalizar(t)


def es_papel(etiqueta: str) -> bool:
    n = _norm(etiqueta)
    if not n or len(n.split()) > 6 or any(x in n for x in NO_SON_PAPELES):
        return False
    return any(re.search(rf"\b{re.escape(p)}", n) for p in PAPELES)


def _prioridad(etiqueta: str) -> int:
    n = _norm(etiqueta)
    if n.startswith("direcc") and any(x in n for x in ("music", "tecnic", "produc")):
        return len(ORDEN)
    for i, raices in enumerate(ORDEN):
        if any(n.startswith(r) for r in raices):
            return i
    return len(ORDEN)


def _partir(etiqueta: str, valor: str) -> list[tuple[str, str]]:
    """«Traducció: Yannick Garcia IL·LUMINACIÓ Jaume Ventura» -> dos papeles."""
    partes = [(etiqueta, valor)]
    m = _ROLES_EN_MAYUSCULAS.search(valor)
    if m and es_papel(m.group(1)):
        partes = [(etiqueta, valor[:m.start()]), (m.group(1), valor[m.end():])]
    return partes


def leer(descripcion: str | None) -> list[list[str]]:
    """[[papel, personas], …] en el orden de importancia; vacío si no hay ficha artística."""
    equipo: list[tuple[int, int, str, str]] = []
    vistos: set[str] = set()
    for linea in (descripcion or "").splitlines():
        m = _LINEA.match(linea)
        if not m or not es_papel(m.group(1)):
            continue
        for etiqueta, valor in _partir(m.group(1), m.group(2)):
            etiqueta = re.sub(r"il\W*lumin", "il·lumin", " ".join(etiqueta.split()).strip(" .").lower())
            valor = " ".join(valor.split()).strip(" .;,")
            if not valor or len(valor) > 300 or etiqueta in vistos:
                continue
            vistos.add(etiqueta)
            equipo.append((_prioridad(etiqueta), len(equipo), etiqueta, valor))
    return [[e, v] for _, _, e, v in sorted(equipo)][:24]


def sin_creditos(descripcion: str | None) -> str:
    """La descripción sin las líneas de la ficha artística (ya se muestran aparte)."""
    lineas = [l for l in (descripcion or "").splitlines()
              if not ((m := _LINEA.match(l)) and es_papel(m.group(1)))]
    return "\n".join(lineas).strip()
