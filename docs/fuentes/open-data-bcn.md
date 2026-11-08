# Open Data BCN: notas técnicas

Revisado el 7/11/2026 desde la nube de Claude Code y desde GitHub Actions.
Licencia de todos los conjuntos: **CC BY 4.0** (uso libre citando al
Ajuntament de Barcelona). Cada ficha de la app cita sus fuentes y la fecha de
comprobación.

## Resumen

| Qué | Dónde | Funciona | Qué trae |
|---|---|---|---|
| Agenda d'actes i activitats (`agenda-diaria`) | API CKAN `datastore_search` | ✅ | lista de actividades, fechas, dirección, coordenadas, tabla de horarios y precios, teléfono |
| Agenda cultural (`agenda-cultural`) | API CKAN `datastore_search` | ✅ | lo mismo |
| Fichero JSON completo de cada agenda | enlace «download» del catálogo | ❌ 403 | descripción, categorías, sala, idiomas, enlaces |
| Páginas web del portal (`/data/ca/dataset/...`) | web | ❌ 403 | — |
| Ficha pública de cada actividad | `guia.barcelona.cat/ca/detall/<texto>_<id>.html` | ✅ (1 cada 10 s) | descripción, sala y su id, enlace de compra, web, organizador, imagen |
| Equipaments de cultura i lleure (`equipament-cultura-i-lleure`) | API CKAN `datastore_search` | ✅ | 3.046 salas y espacios con nombre, equipamiento al que pertenecen, categoría y dirección |

## El bloqueo del fichero completo

- El catálogo (`/data/api/3/action/package_show`) lista dos recursos por
  agenda: un CSV («información básica») y un JSON («información ampliada»).
  Ambos tienen `hide_url: Yes` y `load_type: link_extern`: el portal sirve el
  fichero real a través de su propio enlace `.../resource/<id>/download`.
- Ese enlace, y también las páginas web normales del portal, responden
  **403 Forbidden** (servidor nginx del propio Ayuntamiento) a cualquier
  programa: desde la nube de Claude y desde los servidores de GitHub. No es un
  ajuste del entorno: la conexión llega y es su servidor quien dice que no.
- **No se intenta saltar** (ni cambiando el «User-Agent» ni buscando la
  dirección oculta). Se usa la API oficial, que sí responde.
- El proceso diario pide cada día el primer kilobyte del JSON completo y anota
  el resultado en `data/informe.json` (`descarga.agendas.*.fichero_json_completo`).
  Si algún día pone «disponible», se puede valorar usarlo.
- Posible mejora: escribir al equipo de Open Data BCN (desde su web, apartado
  de contacto) preguntando por el acceso automático al JSON ampliado.

## API (datastore): cómo se usa

- Catálogo: `https://opendata-ajuntament.barcelona.cat/data/api/3/action/`
- Los identificadores de recurso **no se escriben a mano**: se piden cada día
  con `package_show?id=agenda-diaria` (y `agenda-cultural`,
  `equipament-cultura-i-lleure`) y se toma el recurso CSV con
  `datastore_active: true`.
- Lectura: `datastore_search?resource_id=<id>&limit=5000&offset=<n>`.
  Hoy: 4.903 filas en la agenda principal y 4.646 en la cultural (una fila por
  actividad). Tarda unos segundos.

### Campos útiles de cada fila

| Campo | Uso |
|---|---|
| `register_id` | identificador de la actividad (a veces con un carácter invisible delante, BOM: se limpia). Es el mismo en las dos agendas y en la guía. |
| `name` | título. La agenda casi siempre empieza por el formato: «Espectacle…», «Teatre…», «Taller…», «Concert…», «Exposició…». |
| `created`, `modified` | fechas de alta y de última modificación (sirven para saber qué ha cambiado) |
| `start_date`, `end_date` | primer y último día (la hora que traen, 12:00 o 03:00, no es la de la función) |
| `estimated_dates` | texto como «De setembre a juliol» |
| `timetable` | tabla HTML con columnas Període · Dies · Hores · Preus · Observacions (con celdas que ocupan varias filas) |
| `addresses_road_id`, `addresses_road_name`, `addresses_start_street_number`… | dirección. `addresses_road_id` es el código municipal de la calle: junto con el número sirve para agrupar salas |
| `addresses_neighborhood_name`, `addresses_district_name`, `addresses_zip_code` | barrio, distrito, código postal (el CP llega sin el 0 inicial: «8003») |
| `geo_epgs_4326_lat`, `geo_epgs_4326_lon` | coordenadas para el mapa |
| `values_*` | un único atributo: casi siempre un teléfono |

Campos que **llegan vacíos** en la API: `institution_name` (sala),
`secondary_filters_*` (categorías). Por eso las categorías de la agenda no se
usan; de todas formas, el brief dice que solo son una pista y que fallan.

## Unión de las dos agendas

- Se unen por `register_id`. Hoy, entre las actividades vigentes (que no han
  terminado): 2.368 solo en la principal, 2.373 solo en la cultural y 2.129 en
  las dos. Total: **6.870**.
