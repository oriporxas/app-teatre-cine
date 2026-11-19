import { useCallback, useDeferredValue, useEffect, useLayoutEffect, useMemo, useRef, useState, type FormEvent, type RefObject } from 'react';
import { cargarCartelera, type Cartelera, type Espectaculo } from './datos';
import {
  FILTROS_INICIALES, FUNCIONES, GENEROS, MESES_CALENDARIO, guardarOcultos, PRECIO_TOPE, TIPOS_EVENTO, cuantosFiltros, duracionTxt, filtrar,
  distanciaA, fmtCorto, fmtDia, fmtDistancia, fmtRango, funcionesEnRango, hoyEn, pasa, vigentes, precioTxt, publicoTxt, rango,
  sumaDias, tipoTxt,
  type ClaveFecha, type Filtros,
} from './filtros';
import { TEXTOS, guardarIdioma, idiomaInicial, type Idioma, type Textos } from './textos';
import { useFavoritos, type Favoritos } from './favoritos';
import { claveObra, clavePeli, clavePlan, marca, useHistorial, type Clase, type Hecho, type Historial } from './historial';
import { useUbicacion, type Ubicacion } from './ubicacion';
import { MapaSalas, agruparSalas } from './Mapa';
import {
  abrirRutaEnMovil, claveItem, descargar, imagenPlan, itemDe, paradasRuta, planIcs, porDias, rutaIncrustada, solapes, usePlanes,
  type ItemPlan, type Plan, type Planes,
} from './planes';
import { FILTROS_CINE, cargarCine, horaAhora, type CarteleraCine, type FiltrosCine } from './cine';
import { Cartelito, FichaCine, FichaPelicula, VistaCine, VistaMapaCine, enlacePeli } from './Cine';
import { VistaNoticias, cargarNoticias, type Noticia } from './Noticias';
import { VistaInicio } from './Inicio';
import { VistaBuscar, VistaPersona, indicePersonas, separarNombres, slug } from './Buscar';

const POR_PAGINA = 40;

// --- Rutas: la dirección dice qué pantalla se ve, así funciona el botón «atrás» del móvil.
// Solo letras, números y guiones (#mapa, #ficha-open-data-bcn-994…), para que el enlace
// funcione en cualquier sitio donde se publique la app.
type Ruta = { vista: 'inicio' } | { vista: 'cartelera' } | { vista: 'ficha'; clave: string } | { vista: 'mapa' } | { vista: 'favoritos' }
  | { vista: 'planes' } | { vista: 'plan'; id: string } | { vista: 'cine' } | { vista: 'peli'; id: string } | { vista: 'sala'; id: string }
  | { vista: 'mapa-cine' } | { vista: 'noticias' } | { vista: 'buscar' } | { vista: 'persona'; id: string }
  | { vista: 'teatro'; id: string } | { vista: 'historial' };

const claveFicha = (id: string) => id.replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '');

