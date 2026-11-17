# Primer borrador completo · 17/11/2026

Pedido de Uri (14/11/2026): activar la IA, añadir toda la cartelera de cine, noticias por
teatro, cine y magia, carteles bien visibles, diseño negro, rojo y blanco, y comprobar que
todo funciona sin errores. Crédito disponible: 13,24 $. Tope acordado: 11 $.

## Resultado

### Escena (teatro, magia, circo y sus eventos)
- 1.585 actividades candidatas clasificadas con la IA (Sonnet; 136 dudosas revisadas por Opus).
- En la app: 595 (449 teatro, 117 eventos, 15 magia, 14 circo).
- Prueba de magia con las respuestas de Uri: **46 de 47** (8 ya no están en cartel). La que
  no coincide es el taller de neurociencia «Magic brains», el mismo caso límite de la prueba
  de modelos.
- Género de la obra: 303 de 449 obras de teatro (solo cuando es seguro).
- Traducción al castellano: 535 de 538 descripciones (Haiku).
- Temas de la obra: 391 fichas.
- Premios que cita la descripción: 16 obras (Premis Max, FETEN, Teatre Barcelona, Serra d'Or…),
  solo con cita literal comprobada. Una primera pasada dio 25, con errores (premios sin nombre, el
  Nobel de la persona de la que trata una obra, el premio de la novela original); se afinaron las
  instrucciones y se repitió.
- Magos: 15 buscados en internet; 7 con ficha (trayectoria y premios con fuente comprobada); los
  otros 8, sin información fiable, no se publican.

### Cine
- 18 cines en la lista; **8 con horarios** (Mooby Arenas, Aribau, Balmes, Bosque, Glòries, Gran
  Sarrià; Cinemes Verdi —que publica también las de Verdi Park— y Renoir Floridablanca).
- 979 sesiones en 14 días: 888 en cines y 91 proyecciones de la agenda municipal.
- 119 películas; 71 identificadas en TMDB (cartel, sinopsis, reparto, tráiler…); 60 con tráiler;
  16 con premios de Wikidata (y premios de su dirección y reparto principal).
- Versiones: VOSE 458, castellano 411, VO 8, catalán 7, sin indicar 95.
- Sin horarios (respetando sus normas): Cinesa (bloquea programas), Cinemes Girona (robots.txt
  prohíbe su API), Yelmo, Filmoteca, Zumzeig (bloquea la IA)…

### Noticias
- 6 medios (betevé, Ara, La Vanguardia, El País, Espinof, Cinemanía): 293 titulares leídos,
  92 publicados (15 de teatro, 77 de cine). Ninguno de magia o circo esa semana.

## Gasto de IA (ver `data/gasto_ia.json`)

| Tarea | Modelo | $ |
|---|---|---|
| Clasificar (1.585 actividades) | Sonnet 5.5 | 3,52 |
| Revisar dudosos (136) | Opus 5.5 | 1,16 |
| Fichas de magos (15, con búsqueda web) | Sonnet 5.5 (+ 1 prueba con Opus) | 2,26 |
| Traducir, premios citados y temas (538, dos pasadas) | Haiku 5.5 | 0,30 |
| Noticias (293) | Haiku 5.5 | 0,03 |
| **Total** | | **7,27** de 11 |

A partir de ahora solo se procesa lo nuevo: con el tope diario de 2 $ (`ajustes/ia.toml`), el
gasto normal estimado es de unos céntimos a 0,5 $ al día.

## Comprobaciones
- Pruebas automáticas del programa: todas correctas (`python -m unittest discover -s tests -t .`).
- Prueba de la app en un navegador con tamaño de móvil (iPhone SE, iPhone 13, Pixel 7): todas
  las pantallas sin desbordar a lo ancho y sin errores de JavaScript. Flujos probados: filtros de
  cine, añadir una sesión de cine a un plan, ficha de persona, buscador, ocultar musicales, Inicio
  en catalán, imagen del plan para historias.

## Pendiente
- Uri: crear en GitHub los secretos `ANTHROPIC_API_KEY` y `TMDB_TOKEN` (la tarea diaria los usa);
  elegir dónde publicar la app (las fotos de carteles y noticias solo se ven en la app publicada).
- Cines sin horarios: un proveedor de horarios o acuerdos con los cines.
- Premios en Wikidata: a veces Wikidata limita las peticiones; lo pendiente se completa en las
  ejecuciones siguientes.
