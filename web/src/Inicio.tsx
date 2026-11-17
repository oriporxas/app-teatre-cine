// Inicio: qué ver hoy de un vistazo (escena y cine), estrenos, últimos días, magia y noticias.
import { useLayoutEffect, useMemo } from 'react';
import type { Cartelera, Espectaculo } from './datos';
import { esEstreno, minutosHasta, tituloPeli, type CarteleraCine, type Pelicula } from './cine';
import { fmtDia, sumaDias, tipoTxt } from './filtros';
import type { Idioma, Textos } from './textos';
import { Cartelito, Version, enlaceCine, enlacePeli } from './Cine';
import { TarjetaNoticia, type Noticia } from './Noticias';

const enlaceFicha = (id: string) => `#ficha-${id.replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '')}`;

function Fila({ titulo, enlace, t, children }: { titulo: string; enlace?: string; t: Textos; children: React.ReactNode }) {
  return (
    <section className="fila-inicio">
      <div className="fila-cabecera">
        <h2 className="seccion-titulo">{titulo}</h2>
        {enlace ? <a className="ver-todo" href={enlace}>{t.verTodo}</a> : null}
      </div>
      <div className="carrusel">{children}</div>
    </section>
  );
}

function PosterObra({ e, t, detalle }: { e: Espectaculo; t: Textos; detalle: string }) {
  return (
    <a className="poster" href={enlaceFicha(e.id)}>
      <Cartelito src={e.imagen} alt={e.nombre} clase="poster-imagen" />
      <span className="poster-tipo">{tipoTxt(e, t)}</span>
      <span className="poster-nombre">{e.nombre}</span>
      <span className="poster-detalle">{detalle}</span>
    </a>
  );
}

function PosterPeli({ p, lang, detalle, estreno, t }: { p: Pelicula; lang: Idioma; detalle: string; estreno?: boolean; t: Textos }) {
  return (
    <a className="poster" href={enlacePeli(p.id)}>
      <Cartelito src={p.cartel} alt={tituloPeli(p, lang)} clase="poster-imagen vertical" />
      {estreno ? <span className="poster-cinta">{t.estreno}</span> : null}
      <span className="poster-nombre">{tituloPeli(p, lang)}</span>
      <span className="poster-detalle">{detalle}</span>
    </a>
  );
}

