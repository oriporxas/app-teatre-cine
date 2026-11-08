# App de teatro/cine (Barcelona) — guía para cada sesión

Lee esto al empezar. El brief completo está en `docs/brief.md`: es la
referencia de lo decidido. Si algo de aquí contradice el brief, manda el brief
y avisa a Uri.

## El proyecto en pocas líneas

Directorio único y actualizado de lo que hay en cartel en Barcelona (teatro,
magia, circo y eventos del sector; el cine llega en la fase 6), como web
instalable en el móvil (PWA), en castellano y catalán. Usuarios: Uri Herrera
(mago y actor) y gente del mundillo. Sin fines comerciales por ahora.

Estado (8/11/2026): fase 1 (datos) construida y probada. Pendiente de Uri:
responder a la prueba de magia (`docs/pruebas/2026-11-08-magia.md`), decidir el
modelo de IA y crear la clave `ANTHROPIC_API_KEY` en GitHub. Hasta entonces la
app clasifica solo por señales. Siguiente fase: 2 (interfaz). Ver «Plan por
fases» en el brief.

## Principios (no negociables)

1. **La app funciona sola.** Se actualiza cada día sin que nadie revise nada a
   mano. Ninguna función depende de que Uri confirme datos. Si una solución
   necesita intervención humana periódica, no vale: busca otra.
2. **Sin listas hechas a mano.** Salas, festivales, premios y eventos se
   descubren automáticamente; los espectáculos se clasifican solos. No metas
   en el código listas de espectáculos, artistas o salas concretas.
3. **Las pruebas de Uri son puntuales.** Sirven para medir y mejorar
   criterios. Lo aprendido se convierte en **criterios generales**
   (`docs/clasificacion.md`), nunca en excepciones para un espectáculo concreto.
4. **Precisión.** Cada dato lleva su fuente y la fecha de comprobación. Lo que
   no se pueda comprobar se marca «no verificado». Nunca se inventan premios,
   fechas ni repartos. Una sola ficha por obra aunque salga en varias fuentes.

## Cómo trabajar con Uri

- Uri **no sabe programar**. Explica todo paso a paso, en castellano, sin
  jerga. Si usas un término técnico, explícalo en una frase.
- Dile **exactamente** qué tiene que hacer él cuando haga falta (qué botón,
  en qué pantalla), y solo cuando haga falta.
- Uri acepta los cambios en GitHub: «Create pull request» y después «Merge
  pull request». Trabaja en la rama que indique la sesión, haz commit y push,
  y al terminar recuérdale esos dos botones con el enlace.
- Antes de pedirle algo, comprueba si puedes resolverlo tú.
- Si una decisión es suya (presupuesto, modelo de IA, qué cuenta como magia),
  explícale las opciones con su coste y recomienda una.

## Cómo está montado (fase 1)

- `pipeline/` — programa diario en Python (solo biblioteca estándar, salvo
  `anthropic` para la IA).
  - `descargar.py`: las dos agendas por la API oficial de Open Data BCN.
  - `agendas.py`: las une por identificador.
  - `guia.py`: lee la ficha pública de cada actividad en guia.barcelona.cat
    (descripción, sala, enlaces). **1 página cada 10 s** (lo pide su
    robots.txt); se guarda en caché y solo se relee si la actividad cambia.
  - `horario.py`: días, horas, precios, duración e idioma desde el texto.
  - `salas.py`: agrupa salas por dirección con la lista oficial de
    equipamientos culturales.
  - `senales.py` + `clasificar_ia.py`: clasificación en dos capas (ver
    `docs/clasificacion.md`).
  - `principal.py`: lo encadena todo. `python -m pipeline.principal --help`.
  - `prueba_magia.py`: genera el informe de la prueba de magia.
- `.github/workflows/actualizar-datos.yml` — lo ejecuta GitHub cada día a las
  05:17 UTC y guarda los resultados en `data/` con un commit automático.
- `data/espectaculos.json`, `data/salas.json`, `data/informe.json` —
  resultados. `data/cache/` — memoria entre días (fichas leídas,
  clasificaciones de la IA). No borrar la caché: cuesta horas y dinero rehacerla.
- `docs/fuentes/open-data-bcn.md` — notas técnicas de la fuente principal.
- `tests/` — `python -m unittest discover -s tests -t .` (se ejecutan también
  cada día antes del proceso).

## Cosas que conviene saber

- El fichero JSON completo de Open Data BCN y su web normal devuelven 403 a
  los programas (desde la nube de Claude y desde GitHub). La API sí funciona.
  No intentes saltarte ese bloqueo (cambiar el «User-Agent», buscar la URL
  oculta…): usa la API y la guía. Detalles en `docs/fuentes/open-data-bcn.md`.
- La IA necesita el secreto `ANTHROPIC_API_KEY` en GitHub (Settings →
  Secrets and variables → Actions). Sin él, la app clasifica solo por señales
  y lo indica en cada ficha (`clasificado_por`).
- GitHub Actions da 2.000 minutos gratis al mes en repositorios privados. El
  proceso diario debe quedarse en unos 40 minutos como mucho.
- Al escribir código que llame a Claude, consulta la referencia actualizada
  de la API (no la memoria): modelos, precios y parámetros cambian.
- Los textos de la agenda están en catalán; la traducción al castellano llega
  con la interfaz (fase 2).
