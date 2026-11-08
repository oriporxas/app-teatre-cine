"""Primera capa de clasificación: señales de texto, gratis y explicables.

Lee título, descripción, sala, «se celebra a» y artista, y busca vocabulario
general (en catalán, castellano e inglés) de cada disciplina. No hay listas de
espectáculos ni de artistas concretos: solo palabras y construcciones que
describen un tipo de espectáculo. Los criterios están explicados en
docs/clasificacion.md.

Esta capa:
- decide sola cuando no hay clave de IA (y lo indica con «clasificado_por»);
- da a la IA un resumen de pistas;
- decide qué actividades hace falta enviar a la IA (las claramente ajenas al
  sector, como un concierto o una exposición, no se envían).

Trabaja con el formato común de pipeline/fuentes/base.py. Su vocabulario está
pensado para Barcelona (catalán, castellano, inglés): en ciudades con otros
idiomas, la IA hace el trabajo principal y esta capa solo ayuda.
"""

from __future__ import annotations

import re

from .util import normalizar


def minus(texto: str) -> str:
    """Minúsculas conservando acentos (hace falta para distinguir «màgic» de «magic»)."""
    t = (texto or "").lower()
    t = t.replace("l·l", "ll").replace("l.l", "ll").replace("ŀl", "ll")
    t = re.sub(r"[“”«»\"'’‘´`]", " ", t)
    return re.sub(r"\s+", " ", t)


def _r(*patrones: str) -> re.Pattern:
    return re.compile("|".join(f"(?:{p})" for p in patrones))


def _cuenta(patron: re.Pattern, texto: str) -> list[str]:
    return sorted({m.group(0).strip() for m in patron.finditer(texto)})


# --- Vocabulario de magia ---------------------------------------------------
# Fuerte: describe magia como disciplina que alguien hace en directo.
MAGIA_FUERTE = _r(
    r"\b(espectacle|espectáculo|show|xou|número|números|nombres|truc|trucs|truco|trucos|efecte|efectes|efecto|efectos|"
    r"taller|curs|curso|festival|gala|sessió|sesión|nit|noche|vespre|tarda|cabaret|món|mundo|escola|escuela)"
    r"\s+(de|del|d)\s+m[àáa]gia\b",
    r"\bm[àáa]gia\s+(de\s+prop|de\s+cerca|d\s+aprop|de\s+cambra|de\s+saló|de\s+salón|i\s+comèdia|y\s+comedia|i\s+humor|"
    r"y\s+humor|còmica|cómica|familiar|infantil|mental|en\s+directe|en\s+vivo|en\s+viu|kids|clàssica|clásica|moderna|"
    r"negra|general|d\s+escena|de\s+escena|urbana|més\s+espectacular|espectacular|de\s+gran\s+format)\b",
    r"\bil+usionis(me|mo|ta|tes|tas)\b", r"\bil+usionist\b",
    r"\bprestidigita(ció|ción|cion|dor|dora|dors|dores)\b",
    r"\bmentalis(me|mo|ta|tes|tas|m)\b", r"\btelepat", r"\blectura\s+de\s+la\s+ment",
    r"\bcartom[àáa]gia\b", r"\bescapista\b", r"\bgrans\s+il+usions\b|\bgrandes\s+ilusiones\b",
    r"\bclose[\s-]?up\b", r"\bmagician", r"\bmagic\s+(show|lounge|night|club|experience|world)\b",
    r"^(taller|tallers|curs|classe|classes|espectacle|show)\s+m[àáa]gia\s*(\(|$|\*|-|,)",  # «Taller 'Màgia' (…)»
)
# Persona maga en minúsculas: puede ser artista («a càrrec del mag…») o personaje («el mag escombraries»).
MAGIA_PERSONA = _r(r"\b(mag|mags|maga|magues|mago|magos|magas)\b")
# Artista que se presenta como mago: en el TÍTULO, en mayúscula y como nombre («Mag Lari»,
# «El Mago Pop», «Un Mag per Nadal»). En las descripciones no sirve: los personajes de los
# cuentos también van en mayúscula («l'Ase Mag», «la Maga Martina»). «El Mago de Oz» es un personaje.
ARTISTA_MAGO = re.compile(r"\b(Mag|Mago|Maga|Mags|Magos)\b(?!\s+(de|d'|d’|del|dels)\b)")
# Débil: adjetivos y metáforas («nit màgica», «la màgia del Nadal», «grans il·lusions»).
MAGIA_DEBIL = _r(
    r"\bm[àáa]gi(c|ca|cs|ques|co|cos|cas)\b", r"\bm[àáa]gia\b", r"\bmagic\b",
    r"\bil+usions?\b", r"\bilusion(es)?\b", r"\binexplicable", r"\bimpossible|\bimposible",
    r"\bmisteri|\bmisterio", r"\benigma", r"\bescapis(me|mo)\b",
)
METAFORA_MAGIA = _r(r"\bla\s+m[àáa]gia\s+(de|del|dels|de\s+la|de\s+les|d)\b", r"\bm[àáa]gia\s+(molecular|del\s+nadal|de\s+nadal)\b")
AMBIENTE = _r(r"\b(ple|plena|plens|plenes|lleno|llena|llenos|llenas|carregat|carregada)\s+de\s+m[àáa]gia(\s*(,|i|y)\s+\w+)?",
              r"\buna\s+mica\s+de\s+m[àáa]gia\b", r"\bun\s+poco\s+de\s+magia\b", r"\bmolta\s+m[àáa]gia\b",
              r"\bmucha\s+magia\b", r"\bla\s+seva\s+(verdadera\s+)?m[àáa]gia\b", r"\bsu\s+(verdadera\s+)?magia\b")
