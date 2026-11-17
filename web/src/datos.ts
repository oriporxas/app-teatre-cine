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
  premios?: { es: string; ca: string; cita: string }[];
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

export interface Cartelera {
  ciudad: Ciudad;
  actualizado: string;
  licencia: string;
  espectaculos: Espectaculo[];
}

export async function cargarCartelera(ciudad = 'barcelona'): Promise<Cartelera> {
  const r = await fetch(`./datos/${ciudad}.json`);
  if (!r.ok) throw new Error(`No se ha podido cargar la cartelera (${r.status})`);
  return r.json();
}
