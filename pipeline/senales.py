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


# --- Vocabulario de magia ---------------------------------------------------
# Fuerte: describe magia como disciplina.
MAGIA_FUERTE = _r(
    r"\b(espectacle|espectáculo|show|número|números|nombres|truc|trucs|truco|trucos|taller|curs|curso|festival|gala|"
    r"sessió|sesión|nit|noche|vespre|tarda|cabaret|món|mundo|història|historia|escola|escuela)\s+(de\s+|del\s+)?m[àáa]gia\b",
    r"\bm[àáa]gia\s+(de\s+prop|de\s+cerca|i\s+comèdia|y\s+comedia|i\s+humor|y\s+humor|còmica|cómica|familiar|infantil|"
    r"per\s+a|para|mental|amb|con|en\s+directe|en\s+vivo|kids|clàssica|clásica|moderna|negra|general|d.escena|de\s+saló)\b",
    r"\bil+usionis(me|mo|ta|tes|tas)\b", r"\bil+usionist\b",
    r"\bprestidigita(ció|ción|cion|dor|dora|dors|dores)\b",
    r"\bmentalis(me|mo|ta|tes|tas|m)\b",
    r"\bcartom[àáa]gia\b", r"\bescapista\b",
    r"\bclose[\s-]?up\b", r"\bmagician", r"\bmagic\s+(show|lounge|night|club|experience|world)\b",
    r"^(taller|tallers|curs|classe|classes|espectacle|show)\s+m[àáa]gia\s*(\(|$|\*|-|,)",  # «Taller 'Màgia' (…)»
)
# Persona maga: «el Mag Lari», «a càrrec del mag», «el mago», «la maga».
MAGIA_PERSONA = _r(r"\b(mag|mags|maga|magues|mago|magos|magas)\b")
# Débil: adjetivos y metáforas («nit màgica», «la màgia del Nadal», «grans il·lusions»).
MAGIA_DEBIL = _r(
    r"\bm[àáa]gi(c|ca|cs|ques|co|cos|cas)\b", r"\bm[àáa]gia\b", r"\bmagic\b",
    r"\bil+usions?\b", r"\bilusion(es)?\b", r"\binexplicable", r"\bimpossible|\bimposible",
    r"\bmisteri|\bmisterio", r"\benigma", r"\bescapis(me|mo)\b",
)
METAFORA_MAGIA = _r(r"\bla\s+m[àáa]gia\s+(de|del|dels|de\s+la|de\s+les|d)\b", r"\bm[àáa]gia\s+(molecular|del\s+nadal|de\s+nadal)\b")
# Hipnosis como práctica escénica. «Hipnotitzador» suelto en una descripción suele ser un
# personaje («el gat hipnotitzador»), así que en la descripción solo cuenta el sustantivo.
HIPNOSI = _r(r"\bhipno(si|sis|tit|tis|tist|tiza)")
HIPNOSI_DESC = _r(r"\bhipnosis?\b", r"\b(espectacle|show|espectáculo|sessió|sesión)\s+d.?\s*hipno", r"\bhipnotista")

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


def _cuenta(patron: re.Pattern, texto: str) -> list[str]:
    return sorted({m.group(0).strip() for m in patron.finditer(texto)})


