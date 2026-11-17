"""Enlace de compra de cada obra: la página de la obra en la web oficial de su sala.

La agenda municipal suele dar como «enlace de compra» la portada de la web de la sala (225 de
322 obras en noviembre de 2026): al pulsarlo, había que buscar la obra a mano. Para cada obra
cuyo enlace es una portada, se busca en esa misma web la página de la obra:

1. Enlaces de la portada y del mapa del sitio (sitemap.xml), solo de la misma web.
2. Se elige el enlace cuyo texto o dirección contiene las palabras del título. Si dos páginas
   distintas encajan igual de bien, no se elige ninguna: mejor la portada que una obra equivocada.
3. Se comprueba que esa página habla de la obra (el título está en su encabezado).
4. Si la página tiene un único botón de compra propio (no el del menú de toda la web), ese es el
   enlace; si no, la propia página de la obra, donde se compra.

Nada de listas de salas: sirve para cualquier web. Se respetan robots.txt y las pausas de cada web
(`pipeline/cine/red.py`). Lo encontrado se guarda 7 días; cada día solo se buscan las obras nuevas.

La app dice qué tipo de enlace es («compra_tipo»): «obra» (página o compra de la obra) o «sala»
(solo la portada de la sala: el botón dice «Web de la sala», no «Comprar»).
"""

from __future__ import annotations

import datetime as dt
import html
import re
import time
import urllib.parse

from . import config
from .cine import red
from .util import guardar_json, leer_json, normalizar

DIAS_VALIDEZ = 7
MINUTOS_MAX = 8  # tiempo máximo buscando cada día (lo que no dé tiempo, al día siguiente; la tarea diaria no debe pasar de ~40 min)
PORTADAS = {"", "ca", "es", "en", "cat", "esp", "index.php", "index.html", "index.htm", "inici", "inicio", "home",
            "ca/inici", "es/inicio", "ca/home", "es/home"}
VACIAS = {"el", "la", "els", "les", "los", "las", "lo", "de", "del", "dels", "d", "l", "i", "y", "a", "al", "en", "un",
          "una", "the", "of", "and", "per", "amb", "con", "por", "para", "que", "s", "o", "u"}
NO_OBRA = re.compile(r"/(tag|tags|etiqueta|category|categoria|categories|author|autor|feed|wp-content|wp-json|page/\d)"
                     r"|\.(jpe?g|png|gif|webp|svg|pdf|zip|mp4|css|js|xml)$", re.I)
TEXTO_COMPRA = re.compile(r"\b(compra|comprar|compreu|compra entrades|entrades|entradas|tickets?|buy|reserva|reservar|"
                          r"reserveu|reserves)\b")


def es_portada(url: str | None) -> bool:
    if not url:
        return False
    p = urllib.parse.urlsplit(url.strip())
    consulta = not p.query or re.fullmatch(r"(lang|idioma|l)=\w+", p.query)
    return p.path.strip("/").lower() in PORTADAS and bool(consulta)


def palabras(texto: str) -> set[str]:
    return {w for w in normalizar(texto or "").split() if w not in VACIAS}


def encaje(titulo: str, encontradas: set[str]) -> float:
    """Cuánto del título está en `encontradas` (0 a 1), o 0 si no basta para darlo por la misma obra.

    Títulos de hasta 3 palabras: todas. Más largos: el 80 %, o el 60 % si están las 3 primeras
    (las webs acortan los títulos largos: «La segunda venida de Cristo o el yo de la rubia» →
    «La segunda venida de Cristo»)."""
    lista = [w for w in normalizar(titulo or "").split() if w not in VACIAS]
    t = set(lista)
    if not t:
        return 0.0
    nota = len(t & encontradas) / len(t)
    if len(t) <= 3:
        return nota if nota == 1.0 else 0.0
    if nota >= 0.8 or (nota >= 0.6 and set(lista[:3]) <= encontradas):
        return nota
    return 0.0


def _misma_web(a: str, b: str) -> bool:
    ha = urllib.parse.urlsplit(a).netloc.lower().removeprefix("www.")
    hb = urllib.parse.urlsplit(b).netloc.lower().removeprefix("www.")
    return ha == hb or ha.endswith("." + hb) or hb.endswith("." + ha)


