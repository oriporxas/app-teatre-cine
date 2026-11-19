// «Visto» y «Hecho» (Uri, 19/11/2026): tachar lo que ya has visto o hecho —películas, obras,
// espectáculos, eventos y planes enteros— y guardarlo en un historial. Como los favoritos y los
// planes, se guarda en el propio móvil (sin cuenta) y nunca sale de él.
import { useCallback, useState } from 'react';
import type { Tipo } from './datos';
import type { Textos } from './textos';

/** Qué es cada cosa marcada: decide la palabra («Vista», «Visto», «Hecho») y el filtro del historial. */
export type Clase = 'peli' | Tipo | 'plan';

export interface Hecho {
  clave: string; // o:<id obra> · p:<id película> · plan:<id plan>
  clase: Clase;
  nombre: string;
  detalle?: string; // sala, cine o resumen del plan
  enlace: string; // dónde se abre (la ficha o el plan)
  fecha: string; // AAAA-MM-DD, el día que se marcó
}

const CLAVE = 'historial';

export const claveObra = (id: string) => `o:${id}`;
export const clavePeli = (id: string) => `p:${id}`;
export const clavePlan = (id: string) => `plan:${id}`;

function leer(): Hecho[] {
  try {
    const v = JSON.parse(localStorage.getItem(CLAVE) || '[]');
    return Array.isArray(v) ? v.filter((h) => h && typeof h.clave === 'string' && typeof h.nombre === 'string') : [];
  } catch {
    return [];
  }
}

function hoyLocal(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function useHistorial() {
  const [lista, setLista] = useState<Hecho[]>(leer);
  const cambiar = useCallback((f: (a: Hecho[]) => Hecho[]) => {
    setLista((actual) => {
      const nuevo = f(actual);
      try { localStorage.setItem(CLAVE, JSON.stringify(nuevo)); } catch { /* sin almacenamiento: dura hasta cerrar */ }
      return nuevo;
    });
  }, []);
  /** Marca o desmarca (si ya estaba marcado, se quita del historial). */
  const alternar = useCallback((h: Omit<Hecho, 'fecha'>) => {
    cambiar((a) => (a.some((x) => x.clave === h.clave)
      ? a.filter((x) => x.clave !== h.clave)
      : [{ ...h, fecha: hoyLocal() }, ...a]));
  }, [cambiar]);
  const quitar = useCallback((clave: string) => cambiar((a) => a.filter((x) => x.clave !== clave)), [cambiar]);
  const ordenada = [...lista].sort((a, b) => b.fecha.localeCompare(a.fecha));
  return {
    lista: ordenada,
    es: (clave: string) => lista.some((x) => x.clave === clave),
    de: (clave: string) => lista.find((x) => x.clave === clave),
    alternar,
    quitar,
  };
}

export type Historial = ReturnType<typeof useHistorial>;

/** La palabra de cada cosa: las películas y las obras se ven («Vista»), los espectáculos de magia
 * y circo también («Visto»), y los eventos (talleres, festivales, charlas) y los planes se hacen. */
export function marca(clase: Clase, t: Textos): { hecho: string; marcar: string } {
  if (clase === 'peli' || clase === 'teatro') return { hecho: t.vistaF, marcar: t.marcarVistaF };
  if (clase === 'magia' || clase === 'circo') return { hecho: t.vistoM, marcar: t.marcarVistoM };
  if (clase === 'plan') return { hecho: t.hecho, marcar: t.marcarPlanHecho };
  return { hecho: t.hecho, marcar: t.marcarHecho };
}