def analizar(a: dict) -> dict:
    """Devuelve la clasificación por señales y las pistas encontradas."""
    titulo = minus(a.get("titulo", ""))
    desc = minus(" ".join((a.get("descripcion") or {}).values()))
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
    m_fuerte, mt, md, ml = puntos(MAGIA_FUERTE, 4, 2)
    persona_t = _cuenta(MAGIA_PERSONA, titulo)
    persona_d = _cuenta(MAGIA_PERSONA, desc)
    persona_a = _cuenta(MAGIA_PERSONA, artista)
    m_persona = 4 * bool(persona_a or persona_t) + 1.5 * min(len(persona_d), 2)
    metafora = bool(METAFORA_MAGIA.search(titulo)) and not mt
    debil_t = _cuenta(MAGIA_DEBIL, titulo)
    debil_d = _cuenta(MAGIA_DEBIL, desc)
    m_debil = 0.8 * len(debil_t) + 0.4 * min(len(debil_d), 3)
    # «màgia» como sustantivo en la descripción, fuera de metáforas («la màgia de…»): solo
    # refuerza si ya hay otra señal (un mago o maga, o vocabulario fuerte). Por sí sola no
    # basta: «ple de bellesa, màgia i encant» describe un ambiente, no un número de magia.
    if mt or md or persona_t or persona_a or persona_d:
        sustantivo_d = len(re.findall(r"\bm[àáa]gia\b", desc)) - len(METAFORA_MAGIA.findall(desc))
        m_fuerte += 1.5 * max(0, min(sustantivo_d, 2))
    hipnosi = bool(HIPNOSI.search(titulo) or HIPNOSI_DESC.search(desc))
    magia = m_fuerte + m_persona + (0 if metafora else m_debil * 0.5)
    if mt or md or ml:
        pistas.append("vocabulario de magia: " + ", ".join((mt + md + ml)[:4]))
    if persona_a or persona_t or persona_d:
        pistas.append("persona maga: " + ", ".join((persona_a or persona_t or persona_d)[:2]))
    if debil_t and not (mt or md):
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
        fuerte = m_fuerte >= 2 or bool(persona_a or persona_t) or (m_persona >= 3)
        if fuerte:
            return "tema" if tipo_final == "evento" else "incluye"
        if hipnosi:
            return "incluye" if tipo_final != "evento" else "tema"
        return "no"

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
            if rel == "tema" and not (m_fuerte >= 2 or persona_a):
                # Solo un personaje mago («l'aventura del mag X»), sin trucos en la descripción.
                conf, motivo = 0.5, motivo + "; la magia solo aparece como personaje: dudoso"
            return decidir("evento", sub, rel, conf, motivo)
        if formato == "festival" and (musica >= 3 or cine >= 3):
            return decidir("otro", "música" if musica >= cine else "cine", "no", 0.7, "festival de otra disciplina")
        if sector < 1:
            return decidir("otro", sub, "no", 0.85, f"{sub} sin ninguna relación con las artes escénicas")
        return decidir("otro", sub, "no", 0.55, f"{sub} sin relación clara con las artes escénicas")

    if formato == "narracion":
        if md or persona_d:
            return decidir("otro", "narración oral", "incluye", 0.5,
                           "cuentacuentos que menciona trucos o un mago en la descripción; dudoso")
        if sector - magia < 3:
            return decidir("otro", "narración oral", "no", 0.7,
                           "cuentacuentos o narración (la magia del título es el tema del cuento)" if magia
                           else "cuentacuentos o narración (no es teatro)")

    # 3) Espectáculos o actividades sin formato claro
    es_espectaculo = formato == "espectaculo" or sector >= 3 or bool(PISTAS_ESPECTACULO.search(desc))
    if not es_espectaculo:
        if FORMACION_EN_TEXTO.search(desc) and sector >= 1.5:
            return decidir("evento", "formación", relacion_magia("evento"), 0.5, "parece formación del sector")
        conf = 0.5 if not desc else 0.7
        return decidir("otro", "otros", "no", conf, "no hay señales de espectáculo"
                       + ("" if desc else " (todavía sin descripción)"))
    if musica > max(sector, 2) and not mt:
        return decidir("otro", "música", "no", 0.6, "espectáculo sobre todo musical")
    if danza > max(teatro, circo, magia) and danza >= 3:
        return decidir("danza", None, relacion_magia("danza"), 0.75, "vocabulario de danza")

    # ¿Magia como disciplina principal?
    otros = max(circo, teatro * 0.6, danza)
    principal_magia = (
        (mt and not metafora)                      # «Espectacle de màgia …» en el título
        or bool(persona_a or persona_t)            # «a càrrec del Mag …», «Mago …»
        or (m_fuerte + m_persona >= 4 and m_fuerte + m_persona >= 1.3 * otros)
    )
    if principal_magia:
        if hipnosi and m_fuerte < 2:
            return decidir("magia", "hipnosis", "principal", 0.5,
                           "espectáculo de hipnosis: pendiente de decidir si cuenta como magia")
        conf = 0.95 if (mt or persona_a or persona_t) else (0.8 if m_fuerte >= 4 else 0.65)
        if mt:
            origen = "el título"
        elif persona_a:
            origen = "el artista, que se presenta como mago o maga"
        elif persona_t:
            origen = "el título, que nombra a un mago o maga"
        else:
            origen = "la descripción"
        return decidir("magia", None, "principal", conf, f"magia como disciplina principal (lo dice {origen})")
    if hipnosi:
        return decidir("magia", "hipnosis", "principal", 0.45,
                       "espectáculo de hipnosis: pendiente de decidir si cuenta como magia")

    if circo >= 3 and circo >= teatro * 0.7:
        tipo, motivo = "circo", "vocabulario de circo"
    else:
        tipo, motivo = "teatro", ("vocabulario de teatro" if teatro >= 2 else "espectáculo sin disciplina clara; se asume teatro")
    rel = relacion_magia(tipo)
    titulo_teatro = bool(re.match(r"^(teatre|teatro|monòleg|monólogo|circ|circo)\b", titulo.strip()))
    conf = 0.85 if (circo >= 3 or teatro >= 3 or titulo_teatro) else (0.65 if desc else 0.5)
    if rel == "incluye":
        motivo += "; incluye números de magia"
        conf = min(conf, 0.75)
    elif m_debil and not metafora and (debil_t or len(debil_d) >= 2):
        conf = min(conf, 0.6)
        motivo += "; menciona palabras ambiguas de magia"
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
