"""Género de una obra de teatro (comedia, drama, musical, títeres…), solo si es seguro.

Decisión de Uri (9/11/2026): la tarjeta de cada obra enseña su género para que
se vea de un vistazo, pero **solo cuando hay seguridad**. Esta capa (reglas,
gratis) solo acepta lo que el texto dice de forma explícita:

- una etiqueta de género al principio de la descripción («Musical. Una sàtira…»,
  «Teatre musical. 90 minuts…») o en una línea «Gènere: Comèdia»;
- una frase que presenta la obra con su género («és una comèdia», «aquest
  musical», «un drama familiar», «un espectacle de titelles», «teatre
  d'objectes»…);
- el título («Musical "…"», «Monòleg "…"», «…, el musical»).

Una palabra suelta no basta: «una mica de comèdia», «el drama de l'habitatge»,
«una alta dosi d'improvisació» o «direcció musical» no dan género. Si el texto
da señales contradictorias (comedia y drama sin decir «tragicomèdia»), no se
pone ninguno de los dos. El género que se deduce del argumento lo pondrá la IA
cuando se active (`clasificar_ia.py`), también solo si está segura.

Sin listas de obras ni de artistas: solo vocabulario general (catalán,
castellano, inglés).
"""

from __future__ import annotations

import re

from .util import normalizar

# Orden en que se muestran (de más a menos informativo a primera vista).
GENEROS = ("musical", "títeres", "monólogo", "improvisación", "clown", "cabaret", "teatro de objetos",
           "teatro físico", "lectura dramatizada", "teatro documental", "suspense", "tragicomedia",
           "comedia", "drama", "tragedia")
MAXIMO = 2

# Adjetivos que pueden ir entre el artículo y el nombre del género («una premiada comèdia»).
_ADJ = (r"(?:(?:nou|nova|nuevo|nueva|gran|petit|petita|pequeno|pequena|divertid\w*|hilarant|esbojarrad\w*|"
        r"delirant|tendra|tierna|trepidant|brillant|premiad\w*|aclamad\w*|esperad\w*|autentic\w*|veritable|"
        r"bon|bona|buen|buena|millor|mejor|deliciosa|deliciós|delicioso|preciosa|precioso|emocionant|"
        r"emocionante|original|irreverent|irreverente|hilarante|desternillant\w*) )?")
_ART = r"(?:un|una|el|la|l|aquest|aquesta|este|esta|es un|es una|son un|son una|a|an|the)"


def _r(*patrones: str) -> re.Pattern:
    return re.compile("|".join(f"(?:{p})" for p in patrones))


