// Buscador único (obras, películas, personas, salas y cines) y ficha de persona, que une el
// teatro y el cine: quien dirige una película y actúa en una obra sale con las dos cosas.
import { useLayoutEffect, useMemo, useRef } from 'react';
import type { Espectaculo } from './datos';
import type { CarteleraCine, Persona, Premio } from './cine';
import { tituloPeli } from './cine';
import { normaliza, tipoTxt } from './filtros';
import type { Idioma, Textos } from './textos';
import { Cartelito, PremiosLista, clavePersona, enlaceCine, enlacePeli } from './Cine';

export interface FichaPersona {
  clave: string;
  nombre: string;
  foto?: string;
  premios?: Premio[];
  wikidata?: string;
  pelis: { id: string; titulo: string; rol: string }[];
  obras: { id: string; titulo: string; rol: string }[];
}

const slug = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

/** Nombres de una línea de la ficha artística: «Anna Prova, Joan Exemple i Marta Exemple». */
export function separarNombres(s: string): string[] {
  return s.split(/\s*(?:,|;|\/|\s+i\s+|\s+y\s+|\s+&\s+)\s*/).map((x) => x.trim())
    .filter((x) => x.length > 3 && x.length < 60 && /^[A-ZÀ-Ý]/.test(x) && x.split(' ').length <= 6);
}

export function indicePersonas(lista: Espectaculo[], cine: CarteleraCine | null, lang: Idioma, t: Textos): Map<string, FichaPersona> {
  const res = new Map<string, FichaPersona>();
  const porNombre = new Map<string, string>();
  const obtener = (clave: string, nombre: string) => {
    let f = res.get(clave);
    if (!f) {
      f = { clave, nombre, pelis: [], obras: [] };
      res.set(clave, f);
      porNombre.set(slug(nombre), clave);
    }
    return f;
  };
  for (const p of cine?.peliculas || []) {
    const titulo = tituloPeli(p, lang);
    const anade = (xs: Persona[] | undefined, rol: string) => {
      for (const x of xs || []) {
        const f = obtener(clavePersona(x), x.nombre);
        if (x.foto && !f.foto) f.foto = x.foto;
        if (x.premios?.length && !f.premios) f.premios = x.premios;
        if (x.wikidata) f.wikidata = x.wikidata;
        if (!f.pelis.some((y) => y.id === p.id)) f.pelis.push({ id: p.id, titulo, rol: x.papel ? `${rol} · ${x.papel}` : rol });
      }
    };
    anade(p.direccion, t.comoDireccion);
    anade(p.reparto, t.comoReparto);
    anade(p.guion, t.guion);
  }
  for (const e of lista) {
    for (const [papel, nombres] of e.equipo || []) {
      for (const n of separarNombres(nombres)) {
        const clave = porNombre.get(slug(n)) || `n-${slug(n)}`;
        const f = obtener(clave, n);
        if (!f.obras.some((y) => y.id === e.id)) f.obras.push({ id: e.id, titulo: e.nombre, rol: t.papel(papel) });
      }
    }
  }
  return res;
}

const enlaceFicha = (id: string) => `#ficha-${id.replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '')}`;

