"""A quién va dirigida una actividad y, en la formación, de qué nivel es.

Se saca del título y de la descripción (catalán y castellano), con
vocabulario general: «(de 6 a 12 anys)», «a partir de 12 anys», «adults»,
«Adreçat a nens i nenes de 8 a 12 anys», «per a tota la família», «taller
d'iniciació», «avançat»… Sirve para todas las actividades, no solo las de
magia.

Solo cuentan las edades que hablan del público («adreçat a…», «edat
recomanada…», «per a infants de…» o entre paréntesis en el título). Unas
edades sueltas en la descripción pueden ser de otra cosa: en un festival de
jóvenes magos de 14 a 25 años, esa es la edad de los concursantes, no la
del público.
"""

from __future__ import annotations

import re

from .util import normalizar

PUBLICOS = ("infantil", "familiar", "juvenil", "juvenil y adultos", "adultos", "todos los públicos")
NIVELES = ("iniciación", "intermedio", "avanzado")

_ANYS = r"(?:anys|any|anos|ano)"  # ya sin acentos ni «ñ»
_RANGO_TITULO = re.compile(rf"(?:de\s+)?(\d{{1,2}})\s*(?:a|i|fins a|hasta|\s)\s*(\d{{1,2}})\s*{_ANYS}\b")  # «6-12» queda «6 12»
_MINIMO = re.compile(rf"(?:a\s+partir\s+de|desde|des\s+de|majors\s+de|mayores\s+de|mes\s+de)\s*(\d{{1,2}})\s*{_ANYS}\b")
# En la descripción, solo edades que hablan del público.
_MARCA_PUBLICO = (r"(?:adrecat|adrecada|adrecats|dirigit|dirigida|dirigido|destinat|destinada|destinado|"
                  r"recomanat|recomanada|recomendado|recomendada|pensat|pensada|pensado|edat\s+recomanada|"
                  r"edad\s+recomendada|per\s+a\s+infants|para\s+ninos|per\s+a\s+nens|nens\s+i\s+nenes|"
                  r"ninos\s+y\s+ninas|infants|per\s+a\s+joves|para\s+jovenes|public|publico)")
_DESC_RANGO = re.compile(rf"{_MARCA_PUBLICO}[^.]{{0,40}}?(?:de\s+)?(\d{{1,2}})\s*(?:a|i|fins a|hasta|\s)\s*(\d{{1,2}})\s*{_ANYS}\b")
_DESC_MINIMO = re.compile(rf"{_MARCA_PUBLICO}[^.]{{0,40}}?(?:a\s+partir\s+de|desde|des\s+de|majors\s+de|mayores\s+de|mes\s+de)\s*(\d{{1,2}})\s*{_ANYS}\b")

# En un título, «adults» o «adolescents» pueden ser parte del nombre de la obra («Adultos
# disfuncionales»). Solo cuentan solos en títulos de talleres o cursos («Màgia adults avançat»);
# en los demás hace falta una construcción de destinatario.
_ADULTOS = re.compile(r"\badults?\b|\badultos?\b")
_ADULTOS_EXPLICITO = re.compile(r"\bper\s+a\s+(persones\s+)?adult|\bpara\s+adultos\b|\bpublico\s+adulto\b|\bmajors\s+de\s+18\b|\bmayores\s+de\s+18\b")
# «10 € per adult» es un precio, no el público: solo cuentan construcciones de destinatario.
_ADULTOS_DESC = re.compile(r"\b(adrecat|adrecada|dirigit|dirigida|destinat|destinada|pensat|pensada)\s+a\s+(persones\s+)?adult|\bper\s+a\s+(persones\s+)?adult|\bpublico\s+adulto\b|\bsolo\s+para\s+adultos\b")
_FAMILIAR = re.compile(r"\bfamiliar\b|\ben\s+familia\b|\bper\s+a\s+tota\s+la\s+familia\b|\bpara\s+toda\s+la\s+familia\b|\bper\s+a\s+les\s+families\b")
_INFANTIL = re.compile(r"\binfantil\b|\binfants\b|\bnens\s+i\s+nenes\b|\bninos\s+y\s+ninas\b|\bpetita\s+infancia\b|\bper\s+als\s+mes\s+petits\b|\bpara\s+los\s+mas\s+pequenos\b")
_JOVES = re.compile(r"\bjoves\b|\bjovenes\b|\bjuvenil\b|\badolescents\b|\badolescentes\b")
_TOTS = re.compile(r"\btots\s+els\s+publics\b|\btodos\s+los\s+publicos\b|\bper\s+a\s+tots\s+els\s+publics\b")

