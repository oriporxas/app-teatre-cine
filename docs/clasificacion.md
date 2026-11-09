# Clasificación de espectáculos

Cómo decide la app de qué tipo es cada actividad de la agenda. Este documento
tiene dos partes:

1. **Los criterios** (entre las marcas `criterios:inicio` y `criterios:fin`).
   Son, literalmente, las instrucciones que lee la IA cada día. Si se mejoran
   aquí, la IA los aplica en la siguiente ejecución y vuelve a clasificar lo
   que haga falta. Por eso deben ser **reglas generales**, nunca excepciones
   para espectáculos concretos (principio 3 del brief).
2. **Cómo funciona por dentro** (las dos capas, qué se guarda, cuánto cuesta).

---

## 1. Criterios

<!-- criterios:inicio -->
### Tipos

Cada actividad recibe exactamente un **tipo**:

- **teatro**: obras de teatro de cualquier género (drama, comedia, teatro familiar e infantil, títeres y marionetas, clown teatral, monólogos y stand-up, improvisación, cabaret y variedades, lecturas dramatizadas, zarzuela).
- **magia**: espectáculos cuya **razón única y principal** es que un mago, ilusionista, mentalista o hipnotizador haga magia en directo ante el público. Incluye el ilusionismo, la magia de cerca, la magia de escena, la cartomagia, el escapismo, la magia cómica y la magia familiar, **el mentalismo y la hipnosis de espectáculo** (los dos son ramas de la magia). Cada espectáculo de magia lleva un **subtipo**, que la app mostrará como etiqueta y servirá para filtrar:
  - `magia de cerca`: a pocos centímetros del público, en mesa o en salas pequeñas (close-up, «màgia de prop», cartomagia, magia de salón o de cámara);
  - `mentalismo`: lectura de la mente, predicciones, telepatía, «lo imposible en tu mente»;
  - `hipnosis`: hipnosis de espectáculo con voluntarios;
  - `magia general`: magia de escena, grandes ilusiones, magia familiar o cómica, o cuando mezcla varias sin que domine una.
- **circo**: circo clásico y contemporáneo, acrobacias, malabares, aéreos, equilibrios. Un espectáculo de circo con algún payaso sigue siendo circo.
- **clown** (subtipo de teatro): cuando el clown o los payasos son la razón principal del espectáculo, el tipo es «teatro» y el subtipo «clown» (decisión de Uri, 8/11/2026). En los eventos, un taller de clown tiene disciplina «clown».
- **danza**: espectáculos cuya disciplina principal es la danza (contemporánea, ballet, flamenco, danzas urbanas…).
- **musical**: teatro musical («Musical…», «…, el musical», «Teatre musical», o cuando la descripción lo presenta como un musical: «és un musical», «aquest musical»). Un «espectacle musical» que en realidad es un concierto (un grupo que toca sus canciones) es «otro». En la app, el teatro musical sale dentro de teatro con la etiqueta «Musical» (decisión de Uri, 9/11/2026; antes no salía).
- **evento**: actividades del sector de las artes escénicas que no son una función normal. Subtipos: `festival` (festivales, muestras y ciclos), `formación` (talleres, cursos, clases, masterclass), `conferencia o coloquio` (charlas, mesas redondas, presentaciones, encuentros), `ensayo abierto`, `puertas abiertas`, `estreno` (presentación o gala de estreno), `convocatoria` (plazos para presentar espectáculos, cortos o proyectos) y `premios` (galas, concursos, entregas de premios). Cada evento lleva además su **disciplina** (teatro, magia, circo, danza, musical, música…): un taller de danza es un evento de disciplina «danza». En la app solo salen, por ahora, los eventos de teatro, magia y circo.
- **cine**: proyecciones y ciclos de cine (se mostrarán en la fase 6).
- **otro**: todo lo que no es del sector: conciertos y ópera, exposiciones, visitas guiadas y rutas, deportes, mercados y ferias, cuentacuentos y narración oral, espectáculos de divulgación o sensibilización (medio ambiente, ciencia…), talleres de otras materias (cocina, pintura, manualidades, informática…), actos institucionales.

### Relación con la magia (campo aparte)

Además del tipo, cada actividad tiene un campo **magia**:

- `principal`: el tipo es «magia». **Solo estos salen al buscar magia** (decisión de Uri, 8/11/2026).
- `incluye`: espectáculo de otro tipo (circo, humor, variedades, divulgación…) que hace algún número de magia de verdad, de forma secundaria. Se guarda como información, pero **no sale al buscar magia**.
- `tema`: evento cuyo tema es la magia: festival de magia, taller o curso de magia, conferencia sobre magia. **Los talleres de magia son «evento > formación» con magia = tema**, nunca «magia».
- `no`: sin relación con la magia. También cuando la magia solo es el argumento de una historia (ver criterio 4).

### Género de las obras de teatro (campo aparte)

En los tipos «teatro» y «musical», el campo **generos** dice el género de la obra (como mucho dos), para que la app lo muestre en la tarjeta (decisión de Uri, 9/11/2026). Valores: `musical`, `títeres`, `monólogo` (también el stand-up), `improvisación`, `clown`, `cabaret`, `teatro de objetos`, `teatro físico` (o gestual), `lectura dramatizada`, `teatro documental`, `suspense` (thriller, intriga), `tragicomedia`, `comedia` (también humor, sátira y farsa), `drama`, `tragedia`.

**Solo si es seguro**: cuando la descripción lo dice («és una comèdia», «aquest musical», «un monòleg», «un espectacle de titelles», «Gènere: Comèdia») o cuando el argumento no deja ninguna duda. Una palabra suelta no basta («una mica de comèdia», «el drama de l'habitatge», «una alta dosi d'improvisació», «direcció musical»). Si hay dudas, la lista va vacía: es mejor no poner género que ponerlo mal. En los demás tipos, la lista va vacía.

### Cómo decidir