# La magia como argumento de una historia (aventuras, cuentos, hadas…): no es un número de magia.
ARGUMENTO = _r(r"\baventur", r"\bla\s+història\b|\buna\s+història\b|\bla\s+historia\b|\buna\s+historia\b",
               r"\bprotagonist", r"\bpersonatg|\bpersonaje", r"\bconte\b|\bcontes\b|\bcuento", r"\bviurem\b|\bviviremos\b",
               r"\bhaurà\s+de\b|\bhauran\s+de\b|\bhabrá\s+de\b", r"\bfolleta|\bbruix|\bdrac\b|\bprinces|\bfades?\b",
               r"\bdisney\b", r"\bencanteri|\bencantat|\bencantada|\bhechiz", r"\bfantasia\b|\bfantasía\b")
# Mentalismo y su vocabulario típico en títulos («lo imposible está en tu mente»).
MENTE = _r(r"\bment\b|\bmente\b|\bmind\b|\bpensament|\bpensamiento|\bcervell\b|\bcerebro\b")
IMPOSIBLE = _r(r"\bimpossib|\bimposib|\binexplicab|\bmisteri|\bmisterio|\benigma|\bsecret|\bllegir\b|\bleer\b|\bendevin|\badivin")
# Hipnosis como práctica escénica. «Hipnotitzador» suelto en una descripción suele ser un
# personaje («el gat hipnotitzador»), así que en la descripción solo cuenta el sustantivo.
HIPNOSI = _r(r"\bhipno(si|sis|tit|tis|tist|tiza)")
HIPNOSI_DESC = _r(r"\bhipnosis?\b", r"\b(espectacle|show|espectáculo|sessió|sesión)\s+d.?\s*hipno", r"\bhipnotista")
# Para la etiqueta del tipo de magia.
CERCA = _r(r"\bde\s+prop\b", r"\bd\s+aprop\b", r"\bclose[\s-]?up", r"\bde\s+cerca\b", r"\bde\s+cambra\b",
           r"\bde\s+saló\b|\bde\s+salón\b", r"\bcartom[àáa]gia", r"\bcentímetres|\bcentímetros",
           r"\bpúblic\s+(molt\s+)?reduït|\bpúblico\s+(muy\s+)?reducido", r"\bde\s+taula\b|\bde\s+mesa\b")
MENTAL = _r(r"\bmentalis", r"\btelepat", r"\blectura\s+de\s+la\s+ment|\bleer\s+la\s+mente|\bllegir\s+la\s+ment",
            r"\bprediccions?\b|\bpredicciones?\b", r"\bendevin\w*\s+(el\s+que\s+)?pens|\badivin\w*\s+(lo\s+que\s+)?pens")