export function VistaInicio({ t, lang, setLang, cartelera, cine, noticias, hoy, ahora, irABuscar }: {
  t: Textos; lang: Idioma; setLang: (l: Idioma) => void; cartelera: Cartelera | null; cine: CarteleraCine | null;
  noticias: Noticia[] | null; hoy: string; ahora: string; irABuscar: () => void;
}) {
  useLayoutEffect(() => { window.scrollTo(0, 0); }, []);
  const lista = cartelera?.espectaculos ?? [];
  const hora = Number(ahora.split(':')[0] || 12);

  const datos = useMemo(() => {
    const fin7 = sumaDias(hoy, 7);
    const funcionesHoy = (e: Espectaculo) => e.funciones.filter(([d, h]) => d === hoy && (!h || h >= ahora));
    const escenaHoy = lista.filter((e) => e.tipo !== 'eventos' && funcionesHoy(e).length)
      .sort((a, b) => ((funcionesHoy(a)[0][1] || '99') < (funcionesHoy(b)[0][1] || '99') ? -1 : 1));
    const magia = lista.filter((e) => e.tipo === 'magia' && e.funciones.some(([d]) => d >= hoy));
    const ultimos = lista.filter((e) => {
      if (e.tipo === 'eventos') return false;
      const futuras = e.funciones.filter(([d]) => d >= hoy);
      return futuras.length > 0 && futuras[futuras.length - 1][0] <= fin7 && e.funciones[0][0] < hoy;
    });
    const pelis = cine?.peliculas || [];
    const sesHoy = (p: Pelicula) => p.sesiones.filter((s) => s[1] === hoy && (!s[2] || s[2] >= ahora));
    const cineHoy = pelis.filter((p) => sesHoy(p).length && p.cartel).sort((a, b) => sesHoy(b).length - sesHoy(a).length);
    const estrenos = pelis.filter((p) => esEstreno(p, hoy) && p.sesiones.some((s) => s[1] >= hoy));
    // Empieza pronto: lo que empieza en las próximas 2 horas, de cine y de escena
    const pronto: { enlace: string; nombre: string; lugar: string; hora: string; min: number; version?: string | null }[] = [];
    for (const e of escenaHoy) {
      const h = funcionesHoy(e)[0][1];
      const m = h ? minutosHasta(hoy, h, hoy, ahora) : null;
      if (m != null && m >= 0 && m <= 120) pronto.push({ enlace: enlaceFicha(e.id), nombre: e.nombre, lugar: e.sala || '', hora: h!, min: m });
    }
    const cinesMap = new Map((cine?.cines || []).map((c) => [c.id, c]));
    for (const p of pelis) {
      for (const s of sesHoy(p)) {
        const m = minutosHasta(s[1], s[2], hoy, ahora);
        if (m != null && m >= 0 && m <= 90) pronto.push({ enlace: enlacePeli(p.id), nombre: tituloPeli(p, lang), lugar: cinesMap.get(s[0])?.nombre || '', hora: s[2]!, min: m, version: s[3] });
      }
    }
    pronto.sort((a, b) => a.min - b.min);
    // una entrada por obra o película (la sesión más próxima)
    const vistos = new Set<string>();
    const unicos = pronto.filter((x) => (vistos.has(x.enlace) ? false : (vistos.add(x.enlace), true)));
    pronto.length = 0;
    pronto.push(...unicos);
    return { escenaHoy, magia, ultimos, cineHoy, estrenos, pronto: pronto.slice(0, 12) };
  }, [lista, cine, hoy, ahora, lang]);

  return (
    <main className="pantalla inicio">
      <header className="cabecera portada">
        <div className="cabecera-fila">
          <div className="titulo">
            <span className="sobretitulo">{t.saludo(hora)} · {fmtDia(hoy || new Date().toISOString().slice(0, 10), t)}</span>
            <span className="marca">Cartelera <em>Barcelona</em></span>
          </div>
          <div className="idiomas" role="group" aria-label="Idioma">
            {(['es', 'ca'] as Idioma[]).map((l) => (
              <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)}>{l.toUpperCase()}</button>
            ))}
          </div>
        </div>
        <h1 className="titular">{t.inicioTitulo}</h1>
        <button type="button" className="buscador falso" onClick={irABuscar}>
          <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
          <span>{t.buscarTodo}</span>
        </button>
      </header>

      {!cartelera && !cine ? <p className="aviso">{t.cargando}</p> : null}

      {datos.pronto.length ? (
        <section className="fila-inicio">
          <div className="fila-cabecera"><h2 className="seccion-titulo">{t.ahoraMismo}</h2></div>
          <div className="carrusel">
            {datos.pronto.map((x, i) => (
              <a key={`${x.enlace}-${x.hora}-${i}`} className="ticket" href={x.enlace}>
                <span className="ticket-hora">{x.hora}</span>
                <span className="ticket-cuando">{t.empiezaEn(x.min)}</span>
                <span className="ticket-nombre">{x.nombre}</span>
                <span className="ticket-lugar">{x.lugar}{x.version ? ` · ${t.versiones[x.version] || x.version}` : ''}</span>
              </a>
            ))}
          </div>
        </section>
      ) : null}

      {datos.escenaHoy.length ? (
        <Fila titulo={t.hoyEscena} enlace="#cartelera" t={t}>
          {datos.escenaHoy.slice(0, 14).map((e) => {
            const h = e.funciones.find(([d, hh]) => d === hoy && (!hh || hh >= ahora))?.[1];
            return <PosterObra key={e.id} e={e} t={t} detalle={[h, e.sala].filter(Boolean).join(' · ')} />;
          })}
        </Fila>
      ) : null}

      {datos.cineHoy.length ? (
        <Fila titulo={t.hoyCine} enlace="#cine" t={t}>
          {datos.cineHoy.slice(0, 14).map((p) => (
            <PosterPeli key={p.id} p={p} lang={lang} t={t} estreno={esEstreno(p, hoy)}
              detalle={t.sesiones(p.sesiones.filter((s) => s[1] === hoy && (!s[2] || s[2] >= ahora)).length)} />
          ))}
        </Fila>
      ) : null}

      {datos.estrenos.length ? (
        <Fila titulo={t.estrenosCine} enlace="#cine" t={t}>
          {datos.estrenos.map((p) => (
            <PosterPeli key={p.id} p={p} lang={lang} t={t} estreno detalle={[(p.generos || [])[0], p.duracion ? `${p.duracion} min` : ''].filter(Boolean).join(' · ')} />
          ))}
        </Fila>
      ) : null}

      {datos.magia.length ? (
        <Fila titulo={t.magiaDestacada} enlace="#cartelera" t={t}>
          {datos.magia.slice(0, 12).map((e) => {
            const f = e.funciones.find(([d]) => d >= hoy);
            return <PosterObra key={e.id} e={e} t={t} detalle={[f ? fmtDia(f[0], t) : '', e.sala].filter(Boolean).join(' · ')} />;
          })}
        </Fila>
      ) : null}

      {datos.ultimos.length ? (
        <Fila titulo={t.ultimosDias} enlace="#cartelera" t={t}>
          {datos.ultimos.slice(0, 12).map((e) => {
            const fut = e.funciones.filter(([d]) => d >= hoy);
            return <PosterObra key={e.id} e={e} t={t} detalle={`${t.ultimasFunciones}: ${fmtDia(fut[fut.length - 1][0], t)}`} />;
          })}
        </Fila>
      ) : null}

      {noticias?.length ? (
        <section className="fila-inicio">
          <div className="fila-cabecera">
            <h2 className="seccion-titulo">{t.ultimasNoticias}</h2>
            <a className="ver-todo" href="#noticias">{t.verTodo}</a>
          </div>
          <div className="lista sin-padding">
            {noticias.slice(0, 4).map((n) => <TarjetaNoticia key={n.enlace} n={n} t={t} lang={lang} compacta />)}
          </div>
        </section>
      ) : null}

      {cine?.cines.length ? (
        <section className="fila-inicio">
          <div className="fila-cabecera"><h2 className="seccion-titulo">{t.porCine}</h2><a className="ver-todo" href="#mapa-cine">{t.mapaCines}</a></div>
          <div className="carrusel">
            {cine.cines.filter((c) => !c.centro && cine.peliculas.some((p) => p.sesiones.some((s) => s[0] === c.id && s[1] === hoy))).map((c) => (
              <a key={c.id} className="chip-cine" href={enlaceCine(c.id)}>{c.nombre}</a>
            ))}
          </div>
        </section>
      ) : null}

      <footer className="pie">
        <p className="nota"><strong>{t.acercaDe}.</strong> {t.acercaTxt}</p>
        <p className="nota">{t.atribucionTmdb}</p>
      </footer>
    </main>
  );
}

export { Version };
