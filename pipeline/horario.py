"""Lee la tabla de horarios que trae cada actividad y saca días, horas,
precios, duración e idioma.

La tabla viene en HTML con columnas Període · Dies · Hores · Preus ·
Observacions, y celdas que pueden ocupar varias filas (rowspan). Los textos
están en catalán: «Dijous, divendres i dissabte», «5 novembre i 3 desembre»,
«a les 20.15 h», «Entrada general: 18 €», «Durada: 70 minuts»…
"""

from __future__ import annotations

import datetime as dt
import html
import re
from html.parser import HTMLParser

from .util import normalizar, sin_acentos

COLUMNAS = {
    "timetable-period": "periodo",
    "timetable-day": "dias",
    "timetable-hour": "horas",
    "timetable-price": "precios",
    "timetable-description": "observaciones",
}

DIAS_SEMANA = {
    "dilluns": 0, "dimarts": 1, "dimecres": 2, "dijous": 3,
    "divendres": 4, "dissabte": 5, "dissabtes": 5, "diumenge": 6, "diumenges": 6,
    # Por si algún texto llega en castellano
    "lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4,
    "sabado": 5, "sabados": 5, "domingo": 6, "domingos": 6,
}
MESES = {
    "gener": 1, "febrer": 2, "marc": 3, "abril": 4, "maig": 5, "juny": 6,
    "juliol": 7, "agost": 8, "setembre": 9, "octubre": 10, "novembre": 11, "desembre": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "noviembre": 11, "diciembre": 12,
}


