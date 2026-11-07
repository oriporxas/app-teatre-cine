# App de teatro/cine: brief para Claude Code
Versión 3 · 7 de noviembre de 2026

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

## Primera versión

### Búsqueda
- Por ciudad o por la ubicación actual.
- Tipo: teatro, magia, circo o eventos (el cine llega en la fase 6).
- Filtros: fecha, hora, precio e idioma de la función (catalán, castellano, otros o sin texto). En cine, también versión original subtitulada.
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
- Magia: sinopsis comercial; premios del espectáculo, si los tiene; el mago, su trayectoria y todos sus premios y reconocimientos encontrados, cada uno con su explicación, para valorar su nivel.
- Circo: de qué va; artistas o compañía; dónde comprar entradas.
- Cine (fase 6): de qué trata; premios y nominaciones; dirección, guion e intérpretes con sus trayectorias; enlaces de compra por cine; si hay versión original.
- Eventos: festivales, conferencias, ensayos abiertos, puertas abiertas, coloquios y estrenos, más talleres y formación y convocatorias de festivales (plazos para presentar espectáculos o cortos). Los festivales y las convocatorias los descubre la app. Sin castings por ahora.

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

## Pendiente de Uri
- Responder una sola vez a la prueba de magia: qué sobra, qué falta, si los que «incluyen magia» deben salir al buscar magia, qué son los dudosos y si la hipnosis de espectáculo cuenta como magia.
- Presupuesto mensual (se decide al ver el coste real en la fase 3).
- Nombre de la app (más adelante).