export function VistaBuscar({ t, lang, q, setQ, lista, cine, personas, hoy }: {
  t: Textos; lang: Idioma; q: string; setQ: (q: string) => void; lista: Espectaculo[]; cine: CarteleraCine | null;
  personas: Map<string, FichaPersona>; hoy: string;
}) {
  const entrada = useRef<HTMLInputElement>(null);
  useLayoutEffect(() => { window.scrollTo(0, 0); entrada.current?.focus({ preventScroll: true }); }, []);
  const n = normaliza(q.trim());
  const r = useMemo(() => {
    if (n.length < 2) return null;
    const obras = lista.filter((e) => e.funciones.some(([d]) => d >= hoy) && normaliza([e.nombre, e.artista, e.sala, ...(e.equipo || []).map((x) => x[1])].join(' ')).includes(n)).slice(0, 30);
    const pelis = (cine?.peliculas || []).filter((p) => normaliza([p.titulo, p.titulo_ca, p.titulo_original, ...(p.direccion || []).map((x) => x.nombre), ...(p.reparto || []).map((x) => x.nombre)].join(' ')).includes(n)).slice(0, 30);
    const gente = [...personas.values()].filter((p) => normaliza(p.nombre).includes(n))
      .sort((a, b) => (b.pelis.length + b.obras.length) - (a.pelis.length + a.obras.length)).slice(0, 20);
    const salas = new Map<string, { nombre: string; enlace: string; detalle: string }>();
    for (const e of lista) if (e.sala && normaliza(e.sala).includes(n) && !salas.has(e.sala)) salas.set(e.sala, { nombre: e.sala, enlace: '#cartelera', detalle: e.barrio || '' });
    for (const c of cine?.cines || []) if (normaliza(c.nombre).includes(n)) salas.set(c.id, { nombre: c.nombre, enlace: enlaceCine(c.id), detalle: c.barrio || '' });
    return { obras, pelis, gente, salas: [...salas.values()].slice(0, 15) };
  }, [n, lista, cine, personas, hoy]);
  const total = r ? r.obras.length + r.pelis.length + r.gente.length + r.salas.length : 0;
  return (
    <main className="pantalla">
      <header className="cabecera">
        <div className="titulo"><h1>{t.buscarTitulo}</h1></div>
        <div className="buscador">
          <label htmlFor="buscar-todo" className="oculto">{t.buscarLabel}</label>
          <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
          <input ref={entrada} id="buscar-todo" type="search" enterKeyHint="search" autoComplete="off" value={q} placeholder={t.buscarTodo}
            onChange={(e) => setQ(e.target.value)} />
        </div>
      </header>
      <div className="lista">
        {!r ? <p className="aviso">{t.escribeParaBuscar}</p> : null}
        {r && total === 0 ? <p className="aviso">{t.sinResultados}</p> : null}
        {r?.gente.length ? (
          <section className="bloque">
            <h3 className="seccion-titulo">{t.personas}</h3>
            {r.gente.map((p) => (
              <a key={p.clave} className="fila-resultado" href={`#persona-${p.clave}`}>
                <Cartelito src={p.foto} alt={p.nombre} clase="mini-cartel redonda" />
                <span>
                  <span className="caja-titulo">{p.nombre}{p.premios?.some((x) => x.tipo === 'ganado') ? ' ★' : ''}</span>
                  <span className="texto-suave">{[p.pelis.length ? t.peliculas(p.pelis.length) : '', p.obras.length ? `${t.escena}: ${p.obras.length}` : ''].filter(Boolean).join(' · ')}</span>
                </span>
              </a>
            ))}
          </section>
        ) : null}
        {r?.pelis.length ? (
          <section className="bloque">
            <h3 className="seccion-titulo">{t.peliculasTit}</h3>
            {r.pelis.map((p) => (
              <a key={p.id} className="fila-resultado" href={enlacePeli(p.id)}>
                <Cartelito src={p.cartel} alt={tituloPeli(p, lang)} clase="mini-cartel" />
                <span><span className="caja-titulo">{tituloPeli(p, lang)}</span><span className="texto-suave">{[p.anio, (p.direccion || []).map((d) => d.nombre).join(', ')].filter(Boolean).join(' · ')}</span></span>
              </a>
            ))}
          </section>
        ) : null}
        {r?.obras.length ? (
          <section className="bloque">
            <h3 className="seccion-titulo">{t.obras}</h3>
            {r.obras.map((e) => (
              <a key={e.id} className="fila-resultado" href={enlaceFicha(e.id)}>
                <Cartelito src={e.imagen} alt={e.nombre} clase="mini-cartel" />
                <span><span className="caja-titulo">{e.nombre}</span><span className="texto-suave">{[tipoTxt(e, t), e.sala].filter(Boolean).join(' · ')}</span></span>
              </a>
            ))}
          </section>
        ) : null}
        {r?.salas.length ? (
          <section className="bloque">
            <h3 className="seccion-titulo">{t.lugares}</h3>
            {r.salas.map((s) => (
              <a key={s.nombre} className="fila-resultado" href={s.enlace}>
                <span><span className="caja-titulo">{s.nombre}</span><span className="texto-suave">{s.detalle}</span></span>
              </a>
            ))}
          </section>
        ) : null}
      </div>
    </main>
  );
}

export function VistaPersona({ t, p, volver }: { t: Textos; p: FichaPersona | undefined; volver: () => void }) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, [p?.clave]);
  return (
    <main className="pantalla">
      <div className="ficha-barra">
        <button type="button" className="boton-volver" onClick={volver} aria-label={t.volver}>
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 5l-7 7 7 7" /></svg>
          {t.volver.split(' ')[0]}
        </button>
      </div>
      {!p ? <div className="ficha"><p className="aviso">{t.sinResultados}</p></div> : (
        <div className="ficha">
          <div className="persona-cabecera">
            <Cartelito src={p.foto} alt={p.nombre} clase="persona-foto grande" />
            <div>
              <span className="sobretitulo">{t.fichaPersona}</span>
              <h2>{p.nombre}</h2>
            </div>
          </div>
          {p.premios?.length ? (
            <section className="bloque">
              <h3>{t.premiosTit}</h3>
              <PremiosLista premios={p.premios} t={t} max={10} />
              <span className="nota">{t.personaPremiosNota}{p.wikidata ? <> · <a href={`https://www.wikidata.org/wiki/${p.wikidata}`} target="_blank" rel="noopener noreferrer">Wikidata</a></> : null}</span>
            </section>
          ) : null}
          <section className="bloque">
            <h3>{t.enCartel}</h3>
            {p.pelis.map((x) => (
              <a key={x.id} className="fila-resultado" href={enlacePeli(x.id)}>
                <span><span className="caja-titulo">{x.titulo}</span><span className="texto-suave">{t.navCine} · {x.rol}</span></span>
              </a>
            ))}
            {p.obras.map((x) => (
              <a key={x.id} className="fila-resultado" href={enlaceFicha(x.id)}>
                <span><span className="caja-titulo">{x.titulo}</span><span className="texto-suave">{t.escena} · {x.rol}</span></span>
              </a>
            ))}
          </section>
        </div>
      )}
    </main>
  );
}