_INICIACION = re.compile(r"\binicia(cio|cion|l|ls|les)\b|\bprincipiants?\b|\bprincipiantes?\b|\bbasic|\bbasico|\bno\s+cal\s+experiencia|\bsense\s+experiencia|\bno\s+hace\s+falta\s+experiencia|\bsin\s+experiencia")
_INTERMEDIO = re.compile(r"\bintermedi\b|\bintermedio\b|\bintermedia\b")
_AVANZADO = re.compile(r"\bavancat|\bavanzado|\bperfeccionament\b|\bperfeccionamiento\b|\bconeixements\s+previs\b|\bconocimientos\s+previos\b|\bja\s+tenen\s+coneixements\b")


def _por_edades(minima: int | None, maxima: int | None) -> str | None:
    if maxima is not None and maxima <= 12:
        return "infantil"
    if minima is not None and minima >= 18:
        return "adultos"
    if minima is not None and minima >= 12:
        return "juvenil" if (maxima is not None and maxima <= 17) else "juvenil y adultos"
    if minima is not None and maxima is None:
        # «A partir de 3 anys» suele ser un espectáculo familiar; «a partir de 8 anys», apto para todos desde esa edad.
        return "familiar" if minima <= 6 else "todos los públicos"
    if maxima is not None and maxima <= 17:
        return "juvenil"
    return None


def leer(titulo: str, descripcion: str = "", es_formacion: bool = False) -> dict:
    """Devuelve {"publico", "edad_minima", "edad_maxima", "nivel"} (None si no se sabe)."""
    t = normalizar(titulo)
    d = normalizar(descripcion)
    minima = maxima = None
    m = _RANGO_TITULO.search(t) or _DESC_RANGO.search(d)
    if m:
        a, b = int(m.group(m.lastindex - 1)), int(m.group(m.lastindex))
        if a <= b <= 99:
            minima, maxima = a, b
    else:
        m = _MINIMO.search(t) or _DESC_MINIMO.search(d)
        if m:
            minima = int(m.group(m.lastindex))

    if (es_formacion and _ADULTOS.search(t)) or _ADULTOS_EXPLICITO.search(t) or _ADULTOS_DESC.search(d):
        publico = "adultos"
    elif minima is not None or maxima is not None:
        publico = _por_edades(minima, maxima)
    elif _INFANTIL.search(t):
        publico = "infantil"
    elif _FAMILIAR.search(t) or _FAMILIAR.search(d):
        publico = "familiar"
    elif _TOTS.search(t) or _TOTS.search(d):
        publico = "todos los públicos"
    elif es_formacion and _JOVES.search(t):
        publico = "juvenil"
    elif _INFANTIL.search(d):
        publico = "infantil"
    else:
        publico = None

    nivel = None
    if es_formacion:
        texto = f"{t} {d}"
        if _AVANZADO.search(texto):
            nivel = "avanzado"
        elif _INTERMEDIO.search(texto):
            nivel = "intermedio"
        elif _INICIACION.search(texto):
            nivel = "iniciación"
    return {"publico": publico, "edad_minima": minima, "edad_maxima": maxima, "nivel": nivel}


def etiqueta(datos: dict) -> str | None:
    """Texto corto para mostrar: «infantil (6–12 años) · iniciación»."""
    partes = []
    if datos.get("publico"):
        edades = ""
        if datos.get("edad_minima") is not None and datos.get("edad_maxima") is not None:
            edades = f" ({datos['edad_minima']}–{datos['edad_maxima']} años)"
        elif datos.get("edad_minima") is not None:
            edades = f" (desde {datos['edad_minima']} años)"
        partes.append(datos["publico"] + edades)
    if datos.get("nivel"):
        partes.append(f"nivel {datos['nivel']}")
    return " · ".join(partes) or None
