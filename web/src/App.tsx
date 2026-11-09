import { useCallback, useDeferredValue, useEffect, useLayoutEffect, useMemo, useRef, useState, type FormEvent, type RefObject } from 'react';
import { cargarCartelera, type Cartelera, type Espectaculo } from './datos';
import {
  FILTROS_INICIALES, FUNCIONES, GENEROS, MESES_CALENDARIO, PRECIO_TOPE, TIPOS_EVENTO, cuantosFiltros, duracionTxt, filtrar,
  distanciaA, fmtCorto, fmtDia, fmtDistancia, fmtRango, funcionesEnRango, hoyEn, pasa, precioTxt, publicoTxt, rango,
  sumaDias, tipoTxt,
  type ClaveFecha, type Filtros,
} from './filtros';
import { TEXTOS, guardarIdioma, idiomaInicial, type Idioma, type Textos } from './textos';
import { useFavoritos, type Favoritos } from './favoritos';
import { useUbicacion, type Ubicacion } from './ubicacion';
import { MapaSalas, agruparSalas } from './Mapa';
import {
  claveItem, descargar, enlaceRuta, itemDe, planIcs, porDias, solapes, usePlanes, type ItemPlan, type Plan, type Planes,
} from './planes';

const POR_PAGINA = 40;

// --- Rutas: la dirección dice qué pantalla se ve, así funciona el botón «atrás» del móvil.
// Solo letras, números y guiones (#mapa, #ficha-open-data-bcn-994…), para que el enlace
// funcione en cualquier sitio donde se publique la app.
type Ruta = { vista: 'cartelera' } | { vista: 'ficha'; clave: string } | { vista: 'mapa' } | { vista: 'favoritos' }
  | { vista: 'planes' } | { vista: 'plan'; id: string };

const claveFicha = (id: string) => id.replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '');

