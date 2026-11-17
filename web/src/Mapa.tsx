// Mapa de salas: el contorno de los distritos (datos abiertos del Ayuntamiento) y un punto por
// sala con funciones según los filtros. No usa servicios de mapas de terceros.
import { useEffect, useMemo, useRef, useState, type MouseEvent as EventoRaton, type PointerEvent as EventoPuntero } from 'react';
import type { Espectaculo } from './datos';
import type { Textos } from './textos';

interface Area { nombre: string; anillos: [number, number][][] }
interface DatosMapa { areas: Area[]; fuente: string }

export interface Sala {
  id: string;
  nombre: string;
  lat: number;
  lon: number;
  barrio?: string;
  direccion?: string;
  espectaculos: Espectaculo[];
}

export function agruparSalas(lista: Espectaculo[]): Sala[] {
  const salas = new Map<string, Sala>();
  for (const e of lista) {
    if (e.lat == null || e.lon == null) continue;
    const id = e.sala_id || `${e.lat},${e.lon}`;
    let s = salas.get(id);
    if (!s) {
      s = { id, nombre: e.sala || '', lat: e.lat, lon: e.lon, barrio: e.barrio, direccion: e.direccion, espectaculos: [] };
      salas.set(id, s);
    }
    s.espectaculos.push(e);
  }
  return [...salas.values()].sort((a, b) => b.espectaculos.length - a.espectaculos.length);
}

// Proyección sencilla (equirectangular): suficiente para una ciudad.
const LAT0 = 41.39;
const COS = Math.cos((LAT0 * Math.PI) / 180);
const proyectar = (lon: number, lat: number): [number, number] => [lon * COS * 1000, -lat * 1000];

export interface Parada { lat: number; lon: number; nombre: string }

