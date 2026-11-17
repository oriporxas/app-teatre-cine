// Noticias de teatro, cine, magia y circo (titular, medio, resumen y enlace al original).
import { useLayoutEffect, useState } from 'react';
import type { Idioma, Textos } from './textos';

export interface Noticia {
  titulo: string;
  enlace: string;
  medio: string;
  fecha: string;
  idioma?: string;
  tema: 'teatro' | 'cine' | 'magia' | 'circo';
  /** Festival, gala o premios, feria, convención, taller… */
  evento?: boolean;
  resumen?: Record<string, string>;
  imagen?: string;
}

export async function cargarNoticias(ciudad: string): Promise<Noticia[]> {
  const r = await fetch(`./datos/${ciudad}-noticias.json`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return (await r.json()).noticias;
}

export function hace(fecha: string, t: Textos): string {
  const h = Math.max(0, Math.floor((Date.now() - Date.parse(fecha)) / 3600000));
  return t.haceHoras(h);
}

export function TarjetaNoticia({ n, t, lang, compacta }: { n: Noticia; t: Textos; lang: Idioma; compacta?: boolean }) {
  const [sinImagen, setSinImagen] = useState(false);
  return (
    <a className={compacta ? 'noticia compacta' : 'noticia'} href={n.enlace} target="_blank" rel="noopener noreferrer">
      {n.imagen && !sinImagen ? (
        <img className="noticia-imagen" src={n.imagen} alt="" loading="lazy" referrerPolicy="no-referrer" onError={() => setSinImagen(true)} />
      ) : null}
      <span className="noticia-texto">
        <span className="noticia-meta">
          <span className={`tema tema-${n.tema}`}>{t.temasNoticia[n.tema]}</span>
          {n.evento ? <span className="tema tema-evento">{t.temasNoticia.evento}</span> : null}
          <span>{n.medio} · {hace(n.fecha, t)}</span>
        </span>
        <span className="noticia-titulo">{n.titulo}</span>
        {!compacta && n.resumen?.[lang] ? <span className="texto-suave">{n.resumen[lang]}</span> : null}
      </span>
    </a>
  );
}

export function VistaNoticias({ t, lang, noticias, error }: { t: Textos; lang: Idioma; noticias: Noticia[] | null; error: boolean }) {
  const [tema, setTema] = useState('todo');
  useLayoutEffect(() => { window.scrollTo(0, 0); }, []);
  const pasa = (n: Noticia, k: string) => k === 'todo' || (k === 'eventos' ? !!n.evento : n.tema === k);
  const lista = (noticias || []).filter((n) => pasa(n, tema));
  return (
    <main className="pantalla">
      <header className="cabecera">
        <div className="titulo"><span className="sobretitulo">{t.noticiasSub}</span><h1>{t.noticiasTitulo}</h1></div>
      </header>
      <div className="chips" role="group" aria-label={t.noticiasTitulo}>
        {['todo', 'teatro', 'cine', 'magia', 'circo', 'eventos'].map((k) => (
          <button key={k} type="button" className="chip" aria-pressed={tema === k} onClick={() => setTema(k)}>
            {t.temasNoticia[k]}
            {noticias ? <span className="num">{(noticias || []).filter((n) => pasa(n, k)).length}</span> : null}
          </button>
        ))}
      </div>
      <div className="lista">
        {!noticias && !error ? <p className="aviso">{t.cargando}</p> : null}
        {error ? <p className="aviso">{t.error}</p> : null}
        {lista.map((n) => <TarjetaNoticia key={n.enlace} n={n} t={t} lang={lang} />)}
        {noticias && lista.length === 0 ? <p className="aviso">{t.vacio}</p> : null}
        {noticias ? <p className="nota">{t.resumenIA}</p> : null}
      </div>
    </main>
  );
}
