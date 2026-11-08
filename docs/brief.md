# App de teatro/cine: brief para Claude Code
Versión 5 · 8 de noviembre de 2026 (añadidas la «Visión a largo plazo» y las decisiones de Uri sobre la magia)

## La idea
Un directorio único y actualizado de todo lo que hay en cartel en una ciudad: teatro, magia, circo, cine y eventos del sector. Hoy hay que ir web por web o enterarse por el boca a boca. Usuarios: Uri Herrera (mago y actor) y gente del mundillo.

## Decisiones tomadas
- Ciudad (v1): Barcelona.
- Formato: web instalable en el móvil (PWA), sin tiendas de apps.
- Público: Uri y gente del mundillo (sin fines comerciales por ahora).
- Prioridad: primero las artes escénicas (teatro, magia y circo). El cine, en una fase posterior.
- Idiomas: castellano y catalán.
- Fichas de trayectoria: hechas por IA con búsqueda web, citando las fuentes.
- Presupuesto mensual: por decidir. Se mide el coste real en la fase 3.
- Experiencia técnica de Uri: ninguna. Hay que explicarle cada paso sin jerga.
- Qué es magia (Uri, 8 de noviembre, tras la prueba de magia): un espectáculo de magia lo es cuando la magia es su razón única y principal: un mago, ilusionista, mentalista o hipnotizador haciendo magia en directo. El mentalismo y la hipnosis de espectáculo cuentan como magia. Los espectáculos que solo «incluyen» algo de magia no salen al buscar magia. La magia como argumento de una obra, un cuento o un taller infantil no es magia.
- Dónde se trabaja: repositorio privado oriporxas/app-teatre-cine, con la app de Claude instalada, en sesiones de Claude Code en la nube. Uri acepta los cambios con «Create PR» y después «Merge pull request».

## Principios
1. La app funciona sola. Se actualiza cada día sin que nadie revise nada a mano. Ninguna función de la app depende de que Uri confirme datos.
2. Sin listas hechas a mano. La app descubre por sí misma las salas, los festivales, los premios y los eventos, y clasifica los espectáculos. Hay premios y festivales de mil tipos (concursos de televisión o de talentos, festivales grandes como el FISM y otros muy pequeños), y la app tiene que encontrarlos y explicarlos.
3. Las pruebas de Uri son puntuales. Sirven para medir si la app acierta y para mejorar sus criterios. Lo aprendido se convierte en criterios generales, nunca en excepciones para espectáculos concretos.
4. Precisión. Cada dato lleva su fuente y la fecha de la última comprobación. Lo que no se pueda comprobar se marca como «no verificado». Nunca se inventan premios, fechas ni repartos. Si la misma obra aparece en varias fuentes, se muestra una sola ficha. Las fichas de personas se generan una vez, se reutilizan y se revisan cada cierto tiempo.

## Clasificación automática
- La IA decide de qué tipo es cada espectáculo (teatro, magia, circo, evento, formación…) leyendo el título, la descripción, el horario, la sala y el artista.
- Lo hace cada día, solo con los espectáculos nuevos o modificados.
- Las categorías de la agenda del Ayuntamiento son solo una pista, porque fallan en los dos sentidos.
- Si duda, decide igualmente y guarda lo segura que está.
- Un espectáculo puede «incluir magia» sin ser de magia (circo, humor, variedades). Se marca aparte.
- Lo aprendido en la primera prueba de magia (7 de noviembre): el título no basta. «Cleptómago» e «Inexplicable» solo se reconocían por la descripción, y «Hangar 52», por el artista. La categoría «màgia» de la agenda se dejaba «Hangar 52» y la ponía en 6 actividades que no eran magia, como un mercado de Navidad. Los talleres de magia van a «Eventos > formación».
- Lo aprendido con las respuestas de Uri a esa prueba (8 de noviembre): hay que entender la descripción, no solo buscar la palabra «màgia». Sobraban obras, cuentos y talleres infantiles donde la magia era el argumento de la historia («La llibreria màgica», «El mag escombraries», «Disney On Ice. Un viaje mágico»…) y una actividad de sensibilización ambiental con algunos trucos. Faltaba un espectáculo de mentalismo («Lo imposible está… en tu mente»). Con los criterios corregidos, el programa coincide con las 55 respuestas de Uri (detalle en docs/pruebas/ y docs/clasificacion.md).

## Primera versión

### Búsqueda
- Por ciudad o por la ubicación actual.
- Tipo: teatro, magia, circo o eventos (el cine llega en la fase 6).
- En magia, se puede elegir el tipo de magia: magia de cerca, magia general, mentalismo o hipnosis. Si no se elige, salen todos, cada uno con la etiqueta de su tipo para distinguirlos a simple vista. Solo salen los espectáculos cuya razón principal es la magia, no los que solo la incluyen.
- Filtros: fecha, hora, precio e idioma de la función (catalán, castellano, otros o sin texto). En cine, también versión original subtitulada.
- Público al que va dirigido (infantil, familiar, juvenil, adultos o todos los públicos, con las edades si se indican) y, en talleres y cursos, nivel (iniciación, intermedio o avanzado). Lo saca la app de los textos de cada actividad.
- Mapa de salas cercanas.