function leerRuta(): Ruta {
  const h = window.location.hash.replace(/^#\/?/, '');
  if (h.startsWith('ficha-')) return { vista: 'ficha', clave: h.slice(6) };
  if (h === 'mapa') return { vista: 'mapa' };
  if (h === 'favoritos') return { vista: 'favoritos' };
  if (h === 'planes') return { vista: 'planes' };
  if (h.startsWith('plan-')) return { vista: 'plan', id: h.slice(5) };
  return { vista: 'cartelera' };
}

const enlaceFicha = (id: string) => `#ficha-${claveFicha(id)}`;

export default function App() {
  const [lang, setLang] = useState<Idioma>(idiomaInicial);
  const [ruta, setRuta] = useState<Ruta>(leerRuta);
  const [cartelera, setCartelera] = useState<Cartelera | null>(null);
  const [error, setError] = useState(false);
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_INICIALES);
  const [hoja, setHoja] = useState<null | 'filtros' | 'calendario'>(null);
  const [limite, setLimite] = useState(POR_PAGINA);
  const navegado = useRef(false);
  const scrollLista = useRef(0);
  const t = TEXTOS[lang];
  const favs = useFavoritos();
  const ubic = useUbicacion();
  const planes = usePlanes();
  // La ubicación entra en los filtros (para la distancia y el orden «más cerca»).
  useEffect(() => {
    setFiltros((f) => (ubic.pos
      ? { ...f, cerca: { lat: ubic.pos.lat, lon: ubic.pos.lon } }
      : { ...f, cerca: null, orden: 'fecha', distanciaMax: null }));
  }, [ubic.pos]);

  useEffect(() => {
    cargarCartelera('barcelona').then(setCartelera).catch(() => setError(true));
  }, []);

  useEffect(() => {
    const cambio = () => { navegado.current = true; setRuta(leerRuta()); };
    window.addEventListener('hashchange', cambio);
    return () => window.removeEventListener('hashchange', cambio);
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
    guardarIdioma(lang);
  }, [lang]);

  const cambiar = useCallback((cambio: Partial<Filtros>) => {
    setFiltros((f) => ({ ...f, ...cambio }));
    setLimite(POR_PAGINA);
  }, []);

  const volver = useCallback(() => {
    if (navegado.current && window.history.length > 1) window.history.back();
    else window.location.hash = '#cartelera';
  }, []);

  const hoy = cartelera ? hoyEn(cartelera.ciudad.zona_horaria) : '';
  const lista = cartelera?.espectaculos ?? [];
  const actual = ruta.vista === 'ficha' ? lista.find((e) => claveFicha(e.id) === ruta.clave) : undefined;

  return (
    <div className="app">
      {ruta.vista === 'cartelera' || (ruta.vista === 'ficha' && !actual) ? (
        <VistaCartelera
          t={t} lang={lang} setLang={setLang} cartelera={cartelera} error={error} hoy={hoy}
          filtros={filtros} cambiar={cambiar} limite={limite} setLimite={setLimite}
          abrirFiltros={() => setHoja('filtros')} abrirCalendario={() => setHoja('calendario')} scrollLista={scrollLista} favs={favs}
          ubic={ubic}
        />
      ) : null}
      {ruta.vista === 'ficha' && actual && cartelera ? (
        <Ficha t={t} lang={lang} e={actual} hoy={hoy} volver={volver} favs={favs} planes={planes} cartelera={cartelera} />
      ) : null}
      {ruta.vista === 'mapa' ? (
        <VistaMapa t={t} cartelera={cartelera} hoy={hoy} filtros={filtros} cambiar={cambiar}
          abrirCalendario={() => setHoja('calendario')} favs={favs} ubic={ubic} />
      ) : null}
      {ruta.vista === 'favoritos' ? <VistaFavoritos t={t} lista={lista} hoy={hoy} favs={favs} /> : null}
      {ruta.vista === 'planes' ? <VistaPlanes t={t} planes={planes} /> : null}
      {ruta.vista === 'plan' ? <VistaPlan t={t} lista={lista} hoy={hoy} planes={planes} id={ruta.id} /> : null}

      <nav className="nav" aria-label={t.seccionesLabel}>
        <a href="#cartelera" aria-current={ruta.vista === 'cartelera' || ruta.vista === 'ficha' ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M4 6h16v4a2 2 0 0 0 0 4v4H4v-4a2 2 0 0 0 0-4z" /><path d="M10 6v12" strokeDasharray="2 2" /></svg>
          {t.navCartelera}
        </a>
        <a href="#mapa" aria-current={ruta.vista === 'mapa' ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z" /><circle cx="12" cy="10" r="2" /></svg>
          {t.navMapa}
        </a>
        <a href="#favoritos" aria-current={ruta.vista === 'favoritos' ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" /></svg>
          {t.navFavoritos}
        </a>
        <a href="#planes" aria-current={ruta.vista === 'planes' || ruta.vista === 'plan' ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M4 10h16M9 3v4M15 3v4M9 15l2 2 4-4" /></svg>
          {t.navPlanes}
        </a>
      </nav>

      {hoja === 'filtros' && cartelera ? (
        <HojaFiltros t={t} lista={lista} hoy={hoy} filtros={filtros} cambiar={cambiar} cerrar={() => setHoja(null)} ubic={ubic} />
      ) : null}
      {hoja === 'calendario' && cartelera ? (
        <HojaCalendario t={t} lista={lista} hoy={hoy} filtros={filtros} cambiar={cambiar} cerrar={() => setHoja(null)} />
      ) : null}
    </div>
  );
}

// --- Cartelera ------------------------------------------------------------------

interface PropsCartelera {
  t: Textos; lang: Idioma; setLang: (l: Idioma) => void; cartelera: Cartelera | null; error: boolean; hoy: string;
  filtros: Filtros; cambiar: (c: Partial<Filtros>) => void; limite: number; setLimite: (n: number) => void;
  abrirFiltros: () => void; abrirCalendario: () => void; scrollLista: RefObject<number>; favs: Favoritos; ubic: Ubicacion;
}

function VistaCartelera({ t, lang, setLang, cartelera, error, hoy, filtros, cambiar, limite, setLimite, abrirFiltros, abrirCalendario, scrollLista, favs, ubic }: PropsCartelera) {
  const lista = cartelera?.espectaculos ?? [];
  const q = useDeferredValue(filtros.q);
  const f = useMemo(() => ({ ...filtros, q }), [filtros, q]);
  const resultados = useMemo(() => (cartelera ? filtrar(lista, f, hoy) : []), [cartelera, lista, f, hoy]);
  // Se desplaza la página entera (funciona en cualquier móvil y dentro de otras apps).
  // Al volver de una ficha, la cartelera sigue donde estaba.
  useLayoutEffect(() => {
    if (cartelera) window.scrollTo(0, scrollLista.current);
  }, [cartelera, scrollLista]);

  const [desde, hasta] = rango(f, hoy);
  const nFiltros = cuantosFiltros(filtros);

  return (
    <main className="pantalla">
      <header className="cabecera">
        <div className="cabecera-fila">
          <div className="titulo">
            <span className="sobretitulo">
              {cartelera ? `${cartelera.ciudad.nombre} · ${t.actualizado} ${fmtDia(cartelera.actualizado, t).split(' ').slice(1).join(' ')}` : 'Barcelona'}
            </span>
            <h1>{t.cartelera}</h1>
          </div>
          <div className="idiomas" role="group" aria-label="Idioma">
            {(['es', 'ca'] as Idioma[]).map((l) => (
              <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)}>{l.toUpperCase()}</button>
            ))}
          </div>
        </div>
        <div className="buscador">
          <label htmlFor="buscar" className="oculto">{t.buscarLabel}</label>
          <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
          <input id="buscar" type="search" enterKeyHint="search" autoComplete="off" value={filtros.q} placeholder={t.buscar}
            onChange={(e) => cambiar({ q: e.target.value })} />
        </div>
      </header>

      <FiltrosRapidos t={t} lista={lista} f={f} filtros={filtros} cambiar={cambiar} hoy={hoy}
        cargada={!!cartelera} abrirCalendario={abrirCalendario} />
      <BotonCerca t={t} ubic={ubic} filtros={filtros} cambiar={cambiar} />

      <div className="resumen">
        <span aria-live="polite">{error ? t.error : cartelera ? t.resultados(resultados.length) : ''}</span>
        <button type="button" className="boton-filtros" onClick={abrirFiltros} disabled={!cartelera}>
          <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 7h10M18 7h2M4 17h4M12 17h8" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="17" r="2" /></svg>
          <span>{t.filtros}</span>
          {nFiltros > 0 ? <span className="insignia">{nFiltros}</span> : null}
        </button>
      </div>

      <div className="lista">
        {!cartelera && !error ? <p className="aviso">{t.cargando}</p> : null}
        {error ? <p className="aviso">{t.error}</p> : null}
        {cartelera && !q.trim() ? <CercaDeTi t={t} lista={lista} f={f} hoy={hoy} /> : null}
        {resultados.slice(0, limite).map((e) => (
          <Tarjeta key={e.id} e={e} t={t} desde={desde} hasta={hasta} guardado={favs.es(e.id)} dist={distanciaA(e, f)}
            alAbrir={() => { scrollLista.current = window.scrollY; }} />
        ))}
        {cartelera && resultados.length === 0 ? <p className="aviso">{t.vacio}</p> : null}
        {resultados.length > limite ? (
          <button type="button" className="boton-secundario" onClick={() => setLimite(limite + POR_PAGINA)}>
            {t.verMas} ({resultados.length - limite})
          </button>
        ) : null}
        {cartelera ? <p className="licencia">{cartelera.licencia}</p> : null}
      </div>
    </main>
  );
}

// Tipo, subtipo y fechas: los mismos botones en la cartelera y en el mapa.
function FiltrosRapidos({ t, lista, f, filtros, cambiar, hoy, cargada, abrirCalendario }: {
  t: Textos; lista: Espectaculo[]; f: Filtros; filtros: Filtros; cambiar: (c: Partial<Filtros>) => void; hoy: string;
  cargada: boolean; abrirCalendario: () => void;
}) {
  const cartelera = cargada;
  const contar = (cumple: (e: Espectaculo) => boolean, ignorar: 'tipo' | 'sub') =>
    lista.reduce((n, e) => n + (cumple(e) && pasa(e, f, hoy, ignorar) ? 1 : 0), 0);
  const tipos: Filtros['tipo'][] = ['todo', 'teatro', 'magia', 'circo', 'eventos'];
  // Solo los tipos de evento que hay de verdad (sin «otros»: todo está clasificado).
  const tiposEvento = TIPOS_EVENTO.filter((k) => lista.some((e) => e.tipo === 'eventos' && e.subtipo === k));
  // Solo los géneros que hay de verdad en el teatro en cartel.
  const generos = GENEROS.filter((g) => lista.some((e) => e.tipo === 'teatro' && e.generos?.includes(g)));
  return (
    <>
      <div className="chips" role="group" aria-label={t.tiposLabel}>
        {tipos.map((k) => {
          const n = cartelera ? contar((e) => (k === 'todo' ? FUNCIONES.includes(e.tipo) : e.tipo === k), 'tipo') : null;
          return (
            <span key={k} className="chip-envoltorio">
              {k === 'eventos' ? <span className="separador" aria-hidden="true" /> : null}
              <button type="button" className="chip" aria-pressed={filtros.tipo === k}
                onClick={() => cambiar({ tipo: k, subMagia: 'todas', subEvento: 'todos', genero: 'todos' })}>
                {t.tipos[k]}{n != null ? <span className="num">{n}</span> : null}
              </button>
            </span>
          );
        })}
      </div>

      {filtros.tipo === 'magia' ? (
        <div className="chips" role="group" aria-label={t.tipoMagia}>
          {['todas', 'magia de cerca', 'magia general', 'mentalismo', 'hipnosis'].map((k) => (
            <button key={k} type="button" className="chip pequeno" aria-pressed={filtros.subMagia === k} onClick={() => cambiar({ subMagia: k })}>
              {t.subsMagia[k]}
              {cartelera ? <span className="num">{contar((e) => e.tipo === 'magia' && (k === 'todas' || (e.subtipo || 'magia general') === k), 'sub')}</span> : null}
            </button>
          ))}
        </div>
      ) : null}

      {filtros.tipo === 'teatro' && generos.length ? (
        <>
          <div className="chips" role="group" aria-label={t.generoLabel}>
            {['todos', ...generos].map((k) => (
              <button key={k} type="button" className="chip pequeno" aria-pressed={filtros.genero === k} onClick={() => cambiar({ genero: k })}>
                {k === 'todos' ? t.generoTodos : t.generos[k]}
                {cartelera ? <span className="num">{contar((e) => e.tipo === 'teatro' && (k === 'todos' || !!e.generos?.includes(k)), 'sub')}</span> : null}
              </button>
            ))}
          </div>
          {filtros.genero !== 'todos' ? <p className="nota nota-chips">{t.generoNota}</p> : null}
        </>
      ) : null}

      {filtros.tipo === 'eventos' ? (
        <div className="chips" role="group" aria-label={t.tipoEvento}>
          {['todos', ...tiposEvento].map((k) => (
            <button key={k} type="button" className="chip pequeno" aria-pressed={filtros.subEvento === k} onClick={() => cambiar({ subEvento: k })}>
              {t.subsEvento[k]}
              {cartelera ? <span className="num">{contar((e) => e.tipo === 'eventos' && (k === 'todos' || e.subtipo === k), 'sub')}</span> : null}
            </button>
          ))}
        </div>
      ) : null}

      <div className="chips" role="group" aria-label={t.cuando}>
        {(['hoy', 'manana', 'semana', 'mes'] as ClaveFecha[]).map((k) => (
          <button key={k} type="button" className="chip pequeno" aria-pressed={filtros.fecha === k}
            onClick={() => cambiar({ fecha: filtros.fecha === k ? 'todo' : k, desde: '', hasta: '' })}>
            {t.fechas[k]}
          </button>
        ))}
        <button type="button" className="chip pequeno" aria-pressed={filtros.fecha === 'rango'} aria-haspopup="dialog" onClick={abrirCalendario}>
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M4 10h16M9 3v4M15 3v4" /></svg>
          {filtros.fecha === 'rango' ? fmtRango(filtros, t) : t.fechas.rango}
        </button>
      </div>

    </>
  );
}

// «Cerca de mí»: pide la ubicación al móvil y ordena por distancia.
function BotonCerca({ t, ubic, filtros, cambiar }: {
  t: Textos; ubic: Ubicacion; filtros: Filtros; cambiar: (c: Partial<Filtros>) => void;
}) {
  const activa = ubic.estado === 'activa';
  const pulsar = () => {
    if (!activa) { ubic.activar(); cambiar({ orden: 'cerca' }); return; }
    cambiar({ orden: filtros.orden === 'cerca' ? 'fecha' : 'cerca' });
  };
  return (
    <div className="fila-ubicacion">
      <button type="button" className="chip pequeno" aria-pressed={activa && filtros.orden === 'cerca'} onClick={pulsar}
        disabled={ubic.estado === 'pidiendo'}>
        <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="3" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3" /><circle cx="12" cy="12" r="7" /></svg>
        {ubic.estado === 'pidiendo' ? t.buscandoUbic : activa ? t.masCerca : t.cercaDeMi}
      </button>
      {ubic.estado === 'denegada' ? (
        <p className="nota">{t.ubicDenegada} <a href="#mapa">{t.marcarEnMapa}</a></p>
      ) : null}
    </div>
  );
}

// Recomendaciones: lo más cercano que hay hoy y mañana (con los demás filtros).
function CercaDeTi({ t, lista, f, hoy }: { t: Textos; lista: Espectaculo[]; f: Filtros; hoy: string }) {
  const cerca = useMemo(() => (f.cerca
    ? filtrar(lista, { ...f, fecha: 'rango', desde: hoy, hasta: sumaDias(hoy, 1), orden: 'cerca', distanciaMax: f.distanciaMax ?? 3 }, hoy).slice(0, 10)
    : []), [lista, f, hoy]);
  if (!cerca.length) return null;
  return (
    <section className="cerca" aria-labelledby="titulo-cerca">
      <h3 id="titulo-cerca">{t.cercaTitulo}</h3>
      <div className="cerca-fila">
        {cerca.map((e) => {
          const [dia, hora] = e.funciones.find(([d]) => d >= hoy) ?? [hoy];
          const d = distanciaA(e, f);
          return (
            <a key={e.id} className="cerca-tarjeta" href={enlaceFicha(e.id)}>
              <span className="etiqueta suave">{tipoTxt(e, t)}</span>
              <span className="cerca-nombre">{e.nombre}</span>
              <span className="texto-suave">{[e.sala, d != null ? fmtDistancia(d) : ''].filter(Boolean).join(' · ')}</span>
              <span className="cuando">{dia === hoy ? t.fechas.hoy : t.fechas.manana}{hora ? ` · ${hora}` : ''}</span>
            </a>
          );
        })}
      </div>
    </section>
  );
}

function Etiquetas({ e, t }: { e: Espectaculo; t: Textos }) {
  const publico = publicoTxt(e, t);
  return (
    <span className="etiquetas">
      <span className={e.tipo === 'magia' || e.tema_magia ? 'etiqueta destacada' : 'etiqueta'}>
        {e.tipo === 'teatro' && e.generos?.length ? t.tipos.teatro : tipoTxt(e, t)}
      </span>
      {e.tipo === 'teatro' ? e.generos?.map((g) => <span key={g} className="etiqueta genero">{t.generos[g] || g}</span>) : null}
      {publico ? <span className="etiqueta suave">{publico}</span> : null}
      {e.nivel ? <span className="etiqueta suave">{t.nivelTxt(t.niveles[e.nivel] || e.nivel)}</span> : null}
    </span>
  );
}

function Cartel({ e, t, clase }: { e: Espectaculo; t: Textos; clase: string }) {
  const [falla, setFalla] = useState(false);
  if (!e.imagen || falla) return null;
  return (
    <img className={clase} src={e.imagen} alt={`${t.imagen} «${e.nombre}»`} width={760} height={428}
      loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={() => setFalla(true)} />
  );
}

function Tarjeta({ e, t, desde, hasta, alAbrir, guardado, dist }: {
  e: Espectaculo; t: Textos; desde: string; hasta: string; alAbrir: () => void; guardado?: boolean; dist?: number | null;
}) {
  const fs = funcionesEnRango(e, desde, hasta);
  const [dia, hora] = fs[0];
  const precio = precioTxt(e, t);
  const lugar = [e.sala, e.barrio, dist != null ? fmtDistancia(dist) : ''].filter(Boolean).join(' · ');
  return (
    <a className="tarjeta" href={enlaceFicha(e.id)} onClick={alAbrir}>
      <Cartel e={e} t={t} clase="tarjeta-imagen" />
      <span className="tarjeta-cabeza">
        <Etiquetas e={e} t={t} />
        {guardado ? <Corazon lleno /> : null}
      </span>
      <span className="tarjeta-nombre">{e.nombre}</span>
      {e.artista ? <span className="tarjeta-artista">{e.artista}</span> : null}
      {lugar ? <span className="tarjeta-lugar">{lugar}</span> : null}
      <span className="tarjeta-pie">
        <span className="cuando">{fmtDia(dia, t)}{hora ? ` · ${hora}` : ''}{fs.length > 1 ? `  +${fs.length - 1}` : ''}</span>
        {precio ? <span className="precio">{precio}</span> : null}
      </span>
    </a>
  );
}

// --- Ficha ------------------------------------------------------------------------

function Corazon({ lleno }: { lleno?: boolean }) {
  return (
    <svg className={lleno ? 'corazon lleno' : 'corazon'} aria-hidden="true" width="22" height="22" viewBox="0 0 24 24"
      fill={lleno ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinejoin="round">
      <path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" />
    </svg>
  );
}

function Ficha({ t, lang, e, hoy, volver, favs, planes, cartelera }: {
  t: Textos; lang: Idioma; e: Espectaculo; hoy: string; volver: () => void; favs: Favoritos; planes: Planes; cartelera: Cartelera;
}) {
  const guardado = favs.es(e.id);
  const [cuantas, setCuantas] = useState(6);
  const [paraPlan, setParaPlan] = useState<ItemPlan | null>(null);
  const [aviso, setAviso] = useState<{ texto: string; plan: string } | null>(null);
  useLayoutEffect(() => { window.scrollTo(0, 0); setCuantas(6); setAviso(null); }, [e.id]);
  const fs = e.funciones.filter(([f]) => f >= hoy);
  const idiomaDesc = e.descripcion?.[lang] ? lang : Object.keys(e.descripcion || {})[0];
  const desc = idiomaDesc ? e.descripcion?.[idiomaDesc] : '';
  const notaDesc = idiomaDesc && idiomaDesc !== lang ? t.textoOriginal[idiomaDesc] : '';
  const direccion = [e.direccion, e.barrio].filter(Boolean).join(' · ');
  // Solo los datos que se conocen: lo no indicado no aparece.
  const datos = [
    { etiqueta: t.precio, valor: precioTxt(e, t) },
    { etiqueta: t.duracion, valor: duracionTxt(e.duracion) },
    { etiqueta: t.publico, valor: publicoTxt(e, t) },
    { etiqueta: t.nivel, valor: e.nivel ? t.niveles[e.nivel] || e.nivel : '' },
    { etiqueta: t.idioma, valor: (e.idiomas || []).map((i) => t.idiomasFicha[i] || i).join(', ') },
  ].filter((d) => d.valor);

  return (
    <main className="pantalla">
      <div className="ficha-barra">
        <button type="button" className="boton-volver" onClick={volver} aria-label={t.volver}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 5l-7 7 7 7" /></svg>
          {t.cartelera}
        </button>
        <button type="button" className="boton-icono boton-corazon" aria-pressed={guardado}
          aria-label={guardado ? t.favQuitar : t.favGuardar} title={guardado ? t.favQuitar : t.favGuardar}
          onClick={() => favs.alternar(e.id)}>
          <Corazon lleno={guardado} />
        </button>
      </div>
      <div className="ficha">
        <Cartel e={e} t={t} clase="ficha-imagen" />
        <div className="ficha-cabecera">
          <Etiquetas e={e} t={t} />
          <h2>{e.nombre}</h2>
          {e.artista ? <span className="ficha-artista">{e.artista}</span> : null}
        </div>

        {e.sala || direccion ? (
          <section className="caja">
            <h3>{t.donde}</h3>
            {e.sala ? <span className="caja-titulo">{e.sala}</span> : null}
            {e.sala_interior ? <span className="texto-claro">{e.sala_interior}</span> : null}
            {direccion ? <span className="texto-suave">{direccion}</span> : null}
            {e.lat != null && e.lon != null ? (
              <a className="enlace" href={`https://www.google.com/maps/search/?api=1&query=${e.lat},${e.lon}`} target="_blank" rel="noopener noreferrer">{t.comoLlegar}</a>
            ) : null}
          </section>
        ) : null}

        <section className="bloque">
          <h3>{t.funciones}</h3>
          {fs.slice(0, cuantas).map(([dia, hora], i) => {
            const enPlan = planes.conFuncion(e.id, dia, hora);
            return (
              <span key={`${dia}-${hora}-${i}`} className="funcion">
                <span>{fmtDia(dia, t)}</span>
                <span className="funcion-derecha">
                  {hora ? <span className="texto-claro">{hora}</span> : null}
                  {enPlan ? (
                    <a className="boton-icono en-plan" href={`#plan-${enPlan.id}`} aria-label={t.enPlan(enPlan.nombre)} title={t.enPlan(enPlan.nombre)}>
                      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12l5 5 9-10" /></svg>
                    </a>
                  ) : (
                    <button type="button" className="boton-icono anadir-plan" aria-label={t.anadirFuncion(fmtDia(dia, t) + (hora ? ` · ${hora}` : ''))}
                      title={t.anadirFuncion(fmtDia(dia, t))}
                      onClick={() => setParaPlan(itemDe(e, dia, hora, cartelera.ciudad.id, cartelera.ciudad.zona_horaria))}>
                      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round"><path d="M12 5v14M5 12h14" /></svg>
                    </button>
                  )}
                </span>
              </span>
            );
          })}
          {fs.length > cuantas ? (
            <button type="button" className="boton-secundario ver-mas-fechas" onClick={() => setCuantas((n) => n + 20)}>
              {t.verMasFechas} <span className="texto-suave">({t.mas(fs.length - cuantas)})</span>
            </button>
          ) : null}
          {fs.length === 0 ? <span className="texto-suave">{t.sinFechas}</span> : null}
          {aviso ? (
            <p className="aviso-plan" role="status">{aviso.texto} <a href={`#plan-${aviso.plan}`}>{t.verPlan}</a></p>
          ) : null}
        </section>

        {datos.length ? (
          <div className="datos">
            {datos.map((d) => (
              <span key={d.etiqueta} className="dato">
                <span className="dato-etiqueta">{d.etiqueta}</span>
                <span className="dato-valor">{d.valor}</span>
              </span>
            ))}
          </div>
        ) : null}

        {e.compra ? <a className="boton-principal" href={e.compra} target="_blank" rel="noopener noreferrer">{t.comprar}</a> : null}

        {desc ? (
          <section className="bloque">
            <h3>{t.descripcion}</h3>
            <p className="descripcion" lang={idiomaDesc}>{desc}</p>
            {notaDesc ? <span className="nota">{notaDesc}</span> : null}
          </section>
        ) : null}

        {e.equipo?.length ? (
          <section className="bloque">
            <h3>{t.equipo}</h3>
            <dl className="equipo">
              {e.equipo.map(([papel, personas]) => (
                <div key={papel} className="equipo-fila">
                  <dt>{t.papel(papel)}</dt>
                  <dd>{personas}</dd>
                </div>
              ))}
            </dl>
          </section>
        ) : null}

        {e.tipo === 'magia' ? (
          <section className="caja discontinua">
            <h3 className="caja-titulo">{t.magoTit}</h3>
            <p className="texto-suave">{t.magoTxt}</p>
          </section>
        ) : null}

        {paraPlan ? (
          <HojaPlan t={t} item={paraPlan} planes={planes} cerrar={() => setParaPlan(null)}
            listo={(planId, nombre) => { setParaPlan(null); setAviso({ texto: t.anadido(nombre), plan: planId }); }} />
        ) : null}

        {e.fuente ? (
          <p className="nota">
            {t.fuente}: {e.fuente_url ? <a href={e.fuente_url} target="_blank" rel="noopener noreferrer">{e.fuente}</a> : e.fuente}
            {e.comprobado ? ` · ${t.comprobado} ${fmtDia(e.comprobado, t)}` : ''}
          </p>
        ) : null}
      </div>
    </main>
  );
}

// --- Hojas que suben desde abajo («Más filtros» y el calendario) ------------------------

function useHoja(cerrar: () => void, primero: RefObject<HTMLElement | null>) {
  const alCerrar = useRef(cerrar);
  alCerrar.current = cerrar;
  useEffect(() => {
    const anterior = document.activeElement as HTMLElement | null;
    primero.current?.focus({ preventScroll: true });
    // Mientras la hoja está abierta, la página de detrás no se mueve.
    const desbordamiento = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const tecla = (ev: KeyboardEvent) => { if (ev.key === 'Escape') alCerrar.current(); };
    window.addEventListener('keydown', tecla);
    return () => {
      window.removeEventListener('keydown', tecla);
      document.body.style.overflow = desbordamiento;
      anterior?.focus({ preventScroll: true });
    };
  }, [primero]);
}

function BotonCerrar({ t, cerrar, refBoton }: { t: Textos; cerrar: () => void; refBoton: RefObject<HTMLButtonElement | null> }) {
  return (
    <button ref={refBoton} type="button" className="boton-icono relleno" onClick={cerrar} aria-label={t.cerrar}>
      <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
    </button>
  );
}

// Calendario: de este mes a dos años vista; se elige un día o del primer día al último.
function HojaCalendario({ t, lista, hoy, filtros, cambiar, cerrar }: {
  t: Textos; lista: Espectaculo[]; hoy: string; filtros: Filtros; cambiar: (c: Partial<Filtros>) => void; cerrar: () => void;
}) {
  const primero = useRef<HTMLButtonElement>(null);
  const mesElegido = useRef<HTMLDivElement>(null);
  useHoja(cerrar, primero);
  const [desde, setDesde] = useState(filtros.fecha === 'rango' ? filtros.desde : '');
  const [hasta, setHasta] = useState(filtros.fecha === 'rango' ? filtros.hasta : '');
  const fin = hasta || desde;

  // Días con funciones según los demás filtros (tipo, precio, público…).
  const conFunciones = useMemo(() => {
    const dias = new Set<string>();
    for (const e of lista) if (pasa(e, filtros, hoy, 'fecha')) for (const [d] of e.funciones) if (d >= hoy) dias.add(d);
    return dias;
  }, [lista, filtros, hoy]);
  const n = useMemo(() => filtrar(lista, { ...filtros, fecha: desde ? 'rango' : 'todo', desde, hasta: fin }, hoy).length,
    [lista, filtros, hoy, desde, fin]);

  useEffect(() => { mesElegido.current?.scrollIntoView({ block: 'start' }); }, []);

  const elegir = (d: string) => {
    if (!desde || hasta) { setDesde(d); setHasta(''); return; }
    if (d < desde) { setHasta(desde); setDesde(d); } else setHasta(d);
  };
  const aplicar = () => { cambiar({ fecha: desde ? 'rango' : 'todo', desde, hasta: fin }); cerrar(); };

  const [anio0, mes0] = hoy.split('-').map(Number);
  const meses = Array.from({ length: MESES_CALENDARIO + 1 }, (_, i) => {
    const total = mes0 - 1 + i;
    return { anio: anio0 + Math.floor(total / 12), mes: total % 12 };
  });
  const pad = (x: number) => String(x).padStart(2, '0');

  return (
    <div className="fondo-hoja" onClick={(ev) => { if (ev.target === ev.currentTarget) cerrar(); }}>
      <div className="hoja" role="dialog" aria-modal="true" aria-labelledby="titulo-calendario">
        <div className="hoja-cabecera">
          <div className="calendario-titulo">
            <h2 id="titulo-calendario">{t.calTitulo}</h2>
            <span className="cuando" aria-live="polite">{desde ? t.calDel(fmtCorto(desde, t), fmtCorto(fin, t)) : ' '}</span>
          </div>
          <BotonCerrar t={t} cerrar={cerrar} refBoton={primero} />
        </div>
        <div className="hoja-cuerpo calendario">
          <p className="nota">{t.calAyuda} {t.calPuntos}</p>
          {meses.map(({ anio, mes }) => {
            const primeroDelMes = `${anio}-${pad(mes + 1)}-01`;
            const dias = new Date(Date.UTC(anio, mes + 1, 0)).getUTCDate();
            const hueco = (new Date(Date.UTC(anio, mes, 1)).getUTCDay() + 6) % 7; // la semana empieza el lunes
            const contieneDesde = desde.startsWith(primeroDelMes.slice(0, 7));
            return (
              <div key={primeroDelMes} className="mes" ref={contieneDesde ? mesElegido : undefined}>
                <h3>{t.mesesLargos[mes]} {anio}</h3>
                <div className="semana" aria-hidden="true">{t.diasCortos.map((d) => <span key={d}>{d}</span>)}</div>
                <div className="dias">
                  {Array.from({ length: hueco }, (_, i) => <span key={`h${i}`} />)}
                  {Array.from({ length: dias }, (_, i) => {
                    const iso = `${anio}-${pad(mes + 1)}-${pad(i + 1)}`;
                    const pasado = iso < hoy;
                    const extremo = iso === desde || iso === fin;
                    const dentro = !!desde && iso > desde && iso < fin;
                    const clases = ['dia', extremo ? 'extremo' : '', dentro ? 'dentro' : '', iso === hoy ? 'hoy' : '',
                      conFunciones.has(iso) ? 'con-funciones' : ''].filter(Boolean).join(' ');
                    return (
                      <button key={iso} type="button" className={clases} disabled={pasado} aria-pressed={extremo || dentro}
                        aria-label={fmtDia(iso, t)} onClick={() => elegir(iso)}>
                        {i + 1}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
        <div className="hoja-botones">
          <button type="button" className="boton-secundario" onClick={() => { setDesde(''); setHasta(''); }}>{t.calQuitar}</button>
          <button type="button" className="boton-principal" onClick={aplicar}>{t.ver(n)}</button>
        </div>
      </div>
    </div>
  );
}

// --- Más filtros ----------------------------------------------------------------------

function HojaFiltros({ t, lista, hoy, filtros, cambiar, cerrar, ubic }: {
  t: Textos; lista: Espectaculo[]; hoy: string; filtros: Filtros; cambiar: (c: Partial<Filtros>) => void; cerrar: () => void;
  ubic: Ubicacion;
}) {
  const primero = useRef<HTMLButtonElement>(null);
  const n = useMemo(() => filtrar(lista, filtros, hoy).length, [lista, filtros, hoy]);
  const indefinido = filtros.precioMax == null;
  const precioTxtFiltro = indefinido ? t.indefinido : t.hasta(filtros.precioMax as number);

  useHoja(cerrar, primero);

  const opciones = (clave: 'publico' | 'idioma', valores: string[], textos: Record<string, string>) => (
    <div className="opciones">
      {valores.map((v) => (
        <button key={v} type="button" className="chip pequeno" aria-pressed={filtros[clave] === v} onClick={() => cambiar({ [clave]: v })}>{textos[v]}</button>
      ))}
    </div>
  );

  return (
    <div className="fondo-hoja" onClick={(ev) => { if (ev.target === ev.currentTarget) cerrar(); }}>
      <div className="hoja" role="dialog" aria-modal="true" aria-labelledby="titulo-filtros">
        <div className="hoja-cabecera">
          <h2 id="titulo-filtros">{t.filtros}</h2>
          <BotonCerrar t={t} cerrar={cerrar} refBoton={primero} />
        </div>

        <div className="hoja-cuerpo">
        <div className="grupo" role="group" aria-labelledby="titulo-precio">
          <h3 id="titulo-precio">{t.grupoPrecio}</h3>
          <div className="precio-fila">
            <label htmlFor="precio-max">{t.precioMax}</label>
            <span className="cuando">{precioTxtFiltro}</span>
          </div>
          <input id="precio-max" type="range" min={0} max={PRECIO_TOPE} step={5} value={indefinido ? PRECIO_TOPE : (filtros.precioMax as number)}
            aria-valuetext={precioTxtFiltro}
            onChange={(ev) => { const v = Number(ev.target.value); cambiar({ precioMax: v >= PRECIO_TOPE ? null : v }); }} />
          <div className="precio-extremos"><span>0 €</span><span>{t.indefinido}</span></div>
          <label htmlFor="sin-precio" className={indefinido ? 'casilla desactivada' : 'casilla'}>
            <input id="sin-precio" type="checkbox" checked={indefinido || filtros.sinPrecio} disabled={indefinido}
              onChange={(ev) => cambiar({ sinPrecio: ev.target.checked })} />
            <span>{t.sinPrecio}</span>
          </label>
        </div>

        <div className="grupo" role="group" aria-labelledby="titulo-distancia">
          <h3 id="titulo-distancia">{t.grupoDistancia}</h3>
          {filtros.cerca ? (
            <>
              <div className="opciones">
                {[null, 1, 2, 5].map((km) => (
                  <button key={String(km)} type="button" className="chip pequeno" aria-pressed={filtros.distanciaMax === km}
                    onClick={() => cambiar({ distanciaMax: km })}>{t.distancias[km == null ? 'cualquiera' : String(km)]}</button>
                ))}
              </div>
              <button type="button" className="enlace boton-texto" onClick={ubic.apagar}>{t.quitarUbic}</button>
            </>
          ) : <span className="nota">{t.distanciaSinUbic}</span>}
          <span className="nota">{t.ubicPrivada}</span>
        </div>

        <div className="grupo" role="group" aria-labelledby="titulo-publico">
          <h3 id="titulo-publico">{t.grupoPublico}</h3>
          {opciones('publico', ['cualquiera', 'infantil', 'familiar', 'juvenil', 'adultos'], t.publicos)}
        </div>

        <div className="grupo" role="group" aria-labelledby="titulo-idioma">
          <h3 id="titulo-idioma">{t.grupoIdioma}</h3>
          {opciones('idioma', ['catalan', 'castellano', 'ingles', 'cualquiera'], t.idiomas)}
          <span className="nota">{t.notaIdioma}</span>
        </div>
        </div>

        <div className="hoja-botones">
          <button type="button" className="boton-secundario" onClick={() => cambiar({ precioMax: null, sinPrecio: false, publico: 'cualquiera', idioma: 'cualquiera' })}>{t.borrar}</button>
          <button type="button" className="boton-principal" onClick={cerrar}>{t.ver(n)}</button>
        </div>
      </div>
    </div>
  );
}

// --- Mapa de salas ---------------------------------------------------------------------

function VistaMapa({ t, cartelera, hoy, filtros, cambiar, abrirCalendario, favs, ubic }: {
  t: Textos; cartelera: Cartelera | null; hoy: string; filtros: Filtros; cambiar: (c: Partial<Filtros>) => void;
  abrirCalendario: () => void; favs: Favoritos; ubic: Ubicacion;
}) {
  const [marcando, setMarcando] = useState(false);
  const zonaMapa = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => { window.scrollTo(0, 0); }, []);
  const lista = cartelera?.espectaculos ?? [];
  const resultados = useMemo(() => (cartelera ? filtrar(lista, filtros, hoy) : []), [cartelera, lista, filtros, hoy]);
  const salas = useMemo(() => agruparSalas(resultados), [resultados]);
  const [elegida, setElegida] = useState<string | null>(null);
  const sala = salas.find((s) => s.id === elegida) ?? null;
  const [desde, hasta] = rango(filtros, hoy);
  const panel = useRef<HTMLDivElement>(null);
  const elegir = (id: string | null) => {
    setElegida(id);
    if (id) requestAnimationFrame(() => panel.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  };

  return (
    <main className="pantalla">
      <header className="cabecera">
        <div className="titulo">
          <span className="sobretitulo">{cartelera ? `${cartelera.ciudad.nombre} · ${t.salas(salas.length)}` : 'Barcelona'}</span>
          <h1>{t.mapaTit}</h1>
        </div>
      </header>
      <FiltrosRapidos t={t} lista={lista} f={filtros} filtros={filtros} cambiar={(c) => { setElegida(null); cambiar(c); }}
        hoy={hoy} cargada={!!cartelera} abrirCalendario={abrirCalendario} />
      <div className="lista">
        <p className="nota">{t.mapaTxt}</p>
        <div className="fila-ubicacion">
          <button type="button" className="chip pequeno" onClick={ubic.activar} disabled={ubic.estado === 'pidiendo'}
            aria-pressed={ubic.pos?.origen === 'gps'}>
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="3" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3" /><circle cx="12" cy="12" r="7" /></svg>
            {ubic.estado === 'pidiendo' ? t.buscandoUbic : t.miUbicacion}
          </button>
          <button type="button" className="chip pequeno" aria-pressed={marcando} onClick={() => {
            setMarcando(!marcando);
            if (!marcando) zonaMapa.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }}>
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z" /><circle cx="12" cy="10" r="2" /></svg>
            {marcando ? t.marcando : t.marcarEnMapa}
          </button>
        </div>
        {ubic.estado === 'denegada' && !ubic.pos ? <p className="nota">{t.ubicDenegada}</p> : null}
        <div ref={zonaMapa} className="zona-mapa">{cartelera ? (
          <MapaSalas t={t} salas={salas} elegida={elegida} elegir={elegir} ciudad={cartelera.ciudad.id}
            posicion={ubic.pos} marcando={marcando}
            alMarcar={(lat, lon) => { ubic.fijar(lat, lon); setMarcando(false); cambiar({ orden: 'cerca' }); }} />
        ) : <p className="aviso">{t.cargando}</p>}</div>
        <p className="nota">{t.ubicPrivada}</p>
        <div ref={panel} className="panel-sala">
          {sala ? (
            <>
              <section className="caja">
                <h3>{t.donde}</h3>
                <span className="caja-titulo">{sala.nombre}</span>
                <span className="texto-suave">{[sala.direccion, sala.barrio].filter(Boolean).join(' · ')}</span>
                <span className="texto-claro">{t.resultados(sala.espectaculos.length)}</span>
                <a className="enlace" href={`https://www.google.com/maps/search/?api=1&query=${sala.lat},${sala.lon}`} target="_blank" rel="noopener noreferrer">{t.comoLlegar}</a>
              </section>
              {sala.espectaculos.map((e) => (
                <Tarjeta key={e.id} e={e} t={t} desde={desde} hasta={hasta} alAbrir={() => {}} guardado={favs.es(e.id)} />
              ))}
            </>
          ) : (
            <section className="bloque">
              <h3>{filtros.cerca ? t.salasCerca : t.masSalas}</h3>
              {(filtros.cerca ? [...salas].sort((a, b) => distanciaA(a.espectaculos[0], filtros)! - distanciaA(b.espectaculos[0], filtros)!) : salas)
                .slice(0, 12).map((s) => {
                  const d = distanciaA(s.espectaculos[0], filtros);
                  return (
                    <button key={s.id} type="button" className="fila-sala" onClick={() => elegir(s.id)}>
                      <span>
                        <span className="caja-titulo">{s.nombre}</span>
                        <span className="texto-suave"> · {[s.barrio, d != null ? fmtDistancia(d) : ''].filter(Boolean).join(' · ')}</span>
                      </span>
                      <span className="num-sala">{s.espectaculos.length}</span>
                    </button>
                  );
                })}
            </section>
          )}
        </div>
      </div>
    </main>
  );
}

// --- Favoritos ----------------------------------------------------------------------------

function VistaFavoritos({ t, lista, hoy, favs }: { t: Textos; lista: Espectaculo[]; hoy: string; favs: Favoritos }) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, []);
  const guardados = lista.filter((e) => favs.es(e.id) && e.funciones.some(([d]) => d >= hoy))
    .sort((a, b) => (a.funciones.find(([d]) => d >= hoy)?.[0] ?? '').localeCompare(b.funciones.find(([d]) => d >= hoy)?.[0] ?? ''));
  const fuera = lista.length ? favs.ids.length - guardados.length : 0;
  return (
    <main className="pantalla">
      <header className="cabecera">
        <div className="titulo">
          <span className="sobretitulo">{t.resultados(guardados.length)}</span>
          <h1>{t.favTit}</h1>
        </div>
      </header>
      <div className="lista">
        {guardados.length === 0 ? <p className="aviso">{t.favVacio}</p> : null}
        {guardados.map((e) => (
          <Tarjeta key={e.id} e={e} t={t} desde={hoy} hasta="9999-12-31" alAbrir={() => {}} guardado />
        ))}
        {fuera > 0 ? <p className="nota">{t.favFuera(fuera)}</p> : null}
        <p className="nota">{t.favNota}</p>
      </div>
    </main>
  );
}

// --- Planes (itinerarios): qué ver, qué día y dónde ---------------------------------------

function rangoPlan(p: Plan, t: Textos): string {
  if (!p.items.length) return '';
  const dias = p.items.map((i) => i.dia).sort();
  const a = dias[0], b = dias[dias.length - 1];
  return a === b ? fmtDia(a, t) : `${fmtCorto(a, t)} – ${fmtCorto(b, t)}`;
}

function planTexto(p: Plan, t: Textos): string {
  const lineas = [p.nombre, ''];
  for (const [dia, items] of porDias(p.items)) {
    lineas.push(fmtDia(dia, t));
    for (const i of items) {
      const lugar = [i.sala, i.direccion].filter(Boolean).join(', ');
      lineas.push(`· ${i.hora || t.planSinHora} — ${i.nombre}${lugar ? ` (${lugar})` : ''}`);
    }
    lineas.push('');
  }
  return lineas.join('\n').trim();
}

const nombreArchivo = (s: string) =>
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '').toLowerCase() || 'plan';

function FormNuevoPlan({ t, alCrear, boton, inicial = '' }: {
  t: Textos; alCrear: (nombre: string) => void; boton: string; inicial?: string;
}) {
  const [nombre, setNombre] = useState(inicial);
  const enviar = (ev: FormEvent) => { ev.preventDefault(); alCrear(nombre.trim() || t.planNombrePorDefecto); };
  return (
    <form className="plan-nuevo" onSubmit={enviar}>
      <label htmlFor="nombre-plan" className="dato-etiqueta">{t.planNombre}</label>
      <input id="nombre-plan" className="campo" value={nombre} onChange={(ev) => setNombre(ev.target.value)}
        placeholder={t.planNombreEj} maxLength={60} enterKeyHint="done" />
      <button type="submit" className="boton-principal">{boton}</button>
    </form>
  );
}

// Hoja para elegir a qué plan va una función (o crear uno nuevo).
function HojaPlan({ t, item, planes, cerrar, listo }: {
  t: Textos; item: ItemPlan; planes: Planes; cerrar: () => void; listo: (planId: string, nombre: string) => void;
}) {
  const primero = useRef<HTMLButtonElement>(null);
  useHoja(cerrar, primero);
  const [nuevo, setNuevo] = useState(planes.planes.length === 0);
  return (
    <div className="fondo-hoja" onClick={(ev) => { if (ev.target === ev.currentTarget) cerrar(); }}>
      <div className="hoja hoja-baja" role="dialog" aria-modal="true" aria-labelledby="titulo-hoja-plan">
        <div className="hoja-cabecera">
          <div className="calendario-titulo">
            <h2 id="titulo-hoja-plan">{t.elegirPlan}</h2>
            <span className="cuando">{item.nombre} · {fmtDia(item.dia, t)}{item.hora ? ` · ${item.hora}` : ''}</span>
          </div>
          <BotonCerrar t={t} cerrar={cerrar} refBoton={primero} />
        </div>
        <div className="hoja-cuerpo">
          {planes.planes.map((p) => (
            <button key={p.id} type="button" className="plan-opcion"
              onClick={() => { planes.anadir(p.id, item); listo(p.id, p.nombre); }}>
              <span className="caja-titulo">{p.nombre}</span>
              <span className="texto-suave">{[t.planFunciones(p.items.length), rangoPlan(p, t)].filter(Boolean).join(' · ')}</span>
            </button>
          ))}
          {nuevo ? (
            <FormNuevoPlan t={t} boton={t.planCrear} alCrear={(nombre) => listo(planes.crear(nombre, item), nombre)} />
          ) : (
            <button type="button" className="boton-secundario" onClick={() => setNuevo(true)}>+ {t.planNuevo}</button>
          )}
        </div>
      </div>
    </div>
  );
}

function VistaPlanes({ t, planes }: { t: Textos; planes: Planes }) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, []);
  const [creando, setCreando] = useState(false);
  return (
    <main className="pantalla">
      <header className="cabecera">
        <div className="titulo">
          <span className="sobretitulo">{planes.planes.length ? t.planFunciones(planes.planes.reduce((n, p) => n + p.items.length, 0)) : ' '}</span>
          <h1>{t.planesTit}</h1>
        </div>
      </header>
      <div className="lista">
        <p className="texto-suave">{t.planesIntro}</p>
        {planes.planes.length === 0 ? <p className="aviso">{t.planesVacio}</p> : null}
        {planes.planes.map((p) => (
          <a key={p.id} className="tarjeta plan-tarjeta" href={`#plan-${p.id}`}>
            <span className="tarjeta-nombre">{p.nombre}</span>
            <span className="tarjeta-lugar">{[t.planFunciones(p.items.length), rangoPlan(p, t)].filter(Boolean).join(' · ')}</span>
            {p.items.length ? (
              <span className="texto-suave plan-resumen">{p.items.slice(0, 3).map((i) => i.nombre).join(' · ')}{p.items.length > 3 ? ' …' : ''}</span>
            ) : null}
          </a>
        ))}
        {creando ? (
          <FormNuevoPlan t={t} boton={t.planCrearSolo} alCrear={(nombre) => { window.location.hash = `#plan-${planes.crear(nombre)}`; }} />
        ) : (
          <button type="button" className="boton-secundario" onClick={() => setCreando(true)}>+ {t.planNuevo}</button>
        )}
        <p className="nota">{t.planNota}</p>
      </div>
    </main>
  );
}

function VistaPlan({ t, lista, hoy, planes, id }: { t: Textos; lista: Espectaculo[]; hoy: string; planes: Planes; id: string }) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, [id]);
  const [editando, setEditando] = useState(false);
  const [borrando, setBorrando] = useState(false);
  const [copiado, setCopiado] = useState(false);
  const enCartel = useMemo(() => new Set(lista.map((e) => e.id)), [lista]);
  const plan = planes.planes.find((p) => p.id === id);
  const barra = (
    <div className="ficha-barra">
      <a className="boton-volver" href="#planes">
        <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 5l-7 7 7 7" /></svg>
        {t.volverPlanes}
      </a>
    </div>
  );
  if (!plan) return <main className="pantalla">{barra}<div className="ficha"><p className="aviso">{t.planesVacio}</p></div></main>;

  const choques = solapes(plan.items);
  const enlace = (i: ItemPlan) => `${window.location.origin}${window.location.pathname}${enlaceFicha(i.id)}`;
  const compartir = async () => {
    const texto = planTexto(plan, t);
    if (navigator.share) {
      try { await navigator.share({ title: plan.nombre, text: texto }); return; } catch { /* cancelado o no permitido: copiar */ }
    }
    try { await navigator.clipboard.writeText(texto); setCopiado(true); } catch { /* sin portapapeles */ }
  };

  return (
    <main className="pantalla">
      {barra}
      <div className="ficha">
        <div className="ficha-cabecera">
          {editando ? (
            <FormNuevoPlan t={t} boton={t.planGuardar} inicial={plan.nombre}
              alCrear={(nombre) => { planes.renombrar(plan.id, nombre); setEditando(false); }} />
          ) : <h2>{plan.nombre}</h2>}
          <span className="texto-suave">{[t.planFunciones(plan.items.length), rangoPlan(plan, t)].filter(Boolean).join(' · ')}</span>
        </div>

        {plan.items.length === 0 ? <p className="aviso">{t.planVacio}</p> : null}

        {porDias(plan.items).map(([dia, items]) => {
          const ruta = enlaceRuta(items);
          return (
            <section key={dia} className={dia < hoy ? 'bloque plan-dia pasado' : 'bloque plan-dia'}>
              <h3>{fmtDia(dia, t)}{dia < hoy ? ` · ${t.planPasado}` : ''}</h3>
              {items.map((i) => {
                const k = claveItem(i);
                const choque = choques.get(k);
                const lugar = [i.sala, i.direccion, i.barrio].filter(Boolean).join(' · ');
                return (
                  <div key={k} className="plan-item">
                    <span className="plan-hora">{i.hora || '—'}</span>
                    <span className="plan-info">
                      {enCartel.has(i.id) ? <a className="caja-titulo" href={enlaceFicha(i.id)}>{i.nombre}</a> : <span className="caja-titulo">{i.nombre}</span>}
                      {!i.hora ? <span className="texto-suave">{t.planSinHora}</span> : null}
                      {lugar ? <span className="texto-suave">{lugar}</span> : null}
                      {choque ? <span className="plan-choque">{t.planSolape(choque)}</span> : null}
                      {!enCartel.has(i.id) && dia >= hoy && lista.length ? <span className="nota">{t.planFuera}</span> : null}
                      {i.lat != null && i.lon != null ? (
                        <a className="enlace" href={`https://www.google.com/maps/search/?api=1&query=${i.lat},${i.lon}`} target="_blank" rel="noopener noreferrer">{t.comoLlegar}</a>
                      ) : null}
                    </span>
                    <button type="button" className="boton-icono" aria-label={`${t.planQuitar}: ${i.nombre}`} title={t.planQuitar}
                      onClick={() => planes.quitar(plan.id, k)}>
                      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
                    </button>
                  </div>
                );
              })}
              {ruta ? <a className="enlace" href={ruta} target="_blank" rel="noopener noreferrer">{t.planRuta}</a> : null}
            </section>
          );
        })}

        {plan.items.length ? (
          <div className="plan-acciones">
            <button type="button" className="boton-principal"
              onClick={() => descargar(`${nombreArchivo(plan.nombre)}.ics`, planIcs(plan, enlace), 'text/calendar')}>
              {t.planCalendario}
            </button>
            <button type="button" className="boton-secundario" onClick={compartir}>{t.planCompartir}</button>
          </div>
        ) : null}
        {copiado ? <p className="nota" role="status">{t.planCopiado}</p> : null}

        <div className="plan-acciones">
          {!editando ? <button type="button" className="boton-secundario" onClick={() => setEditando(true)}>{t.planRenombrar}</button> : null}
          {borrando ? (
            <button type="button" className="boton-secundario peligro"
              onClick={() => { planes.borrar(plan.id); window.location.hash = '#planes'; }}>{t.planBorrarSeguro}</button>
          ) : (
            <button type="button" className="boton-secundario" onClick={() => setBorrando(true)}>{t.planBorrar}</button>
          )}
        </div>
        <p className="nota">{t.planNota}</p>
      </div>
    </main>
  );
}
