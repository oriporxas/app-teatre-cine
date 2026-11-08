// Textos de la app en castellano y catalán.
export type Idioma = 'es' | 'ca';

const PALABRAS_PAPELES: Record<string, string> = {
  'direcció': 'dirección', 'escènica': 'escénica', 'dramatúrgia': 'dramaturgia', 'autoria': 'autoría',
  'text': 'texto', 'guió': 'guion', 'intèrprets': 'intérpretes', 'intèrpret': 'intérprete',
  'interpretació': 'interpretación', 'repartiment': 'reparto', 'creació': 'creación', 'companyia': 'compañía',
  'adaptació': 'adaptación', 'traducció': 'traducción', 'composició': 'composición', 'espai': 'espacio',
  'sonor': 'sonoro', 'so': 'sonido', 'coreografia': 'coreografía', 'moviment': 'movimiento',
  'escenografia': 'escenografía', 'escènic': 'escénico', 'vestuari': 'vestuario', 'il·luminació': 'iluminación',
  'llums': 'luces', 'visuals': 'visuales', 'caracterització': 'caracterización', 'titellaires': 'titiriteros',
  'titelles': 'títeres', 'producció': 'producción', 'coproducció': 'coproducción', 'executiva': 'ejecutiva',
  'ajudant': 'ayudante', 'ajudanta': 'ayudante', 'ajudantia': 'ayudantía', 'i': 'y', 'disseny': 'diseño',
  'construcció': 'construcción', 'confecció': 'confección', 'regidoria': 'regiduría', 'tècnica': 'técnica',
  'tècnic': 'técnico', 'veus': 'voces', 'veu': 'voz', 'cant': 'canto', 'elements': 'elementos',
  'escenogràfics': 'escenográficos', 'seguiment': 'seguimiento', 'artístic': 'artístico',
  'assessorament': 'asesoramiento', 'original': 'original', 'música': 'música', 'musical': 'musical',
};

