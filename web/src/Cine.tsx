// Cine: cartelera por película o por cine, ficha de cada película y ficha de cada cine.
import { useLayoutEffect, useMemo, useState } from 'react';
import {
  FILTROS_CINE, VERSIONES, esEstreno, filtrarPeliculas, minutosHasta, tituloPeli,
  type Cine, type CarteleraCine, type FiltrosCine, type Pelicula, type Persona, type Premio, type Sesion,
} from './cine';
import { distancia, fmtDia, fmtDistancia, sumaDias, type ClaveFecha } from './filtros';
import type { Idioma, Textos } from './textos';
import type { Favoritos } from './favoritos';
import type { Ubicacion } from './ubicacion';
import type { ItemPlan, Planes } from './planes';
import { MapaSalas, type Sala } from './Mapa';
import { BotonMarca, Corazon, HojaPlan, IconoCheck, enlaceFicha } from './App';
import { clavePeli, marca, type Historial } from './historial';
import type { Espectaculo } from './datos';

export const enlacePeli = (id: string) => `#peli-${id.replace(/[^A-Za-z0-9-]+/g, '-')}`;
export const enlaceCine = (id: string) => `#sala-${id.replace(/[^A-Za-z0-9-]+/g, '-')}`;
export const clavePersona = (p: Persona) => (p.id ? `t${p.id}` : `n-${p.nombre.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-')}`);

// --- Piezas comunes ------------------------------------------------------------------

export function Cartelito({ src, alt, clase }: { src?: string; alt: string; clase: string }) {
  const [falla, setFalla] = useState(false);
  if (!src || falla) {
    return <span className={`${clase} cartel-vacio`} aria-hidden="true"><span>{alt.slice(0, 1)}</span></span>;
  }
  return <img className={clase} src={src} alt={alt} loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={() => setFalla(true)} />;
}

export function Version({ v, t }: { v: string | null; t: Textos }) {
  if (!v) return null;
  return <span className={`version v-${v.replace(/[^A-Za-z]/g, '')}`} title={t.versionesLargo[v]}>{t.versiones[v] || v}</span>;
}

export function PremiosLista({ premios, t, max = 8 }: { premios?: Premio[]; t: Textos; max?: number }) {
  const [todos, setTodos] = useState(false);
  if (!premios?.length) return null;
  const orden = [...premios].sort((a, b) => (a.tipo === b.tipo ? (b.anio || 0) - (a.anio || 0) : a.tipo === 'ganado' ? -1 : 1));
  const vis = todos ? orden : orden.slice(0, max);
  return (
    <ul className="premios">
      {vis.map((p, i) => (
        <li key={`${p.premio}-${p.anio}-${i}`} className={p.tipo === 'ganado' ? 'premio ganado' : 'premio'}>
          <span className="premio-icono" aria-hidden="true">{p.tipo === 'ganado' ? '★' : '☆'}</span>
          <span>{p.premio}{p.anio ? ` · ${p.anio}` : ''}<span className="oculto"> ({p.tipo === 'ganado' ? t.ganado : t.nominado})</span></span>
          {p.tipo === 'nominado' ? <span className="premio-tipo">{t.nominado}</span> : null}
        </li>
      ))}
      {orden.length > max && !todos ? (
        <li><button type="button" className="enlace" onClick={() => setTodos(true)}>{t.mas(orden.length - max).replace(/fecha|data/, 'premi')}</button></li>
      ) : null}
    </ul>
  );
}

const fmtHoraMin = (n?: number) => (n ? `${Math.floor(n / 60)} h ${n % 60 ? `${n % 60} min` : ''}`.trim() : '');

// --- Cartelera de cine -----------------------------------------------------------------