GENERAL = _r(r"\bgrans\s+il+usions|\bgrandes\s+ilusiones", r"\bm[àáa]gia\s+urbana", r"\bpickpocket",
             r"\bm[àáa]gia\s+d\s+escena|\bmagia\s+de\s+escena", r"\bgran\s+format|\bgran\s+formato", r"\bil+usions\b")
SUBTIPOS_MAGIA = ("magia de cerca", "magia general", "mentalismo", "hipnosis")

# Género que declara la propia descripción («Contacontes…», «Espectacle de divulgació…»).
GENERO_DECLARADO = re.compile(
    r"\b(?:espectacle|espectacles|espectáculo|show|xou|obra|proposta|producció|activitat)\s+"
    r"(?:(?:familiar|infantil|nadalenc|nadalenca|participatiu|participativa|teatral)\s+)*(?:de|d)\s+([a-zà-úçï]+)")
GENEROS = {
    "magia": ("magia", "màgia", "illusionisme", "mentalisme", "hipnosi", "prestidigitacio", "prestidigitació"),
    "narracion": ("contes", "conte", "narracio", "narració", "contacontes"),
    "divulgacion": ("divulgacio", "divulgació", "sensibilitzacio", "sensibilització", "ciencia", "ciència",
                    "educacio", "educació", "conscienciacio", "conscienciació"),
    "teatro": ("teatre", "titelles", "clown", "humor", "comedia", "comèdia", "improvisacio", "improvisació"),
    "circo": ("circ",), "danza": ("dansa",),
}
NARRACION_EN_TEXTO = _r(r"\bcontacontes\b", r"\bcuentacuentos\b", r"\bnarraci[óo]\s+(oral|de\s+contes)\b")
MUSICAL_EN_TEXTO = _r(r"\b(espectacle|espectáculo|show|xou)\s+musical\b", r"\bun\s+musical\b")


def genero_declarado(desc: str) -> str | None:
    """Lo que la descripción dice que es el espectáculo, si lo dice."""
    if NARRACION_EN_TEXTO.search(desc):
        return "narracion"
    for m in GENERO_DECLARADO.finditer(desc):
        palabra = m.group(1)
        for genero, palabras in GENEROS.items():
            if palabra in palabras:
                return genero
    if MUSICAL_EN_TEXTO.search(desc):
        return "teatro"
    return None


def subtipo_magia(titulo: str, desc: str, hipnosi: bool, mental_titulo: bool) -> str:
    """Etiqueta del tipo de magia: de cerca, general, mentalismo o hipnosis."""
    if hipnosi:
        return "hipnosis"
    c = 2 * len(_cuenta(CERCA, titulo)) + len(_cuenta(CERCA, desc))
    m = 2 * len(_cuenta(MENTAL, titulo)) + len(_cuenta(MENTAL, desc)) + (2 if mental_titulo else 0)
    g = 2 * len(_cuenta(GENERAL, titulo)) + len(_cuenta(GENERAL, desc))
    mejor = max(c, m, g)
    ganadores = [n for n, v in (("magia de cerca", c), ("mentalismo", m), ("magia general", g)) if v == mejor]
    return ganadores[0] if mejor and len(ganadores) == 1 else "magia general"


# --- Otras disciplinas -------------------------------------------------------
CIRCO = _r(r"\bcirc\b", r"\bcirco\b", r"\bcircus\b", r"\bcirc(ense|enses)\b", r"\bnou\s+circ\b",
           r"\bacrob[àa]", r"\bacròbat", r"\bacróbat", r"\bmalabar", r"\btrapez", r"\bfunambul",
           r"\bequilibris", r"\bequilibrista", r"\bcontorsion", r"\bteles\s+aèries|\btelas\s+aéreas",
           r"\broda\s+cyr|\brueda\s+cyr", r"\bmonocicle|\bmonociclo", r"\bpallass|\bpayas", r"\bclown")