### Información común de cada resultado
- Dónde se hace (sala y dirección), desde cuándo y hasta cuándo, días y horas, precio y enlace de compra.
- Críticas de prensa (extracto breve con enlace) y valoración media, si existe.

### Premios y reconocimientos (en todas las fichas)
- La app busca todos los premios, nominaciones y reconocimientos que encuentre, sean del tipo que sean.
- Cada premio lleva una explicación breve: qué certamen es, de dónde, si su alcance es local, nacional o internacional, y cuánto peso tiene en su ámbito. Así se puede valorar el nivel aunque no se conozca el certamen.
- Cada premio enlaza a su fuente. Si no se puede comprobar, se marca como «no verificado».

### Ficha según el tipo
- Teatro: de qué trata; premios y nominaciones; quién dirige y su trayectoria; dramaturgia y su trayectoria; intérpretes principales y sus trayectorias; enlaces para comprar entradas.
- Magia: tipo de magia (magia de cerca, magia general, mentalismo o hipnosis); sinopsis comercial; premios del espectáculo, si los tiene; el mago, su trayectoria y todos sus premios y reconocimientos encontrados, cada uno con su explicación, para valorar su nivel.
- Circo: de qué va; artistas o compañía; dónde comprar entradas.
- Cine (fase 6): de qué trata; premios y nominaciones; dirección, guion e intérpretes con sus trayectorias; enlaces de compra por cine; si hay versión original.
- Eventos: cada evento lleva su tipo (festival, taller o curso, charla o coloquio, ensayo abierto, puertas abiertas, estreno, convocatoria o premios), su público (por ejemplo, talleres infantiles o para adultos) y, en la formación, su nivel. Así se distinguen, por ejemplo, un taller infantil de magia, un taller avanzado para adultos y un festival como el Màgicus. Son: festivales, conferencias, ensayos abiertos, puertas abiertas, coloquios y estrenos, más talleres y formación y convocatorias de festivales (plazos para presentar espectáculos o cortos). Los festivales y las convocatorias los descubre la app. Sin castings por ahora.

### Cuenta personal
- Favoritos y alertas: estrenos, últimas funciones y plazos de convocatorias. Requiere iniciar sesión.

## Fuente principal: Open Data BCN (revisada el 7 de noviembre)
- Tiene dos agendas: «Agenda d'activitats i esdeveniments», que es la principal para espectáculos (723 de 789 solo están ahí), y «Agenda cultural». Se usan las dos y se unen por el identificador que comparte cada actividad en ambas.
- Hay unos 790 espectáculos en unas 200 salas: unos 600 de teatro y unos 27 de circo. De magia, tras una revisión a fondo, unos 17 espectáculos y un festival.
- Fechas: traen el primer y el último día. Los días y horas de cada función vienen escritos en el texto y hay que extraerlos de ahí.
- Salas: traen dirección, barrio y coordenadas (sirven para el mapa). Algunas aparecen con el nombre de la sala interior («Sala Gran», «Sala Petita») y se agrupan por dirección.
- Precios: no hay una casilla de precio. Aparecen en el texto en 2 de cada 3 espectáculos.
- Enlace de compra: está en 496 de 789, casi siempre a la portada de la web de la sala. El enlace concreto de cada obra se buscará en la fase 5.
- Idioma de la función: la mitad pone «indiferente».
- No incluye director, reparto, dramaturgia, críticas ni premios. Eso lo añade la fase 3.
- Los textos están solo en catalán y hay que traducirlos al castellano.
- Se actualiza cada noche. Se puede usar libremente citando al Ayuntamiento como fuente.
- Salas no encontradas con su nombre: Capitol, Almeria, Akademia, BARTS, Price y La Seca. Hay que comprobarlas; si faltan, se cubren en la fase 5.
- Red: el entorno en la nube necesita permiso para entrar en opendata-ajuntament.barcelona.cat. Habrá que ampliarlo cuando la app lea las webs de las salas.

## Otras fuentes
1. Agenda cultural de la Generalitat (agenda.cultura.gencat.cat).
2. Salas: se descubren automáticamente a partir de los datos abiertos de equipamientos culturales, las agendas y la búsqueda web. Después, la app lee la cartelera en la web de cada sala.
3. Festivales, convocatorias y plataformas de entradas: se descubren con las agendas y la búsqueda web.
4. Personas y premios: búsqueda web con IA y Wikipedia/Wikidata; para cine, bases de datos de películas.
5. Cine (fase 6): no hemos encontrado una API pública y gratuita de horarios de cine en España. Las opciones son las webs de cada cine o los portales de cartelera. Como referencia, en Madrid existe Madrid Film Calendar, que unifica la cartelera de esa ciudad.

