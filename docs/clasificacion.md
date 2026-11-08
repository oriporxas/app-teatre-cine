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

- **teatro**: obras de teatro de cualquier género (drama, comedia, musical, teatro familiar e infantil, títeres y marionetas, clown teatral, monólogos y stand-up, improvisación, cabaret y variedades, lecturas dramatizadas, zarzuela).
- **magia**: espectáculos cuya **razón única y principal** es que un mago, ilusionista, mentalista o hipnotizador haga magia en directo ante el público. Incluye el ilusionismo, la magia de cerca, la magia de escena, la cartomagia, el escapismo, la magia cómica y la magia familiar, **el mentalismo y la hipnosis de espectáculo** (los dos son ramas de la magia). Cada espectáculo de magia lleva un **subtipo**, que la app mostrará como etiqueta y servirá para filtrar:
  - `magia de cerca`: a pocos centímetros del público, en mesa o en salas pequeñas (close-up, «màgia de prop», cartomagia, magia de salón o de cámara);
  - `mentalismo`: lectura de la mente, predicciones, telepatía, «lo imposible en tu mente»;
  - `hipnosis`: hipnosis de espectáculo con voluntarios;
  - `magia general`: magia de escena, grandes ilusiones, magia familiar o cómica, o cuando mezcla varias sin que domine una.
- **circo**: circo clásico y contemporáneo, acrobacias, malabares, aéreos, equilibrios, payasos de circo.
- **danza**: espectáculos cuya disciplina principal es la danza (contemporánea, ballet, flamenco, danzas urbanas…).
- **evento**: actividades del sector de las artes escénicas que no son una función normal. Subtipos: `festival` (festivales, muestras y ciclos), `formación` (talleres, cursos, clases, masterclass), `conferencia o coloquio` (charlas, mesas redondas, presentaciones, encuentros), `ensayo abierto`, `puertas abiertas`, `estreno` (presentación o gala de estreno), `convocatoria` (plazos para presentar espectáculos, cortos o proyectos) y `premios` (galas, concursos, entregas de premios).
- **cine**: proyecciones y ciclos de cine (se mostrarán en la fase 6).
- **otro**: todo lo que no es del sector: conciertos y ópera, exposiciones, visitas guiadas y rutas, deportes, mercados y ferias, cuentacuentos y narración oral, espectáculos de divulgación o sensibilización (medio ambiente, ciencia…), talleres de otras materias (cocina, pintura, manualidades, informática…), actos institucionales.

### Relación con la magia (campo aparte)

Además del tipo, cada actividad tiene un campo **magia**:

- `principal`: el tipo es «magia». **Solo estos salen al buscar magia** (decisión de Uri, 8/11/2026).
- `incluye`: espectáculo de otro tipo (circo, humor, variedades, divulgación…) que hace algún número de magia de verdad, de forma secundaria. Se guarda como información, pero **no sale al buscar magia**.
- `tema`: evento cuyo tema es la magia: festival de magia, taller o curso de magia, conferencia sobre magia. **Los talleres de magia son «evento > formación» con magia = tema**, nunca «magia».
- `no`: sin relación con la magia. También cuando la magia solo es el argumento de una historia (ver criterio 4).

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
10. **Decide siempre.** Si dudas, elige la opción más probable y baja la confianza (0,5 o menos si es casi un empate; 0,9 o más si es evidente).
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
     (de cerca, general, mentalismo o hipnosis).

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
| `tipo` | teatro, magia, circo, danza, evento, cine u otro |
| `subtipo` | etiqueta breve (formación, festival…); en magia, el tipo de magia: magia de cerca, magia general, mentalismo o hipnosis |
| `magia` | principal, incluye, tema o no (al buscar magia solo salen los «principal») |
| `confianza` | de 0 a 1 |
| `motivo` | frase que explica la decisión |
| `clasificado_por` | «ia» o «señales» |
| `modelo_ia` | qué modelo decidió (si fue la IA) |
| `pistas` | lo que encontró la capa de señales |

### Coste y modelo

- Modelos provisionales (`ajustes/ia.toml`): `claude-haiku-5-5` para
  clasificar y `claude-opus-5-5` para revisar los dudosos. Se cambian
  editando ese archivo, sin tocar el código. Cuando se active la IA se
  probarán Haiku 5.5, Sonnet 5.5 y Opus 5.5 con la prueba de magia para
  elegir con datos (aciertos y coste), y el trabajo nocturno pasará al
  procesamiento por lotes (Batch), que cuesta la mitad.
- Se envían 10 actividades por petición (5 en la revisión) y las
  instrucciones van en caché.
- No todo se envía a la IA: de ~6.900 actividades vigentes, unas 1.800 son
  candidatas (las demás son claramente conciertos, exposiciones, visitas,
  talleres de otras materias…).
- Estimación (precios de octubre de 2026: Haiku 5.5 a 0,10 $/0,50 $ y Opus
  5.5 a 4 $/20 $ por millón de tokens de entrada/salida; a confirmar con el
  coste real). Todo con Haiku: unos 0,30 $ la primera vez y menos de 1 $/mes.
  Todo con Opus: unos 10–15 $ la primera vez y 10–20 $/mes. Con la
  combinación prevista (Haiku y solo los dudosos a Opus), según cuántos
  dudosos salgan, algo intermedio: del orden de 2–5 $ la primera vez y unos
  pocos dólares al mes. El informe diario (`informe.json` de cada ciudad,
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
