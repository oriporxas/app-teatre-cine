# Veracidad y cobertura: que todo lo que sale sea cierto y que no se escape nada

Pedido de Uri (17/11/2026), tras ver un precio mal («Magia i comèdia al Bosc de les Fades» salía a
95 € y vale 24,95 €) y enlaces de compra que llevaban a la portada de la sala: *«piensa, analiza y
encuentra una solución para que la información sea verídica, no haya errores y no se escape nada
de la agenda de la ciudad, ninguna sala, ningún cine, ningún evento»*.

La respuesta tiene cuatro piezas. Todas funcionan solas cada día (principio 1): nadie revisa nada
a mano.

## 1. El verificador: nada sale sin pasar las comprobaciones

`pipeline/verificar.py`, justo antes de escribir los archivos de la app (escena y cine).

Cada dato sensible se contrasta con el texto de la fuente o con reglas de sentido común. Si no
pasa, **no se enseña** (mejor un recuadro de menos que un dato falso) y **queda anotado** en
`data/ciudades/<ciudad>/verificacion.json` con el motivo.

| Dato | Comprobación | Si falla |
|---|---|---|
| Precio | cada importe está escrito tal cual en el texto de precios de la fuente; mínimo ≤ máximo | no sale el precio |
| Fechas | dentro del periodo que da la propia fuente | se quita esa función |
| Horas | hora válida; entre las 2:00 y las 7:59 se da por error de lectura | «hora por confirmar» |
| Sala | no puede llamarse como la ciudad («Barcelona» no es una sala) | se enseña la dirección |
| Mapa | las coordenadas caen dentro de la ciudad | no sale el punto |
| Equipo artístico | cada nombre está en la descripción (o el título) de la fuente | se quita esa línea |
| Premios citados | la cita está en la descripción | no sale el premio |
| Duración, edades | 5–600 minutos; 0–99 años | no salen |
| Enlaces | dirección web completa | no sale el enlace |
| Fichas repetidas | mismo título en la misma sala | aviso en el informe |
| Cine | sesión dentro de la ventana de días, hora válida, cine conocido | se quita la sesión |

Primer día (17/11/2026): quitó funciones inventadas en 2027 de una obra que acaba en diciembre
(la causa, en `horario.py`, ya está corregida), 125 líneas de equipo que no estaban en el texto
(venían del título: ahora se mira también) y avisó de 4 fichas repetidas.

## 2. Cada error encontrado se convierte en una prueba

Cuando aparece un error (lo vea Uri o el verificador), se arregla la causa **y** se añade una
prueba automática con el caso real, que se ejecuta cada día antes del proceso
(`python -m unittest discover -s tests -t .`). Así el mismo error no puede volver. Ejemplos:

- `tests/test_horario.py`: «24.95 €» → 24,95 (no 95); «49.19 € / 10 sessions» → 49,19 (no 10);
  «8 a 32 € / 1 h durada» → 8–32 (no 1); «30 octubre» ya pasado no salta a 2027.
- `tests/test_verificar.py`: precio que no está en la fuente, función fuera de periodo, sala
  «Barcelona», equipo que no está en el texto, sesiones de cine imposibles.
- `tests/test_compra.py`: el enlace de compra nunca lleva a otra obra.

## 3. Enlaces de compra: a la sesión o a la obra, nunca a la portada sin decirlo

- **Cine**: la hora lleva a la compra de **esa sesión** en la web oficial del cine, con el mismo
  enlace que forma la propia web del cine (Mooby y Verdi: tienda «admit-one» con el código de la
  sesión; Renoir: su página de cada pase). Los cines que no lo permiten llevan a su cartelera y la
  app lo dice.
- **Teatro**: la agenda municipal suele dar solo la portada de la sala. `pipeline/compra.py` busca
  en la web de la sala (respetando robots.txt) la página de la obra: por los enlaces de la portada
  y el mapa del sitio, comprobando que esa página habla de la obra. Si hay dudas (dos páginas
  posibles), no elige ninguna. El botón dice «Comprar entradas» si es la página de la obra y
  «Web de la sala» si solo hay la portada.

## 4. Auditoría de cobertura: ¿qué salas y cines se nos escapan?

`pipeline/cobertura.py` compara cada día la **lista oficial de equipamientos** de la ciudad
(teatros, auditorios y cines del conjunto abierto del Ayuntamiento) con lo que tenemos. Resultado
en `data/ciudades/<ciudad>/cobertura.json`: salas oficiales sin ninguna actividad en nuestras
fuentes y cines sin horarios, con el motivo.

Primer día: de 121 teatros oficiales, 62 tienen actividades y 59 no (muchos son escuelas o
asociaciones con escenario, pero también salas como Aquitània Teatre, El Teatre Més Petit, City
Hall o Comedianet, que no publican en la agenda municipal). De 25 cines oficiales, 8 tienen
horarios. **Esa lista es el trabajo pendiente para no dejar nada fuera.**

## 5. Lector de webs de salas (aprobado por Uri el 17/11/2026)

`pipeline/fuentes/webs_salas/`: una fuente más, como la agenda municipal. Para cada teatro de la
auditoría que no sale en nuestras fuentes (menos escuelas, institutos y facultades):

1. su web, de la ficha de la guía oficial (guia.barcelona.cat, respetando sus 10 s entre páginas);
2. la portada y hasta dos páginas de programación de esa web, solo si su robots.txt lo permite y
   no prohíbe que su contenido pase por una IA;
3. la IA (modelo barato, tarea «leer_webs» de `ajustes/ia.toml`) extrae las obras **con la cita
   literal** de cada dato; solo se vuelve a pedir cuando la página cambia;
4. el programa comprueba cada cita sin fiarse de la IA: el título está en la página; cada fecha
   sale en su cita (día y mes, y el año si lo pone); la hora también, o se quita; el precio lo lee
   nuestro propio lector de precios; el enlace tiene que ser uno de la página. Lo que no pasa, fuera.

Lo que sale pasa después por la clasificación (solo se publica teatro, magia, circo y sus eventos:
las fiestas, conciertos o presentaciones de libros de esas webs se quedan fuera) y por el
verificador, como todo. Pruebas: `tests/test_webs_salas.py`.

Para que una sala no desaparezca al cubrirla, la auditoría no cuenta lo que trae este lector.

**Primera lectura (17/11/2026).**
- Salas y webs: 35 teatros sin agenda (sin contar escuelas); 19 con web en la guía; 29 páginas leídas.
- Lo que extrajo la IA: 71 obras pasaron las comprobaciones y 20 se descartaron.
- Lo que llegó a la app: 29 obras, después de la clasificación (el resto eran fiestas, conciertos,
  presentaciones de libros…). Son de The Comedy Clubhouse (sus dos locales), Teatre Metamorfosis,
  Badabadoc y el Centre Moral i Cultural del Poblenou.
- Errores encontrados al revisarlo a mano, y corregidos con su prueba:
  - un periodo («del 19 al 29») salía como dos funciones;
  - dos locales con la misma web recibían los dos todos los espectáculos;
  - el enlace a la lista de espectáculos pasaba por enlace de la obra.
- Gasto el primer día: 0,10 $ de lectura y unos 0,55 $ de clasificar las obras nuevas. Los días
  siguientes solo se pagan las páginas que cambian y las obras nuevas.
- Tiempo: como mucho 8 minutos al día.

## Más adelante
- Lo mismo para los cines sin horarios cuando su web lo permita (tarea «horarios_cine», reservada).
- Proveedores de pago donde los haya (cine: International Showtimes) y que las salas publiquen
  directamente en la app con verificación automática (visión a largo plazo).
