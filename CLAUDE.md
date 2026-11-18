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
respondida por Uri y aplicada a los criterios (ver abajo). Fase 2 (interfaz):
la app está hecha y probada en tamaño móvil (`web/`), con la cartelera real;
**falta publicarla** (elegir alojamiento cuando se aclare lo de GitHub) y la
traducción al castellano de las descripciones, que llega con la IA. Mientras,
Uri la puede probar como página privada de Claude:
https://claude.ai/artifact/7ZSzcw6GNbXXf5idrGQw3z (se actualiza a mano: allí no
cargan las fotos de los carteles ni funciona sin conexión). Se publica desde
`web/dist` con una página que carga los archivos de la app (ver el historial).
IA (8/11/2026): Uri creó la clave en la consola de Anthropic (no caduca). Está
guardada en el entorno de la nube de Claude «app-teatre-cine» como
`CLAVE_IA_CARTELERA` (las variables `ANTHROPIC_*` no llegan a las sesiones),
y `clasificar_ia.clave()` acepta los dos nombres. La prueba de los tres modelos
está hecha (`docs/pruebas/2026-11-08-prueba-modelos.md`, costó 1,33 $).
Uri aprobó la propuesta al pedir el primer borrador completo (14/11/2026).

Primer borrador completo (17/11/2026, pedido el 14/11 con 13,24 $ de crédito):
IA activada en teatro (clasificar, traducir, premios citados, temas) y en
noticias; **cine** (`pipeline/cine/`, `docs/fuentes/cine.md`); **noticias**
(`pipeline/noticias.py`, `ajustes/noticias.toml`); diseño negro, rojo y blanco;
pantallas Inicio, Escena, Cine, Noticias, Guardado, buscador único y personas.
Informe y gasto (~7,3 $): `docs/pruebas/2026-11-17-primer-borrador.md`.
GitHub volvió el 14/11/2026: ya se puede hacer push. Secretos `ANTHROPIC_API_KEY` y
`TMDB_TOKEN` en GitHub: **creados por Uri** (lo confirmó el 17/11/2026; no volver a
preguntárselo). Claude no puede leer los secretos: se comprueban en el registro de la tarea
diaria (sale `***` si existen). Comprobado el 17/11/2026 en la ejecución manual (run
44197396365): los dos llegan, 141 pruebas bien, 44 min, 0,51 $, 626 fichas en la app, commit
automático «Datos del …» hecho. La tarea programada vuelve a salir sola (18/11, con una hora de
retraso de GitHub), pero ese día la API del Ayuntamiento respondió 403 a GitHub en la primera
consulta: ahora un 403 se reintenta dos veces con pausa larga (`descargar.py`) y hay un segundo
intento a las 13:17 UTC que solo trabaja si faltan los datos del día. Pendiente de Uri:
elegir alojamiento.
**Antes de dar algo por pendiente o hecho, comprobarlo** (no fiarse de notas antiguas).

Maqueta de la fase 2 (8/11/2026, con 112 actividades reales): prototipo de
móvil en https://claude.ai/artifact/9WzwWKvR8AT6zFEhQKjvrU (cartelera con
pestañas, fechas, buscador, filtros, idioma ES/CA, ficha y avance de mapa y
favoritos). Uri aprobó el aspecto y pidió cambios (precio con deslizable,
idiomas, ocultar lo no indicado), ya aplicados y anotados en el brief.

Historial (8-14/11/2026, ya resuelto): GitHub suspendió la cuenta de Uri (oriporxas) sin explicar
el motivo; se le propuso escribir a soporte. Mientras dure, no hay acceso al
repositorio ni se ejecuta la tarea diaria. Uri tiene copias completas del
proyecto. No crear otra cuenta para esquivar la suspensión.
Soporte respondió (8/11/2026): sus sistemas automáticos marcaron actividad
para revisión manual y preguntan cómo piensa usar GitHub. Se le preparó a Uri
una respuesta sincera (proyecto personal sin ánimo de lucro, código escrito
con Claude Code mediante la app de GitHub, una tarea diaria de Actions que
recoge datos abiertos respetando robots.txt) ofreciendo cambiar lo que haga
falta. Si GitHub pone pegas a la tarea diaria, plan B: hacer la recogida
fuera de GitHub (servidor pequeño en la nube) y dejar GitHub solo para el
código. Uri avisó el 14/11/2026 de que le devolvieron la cuenta.

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
- Los **eventos** se distinguen por su tipo (festival, taller, charla…), su
  **público** (infantil, familiar, juvenil, adultos…) y, en la formación, su
  **nivel** (`pipeline/publico.py`): p. ej., taller infantil de magia, taller
  avanzado para adultos o un festival como el Màgicus.
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
- **IA dentro de la app:** prueba de los tres modelos hecha (8/11/2026,
  `docs/pruebas/2026-11-08-prueba-modelos.md`). Todos aciertan la magia, pero
  Haiku falla los casos difíciles muy seguro de sí mismo. Propuesta pendiente
  de Uri: Sonnet clasifica y solo lo dudoso (según la confianza guardada) y
  las fichas de trayectoria y premios suben a Opus; Haiku, para extraer
  datos sin interpretar. Trabajo nocturno por lotes (Batch, mitad de precio). Guiar a Uri paso a paso para crear la
  clave; nunca la pegará en el chat.
