"""Equipo artístico de un espectáculo, leído de su ficha artística.

La guía de Barcelona trae la ficha artística dentro del texto de cada
actividad, escrita de muchas maneras. Aquí se entienden todas las que
aparecen, y se copia solo lo que la fuente etiqueta con un papel
(principio 4: nada se deduce ni se inventa):

- una línea por papel: «Direcció: Anna Prova»;
- varios papeles en una línea: «Direcció: Anna Prova; Intèrpret: Joan Exemple»;
- el papel en una línea y las personas en la siguiente: «Dramatúrgia» / «Anna Prova»,
  o en mayúsculas: «INTÈRPRETS» / «Joan Exemple i Marta Exemple»;
- papeles en mayúsculas dentro de la misma línea: «… IL·LUMINACIÓ Pere Llum SO Pau So»;
- en el título: «Teatre "Obra", text i direcció Anna Prova»;
- en una frase explícita: «amb la direcció de Anna Prova», «dirigida per…».

Si no hay nada de eso, no hay equipo y la app no muestra el apartado.
"""

from __future__ import annotations

import re

from .util import normalizar

# Raíces (sin acentos, en minúscula) de los papeles de una ficha artística.
PAPELES = (
    "direcc", "dirrecc", "dramaturg", "autor", "guio", "guion", "interpret", "repartiment", "reparto",
    "creacio", "creacion", "companyia", "compania", "adaptacio", "adaptacion", "traduccio", "traduccion",
    "music", "composicio", "composicion", "espai sonor", "espacio sonoro", "coreograf", "moviment",
    "movimiento", "escenograf", "espai escenic", "espacio escenico", "vestuari", "vestuario", "illuminacio",
    "iluminacion", "llums", "luces", "video", "visuals", "caracteritzacio", "caracterizacion", "titell",
    "titere", "marionet", "produccio", "produccion", "coproduccio", "coproduccion", "mirada externa",
    "assessor", "asesor", "ajudant", "ayudant", "regidoria", "actor", "actriu", "actriz", "elenc",
    "elenco", "dramatur", "repartiment", "interpretacio", "interpretacion", "versio", "version",
)
# Papeles de una sola palabra corta: tienen que ir enteros («so», no «sobre»).
PAPELES_ENTEROS = ("so", "text", "texto", "idea", "cant", "veu", "veus", "voz", "piano", "guitarra", "amb", "con")
# Etiquetas con dos puntos que no son del equipo artístico.
NO_SON_PAPELES = ("professor", "tallerista", "edat", "durada", "organitza", "suport", "col laboracio",
                  "agraiment", "observacio", "idioma", "lloc", "genere", "public", "premsa", "distribucio",
                  "atencio", "responsable", "imparteix", "preu", "horari", "data", "inscripcio", "fotografia",
                  "disseny grafic", "a carrec", "entrades", "venda", "adreca", "web", "telefon", "informacio",
                  "reserva", "acces", "sinopsi", "marqueting", "comunicacio", "administracio", "reportatge",
                  "gerencia", "comptabilitat", "management", "cap tecnic", "tecnica del teatre", "tecnic del teatre")
# Los papeles principales van primero (brief: dirección, dramaturgia, intérpretes).
ORDEN = (("direcc", "dirrecc"), ("dramatur", "autor", "text", "guio", "guion", "creacio", "creacion", "idea",
                                 "adaptacio", "versio"),
         ("interpret", "repartiment", "reparto", "actor", "actriu", "actriz", "elenc", "amb", "con"),
         ("companyia", "compania", "a carrec"))
ENCABEZADO = re.compile(r"^(fitxa|ficha)\s+(art[íi]stica|t[èe]cnica)(\s+(i|y)\s+(art[íi]stica|t[èe]cnica))?$|"
                        r"^(cr[èe]dits|cr[ée]ditos|equip\s+art[íi]stic|equipo\s+art[íi]stico)$")