1. **Lee y entiende la descripción, no solo el título.** El título no basta, ni para incluir ni para excluir: hay espectáculos de magia cuyo título no lo dice y que solo se reconocen por la descripción o por el artista (cuando se presenta como «Mag …», «Mago …», «Maga …», ilusionista o mentalista), y hay muchas obras con «màgia» en el título que no son magia. Usa título, descripción, sala, tipo de lugar, organizador, artista y horario.
2. **Las categorías de la agenda y las pistas automáticas son solo pistas.** Fallan en los dos sentidos: dejan fuera espectáculos de magia y meten actividades que no lo son (un mercado de Navidad, una fuente «màgica», un itinerario «Barcelona màgica»).
3. **La pregunta clave: ¿alguien hace magia en directo y es la razón del espectáculo?** Solo es «magia» si la descripción presenta a un mago, ilusionista, mentalista o hipnotizador haciendo trucos, ilusiones, mentalismo o hipnosis ante el público como eje del espectáculo («un espectacle de màgia», «la millor màgia de prop», «l'il·lusionista…», «mentalisme i màgia urbana»).
4. **La magia como argumento no es un espectáculo de magia.** Las obras de teatro infantil o familiar, los musicales, los espectáculos sobre hielo, los cuentacuentos y los talleres de manualidades usan a menudo la magia como parte de una historia de fantasía: una librería mágica, una noche mágica, un baúl mágico, un viaje mágico, un mago que hay que encontrar, un personaje que «hace magia». Eso es el argumento, no un número de magia: magia = `no`, y el tipo es el que corresponda (teatro, otro…). Lo mismo con las metáforas y el ambiente («la màgia del Nadal», «la màgia de la ciència», «un ballet ple de bellesa, màgia i encant»).
5. **Manda lo que la descripción dice que es.** Si la descripción declara el género («Contacontes a càrrec de…», «Espectacle de divulgació i sensibilització ambiental que combina màgia…», «Un espectacle musical familiar…»), ese es el tipo. Si combina algunos trucos con otra finalidad (educar, concienciar, contar un cuento), magia = `incluye` como mucho, nunca `principal`.
6. **El formato manda sobre el tema.** Un taller, curso o clase es «evento > formación» aunque sea de teatro, circo o magia. Una charla sobre teatro es «evento > conferencia o coloquio». Un concierto es «otro» aunque sea en un teatro.
7. **Disciplina principal.** Si un espectáculo mezcla disciplinas, el tipo es la que domina según la descripción. Si la magia es solo una parte (un número dentro de un espectáculo de circo, clown o variedades), el tipo es el de la disciplina principal y magia = `incluye`.
8. **Mentalismo e hipnosis son magia.** Todo espectáculo de mentalismo o de hipnosis de espectáculo es «magia», con su subtipo, aunque no use la palabra «màgia». Solo si es el número del espectáculo: un «gato hipnotizador» o un «asno mago» que son personajes de un cuento no cuentan. «Escapisme» suele significar «evasión», no el número de escapismo.
9. **Público familiar o infantil no cambia el tipo.** Un espectáculo de magia para familias («espectacle de màgia familiar») es «magia»; una obra infantil con magia en el argumento es «teatro».
10. **Teatro no es la opción por defecto.** Si nada indica que sea un espectáculo o un evento de artes escénicas (ni el formato, ni la palabra «espectáculo», ni vocabulario de la disciplina), es «otro»: una carrera popular, una feria, un aviso de cortes de tráfico, una charla sobre vivienda. Que la descripción nombre un teatro o un escenario no basta.
11. **Cuidado con las palabras que comparten varias artes.** «Direcció», «obra», «escenari», «companyia», «intèrprets», «comèdia» o «improvisació» aparecen también en danza, música, cine o pintura («una obra d'art», «la Divina comèdia», «Contact Improvisació»), y «musical» sola suele ser música («estimulació musical per a nadons»). No bastan para decir que algo es teatro: hace falta que sea teatro de verdad (una obra, títeres, clown, monólogo, cabaret…) o que lo diga la descripción.
12. **Decide siempre.** Si dudas, elige la opción más probable y baja la confianza (0,5 o menos si es casi un empate; 0,9 o más si es evidente).
<!-- criterios:fin -->

---

## 2. Cómo funciona por dentro

### Dos capas

1. **Señales** (`pipeline/senales.py`). Gratis, instantánea y explicable.
   Busca vocabulario general de cada disciplina en catalán, castellano e
   inglés (por ejemplo «il·lusionisme», «mentalisme», «a càrrec del mag»,
   «malabars», «monòleg»), mira el formato que indica la primera palabra
   del título (la agenda del Ayuntamiento escribe casi siempre «Espectacle…»,
   «Taller…», «Concert…», «Exposició…») y distingue las palabras fuertes
   («espectacle de màgia») de las ambiguas («nit màgica»). Además:
   - distingue al **artista** que se presenta como mago en el título («Mag
     Lari», «El Mago Pop», «a càrrec del mag…») del **personaje** de una
     historia («el mag escombraries», «la Maga Martina»);
   - detecta cuándo la magia es el **argumento de una historia** (aventuras,
     cuentos, hadas, Disney…) y entonces no la cuenta;
   - lee el **género que declara la descripción** («Contacontes…»,
     «Espectacle de divulgació…», «Espectacle de circ…») y le hace caso;
   - reconoce el **mentalismo** y la **hipnosis** y pone el **tipo de magia**
     (de cerca, general, mentalismo o hipnosis);
   - separa las palabras propias del teatro («teatre», «dramatúrgia», «titelles»,
     «monòleg», «clown») de las que comparten varias artes («direcció», «obra»,
     «escenari», «companyia»), que cuentan poco;
   - reconoce los **musicales** como género propio y, en los eventos, su
     **disciplina** (un taller de danza o de música no es de teatro);
   - si casi no hay vocabulario de teatro, circo o magia y sí de danza o de
     música, no lo da por teatro;
   - no da nada por teatro «por defecto»: si el título no dice qué es, no
     lleva la palabra «espectáculo» y casi no hay vocabulario escénico, queda
     como «otro» dudoso (confianza 0,5) y fuera de la cartelera hasta que la
     IA lo lea.

   No contiene ninguna lista de espectáculos, artistas ni salas.
   - Si no hay clave de IA, su decisión es la que se publica
     (`clasificado_por: "señales"`).
   - Si hay clave, sus pistas se le pasan a la IA como ayuda.
   - Decide qué actividades **no** hace falta enviar a la IA: las que son
     claramente ajenas (un concierto, una exposición, una visita guiada).
2. **IA** (`pipeline/clasificar_ia.py`). Claude lee los criterios de arriba y
   decide tipo, subtipo, relación con la magia, confianza y motivo
   (`clasificado_por: "ia"`). Lo hace en dos tareas, cada una con su modelo
   (`ajustes/ia.toml`):
   - `clasificar`: un modelo rápido y barato clasifica lo nuevo o cambiado;
   - `revisar_dudosos`: lo que esa tarea decidió con poca seguridad
     (confianza menor que el umbral, hoy 0,7) lo vuelve a mirar un modelo
     superior, y su decisión es la que vale (`revisado: true`).

### Solo lo nuevo o cambiado

Cada resultado de la IA se guarda en
`data/ciudades/<ciudad>/cache/ia/<tarea>.json` con
una «huella» de lo que se le enseñó (título, descripción, sala, horario,
criterios y modelo). Al día siguiente solo se envía lo que tenga una huella
distinta: actividades nuevas, modificadas por el Ayuntamiento o afectadas por
un cambio de criterios.

### Qué se guarda de cada decisión

En `data/ciudades/<ciudad>/espectaculos.json` (y en `clasificacion.json`,
en la misma carpeta, que incluye también lo descartado):

| Campo | Qué es |
|---|---|
| `tipo` | teatro, magia, circo, danza, musical, evento, cine u otro |
| `subtipo` | etiqueta breve (formación, festival…); en magia, el tipo de magia: magia de cerca, magia general, mentalismo o hipnosis |
| `disciplina` | solo en los eventos: de qué es el taller, festival o charla (teatro, magia, circo, danza, musical, música…) |
| `magia` | principal, incluye, tema o no (al buscar magia solo salen los «principal») |
| `confianza` | de 0 a 1 |
| `motivo` | frase que explica la decisión |
| `publico` | infantil, familiar, juvenil, juvenil y adultos, adultos o todos los públicos (vacío si no se dice) |
| `edad_minima`, `edad_maxima` | edades del público, si se indican |
| `nivel` | en talleres y cursos: iniciación, intermedio o avanzado |
| `clasificado_por` | «ia» o «señales» |
| `modelo_ia` | qué modelo decidió (si fue la IA) |
| `pistas` | lo que encontró la capa de señales |

### Público y nivel

`pipeline/publico.py` saca de los textos a quién va dirigida cada actividad
(«(de 6 a 12 anys)», «a partir de 12 anys», «adults», «Adreçat a nens i nenes
de 8 a 12 anys», «per a tota la família») y, en la formación, el nivel
(«iniciació», «no cal experiència», «avançat», «coneixements previs»). Reglas
generales:

- Solo cuentan las edades que hablan del público («adreçat a…», «edat
  recomanada…», o entre paréntesis en el título). En un festival de jóvenes
  magos «d'entre 14 i 25 anys», esa es la edad de los concursantes, no la del
  público.
- En el título de un espectáculo, «Adultos» o «Adolescentes» pueden ser el
  nombre de la obra: solo cuenta «per a adults» o «majors de 18». En el
  título de un taller, «adults» sí indica el público («Màgia adults avançat»).
- «A partir de 3 anys» indica un espectáculo familiar; «a partir de 8 anys»,
  apto para todos los públicos desde esa edad.
- «10 € per adult» es un precio, no el público.

### Coste y modelo

- Modelos (`ajustes/ia.toml`), elegidos con la prueba de los tres modelos del
  8/11/2026 (`docs/pruebas/2026-11-08-prueba-modelos.md`):
  `claude-sonnet-5-5` (esfuerzo medio) para clasificar y `claude-opus-5-5`
  para revisar los dudosos (confianza < 0,7, aprox. 1 de cada 10). Haiku
  acertó la magia igual, pero en los casos difíciles se equivoca con mucha
  confianza, y la revisión de dudosos no lo corrige. Se cambian editando ese
  archivo, sin tocar el código. El trabajo nocturno pasará al procesamiento
  por lotes (Batch), que cuesta la mitad.
- Se envían 10 actividades por petición (5 en la revisión) y las
  instrucciones van en caché.
- No todo se envía a la IA: de ~6.900 actividades vigentes, unas 1.800 son
  candidatas (las demás son claramente conciertos, exposiciones, visitas,
  talleres de otras materias…).
- Coste medido en la prueba (por 1000 actividades): Haiku 0,13–0,17 $,
  Sonnet 2,1 $, Opus 4,3–5,3 $. Con Sonnet y la revisión de dudosos con Opus,
  en Barcelona: unos 4,6 $ la primera vez (1712 candidatas) y como mucho
  12 $/mes (6 $ por lotes), contando 150 novedades al día. El informe diario (`informe.json` de cada ciudad,
  apartado `ia`) guarda los tokens gastados por tarea para medir el coste
  real.

### Historial de pruebas

- **7/11/2026 (sesión en el Mac):** el título no basta («Cleptómago» e
  «Inexplicable» solo se reconocían por la descripción y «Hangar 52», por
  el artista). La categoría «màgia» de la agenda se dejaba «Hangar 52» y la
  ponía en 6 actividades que no eran magia. Los talleres de magia van a
  «Eventos > formación». → Criterios 1, 2, 3 y 4.
- **7–8/11/2026 (sesión en la nube):** primera prueba de magia del programa,
  con la capa de señales (todavía sin clave de IA), en
  `docs/pruebas/2026-11-08-magia.md`. Al revisarla salieron criterios
  generales nuevos: números y ordinales al principio del título («17è
  Festival…») no son el formato; galas de premios son «evento › premios»;
  «màgia» usada para crear ambiente no cuenta; los personajes (un gato
  hipnotizador, un asno mago) no son números; en los cuentacuentos la magia
  del título es el tema del cuento; «mágico» con acento castellano también es
  una palabra ambigua.
- **8/11/2026, respuestas de Uri** (al final de `docs/pruebas/2026-11-08-magia.md`):
  la magia como argumento de una obra, un cuento o un taller infantil no es
  un espectáculo de magia; un espectáculo de magia lo es como razón única y
  principal; los que solo «incluyen» magia no salen al buscar magia; el
  mentalismo y la hipnosis son magia; cada espectáculo de magia lleva su
  tipo (de cerca, general, mentalismo o hipnosis). → Criterios 3, 4, 5 y 8 y
  los subtipos de magia. Al aplicarlos se vio otro criterio general: en las
  descripciones, los personajes también van en mayúscula («la Maga
  Martina»), así que «Mag/Mago» con mayúscula solo indica un artista en el
  título.
- **8/11/2026, nueva medición** (`docs/pruebas/2026-11-08-magia-medicion.md`):
  con los criterios nuevos, la capa de señales coincide en **55 de 55**
  decisiones con las respuestas de Uri (16 espectáculos de magia, 5 eventos
  sobre magia y 34 que no lo son). Ojo: se ha medido con los mismos ejemplos
  de los que salieron los criterios, así que no garantiza el mismo acierto
  con espectáculos nuevos. La medición de verdad vendrá con las semanas y con
  la IA, que se medirá con el mismo archivo de respuestas
  (`docs/pruebas/2026-11-08-respuestas-uri.json`).
- **8/11/2026, eventos:** Uri confirmó los cinco eventos sobre magia y pidió
  distinguir su tipo (talleres infantiles o para adultos, festivales…). →
  Cada ficha lleva ahora `publico`, edades y, en la formación, `nivel`; el
  informe de la prueba agrupa los eventos por tipo.
- **8/11/2026, al montar la app (fase 2):** con la cartelera a la vista
  aparecieron como «teatro» actividades que no lo son (un aviso de cortes de
  tráfico por una carrera, una media maratón, una feria de manga, una bienal
  de arte digital), porque la capa de señales daba por teatro todo lo que
  no tenía disciplina clara. → Criterio 10: sin formato en el título, sin la
  palabra «espectáculo» y casi sin vocabulario escénico, es «otro» dudoso.
  Salen de la cartelera 45 actividades; la medición de magia sigue en 55 de
  55.
- **8/11/2026, Uri prueba la app:** salían muchos talleres y espectáculos que
  no eran de teatro, magia ni circo (danza, musicales, talleres de música para
  bebés…). Decisión de Uri: por ahora, solo teatro, magia y circo. → Los
  musicales son un tipo propio; cada evento lleva su disciplina; las palabras
  que comparten varias artes cuentan poco (criterio 11); y la app no publica
  lo dudoso (confianza menor de 0,6) hasta que la IA lo lea. La app pasa de
  944 a 633 actividades. La medición de magia sigue en 55 de 55.
- **8/11/2026, Uri revisa los eventos:** pide quitar «Sobre magia» y «Otros»
  (todo tiene que estar clasificado) y poner el clown en teatro con su
  etiqueta. → El clown tiene vocabulario propio, separado del circo y del
  teatro; con el clown como razón principal es teatro › clown. Los eventos se
  filtran por su tipo real y muestran su disciplina. Magia: 55 de 55.
- **9/11/2026, Uri pide ver el género de las obras:** en teatro salían
  musicales sin etiqueta y quiere saber el género de un vistazo. → Nuevo campo
  `generos` (como mucho dos) en teatro y musical, solo si es seguro
  (`pipeline/genero.py`: etiqueta de la fuente, frase explícita o título; una
  palabra suelta no basta y las contradicciones anulan). El teatro musical
  seguro sale dentro de teatro con la etiqueta «Musical»; el «espectacle
  musical» sin más espera a la IA. Resultado: 175 de 527 obras con género
  (comedia 68, monólogo 55, musical 36, títeres 23…). La IA devolverá también
  `generos`. Magia: 54 de 54 (una de las 55 ya no está en cartel).
