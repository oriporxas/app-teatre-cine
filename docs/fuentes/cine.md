# Cartelera de cine (Barcelona)

Añadida el 17/11/2026 a petición de Uri: la fase 6 (cine) se adelanta. El cine va en una
pieza aparte (`pipeline/cine/`), porque no son actividades de la agenda sino películas con
sesiones en muchos cines.

## De dónde sale cada dato

| Dato | Fuente | Cómo |
|---|---|---|
| Lista de cines, dirección y coordenadas | Datos abiertos del Ayuntamiento (`equipament-cultura-i-lleure`, categoría «Cinemes») | API CKAN `datastore_search`, cada 30 días |
| Web de cada cine | Ficha del cine en guia.barcelona.cat | 1 página cada 10 s (su robots.txt), cada 30 días |
| Sesiones (día, hora, versión, sala) | La web de cada cine | Ver «Lectores» abajo; solo lo que permite su robots.txt |
| Proyecciones en centros cívicos, ciclos, cinefórums | Agenda del Ayuntamiento | Actividades que la clasificación marca como «cine» |
| Cartel, fondo, sinopsis (es/ca), géneros, duración, dirección, guion, reparto, tráiler, edad | TMDB (The Movie Database) | API con clave (`TMDB_TOKEN`), caché de 14 días |
| Premios y nominaciones (película, dirección y 4 primeros del reparto) | Wikidata (CC0) | `P166` (premio recibido) y `P1411` (nominado a), con el año |

## Lectores de horarios (`pipeline/cine/lectores.py`)

Cada lector entiende un tipo de web (el programa de venta del cine), no un cine concreto:

- **elqueque** (Mooby, Verdi…): la página lleva los datos de todas las salas de la cadena
  (`window.shops`) o los publica en `/api/get-events`. Si dos cines comparten web y la web los
  publica juntos (Verdi y Verdi Park), las sesiones van al que coincide con el nombre y el otro
  remite a él.
- **pillalas** (Renoir): una página por día con las sesiones (7 días).

Estado del 17/11/2026: 8 cines con horarios (los seis Mooby, Verdi y Renoir Floridablanca),
unas 900 sesiones en 14 días.

## Lo que no se lee (y por qué)

- **Cinesa**: su web responde 403 incluso al robots.txt → no quiere programas. Sale con su
  dirección y el enlace a su web.
- **Cinemes Girona**: su robots.txt prohíbe `/api/`, que es donde están sus horarios.
- **Yelmo, Filmoteca, Zumzeig, Dididado…**: su web no da los horarios en un formato legible sin
  ejecutar su programa, o (Zumzeig) bloquea a los programas de IA. Salen con «Horarios en su web».
- Nunca se intenta saltar un bloqueo (cambiar el «User-Agent», usar otra dirección…).
- Para cubrirlos todos: un proveedor de horarios (p. ej. International Showtimes, de pago), o
  acuerdos con los cines. Apuntado en la visión a largo plazo.

## Identificar bien cada película (principio 4)

1. Si la web del cine da el código de IMDb (Mooby, Verdi), se busca en TMDB por ese código.
2. Si no (Renoir, la agenda), por título: tiene que coincidir el título y, si se sabe, la
   dirección (palabras del nombre en cualquier orden). Con la dirección se acepta un título casi
   igual («La violinista» / «El violinista»).
3. Sin dirección, solo si hay un único candidato con ese título exacto estrenado en los últimos
   tres años. Si no hay seguridad, la película sale con los datos del cine y sin TMDB.
4. La misma película de dos cines (una con IMDb y otra sin) se junta en una sola ficha.

## Atribución obligatoria

TMDB exige: «This product uses the TMDB API but is not endorsed or certified by TMDB.» La app lo
muestra en cada ficha de película, en la cartelera de cine y en «Acerca de». La clave
«Developer» de TMDB es para uso no comercial: si la app pasa a ser un negocio, hace falta un
acuerdo comercial con TMDB.

## Claves

- `TMDB_TOKEN`: el «API Read Access Token» de TMDB. En GitHub: Settings → Secrets and variables →
  Actions → `TMDB_TOKEN`. En las sesiones de Claude en la nube la pone la red: allí se ejecuta
  con `TMDB_TOKEN=proxy-injected`.
- Wikidata no necesita clave. A veces limita las peticiones (429): se espera y, si sigue, se deja
  para la siguiente ejecución.