TEATRO = _r(r"\bteatr", r"\btheat", r"\bdramat", r"\bdramaturg", r"\bobra\b", r"\bcomèdia|\bcomedia",
            r"\bmonòleg|\bmonólogo|\bmonolog", r"\bstand[\s-]?up", r"\bhumor", r"\bimprovisaci|\bimpro\b",
            r"\btitell|\btítere|\btitere|\bmarionet|\bputxinel", r"\bmusical\b", r"\bcabaret",
            r"\bvarietats|\bvariedades|\bvodevil", r"\bsarsuela|\bzarzuela", r"\bintèrprets|\bintérpretes",
            r"\brepartiment|\breparto\b", r"\bdirecció\b|\bdirección\b", r"\bcompanyia|\bcompañía|\bcia\b",
            r"\ben\s+escena\b", r"\bescenari|\bescenario", r"\bclown")
DANZA = _r(r"\bdansa\b", r"\bdanza\b", r"\bdance\b", r"\bballet", r"\bcoreogr", r"\bflamenc", r"\bclaqué|\bclaque\b",
           r"\bballarin|\bbailarin|\bbailaor", r"\bhip[\s-]?hop", r"\bbreak\s*dance")
CINE = _r(r"\bcinema\b", r"\bcine\b", r"\bpel+[íi]cula", r"\bprojecci[óo]|\bproyecci[óo]n", r"\bcurtmetratge|\bcortometraje",
          r"\bfilm\b", r"\bdocumental\b", r"\bcinef[òo]rum")
MUSICA = _r(r"\bconcert", r"\bconcierto", r"\brecital", r"\bòpera\b|\bópera\b|\bopera\b", r"\borquestra|\borquesta",
            r"\bcoral\b|\bcor\b", r"\bjazz", r"\bbanda\b", r"\bdj\b", r"\bquartet|\bcuarteto", r"\bsimfon|\bsinfon")

# --- Formatos (sobre todo por la primera palabra del título) -----------------
# La agenda del Ayuntamiento empieza casi siempre el título por el formato:
# «Espectacle …», «Taller …», «Concert …», «Exposició …».
FORMATOS = [
    ("espectaculo", r"^(espectacle|espectacles|espectaculo|teatre|teatro|monoleg|monolegs|monologo|circ|circo|comedia|"
                    r"musical|titelles|titella|cabaret|impro|improvisacio|clown|show|varietats|lectura dramatitzada|"
                    r"dansa|danza|ballet|gala|sarsuela|pastorets|els pastorets|obra)\b"),
    ("festival", r"^(festival|mostra|cicle|fira de teatre|temporada|maratoni?)\b"),
    ("formacion", r"^(taller|tallers|curs|cursos|classe|classes|masterclass|master class|workshop|formacio|laboratori|"
                  r"seminari|seminario|intensiu|monografic|escola)\b"),
    ("charla", r"^(conferencia|xerrada|xerrades|colloqui|coloquio|taula rodona|debat|presentacio|jornada|jornades|"
               r"trobada|congres|dialeg|conversa|entrevista|tertulia)\b"),
    ("ensayo_abierto", r"^(assaig obert|assajos oberts|ensayo abierto)\b"),
    ("puertas_abiertas", r"^(portes obertes|jornada de portes obertes|puertas abiertas)\b"),
    ("convocatoria", r"^(convocatoria|open call|crida)\b"),
    ("premios", r"^(premis|premi|concurs|certamen|lliurament)\b"),
    ("cine", r"^(cinema|cine|projeccio|projeccions|cinefòrum|cineforum|cicle de cinema|pel licula|curtmetratges?)\b"),
    ("narracion", r"^(contacontes|conte|contes|narracio|hora del conte|explica m un conte|lletra petita)\b"),
    ("musica", r"^(concert|concerts|recital|opera|audicio|vermut musical|sessio de dj|cantada|coral)\b"),
    ("fuera", r"^(exposicio|exposicions|visita|visites|ruta|rutes|itinerari|passejada|sortida|excursio|club|sessio|"
              r"patis|horari|mercat|campanya|joc|jocs|gimcana|basquet|futbol|handbol|voleibol|cursa|caminada|"
              r"bicicletada|esport|esports|fira|festa|celebracio|dinar|sopar|esmorzar|tast|degustacio|punt|servei|"
              r"inscripcions|assemblea|consell|audiencia|plens?|ple municipal|recollida|donacio|vacunacio|"
              r"mostra d entitats|biblioteca|lectura|hora|espai|setmana|dia|nit)\b"),
]
FORMATOS = [(n, re.compile(p)) for n, p in FORMATOS]

