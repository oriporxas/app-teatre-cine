// Lógica de búsqueda y filtros. Decisiones de Uri (brief, 8/11/2026):
// - Las funciones (teatro, magia, circo) y los eventos no se mezclan.
// - Precio: deslizable de 0 a 150 € y, al final, «Indefinido»; casilla para incluir las que no indican precio.
// - Idioma: catalán, castellano, inglés o cualquiera.
import type { Espectaculo, Tipo } from './datos';
import type { Textos } from './textos';

export const FUNCIONES: Tipo[] = ['teatro', 'magia', 'circo'];
export const PRECIO_TOPE = 155; // última posición del deslizable, después de 150 €: «Indefinido»

export type ClaveFecha = 'todo' | 'hoy' | 'manana' | 'semana' | 'mes' | 'rango';
// El calendario llega hasta dos años vista (obras en gira y temporadas largas).
export const MESES_CALENDARIO = 24;

export interface Filtros {
  tipo: 'todo' | Tipo;
  subMagia: string;
  subEvento: string;
  fecha: ClaveFecha;
  desde: string; // solo con fecha «rango» (calendario)
  hasta: string;
  q: string;
  precioMax: number | null;
  sinPrecio: boolean;
  publico: string;
  idioma: string;
  // Ubicación (solo en el móvil: la app no la envía a ningún sitio)
  cerca: { lat: number; lon: number } | null;
  orden: 'fecha' | 'cerca';
  distanciaMax: number | null; // km
}

export const FILTROS_INICIALES: Filtros = {
  tipo: 'todo', subMagia: 'todas', subEvento: 'todos', fecha: 'todo', desde: '', hasta: '', q: '',
  precioMax: null, sinPrecio: false, publico: 'cualquiera', idioma: 'cualquiera',
  cerca: null, orden: 'fecha', distanciaMax: null,
};

/** Distancia en metros entre dos puntos (fórmula del haversine). */
export function distancia(a: { lat: number; lon: number }, lat: number, lon: number): number {
  const r = Math.PI / 180;
  const dLat = (lat - a.lat) * r, dLon = (lon - a.lon) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(lat * r) * Math.sin(dLon / 2) ** 2;
  return 2 * 6371000 * Math.asin(Math.sqrt(h));
}

export function distanciaA(e: Espectaculo, f: Pick<Filtros, 'cerca'>): number | null {
  return f.cerca && e.lat != null && e.lon != null ? distancia(f.cerca, e.lat, e.lon) : null;
}

export function fmtDistancia(m: number): string {
  return m < 1000 ? `${Math.max(50, Math.round(m / 50) * 50)} m` : `${(m / 1000).toFixed(1).replace('.', ',')} km`;
}

const PUBLICO_ENCAJA: Record<string, string[]> = {
  infantil: ['infantil'],
  familiar: ['familiar', 'todos los públicos'],
  juvenil: ['juvenil', 'juvenil y adultos'],
  adultos: ['adultos', 'juvenil y adultos'],
};