- **Compartir planes (Uri, 9/11/2026):** con los amigos por cualquier vía
  (redes sociales, historias de Instagram, WhatsApp, SMS, correo…). Hoy:
  menú de compartir del móvil con el plan en texto y una imagen vertical para
  historias (`imagenPlan` en `web/src/planes.ts`). Pendiente: enlace que abre el
  plan en la app (sin servidor, el plan dentro del enlace, cuando la app esté
  publicada) y, con cuentas, planes en grupo. Detalle en el brief.
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
    `revisar_dudosos`, `fichas_personas`). Elegidos con la prueba de modelos
    (8/11/2026), pendientes del visto bueno de Uri.
- `pipeline/` — programa diario (la «recogida») en Python (biblioteca
  estándar, salvo `anthropic` para la IA).
  - `fuentes/`: **cada fuente es una pieza independiente** que entrega las
    actividades en el formato común de `fuentes/base.py`. Hoy:
    `fuentes/open_data_bcn/` (agendas por la API oficial, fichas de
    guia.barcelona.cat a **1 página cada 10 s** como pide su robots.txt,
    salas con la lista oficial de equipamientos) y `fuentes/webs_salas/`
    (Uri, 17/11/2026: la web oficial de los teatros que no salen en la agenda,
    según `cobertura.json`; la IA extrae con citas literales que el programa
    comprueba; ver `docs/veracidad.md`). Para añadir una fuente:
    nueva carpeta con `recoger(ctx)` y nombrarla en `ajustes/ciudades.toml`.
  - `horario.py`: días, horas, precios, duración e idioma desde el texto.
  - `publico.py`: a quién va dirigida cada actividad (y edades) y el nivel de
    los talleres.
  - `senales.py` + `clasificar_ia.py`: clasificación en dos capas (ver
    `docs/clasificacion.md`); la IA usa el modelo de cada tarea y los dudosos
    suben a un modelo superior.
  - `salas.py`: junta los lugares de cualquier fuente en salas.
  - `principal.py`: recorre ciudades y fuentes y guarda los resultados.
    `python -m pipeline.principal --help`.
  - `prueba_magia.py`: genera el informe de la prueba de magia.
  - `exportar_web.py`: al final de cada día escribe la cartelera de cada
    ciudad para la app (`web/public/datos/<ciudad>.json`): títulos limpios,
    solo lo que se sabe y solo teatro, magia, circo y sus eventos.
  - `equipo.py`: equipo artístico desde la ficha artística de la descripción.
  - `genero.py`: género de las obras de teatro, solo si es seguro.
  - `ia.py`: cliente de la IA, coste de cada petición y **freno de gasto** por
    ejecución (`[presupuesto]` de `ajustes/ia.toml`); registro en
    `data/gasto_ia.json`. Toda tarea de IA pasa por aquí.
  - `enriquecer_ia.py`: traducción, premios citados (con la cita literal, que
    se comprueba) y temas de cada ficha publicada (tarea «traducir»).
  - `cine/`: cartelera de cine (salas, lectores de horarios, TMDB y Wikidata).
  - `noticias.py`: noticias de los medios de `ajustes/noticias.toml` (teatro, cine, magia,
    circo y la marca «evento»: festival, gala, feria, taller…).
  - `verificar.py`: **nada sale en la app sin pasar sus comprobaciones** (precio escrito tal
    cual en la fuente, fechas dentro del periodo, horas, sala, mapa, equipo, enlaces, sesiones
    de cine). Lo que falla no se enseña y queda en `verificacion.json`. Ver `docs/veracidad.md`.
  - `compra.py`: busca en la web de la sala la página de la obra (la agenda da la portada);
    `compra_tipo` «obra» o «sala» (el botón lo dice).
  - `cobertura.py`: lista oficial de teatros, auditorios y cines contra lo que tenemos
    (`cobertura.json`): qué salas se escapan.
- `web/` — la app (fase 2): React + Vite, web instalable en el móvil (PWA).
  El móvil descarga el archivo de su ciudad y busca dentro (rápido, gratis,
  sin conexión). Cómo probarla y construirla: `web/LEEME.md`
  (`npm run check`, `npm run build`).
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

- **Veracidad (Uri, 17/11/2026, lo más importante):** cada error que se encuentre se arregla en
  la causa **y** se añade una prueba con el caso real (`tests/test_verificar.py`,
  `tests/test_horario.py`…). Los precios no pasan por `normalizar` (quitaba los decimales:
  «24.95 €» salía «95 €»). Detalle y siguiente paso propuesto (lector de webs de salas, con
  coste): `docs/veracidad.md`.