# Nombres propios: «Anna Prova», «Josep Maria de la Prova», «Anna Prova i Joan Exemple».
_PALABRA = r"[A-ZÀ-Ý][\w'’À-ÿ.\-]*"
# (sin saltar de línea: el nombre acaba donde acaba la línea)
_NOMBRE = rf"{_PALABRA}(?:[ \t]+(?:(?:de|del|la|las|los|van|von|da|dos|d['’])[ \t]*)?{_PALABRA})*"
_NOMBRES = rf"{_NOMBRE}(?:(?:[ \t]*,[ \t]*|[ \t]+i[ \t]+|[ \t]+y[ \t]+|[ \t]*&[ \t]*){_NOMBRE})*"

_LINEA = re.compile(r"^\s*([A-Za-zÀ-ÿ·.'’ /]{2,45}?)\s*:\s*(\S.*?)\s*$")
_ROLES_EN_MAYUSCULAS = re.compile(r"\s+([A-ZÀ-Ý][A-ZÀ-Ý·.'’]+(?:\s+[A-ZÀ-Ý·.'’]+)*)\s+(?=[A-ZÀ-Ý][a-zà-ÿ])")
_ROL_TITULO = r"(?i:text|texto|direcci[óo]|dramat[úu]rgia|idea|autoria|autoría|creaci[óo]|coreografia|adaptaci[óo]|versi[óo])"
_TITULO = re.compile(rf"^({_ROL_TITULO}(?:\s+(?:i|y)\s+{_ROL_TITULO})*)\s+({_NOMBRES})$")
_PROSA = (
    (re.compile(rf"\b(?:amb|sota)\s+la\s+direcci[óo]\s+(?:de\s+|d['’])({_NOMBRES})"), "direcció"),
    (re.compile(rf"\bdirigi(?:da|t|des|ts)\s+per\s+({_NOMBRES})"), "direcció"),
    (re.compile(rf"\bescri(?:ta|t|tes|ts)\s+per\s+({_NOMBRES})"), "text"),
    (re.compile(rf"\binterpreta(?:da|t|des|ts)\s+per\s+({_NOMBRES})"), "intèrprets"),
    (re.compile(rf"(?:^|\n)\s*[Aa]\s+c[àa]rrec\s+de\s*:?\s+(?:la\s+|l['’]|el\s+|les\s+|els\s+)?"
                rf"(?:(?:cia\.?|companyia)\s+(?=[A-ZÀ-Ý]))?({_NOMBRES})"), "a càrrec de"),
    # «… - Cia Deliri» dentro del título
    (re.compile(rf"[-–]\s*((?:Cia\.?|Companyia|Compañía)\s+{_NOMBRES})"), "companyia"),
    # Frase corta y sola: «Amb Marga Socias.»
    (re.compile(rf"(?:^|\n|\.\s)\s*(?:Amb|Con)\s+({_NOMBRES})[ \t]*(?:\.|$)", re.M), "amb"),
    (re.compile(rf"(?:^|\n)\s*(?:[Aa]mb|[Cc]on)\s+(?:la\s+)?((?:Cia\.?|Companyia|Compañía)\s+{_NOMBRES})"), "companyia"),
)
_COMILLAS = (r'"(.+?)"', r"“(.+?)”", r"«(.+?)»", r"(?<![A-Za-zÀ-ÿ])['‘](.+?)['’](?![A-Za-zÀ-ÿ])")


def _fin_del_nombre(titulo: str) -> int:
    """Dónde acaba el nombre entre comillas del título (0 si no lleva comillas)."""
    for patron in _COMILLAS:
        m = re.search(patron, titulo)
        if m:
            return m.end()
    return 0


def _norm(etiqueta: str) -> str:
    return normalizar(re.sub(r"il\W*lumin", "illumin", etiqueta.lower()))