# Para actividades sin formato claro en el título: ¿la descripción habla de un espectáculo?
PISTAS_ESPECTACULO = _r(r"\bespectacle", r"\bespectáculo", r"\bfunci[óo]", r"\bescenari|\bescenario", r"\ben\s+escena\b",
                        r"\bcompanyia|\bcompañía", r"\bpúblic familiar|\bpúblico familiar", r"\bactors?\b|\bactriu|\bactriz",
                        r"\bintèrpret|\bintérpret", r"\bdramat", r"\bestrena\b|\bestreno\b")
FORMACION_EN_TEXTO = _r(r"\btaller\b", r"\bcurs\b", r"\bcurso\b", r"\bclasses?\b", r"\binscripci", r"\baprendre|\baprender",
                        r"\balumnes|\balumnos", r"\bmasterclass")


PREMIOS_EN_TITULO = re.compile(r"\b(premis|premi|premios|premio|lliurament|entrega de premios?|gala de premis)\b")


def formato_del_titulo(titulo: str) -> str | None:
    t = normalizar(titulo)
    # «17è Festival…», «XVII Mostra…», «2026 Cicle…»: el número no es el formato.
    t = re.sub(r"^((\d+\s*(e|a|r|n|t|o|er|na|nd|rd|th)?|[ivxlc]+a?|edicio|edicion)\s+)+", "", t)
    if PREMIOS_EN_TITULO.search(t) and re.match(r"^(gala|nit|cerimonia|acte|festa|lliurament|entrega)\b", t):
        return "premios"
    for nombre, patron in FORMATOS:
        if patron.search(t):
            return nombre
    return None