- Cambios de pantalla de Uri (17/11/2026): barra de abajo Inicio, Escena, Cine, Planes, Desat
  (solo lo guardado), Notícies; en la película, cada cine es un desplegable con sus horas; la
  hora lleva a la compra de esa sesión (Mooby, Verdi y Renoir lo permiten); en Inicio, fila de
  «Salas» (página `#teatro-<id>`); en el plan: Compartir (con «stories» dentro), Añadir a mi
  calendario, «Ruta del día» con mapa propio y botones a Google/Apple Maps, lápiz para el
  nombre y «Borrar plan» abajo con pregunta; fondo de telón color vino muy apagado.

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
  con la IA. Mientras, la ficha muestra el texto en catalán con una nota.
- La app solo enseña lo que se sabe: si falta un dato (duración, público,
  idioma, precio, enlace de compra), su recuadro no aparece. Las fotos de los
  carteles se muestran desde el servidor de la guía de Barcelona.
- Funciones (teatro, magia, circo) y eventos (festivales, talleres, charlas)
  nunca se mezclan en los resultados.
- **Por ahora la app es solo de teatro, magia y circo** (Uri, 8/11/2026): los
  eventos solo si son de esas disciplinas; fuera danza, conciertos y talleres
  de otras materias (los musicales salen desde el 9/11, ver abajo). Lo dudoso
  (confianza < 0,6) no se publica hasta que la IA lo lea
  (`pipeline/exportar_web.py`).
- La ficha muestra el equipo artístico cuando la descripción trae la ficha
  artística («Direcció: …», «Intèrprets: …»): `pipeline/equipo.py` la copia
  tal cual, sin deducir nada.
- Las fotos de los carteles **no se descargan**: el robots.txt de su servidor
  (estatics-nasia.dtibcn.cat) prohíbe el acceso automático. La app solo las
  enlaza y las carga el móvil de cada persona. Por eso no se ven en la vista
  previa de Claude, que no deja cargar imágenes de otras webs.
- Fechas: «Hoy», «Mañana», «Esta semana», «Este mes» y «Calendario» (por
  meses, hasta dos años vista, para elegir un día o un intervalo). Por eso
  `horario.interpretar` calcula las funciones de 731 días y la app las recibe
  todas.
- Clown: teatro con subtipo «clown» (Uri, 8/11/2026). Eventos: sin «Sobre
  magia» ni «Otros»; se filtran por su tipo real y llevan su `disciplina`.
- Mapa (fase 4): `web/src/Mapa.tsx` dibuja los distritos de
  `web/public/datos/<ciudad>-mapa.json` (los da la fuente: `Resultado.mapa`;
  en Barcelona, `fuentes/open_data_bcn/mapa.py`, renovado cada 90 días) y un
  punto por sala. Favoritos: en el propio móvil (`web/src/favoritos.ts`).
- Planes (Uri, 9/11/2026): itinerarios con las funciones que se quieren ver,
  por días (`web/src/planes.ts`, rutas `#planes` y `#plan-<id>`). En el
  móvil; cada función guarda nombre, sala, dirección, ciudad y zona horaria
  (sirve aunque la obra salga de cartel o sea de otra ciudad). Avisos de
  funciones que coinciden, ruta del día, paso al calendario (.ics) y compartir.
- Género de las obras (Uri, 9/11/2026): `pipeline/genero.py` lo pone **solo si
  es seguro** (lo dice la descripción o el título; una palabra suelta no
  basta). La IA, cuando se active, también lo deduce del argumento si no hay
  dudas (campo `generos`). La tarjeta lo enseña y Teatro filtra por género.
- Musicales (Uri, 9/11/2026): salen dentro de teatro con la etiqueta
  «Musical», solo si es seguro que es teatro musical (un «espectacle musical»
  puede ser un concierto). Interruptor: `MUSICALES_EN_TEATRO` en
  `pipeline/exportar_web.py`.
- Diseño (Uri, 14/11/2026): negro, rojo y blanco; títulos en Playfair Display,
  textos en Inter; el rojo de texto es `--acento-texto` (legible sobre negro) y el
  de fondo, `--acento` (con texto blanco). Sesiones de cine como «entradas».
- Cine: la app carga `web/public/datos/<ciudad>-cine.json`; rutas `#cine`,
  `#peli-<id>`, `#sala-<id>`, `#mapa-cine`. Noticias: `<ciudad>-noticias.json`,
  ruta `#noticias`. Buscador: `#buscar`; personas: `#persona-<clave>`
  (`t<id TMDB>` o `n-<nombre>`). La sesión de cine se añade a un plan con «+».
- En las sesiones de Claude en la nube: la IA con `CLAVE_IA_CARTELERA` y TMDB
  con `TMDB_TOKEN=proxy-injected` (la red pone la clave). Antes de lanzar algo que
  gaste, fijar un tope con `IA_TOPE_USD`.
- Ubicación (Uri, 8/11/2026): `web/src/ubicacion.ts` (GPS con permiso, o
  marcar el punto en el mapa) entra en los filtros (`cerca`, `orden`,
  `distanciaMax`). Nunca sale del móvil. En la vista previa de Claude el GPS
  no está disponible: allí se prueba marcando en el mapa.
- La página se desplaza entera (no hay zonas con desplazamiento propio): así
  funciona en cualquier móvil y dentro de otras apps.
