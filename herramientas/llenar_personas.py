"""Rellena de una vez las fichas ampliadas de personas (TMDB y Wikidata, gratis), sin el tope diario
de 8 minutos. Necesita TMDB_TOKEN. Uso, desde la carpeta del proyecto:
    TMDB_TOKEN=... python3 herramientas/llenar_personas.py"""
import json, sys, os, time
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ)); os.chdir(RAIZ)
from pipeline import ajustes, biografias
biografias.MINUTOS_MAX = 25
c = ajustes.ciudades()['barcelona']
inf = {}
t0 = time.time()
biografias.aplicar(c, inf, leer_webs=True)
print(json.dumps(inf, ensure_ascii=False, indent=1), round(time.time() - t0), "s")
