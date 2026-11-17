// Planes (itinerarios): qué funciones quieres ver, qué día y dónde (Uri, 9/11/2026).
// Sirven para preparar un fin de semana o unas vacaciones en otra ciudad. Se guardan en el
// propio móvil (sin cuenta, como los favoritos) y cada función guarda lo necesario para verse
// aunque el espectáculo salga de cartel o sea de otra ciudad: nombre, sala, dirección, ciudad
// y zona horaria.
import { useCallback, useState } from 'react';
import type { Espectaculo } from './datos';

export interface ItemPlan {
  id: string; // del espectáculo
  dia: string; // AAAA-MM-DD
  hora?: string; // HH:MM
  nombre: string;
  sala?: string;
  direccion?: string;
  barrio?: string;
  lat?: number;
  lon?: number;
  duracion?: number; // minutos
  ciudad: string;
  zona: string; // zona horaria de la ciudad, p. ej. Europe/Madrid
}

export interface Plan {
  id: string;
  nombre: string;
  creado: string;
  items: ItemPlan[];
}

const CLAVE = 'planes';

export const claveItem = (i: Pick<ItemPlan, 'id' | 'dia' | 'hora'>) => `${i.id}|${i.dia}|${i.hora || ''}`;

function leer(): Plan[] {
  try {
    const v = JSON.parse(localStorage.getItem(CLAVE) || '[]');
    return Array.isArray(v) ? v.filter((p) => p && typeof p.id === 'string' && Array.isArray(p.items)) : [];
  } catch {
    return [];
  }
}

function guardar(planes: Plan[]) {
  try { localStorage.setItem(CLAVE, JSON.stringify(planes)); } catch { /* sin almacenamiento: dura hasta cerrar */ }
}

export function itemDe(e: Espectaculo, dia: string, hora: string | undefined, ciudad: string, zona: string): ItemPlan {
  return {
    id: e.id, dia, hora, nombre: e.nombre, sala: e.sala, direccion: e.direccion, barrio: e.barrio,
    lat: e.lat, lon: e.lon, duracion: e.duracion, ciudad, zona,
  };
}

const ordenar = (items: ItemPlan[]) =>
  [...items].sort((a, b) => (a.dia + (a.hora || '99')).localeCompare(b.dia + (b.hora || '99')));

