# Revisión de Uri del primer borrador · 17/11/2026

Uri probó el primer borrador y pidió correcciones de datos, cambios de pantalla y, sobre todo,
una solución para que la cartelera sea verídica y no se escape nada. Qué se hizo y qué se midió.

## Datos

| Problema | Causa | Arreglo | Alcance |
|---|---|---|---|
| «Magia i comèdia al Bosc de les Fades» a 95 € (vale 24,95 €) | el lector de precios quitaba puntos y comas: «24.95» → «24» y «95» | precios leídos con sus decimales; cada importe tiene que estar escrito tal cual en la fuente | **341 de 1.101 fichas** tenían el precio mal; ahora 0 (comprobado uno a uno contra el texto de la fuente) |
| «49.19 € / 10 Sessions» salía «10–49,19 €»; «8 a 32 € / 1 h durada», «1–32 €» | un «€» al final de línea se leía junto al número de la línea siguiente | el salto de línea separa importes | pruebas con los dos casos |
| Funciones en 2027 de obras que acaban en diciembre de 2026 | una fecha ya pasada («30 octubre») saltaba al año siguiente | si cae fuera del periodo de la fuente, no se pasa al año siguiente; el verificador quita lo que quede fuera | 13 funciones quitadas el primer día |
| La hora del cine llevaba a la portada del cine | se guardaba la web del cine | enlace de compra de **cada sesión**, el mismo que forma la web del cine | las 1.377 sesiones de los 8 cines con horarios |
| «Comprar entradas» de teatro llevaba a la portada de la sala | la agenda municipal solo da la portada (234 de 322 obras con enlace) | búsqueda de la página de la obra en la web de la sala | ver abajo |
| Ninguna noticia de magia, circo ni eventos | solo había medios generalistas, y se miraban 10 días | 7 canales más (Zirkolika, betevé magia y festivales, VilaWeb circ, magia y arts escèniques, El Mundo y elDiario.es teatro), más días para los especializados, marca «evento» | 5 noticias de magia, 7 de circo y 18 de eventos (antes 0) |

## Pantallas

- Barra de abajo: Inicio, Escena, Cine, Planes, Desat (solo lo guardado), Notícies.
- Película: un desplegable por cine con sus horas.
- Inicio: fila de «Salas» (40 salas de teatro), cada una con su página.
- Plan: Compartir (con «Compartir en stories» dentro) y Añadir a mi calendario, con iconos;
  «Ruta del día» abre un mapa con las paradas numeradas y botones a Google Maps y Apple Maps (y
  a otra app de mapas en Android); lápiz junto al título; «Borrar plan» abajo, con pregunta.
- Fondo: telón color vino, apagado.

## Comprobaciones

- 132 pruebas automáticas del programa, todas correctas.
- App en un navegador con tamaño de móvil (iPhone SE, iPhone 13, Pixel 7): 41 comprobaciones
  correctas (sin desbordar, sin errores, la hora del cine lleva a la sesión, planes, buscador,
  catalán…).
- Gasto de IA de esta revisión: unos 0,03 $ (volver a clasificar las noticias con la marca «evento»).
