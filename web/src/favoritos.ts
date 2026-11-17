// Favoritos guardados en el propio móvil (sin cuenta: las cuentas llegarán más adelante).
import { useCallback, useState } from 'react';

const CLAVE = 'favoritos';

function leer(): string[] {
  try {
    const v = JSON.parse(localStorage.getItem(CLAVE) || '[]');
    return Array.isArray(v) ? v.filter((x) => typeof x === 'string') : [];
  } catch {
    return [];
  }
}

export function useFavoritos() {
  const [ids, setIds] = useState<string[]>(leer);
  const alternar = useCallback((id: string) => {
    setIds((actual) => {
      const nuevo = actual.includes(id) ? actual.filter((x) => x !== id) : [id, ...actual];
      try { localStorage.setItem(CLAVE, JSON.stringify(nuevo)); } catch { /* sin almacenamiento: dura hasta cerrar */ }
      return nuevo;
    });
  }, []);
  return { ids, es: (id: string) => ids.includes(id), alternar };
}

export type Favoritos = ReturnType<typeof useFavoritos>;