def es_papel(etiqueta: str) -> bool:
    n = _norm(etiqueta)
    if not n or len(n.split()) > 6 or any(x in n for x in NO_SON_PAPELES):
        return False
    return (any(re.search(rf"\b{re.escape(p)}", n) for p in PAPELES)
            or any(re.search(rf"\b{p}\b", n) for p in PAPELES_ENTEROS))


def _parece_etiqueta(texto: str) -> bool:
    """Dentro de una ficha artística, cualquier «Algo: …» corto es un papel («Músics: …»)."""
    n = _norm(texto)
    return bool(n) and len(n.split()) <= 5 and texto[:1].isupper() and not any(x in n for x in NO_SON_PAPELES)


def _etiqueta_sola(linea: str, en_ficha: bool) -> bool:
    """«Dramatúrgia», «INTÈRPRETS», «Idea original:»: un papel solo en su línea."""
    t = linea.strip()
    if not t or len(t) > 45 or re.search(r"[.,;!?¿¡()]", t.rstrip(":")):
        return False
    base = t.rstrip(":").strip()
    return es_papel(base) or (en_ficha and t.endswith(":") and _parece_etiqueta(base))


def _partir(etiqueta: str, valor: str) -> list[tuple[str, str]]:
    """«Escenografia: Anna Prova IL·LUMINACIÓ Pere Llum SO Pau So» -> tres papeles."""
    partes: list[tuple[str, str]] = []
    while True:
        m = _ROLES_EN_MAYUSCULAS.search(valor)
        if not (m and es_papel(m.group(1))):
            partes.append((etiqueta, valor))
            return partes
        partes.append((etiqueta, valor[:m.start()]))
        etiqueta, valor = m.group(1), valor[m.end():]


def _limpiar_etiqueta(e: str) -> str:
    return re.sub(r"il\W*lumin", "il·lumin", " ".join(e.split()).strip(" .:").lower())


def _limpiar_valor(v: str) -> str:
    return " ".join(v.split()).strip(" .;,:")


def _prioridad(etiqueta: str) -> int:
    n = _norm(etiqueta)
    if n.startswith("direcc") and any(x in n for x in ("music", "tecnic", "produc")):
        return len(ORDEN)
    for i, raices in enumerate(ORDEN):
        if any(n.startswith(r) for r in raices):
            return i
    return len(ORDEN)


