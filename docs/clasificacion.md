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
- **magia**: espectáculos cuya disciplina principal es la magia: ilusionismo, magia de cerca (close-up), magia de escena, cartomagia, mentalismo, escapismo, magia cómica o familiar. El mentalismo cuenta como magia.
- **circo**: circo clásico y contemporáneo, acrobacias, malabares, aéreos, equilibrios, payasos de circo.
- **danza**: espectáculos cuya disciplina principal es la danza (contemporánea, ballet, flamenco, danzas urbanas…).
- **evento**: actividades del sector de las artes escénicas que no son una función normal. Subtipos: `festival` (festivales, muestras y ciclos), `formación` (talleres, cursos, clases, masterclass), `conferencia o coloquio` (charlas, mesas redondas, presentaciones, encuentros), `ensayo abierto`, `puertas abiertas`, `estreno` (presentación o gala de estreno), `convocatoria` (plazos para presentar espectáculos, cortos o proyectos) y `premios` (galas, concursos, entregas de premios).
- **cine**: proyecciones y ciclos de cine (se mostrarán en la fase 6).
- **otro**: todo lo que no es del sector: conciertos y ópera, exposiciones, visitas guiadas y rutas, deportes, mercados y ferias, cuentacuentos y narración oral, talleres de otras materias (cocina, pintura, informática…), actos institucionales.

### Relación con la magia (campo aparte)

Además del tipo, cada actividad tiene un campo **magia**:

- `principal`: el tipo es «magia».
- `incluye`: espectáculo de otro tipo (circo, humor, variedades, teatro familiar…) que incluye números de magia de verdad.
- `tema`: evento cuyo tema es la magia: festival de magia, taller o curso de magia, conferencia sobre magia. **Los talleres de magia son «evento > formación» con magia = tema**, nunca «magia».
- `no`: sin relación con la magia.

### Cómo decidir

1. **Lee todo, no solo el título.** El título no basta: hay espectáculos de magia cuyo título no lo dice y que solo se reconocen por la descripción o por el artista (por ejemplo, cuando el artista se presenta como «Mag …», «Mago …» o «Maga …», o la descripción habla de ilusionismo, mentalismo o trucos). Usa título, descripción, sala, tipo de lugar, organizador, artista y horario.
2. **Las categorías de la agenda y las pistas automáticas son solo pistas.** Fallan en los dos sentidos: dejan fuera espectáculos de magia y meten actividades que no lo son (un mercado de Navidad, una fuente «màgica», un itinerario «Barcelona màgica»).
3. **«Màgic», «màgica», «la màgia de…» suelen ser metáforas.** «Una nit màgica», «la màgia del Nadal», «la màgia de la ciència», «sorra màgica» no son magia, y tampoco las descripciones que usan la palabra para crear ambiente («un ballet ple de bellesa, màgia i encant»). Solo cuenta si se describe magia como disciplina: trucos, ilusiones de escena, un mago o maga en escena, «espectacle de màgia».
4. **El formato manda sobre el tema.** Un taller, curso o clase es «evento > formación» aunque sea de teatro, circo o magia. Una charla sobre teatro es «evento > conferencia o coloquio». Un concierto es «otro» aunque sea en un teatro.
5. **Disciplina principal.** Si un espectáculo mezcla disciplinas, el tipo es la que domina según la descripción. Si la magia es solo una parte (un número dentro de un espectáculo de circo, clown o variedades), el tipo es el de la disciplina principal y magia = `incluye`.
6. **Hipnosis de espectáculo:** todavía no está decidido si cuenta como magia. Clasifícala como «magia» con subtipo «hipnosis» y confianza máxima de 0,5, para que salga entre los dudosos. Solo si la hipnosis es el número del espectáculo; no si es un personaje.
7. **Personajes no son números.** Un mago, una bruja o un hipnotizador que aparecen como personajes de una obra, un cuento o un espectáculo de títeres no hacen que sea magia, salvo que la descripción diga que en escena se hacen trucos o números de magia. Del mismo modo, «escapisme» suele significar «evasión», no el número de escapismo.
8. **Público familiar o infantil no cambia el tipo.** Un espectáculo de magia para familias es «magia»; una obra infantil es «teatro».
9. **Decide siempre.** Si dudas, elige la opción más probable y baja la confianza (0,5 o menos si es casi un empate; 0,9 o más si es evidente).
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
   («espectacle de màgia») de las ambiguas («nit màgica»). No contiene
   ninguna lista de espectáculos, artistas ni salas.
   - Si no hay clave de IA, su decisión es la que se publica
     (`clasificado_por: "señales"`).
   - Si hay clave, sus pistas se le pasan a la IA como ayuda.
   - Decide qué actividades **no** hace falta enviar a la IA: las que son
     claramente ajenas (un concierto, una exposición, una visita guiada).
2. **IA** (`pipeline/clasificar_ia.py`). Claude lee los criterios de arriba y
   decide tipo, subtipo, relación con la magia, confianza y motivo
   (`clasificado_por: "ia"`).

### Solo lo nuevo o cambiado

Cada resultado de la IA se guarda en `data/cache/clasificacion_ia.json` con
una «huella» de lo que se le enseñó (título, descripción, sala, horario,
criterios y modelo). Al día siguiente solo se envía lo que tenga una huella
distinta: actividades nuevas, modificadas por el Ayuntamiento o afectadas por
un cambio de criterios.

### Qué se guarda de cada decisión

En `data/espectaculos.json` (y en `data/clasificacion.json`, que incluye
también lo descartado):

| Campo | Qué es |
|---|---|
| `tipo` | teatro, magia, circo, danza, evento, cine u otro |
| `subtipo` | etiqueta breve (formación, festival, hipnosis…) |
| `magia` | principal, incluye, tema o no |
| `confianza` | de 0 a 1 |
| `motivo` | frase que explica la decisión |
| `clasificado_por` | «ia» o «señales» |

### Coste y modelo

- Modelo por defecto: `claude-opus-5-5` (el más capaz de uso general) con
  esfuerzo bajo. Se cambia con la variable `MODELO_IA` (por ejemplo
  `claude-haiku-5-5`, mucho más barato) sin tocar el código.
- Se envían 10 actividades por petición y las instrucciones van en caché.
- No todo se envía a la IA: de ~6.900 actividades vigentes, unas 1.800 son
  candidatas (las demás son claramente conciertos, exposiciones, visitas,
  talleres de otras materias…).
- Estimación (precios de octubre de 2026: Opus 5.5 a 4 $/20 $ y Haiku 5.5 a
  0,10 $/0,50 $ por millón de tokens de entrada/salida; a confirmar con el
  coste real): la primera clasificación completa costaría unos 10–15 $ con
  Opus 5.5 o unos 0,30 $ con Haiku 5.5. Después, con ~50–100 actividades
  nuevas o cambiadas al día, unos 10–20 $/mes con Opus 5.5 o menos de 1 $/mes
  con Haiku 5.5. El informe diario (`data/informe.json`, apartado `ia`)
  guarda los tokens gastados para medir el coste real.

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
  una palabra ambigua. Pendiente de la respuesta de Uri.
