// Dónde está la persona: por el GPS del móvil (con su permiso) o marcándolo en el mapa.
// La ubicación se usa solo en el móvil: la app no tiene servidor y no la envía a ningún sitio.
import { useCallback, useEffect, useState } from 'react';

export type EstadoUbicacion = 'apagada' | 'pidiendo' | 'activa' | 'denegada';
export interface Posicion { lat: number; lon: number; origen: 'gps' | 'mapa' }

const CLAVE = 'ubicacion';

function guardar(valor: object | null) {
  try {
    if (valor) localStorage.setItem(CLAVE, JSON.stringify(valor));
    else localStorage.removeItem(CLAVE);
  } catch { /* sin almacenamiento: no se recuerda */ }
}

function leer(): { origen: 'gps' } | Posicion | null {
  try { return JSON.parse(localStorage.getItem(CLAVE) || 'null'); } catch { return null; }
}

export function useUbicacion() {
  const [pos, setPos] = useState<Posicion | null>(null);
  const [estado, setEstado] = useState<EstadoUbicacion>('apagada');

  const activar = useCallback(() => {
    if (!('geolocation' in navigator)) { setEstado('denegada'); return; }
    setEstado('pidiendo');
    navigator.geolocation.getCurrentPosition(
      (p) => {
        setPos({ lat: p.coords.latitude, lon: p.coords.longitude, origen: 'gps' });
        setEstado('activa');
        guardar({ origen: 'gps' }); // del GPS solo se recuerda que la persona lo activó, no dónde estaba
      },
      () => setEstado('denegada'),
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 5 * 60 * 1000 },
    );
  }, []);

  const fijar = useCallback((lat: number, lon: number) => {
    const p: Posicion = { lat, lon, origen: 'mapa' };
    setPos(p);
    setEstado('activa');
    guardar(p);
  }, []);

  const apagar = useCallback(() => { setPos(null); setEstado('apagada'); guardar(null); }, []);

  // Si la persona ya lo había activado, se recupera al abrir (el móvil no vuelve a preguntar).
  useEffect(() => {
    const g = leer();
    if (g && 'lat' in g) { setPos(g); setEstado('activa'); } else if (g?.origen === 'gps') activar();
  }, [activar]);

  return { pos, estado, activar, fijar, apagar };
}

export type Ubicacion = ReturnType<typeof useUbicacion>;