function leerRuta(): Ruta {
  const h = window.location.hash.replace(/^#\/?/, '');
  if (h.startsWith('ficha-')) return { vista: 'ficha', clave: h.slice(6) };
  if (h.startsWith('peli-')) return { vista: 'peli', id: h.slice(5) };
  if (h.startsWith('sala-')) return { vista: 'sala', id: h.slice(5) };
  if (h.startsWith('teatro-')) return { vista: 'teatro', id: h.slice(7) };
  if (h.startsWith('persona-')) return { vista: 'persona', id: h.slice(8) };
  if (h === 'cartelera') return { vista: 'cartelera' };
  if (h === 'cine') return { vista: 'cine' };
  if (h === 'mapa-cine') return { vista: 'mapa-cine' };
  if (h === 'noticias') return { vista: 'noticias' };
  if (h === 'buscar') return { vista: 'buscar' };
  if (h === 'mapa') return { vista: 'mapa' };
  if (h === 'favoritos') return { vista: 'favoritos' };
  if (h === 'planes') return { vista: 'planes' };
  if (h === 'historial') return { vista: 'historial' };
  if (h.startsWith('plan-')) return { vista: 'plan', id: h.slice(5) };
  return { vista: 'inicio' };
}

const enlaceFicha = (id: string) => `#ficha-${claveFicha(id)}`;
/** Página de una sala de teatro (con todo lo que tiene en cartel). */
export const enlaceSala = (id: string) => `#teatro-${claveFicha(id)}`;

export default function App() {
  const [lang, setLang] = useState<Idioma>(idiomaInicial);
  const [ruta, setRuta] = useState<Ruta>(leerRuta);
  const [cartelera, setCartelera] = useState<Cartelera | null>(null);
  const [error, setError] = useState(false);
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_INICIALES);
  const [hoja, setHoja] = useState<null | 'filtros' | 'calendario'>(null);
  const [limite, setLimite] = useState(POR_PAGINA);
  const [cine, setCine] = useState<CarteleraCine | null>(null);
  const [errorCine, setErrorCine] = useState(false);
  const [noticias, setNoticias] = useState<Noticia[] | null>(null);
  const [errorNoticias, setErrorNoticias] = useState(false);
  const [filtrosCine, setFiltrosCine] = useState<FiltrosCine>(FILTROS_CINE);
  const [busqueda, setBusqueda] = useState('');
  const [reloj, setReloj] = useState(0);
  const navegado = useRef(false);
  const scrollLista = useRef(0);
  const t = TEXTOS[lang];
  const favs = useFavoritos();
  const ubic = useUbicacion();
  const planes = usePlanes();
  const hist = useHistorial();
  // «Agenda» abre el último apartado usado (Planes, Guardado o Historial).
  const [agenda, setAgenda] = useState<string>(() => { try { return localStorage.getItem('agenda') || '#planes'; } catch { return '#planes'; } });
  useEffect(() => {
    const h = { planes: '#planes', plan: '#planes', favoritos: '#favoritos', historial: '#historial' }[ruta.vista as string];
    if (h) { setAgenda(h); try { localStorage.setItem('agenda', h); } catch { /* sin almacenamiento */ } }
  }, [ruta.vista]);
  // La ubicación entra en los filtros (para la distancia y el orden «más cerca»).
  useEffect(() => {
    setFiltros((f) => (ubic.pos
      ? { ...f, cerca: { lat: ubic.pos.lat, lon: ubic.pos.lon } }
      : { ...f, cerca: null, orden: 'fecha', distanciaMax: null }));
  }, [ubic.pos]);

  useEffect(() => {
    let cargado = 0;
    const cargar = () => {
      cargado = Date.now();
      cargarCartelera('barcelona').then(setCartelera).catch(() => setError(true));
      cargarCine('barcelona').then(setCine).catch(() => setErrorCine(true));
      cargarNoticias('barcelona').then(setNoticias).catch(() => setErrorNoticias(true));
    };
    cargar();
    // La hora avanza: «empieza pronto» y lo que ya ha empezado se recalcula cada minuto.
    const id = window.setInterval(() => setReloj((n) => n + 1), 60000);
    // Al volver a la app (el móvil la deja abierta en segundo plano), si han pasado más de 30 minutos,
    // se descarga la cartelera otra vez por si ha habido actualización.
    const alVolver = () => {
      if (document.visibilityState !== 'visible') return;
      setReloj((n) => n + 1);
      if (Date.now() - cargado > 30 * 60000) cargar();
    };
    document.addEventListener('visibilitychange', alVolver);
    return () => { window.clearInterval(id); document.removeEventListener('visibilitychange', alVolver); };
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

  const zona = cartelera?.ciudad.zona_horaria || 'Europe/Madrid';
  const hoy = hoyEn(zona);
  const ahora = useMemo(() => horaAhora(zona), [zona, reloj]); // eslint-disable-line react-hooks/exhaustive-deps
  // Lo que ya ha empezado o pasado desaparece al momento (se recalcula cada minuto).
  const lista = useMemo(() => vigentes(cartelera?.espectaculos ?? [], hoy, ahora), [cartelera, hoy, ahora]);
  const vigente = useMemo(() => (cartelera ? { ...cartelera, espectaculos: lista } : null), [cartelera, lista]);
  // La ficha se abre aunque la obra ya no esté en cartel (desde un plan o el historial).
  const actual = ruta.vista === 'ficha'
    ? (lista.find((e) => claveFicha(e.id) === ruta.clave) ?? cartelera?.espectaculos.find((e) => claveFicha(e.id) === ruta.clave))
    : undefined;
  const peli = ruta.vista === 'peli' ? cine?.peliculas.find((p) => enlacePeli(p.id) === `#peli-${ruta.id}`) : undefined;
  const salaCine = ruta.vista === 'sala' ? cine?.cines.find((c) => c.id.replace(/[^A-Za-z0-9-]+/g, '-') === ruta.id) : undefined;
  const personas = useMemo(() => indicePersonas(lista, cine, lang, t, cartelera?.personas), [lista, cine, lang, t, cartelera]);
  const cambiarCine = useCallback((c: Partial<FiltrosCine>) => setFiltrosCine((f) => ({ ...f, ...c })), []);
  const idsPelis = useMemo(() => new Set((cine?.peliculas || []).map((p) => p.id)), [cine]);

  return (
    <div className="app">
      {ruta.vista === 'inicio' ? (
        <VistaInicio t={t} lang={lang} setLang={setLang} cartelera={vigente} cine={cine} noticias={noticias} hoy={hoy} ahora={ahora}
          irABuscar={() => { window.location.hash = '#buscar'; }} />
      ) : null}
      {ruta.vista === 'cine' ? (
        <VistaCine t={t} lang={lang} datos={cine} error={errorCine} hoy={hoy} ahora={ahora} favs={favs} hist={hist} ubic={ubic}
          filtros={filtrosCine} cambiar={cambiarCine} />
      ) : null}
      {ruta.vista === 'peli' && peli && cine ? (
        <FichaPelicula t={t} lang={lang} p={peli} datos={cine} hoy={hoy} ahora={ahora} volver={volver} favs={favs} planes={planes}
          hist={hist} zona={zona} ciudad="barcelona" />
      ) : null}
      {ruta.vista === 'peli' && cine && !peli ? <main className="pantalla"><p className="aviso">{t.sinResultados}</p></main> : null}
      {ruta.vista === 'sala' && salaCine && cine ? <FichaCine t={t} lang={lang} c={salaCine} datos={cine} hoy={hoy} ahora={ahora} volver={volver} /> : null}
      {ruta.vista === 'mapa-cine' ? <VistaMapaCine t={t} datos={cine} hoy={hoy} ubic={ubic} /> : null}
      {ruta.vista === 'noticias' ? <VistaNoticias t={t} lang={lang} noticias={noticias} error={errorNoticias} /> : null}
      {ruta.vista === 'buscar' ? <VistaBuscar t={t} lang={lang} q={busqueda} setQ={setBusqueda} lista={lista} cine={cine} personas={personas} hoy={hoy} /> : null}
      {ruta.vista === 'persona' ? <VistaPersona t={t} p={personas.get(ruta.id) || [...personas.values()].find((x) => `n-${slug(x.nombre)}` === ruta.id)} volver={volver} /> : null}
      {ruta.vista === 'cartelera' || (ruta.vista === 'ficha' && !actual) ? (
        <VistaCartelera
          t={t} lang={lang} setLang={setLang} cartelera={vigente} error={error} hoy={hoy}
          filtros={filtros} cambiar={cambiar} limite={limite} setLimite={setLimite}
          abrirFiltros={() => setHoja('filtros')} abrirCalendario={() => setHoja('calendario')} scrollLista={scrollLista} favs={favs}
          ubic={ubic} hist={hist}
        />
      ) : null}
      {ruta.vista === 'ficha' && actual && cartelera ? (
        <Ficha t={t} lang={lang} e={actual} hoy={hoy} volver={volver} favs={favs} planes={planes} hist={hist} cartelera={cartelera} />
      ) : null}
      {ruta.vista === 'mapa' ? (
        <VistaMapa t={t} cartelera={vigente} hoy={hoy} filtros={filtros} cambiar={cambiar}
          abrirCalendario={() => setHoja('calendario')} favs={favs} ubic={ubic} />
      ) : null}
      {ruta.vista === 'favoritos' ? <VistaFavoritos t={t} lang={lang} lista={lista} cine={cine} hoy={hoy} favs={favs} hist={hist} planes={planes} /> : null}
      {ruta.vista === 'planes' ? <VistaPlanes t={t} planes={planes} hist={hist} favs={favs} /> : null}
      {ruta.vista === 'historial' ? <VistaHistorial t={t} hist={hist} planes={planes} favs={favs} /> : null}
      {ruta.vista === 'teatro' ? <VistaSala t={t} lista={lista} hoy={hoy} id={ruta.id} volver={volver} cargada={!!cartelera} /> : null}
      {ruta.vista === 'plan' ? <VistaPlan t={t} lang={lang} lista={cartelera?.espectaculos ?? []} vigentes={lista} idsPelis={idsPelis} hoy={hoy} planes={planes} hist={hist} id={ruta.id} /> : null}

      <nav className="nav" aria-label={t.seccionesLabel}>
        <a href="#inicio" aria-current={ruta.vista === 'inicio' || ruta.vista === 'buscar' || ruta.vista === 'persona' ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M4 11l8-7 8 7v9H4z" /><path d="M10 20v-5h4v5" /></svg>
          {t.navInicio}
        </a>
        <a href="#cartelera" aria-current={['cartelera', 'ficha', 'mapa', 'teatro'].includes(ruta.vista) ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M3 4h18v3c-2.5 1.6-5.6 2.5-9 2.5S5.5 8.6 3 7z" /><path d="M3 7c1 4.5 1.6 9 1.6 13H3zM21 7c-1 4.5-1.6 9-1.6 13H21z" /></svg>
          {t.navEscena}
        </a>
        <a href="#cine" aria-current={['cine', 'peli', 'sala', 'mapa-cine'].includes(ruta.vista) ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><rect x="3" y="6" width="18" height="13" rx="2" /><path d="M3 10h18M7 6l2 4M12 6l2 4M17 6l2 4" /></svg>
          {t.navCine}
        </a>
        <a href={agenda} aria-current={['planes', 'plan', 'favoritos', 'historial'].includes(ruta.vista) ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4M8.5 15.5l2.5 2.5 4.5-5" /></svg>
          {t.navAgenda}
        </a>
        <a href="#noticias" aria-current={ruta.vista === 'noticias' ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M5 5h11v14H6a1 1 0 0 1-1-1z" /><path d="M16 9h3v9a1 1 0 0 1-1 1h-2M8 9h5M8 12h5M8 15h3" /></svg>
          {t.navNoticias}
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
  hist: Historial;
}

function VistaCartelera({ t, lang, setLang, cartelera, error, hoy, filtros, cambiar, limite, setLimite, abrirFiltros, abrirCalendario, scrollLista, favs, ubic, hist }: PropsCartelera) {
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
            <h1>{t.escena}</h1>
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
            marcado={hist.es(claveObra(e.id)) ? marca(e.tipo, t).hecho : undefined}
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

function Tarjeta({ e, t, desde, hasta, alAbrir, guardado, dist, marcado, tachado }: {
  e: Espectaculo; t: Textos; desde: string; hasta: string; alAbrir: () => void; guardado?: boolean; dist?: number | null;
  /** «Vista», «Visto» o «Hecho» si está en el historial. */
  marcado?: string; tachado?: boolean;
}) {
  const fs = funcionesEnRango(e, desde, hasta);
  const [dia, hora] = fs[0] ?? [];
  const precio = precioTxt(e, t);
  const lugar = [e.sala, e.barrio, dist != null ? fmtDistancia(dist) : ''].filter(Boolean).join(' · ');
  return (
    <a className={tachado ? 'tarjeta tachado' : 'tarjeta'} href={enlaceFicha(e.id)} onClick={alAbrir}>
      <Cartel e={e} t={t} clase="tarjeta-imagen" />
      <span className="tarjeta-cabeza">
        <Etiquetas e={e} t={t} />
        <span className="tarjeta-marcas">
          {marcado ? <span className="etiqueta marca-hecho"><IconoCheck lleno />{marcado}</span> : null}
          {guardado ? <Corazon lleno /> : null}
        </span>
      </span>
      <span className="tarjeta-nombre">{e.nombre}</span>
      {e.artista ? <span className="tarjeta-artista">{e.artista}</span> : null}
      {lugar ? <span className="tarjeta-lugar">{lugar}</span> : null}
      <span className="tarjeta-pie">
        {dia ? <span className="cuando">{fmtDia(dia, t)}{hora ? ` · ${hora}` : ''}{fs.length > 1 ? `  +${fs.length - 1}` : ''}</span> : <span />}
        {precio ? <span className="precio">{precio}</span> : null}
      </span>
    </a>
  );
}

// --- Ficha ------------------------------------------------------------------------

export function IconoCheck({ lleno }: { lleno?: boolean }) {
  return (
    <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
      {lleno ? null : <circle cx="12" cy="12" r="9" strokeWidth="1.8" />}
      <path d="M7.5 12.5l3 3 6-6.5" />
    </svg>
  );
}

/** Botón ✓ para marcar algo como visto o hecho (y quitar la marca). Lo marcado va al historial. */
export function BotonMarca({ t, hist, h, grande }: { t: Textos; hist: Historial; h: Omit<Hecho, 'fecha'>; grande?: boolean }) {
  const m = marca(h.clase, t);
  const hecho = hist.es(h.clave);
  return (
    <button type="button" className={`boton-marca${hecho ? ' marcado' : ''}${grande ? ' grande' : ''}`} aria-pressed={hecho}
      title={hecho ? t.quitarMarca : m.marcar} onClick={() => hist.alternar(h)}>
      <IconoCheck lleno={hecho} />{hecho ? m.hecho : m.marcar}
    </button>
  );
}

export function Corazon({ lleno }: { lleno?: boolean }) {
  return (
    <svg className={lleno ? 'corazon lleno' : 'corazon'} aria-hidden="true" width="22" height="22" viewBox="0 0 24 24"
      fill={lleno ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinejoin="round">
      <path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" />
    </svg>
  );
}

function Ficha({ t, lang, e, hoy, volver, favs, planes, hist, cartelera }: {
  t: Textos; lang: Idioma; e: Espectaculo; hoy: string; volver: () => void; favs: Favoritos; planes: Planes; hist: Historial; cartelera: Cartelera;
}) {
  const guardado = favs.es(e.id);
  const [cuantas, setCuantas] = useState(6);
  const [paraPlan, setParaPlan] = useState<ItemPlan | null>(null);
  const [aviso, setAviso] = useState<{ texto: string; plan: string } | null>(null);
  useLayoutEffect(() => { window.scrollTo(0, 0); setCuantas(6); setAviso(null); }, [e.id]);
  const fs = e.funciones.filter(([d, h]) => d > hoy || (d === hoy && (!h || h >= horaAhora(cartelera.ciudad.zona_horaria))));
  // El texto en el idioma de la app; si no, en el otro idioma de la app; si no, el original (p. ej. inglés).
  const idiomaDesc = e.descripcion?.[lang] ? lang : (['es', 'ca'].find((k) => e.descripcion?.[k]) || Object.keys(e.descripcion || {})[0]);
  const desc = idiomaDesc ? e.descripcion?.[idiomaDesc] : '';
  const notaDesc = idiomaDesc && idiomaDesc !== lang ? t.textoOriginal[idiomaDesc]
    : e.traducido && e.traducido === idiomaDesc ? (idiomaDesc === 'es' ? t.traducidoIA : t.traducidoIACa) : '';
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
        <span className="barra-derecha">
          <BotonMarca t={t} hist={hist} h={{ clave: claveObra(e.id), clase: e.tipo, nombre: e.nombre, detalle: e.sala, enlace: enlaceFicha(e.id) }} />
          <button type="button" className="boton-icono boton-corazon" aria-pressed={guardado}
            aria-label={guardado ? t.favQuitar : t.favGuardar} title={guardado ? t.favQuitar : t.favGuardar}
            onClick={() => favs.alternar(e.id)}>
            <Corazon lleno={guardado} />
          </button>
        </span>
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
            {e.sala ? (e.sala_id ? <a className="caja-titulo" href={enlaceSala(e.sala_id)}>{e.sala}</a> : <span className="caja-titulo">{e.sala}</span>) : null}
            {e.sala_interior ? <span className="texto-claro">{e.sala_interior}</span> : null}
            {direccion ? <span className="texto-suave">{direccion}</span> : null}
            <span className="fila-enlaces">
              {e.lat != null && e.lon != null ? (
                <a className="enlace" href={`https://www.google.com/maps/search/?api=1&query=${e.lat},${e.lon}`} target="_blank" rel="noopener noreferrer">{t.comoLlegar}</a>
              ) : null}
              {e.sala_id ? <a className="enlace" href={enlaceSala(e.sala_id)}>{t.verSala}</a> : null}
            </span>
          </section>
        ) : null}

        <section className="bloque">
          <h3>{t.funciones}</h3>
          {fs.length === 0 ? <p className="aviso">{t.fueraDeCartel}</p> : null}
          {fs.slice(0, cuantas).map(([dia, hora], i) => {
            const enPlan = planes.conFuncion(e.id, dia, hora);
            return (
              <span key={`${dia}-${hora}-${i}`} className="funcion">
                <span>{fmtDia(dia, t)}</span>
                <span className="funcion-derecha">
                  {hora ? (e.compra && e.compra_tipo === 'obra' ? (
                    <a className="hora-chip" href={e.compra} target="_blank" rel="noopener noreferrer" aria-label={`${t.comprar}: ${fmtDia(dia, t)} ${hora}`}>{hora}</a>
                  ) : <span className="texto-claro">{hora}</span>) : null}
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

        {e.compra ? (
          <div className="compra">
            <a className={e.compra_tipo === 'sala' ? 'boton-secundario' : 'boton-principal'} href={e.compra} target="_blank" rel="noopener noreferrer">
              {e.compra_tipo === 'sala' ? t.webSala : t.comprar}
            </a>
            {e.compra_tipo ? <span className="nota">{e.compra_tipo === 'sala' ? t.compraSalaNota : t.compraObraNota}</span> : null}
          </div>
        ) : null}

        {desc ? (
          <section className="bloque">
            <h3>{t.descripcion}</h3>
            <p className="descripcion" lang={idiomaDesc}>{desc}</p>
            {notaDesc ? <span className="nota">{notaDesc}</span> : null}
            {e.temas?.[lang]?.length ? (
              <span className="etiquetas temas" aria-label={t.temasObra}>
                {e.temas[lang].map((x) => <span key={x} className="etiqueta suave">#{x}</span>)}
              </span>
            ) : null}
          </section>
        ) : null}

        {e.premios?.length ? (
          <section className="bloque">
            <h3>{t.premiosCitados}</h3>
            <ul className="premios">
              {e.premios.map((x) => (
                <li key={x.cita} className="premio ganado">
                  <span className="premio-icono" aria-hidden="true">★</span>
                  <span>{lang === 'ca' ? x.ca : x.es}<span className="premio-cita">{x.origen === 'web' ? t.citaWeb : t.citaTxt} «{x.cita}»</span></span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {e.equipo?.length ? (
          <section className="bloque">
            <h3>{t.equipo}</h3>
            <dl className="equipo">
              {e.equipo.map(([papel, personas]) => (
                <div key={papel} className="equipo-fila">
                  <dt>{t.papel(papel)}</dt>
                  <dd>{/* Cada nombre lleva a su ficha (sus obras y, si está en Wikidata, foto y premios). */}
                    {separarNombres(personas).length ? personas.split(/(\s*(?:,|;|\/|\s+i\s+|\s+y\s+|\s+&\s+)\s*)/).map((trozo, k) => (
                      separarNombres(trozo).length === 1 && separarNombres(trozo)[0] === trozo.trim()
                        ? <a key={k} className="persona-enlace" href={`#persona-n-${slug(trozo.trim())}`}>{trozo}</a>
                        : <span key={k}>{trozo}</span>
                    )) : personas}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        ) : null}

        {e.tipo === 'magia' && e.artista_ficha ? (
          <section className="caja mago">
            <h3>{t.magoTit}</h3>
            <span className="caja-titulo">{e.artista_ficha.nombre}</span>
            {e.artista_ficha.trayectoria?.[lang] ? <p className="descripcion">{e.artista_ficha.trayectoria[lang]}</p> : null}
            {e.artista_ficha.premios.length ? (
              <ul className="premios">
                {e.artista_ficha.premios.map((x) => (
                  <li key={`${x.premio}-${x.anio}`} className="premio ganado">
                    <span className="premio-icono" aria-hidden="true">★</span>
                    <span>{x.premio}{x.anio ? ` · ${x.anio}` : ''} <a className="fuente-mini" href={x.fuente} target="_blank" rel="noopener noreferrer">{t.fuente}</a></span>
                  </li>
                ))}
              </ul>
            ) : null}
            {e.artista_ficha.fuentes.length ? (
              <span className="nota">{t.fuente}: {e.artista_ficha.fuentes.map((u, i) => (
                <a key={u} href={u} target="_blank" rel="noopener noreferrer">{i ? ', ' : ''}{(u.match(/^https?:\/\/([^/]+)/)?.[1] || u).replace(/^www\./, '')}</a>
              ))}. {t.magoNota}</span>
            ) : null}
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

        <div className="grupo" role="group" aria-labelledby="titulo-ocultos">
          <h3 id="titulo-ocultos">{t.ocultarGeneros}</h3>
          <div className="opciones">
            {GENEROS.filter((g) => lista.some((e) => e.generos?.includes(g))).map((g) => {
              const oculto = filtros.ocultos.includes(g);
              return (
                <button key={g} type="button" className="chip pequeno" aria-pressed={oculto}
                  onClick={() => {
                    const v = oculto ? filtros.ocultos.filter((x) => x !== g) : [...filtros.ocultos, g];
                    guardarOcultos(v);
                    cambiar({ ocultos: v });
                  }}>
                  {oculto ? '✕ ' : ''}{t.generos[g]}
                </button>
              );
            })}
          </div>
          <span className="nota">{t.ocultarGenerosNota}</span>
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

/** Selector de la Agenda: Planes, Guardado e Historial (la barra de abajo tiene una sola pestaña). */
function SegmentosAgenda({ t, actual, n }: { t: Textos; actual: 'planes' | 'favoritos' | 'historial'; n: [number, number, number] }) {
  const segs: [typeof actual, string, number][] = [['planes', t.navPlanes, n[0]], ['favoritos', t.navGuardado, n[1]], ['historial', t.segHistorial, n[2]]];
  return (
    <nav className="segmentos-agenda" aria-label={t.agendaTit}>
      {segs.map(([k, txt, num]) => (
        <a key={k} href={`#${k}`} aria-current={actual === k ? 'page' : undefined}>
          {txt}{num ? <span className="num">{num}</span> : null}
        </a>
      ))}
    </nav>
  );
}

/** Lo que cuenta cada apartado de la Agenda (para el selector). */
function cuentasAgenda(planes: Planes, favs: Favoritos, hist: Historial): [number, number, number] {
  return [planes.planes.filter((p) => !hist.es(clavePlan(p.id))).length, favs.ids.length, hist.lista.length];
}

function CabeceraAgenda({ t, sub, actual, n }: { t: Textos; sub: string; actual: 'planes' | 'favoritos' | 'historial'; n: [number, number, number] }) {
  return (
    <header className="cabecera cabecera-agenda">
      <div className="titulo">
        <span className="sobretitulo">{sub || ' '}</span>
        <h1>{t.agendaTit}</h1>
      </div>
      <SegmentosAgenda t={t} actual={actual} n={n} />
    </header>
  );
}

function VistaFavoritos({ t, lang, lista, cine, hoy, favs, hist, planes }: {
  t: Textos; lang: Idioma; lista: Espectaculo[]; cine: CarteleraCine | null; hoy: string; favs: Favoritos; hist: Historial; planes: Planes;
}) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, []);
  const guardados = lista.filter((e) => favs.es(e.id))
    .sort((a, b) => (a.funciones[0]?.[0] ?? '').localeCompare(b.funciones[0]?.[0] ?? ''));
  const pelis = (cine?.peliculas || []).filter((p) => favs.es(p.id));
  const fuera = lista.length && cine ? favs.ids.length - guardados.length - pelis.length : 0;
  // Lo ya visto o hecho va al final, tachado.
  const obrasPend = guardados.filter((e) => !hist.es(claveObra(e.id)));
  const obrasHechas = guardados.filter((e) => hist.es(claveObra(e.id)));
  const pelisPend = pelis.filter((p) => !hist.es(clavePeli(p.id)));
  const pelisHechas = pelis.filter((p) => hist.es(clavePeli(p.id)));
  const filaPeli = (p: (typeof pelis)[number], tachada: boolean) => (
    <a key={p.id} className={tachada ? 'fila-resultado tachado' : 'fila-resultado'} href={enlacePeli(p.id)}>
      <Cartelito src={p.cartel} alt={p.titulo} clase="mini-cartel" />
      <span>
        <span className="caja-titulo">{(lang === 'ca' && p.titulo_ca) || p.titulo}</span>
        <span className="texto-suave">{tachada ? `✓ ${marca('peli', t).hecho}` : t.sesiones(p.sesiones.filter((s) => s[1] >= hoy).length)}</span>
      </span>
    </a>
  );
  return (
    <main className="pantalla">
      <CabeceraAgenda t={t} actual="favoritos" sub={t.guardadoTit} n={cuentasAgenda(planes, favs, hist)} />
      <div className="lista">
        {guardados.length === 0 && pelis.length === 0 ? <p className="aviso">{t.favVacio}</p> : null}
        {obrasPend.length ? <h2 className="seccion-titulo">{t.favObras}</h2> : null}
        {obrasPend.map((e) => (
          <Tarjeta key={e.id} e={e} t={t} desde={hoy} hasta="9999-12-31" alAbrir={() => {}} guardado />
        ))}
        {pelisPend.length ? <h2 className="seccion-titulo">{t.favPelis}</h2> : null}
        {pelisPend.map((p) => filaPeli(p, false))}
        {obrasHechas.length || pelisHechas.length ? <h2 className="seccion-titulo">{t.yaVistos}</h2> : null}
        {obrasHechas.map((e) => (
          <Tarjeta key={e.id} e={e} t={t} desde={hoy} hasta="9999-12-31" alAbrir={() => {}} guardado tachado
            marcado={marca(e.tipo, t).hecho} />
        ))}
        {pelisHechas.map((p) => filaPeli(p, true))}
        {fuera > 0 ? <p className="nota">{t.favFuera(fuera)}</p> : null}
        <p className="nota">{t.favNota}</p>
      </div>
    </main>
  );
}

// --- Sala de teatro: dónde está y todo lo que tiene en cartel ------------------------------

function VistaSala({ t, lista, hoy, id, volver, cargada }: {
  t: Textos; lista: Espectaculo[]; hoy: string; id: string; volver: () => void; cargada: boolean;
}) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, [id]);
  const obras = lista.filter((e) => e.sala_id && claveFicha(e.sala_id) === id && e.funciones.some(([d]) => d >= hoy))
    .sort((a, b) => (a.funciones.find(([d]) => d >= hoy)?.[0] ?? '').localeCompare(b.funciones.find(([d]) => d >= hoy)?.[0] ?? ''));
  const s = obras[0];
  const web = obras.map((e) => e.compra_sala || (e.compra_tipo === 'sala' ? e.compra : undefined)).find(Boolean);
  return (
    <main className="pantalla">
      <div className="ficha-barra">
        <button type="button" className="boton-volver" onClick={volver} aria-label={t.volver}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 5l-7 7 7 7" /></svg>
          {t.navEscena}
        </button>
      </div>
      <div className="ficha">
        {!s ? <p className="aviso">{cargada ? t.sinResultados : t.cargando}</p> : (
          <>
            <div className="ficha-cabecera">
              <span className="sobretitulo">{t.salasTit}</span>
              <h2>{s.sala}</h2>
              <span className="texto-suave">{[s.direccion, s.barrio].filter(Boolean).join(' · ')}</span>
              <span className="fila-enlaces">
                {s.lat != null && s.lon != null ? (
                  <a className="enlace" href={`https://www.google.com/maps/search/?api=1&query=${s.lat},${s.lon}`} target="_blank" rel="noopener noreferrer">{t.comoLlegar}</a>
                ) : null}
                {web ? <a className="enlace" href={web} target="_blank" rel="noopener noreferrer">{t.webSala}</a> : null}
              </span>
            </div>
            <h3 className="seccion-titulo">{t.salaObras} · {t.resultados(obras.length)}</h3>
            {obras.map((e) => <Tarjeta key={e.id} e={e} t={t} desde={hoy} hasta="9999-12-31" alAbrir={() => {}} />)}
          </>
        )}
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
export function HojaPlan({ t, item, planes, cerrar, listo }: {
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

function VistaPlanes({ t, planes, hist, favs }: { t: Textos; planes: Planes; hist: Historial; favs: Favoritos }) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, []);
  const [creando, setCreando] = useState(false);
  const activos = planes.planes.filter((p) => !hist.es(clavePlan(p.id)));
  const hechos = planes.planes.filter((p) => hist.es(clavePlan(p.id)));
  const tarjeta = (p: Plan, hecho: boolean) => (
    <a key={p.id} className={hecho ? 'tarjeta plan-tarjeta tachado' : 'tarjeta plan-tarjeta'} href={`#plan-${p.id}`}>
      <span className="tarjeta-cabeza">
        <span className="tarjeta-nombre">{p.nombre}</span>
        {hecho ? <span className="etiqueta marca-hecho"><IconoCheck lleno />{t.hecho}</span> : null}
      </span>
      <span className="tarjeta-lugar">{[t.planFunciones(p.items.length), rangoPlan(p, t)].filter(Boolean).join(' · ')}</span>
      {p.items.length ? (
        <span className="texto-suave plan-resumen">{p.items.slice(0, 3).map((i) => i.nombre).join(' · ')}{p.items.length > 3 ? ' …' : ''}</span>
      ) : null}
    </a>
  );
  return (
    <main className="pantalla">
      <CabeceraAgenda t={t} actual="planes" n={cuentasAgenda(planes, favs, hist)}
        sub={activos.length ? t.planFunciones(activos.reduce((n, p) => n + p.items.length, 0)) : t.planesTit} />
      <div className="lista">
        <p className="texto-suave">{t.planesIntro}</p>
        {planes.planes.length === 0 ? <p className="aviso">{t.planesVacio}</p> : null}
        {activos.map((p) => tarjeta(p, false))}
        {creando ? (
          <FormNuevoPlan t={t} boton={t.planCrearSolo} alCrear={(nombre) => { window.location.hash = `#plan-${planes.crear(nombre)}`; }} />
        ) : (
          <button type="button" className="boton-secundario" onClick={() => setCreando(true)}>+ {t.planNuevo}</button>
        )}
        {hechos.length ? <h2 className="seccion-titulo">{t.planesHechos}</h2> : null}
        {hechos.map((p) => tarjeta(p, true))}
        <p className="nota">{t.planNota}</p>
      </div>
    </main>
  );
}

/** Historial: todo lo marcado como visto o hecho, por meses (lo más reciente primero). */
function VistaHistorial({ t, hist, planes, favs }: { t: Textos; hist: Historial; planes: Planes; favs: Favoritos }) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, []);
  const [filtro, setFiltro] = useState<'todo' | 'cine' | 'escena' | 'eventos' | 'plan'>('todo');
  const grupo = (c: Clase) => (c === 'peli' ? 'cine' : c === 'plan' ? 'plan' : c === 'eventos' ? 'eventos' : 'escena');
  const lista = hist.lista.filter((h) => filtro === 'todo' || grupo(h.clase) === filtro);
  const meses: [string, Hecho[]][] = [];
  for (const h of lista) {
    const m = h.fecha.slice(0, 7);
    if (meses.length && meses[meses.length - 1][0] === m) meses[meses.length - 1][1].push(h);
    else meses.push([m, [h]]);
  }
  const cuenta = (k: string) => hist.lista.filter((h) => k === 'todo' || grupo(h.clase) === k).length;
  return (
    <main className="pantalla">
      <CabeceraAgenda t={t} actual="historial" n={cuentasAgenda(planes, favs, hist)}
        sub={hist.lista.length ? t.historialResumen(hist.lista.length) : t.segHistorial} />
      <div className="lista">
        {hist.lista.length === 0 ? <p className="aviso">{t.historialVacio}</p> : (
          <div className="chips sin-margen">
            {(['todo', 'cine', 'escena', 'eventos', 'plan'] as const).map((k) => (
              <button key={k} type="button" className="chip pequeno" aria-pressed={filtro === k} onClick={() => setFiltro(k)}>
                {t.filtroHist[k]}<span className="num">{cuenta(k)}</span>
              </button>
            ))}
          </div>
        )}
        {hist.lista.length && lista.length === 0 ? <p className="aviso">{t.historialNada}</p> : null}
        {meses.map(([mes, hs]) => (
          <section key={mes} className="bloque">
            <h2 className="seccion-titulo">{t.mesesLargos[Number(mes.slice(5)) - 1]} {mes.slice(0, 4)}</h2>
            {hs.map((h) => (
              <div key={h.clave} className="fila-historial">
                <span className="hist-check" aria-hidden="true"><IconoCheck lleno /></span>
                <a className="hist-info" href={h.enlace}>
                  <span className="caja-titulo">{h.nombre}</span>
                  <span className="texto-suave">
                    {[t.claseTxt[h.clase], t.marcadoEl(marca(h.clase, t).hecho, fmtCorto(h.fecha, t)), h.detalle].filter(Boolean).join(' · ')}
                  </span>
                </a>
                <button type="button" className="boton-icono" aria-label={`${t.quitarMarca}: ${h.nombre}`} title={t.quitarMarca}
                  onClick={() => hist.quitar(h.clave)}>
                  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
                </button>
              </div>
            ))}
          </section>
        ))}
        <p className="nota">{t.historialNota}</p>
      </div>
    </main>
  );
}

// Iconos de las acciones del plan (trazo, como el resto de la app).
const IconoCompartir = () => (
  <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v12M7 8l5-5 5 5" /><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7" /></svg>
);
const IconoCalendario = () => (
  <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4M12 13v5M9.5 15.5h5" /></svg>
);
const IconoMapa = () => (
  <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2z" /><path d="M9 4v14M15 6v14" /></svg>
);
const IconoLapiz = () => (
  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg>
);
const IconoPapelera = () => (
  <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" /></svg>
);

// Hoja de compartir: el plan en texto (WhatsApp, mensajes, correo…) o como imagen para stories.
function HojaCompartir({ t, plan, cerrar }: { t: Textos; plan: Plan; cerrar: () => void }) {
  const primero = useRef<HTMLButtonElement>(null);
  useHoja(cerrar, primero);
  const [copiado, setCopiado] = useState(false);
  const texto = async () => {
    const txt = planTexto(plan, t);
    if (navigator.share) {
      try { await navigator.share({ title: plan.nombre, text: txt }); cerrar(); return; } catch { /* cancelado o no permitido: copiar */ }
    }
    try { await navigator.clipboard.writeText(txt); setCopiado(true); } catch { /* sin portapapeles */ }
  };
  // Imagen vertical para historias: con el menú de compartir del móvil si deja compartir archivos; si no, se descarga.
  const imagen = async () => {
    const blob = await imagenPlan(plan, (d) => fmtDia(d, t), t.planPieImagen);
    if (!blob) return;
    const archivo = new File([blob], `${nombreArchivo(plan.nombre)}.png`, { type: 'image/png' });
    if (navigator.canShare?.({ files: [archivo] })) {
      try { await navigator.share({ files: [archivo], title: plan.nombre }); cerrar(); return; } catch { /* cancelado */ }
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = archivo.name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  };
  return (
    <div className="fondo-hoja" onClick={(ev) => { if (ev.target === ev.currentTarget) cerrar(); }}>
      <div className="hoja hoja-baja" role="dialog" aria-modal="true" aria-labelledby="titulo-compartir">
        <div className="hoja-cabecera">
          <div className="calendario-titulo"><h2 id="titulo-compartir">{t.planCompartir}</h2><span className="cuando">{plan.nombre}</span></div>
          <BotonCerrar t={t} cerrar={cerrar} refBoton={primero} />
        </div>
        <div className="hoja-cuerpo">
          <button type="button" className="plan-opcion con-icono" onClick={texto}>
            <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M4 5h16v11H9l-5 4z" /></svg>
            <span><span className="caja-titulo">{t.compartirTexto}</span><span className="texto-suave">{t.compartirTextoSub}</span></span>
          </button>
          <button type="button" className="plan-opcion con-icono" onClick={imagen}>
            <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><rect x="6" y="2" width="12" height="20" rx="2.5" /><circle cx="12" cy="10" r="3" /><path d="M9 17h6" /></svg>
            <span><span className="caja-titulo">{t.compartirStories}</span><span className="texto-suave">{t.compartirStoriesSub}</span></span>
          </button>
          {copiado ? <p className="nota" role="status">{t.planCopiado}</p> : null}
        </div>
      </div>
    </div>
  );
}


function HojaRuta({ t, lang, dia, items, cerrar }: { t: Textos; lang: Idioma; dia: string; items: ItemPlan[]; cerrar: () => void }) {
  const primero = useRef<HTMLButtonElement>(null);
  useHoja(cerrar, primero);
  const paradas = paradasRuta(items);
  const sinUbicacion = items.filter((i) => i.lat == null || i.lon == null);
  const mapa = rutaIncrustada(paradas, lang);
  return (
    <div className="fondo-hoja" onClick={(ev) => { if (ev.target === ev.currentTarget) cerrar(); }}>
      <div className="hoja" role="dialog" aria-modal="true" aria-labelledby="titulo-ruta">
        <div className="hoja-cabecera">
          <div className="calendario-titulo"><h2 id="titulo-ruta">{t.rutaTit}</h2><span className="cuando">{fmtDia(dia, t)} · {t.rutaParadas(paradas.length)}</span></div>
          <BotonCerrar t={t} cerrar={cerrar} refBoton={primero} />
        </div>
        <div className="hoja-cuerpo">
          {/* El mapa de Google dentro de la app, con el recorrido a pie por las calles. */}
          {mapa ? <iframe className="mapa-google" src={mapa} title={t.rutaTit} loading="lazy" referrerPolicy="no-referrer-when-downgrade" allowFullScreen /> : null}
          {paradas.length ? (
            <button type="button" className="boton-principal con-icono" onClick={() => abrirRutaEnMovil(paradas)}>
              <IconoMapa />{t.rutaAbrirMovil}
            </button>
          ) : null}
          <ol className="ruta-lista">
            {paradas.map((p, k) => (
              <li key={k}>
                <span className="ruta-num" aria-hidden="true">{k + 1}</span>
                <span className="plan-info">
                  <span className="caja-titulo">{p.hora ? `${p.hora} · ` : ''}{p.nombre}</span>
                  <span className="texto-suave">{[p.sala, p.direccion].filter(Boolean).join(' · ')}</span>
                </span>
              </li>
            ))}
          </ol>
          {sinUbicacion.length ? <p className="nota">{t.rutaSinMapa}: {sinUbicacion.map((i) => i.nombre).join(', ')}</p> : null}
          <p className="nota">{t.rutaNota}</p>
        </div>
      </div>
    </div>
  );
}

function DialogoBorrar({ t, nombre, borrar, cerrar }: { t: Textos; nombre: string; borrar: () => void; cerrar: () => void }) {
  const primero = useRef<HTMLButtonElement>(null);
  useHoja(cerrar, primero);
  return (
    <div className="fondo-hoja centrado" onClick={(ev) => { if (ev.target === ev.currentTarget) cerrar(); }}>
      <div className="dialogo" role="alertdialog" aria-modal="true" aria-labelledby="titulo-borrar">
        <p id="titulo-borrar" className="dialogo-texto">{t.borrarPregunta(nombre)}</p>
        <div className="dialogo-botones">
          <button ref={primero} type="button" className="boton-secundario" onClick={cerrar}>{t.cancelar}</button>
          <button type="button" className="boton-principal peligro" onClick={borrar}>{t.borrarSi}</button>
        </div>
      </div>
    </div>
  );
}

function VistaPlan({ t, lang, lista, vigentes: enCartelera, idsPelis, hoy, planes, hist, id }: {
  t: Textos; lang: Idioma; lista: Espectaculo[]; vigentes: Espectaculo[]; idsPelis: Set<string>; hoy: string; planes: Planes; hist: Historial; id: string;
}) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, [id]);
  const [editando, setEditando] = useState(false);
  const [hoja, setHoja] = useState<null | 'compartir' | 'borrar' | { ruta: string }>(null);
  const enCartel = useMemo(() => new Set([...enCartelera.map((e) => e.id), ...idsPelis]), [enCartelera, idsPelis]);
  const porId = useMemo(() => new Map(lista.map((e) => [e.id, e])), [lista]);
  const claseItem = (i: ItemPlan): Clase => i.clase ?? (idsPelis.has(i.id) ? 'peli' : porId.get(i.id)?.tipo ?? 'teatro');
  const enlaceItem = (id: string) => (idsPelis.has(id) ? enlacePeli(id) : enlaceFicha(id));
  // Marca de cada función: la de su obra o película (vista una vez, vista en todos los planes).
  const marcaItem = (i: ItemPlan): Omit<Hecho, 'fecha'> => {
    const clase = claseItem(i);
    return { clave: clase === 'peli' ? clavePeli(i.id) : claveObra(i.id), clase, nombre: i.nombre, detalle: i.sala,
      enlace: clase === 'peli' ? enlacePeli(i.id) : enlaceFicha(i.id) };
  };
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
  const enlace = (i: ItemPlan) => `${window.location.origin}${window.location.pathname}${enlaceItem(i.id)}`;
  const dias = porDias(plan.items);

  return (
    <main className="pantalla">
      {barra}
      <div className="ficha">
        <div className="ficha-cabecera">
          {editando ? (
            <FormNuevoPlan t={t} boton={t.planGuardar} inicial={plan.nombre}
              alCrear={(nombre) => { planes.renombrar(plan.id, nombre); setEditando(false); }} />
          ) : (
            <div className="plan-titulo">
              <h2 className={hist.es(clavePlan(plan.id)) ? 'tachado' : undefined}>{plan.nombre}</h2>
              <button type="button" className="boton-icono" aria-label={t.editarNombre} title={t.editarNombre} onClick={() => setEditando(true)}>
                <IconoLapiz />
              </button>
            </div>
          )}
          {editando ? <button type="button" className="enlace" onClick={() => setEditando(false)}>{t.cancelar}</button> : null}
          <span className="texto-suave">{[t.planFunciones(plan.items.length), rangoPlan(plan, t)].filter(Boolean).join(' · ')}</span>
          <BotonMarca t={t} hist={hist} grande
            h={{ clave: clavePlan(plan.id), clase: 'plan', nombre: plan.nombre, enlace: `#plan-${plan.id}`,
              detalle: [t.planFunciones(plan.items.length), rangoPlan(plan, t)].filter(Boolean).join(' · ') }} />
        </div>

        {plan.items.length ? (
          <div className="plan-acciones">
            <button type="button" className="boton-principal con-icono" onClick={() => setHoja('compartir')}><IconoCompartir />{t.planCompartir}</button>
            <button type="button" className="boton-secundario con-icono"
              onClick={() => descargar(`${nombreArchivo(plan.nombre)}.ics`, planIcs(plan, enlace), 'text/calendar')}>
              <IconoCalendario />{t.planCalendario}
            </button>
          </div>
        ) : <p className="aviso">{t.planVacio}</p>}

        {dias.map(([dia, items]) => {
          const conMapa = items.some((i) => i.lat != null && i.lon != null);
          return (
            <section key={dia} className={dia < hoy ? 'bloque plan-dia pasado' : 'bloque plan-dia'}>
              <h3>{fmtDia(dia, t)}{dia < hoy ? ` · ${t.planPasado}` : ''}</h3>
              {items.map((i) => {
                const k = claveItem(i);
                const choque = choques.get(k);
                const lugar = [i.sala, i.direccion, i.barrio].filter(Boolean).join(' · ');
                const m = marcaItem(i);
                const vista = hist.es(m.clave);
                return (
                  <div key={k} className={vista ? 'plan-item tachado' : 'plan-item'}>
                    <span className="plan-hora">{i.hora || '—'}</span>
                    <span className="plan-info">
                      {enCartel.has(i.id) ? <a className="caja-titulo" href={enlaceItem(i.id)}>{i.nombre}</a> : <span className="caja-titulo">{i.nombre}</span>}
                      {!i.hora ? <span className="texto-suave">{t.planSinHora}</span> : null}
                      {lugar ? <span className="texto-suave">{lugar}</span> : null}
                      {choque ? <span className="plan-choque">{t.planSolape(choque)}</span> : null}
                      {!enCartel.has(i.id) && dia >= hoy && lista.length ? <span className="nota">{t.planFuera}</span> : null}
                    </span>
                    <span className="plan-item-botones">
                    <button type="button" className={vista ? 'boton-icono check marcado' : 'boton-icono check'} aria-pressed={vista}
                      aria-label={`${vista ? t.quitarMarca : marca(m.clase, t).marcar}: ${i.nombre}`} title={vista ? t.quitarMarca : marca(m.clase, t).marcar}
                      onClick={() => hist.alternar(m)}>
                      <IconoCheck lleno={vista} />
                    </button>
                    <button type="button" className="boton-icono" aria-label={`${t.planQuitar}: ${i.nombre}`} title={t.planQuitar}
                      onClick={() => planes.quitar(plan.id, k)}>
                      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
                    </button>
                    </span>
                  </div>
                );
              })}
              {conMapa ? (
                <button type="button" className="boton-ruta" onClick={() => setHoja({ ruta: dia })}>
                  <IconoMapa />{t.planRuta}
                  <svg className="flecha-derecha" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l6 6-6 6" /></svg>
                </button>
              ) : null}
            </section>
          );
        })}

        <p className="nota">{t.planNota}</p>
        <div className="plan-borrar">
          <button type="button" className="boton-secundario peligro con-icono" onClick={() => setHoja('borrar')}><IconoPapelera />{t.planBorrar}</button>
        </div>
      </div>
      {hoja === 'compartir' ? <HojaCompartir t={t} plan={plan} cerrar={() => setHoja(null)} /> : null}
      {hoja === 'borrar' ? (
        <DialogoBorrar t={t} nombre={plan.nombre} cerrar={() => setHoja(null)}
          borrar={() => { planes.borrar(plan.id); window.location.hash = '#planes'; }} />
      ) : null}
      {hoja && typeof hoja === 'object' ? (
        <HojaRuta t={t} lang={lang} dia={hoja.ruta} items={dias.find(([d]) => d === hoja.ruta)?.[1] || []} cerrar={() => setHoja(null)} />
      ) : null}
    </main>
  );
}
