# Arquitectura: preparada para crecer

Cómo está montada la app para que pasar de Barcelona a muchas ciudades no
obligue a rehacerla. Responde a la «Visión a largo plazo» del brief.
Escrito el 8/11/2026. **Hoy solo funciona Barcelona, a propósito.**

## 1. Dos trabajos separados

| Trabajo | Qué hace | Cuándo | Quién espera |
|---|---|---|---|
| **Recogida** (`pipeline/`) | descarga fuentes, lee webs respetando sus límites, entiende horarios, clasifica, agrupa salas | cada día a horas fijas (GitHub Actions, 05:17 UTC) | nadie |
| **Búsqueda** (fase 2, por hacer) | responde a lo que pide el usuario | al momento | el usuario: menos de 1 segundo |

La búsqueda nunca lee webs ni llama a la IA: solo consulta datos ya
preparados. Por eso el coste crece con las ciudades y los espectáculos, no
con las búsquedas.

## 2. Ciudades (`ajustes/ciudades.toml`)

Cada ciudad tiene país, zona horaria, moneda, idiomas y la lista de fuentes
que la cubren. Hoy solo hay `barcelona`.

- **Zona horaria:** «hoy» se calcula en la hora de la ciudad, no en la del
  servidor (`Ciudad.hoy()`). Las fechas y horas de las funciones se guardan en
  hora local, y cada ficha lleva su `zona_horaria`.
- **Moneda:** cada precio lleva su `moneda`.
- **Idiomas:** los textos se guardan por idioma (`descripcion: {"ca": …}`), y
  cada ficha dice en qué idioma vienen sus textos (`idioma_textos`). La
  traducción (fase 2) añadirá más idiomas sin cambiar el formato.
- **Independencia:** cada ciudad guarda sus resultados y su memoria en su
  propia carpeta (`data/ciudades/<ciudad>/`). Así, en el futuro, cada ciudad
  se podrá procesar por separado y a la vez que las demás.

Para añadir una ciudad: un bloque nuevo en `ajustes/ciudades.toml` con sus
fuentes.

## 3. Fuentes: piezas independientes (`pipeline/fuentes/`)

Cada fuente es una carpeta con una función `recoger()` que entrega las
actividades en un **formato común** (descrito en `pipeline/fuentes/base.py`).
El resto del programa (clasificación, salas, resultados) solo conoce ese
formato. Una fuente:

- descarga y entiende sus propios datos;
- respeta su propio límite de velocidad (la guía de Barcelona: 1 página cada
  10 s) y solo relee lo nuevo o cambiado;
- guarda su memoria en `data/ciudades/<ciudad>/cache/<fuente>/`;
- da a cada actividad un identificador único en el mundo
  (`<fuente>:<id de origen>`) y a cada lugar una clave estable
  (`<ciudad>:<dirección u otra referencia>`);
- cita de dónde sale cada dato (`fuentes`, principio 4).

Si una fuente falla, su ciudad conserva los datos del día anterior y el error
queda en `data/ciudades/<ciudad>/informe_fallo.json` y en `data/indice.json`.

Hoy hay una: `open_data_bcn` (agendas de Open Data BCN + fichas de
guia.barcelona.cat). Futuras, según la visión: agenda de la Generalitat, webs
de salas leídas por IA, proveedores de pago (cine), publicaciones de salas y
artistas.

Para añadir una fuente: crear `pipeline/fuentes/<nombre>/__init__.py` con
`NOMBRE`, `DESCRIPCION` y `recoger(ctx)`, y nombrarla en la ciudad.

**Pendiente cuando llegue la segunda fuente de una ciudad:** detectar la
misma obra en varias fuentes y dejar una sola ficha (principio 4). El sitio
donde hacerlo está marcado en `pipeline/principal.py`.

## 4. IA por tareas (`ajustes/ia.toml`)

Cada tarea tiene su modelo, su esfuerzo y su tope diario. Cambiar de modelo
es cambiar una línea. Hoy:

