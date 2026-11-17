// Cartelera de cine: forma de los datos (web/public/datos/<ciudad>-cine.json) y búsqueda.
import { distancia, normaliza, rango, type ClaveFecha } from './filtros';

export interface Persona { id?: number; nombre: string; foto?: string; papel?: string; wikidata?: string; premios?: Premio[] }
export interface Premio { premio: string; anio?: number; tipo: 'ganado' | 'nominado' }

// [cine, fecha, hora, versión, sala, compra, especial]
// [cine, día, hora, versión, sala, enlace de compra, pase especial, 1 si el enlace es la compra de ESA sesión]
export type Sesion = [string, string, string | null, string | null, string | null, string | null, string | null, number?];

export interface Pelicula {
  id: string;
  titulo: string;
  titulo_ca?: string;
  titulo_original?: string;
  anio?: number;
  estreno?: string;
  duracion?: number;
  generos?: string[];
  sinopsis?: Record<string, string>;
  lema?: string;
  cartel?: string;
  fondo?: string;
  trailer?: string;
  edad?: string;
  nota?: number;
  paises?: string[];
  idioma_original?: string;
  direccion?: Persona[];
  guion?: Persona[];
  musica?: Persona[];
  reparto?: Persona[];
  premios?: Premio[];
  tmdb?: number;
  imdb?: string;
  agenda?: string;
  gratis?: boolean;
  sesiones: Sesion[];
}

export interface Cine {
  id: string;
  nombre: string;
  direccion?: string;
  barrio?: string;
  lat?: number;
  lon?: number;
  web?: string;
  ver_en?: string;
  centro?: boolean;
  fuente?: string;
}

export interface CarteleraCine {
  actualizado: string;
  atribucion: string;
  cines: Cine[];
  peliculas: Pelicula[];
}

export async function cargarCine(ciudad: string): Promise<CarteleraCine> {
  const r = await fetch(`./datos/${ciudad}-cine.json`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export const VERSIONES = ['VOSE', 'VOSC', 'VO', 'Català', 'Castellano'];

export interface FiltrosCine {
  fecha: ClaveFecha;
  desde: string;
  hasta: string;
  q: string;
  cine: string; // id o 'todos'
  version: string; // 'todas' o una de VERSIONES
  genero: string; // 'todos' o un género de TMDB
  soloCines: boolean; // sin las proyecciones de centros cívicos
  cerca: { lat: number; lon: number } | null;
  distanciaMax: number | null;
}

export const FILTROS_CINE: FiltrosCine = {
  fecha: 'hoy', desde: '', hasta: '', q: '', cine: 'todos', version: 'todas', genero: 'todos', soloCines: false,
  cerca: null, distanciaMax: null,
};

const TEXTO = new WeakMap<Pelicula, string>();
function textoBusqueda(p: Pelicula): string {
  let t = TEXTO.get(p);
  if (t == null) {
    t = normaliza([p.titulo, p.titulo_ca, p.titulo_original, ...(p.direccion || []).map((x) => x.nombre),
      ...(p.reparto || []).map((x) => x.nombre), ...(p.guion || []).map((x) => x.nombre), ...(p.generos || [])].join(' '));
    TEXTO.set(p, t);
  }
  return t;
}

/** Sesiones de la película que cumplen los filtros (fecha, cine, versión, distancia). */
export function sesionesQuePasan(p: Pelicula, f: FiltrosCine, hoy: string, cines: Map<string, Cine>, ahora?: string): Sesion[] {
  const [desde, hasta] = rango(f, hoy);
  return p.sesiones.filter((s) => {
    if (s[1] < desde || s[1] > hasta) return false;
    if (ahora && s[1] === hoy && s[2] && s[2] < ahora) return false; // ya empezó
    if (f.cine !== 'todos' && s[0] !== f.cine) return false;
    if (f.version !== 'todas' && s[3] !== f.version) return false;
    const c = cines.get(s[0]);
    if (f.soloCines && c?.centro) return false;
    if (f.distanciaMax != null && f.cerca) {
      if (c?.lat == null || c.lon == null || distancia(f.cerca, c.lat, c.lon) > f.distanciaMax * 1000) return false;
    }
    return true;
  });
}

export function filtrarPeliculas(lista: Pelicula[], f: FiltrosCine, hoy: string, cines: Map<string, Cine>, ahora?: string) {
  const q = normaliza(f.q.trim());
  return lista
    .filter((p) => (f.genero === 'todos' || (p.generos || []).includes(f.genero)) && (!q || textoBusqueda(p).includes(q)))
    .map((p) => ({ p, s: sesionesQuePasan(p, f, hoy, cines, ahora) }))
    .filter((x) => x.s.length > 0);
}

/** Estrenada en los últimos 10 días (según TMDB). */
export function esEstreno(p: Pelicula, hoy: string): boolean {
  if (!p.estreno) return false;
  const d = (Date.parse(`${hoy}T12:00:00Z`) - Date.parse(`${p.estreno}T12:00:00Z`)) / 86400000;
  return d >= 0 && d <= 10;
}

export function tituloPeli(p: Pelicula, lang: string): string {
  return (lang === 'ca' && p.titulo_ca) || p.titulo;
}

export function horaAhora(zona: string): string {
  return new Intl.DateTimeFormat('es-ES', { timeZone: zona, hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date());
}

export function minutosHasta(fecha: string, hora: string | null, hoy: string, ahora: string): number | null {
  if (!hora || fecha !== hoy) return null;
  const [h, m] = hora.split(':').map(Number);
  const [ah, am] = ahora.split(':').map(Number);
  return h * 60 + m - (ah * 60 + am);
}