class _LectorTabla(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.filas: list[list[tuple[str, int, list[str]]]] = []
        self._celda = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self.filas.append([])
        elif tag == "td" and self.filas is not None:
            clase = a.get("class", "")
            try:
                rowspan = int(a.get("rowspan") or 1)
            except ValueError:
                rowspan = 1
            self._celda = (COLUMNAS.get(clase, clase), rowspan, [])
        elif tag in ("br", "p", "div") and self._celda is not None:
            self._celda[2].append("\n")

    def handle_endtag(self, tag):
        if tag == "td" and self._celda is not None and self.filas:
            self.filas[-1].append(self._celda)
            self._celda = None

    def handle_data(self, data):
        if self._celda is not None:
            self._celda[2].append(data)


def _texto(trozos: list[str]) -> str:
    t = "".join(trozos).replace("\xa0", " ")
    lineas = [re.sub(r"[ \t]+", " ", l).strip() for l in t.split("\n")]
    return "\n".join(l for l in lineas if l)


def leer_tabla(html_tabla: str) -> list[dict]:
    """Convierte la tabla HTML en filas {periodo, dias, horas, precios, observaciones}."""
    if not html_tabla:
        return []
    lector = _LectorTabla()
    lector.feed(html_tabla)
    filas: list[dict] = []
    arrastre: dict[str, list] = {}  # columna -> [texto, filas que faltan]
    for celdas in lector.filas:
        if not celdas:
            continue  # cabecera
        fila: dict[str, str] = {}
        for col, (texto, faltan) in list(arrastre.items()):
            fila[col] = texto
            if faltan <= 1:
                del arrastre[col]
            else:
                arrastre[col][1] = faltan - 1
        for col, rowspan, trozos in celdas:
            texto = _texto(trozos)
            fila[col] = texto
            if rowspan > 1:
                arrastre[col] = [texto, rowspan - 1]
        filas.append(fila)
    return filas


# --- Horas ---------------------------------------------------------------

_HORA = re.compile(r"(?<![\d/])(\d{1,2})(?:[.:,h](\d{2}))?\s*h\b|(?<![\d/])(\d{1,2})[.:](\d{2})(?!\d)")


def leer_horas(texto: str) -> list[dict]:
    """«a les 11.00 h i a les 12.45 h» -> [{inicio: 11:00}, {inicio: 12:45}];
    «de 09.00 h a 15.30 h» -> [{inicio: 09:00, fin: 15:30}]."""
    if not texto:
        return []
    resultado = []
    for trozo in re.split(r",|\bi\b|\n|;|/", texto):
        horas = []
        for m in _HORA.finditer(trozo):
            h = int(m.group(1) or m.group(3))
            mi = int(m.group(2) or m.group(4) or 0)
            if 0 <= h <= 24 and 0 <= mi < 60:
                horas.append(f"{h % 24:02d}:{mi:02d}")
        if not horas:
            continue
        if re.search(r"\bde\b.*\ba\b", trozo) and len(horas) >= 2:
            resultado.append({"inicio": horas[0], "fin": horas[1]})
        else:
            resultado.extend({"inicio": x} for x in horas)
    vistos, unicos = set(), []
    for x in resultado:
        clave = (x["inicio"], x.get("fin"))
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(x)
    return unicos


# --- Días ----------------------------------------------------------------

def _anyo_para(mes: int, dia: int, inicio: dt.date | None, fin: dt.date | None) -> dt.date | None:
    candidatos = []
    anyos = {d.year for d in (inicio, fin) if d} or {dt.date.today().year}
    for a in sorted(anyos | {max(anyos) + 1}):
        try:
            candidatos.append(dt.date(a, mes, dia))
        except ValueError:
            pass
    if not candidatos:
        return None
    dentro = [c for c in candidatos if (not inicio or c >= inicio) and (not fin or c <= fin)]
    if dentro:
        return dentro[0]
    if inicio and fin:
        # Fuera del periodo que da la propia fuente: la fecha más cercana a ese periodo, sin
        # pasarla al año siguiente (error de noviembre de 2026: «30 octubre», ya pasado, salía
        # como función del 30/10/2027). Si cae fuera, el verificador la quita.
        return min(candidatos, key=lambda c: min(abs((c - inicio).days), abs((c - fin).days)))
    if inicio:
        despues = [c for c in candidatos if c >= inicio]
        if despues:
            return despues[0]
    return candidatos[0]


def _fechas_en(texto: str, inicio, fin) -> list[str]:
    """Busca «5 novembre», «21 febrer i 14 març», «3 i 4 de desembre»."""
    fechas = []
    t = normalizar(texto)
    # «3, 4 i 5 de desembre» o «3 i 4 desembre»: varios días seguidos de un mes
    for m in re.finditer(r"((?:\d{1,2}\s*(?:i|y)?\s*)+)(?:de\s+|d\s+)?(" + "|".join(MESES) + r")\b", t):
        mes = MESES[m.group(2)]
        for d in re.findall(r"\d{1,2}", m.group(1)):
            f = _anyo_para(mes, int(d), inicio, fin)
            if f:
                fechas.append(f.isoformat())
    return sorted(set(fechas))


def leer_dias(texto: str, inicio: dt.date | None = None, fin: dt.date | None = None) -> dict:
    """Interpreta la columna «Dies».

    Devuelve {"semana": [0..6], "fechas": [...], "excepto": [...], "festivos": bool}.
    """
    res = {"semana": [], "fechas": [], "excepto": [], "festivos": False}
    if not texto:
        return res
    t = normalizar(texto)
    principal, _, excepciones = t.partition("excepte")
    if not excepciones:
        principal, _, excepciones = t.partition("excepto")
    if excepciones:
        res["excepto"] = _fechas_en(excepciones, inicio, fin)
    if re.search(r"\b(cada dia|tots els dies|todos los dias|diari|diariament)\b", principal):
        res["semana"] = list(range(7))
    for m in re.finditer(r"\bde (\w+) a (\w+)\b", principal):
        a, b = DIAS_SEMANA.get(m.group(1)), DIAS_SEMANA.get(m.group(2))
        if a is not None and b is not None:
            dias = list(range(a, b + 1)) if a <= b else list(range(a, 7)) + list(range(0, b + 1))
            res["semana"].extend(dias)
            principal = principal.replace(m.group(0), " ")
    for palabra in re.findall(r"[a-z]+", principal):
        if palabra in DIAS_SEMANA:
            res["semana"].append(DIAS_SEMANA[palabra])
    res["semana"] = sorted(set(res["semana"]))
    res["festivos"] = bool(re.search(r"\bfestius?\b|\bfestivos?\b", principal))
    res["fechas"] = _fechas_en(principal, inicio, fin)
    return res


# --- Precios, duración e idioma -------------------------------------------

# Los precios NO pasan por `normalizar` (que quita los signos): «24,95 €» y «24.95 €» tienen
# que quedarse con sus decimales. Error de noviembre de 2026: «24.95 €» salía como «95 €».
_NUM = r"\d+(?:[.,']\d+)*"
_EUROS = re.compile(rf"(?<![\d.,'])({_NUM})\s*(?:€|eur\b|euros?\b)")
# «€15»: solo si el «€» no cierra otro importe («49 €\n10 sessions» no es «€10») y va pegado.
_EUROS_ANTES = re.compile(rf"(?<![\d\s])\s?€ ?({_NUM})(?![\d.,'])|^€ ?({_NUM})(?![\d.,'])")
_RANGO = re.compile(rf"(?<![\d.,'])({_NUM})\s*(?:€\s*)?(?:a|al|-|–|i|y|/)\s*({_NUM})\s*(?:€|eur\b|euros?\b)")
_GRATIS = re.compile(r"\b(gratuit|gratuita|gratuits|gratuites|gratis|gratuito|gratuita|entrada lliure|entrada libre|acces lliure|acces gratuit)\b")


def importe(texto: str) -> float | None:
    """«24,95» → 24.95; «24.95» → 24.95; «12'5» → 12.5; «1.200» → 1200; «20.30.5» → None."""
    if re.fullmatch(r"\d+", texto):
        return float(texto)
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?", texto):  # miles con punto
        return float(texto.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d+[.,']\d{1,2}", texto):
        return float(re.sub(r"[,']", ".", texto))
    return None  # forma rara: mejor no mostrar nada que mostrar un precio falso


def _texto_precio(*textos: str) -> str:
    t = sin_acentos(" ".join(x for x in textos if x)).lower()
    t = re.sub(r"[ \t]+", " ", t.replace("’", "'").replace("‘", "'"))
    return re.sub(r"\s*\n\s*", " | ", t)  # el salto de línea separa importes: «€ | 1 h» no es «€1»


def aparece(valor: float, texto: str) -> bool:
    """¿Está este importe escrito, tal cual, en el texto original? (con coma, punto o apóstrofo)."""
    if valor == int(valor):
        formas = [str(int(valor))]
        formas += [f"{int(valor)}{sep}00" for sep in ".,'"] + [f"{int(valor)}{sep}0" for sep in ".,'"]
        formas += [f"{int(valor):,}".replace(",", ".")] if valor >= 1000 else []
    else:
        cent = f"{valor:.2f}"
        formas = [cent.replace(".", sep) for sep in ".,'"]
        if cent.endswith("0"):
            formas += [cent[:-1].replace(".", sep) for sep in ".,'"]
    t = _texto_precio(texto)
    return any(re.search(rf"(?<![\d.,']){re.escape(f)}(?![\d]|[.,']\d)", t) for f in formas)


def leer_precios(*textos: str) -> dict | None:
    """Saca importes en euros. Devuelve None si no hay ninguna pista de precio.

    Cada importe que se devuelve está escrito tal cual en el texto (`aparece`): si no, se descarta."""
    original = " ".join(x for x in textos if x)
    t = _texto_precio(original)
    if not t.strip():
        return None
    importes = []
    for m in _RANGO.finditer(t):
        importes += [m.group(1), m.group(2)]
    importes += _EUROS.findall(t) + [a or b for a, b in _EUROS_ANTES.findall(t)]
    valores = sorted({v for v in (importe(x) for x in importes) if v is not None and 0 < v < 1000 and aparece(v, original)})
    gratis = bool(_GRATIS.search(normalizar(original)))
    taquilla_inversa = "taquilla inversa" in normalizar(original)
    if not valores and not gratis and not taquilla_inversa:
        return None
    res = {"gratis": gratis and not valores, "taquilla_inversa": taquilla_inversa}
    if valores:
        res["minimo"] = valores[0]
        res["maximo"] = valores[-1]
        if gratis:
            res["hay_entradas_gratuitas"] = True  # p. ej. «gratuït per a menors de 10 anys»
    return res


def leer_duracion(*textos: str) -> int | None:
    t = normalizar(" ".join(x for x in textos if x))
    m = re.search(r"durada\s*(?:aproximada)?\s*(?:de)?\s*(\d+)\s*(?:min|minuts|minutos)", t)
    if m:
        return int(m.group(1))
    m = re.search(r"durada\s*(?:aproximada)?\s*(?:de)?\s*(\d+)\s*(?:hores|horas|hora|h)\b(?:\s*(?:i|y)?\s*(\d+)\s*(?:minuts|minutos|min))?", t)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2) or 0)
    m = re.search(r"durada\s*(?:aproximada)?\s*(?:de)?\s*una?\s*hora(?:\s*i\s*mitja)?", t)
    if m:
        return 90 if "mitja" in m.group(0) else 60
    return None


_IDIOMAS = [
    ("catalan", r"\b(en catala|idioma catala|llengua catala|idioma: catala|en catalan)\b"),
    ("castellano", r"\b(en castella|idioma castella|en castellano|en espanyol|idioma: castella)\b"),
    ("ingles", r"\b(en angles|en ingles|in english|idioma angles)\b"),
    ("frances", r"\b(en frances|en frances)\b"),
    ("italiano", r"\b(en italia|en italiano)\b"),
    ("sin_texto", r"\b(sense text|sense paraules|sin texto|sin palabras|gestual|sense dialeg|espectacle visual|teatre visual|no verbal)\b"),
]


def leer_idiomas(*textos: str) -> list[str]:
    t = normalizar(" ".join(x for x in textos if x))
    return [nombre for nombre, patron in _IDIOMAS if re.search(patron, t)]


# --- Todo junto ------------------------------------------------------------

def _fecha(valor: str | None) -> dt.date | None:
    if not valor:
        return None
    try:
        return dt.date.fromisoformat(valor[:10])
    except ValueError:
        return None


def interpretar(html_tabla: str, inicio: str | None, fin: str | None, hoy: dt.date | None = None,
                dias_vista: int = 731) -> dict:
    """Lee la tabla y calcula las próximas funciones (fecha + hora) de los próximos dos años
    (el calendario de la app llega hasta dos años vista: obras en gira y temporadas largas)."""
    hoy = hoy or dt.date.today()
    d_ini, d_fin = _fecha(inicio), _fecha(fin) or _fecha(inicio)
    filas = leer_tabla(html_tabla)
    salida = []
    funciones: set[tuple[str, str]] = set()
    textos_precio, textos_obs = [], []
    for f in filas:
        dias = leer_dias(f.get("dias", ""), d_ini, d_fin)
        horas = leer_horas(f.get("horas", ""))
        if f.get("precios"):
            textos_precio.append(f["precios"])
        if f.get("observaciones"):
            textos_obs.append(f["observaciones"])
        salida.append({
            "texto": {k: v for k, v in f.items() if v},
            "dias": dias,
            "horas": horas,
        })
        # Fechas concretas de esta fila
        fechas: set[dt.date] = {dt.date.fromisoformat(x) for x in dias["fechas"]}
        if dias["semana"] and d_ini:
            desde = max(d_ini, hoy)
            hasta = min(d_fin or desde, hoy + dt.timedelta(days=dias_vista))
            dia = desde
            while dia <= hasta:
                if dia.weekday() in dias["semana"]:
                    fechas.add(dia)
                dia += dt.timedelta(days=1)
        excluidas = {dt.date.fromisoformat(x) for x in dias["excepto"]}
        for fecha in fechas - excluidas:
            if fecha < hoy or fecha > hoy + dt.timedelta(days=dias_vista):
                continue
            if horas:
                for h in horas:
                    funciones.add((fecha.isoformat(), h["inicio"]))
            else:
                funciones.add((fecha.isoformat(), ""))
    # Si la tabla no dice días pero inicio == fin, es una función de un solo día.
    if not funciones and d_ini and d_ini == d_fin and d_ini >= hoy:
        horas = [h for fila in salida for h in fila["horas"]]
        for h in horas or [{"inicio": ""}]:
            funciones.add((d_ini.isoformat(), h["inicio"]))
    todo_texto = textos_precio + textos_obs
    return {
        "filas": salida,
        "proximas_funciones": [{"fecha": a, "hora": b or None} for a, b in sorted(funciones)][:1500],
        "precio": leer_precios(*textos_precio) or leer_precios(*textos_obs),
        "duracion_minutos": leer_duracion(*todo_texto),
        "idiomas": leer_idiomas(*todo_texto),
    }


def texto_plano(html_tabla: str) -> str:
    """Versión legible de la tabla (para la IA y para mostrar)."""
    partes = []
    for f in leer_tabla(html_tabla):
        partes.append(" · ".join(f"{k}: {v}".replace("\n", " ") for k, v in f.items() if v))
    return html.unescape("\n".join(partes))