export function usePlanes() {
  const [planes, setPlanes] = useState<Plan[]>(leer);
  const cambiar = useCallback((f: (actual: Plan[]) => Plan[]) => {
    setPlanes((actual) => { const nuevo = f(actual); guardar(nuevo); return nuevo; });
  }, []);

  const crear = useCallback((nombre: string, item?: ItemPlan): string => {
    const id = `p${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
    cambiar((a) => [{ id, nombre, creado: new Date().toISOString().slice(0, 10), items: item ? [item] : [] }, ...a]);
    return id;
  }, [cambiar]);

  const anadir = useCallback((planId: string, item: ItemPlan) => {
    cambiar((a) => a.map((p) => (p.id !== planId || p.items.some((i) => claveItem(i) === claveItem(item))
      ? p : { ...p, items: ordenar([...p.items, item]) })));
  }, [cambiar]);

  const quitar = useCallback((planId: string, clave: string) => {
    cambiar((a) => a.map((p) => (p.id === planId ? { ...p, items: p.items.filter((i) => claveItem(i) !== clave) } : p)));
  }, [cambiar]);

  const renombrar = useCallback((planId: string, nombre: string) => {
    cambiar((a) => a.map((p) => (p.id === planId ? { ...p, nombre } : p)));
  }, [cambiar]);

  const borrar = useCallback((planId: string) => { cambiar((a) => a.filter((p) => p.id !== planId)); }, [cambiar]);

  /** El plan que ya tiene esta función, si alguno la tiene. */
  const conFuncion = (id: string, dia: string, hora?: string) =>
    planes.find((p) => p.items.some((i) => claveItem(i) === claveItem({ id, dia, hora })));

  return { planes, crear, anadir, quitar, renombrar, borrar, conFuncion };
}

export type Planes = ReturnType<typeof usePlanes>;

// --- Utilidades -------------------------------------------------------------------

const minutos = (hora: string) => { const [h, m] = hora.split(':').map(Number); return h * 60 + (m || 0); };
export const DURACION_SUPUESTA = 90; // minutos, cuando la ficha no dice la duración

/** Funciones del plan que coinciden en el tiempo: {clave: nombre de la otra}. */
export function solapes(items: ItemPlan[]): Map<string, string> {
  const res = new Map<string, string>();
  const conHora = ordenar(items).filter((i) => i.hora);
  for (let k = 1; k < conHora.length; k++) {
    const a = conHora[k - 1], b = conHora[k];
    if (a.dia !== b.dia) continue;
    if (minutos(b.hora as string) < minutos(a.hora as string) + (a.duracion || DURACION_SUPUESTA)) {
      res.set(claveItem(a), b.nombre);
      res.set(claveItem(b), a.nombre);
    }
  }
  return res;
}

export function porDias(items: ItemPlan[]): [string, ItemPlan[]][] {
  const dias = new Map<string, ItemPlan[]>();
  for (const i of ordenar(items)) dias.set(i.dia, [...(dias.get(i.dia) || []), i]);
  return [...dias.entries()];
}

/** Ruta del día en el mapa (de sala en sala, en el orden de las funciones). */
export function enlaceRuta(items: ItemPlan[]): string | null {
  const puntos = items.filter((i) => i.lat != null && i.lon != null).map((i) => `${i.lat},${i.lon}`);
  const unicos = puntos.filter((p, k) => p !== puntos[k - 1]);
  if (unicos.length < 2) return null;
  return `https://www.google.com/maps/dir/${unicos.join('/')}`;
}

/** Hora local de una ciudad → instante UTC (tiene en cuenta el horario de verano). */
export function aUtc(dia: string, hora: string, zona: string): Date {
  const [a, m, d] = dia.split('-').map(Number);
  const [h, mi] = hora.split(':').map(Number);
  const supuesto = Date.UTC(a, m - 1, d, h, mi);
  const desfase = (t: number) => {
    const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
      timeZone: zona, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
    }).formatToParts(new Date(t)).map((x) => [x.type, x.value]));
    return Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute) - t;
  };
  let t = supuesto - desfase(supuesto);
  t = supuesto - desfase(t);
  return new Date(t);
}

const icsFecha = (d: Date) => d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
const icsTexto = (s: string) => s.replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/([,;])/g, '\\$1');

/** El plan como archivo de calendario (.ics): se abre con el calendario del móvil. */
export function planIcs(plan: Plan, enlace: (i: ItemPlan) => string): string {
  const ahora = icsFecha(new Date());
  const eventos = plan.items.map((i) => {
    const lugar = [i.sala, i.direccion, i.barrio].filter(Boolean).join(', ');
    let cuando: string[];
    if (i.hora) {
      const inicio = aUtc(i.dia, i.hora, i.zona);
      const fin = new Date(inicio.getTime() + (i.duracion || DURACION_SUPUESTA) * 60000);
      cuando = [`DTSTART:${icsFecha(inicio)}`, `DTEND:${icsFecha(fin)}`];
    } else {
      const siguiente = new Date(`${i.dia}T12:00:00Z`);
      siguiente.setUTCDate(siguiente.getUTCDate() + 1);
      cuando = [`DTSTART;VALUE=DATE:${i.dia.replace(/-/g, '')}`, `DTEND;VALUE=DATE:${siguiente.toISOString().slice(0, 10).replace(/-/g, '')}`];
    }
    return [
      'BEGIN:VEVENT', `UID:${claveItem(i).replace(/[^A-Za-z0-9]+/g, '-')}@cartelera`, `DTSTAMP:${ahora}`, ...cuando,
      `SUMMARY:${icsTexto(i.nombre)}`, lugar ? `LOCATION:${icsTexto(lugar)}` : '', `URL:${enlace(i)}`, 'END:VEVENT',
    ].filter(Boolean).join('\r\n');
  });
  return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Cartelera//Planes//ES', 'CALSCALE:GREGORIAN',
    `X-WR-CALNAME:${icsTexto(plan.nombre)}`, ...eventos, 'END:VCALENDAR', ''].join('\r\n');
}