def enlaces(pagina: str, base: str) -> list[tuple[str, str]]:
    """(dirección completa, texto) de cada enlace <a href> de la página."""
    res = []
    for m in re.finditer(r"<a\b[^>]*?href=[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", pagina, re.S | re.I):
        href = html.unescape(m.group(1)).strip()
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        texto = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()
        res.append((urllib.parse.urljoin(base, href), texto))
    return res


def _del_sitemap(raiz: str, limite: int = 6) -> list[str]:
    """Direcciones del mapa del sitio (sitemap.xml y sus hijos más prometedores)."""
    rp, _, _ = red._reglas(raiz)
    mapas = list((rp.site_maps() if rp else None) or []) or [f"{raiz}/sitemap.xml"]
    urls, vistos = [], set()
    while mapas and len(vistos) < limite:
        m = mapas.pop(0)
        if m in vistos:
            continue
        vistos.add(m)
        cont = red.pedir(m, timeout=25)
        if not cont:
            continue
        texto = cont.decode("utf-8", "replace")
        locs = [html.unescape(x).strip() for x in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", texto)]
        if "<sitemapindex" in texto:
            hijos = [x for x in locs if not re.search(r"image|attachment|author|category|tag|post_tag|media", x, re.I)]
            # primero los que suenan a obras o eventos
            hijos.sort(key=lambda x: 0 if re.search(r"espect|obra|show|event|progra|produc|activ|funci|teatre|teatro", x, re.I) else 1)
            mapas = hijos + mapas
        else:
            urls += locs
    return urls


def _palabras_url(url: str) -> set[str]:
    p = urllib.parse.urlsplit(url)
    return palabras(re.sub(r"[-_/.+]", " ", urllib.parse.unquote(p.path)))


def elegir(titulo: str, candidatos: list[tuple[str, str]], web: str) -> str | None:
    """La página de la obra entre los enlaces de la web, o None si no hay una clara."""
    t = palabras(titulo)
    if not t or not any(len(w) >= 4 or w.isdigit() and len(w) >= 2 for w in t):
        return None  # título demasiado corto o genérico para buscarlo con seguridad
    puntos: dict[str, tuple[float, int, int]] = {}
    en_portada = {u.split("#")[0] for u, texto in candidatos if texto}
    for url, texto in candidatos:
        if not url.startswith("http") or not _misma_web(url, web) or es_portada(url) or NO_OBRA.search(url):
            continue
        en_url = _palabras_url(url)
        c = palabras(texto) | en_url
        nota = encaje(titulo, c)
        if not nota:
            continue
        url = url.split("#")[0]
        # Mejor: más palabras del título; después, enlazada desde la portada (lo que está en
        # cartel ahora, no una temporada pasada del mapa del sitio); después, menos palabras de más.
        valor = (nota, 1 if url in en_portada else 0, -len(en_url - t))
        if url not in puntos or valor > puntos[url]:
            puntos[url] = valor
    if not puntos:
        return None
    mejor = max(puntos.values())
    empatados = [u for u, v in puntos.items() if v == mejor]
    # La misma obra en dos idiomas (/ca/obra y /es/obra) no es un empate: misma última parte.
    finales = {urllib.parse.urlsplit(u).path.rstrip("/").rsplit("/", 1)[-1] for u in empatados}
    if len(finales) > 1:
        return None
    empatados.sort(key=lambda u: (0 if "/ca/" in u or "/ca" == urllib.parse.urlsplit(u).path[:3] else 1, len(u)))
    return empatados[0]


def habla_de(pagina: str, titulo: str) -> bool:
    """¿El encabezado de la página (title, h1, h2, og:title) contiene el título de la obra?"""
    trozos = re.findall(r"<title[^>]*>(.*?)</title>|<h[12][^>]*>(.*?)</h[12]>|property=[\"']og:title[\"'][^>]*content=[\"']([^\"']+)",
                        pagina, re.S | re.I)
    cabecera = palabras(" ".join(re.sub(r"<[^>]+>", " ", html.unescape(x)) for g in trozos for x in g if x))
    return encaje(titulo, cabecera) > 0


_MENUS = re.compile(r"<(nav|header|footer)\b.*?</\1>", re.S | re.I)


def menus(pagina: str, base: str) -> set[str]:
    """Enlaces del menú, la cabecera y el pie: los que salen en todas las páginas de la web."""
    return {u.split("#")[0] for m in _MENUS.finditer(pagina) for u, _ in enlaces(m.group(0), base)}


def limpia(url: str) -> str:
    """Sin parámetros de seguimiento (_gl, utm_…, fbclid…): el mismo enlace, más limpio."""
    p = urllib.parse.urlsplit(url)
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
         if not re.match(r"(_gl|_ga|utm_\w+|fbclid|gclid|mc_\w+)$", k)]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q), ""))