| Tarea | Modelo provisional | Qué hace |
|---|---|---|
| `clasificar` | `claude-haiku-5-5` | clasifica lo nuevo o cambiado |
| `revisar_dudosos` | `claude-opus-5-5` | vuelve a mirar lo que la tarea anterior decidió con confianza < 0,7 |
| `fichas_personas` | `claude-opus-5-5` (desactivada) | fase 3: trayectorias y premios |

- Cada tarea tiene su memoria (`data/ciudades/<ciudad>/cache/ia/<tarea>.json`):
  nada se paga dos veces si no cambia.
- Para pruebas puntuales (por ejemplo, comparar modelos) se puede sustituir un
  valor sin tocar el archivo: `IA_CLASIFICAR_MODELO=claude-sonnet-5-5`.
- Sin la clave `ANTHROPIC_API_KEY` no se usa la IA y no se gasta nada.

**Al activar la IA (cuando Uri avise):**
1. Probar Haiku 5.5, Sonnet 5.5 y Opus 5.5 con la prueba de magia y enseñar
   aciertos y coste de cada uno; fijar los modelos en `ajustes/ia.toml` con
   esos datos.
2. Pasar el trabajo nocturno al procesamiento por lotes (Batch), que cuesta
   la mitad: se envía el lote en una ejecución y se recogen los resultados en
   la misma o en la siguiente. Hoy las peticiones son directas.

## 5. Dónde viven los datos

```
data/
  indice.json                      resumen de todas las ciudades
  ciudades/<ciudad>/
    espectaculos.json              fichas publicadas (teatro, magia, circo, danza, eventos, cine)
    salas.json                     salas con espectáculos
    clasificacion.json             todas las decisiones, también las descartadas
    informe.json                   qué ha pasado hoy
    cache/<fuente>/…               memoria de cada fuente
    cache/ia/<tarea>.json          memoria de cada tarea de IA
```

### Cómo serán las tablas de la base de datos (fase 2)

Cuando se monte la búsqueda, estos archivos se cargarán en una base de datos
de verdad. Las tablas seguirán el mismo formato:

- **ciudades**: id, nombre, país, zona horaria, moneda, idiomas.
- **salas**: id (`<ciudad>:…`), ciudad, nombre, salas interiores, dirección,
  coordenadas.
- **espectaculos**: id (`<fuente>:<id>`), ciudad, tipo, subtipo, relación con
  la magia, confianza, textos por idioma, precio y moneda, sala, fuentes.
- **funciones**: espectáculo, fecha y hora locales, zona horaria.

Con índices por ciudad, fecha, tipo y ubicación, para responder en menos de
un segundo aunque haya muchas ciudades.

## 6. Lo que choca con la visión (y qué se hará)

| Hoy | Por qué choca a gran escala | Qué se hará |
|---|---|---|
| Los resultados se guardan como archivos dentro del repositorio | Con muchas ciudades el repositorio crecería sin parar, y buscar en archivos no da respuestas en menos de un segundo | En la fase 2 (ya prevista) se cargan en una base de datos; el repositorio queda para el código. El programa no cambia: solo dónde guarda |
| La recogida se hace en GitHub Actions (gratis hasta 2.000 minutos al mes) | Muchas ciudades no cabrían en ese tiempo | Cuando haya más ciudades, pasar la recogida a un servidor en la nube que trabaje con muchas fuentes a la vez. Como cada ciudad y cada fuente son independientes, se pueden repartir |
| Las fuentes se leen una detrás de otra | Más lento de lo necesario | Lo mismo: leerlas a la vez, cada una con su propio límite de velocidad |
| La capa de señales solo entiende catalán, castellano e inglés | En otras ciudades no sirve tal cual | Allí la IA hace el trabajo principal; las señales quedan como ayuda local |
| La primera carga de una ciudad es lenta (Barcelona: unas 5 horas para 1.700 fichas, por la pausa de 10 s) | No choca: la visión ya lo prevé | Se hace una vez; después solo lo nuevo |

Ya resueltos el 8/11/2026: precios sin moneda, «hoy» calculado en la hora del
servidor, nombres de ciudad escritos dentro del código, un solo modelo de IA
para todo, lógica de Barcelona mezclada con la general, y actividades sin
dirección agrupadas en una «sala» falsa.
