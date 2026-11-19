"""Prepara la vista previa de Claude (uso: python3 herramientas/preparar_vista_previa.py <carpeta> <proyecto>): copia la app construida y los datos, y como la vista previa
no deja cargar imágenes de otras webs, descarga los carteles de TMDB (permitido por sus
condiciones, con la atribución) y los sirve desde la propia página."""
import json, sys, shutil, urllib.request, hashlib, pathlib, time
S = pathlib.Path(sys.argv[1]); RAIZ = pathlib.Path(sys.argv[2])
vp = S / "vista-previa"; (vp / "img").mkdir(parents=True, exist_ok=True); (vp / "datos").mkdir(exist_ok=True); (vp / "assets").mkdir(exist_ok=True)
for f in (vp / "assets").glob("*"): f.unlink()
dist = RAIZ / "web" / "dist"
for f in (dist / "assets").glob("*"): shutil.copy(f, vp / "assets" / f.name)
for n in ("barcelona.json", "barcelona-mapa.json", "barcelona-noticias.json"):
    shutil.copy(RAIZ / "web/public/datos" / n, vp / "datos" / n)
for f in (RAIZ / "web/public/datos").glob("barcelona-personas-*.json"):  # fichas ampliadas de personas
    shutil.copy(f, vp / "datos" / f.name)
plantilla = vp / "cartelera-barcelona.html"
if not plantilla.exists():  # la página que carga la app (herramientas/vista-previa-plantilla.html)
    shutil.copy(pathlib.Path(__file__).with_name("vista-previa-plantilla.html"), plantilla)
cine = json.load(open(RAIZ / "web/public/datos/barcelona-cine.json"))
def local(url, ancho):
    if not url or "image.tmdb.org" not in url:
        return None
    url = url.replace("/w500/", f"/{ancho}/").replace("/w1280/", f"/{ancho}/").replace("/w185/", f"/{ancho}/")
    nombre = hashlib.sha1(url.encode()).hexdigest()[:16] + ".jpg"
    destino = vp / "img" / nombre
    if not destino.exists():
        try:
            destino.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "CarteleraBarcelona/1.0"}), timeout=30).read())
            time.sleep(0.05)
        except Exception:
            return None
    return f"./img/{nombre}"
n = 0
for i, p in enumerate(cine["peliculas"]):
    c = local(p.get("cartel"), "w342")
    if c: p["cartel"] = c; n += 1
    if i < 30:
        f = local(p.get("fondo"), "w780")
        if f: p["fondo"] = f
    if i < 20:
        for x in (p.get("direccion") or []) + (p.get("reparto") or [])[:6]:
            fo = local(x.get("foto"), "w185")
            if fo: x["foto"] = fo
json.dump(cine, open(vp / "datos/barcelona-cine.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("carteles locales:", n, "| imágenes:", len(list((vp / "img").glob("*"))), "| MB:", round(sum(f.stat().st_size for f in (vp / "img").glob("*")) / 1e6, 1))
idx = (dist / "index.html").read_text()
import re
css = re.search(r'href="\./assets/([^"]+\.css)"', idx).group(1); js = re.search(r'src="\./assets/([^"]+\.js)"', idx).group(1)
pag = (vp / "cartelera-barcelona.html").read_text()
pag = re.sub(r'assets/index-[^"]+\.css', f"assets/{css}", pag); pag = re.sub(r'assets/index-[^"]+\.js', f"assets/{js}", pag)
pag = pag.replace("family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap", "family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;0,900;1,600&display=swap")
pag = pag.replace('content="#121214"', 'content="#0A0A0B"').replace("background: #121214", "background: #0A0A0B")
(vp / "cartelera-barcelona.html").write_text(pag)
print(css, js)