export function hoyEn(zona: string): string {
  // en-CA da la fecha como AAAA-MM-DD
  return new Intl.DateTimeFormat('en-CA', { timeZone: zona, year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
}

export function sumaDias(iso: string, n: number): string {
  const d = new Date(`${iso}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

function diaSemana(iso: string): number {
  return new Date(`${iso}T12:00:00Z`).getUTCDay();
}

export function finDeMes(iso: string): string {
  const d = new Date(`${iso}T12:00:00Z`);
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0, 12)).toISOString().slice(0, 10);
}

type ConFechas = Pick<Filtros, 'fecha' | 'desde' | 'hasta'>;

export function rango(f: ConFechas, hoy: string): [string, string] {
  if (f.fecha === 'hoy') return [hoy, hoy];
  if (f.fecha === 'manana') { const m = sumaDias(hoy, 1); return [m, m]; }
  // Esta semana: de hoy al domingo (la semana empieza el lunes).
  if (f.fecha === 'semana') return [hoy, sumaDias(hoy, (7 - diaSemana(hoy)) % 7)];
  if (f.fecha === 'mes') return [hoy, finDeMes(hoy)];
  if (f.fecha === 'rango' && f.desde) return [f.desde < hoy ? hoy : f.desde, f.hasta || f.desde];
  return [hoy, '9999-12-31'];
}

export function normaliza(s?: string): string {
  return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

// Tipos de evento, en el orden en que se muestran.
export const TIPOS_EVENTO = ['festival', 'formación', 'conferencia o coloquio', 'ensayo abierto', 'puertas abiertas',
  'estreno', 'convocatoria', 'premios'];

export function funcionesEnRango(e: Espectaculo, desde: string, hasta: string) {
  return e.funciones.filter(([f]) => f >= desde && f <= hasta);
}

export type Ignorar = 'tipo' | 'sub' | 'fecha' | null;

export function pasa(e: Espectaculo, f: Filtros, hoy: string, ignorar: Ignorar = null): boolean {
  if (ignorar !== 'tipo') {
    if (f.tipo === 'todo' ? !FUNCIONES.includes(e.tipo) : e.tipo !== f.tipo) return false;
    if (ignorar !== 'sub' && f.tipo === 'magia' && f.subMagia !== 'todas' && (e.subtipo || 'magia general') !== f.subMagia) return false;
    if (ignorar !== 'sub' && f.tipo === 'eventos' && f.subEvento !== 'todos' && e.subtipo !== f.subEvento) return false;
  }
  if (ignorar === 'fecha') return pasaResto(e, f);
  const [desde, hasta] = rango(f, hoy);
  if (funcionesEnRango(e, desde, hasta).length === 0) return false;
  return pasaResto(e, f);
}

function pasaResto(e: Espectaculo, f: Filtros): boolean {
  if (f.distanciaMax != null && f.cerca) {
    const d = distanciaA(e, f);
    if (d == null || d > f.distanciaMax * 1000) return false;
  }
  if (f.precioMax != null) {
    const sinPrecio = !e.gratis && e.precio_min == null;
    if (sinPrecio ? !f.sinPrecio : !(e.gratis || (e.precio_min as number) <= f.precioMax)) return false;
  }
  if (f.publico !== 'cualquiera' && !PUBLICO_ENCAJA[f.publico].includes(e.publico || '')) return false;
  if (f.idioma !== 'cualquiera' && !(e.idiomas || []).includes(f.idioma)) return false;
  const q = normaliza(f.q.trim());
  if (q && !textoBusqueda(e).includes(q)) return false;
  return true;
}

// El texto en el que se busca se prepara una sola vez por actividad.
const TEXTOS_BUSQUEDA = new WeakMap<Espectaculo, string>();
function textoBusqueda(e: Espectaculo): string {
  let texto = TEXTOS_BUSQUEDA.get(e);
  if (texto == null) {
    texto = normaliza([e.nombre, e.artista, e.sala, e.sala_interior, e.barrio, ...Object.values(e.descripcion || {})].join(' '));
    TEXTOS_BUSQUEDA.set(e, texto);
  }
  return texto;
}

export function filtrar(lista: Espectaculo[], f: Filtros, hoy: string): Espectaculo[] {
  const [desde, hasta] = rango(f, hoy);
  const clave = (e: Espectaculo) => { const [d, h] = funcionesEnRango(e, desde, hasta)[0]; return d + (h || ''); };
  const salida = lista.filter((e) => pasa(e, f, hoy)).sort((a, b) => clave(a).localeCompare(clave(b)));
  if (f.orden === 'cerca' && f.cerca) {
    const d = (e: Espectaculo) => distanciaA(e, f) ?? Number.MAX_VALUE;
    salida.sort((a, b) => d(a) - d(b) || clave(a).localeCompare(clave(b)));
  }
  return salida;
}

export function fmtRango(f: ConFechas, t: Textos): string {
  if (!f.desde) return t.fechas.rango;
  if (!f.hasta || f.hasta === f.desde) return fmtCorto(f.desde, t);
  return `${fmtCorto(f.desde, t)} – ${fmtCorto(f.hasta, t)}`;
}

export function fmtCorto(iso: string, t: Textos): string {
  const d = new Date(`${iso}T12:00:00Z`);
  return `${d.getUTCDate()} ${t.meses[d.getUTCMonth()]}`;
}

export function cuantosFiltros(f: Filtros): number {
  return (f.precioMax != null ? 1 : 0) + (f.publico !== 'cualquiera' ? 1 : 0) + (f.idioma !== 'cualquiera' ? 1 : 0)
    + (f.distanciaMax != null && f.cerca ? 1 : 0);
}

// --- Presentación -----------------------------------------------------------

export function fmtDia(iso: string, t: Textos): string {
  const d = new Date(`${iso}T12:00:00Z`);
  return `${t.dias[d.getUTCDay()]} ${d.getUTCDate()} ${t.meses[d.getUTCMonth()]}`;
}

function euros(n: number): string {
  return Number.isInteger(n) ? String(n) : n.toFixed(2).replace('.', ',');
}

export function precioTxt(e: Espectaculo, t: Textos): string {
  if (e.gratis) return t.gratis;
  if (e.precio_min == null) return '';
  const max = e.precio_max ?? e.precio_min;
  return e.precio_min === max ? `${euros(e.precio_min)} €` : `${euros(e.precio_min)}–${euros(max)} €`;
}

export function tipoTxt(e: Espectaculo, t: Textos): string {
  if (e.tipo === 'magia') return `${t.tipos.magia} · ${t.subsMagia[e.subtipo || 'magia general'] || t.subsMagia['magia general']}`;
  if (e.tipo === 'eventos') {
    const base = t.eventos[e.subtipo || ''] || t.tipos.eventos;
    const disciplina = e.disciplina ? t.disciplinas[e.disciplina] : '';
    return disciplina ? `${base} · ${disciplina}` : base;
  }
  if (e.tipo === 'teatro' && e.subtipo === 'clown') return `${t.tipos.teatro} · ${t.disciplinas.clown}`;
  return t.tipos[e.tipo];
}

export function duracionTxt(min?: number): string {
  if (!min) return '';
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60), m = min % 60;
  return m ? `${h} h ${m} min` : `${h} h`;
}

export function publicoTxt(e: Espectaculo, t: Textos): string {
  if (!e.publico) return '';
  const edades = t.edades(e.edad_min, e.edad_max);
  return (t.publicoEtiqueta[e.publico] || e.publico) + (edades ? ` (${edades})` : '');
}