- Cuando una actividad está en las dos, los datos coinciden casi siempre; si
  no, se usa la versión con `modified` más reciente. Cada ficha guarda en qué
  agendas aparece (`agendas`).

## Horarios, fechas y precios

`pipeline/horario.py` lee la tabla `timetable`:

- **Días:** días de la semana («Dijous, divendres i dissabte», «De dimarts a
  dissabte», «Cada dia»), fechas concretas («5 novembre, 3 desembre i
  21 gener»; el año se deduce del intervalo inicio–fin) y excepciones
  («excepte 25 desembre»).
- **Horas:** «a les 20.15 h», «a les 11.00 h i a les 12.45 h», «de 09.00 h a 15.30 h».
- Con eso calcula las **próximas funciones** (fecha + hora) de los próximos
  120 días.
- **Precios:** importes en euros («Entrada general: 18 €», «de: 17 a 19 €»),
  gratuidad («Entrada gratuïta») y taquilla inversa. Se guarda mínimo y máximo.
- **Duración:** «Durada: 70 minuts», «1 hora i 15 minuts».
- **Idioma:** solo si el texto lo dice («en català», «en castellà», «sense
  text»…). La mayoría no lo dice.

## La guía (guia.barcelona.cat)

- Cada actividad tiene ficha pública en
  `https://guia.barcelona.cat/ca/detall/<texto>_<register_id>.html` (el texto
  del enlace da igual; se genera a partir del título).
- `robots.txt` permite esas páginas y pide **Crawl-delay: 10**: el programa
  espera 10 segundos entre páginas, siempre. También prohíbe los listados y
  búsquedas (`/llistat`, `pg=search`), que no se usan.
- De la ficha se extrae: descripción (`div.cos`), organizador, imagen, sala y
  su identificador (el bloque `info-lloc` enlaza a `<sala>_<id>.html`), «Se
  celebra a» (tipo de lugar), enlaces («Web venda d'entrades», «Web») y
  estado («Cancel·lat»…).
- Se guarda en `data/cache/guia.json` con la fecha de lectura y la versión
  (`modified`) de la actividad. Solo se relee si el Ayuntamiento modifica la
  actividad.
- Orden de lectura: primero espectáculos y actividades con título poco claro,
  después festivales, talleres y charlas, y al final conciertos, exposiciones
  y visitas. El proceso diario lee como mucho 35 minutos (unas 200 fichas);
  hay unas 100–200 actividades nuevas o modificadas al día, casi siempre ya
  cubiertas. El primer relleno se hizo el 7/11/2026 desde la sesión de Claude.

## Salas

- `pipeline/salas.py` agrupa por **código de calle + número**. Si falta, por
  coordenadas; si faltan, por nombre de calle.
- El nombre sale de la ficha de la guía («Teatreneu Multisales - Sala Cafè
  Teatre») y de la lista oficial de equipamientos, que dice a qué casa
  pertenece cada sala (`institution_name`). Así las salas interiores («Sala
  Gran», «Sala Petita», «Sala Cafè Teatre»…) quedan dentro de su teatro.
- Cada sala guarda dirección, barrio, distrito, coordenadas, salas interiores,
  categorías de equipamiento e identificadores de la guía.

### Salas que el brief no encontraba por su nombre (comprobado el 8/11/2026)

Buscadas por nombre y por la dirección donde se conocen:

| Sala | Qué hay en la agenda |
|---|---|
| Akademia | Está, como «Teatre Akadèmia» (con acento): 3 espectáculos. |
| Almeria (c. Sant Lluís, 64) | En esa dirección la guía del Ayuntamiento dice «Teatre Golem's»: 9 espectáculos. |
| BARTS (Av. Paral·lel, 62) | En esa dirección la guía dice «Sala Paral·lel 62»: 4 espectáculos. |
| La Seca (c. Flassaders, 40) | En esa dirección la guía dice «Fundació Joan Brossa - Centre de les Arts Lliures»: 7 espectáculos. |
| Capitol (La Rambla, 138) | Nada en la agenda. Se cubrirá con la web de la sala (fase 5). |
| Price | Nada en la agenda con ese nombre. Pendiente de saber a qué sala se refería. |

Conclusión: casi todas están; la app usa el nombre que da hoy el Ayuntamiento.
Como las salas se agrupan por dirección, si una sala cambia de nombre sigue
siendo la misma ficha.

## Otras fuentes revisadas para más adelante

- **Agenda cultural de la Generalitat** (dades obertes de Catalunya,
  conjunto `rhpv-yr4f`, API Socrata en `analisi.transparenciacatalunya.cat`):
  funciona y trae descripción, categorías (incluida `agenda:categories/magia`),
  sala, horario, precio y enlace de compra. Hoy tiene unas 400 actividades
  vigentes en Barcelona ciudad (~110 de teatro). Útil como segunda fuente y para
  cruzar categorías; habrá que evitar duplicados (una sola ficha por obra).
