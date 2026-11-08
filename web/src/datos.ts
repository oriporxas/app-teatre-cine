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
  imagen?: string;
  fuente?: string;
  fuente_url?: string;
  comprobado?: string;
  /** Ficha artística tal como la da la fuente: [papel, personas]. */
  equipo?: [string, string][];
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