# Patrones sobre el texto normalizado (minúsculas, sin acentos ni signos).
PATRONES: dict[str, re.Pattern] = {
    "musical": _r(
        rf"\b{_ART} {_ADJ}musical\b(?! (de|del|d|a) (la |l )?(direccio|direccion|produccio|produccion))",
        # «teatre musical», pero no «llegenda del teatre musical» (eso es su carrera, no la obra)
        r"(?<!del )(?<!de )(?<!\bd )\b(teatre|teatro|comedia|monoleg|monologo) musical\b",
        r"\b(espectacle|espectaculo|obra|proposta|propuesta|peca|pieza|projecte|proyecto|muntatge|montaje|"
        r"produccio|produccion) (\w+ )?(de|d) (teatre|teatro) musical\b",
        r"\b(versio|version|adaptacio|adaptacion) musical\b",
    ),
    "títeres": _r(
        # «espectacle de titelles», «una obra amb marionetes» (no «la trama del teatre de marionetes»)
        r"\b(espectacle|espectacles|espectaculo|espectaculos|obra|historia|conte|cuento|peca|pieza|"
        r"muntatge|montaje|proposta|propuesta|funcio|funcion|show) (\w+ )?(de|d|amb|con) (\w+ )?"
        r"(titelles|titella|marionetes|marionetas|titeres|putxinellis|guinyol)\b",
        r"\b(un|es un|aquest|este) (teatre|teatro) (de|d) (titelles|marionetes|marionetas|titeres)\b",
        r"\b(amb|con|i|y) (titelles|marionetes|marionetas|titeres)\b",
        r"\bpuppet (show|theatre|theater)\b",
    ),
    "monólogo": _r(
        rf"\b{_ART} {_ADJ}(monoleg|monologo)\b",
        r"\b(monolegs|monologos|monoleg|monologo) (d|de) humor\b",
        r"\bstand ?up\b",
    ),
    "improvisación": _r(
        r"\b(teatre|teatro|espectacle|espectaculo|show|xou|match|lliga|liga|format|formato|sessio|sesion|"
        r"nit|noche|batalla|combat|torneig|torneo|duel|duelo) (d|de) (improvisacio|improvisacion|impro)\b",
        r"\b(improvisacio|improvisacion) teatral\b",
        r"\bimpro (show|teatral|comedy)\b",
    ),
    "cabaret": _r(
        rf"\b{_ART} {_ADJ}cabaret\b",
        r"\bcabaret (musical|politic|politico|brutal|burlesque|literari|literario)\b",
        r"\b(espectacle|espectaculo|show|nit|noche) (de|d) cabaret\b",
    ),
    "teatro de objetos": _r(r"\b(teatre|teatro) (d|de) (objectes|objetos)\b", r"\bobject theat(re|er)\b"),
    "teatro físico": _r(
        r"\b(teatre|teatro) (fisic|fisico|gestual|de gest|de gesto)\b",
        r"\bphysical theat(re|er)\b",
    ),
    "lectura dramatizada": _r(r"\blectura (dramatitzada|dramatizada|escenificada|teatralitzada|teatralizada)\b"),
    "teatro documental": _r(r"\b(teatre|teatro) (documental|verbatim)\b"),
    "suspense": _r(
        rf"(?<!sobre )\b{_ART} {_ADJ}thriller\b",
        r"(?<!sobre un )\bthriller (psicologic|psicologico|immobiliari|inmobiliario|policiac|policiaco|politic|politico|teatral)\b",
        r"\b(obra|comedia|espectacle|espectaculo|historia|thriller) (de|d) (suspens|suspense|intriga)\b",
    ),
    "tragicomedia": _r(r"\btragicomedia\b", r"\bcomedia dramatica\b"),
    "comedia": _r(
        r"\b(es|son|sera) (una|un) " + _ADJ + r"comedia\b",
        r"\b(una|aquesta|esta|nova|nueva) " + _ADJ + r"comedia (sobre|de|d|que|on|donde|amb|con|negra|negre|"
        r"romantica|musical|acida|absurda|esbojarrada|hilarant|hilarante|delirant|social|familiar|costumista|"
        r"surrealista|per|para|plena|llena|tendra|irreverent|brillant|fresca|sorprenent|divertid\w*|catalana|"
        r"classica|clasica|amarga|coral|alocada|bogeria|disparatada|negra)\b",
        r"\bcomedia (negra|negre|romantica|d embolics|de embolics|de enredo|absurda|acida|bufa|de situacio|"
        r"de situacion|dell arte|musical|esbojarrada|disparatada|alocada|costumista)\b",
        r"\bcommedia dell arte\b",
        rf"\b(a|an) {_ADJ}comedy\b", r"\bcomedy show\b",
        r"\b(espectacle|espectaculo|show|xou|monolegs|monologos|monoleg|monologo|nit|noche|sessio|sesion|"
        r"obra|gala) (d|de) (humor|comedia)\b",
        rf"\b(es una|una|aquesta|esta) {_ADJ}(satira|farsa)\b",
    ),
    "drama": _r(
        rf"\b(es|son) (un|una) {_ADJ}drama\b",
        rf"\b(un|aquest|este) {_ADJ}drama (familiar|social|psicologic|psicologico|rural|historic|historico|"
        r"intens|intenso|contemporani|contemporaneo|politic|politico|existencial|domestic|domestico|romantic|"
        r"romantico|sobre|que|on|donde|de|amb|con|ambientat|ambientado|basat|basado|coral|intim|intimo|"
        r"biografic|biografico|judicial|carregat|cargado)\b",
        rf"\b(a|an) {_ADJ}drama\b",
    ),
    "tragedia": _r(
        # Solo la obra presentada como tragedia («és una tragèdia», «aquesta tragèdia», «una tragèdia
        # grega»); «una tragèdia familiar que es repeteix» suele ser el argumento, no el género.
        r"\b(es|son) una " + _ADJ + r"tragedia\b",
        rf"\b(aquesta|esta) {_ADJ}tragedia\b",
        rf"\buna {_ADJ}tragedia (grega|griega|classica|clasica|contemporania|contemporanea|moderna|shakespeariana)\b",
        r"\btragedia (grega|griega|classica|clasica)\b",
    ),
}

_HUMOR_MONOLEG = re.compile(r"\b(monolegs|monologos|monoleg|monologo) (d|de) humor\b|\bstand ?up\b")