def boton_compra(pagina: str, url_obra: str, del_menu: set[str], titulo: str | None = None) -> str | None:
    """El único enlace de compra propio de la página de la obra (no los del menú de la web).

    Con `titulo`, el enlace tiene que nombrar la obra (en su dirección o en su texto). Error del
    17/11/2026: en la página de una obra, el único botón «Entrades» era de OTRA obra (un recuadro
    de «otros espectáculos»). Si el botón no nombra la obra, se usa la página de la obra."""
    del_menu = del_menu | menus(pagina, url_obra)
    cuerpo = _MENUS.sub(" ", pagina)
    propios: dict[str, str] = {}
    for u, texto in enlaces(cuerpo, url_obra):
        u = u.split("#")[0]
        if (u.startswith("http") and TEXTO_COMPRA.search(normalizar(texto)) and u not in del_menu
                and u.rstrip("/") != url_obra.split("#")[0].rstrip("/") and not es_portada(u)):
            propios[u] = propios.get(u, "") + " " + texto
    if len(propios) != 1:
        return None
    u, texto = next(iter(propios.items()))
    if titulo and not encaje(titulo, palabras(texto) | _palabras_url(u)):
        return None
    return limpia(u)


def aplicar(ciudad, items: list[dict], informe: dict, leer_webs: bool = True) -> None:
    """Pone en cada obra el mejor enlace de compra y su tipo («obra» o «sala»)."""
    ruta = config.carpeta_cache(ciudad.id, "compra") / "obras.json"
    cache = leer_json(ruta, {}) or {}
    hoy = dt.date.today()
    fin = time.monotonic() + MINUTOS_MAX * 60
    webs: dict[str, tuple[list[tuple[str, str]], set[str]]] = {}
    inf = {"con_enlace": 0, "portadas": 0, "buscadas_hoy": 0, "encontradas": 0, "obra": 0, "sala": 0}
    for it in items:
        url = it.get("compra")
        if not url:
            continue
        inf["con_enlace"] += 1
        if not es_portada(url):
            it["compra_tipo"] = "obra"
            inf["obra"] += 1
            continue
        inf["portadas"] += 1
        clave = f"{it['id']}|{url}|{it.get('nombre')}"
        reg = cache.get(clave)
        caducado = not reg or (hoy - dt.date.fromisoformat(reg["fecha"])).days >= DIAS_VALIDEZ
        if caducado and leer_webs and time.monotonic() < fin:
            raiz = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
            try:
                if raiz not in webs:
                    portada = red.pedir(url, timeout=25)
                    texto = portada.decode("utf-8", "replace") if portada else ""
                    de_portada = enlaces(texto, url)
                    webs[raiz] = (de_portada + [(u, "") for u in _del_sitemap(raiz)], menus(texto, url))
                candidatos, del_menu = webs[raiz]
                encontrada, final = elegir(it.get("nombre") or "", candidatos, url), None
                if encontrada:
                    pagina = red.pedir(encontrada, timeout=25)
                    pagina = pagina.decode("utf-8", "replace") if pagina else ""
                    if pagina and habla_de(pagina, it.get("nombre") or ""):
                        final = boton_compra(pagina, encontrada, del_menu, it.get("nombre")) or limpia(encontrada)
                reg = {"fecha": hoy.isoformat(), "url": final}
                cache[clave] = reg
                inf["buscadas_hoy"] += 1
            except Exception as e:  # noqa: BLE001 - una web rara no para la exportación
                inf.setdefault("errores", []).append(f"{raiz}: {type(e).__name__}")
        if reg and reg.get("url"):
            it["compra"] = reg["url"]
            it["compra_sala"] = url
            it["compra_tipo"] = "obra"
            inf["encontradas"] += 1
            inf["obra"] += 1
        else:
            it["compra_tipo"] = "sala"
            inf["sala"] += 1
    # Solo se guardan las búsquedas de obras que siguen en cartel.
    vivas = {f"{it['id']}|{it.get('compra_sala') or it.get('compra')}|{it.get('nombre')}" for it in items}
    guardar_json(ruta, {k: v for k, v in cache.items() if k in vivas})
    informe["compra"] = inf