function traducirPapel(p: string): string {
  return p.split(' ').map((w) => {
    const d = w.match(/^d['’](.+)$/);
    return d ? `de ${PALABRAS_PAPELES[d[1]] ?? d[1]}` : (PALABRAS_PAPELES[w] ?? w);
  }).join(' ');
}

const mayuscula = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

const es = {
  cartelera: 'Cartelera', buscar: 'Obra, artista o sala', buscarLabel: 'Buscar',
  tiposLabel: 'Qué buscas', tipoMagia: 'Tipo de magia', tipoEvento: 'Tipo de evento', cuando: 'Cuándo',
  filtros: 'Más filtros', cerrar: 'Cerrar', borrar: 'Borrar', cargando: 'Cargando la cartelera…',
  error: 'No se ha podido cargar la cartelera. Comprueba la conexión.',
  vacio: 'No hay nada con estos filtros. Prueba con otra fecha o quita algún filtro.',
  actualizado: 'datos del', verMas: 'Ver más',
  volver: 'Volver a la cartelera', favoritoPronto: 'Guardar en favoritos (llega en la fase 4)',
  donde: 'Dónde', comoLlegar: 'Cómo llegar', funciones: 'Próximas funciones', sinFechas: 'Sin fechas concretas',
  precio: 'Precio', duracion: 'Duración', publico: 'Público', idioma: 'Idioma', nivel: 'Nivel',
  comprar: 'Comprar entradas', descripcion: 'De qué va', equipo: 'Equipo artístico',
  // Los papeles llegan en catalán («direcció», «intèrprets»): se traducen palabra a palabra.
  papel: (p: string) => mayuscula(traducirPapel(p)),
  textoOriginal: { ca: 'Texto original en catalán. Se traducirá al castellano cuando se active la IA.', es: '' } as Record<string, string>,
  magoTit: 'El mago, su trayectoria y sus premios',
  magoTxt: 'Llega en la fase 3: la ficha del artista con todos sus premios y reconocimientos, cada uno explicado y con su fuente.',
  fuente: 'Fuente', comprobado: 'comprobado el',
  navCartelera: 'Cartelera', navMapa: 'Mapa', navFavoritos: 'Favoritos', seccionesLabel: 'Secciones',
  mapaTit: 'Mapa de salas', mapaTxt: 'Llega en la fase 4: las salas cercanas en un mapa, con lo que hay hoy en cada una.',
  irCartelera: 'Ir a la cartelera', imagen: 'Cartel de', nivelTxt: (n: string) => `nivel ${n}`,
  favTit: 'Favoritos y alertas', favTxt: 'Llegan en la fase 4: guarda espectáculos y recibe avisos de estrenos, últimas funciones y plazos de convocatorias.',
  tipos: { todo: 'Espectáculos', teatro: 'Teatro', magia: 'Magia', circo: 'Circo', eventos: 'Eventos' } as Record<string, string>,
  subsMagia: { todas: 'Todas', 'magia de cerca': 'De cerca', 'magia general': 'General', mentalismo: 'Mentalismo', hipnosis: 'Hipnosis' } as Record<string, string>,
  subsEvento: { todos: 'Todos', festival: 'Festivales', formacion: 'Talleres y cursos', charla: 'Charlas', otros: 'Otros', magia: 'Sobre magia' } as Record<string, string>,
  eventos: { 'formación': 'Taller o curso', festival: 'Festival', 'conferencia o coloquio': 'Charla o coloquio', premios: 'Premios', 'ensayo abierto': 'Ensayo abierto', 'puertas abiertas': 'Puertas abiertas', estreno: 'Estreno', convocatoria: 'Convocatoria' } as Record<string, string>,
  fechas: { todo: 'Cualquier día', hoy: 'Hoy', manana: 'Mañana', finde: 'Fin de semana', semana: 'Próximos 7 días' } as Record<string, string>,
  grupoPrecio: 'Precio', precioMax: 'Precio máximo', indefinido: 'Indefinido',
  hasta: (n: number) => (n === 0 ? '0 € (solo gratis)' : `Hasta ${n} €`),
  sinPrecio: 'Mostrar también las que no indican precio',
  grupoPublico: 'Público', grupoIdioma: 'Idioma de la función',
  publicos: { cualquiera: 'Cualquiera', infantil: 'Infantil', familiar: 'Familiar', juvenil: 'Juvenil', adultos: 'Adultos' } as Record<string, string>,
  idiomas: { catalan: 'Catalán', castellano: 'Castellano', ingles: 'Inglés', cualquiera: 'Cualquiera' } as Record<string, string>,
  idiomasFicha: { catalan: 'Catalán', castellano: 'Castellano', ingles: 'Inglés', frances: 'Francés', italiano: 'Italiano', sin_texto: 'Sin texto' } as Record<string, string>,
  notaIdioma: 'Pocas actividades indican el idioma. La IA lo completará.',
  publicoEtiqueta: { infantil: 'infantil', familiar: 'familiar', juvenil: 'juvenil', 'juvenil y adultos': 'juvenil y adultos', adultos: 'adultos', 'todos los públicos': 'todos los públicos' } as Record<string, string>,
  edades: (a?: number, b?: number) => (a != null && b != null ? `${a}–${b} años` : a != null ? `desde ${a} años` : ''),
  niveles: { 'iniciación': 'iniciación', intermedio: 'intermedio', avanzado: 'avanzado' } as Record<string, string>,
  gratis: 'Gratis',
  resultados: (n: number) => (n === 1 ? '1 resultado' : `${n} resultados`),
  ver: (n: number) => (n === 1 ? 'Ver 1 resultado' : `Ver ${n} resultados`),
  mas: (n: number) => (n === 1 ? 'y 1 fecha más' : `y ${n} fechas más`),
  dias: ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'],
  meses: ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
};

export type Textos = typeof es;

const ca: Textos = {
  ...es,
  cartelera: 'Cartellera', buscar: 'Obra, artista o sala', buscarLabel: 'Cercar',
  tiposLabel: 'Què busques', tipoMagia: 'Tipus de màgia', tipoEvento: "Tipus d'esdeveniment", cuando: 'Quan',
  filtros: 'Més filtres', cerrar: 'Tancar', borrar: 'Esborrar', cargando: 'Carregant la cartellera…',
  error: "No s'ha pogut carregar la cartellera. Comprova la connexió.",
  vacio: 'No hi ha res amb aquests filtres. Prova una altra data o treu algun filtre.',
  actualizado: 'dades del', verMas: 'Veure més',
  volver: 'Tornar a la cartellera', favoritoPronto: 'Desar a preferits (arriba a la fase 4)',
  donde: 'On', comoLlegar: 'Com arribar-hi', funciones: 'Properes funcions', sinFechas: 'Sense dates concretes',
  precio: 'Preu', duracion: 'Durada', publico: 'Públic', idioma: 'Idioma', nivel: 'Nivell',
  comprar: 'Comprar entrades', descripcion: 'De què va', equipo: 'Equip artístic',
  papel: (p: string) => mayuscula(p),
  textoOriginal: { ca: '', es: 'Text original en castellà.' },
  magoTit: 'El mag, la seva trajectòria i els seus premis',
  magoTxt: "Arriba a la fase 3: la fitxa de l'artista amb tots els seus premis i reconeixements, cadascun explicat i amb la seva font.",
  fuente: 'Font', comprobado: 'comprovat el',
  navCartelera: 'Cartellera', navMapa: 'Mapa', navFavoritos: 'Preferits', seccionesLabel: 'Seccions',
  mapaTit: 'Mapa de sales', mapaTxt: 'Arriba a la fase 4: les sales properes en un mapa, amb el que hi ha avui a cadascuna.',
  irCartelera: 'Anar a la cartellera', imagen: 'Cartell de', nivelTxt: (n: string) => `nivell ${n}`,
  favTit: 'Preferits i alertes', favTxt: "Arriben a la fase 4: desa espectacles i rep avisos d'estrenes, últimes funcions i terminis de convocatòries.",
  tipos: { todo: 'Espectacles', teatro: 'Teatre', magia: 'Màgia', circo: 'Circ', eventos: 'Esdeveniments' },
  subsMagia: { todas: 'Totes', 'magia de cerca': 'De prop', 'magia general': 'General', mentalismo: 'Mentalisme', hipnosis: 'Hipnosi' },
  subsEvento: { todos: 'Tots', festival: 'Festivals', formacion: 'Tallers i cursos', charla: 'Xerrades', otros: 'Altres', magia: 'Sobre màgia' },
  eventos: { 'formación': 'Taller o curs', festival: 'Festival', 'conferencia o coloquio': 'Xerrada o col·loqui', premios: 'Premis', 'ensayo abierto': 'Assaig obert', 'puertas abiertas': 'Portes obertes', estreno: 'Estrena', convocatoria: 'Convocatòria' },
  fechas: { todo: 'Qualsevol dia', hoy: 'Avui', manana: 'Demà', finde: 'Cap de setmana', semana: 'Propers 7 dies' },
  grupoPrecio: 'Preu', precioMax: 'Preu màxim', indefinido: 'Indefinit',
  hasta: (n: number) => (n === 0 ? '0 € (només gratuït)' : `Fins a ${n} €`),
  sinPrecio: 'Mostrar també les que no indiquen preu',
  grupoPublico: 'Públic', grupoIdioma: 'Idioma de la funció',
  publicos: { cualquiera: 'Qualsevol', infantil: 'Infantil', familiar: 'Familiar', juvenil: 'Juvenil', adultos: 'Adults' },
  idiomas: { catalan: 'Català', castellano: 'Castellà', ingles: 'Anglès', cualquiera: 'Qualsevol' },
  idiomasFicha: { catalan: 'Català', castellano: 'Castellà', ingles: 'Anglès', frances: 'Francès', italiano: 'Italià', sin_texto: 'Sense text' },
  notaIdioma: "Poques activitats indiquen l'idioma. La IA el completarà.",
  publicoEtiqueta: { infantil: 'infantil', familiar: 'familiar', juvenil: 'juvenil', 'juvenil y adultos': 'juvenil i adults', adultos: 'adults', 'todos los públicos': 'tots els públics' },
  edades: (a?: number, b?: number) => (a != null && b != null ? `${a}–${b} anys` : a != null ? `des de ${a} anys` : ''),
  niveles: { 'iniciación': 'iniciació', intermedio: 'intermedi', avanzado: 'avançat' },
  gratis: 'Gratuït',
  resultados: (n: number) => (n === 1 ? '1 resultat' : `${n} resultats`),
  ver: (n: number) => (n === 1 ? 'Veure 1 resultat' : `Veure ${n} resultats`),
  mas: (n: number) => (n === 1 ? 'i 1 data més' : `i ${n} dates més`),
  dias: ['dg', 'dl', 'dt', 'dc', 'dj', 'dv', 'ds'],
  meses: ['gen', 'febr', 'març', 'abr', 'maig', 'juny', 'jul', 'ag', 'set', 'oct', 'nov', 'des'],
};

export const TEXTOS: Record<Idioma, Textos> = { es, ca };

export function idiomaInicial(): Idioma {
  try {
    const guardado = localStorage.getItem('idioma');
    if (guardado === 'es' || guardado === 'ca') return guardado;
  } catch { /* sin almacenamiento: seguimos */ }
  return (navigator.language || '').toLowerCase().startsWith('ca') ? 'ca' : 'es';
}

export function guardarIdioma(i: Idioma) {
  try { localStorage.setItem('idioma', i); } catch { /* da igual */ }
}