Reglas: dar preferencia a los datos abiertos, respetar las condiciones de uso de cada web y no copiar críticas largas (solo un extracto breve con enlace).

## Propuesta técnica (a confirmar)
- Web instalable (PWA), por ejemplo con Next.js, alojada en un servicio con plan gratuito.
- Base de datos con usuarios para favoritos y alertas, por ejemplo Supabase.
- Recogida automática diaria con tareas programadas.
- IA (API de Claude con búsqueda web) para clasificar los espectáculos, hacer las fichas y descubrir salas, festivales y premios, con caché para controlar el coste.
- Interfaz en castellano y catalán.

## Plan por fases
0. Preparación: hecha. Repositorio creado, con la app de Claude instalada.
1. Datos (en curso): programa diario que descarga y une las dos agendas, clasifica los espectáculos, extrae fechas y precios y agrupa las salas.
2. Interfaz básica: buscador, filtros, resultados y ficha.
3. Fichas de personas y premios hechas con IA y con fuentes. Aquí se mide el coste real.
4. Funciones extra: mapa, favoritos, alertas y críticas.
5. Más fuentes: webs de las salas, enlaces de compra concretos, salas que falten, festivales y eventos profesionales.
6. Cine.

## Visión a largo plazo
Escrita el 8 de noviembre de 2026 para que no se pierda de vista en ninguna sesión. **No cambia el plan de fases**: la prioridad sigue siendo Barcelona.

### Hoja de ruta
1. **Ahora:** artes escénicas (teatro, magia y circo) y eventos en Barcelona, hasta que funcione muy bien. Esta sigue siendo la prioridad.
2. **Después:** añadir el cine en Barcelona.
3. **Si todo va bien:** crecer ciudad a ciudad hasta cubrir todo el mundo, con la posibilidad de convertir la app en un negocio. Por eso el repositorio es privado.

### Cómo tiene que funcionar a gran escala (como Moovit)
- **Dos trabajos separados:**
  - **Recoger datos:** por detrás, a horas fijas, sin que ningún usuario espere. La primera carga de cada ciudad o fuente es lenta; después, cada día solo se lee lo nuevo o cambiado.
  - **Buscar:** el usuario solo consulta la base de datos de la app, que ya está preparada. Los resultados tienen que salir en menos de un segundo, haya las ciudades que haya.
- **Los límites de velocidad se respetan web a web** (por ejemplo, una página cada 10 segundos). Esas pausas solo afectan a la recogida nocturna, nunca al usuario, y se pueden leer muchas webs distintas a la vez.
- **El coste tiene que crecer con el número de ciudades y espectáculos, no con las búsquedas de los usuarios.**

### El reto real: la cobertura
No existe un estándar mundial de carteleras de teatro, como el GTFS en el transporte público. Cada ciudad publica a su manera, así que habrá que combinar, ciudad a ciudad:
1. Datos abiertos públicos, donde existan (como Open Data BCN).
2. Proveedores de pago, donde los haya. Para el cine existen servicios de horarios con cobertura internacional, como International Showtimes.
3. La IA leyendo la web de cada sala.
4. A futuro: que salas, compañías y artistas publiquen sus propios espectáculos en la app (como la comunidad de editores de Moovit), siempre con verificación automática.

### La IA que trabaja dentro de la app
Cuando la activemos (sin prisa; Uri avisará):
- Probar los tres modelos (Haiku 5.5, Sonnet 5.5 y Opus 5.5) con la prueba de magia y enseñar a Uri aciertos y coste de cada uno, para elegir con datos.
- La idea es usar Haiku para clasificar y extraer datos, y que solo los casos dudosos y las fichas de trayectoria y premios pasen a un modelo superior. La app ya guarda lo segura que está de cada decisión: se usa para decidir qué casos suben de modelo.
- Usar el procesamiento por lotes (Batch) para el trabajo nocturno, que cuesta la mitad.
- Cuando toque crear la clave, guiar a Uri paso a paso. Uri nunca la pegará en el chat.

### Qué se hace ahora
- No se construye nada de la escala mundial todavía. Se sigue con Barcelona.
- Pero las decisiones técnicas de hoy se toman de forma que crecer no obligue a rehacerlo todo:
  - la base de datos admite varias ciudades y países, cada uno con su zona horaria, su moneda y sus idiomas;
  - cada fuente de datos es una pieza independiente, que se puede añadir o quitar sin tocar el resto;
  - la IA de la app puede cambiar de modelo según la tarea con un simple ajuste.
- Si alguna decisión ya tomada choca con esta visión, se avisa a Uri y se le explica sin tecnicismos.

## Pendiente de Uri
- Avisar cuándo activar la IA (entonces: prueba de los tres modelos y creación de la clave, paso a paso).
- Presupuesto mensual (se decide al ver el coste real en la fase 3).
- Nombre de la app (más adelante).
