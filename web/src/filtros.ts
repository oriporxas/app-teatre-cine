// Lógica de búsqueda y filtros. Decisiones de Uri (brief, 8/11/2026):
// - Las funciones (teatro, magia, circo) y los eventos no se mezclan.
// - Precio: deslizable de 0 a 150 € y, al final, «Indefinido»; casilla para incluir las que no indican precio.
// - Idioma: catalán, castellano, inglés o cualquiera.
import type { Espectaculo, Tipo } from './datos';
import type { Textos } from './textos';

export const FUNCIONES: Tipo[] = ['teatro', 'magia', 'circo'];
export const PRECIO_TOPE = 155; // última posición del deslizable, después de 150 €: «Indefinido»

export type ClaveFecha = 'todo' | 'hoy' | 'manana' | 'finde' | 'semana';

export interface Filtros {
  tipo: 'todo' | Tipo;
  subMagia: string;
  subEvento: string;
  fecha: ClaveFecha;
  q: string;
  precioMax: number | null;
  sinPrecio: boolean;
  publico: string;
  idioma: string;
}

export const FILTROS_INICIALES: Filtros = {
  tipo: 'todo', subMagia: 'todas', subEvento: 'todos', fecha: 'todo', q: '',
  precioMax: null, sinPrecio: false, publico: 'cualquiera', idioma: 'cualquiera',
};

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

export function rango(clave: ClaveFecha, hoy: string): [string, string] {
  if (clave === 'hoy') return [hoy, hoy];
  if (clave === 'manana') { const m = sumaDias(hoy, 1); return [m, m]; }
  if (clave === 'semana') return [hoy, sumaDias(hoy, 6)];
  if (clave === 'finde') {
    const d = diaSemana(hoy);
    if (d === 5) return [hoy, sumaDias(hoy, 2)];
    if (d === 6) return [hoy, sumaDias(hoy, 1)];
    if (d === 0) return [hoy, hoy];
    const viernes = sumaDias(hoy, 5 - d);
    return [viernes, sumaDias(viernes, 2)];
  }
  return [hoy, '9999-12-31'];
}

export function normaliza(s?: string): string {
  return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

export function grupoEvento(e: Espectaculo): string {
  if (e.subtipo === 'festival') return 'festival';
  if (e.subtipo === 'formación') return 'formacion';
  if (e.subtipo === 'conferencia o coloquio') return 'charla';
  return 'otros';
}

export function funcionesEnRango(e: Espectaculo, desde: string, hasta: string) {
  return e.funciones.filter(([f]) => f >= desde && f <= hasta);
}

export type Ignorar = 'tipo' | 'sub' | null;

export function pasa(e: Espectaculo, f: Filtros, hoy: string, ignorar: Ignorar = null): boolean {
  if (ignorar !== 'tipo') {
    if (f.tipo === 'todo' ? !FUNCIONES.includes(e.tipo) : e.tipo !== f.tipo) return false;
    if (ignorar !== 'sub' && f.tipo === 'magia' && f.subMagia !== 'todas' && (e.subtipo || 'magia general') !== f.subMagia) return false;
    if (ignorar !== 'sub' && f.tipo === 'eventos' && f.subEvento !== 'todos') {
      if (f.subEvento === 'magia' ? !e.tema_magia : grupoEvento(e) !== f.subEvento) return false;
    }
  }
  const [desde, hasta] = rango(f.fecha, hoy);
  if (funcionesEnRango(e, desde, hasta).length === 0) return false;
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
  const [desde, hasta] = rango(f.fecha, hoy);
  const clave = (e: Espectaculo) => { const [d, h] = funcionesEnRango(e, desde, hasta)[0]; return d + (h || ''); };
  return lista.filter((e) => pasa(e, f, hoy)).sort((a, b) => clave(a).localeCompare(clave(b)));
}

export function cuantosFiltros(f: Filtros): number {
  return (f.precioMax != null ? 1 : 0) + (f.publico !== 'cualquiera' ? 1 : 0) + (f.idioma !== 'cualquiera' ? 1 : 0);
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
  if (e.tipo === 'eventos') return t.eventos[e.subtipo || ''] || t.tipos.eventos;
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