def _analizar(descripcion: str | None, titulo: str | None = None) -> tuple[list[list[str]], set[int]]:
    lineas = [l.strip() for l in (descripcion or "").splitlines()]
    pares: list[tuple[str, str]] = []
    usadas: set[int] = set()
    en_ficha = False
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        # «Fitxa artística» (a veces con los papeles detrás, en la misma línea)
        m = re.match(r"^(fitxa|ficha)\s+(art[íi]stica|t[èe]cnica)[^:]*:?\s*", linea, re.I)
        if ENCABEZADO.match(linea.rstrip(":").strip().lower()) or (m and m.end() < len(linea)):
            en_ficha = True
            usadas.add(i)
            if m and m.end() < len(linea):
                linea = linea[m.end():]
            else:
                i += 1
                continue
        siguiente = lineas[i + 1] if i + 1 < len(lineas) else ""
        if (_etiqueta_sola(linea, en_ficha) and siguiente and not _etiqueta_sola(siguiente, en_ficha)
                and not _LINEA.match(siguiente) and re.match(r"[A-ZÀ-Ý0-9]", siguiente)):
            pares.append((linea.rstrip(":"), siguiente))
            usadas.update({i, i + 1})
            i += 2
            continue
        encontrados = []
        for parte in re.split(r"\s*;\s*", linea):
            m2 = _LINEA.match(parte)
            if m2 and (es_papel(m2.group(1)) or (en_ficha and _parece_etiqueta(m2.group(1)))):
                encontrados.append((m2.group(1), m2.group(2)))
        if encontrados:
            pares.extend(encontrados)
            usadas.add(i)
        i += 1

    # En el título: «Teatre "Obra", text i direcció Anna Prova - dramatúrgia Joan Exemple»
    if titulo:
        cierre = _fin_del_nombre(titulo)
        for trozo in re.split(r"\s*,\s*|\s*[-–]\s+", titulo[cierre:] if cierre else ""):
            mt = _TITULO.match(trozo.strip())
            if mt:
                pares.append((mt.group(1), mt.group(2)))
    # Quién firma el espectáculo, según el título: «…", amb Anna Prova», «…", de la Cia. Prova»,
    # «Els Pastorets del barri, a càrrec d'Abraxas Teatre» (sin comillas: lo que va tras la coma).
    if titulo:
        cierre = _fin_del_nombre(titulo)
        if cierre:
            resto = titulo[cierre:].strip(" ,.-–")
        else:
            mc = re.search(r",\s*((?:a\s+c[àa]rrec|amb)\b.*)$", titulo, re.I)
            resto = mc.group(1) if mc else ""
        mf = re.match(r"^(a\s+c[àa]rrec\s+d(?:e\s+la\s+|e\s+l['’]|el\s+|e\s+|['’]en\s+|els\s+|['’])|amb\s+(?:la\s+|el\s+|l['’])?|"
                      r"de\s+(?:la\s+|l['’])?|d['’])(.+)$", resto, re.I)
        if mf and re.match(r"[A-ZÀ-Ý]", mf.group(2)) and not _TITULO.match(resto):
            conector = _norm(mf.group(1))
            quien = mf.group(2)
            if conector.startswith("a carrec"):
                papel = "a càrrec de"
            elif conector.startswith("amb"):
                papel = "amb"
            elif re.match(r"(?i)(cia\b|cia\.|companyia|compañía|grup|col·lectiu|colectivo)", quien):
                papel = "companyia"
            else:
                papel = "autoria"
            # «de Josep Prova a càrrec del Grup de Teatre Exemple»: dos papeles
            dos = re.split(r"\s+a\s+c[àa]rrec\s+d(?:e\s+la\s+|e\s+l['’]|el\s+|e\s+|['’])", quien, maxsplit=1)
            if len(dos) == 2 and papel != "a càrrec de":
                pares.insert(0, ("a càrrec de", dos[1]))
                quien = dos[0]
            pares.insert(0, (papel, quien))
    # En una frase explícita: «amb la direcció de…», «dirigida per…»
    texto = (titulo or "") + "\n" + (descripcion or "")
    for patron, papel in _PROSA:
        mp = patron.search(texto)
        if mp:
            pares.append((papel, mp.group(1)))

    equipo: list[tuple[int, int, str, str]] = []
    vistos: set[str] = set()
    for etiqueta, valor in pares:
        for e, v in _partir(etiqueta, valor):
            e, v = _limpiar_etiqueta(e), _limpiar_valor(v)
            if not v or len(v) > 300 or not re.search(r"[A-ZÀ-Ý]", v) or e in vistos:
                continue
            # La misma persona con el mismo papel ya está (p. ej. en el título y en la ficha)
            if _norm(e) in {_norm(x) for x in vistos} :
                continue
            vistos.add(e)
            equipo.append((_prioridad(e), len(equipo), e, v))
    return [[e, v] for _, _, e, v in sorted(equipo)][:24], usadas


def leer(descripcion: str | None, titulo: str | None = None) -> list[list[str]]:
    """[[papel, personas], …] en el orden de importancia; vacío si no hay ficha artística."""
    return _analizar(descripcion, titulo)[0]


def sin_creditos(descripcion: str | None) -> str:
    """La descripción sin las líneas de la ficha artística (ya se muestran aparte)."""
    _, usadas = _analizar(descripcion)
    lineas = (descripcion or "").splitlines()
    return "\n".join(l for i, l in enumerate(lineas) if i not in usadas).strip()