def analizar(a: dict) -> dict:
    """Devuelve la clasificación por señales y las pistas encontradas."""
    titulo = minus(a.get("titulo", ""))
    desc = minus(" ".join((a.get("descripcion") or {}).values()))
    # «Plena de màgia i humor», «una mica de màgia»: ambiente, no un número de magia.
    desc = AMBIENTE.sub(" ", desc)
    l = a.get("lugar") or {}
    lugar = minus(" ".join(x for x in (l.get("nombre_en_fuente"), l.get("tipo_de_lugar")) if x))
    artista = ""
    m = re.search(r"\b(?:a càrrec d[e'’]?l?a?|a càrrec de|amb|con|de la cia\.?|per)\s+(.+)$", a.get("titulo", ""), re.I)
    if m:
        artista = minus(m.group(1))
    formato = formato_del_titulo(a.get("titulo", ""))
    pistas: list[str] = []

    def puntos(patron, peso_titulo=3.0, peso_desc=1.0, tope_desc=3):
        en_t = _cuenta(patron, titulo)
        en_d = _cuenta(patron, desc)
        en_l = _cuenta(patron, lugar)
        return (peso_titulo * min(len(en_t), 2) + peso_desc * min(len(en_d), tope_desc) + 1.0 * min(len(en_l), 1)), en_t, en_d, en_l

    # Magia
    titulo_original = a.get("titulo", "")
    m_fuerte, mt, md, ml = puntos(MAGIA_FUERTE, 4, 2)
    genero = genero_declarado(desc)
    argumento = bool(ARGUMENTO.search(desc))
    # Artista mago: se presenta como tal («Mag Lari», «a càrrec del mag…»). Un «mag» en
    # minúsculas dentro de una historia es un personaje, no un artista.
    artista_mago = sorted({x.group(0) for x in ARTISTA_MAGO.finditer(titulo_original)})
    persona_a = _cuenta(MAGIA_PERSONA, artista)
    persona_t = _cuenta(MAGIA_PERSONA, titulo)
    persona_d = _cuenta(MAGIA_PERSONA, desc)
    es_artista = bool(artista_mago or persona_a)
    mental_titulo = bool(MENTE.search(titulo) and IMPOSIBLE.search(titulo))
    evidencia = bool(mt or md or es_artista or genero == "magia" or mental_titulo)
    # Menciones de «mags» en la descripción: cuentan si no forman parte de una historia.
    peso_persona_d = 0.0 if (argumento and not evidencia) else 1.5
    m_persona = 4 * es_artista + peso_persona_d * min(len(persona_d), 2)
    metafora = bool(METAFORA_MAGIA.search(titulo)) and not mt
    debil_t = _cuenta(MAGIA_DEBIL, titulo)
    debil_d = _cuenta(MAGIA_DEBIL, desc)
    m_debil = 0.8 * len(debil_t) + 0.4 * min(len(debil_d), 3)
    # «màgia» como sustantivo en la descripción: solo refuerza si ya hay otra señal de un
    # número de magia de verdad. Por sí sola describe un ambiente o un argumento.
    if evidencia or (persona_d and not argumento):
        sustantivo_d = len(re.findall(r"\bm[àáa]gia\b", desc)) - len(METAFORA_MAGIA.findall(desc))
        m_fuerte += 1.5 * max(0, min(sustantivo_d, 2))
    if mental_titulo:
        m_fuerte += 3
    hipnosi = bool(HIPNOSI.search(titulo) or HIPNOSI_DESC.search(desc))
    magia = m_fuerte + m_persona + (0 if (metafora or argumento) else m_debil * 0.5)
    if mt or md or ml:
        pistas.append("vocabulario de magia: " + ", ".join((mt + md + ml)[:4]))
    if es_artista:
        pistas.append("artista mago: " + ", ".join((artista_mago or persona_a)[:2]))
    elif persona_t or persona_d:
        pistas.append("un mago como personaje: " + ", ".join((persona_t or persona_d)[:2]))
    if mental_titulo:
        pistas.append("título típico de mentalismo (la mente + lo imposible)")
    if genero:
        pistas.append(f"la descripción dice que es: {genero}")
    if argumento and (debil_t or debil_d or persona_t or persona_d) and not evidencia:
        pistas.append("la magia forma parte del argumento de una historia")
    elif debil_t and not (mt or md):
        pistas.append("solo palabras ambiguas de magia en el título: " + ", ".join(debil_t[:4]))
    elif debil_d and not (mt or md):
        pistas.append("solo palabras ambiguas de magia en la descripción: " + ", ".join(debil_d[:4]))
    if metafora:
        pistas.append("«la màgia de…» usado como metáfora en el título")
    if hipnosi:
        pistas.append("hipnosis")

    circo, ct, cd, cl = puntos(CIRCO)
    teatro, tt, td, tl = puntos(TEATRO, 2, 0.7)
    danza, dt_, dd, dl = puntos(DANZA)
    cine, it, idd, il = puntos(CINE, 3, 0.5)
    musica, ut, ud, ul = puntos(MUSICA, 3, 0.5)
    for nombre, (t, d, l) in {"circo": (ct, cd, cl), "teatro": (tt, td, tl), "danza": (dt_, dd, dl),
                              "cine": (it, idd, il), "música": (ut, ud, ul)}.items():
        if t or d or l:
            pistas.append(f"{nombre}: " + ", ".join((t + d + l)[:3]))

    disciplinas = {"magia": magia, "circo": circo, "danza": danza, "teatro": teatro}
    sector = magia + circo + danza + teatro
    res = {"formato": formato, "pistas": pistas}

    def decidir(tipo, subtipo, relacion, confianza, motivo):
        res.update(tipo=tipo, subtipo=subtipo, magia=relacion, confianza=round(confianza, 2), motivo=motivo)
        return res

    # Relación con la magia (vale para cualquier tipo)
    def relacion_magia(tipo_final):
        if tipo_final == "magia":
            return "principal"
        fuerte = m_fuerte >= 2 or es_artista or (m_persona >= 3)
        if fuerte or hipnosi:
            return "tema" if tipo_final == "evento" else "incluye"
        return "no"

    def magia_principal(confianza, motivo):
        sub = subtipo_magia(titulo, desc, hipnosi, mental_titulo)
        return decidir("magia", sub, "principal", confianza, motivo)

    # 1) Formatos ajenos al sector
    if formato in ("fuera", "musica"):
        if sector >= 6 and formato == "fuera":
            pass  # p. ej. «Visita teatralitzada»: se decide abajo como espectáculo
        else:
            sub = "música" if formato == "musica" else "otros"
            return decidir("otro", sub, relacion_magia("otro") if m_fuerte >= 4 else "no", 0.9,
                           f"el título indica {'un concierto o música' if formato == 'musica' else 'una actividad ajena a las artes escénicas'}")
    if formato == "cine":
        return decidir("cine", "proyección", "no", 0.9, "el título indica una proyección de cine")

    # 2) Eventos del sector (formación, festivales, charlas…)
    if formato in ("formacion", "festival", "charla", "ensayo_abierto", "puertas_abiertas", "convocatoria", "premios"):
        sub = {"formacion": "formación", "festival": "festival", "charla": "conferencia o coloquio",
               "ensayo_abierto": "ensayo abierto", "puertas_abiertas": "puertas abiertas",
               "convocatoria": "convocatoria", "premios": "premios"}[formato]
        if sector >= 2 or formato in ("ensayo_abierto", "convocatoria"):
            rel = relacion_magia("evento")
            tema = max(disciplinas, key=disciplinas.get)
            conf = 0.85 if sector >= 4 else 0.65
            motivo = f"{sub} sobre {tema} (por el título y la descripción)"
            if rel == "tema" and not (m_fuerte >= 2 or es_artista):
                conf, motivo = 0.5, motivo + "; la magia solo aparece de pasada: dudoso"
            return decidir("evento", sub, rel, conf, motivo)
        if formato == "festival" and (musica >= 3 or cine >= 3):
            return decidir("otro", "música" if musica >= cine else "cine", "no", 0.7, "festival de otra disciplina")
        if sector < 1:
            return decidir("otro", sub, "no", 0.85, f"{sub} sin ninguna relación con las artes escénicas")
        return decidir("otro", sub, "no", 0.55, f"{sub} sin relación clara con las artes escénicas")

    # 3) Manda lo que la descripción (o el título) dice que es, salvo que un artista mago
    #    o el propio título anuncien un espectáculo de magia.
    if formato == "narracion" or (genero == "narracion" and not (es_artista or mt)):
        rel = "incluye" if md else "no"
        return decidir("otro", "narración oral", rel, 0.75,
                       "cuentacuentos o narración; la magia, si aparece, es parte del cuento")
    if genero == "divulgacion" and not (es_artista or mt):
        rel = "incluye" if (md or m_fuerte >= 2) else "no"
        return decidir("otro", "divulgación", rel, 0.75,
                       "espectáculo de divulgación o sensibilización" + ("; usa algunos efectos de magia" if rel == "incluye" else ""))

    # 4) Espectáculos o actividades sin formato claro
    es_espectaculo = formato == "espectaculo" or sector >= 3 or bool(PISTAS_ESPECTACULO.search(desc))
    if not es_espectaculo:
        if FORMACION_EN_TEXTO.search(desc) and sector >= 1.5:
            return decidir("evento", "formación", relacion_magia("evento"), 0.5, "parece formación del sector")
        conf = 0.5 if not desc else 0.7
        return decidir("otro", "otros", "no", conf, "no hay señales de espectáculo"
                       + ("" if desc else " (todavía sin descripción)"))
    teatro_musical = bool(re.search(r"^(espectacle|espectáculo|show)(\s+\w+)?\s+musical\b|^musical\b", titulo.strip())) \
        or genero == "teatro"
    if musica > max(sector, 2) and not mt and not teatro_musical:
        return decidir("otro", "música", "no", 0.6, "espectáculo sobre todo musical")
    if danza > max(teatro, circo, magia) and danza >= 3:
        return decidir("danza", None, relacion_magia("danza"), 0.75, "vocabulario de danza")

    # ¿Magia como razón principal del espectáculo?
    declara_otro = genero in ("teatro", "circo", "danza") and not (es_artista or mt)
    otros = max(circo, teatro * 0.6, danza)
    principal = not declara_otro and (
        bool(mt and not metafora)                  # «Espectacle de màgia …», «Màgia de prop» en el título
        or es_artista                              # «a càrrec del Mag …», «El Mago …»
        or genero == "magia"                       # «és un espectacle de màgia…»
        or mental_titulo                           # «Lo imposible… en tu mente»
        or (m_fuerte + m_persona >= 3.5 and m_fuerte + m_persona >= 1.3 * otros)
    )
    if hipnosi and not declara_otro:
        return magia_principal(0.8 if HIPNOSI.search(titulo) else 0.7, "espectáculo de hipnosis (cuenta como magia)")
    if principal:
        conf = 0.95 if (mt or es_artista or genero == "magia") else (0.8 if m_fuerte >= 4 else 0.65)
        if mt:
            origen = "el título"
        elif es_artista:
            origen = "el artista, que se presenta como mago o maga"
        elif genero == "magia":
            origen = "la descripción, que lo presenta como espectáculo de magia"
        elif mental_titulo and not md:
            conf, origen = 0.65, "el título, típico de mentalismo"
        else:
            origen = "la descripción"
        return magia_principal(conf, f"magia como razón principal del espectáculo (lo dice {origen})")

    if genero in ("circo", "danza"):
        tipo, motivo = ("circo", "la descripción dice que es circo") if genero == "circo" \
            else ("danza", "la descripción dice que es danza")
    elif circo >= 3 and circo >= teatro * 0.7:
        tipo, motivo = "circo", "vocabulario de circo"
    else:
        tipo, motivo = "teatro", ("vocabulario de teatro" if teatro >= 2 or genero == "teatro"
                                  else "espectáculo sin disciplina clara; se asume teatro")
    rel = relacion_magia(tipo)
    if rel == "incluye" and argumento and not (md or es_artista):
        rel = "no"  # la magia es el argumento de la historia, no un número
    titulo_teatro = bool(re.match(r"^(teatre|teatro|monòleg|monólogo|circ|circo)\b", titulo.strip()))
    conf = 0.85 if (circo >= 3 or teatro >= 3 or titulo_teatro or genero) else (0.65 if desc else 0.5)
    if rel == "incluye":
        motivo += "; incluye algún número de magia (no sale al buscar magia)"
        conf = min(conf, 0.75)
    elif debil_t or persona_t or (argumento and (debil_d or persona_d)):
        motivo += "; la magia es parte del argumento o del ambiente, no un número de magia"
    return decidir(tipo, None, rel, conf, motivo)