export function VistaCine({ t, lang, datos, error, hoy, ahora, favs, hist, ubic, filtros, cambiar, eventos = [] }: {
  t: Textos; lang: Idioma; datos: CarteleraCine | null; error: boolean; hoy: string; ahora: string; favs: Favoritos; hist: Historial;
  /** Eventos de cine de la agenda: festivales, ciclos, cinefórums, premios, talleres… (Uri, 19/11/2026) */
  eventos?: Espectaculo[];
  ubic: Ubicacion; filtros: FiltrosCine; cambiar: (c: Partial<FiltrosCine>) => void;
}) {
  const [modo, setModo] = useState<'peliculas' | 'cines'>('peliculas');
  const cines = useMemo(() => new Map((datos?.cines || []).map((c) => [c.id, c])), [datos]);
  const f = useMemo(() => ({ ...filtros, cerca: ubic.pos ? { lat: ubic.pos.lat, lon: ubic.pos.lon } : null }), [filtros, ubic.pos]);
  const res = useMemo(() => (datos ? filtrarPeliculas(datos.peliculas, f, hoy, cines, ahora) : []), [datos, f, hoy, cines, ahora]);
  const generos = useMemo(() => {
    const c = new Map<string, number>();
    for (const p of datos?.peliculas || []) for (const g of p.generos || []) c.set(g, (c.get(g) || 0) + 1);
    return [...c.entries()].sort((a, b) => b[1] - a[1]).map(([g]) => g);
  }, [datos]);
  const cinesConSesiones = useMemo(() => (datos?.cines || []).filter((c) => !c.centro && datos!.peliculas.some((p) => p.sesiones.some((s) => s[0] === c.id))), [datos]);
  useLayoutEffect(() => { window.scrollTo(0, 0); }, []);

  return (
    <main className="pantalla">
      <header className="cabecera">
        <div className="titulo">
          <span className="sobretitulo">{t.cineSub}</span>
          <h1>{t.cineTitulo}</h1>
        </div>
        <div className="buscador">
          <label htmlFor="buscar-cine" className="oculto">{t.buscarLabel}</label>
          <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
          <input id="buscar-cine" type="search" enterKeyHint="search" autoComplete="off" value={filtros.q} placeholder={t.buscarTodo}
            onChange={(e) => cambiar({ q: e.target.value })} />
        </div>
      </header>

      <div className="chips" role="group" aria-label={t.cuando}>
        {(['hoy', 'manana', 'semana', 'todo'] as ClaveFecha[]).map((k) => (
          <button key={k} type="button" className="chip pequeno" aria-pressed={filtros.fecha === k} onClick={() => cambiar({ fecha: k })}>{t.fechas[k]}</button>
        ))}
      </div>
      <div className="chips" role="group" aria-label={t.version}>
        {['todas', ...VERSIONES].map((v) => (
          <button key={v} type="button" className="chip pequeno" aria-pressed={filtros.version === v} onClick={() => cambiar({ version: v })}
            title={v === 'todas' ? undefined : t.versionesLargo[v]}>
            {v === 'todas' ? `${t.version}: ${t.todasVersiones}` : t.versiones[v]}
          </button>
        ))}
      </div>
      {generos.length ? (
        <div className="chips" role="group" aria-label={t.generoLabel}>
          {['todos', ...generos].map((g) => (
            <button key={g} type="button" className="chip pequeno" aria-pressed={filtros.genero === g} onClick={() => cambiar({ genero: g })}>
              {g === 'todos' ? `${t.generoLabel}: ${t.todosGeneros}` : g}
            </button>
          ))}
        </div>
      ) : null}
      <div className="fila-controles">
        <label className="selector">
          <span className="oculto">{t.todosCines}</span>
          <select value={filtros.cine} onChange={(e) => cambiar({ cine: e.target.value })}>
            <option value="todos">{t.todosCines}</option>
            {cinesConSesiones.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </label>
        <button type="button" className="chip pequeno" aria-pressed={!!ubic.pos && filtros.distanciaMax != null}
          onClick={() => { if (!ubic.pos) ubic.activar(); cambiar({ distanciaMax: filtros.distanciaMax == null ? 3 : null }); }}>
          {t.cercaDeMi}
        </button>
        <a className="chip pequeno" href="#mapa-cine">{t.mapaCines}</a>
      </div>

      <div className="resumen">
        <span aria-live="polite">{error ? t.error : datos ? `${t.peliculas(res.length)} · ${t.sesiones(res.reduce((n, x) => n + x.s.length, 0))}` : ''}</span>
        <div className="segmentos" role="group" aria-label={t.porPelicula}>
          <button type="button" aria-pressed={modo === 'peliculas'} onClick={() => setModo('peliculas')}>{t.porPelicula}</button>
          <button type="button" aria-pressed={modo === 'cines'} onClick={() => setModo('cines')}>{t.porCine}</button>
        </div>
      </div>

      {eventos.length && modo === 'peliculas' ? (
        <section className="fila-inicio eventos-cine">
          <div className="fila-cabecera"><h2 className="seccion-titulo">{t.eventosCine}</h2><a className="ver-todo" href="#eventos">{t.verTodo}</a></div>
          <div className="carrusel">
            {eventos.slice(0, 14).map((e) => (
              <a key={e.id} className="ticket ticket-escena" href={enlaceFicha(e.id)}>
                <span className="ticket-hora">{fmtDia(e.funciones[0][0], t)}</span>
                <span className="ticket-cuando">{t.eventos[e.subtipo || ''] || t.tipos.eventos}</span>
                <span className="ticket-nombre">{e.nombre}</span>
                <span className="ticket-lugar">{e.sala || ''}</span>
              </a>
            ))}
          </div>
        </section>
      ) : null}

      <div className="lista">
        {!datos && !error ? <p className="aviso">{t.cargando}</p> : null}
        {datos && modo === 'peliculas' ? res.map(({ p, s }) => (
          <TarjetaPeli key={p.id} p={p} s={s} t={t} lang={lang} hoy={hoy} ahora={ahora} cines={cines} guardada={favs.es(p.id)}
            vista={hist.es(clavePeli(p.id)) ? marca('peli', t).hecho : undefined}
            dist={f.cerca ? Math.min(...s.map((x) => { const c = cines.get(x[0]); return c?.lat != null && c.lon != null ? distancia(f.cerca!, c.lat, c.lon) : Infinity; })) : null} />
        )) : null}
        {datos && modo === 'cines' ? <ListaCines t={t} datos={datos} res={res} hoy={hoy} cerca={f.cerca} /> : null}
        {datos && res.length === 0 ? <p className="aviso">{t.vacio}</p> : null}
        {datos ? <p className="nota">{t.atribucionTmdb}</p> : null}
      </div>
    </main>
  );
}

function TarjetaPeli({ p, s, t, lang, hoy, ahora, cines, guardada, dist, vista }: {
  p: Pelicula; s: Sesion[]; t: Textos; lang: Idioma; hoy: string; ahora: string; cines: Map<string, Cine>; guardada: boolean; dist: number | null;
  vista?: string;
}) {
  const proxima = s[0];
  const versiones = [...new Set(s.map((x) => x[3]).filter(Boolean))] as string[];
  const nCines = new Set(s.map((x) => x[0])).size;
  const m = minutosHasta(proxima[1], proxima[2], hoy, ahora);
  const titulo = tituloPeli(p, lang);
  return (
    <a className="tarjeta tarjeta-peli" href={enlacePeli(p.id)}>
      <Cartelito src={p.cartel} alt={titulo} clase="peli-cartel" />
      <span className="peli-info">
        <span className="etiquetas">
          {esEstreno(p, hoy) ? <span className="etiqueta roja">{t.estreno}</span> : null}
          {p.premios?.some((x) => x.tipo === 'ganado') ? <span className="etiqueta genero">★ {t.premiada}</span> : null}
          {vista ? <span className="etiqueta marca-hecho"><IconoCheck lleno />{vista}</span> : null}
          {guardada ? <Corazon lleno /> : null}
        </span>
        <span className="tarjeta-nombre">{titulo}</span>
        <span className="texto-suave">{[p.anio, fmtHoraMin(p.duracion), (p.generos || []).slice(0, 2).join(', ')].filter(Boolean).join(' · ')}</span>
        {p.direccion?.length ? <span className="texto-suave">{t.direccionPeli}: {p.direccion.map((d) => d.nombre).join(', ')}</span> : null}
        <span className="versiones">{versiones.map((v) => <Version key={v} v={v} t={t} />)}</span>
        <span className="cuando">
          {proxima[1] === hoy ? t.sesionesHoy : fmtDia(proxima[1], t)}{proxima[2] ? ` · ${proxima[2]}` : ''}
          {m != null && m >= 0 && m <= 90 ? ` (${t.empiezaEn(m)})` : ''}
        </span>
        <span className="texto-suave">
          {cines.get(proxima[0])?.nombre}{nCines > 1 ? ` + ${nCines - 1}` : ''} · {t.sesiones(s.length)}{dist != null && dist !== Infinity ? ` · ${fmtDistancia(dist)}` : ''}
        </span>
      </span>
    </a>
  );
}

function ListaCines({ t, datos, res, hoy, cerca }: {
  t: Textos; datos: CarteleraCine; res: { p: Pelicula; s: Sesion[] }[]; hoy: string; cerca: { lat: number; lon: number } | null;
}) {
  const porCine = new Map<string, number>();
  for (const { s } of res) for (const x of s) porCine.set(x[0], (porCine.get(x[0]) || 0) + 1);
  const conHorarios = datos.cines.filter((c) => porCine.has(c.id));
  const d = (c: Cine) => (cerca && c.lat != null && c.lon != null ? distancia(cerca, c.lat, c.lon) : null);
  conHorarios.sort((a, b) => (cerca ? (d(a) ?? 9e9) - (d(b) ?? 9e9) : (porCine.get(b.id) || 0) - (porCine.get(a.id) || 0)));
  const sinHorarios = datos.cines.filter((c) => !c.centro && !datos.peliculas.some((p) => p.sesiones.some((s) => s[0] === c.id && s[1] >= hoy)));
  return (
    <>
      {conHorarios.map((c) => (
        <a key={c.id} className="tarjeta fila-cine" href={enlaceCine(c.id)}>
          <span className="tarjeta-nombre">{c.nombre}</span>
          <span className="texto-suave">{[c.direccion, c.barrio, d(c) != null ? fmtDistancia(d(c)!) : ''].filter(Boolean).join(' · ')}</span>
          <span className="cuando">{t.sesiones(porCine.get(c.id) || 0)}{c.centro ? ` · ${t.centroCivico}` : ''}</span>
        </a>
      ))}
      {sinHorarios.length ? (
        <section className="bloque">
          <h3 className="seccion-titulo">{t.cinesSinHorarios}</h3>
          {sinHorarios.map((c) => (
            <div key={c.id} className="fila-cine sin">
              <span className="caja-titulo">{c.nombre}</span>
              <span className="texto-suave">{[c.direccion, c.barrio].filter(Boolean).join(' · ')}</span>
              {c.ver_en ? <a className="enlace" href={enlaceCine(c.ver_en)}>{t.verEn(datos.cines.find((x) => x.id === c.ver_en)?.nombre || '')}</a>
                : c.web ? <a className="enlace" href={c.web} target="_blank" rel="noopener noreferrer">{t.horariosEnWeb}</a> : null}
            </div>
          ))}
        </section>
      ) : null}
    </>
  );
}

// --- Ficha de película -------------------------------------------------------------------

// Cine → días → sesiones, con los cines ordenados por su primera sesión.
function porCines(s: Sesion[]): [string, [string, Sesion[]][]][] {
  const orden = [...s].sort((a, b) => (a[1] + (a[2] || '')).localeCompare(b[1] + (b[2] || '')));
  const cines = new Map<string, Map<string, Sesion[]>>();
  for (const x of orden) {
    if (!cines.has(x[0])) cines.set(x[0], new Map());
    const m = cines.get(x[0])!;
    m.set(x[1], [...(m.get(x[1]) || []), x]);
  }
  return [...cines.entries()].map(([c, m]) => [c, [...m.entries()]]);
}

// Enlace de compra en el idioma de la app (las tiendas de Mooby y Verdi lo llevan en la dirección).
export function enlaceCompra(url: string | null | undefined, lang: Idioma): string | undefined {
  if (!url) return undefined;
  return lang === 'ca' ? url.replace('language=esp', 'language=cat').replace('language=ESP', 'language=CAT') : url;
}

export function FichaPelicula({ t, lang, p, datos, hoy, ahora, volver, favs, planes, hist, zona, ciudad }: {
  t: Textos; lang: Idioma; p: Pelicula; datos: CarteleraCine; hoy: string; ahora: string; volver: () => void;
  favs: Favoritos; planes: Planes; hist: Historial; zona: string; ciudad: string;
}) {
  const cines = useMemo(() => new Map(datos.cines.map((c) => [c.id, c])), [datos]);
  const [version, setVersion] = useState('todas');
  const [paraPlan, setParaPlan] = useState<ItemPlan | null>(null);
  const [aviso, setAviso] = useState<{ texto: string; plan: string } | null>(null);
  useLayoutEffect(() => { window.scrollTo(0, 0); setAviso(null); }, [p.id]);
  const futuras = p.sesiones.filter((s) => s[1] > hoy || (s[1] === hoy && (!s[2] || s[2] >= ahora)));
  const versiones = [...new Set(futuras.map((s) => s[3]).filter(Boolean))] as string[];
  const visibles = futuras.filter((s) => version === 'todas' || s[3] === version);
  const grupos = porCines(visibles);
  const titulo = tituloPeli(p, lang);
  const sinopsis = p.sinopsis?.[lang] || p.sinopsis?.es || p.sinopsis?.ca || Object.values(p.sinopsis || {})[0];
  const guardada = favs.es(p.id);
  const item = (s: Sesion): ItemPlan => {
    const c = cines.get(s[0]);
    return { id: p.id, dia: s[1], hora: s[2] || undefined, nombre: titulo, sala: c?.nombre, direccion: c?.direccion, barrio: c?.barrio,
      lat: c?.lat, lon: c?.lon, duracion: p.duracion, ciudad, zona, clase: 'peli' };
  };
  const personas = (lista: Persona[] | undefined, titulo2: string, fotos = false) => (lista?.length ? (
    <section className="bloque">
      <h3>{titulo2}</h3>
      <div className={fotos ? 'personas con-fotos' : 'personas'}>
        {lista.map((x) => (
          <a key={`${x.nombre}-${x.papel}`} className="persona" href={`#persona-${clavePersona(x)}`}>
            {fotos ? <Cartelito src={x.foto} alt={x.nombre} clase="persona-foto" /> : null}
            <span className="persona-nombre">{x.nombre}{x.premios?.some((y) => y.tipo === 'ganado') ? ' ★' : ''}</span>
            {x.papel ? <span className="texto-suave persona-papel">{x.papel}</span> : null}
          </a>
        ))}
      </div>
    </section>
  ) : null);

  return (
    <main className="pantalla">
      <div className="ficha-barra">
        <button type="button" className="boton-volver" onClick={volver} aria-label={t.volver}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 5l-7 7 7 7" /></svg>
          {t.navCine}
        </button>
        <span className="barra-derecha">
          <BotonMarca t={t} hist={hist} h={{ clave: clavePeli(p.id), clase: 'peli', nombre: titulo, enlace: enlacePeli(p.id) }} />
          <button type="button" className="boton-icono boton-corazon" aria-pressed={guardada} aria-label={guardada ? t.favQuitar : t.favGuardar}
            onClick={() => favs.alternar(p.id)}>
            <Corazon lleno={guardada} />
          </button>
        </span>
      </div>
      <div className="peli-hero">
        {p.fondo ? <img className="peli-fondo" src={p.fondo} alt="" aria-hidden="true" referrerPolicy="no-referrer" /> : null}
        <div className="peli-hero-contenido">
          <Cartelito src={p.cartel} alt={`${t.imagen} «${titulo}»`} clase="peli-cartel grande" />
          <div className="peli-hero-texto">
            <span className="etiquetas">
              {esEstreno(p, hoy) ? <span className="etiqueta roja">{t.estreno}</span> : null}
              {p.edad ? <span className="etiqueta suave">{t.edadTxt(p.edad)}</span> : null}
              {p.nota ? <span className="etiqueta suave" title={t.notaTmdb}>★ {p.nota.toFixed(1)}</span> : null}
            </span>
            <h2>{titulo}</h2>
            {p.titulo_original && p.titulo_original !== titulo ? <span className="texto-suave titulo-original">{p.titulo_original}</span> : null}
            <span className="texto-claro">{[p.anio, fmtHoraMin(p.duracion), (p.generos || []).join(', ')].filter(Boolean).join(' · ')}</span>
          </div>
        </div>
      </div>
      <div className="ficha">
        {p.lema ? <p className="lema">«{p.lema}»</p> : null}
        {p.trailer ? (
          <a className="trailer" href={`https://www.youtube.com/watch?v=${p.trailer}`} target="_blank" rel="noopener noreferrer">
            <img src={`https://i.ytimg.com/vi/${p.trailer}/hqdefault.jpg`} alt="" loading="lazy" referrerPolicy="no-referrer" />
            <span className="trailer-boton"><svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>{t.verTrailer}</span>
          </a>
        ) : null}

        <section className="bloque">
          <h3>{t.dondeVer}</h3>
          {versiones.length > 1 ? (
            <div className="chips sin-margen" role="group" aria-label={t.version}>
              {['todas', ...versiones].map((v) => (
                <button key={v} type="button" className="chip pequeno" aria-pressed={version === v} onClick={() => setVersion(v)}>
                  {v === 'todas' ? t.todasVersiones : t.versiones[v] || v}
                </button>
              ))}
            </div>
          ) : null}
          {grupos.map(([cid, porDia]) => {
            const c = cines.get(cid);
            const primera = porDia[0][1][0];
            const total = porDia.reduce((n, [, ss]) => n + ss.length, 0);
            const directas = porDia.some(([, ss]) => ss.some((s) => s[7] === 1));
            return (
              <details key={cid} className="cine-desplegable" open={grupos.length === 1}>
                <summary>
                  <span className="cine-desplegable-texto">
                    <span className="cine-nombre">{c?.nombre || cid}</span>
                    <span className="texto-suave">
                      {[c?.barrio, `${t.proxima} ${primera[1] === hoy ? t.sesionesHoy : fmtDia(primera[1], t)}${primera[2] ? ` · ${primera[2]}` : ''}`, t.sesiones(total)].filter(Boolean).join(' · ')}
                    </span>
                  </span>
                  <svg className="flecha" aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6" /></svg>
                </summary>
                <div className="cine-desplegable-cuerpo">
                  {porDia.map(([dia, ss]) => (
                    <div key={dia} className="dia-sesiones">
                      <h4>{dia === hoy ? `${t.sesionesHoy} · ${fmtDia(dia, t)}` : fmtDia(dia, t)}</h4>
                      <div className="entradas">
                        {ss.map((s, i) => {
                          const enPlan = planes.conFuncion(p.id, s[1], s[2] || undefined);
                          const directa = s[7] === 1;
                          return (
                            <span key={`${s[2]}-${i}`} className="entrada">
                              <a className="entrada-hora" href={enlaceCompra(s[5] || c?.web, lang)} target="_blank" rel="noopener noreferrer"
                                aria-label={`${directa ? t.comprarEntrada : t.horariosEnWeb}: ${c?.nombre} ${s[2] || ''}`}>
                                <strong>{s[2] || '—'}</strong>
                                <span className="entrada-meta">{[s[3] ? t.versiones[s[3]] || s[3] : '', s[4]].filter(Boolean).join(' · ')}</span>
                                {s[6] ? <span className="entrada-especial">{s[6]}</span> : null}
                              </a>
                              {enPlan ? (
                                <a className="entrada-plan hecho" href={`#plan-${enPlan.id}`} aria-label={t.enPlan(enPlan.nombre)}>✓</a>
                              ) : (
                                <button type="button" className="entrada-plan" aria-label={t.anadirSesion(`${fmtDia(s[1], t)} ${s[2] || ''}`)}
                                  onClick={() => setParaPlan(item(s))}>+</button>
                              )}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                  <span className="nota">{directas ? t.compraDirecta : t.compraEnWebCine}</span>
                  <a className="enlace" href={enlaceCine(cid)}>{t.verCine}</a>
                </div>
              </details>
            );
          })}
          {grupos.length === 0 ? <span className="texto-suave">{t.sinFechas}</span> : null}
          {aviso ? <p className="aviso-plan" role="status">{aviso.texto} <a href={`#plan-${aviso.plan}`}>{t.verPlan}</a></p> : null}
        </section>

        {sinopsis ? (
          <section className="bloque">
            <h3>{t.sinopsis}</h3>
            <p className="descripcion">{sinopsis.replace(/<[^>]+>/g, '')}</p>
          </section>
        ) : null}
        {p.premios?.length ? (
          <section className="bloque">
            <h3>{t.premiosTit}</h3>
            <PremiosLista premios={p.premios} t={t} />
            <span className="nota">{t.personaPremiosNota}</span>
          </section>
        ) : null}
        {personas(p.direccion, t.direccionPeli, true)}
        {personas(p.reparto, t.reparto, true)}
        {personas(p.guion, t.guion)}
        {personas(p.musica, t.musica)}
        <p className="nota">{t.atribucionTmdb}{p.tmdb ? <> · <a href={`https://www.themoviedb.org/movie/${p.tmdb}`} target="_blank" rel="noopener noreferrer">TMDB</a></> : null}{p.imdb ? <> · <a href={`https://www.imdb.com/title/${p.imdb}/`} target="_blank" rel="noopener noreferrer">IMDb</a></> : null}</p>
      </div>
      {paraPlan ? (
        <HojaPlan t={t} item={paraPlan} planes={planes} cerrar={() => setParaPlan(null)}
          listo={(planId, nombre) => { setParaPlan(null); setAviso({ texto: t.anadido(nombre), plan: planId }); }} />
      ) : null}
    </main>
  );
}

// --- Ficha de cine -----------------------------------------------------------------------

export function FichaCine({ t, lang, c, datos, hoy, ahora, volver }: {
  t: Textos; lang: Idioma; c: Cine; datos: CarteleraCine; hoy: string; ahora: string; volver: () => void;
}) {
  const [dia, setDia] = useState(hoy);
  useLayoutEffect(() => { window.scrollTo(0, 0); setDia(hoy); }, [c.id, hoy]);
  const dias = Array.from({ length: 7 }, (_, i) => sumaDias(hoy, i));
  const pelis = datos.peliculas
    .map((p) => ({ p, s: p.sesiones.filter((s) => s[0] === c.id && s[1] === dia && (dia !== hoy || !s[2] || s[2] >= ahora)) }))
    .filter((x) => x.s.length);
  return (
    <main className="pantalla">
      <div className="ficha-barra">
        <button type="button" className="boton-volver" onClick={volver} aria-label={t.volver}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 5l-7 7 7 7" /></svg>
          {t.navCine}
        </button>
      </div>
      <div className="ficha">
        <div className="ficha-cabecera">
          <span className="sobretitulo">{c.centro ? t.centroCivico : t.navCine}</span>
          <h2>{c.nombre}</h2>
          <span className="texto-suave">{[c.direccion, c.barrio].filter(Boolean).join(' · ')}</span>
          <span className="fila-enlaces">
            {c.lat != null && c.lon != null ? <a className="enlace" href={`https://www.google.com/maps/search/?api=1&query=${c.lat},${c.lon}`} target="_blank" rel="noopener noreferrer">{t.comoLlegar}</a> : null}
            {c.web ? <a className="enlace" href={c.web} target="_blank" rel="noopener noreferrer">Web</a> : null}
          </span>
        </div>
        <div className="chips sin-margen" role="group" aria-label={t.cuando}>
          {dias.map((d) => <button key={d} type="button" className="chip pequeno" aria-pressed={dia === d} onClick={() => setDia(d)}>{d === hoy ? t.fechas.hoy : fmtDia(d, t)}</button>)}
        </div>
        {pelis.length === 0 ? <p className="texto-suave">{c.ver_en ? t.verEn(datos.cines.find((x) => x.id === c.ver_en)?.nombre || '') : t.sinFechas}</p> : null}
        {pelis.map(({ p, s }) => (
          <div key={p.id} className="tarjeta tarjeta-peli compacta">
            <a href={enlacePeli(p.id)} tabIndex={-1} aria-hidden="true"><Cartelito src={p.cartel} alt={tituloPeli(p, lang)} clase="peli-cartel" /></a>
            <span className="peli-info">
              <a className="tarjeta-nombre" href={enlacePeli(p.id)}>{tituloPeli(p, lang)}</a>
              <span className="texto-suave">{[fmtHoraMin(p.duracion), (p.generos || []).slice(0, 2).join(', ')].filter(Boolean).join(' · ')}</span>
              {/* Cada hora lleva a la compra de esa sesión en la web del cine (si la web lo permite). */}
              <span className="horas">{s.map((x, i) => (
                <a key={i} className="hora-chip" href={enlaceCompra(x[5] || c.web, lang)} target="_blank" rel="noopener noreferrer"
                  aria-label={`${x[7] === 1 ? t.comprarEntrada : t.horariosEnWeb}: ${tituloPeli(p, lang)} ${x[2] || ''}`}>
                  {x[2] || '—'}{x[3] ? <small> {t.versiones[x[3]] || x[3]}</small> : null}
                </a>
              ))}</span>
            </span>
          </div>
        ))}
        {pelis.length ? <p className="nota">{pelis.some(({ s }) => s.some((x) => x[7] === 1)) ? t.compraDirecta : t.compraEnWebCine}</p> : null}
        {c.fuente ? <p className="nota">{t.fuente}: <a href={c.fuente} target="_blank" rel="noopener noreferrer">Guia BCN</a></p> : null}
      </div>
    </main>
  );
}

// --- Mapa de cines -------------------------------------------------------------------------

export function VistaMapaCine({ t, datos, hoy, ubic }: { t: Textos; datos: CarteleraCine | null; hoy: string; ubic: Ubicacion }) {
  const [elegida, setElegida] = useState<string | null>(null);
  const salas: Sala[] = useMemo(() => (datos?.cines || []).filter((c) => c.lat != null && c.lon != null).map((c) => ({
    id: c.id, nombre: c.nombre, lat: c.lat!, lon: c.lon!, barrio: c.barrio, direccion: c.direccion,
    // el mapa cuenta «espectáculos»: aquí, películas con sesión desde hoy
    espectaculos: (datos?.peliculas || []).filter((p) => p.sesiones.some((s) => s[0] === c.id && s[1] >= hoy)) as never[],
  })).filter((s) => s.espectaculos.length), [datos, hoy]);
  const sala = salas.find((s) => s.id === elegida);
  return (
    <main className="pantalla">
      <header className="cabecera">
        <div className="titulo"><span className="sobretitulo">{t.navCine}</span><h1>{t.mapaCines}</h1></div>
      </header>
      <div className="lista">
        <MapaSalas t={t} salas={salas} elegida={elegida} elegir={setElegida} ciudad="barcelona"
          posicion={ubic.pos ? { lat: ubic.pos.lat, lon: ubic.pos.lon } : null} />
        {sala ? (
          <a className="tarjeta fila-cine" href={enlaceCine(sala.id)}>
            <span className="tarjeta-nombre">{sala.nombre}</span>
            <span className="texto-suave">{[sala.direccion, sala.barrio].filter(Boolean).join(' · ')}</span>
            <span className="cuando">{t.peliculas(sala.espectaculos.length)}</span>
          </a>
        ) : <p className="nota">{t.mapaTxt}</p>}
      </div>
    </main>
  );
}

export { FILTROS_CINE };