export function MapaSalas({ t, salas, elegida, elegir, ciudad, posicion, marcando, alMarcar, ruta }: {
  t: Textos; salas: Sala[]; elegida: string | null; elegir: (id: string | null) => void; ciudad: string;
  posicion?: { lat: number; lon: number } | null; marcando?: boolean; alMarcar?: (lat: number, lon: number) => void;
  ruta?: Parada[];
}) {
  const movido = useRef(false);
  const [datos, setDatos] = useState<DatosMapa | null>(null);
  const [vista, setVista] = useState<[number, number, number, number] | null>(null);
  const arrastre = useRef<{ x: number; y: number; vista: [number, number, number, number] } | null>(null);
  const svg = useRef<SVGSVGElement>(null);

  useEffect(() => {
    fetch(`./datos/${ciudad}-mapa.json`).then((r) => (r.ok ? r.json() : null)).then(setDatos).catch(() => setDatos(null));
  }, [ciudad]);

  const caminos = useMemo(() => (datos?.areas ?? []).map((a) => ({
    nombre: a.nombre,
    d: a.anillos.map((anillo) => anillo.map(([lon, lat], i) => {
      const [x, y] = proyectar(lon, lat);
      return `${i ? 'L' : 'M'}${x.toFixed(2)},${y.toFixed(2)}`;
    }).join('') + 'Z').join(''),
    centro: (() => {
      const pts = a.anillos[0];
      const [x, y] = pts.reduce(([sx, sy], [lon, lat]) => { const [px, py] = proyectar(lon, lat); return [sx + px, sy + py]; }, [0, 0]);
      return [x / pts.length, y / pts.length] as [number, number];
    })(),
  })), [datos]);

  // Encuadre inicial: toda la ciudad.
  const encuadre = useMemo<[number, number, number, number] | null>(() => {
    const pts = (datos?.areas ?? []).flatMap((a) => a.anillos.flat()).map(([lon, lat]) => proyectar(lon, lat));
    if (!pts.length) return null;
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    const m = 2;
    return [Math.min(...xs) - m, Math.min(...ys) - m, Math.max(...xs) - Math.min(...xs) + 2 * m, Math.max(...ys) - Math.min(...ys) + 2 * m];
  }, [datos]);
  // Con una ruta, el mapa empieza encuadrando sus paradas (con margen, y al menos 1,5 km de ancho).
  const encuadreRuta = useMemo<[number, number, number, number] | null>(() => {
    if (!ruta?.length || !encuadre) return null;
    const pts = ruta.map((p) => proyectar(p.lon, p.lat));
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
    const proporcion = encuadre[3] / encuadre[2];
    let w = Math.max(Math.max(...xs) - Math.min(...xs), 1.5) * 1.5;
    w = Math.max(w, (Math.max(...ys) - Math.min(...ys)) * 1.5 / proporcion);
    w = Math.min(w, encuadre[2]);
    return [cx - w / 2, cy - (w * proporcion) / 2, w, w * proporcion];
  }, [ruta, encuadre]);
  const v = vista ?? encuadreRuta ?? encuadre;

  // Al saber dónde está la persona, el mapa se acerca a esa zona.
  useEffect(() => {
    if (!posicion || !encuadre) return;
    const [x, y] = proyectar(posicion.lon, posicion.lat);
    const w = encuadre[2] / 3, h = (encuadre[3] * w) / encuadre[2];
    setVista([x - w / 2, y - h / 2, w, h]);
  }, [posicion?.lat, posicion?.lon, encuadre]); // eslint-disable-line react-hooks/exhaustive-deps

  const marcar = (ev: EventoRaton<SVGSVGElement>) => {
    if (!marcando || movido.current || !svg.current || !alMarcar) return;
    const ctm = svg.current.getScreenCTM();
    if (!ctm) return;
    const pt = new DOMPoint(ev.clientX, ev.clientY).matrixTransform(ctm.inverse());
    alMarcar(-pt.y / 1000, pt.x / (COS * 1000));
  };

  const zoom = (factor: number) => {
    if (!v) return;
    const [x, y, w, h] = v;
    const nw = Math.min(Math.max(w * factor, (encuadre?.[2] ?? w) / 12), encuadre?.[2] ?? w);
    const nh = (h * nw) / w;
    setVista([x + (w - nw) / 2, y + (h - nh) / 2, nw, nh]);
  };

  const alPulsar = (ev: EventoPuntero<SVGSVGElement>) => {
    if (!v) return;
    arrastre.current = { x: ev.clientX, y: ev.clientY, vista: v };
    movido.current = false;
  };
  const alMover = (ev: EventoPuntero<SVGSVGElement>) => {
    const a = arrastre.current;
    if (!a || !svg.current) return;
    const escala = a.vista[2] / svg.current.clientWidth;
    const dx = (ev.clientX - a.x) * escala, dy = (ev.clientY - a.y) * escala;
    if (Math.abs(ev.clientX - a.x) + Math.abs(ev.clientY - a.y) > 4) {
      movido.current = true;
      svg.current.setPointerCapture(ev.pointerId);
    }
    setVista([a.vista[0] - dx, a.vista[1] - dy, a.vista[2], a.vista[3]]);
  };
  const alSoltar = () => { arrastre.current = null; };

  if (!v) return <div className="mapa mapa-vacio" aria-busy="true" />;
  const radio = (n: number) => Math.min(0.55 + Math.sqrt(n) * 0.28, 2.2) * (v[2] / (encuadre?.[2] ?? v[2])) ** 0.6;
  const max = Math.max(1, ...salas.map((s) => s.espectaculos.length));

  return (
    <div className="mapa">
      <svg ref={svg} viewBox={v.join(' ')} role="img" aria-label={t.mapaAria(salas.length)} className={marcando ? 'marcando' : ''}
        onPointerDown={alPulsar} onPointerMove={alMover} onPointerUp={alSoltar} onPointerCancel={alSoltar} onClick={marcar}>
        {caminos.map((c) => <path key={c.nombre} d={c.d} className="distrito" />)}
        {caminos.map((c) => (
          <text key={`t-${c.nombre}`} x={c.centro[0]} y={c.centro[1]} className="distrito-nombre"
            style={{ fontSize: `${v[2] / 38}px` }}>{c.nombre}</text>
        ))}
        {[...salas].reverse().map((s) => {
          const [x, y] = proyectar(s.lon, s.lat);
          const n = s.espectaculos.length;
          return (
            <g key={s.id} onClick={() => { if (!marcando && !movido.current) elegir(s.id === elegida ? null : s.id); }}>
              <circle cx={x} cy={y} r={radio(n)} className={s.id === elegida ? 'sala elegida' : 'sala'}
                style={{ opacity: 0.55 + 0.45 * (n / max) }} />
              {/* Zona de toque más grande que el punto, para el dedo */}
              <circle cx={x} cy={y} r={Math.max(radio(n), v[2] / 40)} className="sala-toque">
                <title>{`${s.nombre}: ${t.resultados(n)}`}</title>
              </circle>
            </g>
          );
        })}
        {ruta?.length ? (() => {
          const pts = ruta.map((p) => proyectar(p.lon, p.lat));
          const r = v[2] / 34;
          return (
            <g className="ruta" pointerEvents="none">
              {pts.length > 1 ? <polyline points={pts.map(([x, y]) => `${x},${y}`).join(' ')} className="ruta-linea"
                style={{ strokeWidth: v[2] / 160, strokeDasharray: `${v[2] / 60} ${v[2] / 90}` }} /> : null}
              {pts.map(([x, y], i) => (
                <g key={i}>
                  <circle cx={x} cy={y} r={r} className="ruta-parada" style={{ strokeWidth: v[2] / 260 }}><title>{`${i + 1}. ${ruta[i].nombre}`}</title></circle>
                  <text x={x} y={y} className="ruta-numero" style={{ fontSize: `${r * 1.15}px` }}>{i + 1}</text>
                </g>
              ))}
            </g>
          );
        })() : null}
        {posicion ? (() => {
          const [x, y] = proyectar(posicion.lon, posicion.lat);
          const r = v[2] / 45;
          return (
            <g className="yo" pointerEvents="none">
              <circle cx={x} cy={y} r={r * 2.2} className="yo-halo" />
              <circle cx={x} cy={y} r={r} className="yo-punto"><title>{t.estasAqui}</title></circle>
            </g>
          );
        })() : null}
      </svg>
      <div className="mapa-botones">
        <button type="button" className="boton-icono relleno" onClick={() => zoom(0.6)} aria-label={t.acercar}>+</button>
        <button type="button" className="boton-icono relleno" onClick={() => zoom(1 / 0.6)} aria-label={t.alejar}>−</button>
      </div>
      {datos?.fuente ? <p className="nota mapa-fuente">{t.fuente}: {datos.fuente}</p> : null}
    </div>
  );
}
