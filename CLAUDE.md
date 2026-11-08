# App de teatro/cine (Barcelona) — guía para cada sesión

Lee esto al empezar. El brief completo está en `docs/brief.md`: es la
referencia de lo decidido. Si algo de aquí contradice el brief, manda el brief
y avisa a Uri.

## El proyecto en pocas líneas

Directorio único y actualizado de lo que hay en cartel en Barcelona (teatro,
magia, circo y eventos del sector; el cine llega en la fase 6), como web
instalable en el móvil (PWA), en castellano y catalán. Usuarios: Uri Herrera
(mago y actor) y gente del mundillo. Sin fines comerciales por ahora.

Estado (8/11/2026): fase 1 (datos) construida y probada. Prueba de magia
respondida por Uri y aplicada a los criterios (ver abajo). Pendiente de Uri:
avisar cuándo activar la IA (entonces, prueba de los tres modelos y creación de
la clave `ANTHROPIC_API_KEY`). Hasta entonces la app clasifica solo por señales.
Siguiente fase: 2 (interfaz). Ver «Plan por fases» en el brief.

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

## Qué es magia (decisiones de Uri, 8/11/2026)

- Es magia solo si es la **razón única y principal**: un mago, ilusionista,
  mentalista o hipnotizador haciendo magia en directo. **El mentalismo y la
  hipnosis de espectáculo son magia.**
- **Al buscar magia solo salen los de tipo «magia».** Los que solo «incluyen»
  algo de magia no salen.
- **La magia como argumento** de una obra, un cuento o un taller infantil
  (una librería mágica, un mago que hay que encontrar…) **no es magia**. Hay
  que entender la descripción, no buscar la palabra.
- Cada espectáculo de magia lleva su **tipo de magia**: magia de cerca, magia
  general, mentalismo o hipnosis. La búsqueda podrá filtrar por él.
- Sus respuestas están guardadas como datos de evaluación en
  `docs/pruebas/2026-11-08-respuestas-uri.json`: úsalas para medir cualquier
  cambio de criterios o de modelo de IA
  (`python -m pipeline.prueba_magia salida.md --respuestas <archivo>`).

## Visión a largo plazo (resumen; completa en el brief)

- **Hoja de ruta:** 1) artes escénicas y eventos en Barcelona hasta que
  funcione muy bien (**prioridad actual; el plan de fases no cambia**);
  2) cine en Barcelona; 3) si va bien, ciudad a ciudad hasta todo el mundo,
  quizá como negocio (por eso el repositorio es privado).
- **Dos trabajos separados, como Moovit:** la *recogida* va por detrás, a
  horas fijas, lenta la primera vez y después solo lo nuevo o cambiado; la
  *búsqueda* solo consulta la base de datos ya preparada y responde en menos
  de un segundo, haya las ciudades que haya.
- **Límites de velocidad web a web** (p. ej. 1 página cada 10 s): solo
  afectan a la recogida, nunca al usuario; se pueden leer muchas webs a la vez.
- **El coste crece con ciudades y espectáculos, no con las búsquedas.**
- **Cobertura, ciudad a ciudad:** datos abiertos; proveedores de pago donde
  los haya (cine: p. ej. International Showtimes); la IA leyendo la web de cada
  sala; y a futuro, salas y artistas publicando en la app con verificación
  automática.
- **IA dentro de la app (cuando Uri avise):** probar Haiku 5.5, Sonnet 5.5 y
  Opus 5.5 con la prueba de magia y enseñar aciertos y coste; Haiku para
  clasificar y extraer, y solo lo dudoso (según la confianza guardada) y las
  fichas de trayectoria y premios suben a un modelo superior; trabajo nocturno
  por lotes (Batch, mitad de precio). Guiar a Uri paso a paso para crear la
  clave; nunca la pegará en el chat.
- **Hoy:** nada de escala mundial, pero sin cerrarle la puerta: datos con
  ciudad y país (zona horaria, moneda, idiomas), cada fuente como pieza
  independiente y modelo de IA por tarea en un ajuste. Ver
  `docs/arquitectura.md`. Si algo choca con la visión, avisar a Uri sin
  tecnicismos.

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

Detalle y razones en `docs/arquitectura.md`.

- `ajustes/` — lo que se cambia sin programar:
  - `ciudades.toml`: cada ciudad con país, zona horaria, moneda, idiomas y
    sus fuentes. Hoy solo `barcelona`.
  - `ia.toml`: qué modelo de Claude hace cada tarea (`clasificar`,
    `revisar_dudosos`, `fichas_personas`). Valores provisionales.
- `pipeline/` — programa diario (la «recogida») en Python (biblioteca
  estándar, salvo `anthropic` para la IA).
  - `fuentes/`: **cada fuente es una pieza independiente** que entrega las
    actividades en el formato común de `fuentes/base.py`. Hoy:
    `fuentes/open_data_bcn/` (agendas por la API oficial, fichas de
    guia.barcelona.cat a **1 página cada 10 s** como pide su robots.txt,
    salas con la lista oficial de equipamientos). Para añadir una fuente:
    nueva carpeta con `recoger(ctx)` y nombrarla en `ajustes/ciudades.toml`.
  - `horario.py`: días, horas, precios, duración e idioma desde el texto.
  - `senales.py` + `clasificar_ia.py`: clasificación en dos capas (ver
    `docs/clasificacion.md`); la IA usa el modelo de cada tarea y los dudosos
    suben a un modelo superior.
  - `salas.py`: junta los lugares de cualquier fuente en salas.
  - `principal.py`: recorre ciudades y fuentes y guarda los resultados.
    `python -m pipeline.principal --help`.
  - `prueba_magia.py`: genera el informe de la prueba de magia.
- `.github/workflows/actualizar-datos.yml` — GitHub lo ejecuta cada día a las
  05:17 UTC y guarda los resultados con un commit automático.
- `data/indice.json` y `data/ciudades/<ciudad>/` — resultados de cada ciudad
  (`espectaculos.json`, `salas.json`, `clasificacion.json`, `informe.json`) y
  su memoria entre días en `cache/` (fichas leídas, decisiones de la IA). **No
  borrar la caché:** cuesta horas y dinero rehacerla.
- `docs/fuentes/open-data-bcn.md` — notas técnicas de la fuente de Barcelona.
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