# Etiquetas de género tal como las escribe la fuente al principio («Musical.»), en
# «Gènere: …» o justo antes de la duración («Teatre musical. 90 minuts»).
ETIQUETAS = {
    "musical": "musical", "teatre musical": "musical", "teatro musical": "musical", "comedia musical": "musical",
    "comedia": "comedia", "humor": "comedia", "comedia negra": "comedia", "comedia negre": "comedia",
    "drama": "drama", "tragedia": "tragedia", "tragicomedia": "tragicomedia",
    "monoleg": "monólogo", "monologo": "monólogo", "stand up": "monólogo",
    "improvisacio": "improvisación", "improvisacion": "improvisación", "impro": "improvisación",
    "titelles": "títeres", "teatre de titelles": "títeres", "titeres": "títeres", "marionetes": "títeres",
    "teatre d objectes": "teatro de objetos", "teatro de objetos": "teatro de objetos",
    "teatre fisic": "teatro físico", "teatro fisico": "teatro físico", "teatre gestual": "teatro físico",
    "cabaret": "cabaret", "thriller": "suspense", "lectura dramatitzada": "lectura dramatizada",
    "lectura dramatizada": "lectura dramatizada", "teatre documental": "teatro documental",
}
_ETIQUETA_INICIO = re.compile(r"^\s*([^\.\n:]{2,40})[\.\n]")
_ETIQUETA_DURACION = re.compile(r"(?:^|[\.\n]\s*)([A-ZÀ-Úa-zà-úçï' \-]{3,40})\.\s*\d+\s*(?:minuts|minutos|min)\b")
_ETIQUETA_GENERE = re.compile(r"(?i)\bg[èée]nere?o?\s*:\s*([^\n\.;]{2,40})")

# Título: empieza por el género («Musical "…"», «Monòleg "…"», «Titelles "…"») o «…, el musical».
_TITULO = {
    "musical": re.compile(r"^(musical|teatre musical|teatro musical)\b|^(espectacle|espectaculo|show)( \w+)? musical\b|"
                          r"\b(el|the|un) musical\b|\bcomedia musical\b"),
    "monólogo": re.compile(r"^(monoleg|monologo|monolegs|monologos)\b|\bstand ?up\b"),
    "títeres": re.compile(r"^(espectacle (familiar )?de )?(titelles|titeres|marionetes|marionetas)\b"),
    "improvisación": re.compile(r"^(impro|improvisacio|improvisacion)\b"),
    "cabaret": re.compile(r"^cabaret\b"),
    "lectura dramatizada": re.compile(r"^lectura (dramatitzada|dramatizada|escenificada)\b"),
    "comedia": re.compile(r"^comedia\b"),
}


def _etiquetas(texto: str) -> list[str]:
    """Géneros que la fuente escribe como etiqueta."""
    res = []
    candidatos = []
    m = _ETIQUETA_INICIO.match(texto)
    if m and len(m.group(1).split()) <= 3:
        candidatos.append(m.group(1))
    candidatos += [m.group(1) for m in _ETIQUETA_DURACION.finditer(texto)]
    for m in _ETIQUETA_GENERE.finditer(texto):
        candidatos += re.split(r"\s*(?:/|,| i | y )\s*", m.group(1))
    for c in candidatos:
        g = ETIQUETAS.get(normalizar(c))
        if g and g not in res:
            res.append(g)
    return res


def leer(titulo: str, descripcion: str | None, subtipo: str | None = None) -> list[str]:
    """Géneros seguros de una obra de teatro (como mucho dos), en el orden de GENEROS."""
    texto = descripcion or ""
    etiquetas = _etiquetas(texto)
    t = normalizar(titulo)
    d = normalizar(texto)
    encontrados = set(etiquetas)
    for genero, patron in _TITULO.items():
        if patron.search(t):
            encontrados.add(genero)
    for genero, patron in PATRONES.items():
        if patron.search(d):
            encontrados.add(genero)
    if _HUMOR_MONOLEG.search(d) or _HUMOR_MONOLEG.search(t):
        encontrados.add("comedia")
    if subtipo == "clown":
        encontrados.add("clown")
    if "tragicomedia" in encontrados:
        encontrados -= {"comedia", "drama", "tragedia"}
    tono = encontrados & {"comedia", "drama", "tragedia"}
    if len(tono) > 1:
        # Señales contradictorias: solo vale lo que la fuente pone como etiqueta.
        encontrados -= tono - set(etiquetas[:1])
        if len(encontrados & {"comedia", "drama", "tragedia"}) > 1:
            encontrados -= {"comedia", "drama", "tragedia"}
    return [g for g in GENEROS if g in encontrados][:MAXIMO]


def es_musical(titulo: str, descripcion: str | None) -> bool:
    """¿Es teatro musical? (lo dice el título, una etiqueta o una frase explícita)."""
    return "musical" in leer(titulo, descripcion)