export function descargar(nombre: string, contenido: string, tipo: string) {
  const url = URL.createObjectURL(new Blob([contenido], { type: tipo }));
  const a = document.createElement('a');
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

/** Imagen vertical (1080×1920) del plan para compartir en historias de Instagram, WhatsApp…
 *  Se dibuja en el propio móvil: no se envía nada a ningún servidor. */
export async function imagenPlan(plan: Plan, fmtDia: (d: string) => string, pie: string): Promise<Blob | null> {
  const W = 1080, H = 1920, M = 90;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const g = c.getContext('2d');
  if (!g) return null;
  try { await document.fonts?.ready; } catch { /* sin fuentes web: se usan las del sistema */ }
  const serif = "'Playfair Display', Georgia, serif";
  const sans = "Inter, system-ui, sans-serif";
  g.fillStyle = '#0A0A0B'; g.fillRect(0, 0, W, H);
  // telón rojo arriba
  const grad = g.createLinearGradient(0, 0, 0, 420);
  grad.addColorStop(0, 'rgba(209,31,53,0.55)'); grad.addColorStop(1, 'rgba(209,31,53,0)');
  g.fillStyle = grad; g.fillRect(0, 0, W, 420);
  g.fillStyle = '#D11F35'; g.fillRect(0, 0, W, 14);
  g.fillStyle = '#FAF8F5';
  g.font = `italic 700 44px ${serif}`; g.fillText('Cartelera Barcelona', M, 140);
  // título del plan (hasta dos líneas)
  g.font = `900 92px ${serif}`;
  const palabras = plan.nombre.split(' ');
  let linea = '', y = 290;
  const lineas: string[] = [];
  for (const p of palabras) {
    const prueba = linea ? `${linea} ${p}` : p;
    if (g.measureText(prueba).width > W - 2 * M && linea) { lineas.push(linea); linea = p; } else linea = prueba;
  }
  lineas.push(linea);
  for (const l of lineas.slice(0, 2)) { g.fillText(l, M, y); y += 104; }
  y += 30;
  const recorta = (s: string, ancho: number) => {
    if (g.measureText(s).width <= ancho) return s;
    while (s.length > 3 && g.measureText(`${s}…`).width > ancho) s = s.slice(0, -1);
    return `${s}…`;
  };
  for (const [dia, items] of porDias(plan.items)) {
    if (y > H - 260) break;
    g.fillStyle = '#FF5A6E'; g.font = `800 34px ${sans}`;
    g.fillText(fmtDia(dia).toUpperCase(), M, y); y += 24;
    for (const i of items) {
      if (y > H - 260) break;
      // entrada blanca con la hora
      g.fillStyle = '#FAF8F5';
      g.beginPath(); g.roundRect(M, y, W - 2 * M, 150, 18); g.fill();
      g.fillStyle = '#D11F35'; g.font = `900 56px ${serif}`;
      g.fillText(i.hora || '—', M + 34, y + 92);
      g.fillStyle = '#0A0A0B'; g.font = `800 40px ${sans}`;
      g.fillText(recorta(i.nombre, W - 2 * M - 260), M + 220, y + 68);
      g.fillStyle = '#4A4744'; g.font = `500 30px ${sans}`;
      g.fillText(recorta(i.sala || '', W - 2 * M - 260), M + 220, y + 114);
      y += 176;
    }
    y += 36;
  }
  g.fillStyle = '#ABA7A1'; g.font = `500 30px ${sans}`;
  g.fillText(pie, M, H - 110);
  g.fillStyle = '#D11F35'; g.fillRect(M, H - 80, 120, 6);
  return new Promise((r) => c.toBlob((b) => r(b), 'image/png'));
}
