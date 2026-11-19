// Forma de la cartelera que prepara cada noche pipeline/exportar_web.py.
// Los campos que no se conocen no vienen (solo se muestra lo que se sabe).

export type Tipo = 'teatro' | 'magia' | 'circo' | 'eventos';

export interface Espectaculo {
  id: string;
  nombre: string;
  artista?: string;
  tipo: Tipo;
  subtipo?: string;
  tema_magia?: boolean;
  /** En el teatro: género de la obra (comedia, musical…), solo si es seguro. */
  generos?: string[];
  /** En los eventos: de qué es el taller, festival o charla (teatro, magia, circo, clown). */
  disciplina?: string;
  sala?: string;
  sala_interior?: string;
  sala_id?: string;
  barrio?: string;
  direccion?: string;
  lat?: number;
  lon?: number;
  funciones: [string, string?][];
  /** Lo pone la app: primera fecha de la obra aunque ya haya pasado (para «Últimos días»). */
  desde?: string;
  /** Si ya ha terminado: fecha de la última función (sale un mes con «Caducado»). */
  caducado?: string;
  precio_min?: number;
  precio_max?: number;
  gratis?: boolean;
  publico?: string;
  edad_min?: number;
  edad_max?: number;
  nivel?: string;
  duracion?: number;
  idiomas?: string[];
  descripcion?: Record<string, string>;
  idioma_textos?: string;
  compra?: string;
  /** «obra»: página o compra de esta obra en la web oficial; «sala»: solo la portada de la sala. */
  compra_tipo?: 'obra' | 'sala';
  /** Portada de la sala, cuando «compra» es la página de la obra. */
  compra_sala?: string;
  imagen?: string;
  fuente?: string;
  fuente_url?: string;
  comprobado?: string;
  /** Ficha artística tal como la da la fuente: [papel, personas]. */
  equipo?: [string, string][];
  /** Idioma al que la IA ha traducido la descripción. */
  traducido?: string;
  /** Premios que cita la descripción (con la cita literal). */
  premios?: { es: string; ca: string; cita: string; origen?: 'web' }[];
  /** Temas de la obra (IA, solo si la descripción los deja claros). */
  temas?: Record<string, string[]>;
  /** Magia: trayectoria y premios del artista, buscados por la IA con fuentes comprobadas. */
  artista_ficha?: { nombre: string; trayectoria?: Record<string, string>; premios: { premio: string; anio?: number | null; fuente: string }[]; fuentes: string[] };
}

export interface Ciudad {
  id: string;
  nombre: string;
  pais: string;
  zona_horaria: string;
  moneda: string;
  idiomas: string[];
}

/** Persona del equipo de las obras con ficha en Wikidata (solo coincidencias seguras). */
export interface PersonaEscena {
  wikidata: string;
  foto?: string;
  descripcion?: Record<string, string>;
  wikipedia?: string;
  premios?: { premio: string; anio?: number; tipo: 'ganado' | 'nominado' }[];
  fuente?: string;
}

export interface Cartelera {
  ciudad: Ciudad;
  actualizado: string;
  licencia: string;
  espectaculos: Espectaculo[];
  /** Lo que terminó en el último mes (pipeline/caducados.py). */
  caducados?: Espectaculo[];
  /** Clave: el nombre en minúsculas, sin acentos y con guiones (como pipeline/personas.py). */
  personas?: Record<string, PersonaEscena>;
}

export async function cargarCartelera(ciudad = 'barcelona'): Promise<Cartelera> {
  const r = await fetch(`./datos/${ciudad}.json`);
  if (!r.ok) throw new Error(`No se ha podido cargar la cartelera (${r.status})`);
  return r.json();
}

/** Ficha ampliada de una persona (pipeline/biografias.py): TMDB y Wikidata. Va en archivos aparte que
 * solo se descargan al abrir la ficha de una persona. */
export interface DatosPersona {
  tmdb?: number;
  nombre?: string;
  foto?: string;
  oficio?: string;
  nacimiento?: string;
  muerte?: string;
  lugar?: string;
  bio?: Record<string, string>;
  /** Trabajos más vistos: [título, año, «pelicula» | «serie», papel o personaje]. */
  conocida?: [string, number | null, 'pelicula' | 'serie', string][];
  wikidata?: string;
  descripcion?: Record<string, string>;
  wikipedia?: string;
}

/** En qué archivo está cada persona (la misma cuenta que pipeline/biografias.py: trozo()). */
export function trozoPersona(clave: string): number {
  let n = 0;
  for (let i = 0; i < clave.length; i++) n += clave.charCodeAt(i);
  return n % 16;
}

const trozos = new Map<string, Promise<Record<string, DatosPersona>>>();

export function cargarPersona(ciudad: string, claves: string[]): Promise<DatosPersona | undefined> {
  const pedir = (clave: string) => {
    const archivo = `./datos/${ciudad}-personas-${trozoPersona(clave)}.json`;
    if (!trozos.has(archivo)) {
      trozos.set(archivo, fetch(archivo).then((r) => (r.ok ? r.json() : { personas: {} }))
        .then((d) => d.personas || {}).catch(() => { trozos.delete(archivo); return {}; }));
    }
    return trozos.get(archivo)!.then((t) => t[clave]);
  };
  return Promise.all(claves.map(pedir)).then((xs) => xs.find(Boolean));
}
