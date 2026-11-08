import { useCallback, useDeferredValue, useEffect, useLayoutEffect, useMemo, useRef, useState, type RefObject } from 'react';
import { cargarCartelera, type Cartelera, type Espectaculo } from './datos';
import {
  FILTROS_INICIALES, FUNCIONES, PRECIO_TOPE, cuantosFiltros, duracionTxt, filtrar, fmtDia, funcionesEnRango,
  grupoEvento, hoyEn, pasa, precioTxt, publicoTxt, rango, tipoTxt, type ClaveFecha, type Filtros,
} from './filtros';
import { TEXTOS, guardarIdioma, idiomaInicial, type Idioma, type Textos } from './textos';

const POR_PAGINA = 40;

// --- Rutas: la dirección dice qué pantalla se ve, así funciona el botón «atrás» del móvil.
type Ruta = { vista: 'cartelera' } | { vista: 'ficha'; id: string } | { vista: 'mapa' } | { vista: 'favoritos' };

function leerRuta(): Ruta {
  const h = window.location.hash.replace(/^#\/?/, '');
  if (h.startsWith('ficha/')) return { vista: 'ficha', id: decodeURIComponent(h.slice(6)) };
  if (h === 'mapa') return { vista: 'mapa' };
  if (h === 'favoritos') return { vista: 'favoritos' };
  return { vista: 'cartelera' };
}

const enlaceFicha = (id: string) => `#/ficha/${encodeURIComponent(id)}`;

export default function App() {
  const [lang, setLang] = useState<Idioma>(idiomaInicial);
  const [ruta, setRuta] = useState<Ruta>(leerRuta);
  const [cartelera, setCartelera] = useState<Cartelera | null>(null);
  const [error, setError] = useState(false);
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_INICIALES);
  const [hojaAbierta, setHojaAbierta] = useState(false);
  const [limite, setLimite] = useState(POR_PAGINA);
  const navegado = useRef(false);
  const scrollLista = useRef(0);
  const t = TEXTOS[lang];

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
    else window.location.hash = '#/';
  }, []);

  const hoy = cartelera ? hoyEn(cartelera.ciudad.zona_horaria) : '';
  const lista = cartelera?.espectaculos ?? [];
  const actual = ruta.vista === 'ficha' ? lista.find((e) => e.id === ruta.id) : undefined;

  return (
    <div className="app">
      {ruta.vista === 'cartelera' || (ruta.vista === 'ficha' && !actual) ? (
        <VistaCartelera
          t={t} lang={lang} setLang={setLang} cartelera={cartelera} error={error} hoy={hoy}
          filtros={filtros} cambiar={cambiar} limite={limite} setLimite={setLimite}
          abrirHoja={() => setHojaAbierta(true)} scrollLista={scrollLista}
        />
      ) : null}
      {ruta.vista === 'ficha' && actual ? <Ficha t={t} lang={lang} e={actual} hoy={hoy} volver={volver} /> : null}
      {ruta.vista === 'mapa' ? <Pronto titulo={t.mapaTit} texto={t.mapaTxt} t={t} /> : null}
      {ruta.vista === 'favoritos' ? <Pronto titulo={t.favTit} texto={t.favTxt} t={t} /> : null}

      <nav className="nav" aria-label={t.seccionesLabel}>
        <a href="#/" aria-current={ruta.vista === 'cartelera' || ruta.vista === 'ficha' ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M4 6h16v4a2 2 0 0 0 0 4v4H4v-4a2 2 0 0 0 0-4z" /><path d="M10 6v12" strokeDasharray="2 2" /></svg>
          {t.navCartelera}
        </a>
        <a href="#/mapa" aria-current={ruta.vista === 'mapa' ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z" /><circle cx="12" cy="10" r="2" /></svg>
          {t.navMapa}
        </a>
        <a href="#/favoritos" aria-current={ruta.vista === 'favoritos' ? 'page' : undefined}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" /></svg>
          {t.navFavoritos}
        </a>
      </nav>

      {hojaAbierta && cartelera ? (
        <HojaFiltros t={t} lista={lista} hoy={hoy} filtros={filtros} cambiar={cambiar} cerrar={() => setHojaAbierta(false)} />
      ) : null}
    </div>
  );
}

// --- Cartelera ------------------------------------------------------------------

interface PropsCartelera {
  t: Textos; lang: Idioma; setLang: (l: Idioma) => void; cartelera: Cartelera | null; error: boolean; hoy: string;
  filtros: Filtros; cambiar: (c: Partial<Filtros>) => void; limite: number; setLimite: (n: number) => void;
  abrirHoja: () => void; scrollLista: RefObject<number>;
}

function VistaCartelera({ t, lang, setLang, cartelera, error, hoy, filtros, cambiar, limite, setLimite, abrirHoja, scrollLista }: PropsCartelera) {
  const lista = cartelera?.espectaculos ?? [];
  const q = useDeferredValue(filtros.q);
  const f = useMemo(() => ({ ...filtros, q }), [filtros, q]);
  const resultados = useMemo(() => (cartelera ? filtrar(lista, f, hoy) : []), [cartelera, lista, f, hoy]);
  const contenedor = useRef<HTMLDivElement>(null);

  // Al volver de una ficha, la lista sigue donde estaba; al cambiar un filtro, vuelve arriba.
  const restaurado = useRef(false);
  useLayoutEffect(() => {
    if (!contenedor.current || !cartelera) return;
    contenedor.current.scrollTop = restaurado.current ? 0 : scrollLista.current;
    restaurado.current = true;
  }, [cartelera, f, scrollLista]);

  const contar = (cumple: (e: Espectaculo) => boolean, ignorar: 'tipo' | 'sub') =>
    lista.reduce((n, e) => n + (cumple(e) && pasa(e, f, hoy, ignorar) ? 1 : 0), 0);

  const tipos: Filtros['tipo'][] = ['todo', 'teatro', 'magia', 'circo', 'eventos'];
  const [desde, hasta] = rango(f.fecha, hoy);
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

      <div className="chips" role="group" aria-label={t.tiposLabel}>
        {tipos.map((k) => {
          const n = cartelera ? contar((e) => (k === 'todo' ? FUNCIONES.includes(e.tipo) : e.tipo === k), 'tipo') : null;
          return (
            <span key={k} className="chip-envoltorio">
              {k === 'eventos' ? <span className="separador" aria-hidden="true" /> : null}
              <button type="button" className="chip" aria-pressed={filtros.tipo === k}
                onClick={() => cambiar({ tipo: k, subMagia: 'todas', subEvento: 'todos' })}>
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

      {filtros.tipo === 'eventos' ? (
        <div className="chips" role="group" aria-label={t.tipoEvento}>
          {['todos', 'festival', 'formacion', 'charla', 'magia', 'otros'].map((k) => (
            <button key={k} type="button" className="chip pequeno" aria-pressed={filtros.subEvento === k} onClick={() => cambiar({ subEvento: k })}>
              {t.subsEvento[k]}
              {cartelera ? <span className="num">{contar((e) => e.tipo === 'eventos' && (k === 'todos' || (k === 'magia' ? !!e.tema_magia : grupoEvento(e) === k)), 'sub')}</span> : null}
            </button>
          ))}
        </div>
      ) : null}

      <div className="chips" role="group" aria-label={t.cuando}>
        {(['todo', 'hoy', 'manana', 'finde', 'semana'] as ClaveFecha[]).map((k) => (
          <button key={k} type="button" className="chip pequeno" aria-pressed={filtros.fecha === k} onClick={() => cambiar({ fecha: k })}>
            {t.fechas[k]}
          </button>
        ))}
      </div>

      <div className="resumen">
        <span aria-live="polite">{error ? t.error : cartelera ? t.resultados(resultados.length) : ''}</span>
        <button type="button" className="boton-filtros" onClick={abrirHoja} disabled={!cartelera}>
          <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 7h10M18 7h2M4 17h4M12 17h8" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="17" r="2" /></svg>
          <span>{t.filtros}</span>
          {nFiltros > 0 ? <span className="insignia">{nFiltros}</span> : null}
        </button>
      </div>

      <div className="lista" ref={contenedor}>
        {!cartelera && !error ? <p className="aviso">{t.cargando}</p> : null}
        {error ? <p className="aviso">{t.error}</p> : null}
        {resultados.slice(0, limite).map((e) => (
          <Tarjeta key={e.id} e={e} t={t} desde={desde} hasta={hasta}
            alAbrir={() => { scrollLista.current = contenedor.current?.scrollTop ?? 0; }} />
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

function Etiquetas({ e, t }: { e: Espectaculo; t: Textos }) {
  const publico = publicoTxt(e, t);
  return (
    <span className="etiquetas">
      <span className={e.tipo === 'magia' || e.tema_magia ? 'etiqueta destacada' : 'etiqueta'}>{tipoTxt(e, t)}</span>
      {publico ? <span className="etiqueta suave">{publico}</span> : null}
      {e.nivel ? <span className="etiqueta suave">{t.nivelTxt(t.niveles[e.nivel] || e.nivel)}</span> : null}
    </span>
  );
}

function Tarjeta({ e, t, desde, hasta, alAbrir }: { e: Espectaculo; t: Textos; desde: string; hasta: string; alAbrir: () => void }) {
  const fs = funcionesEnRango(e, desde, hasta);
  const [dia, hora] = fs[0];
  const precio = precioTxt(e, t);
  const lugar = [e.sala, e.barrio].filter(Boolean).join(' · ');
  return (
    <a className="tarjeta" href={enlaceFicha(e.id)} onClick={alAbrir}>
      <Etiquetas e={e} t={t} />
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

function Ficha({ t, lang, e, hoy, volver }: { t: Textos; lang: Idioma; e: Espectaculo; hoy: string; volver: () => void }) {
  const [sinImagen, setSinImagen] = useState(false);
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
        <button type="button" className="boton-icono" disabled aria-label={t.favoritoPronto} title={t.favoritoPronto}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" /></svg>
        </button>
      </div>
      <div className="ficha">
        {e.imagen && !sinImagen ? (
          <img className="ficha-imagen" src={e.imagen} alt={`${t.imagen} «${e.nombre}»`} width={760} height={428}
            loading="lazy" referrerPolicy="no-referrer" onError={() => setSinImagen(true)} />
        ) : null}
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
          {fs.slice(0, 6).map(([dia, hora], i) => (
            <span key={`${dia}-${hora}-${i}`} className="funcion">
              <span>{fmtDia(dia, t)}</span>
              {hora ? <span className="texto-claro">{hora}</span> : null}
            </span>
          ))}
          {fs.length > 6 ? <span className="texto-suave">{t.mas(fs.length - 6)}</span> : null}
          {fs.length === 0 ? <span className="texto-suave">{t.sinFechas}</span> : null}
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

        {e.tipo === 'magia' ? (
          <section className="caja discontinua">
            <h3 className="caja-titulo">{t.magoTit}</h3>
            <p className="texto-suave">{t.magoTxt}</p>
          </section>
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

// --- Más filtros (hoja que sube desde abajo) -----------------------------------------

function HojaFiltros({ t, lista, hoy, filtros, cambiar, cerrar }: {
  t: Textos; lista: Espectaculo[]; hoy: string; filtros: Filtros; cambiar: (c: Partial<Filtros>) => void; cerrar: () => void;
}) {
  const primero = useRef<HTMLButtonElement>(null);
  const n = useMemo(() => filtrar(lista, filtros, hoy).length, [lista, filtros, hoy]);
  const indefinido = filtros.precioMax == null;
  const precioTxtFiltro = indefinido ? t.indefinido : t.hasta(filtros.precioMax as number);

  useEffect(() => {
    const anterior = document.activeElement as HTMLElement | null;
    primero.current?.focus();
    const tecla = (ev: KeyboardEvent) => { if (ev.key === 'Escape') cerrar(); };
    window.addEventListener('keydown', tecla);
    return () => { window.removeEventListener('keydown', tecla); anterior?.focus(); };
  }, [cerrar]);

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
          <button ref={primero} type="button" className="boton-icono relleno" onClick={cerrar} aria-label={t.cerrar}>
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
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

// --- Lo que llega en otras fases ----------------------------------------------------

function Pronto({ titulo, texto, t }: { titulo: string; texto: string; t: Textos }) {
  return (
    <main className="pantalla pronto">
      <h2>{titulo}</h2>
      <p>{texto}</p>
      <a className="boton-principal" href="#/">{t.irCartelera}</a>
    </main>
  );
}