# Categorías de la lista oficial de equipamientos que indican un lugar donde
# suele haber funciones. Solo se usan para decidir qué ficha leer antes.
LUGARES_ESCENICOS = {"Teatres", "Auditoris", "Centres cívics", "Sales de festes", "Tablaos flamencs"}


def prioridad_lectura(a: dict, categorias_lugar: set[str] | frozenset = frozenset()) -> float:
    """Qué fichas de la guía leer primero (con el título y el tipo de lugar):
    espectáculos y actividades sin formato claro antes que conciertos o exposiciones."""
    f = formato_del_titulo(a.get("titulo", ""))
    t = minus(a.get("titulo", ""))
    base = {"espectaculo": 100, None: 80, "festival": 75, "formacion": 40, "charla": 35, "ensayo_abierto": 90,
            "puertas_abiertas": 50, "convocatoria": 90, "premios": 60, "narracion": 45, "cine": 20,
            "musica": 10, "fuera": 5}.get(f, 30)
    if MAGIA_FUERTE.search(t) or MAGIA_PERSONA.search(t) or MAGIA_DEBIL.search(t) or HIPNOSI.search(t):
        base += 50
    if CIRCO.search(t) or TEATRO.search(t) or DANZA.search(t):
        base += 20
    if categorias_lugar & LUGARES_ESCENICOS and f in ("espectaculo", None, "festival", "formacion", "charla", "narracion"):
        base += 30
    return base


def necesita_ia(resultado: dict) -> bool:
    """Las actividades claramente ajenas (concierto, exposición…) no se envían a la IA."""
    if resultado["tipo"] == "otro" and resultado["confianza"] >= 0.85 and resultado["magia"] == "no":
        return False
    if resultado["tipo"] == "cine" and resultado["confianza"] >= 0.85:
        return False
    return True
