# Copia de seguridad del proyecto

Pedido de Uri (19/11/2026): «Quiero estar seguro de que todo el trabajo que hemos estado haciendo
este tiempo juntos no se va a perder», por si pasa cualquier cosa o GitHub vuelve a suspender la
cuenta (ya pasó del 8 al 14/11/2026).

Guárdala en **dos sitios distintos**, por ejemplo en el ordenador y en iCloud Drive o un pendrive.
Si un sitio falla, queda el otro.

## Qué hay en la copia

Son dos archivos y esta guía:

| Archivo | Qué es | Para qué sirve |
|---|---|---|
| `app-teatre-cine-AAAA-MM-DD.zip` | Todos los archivos del proyecto tal como están ese día: la app, la actualización diaria, los ajustes, los datos y la memoria de cada día (la caché: lo que costó horas y dinero hacer), los documentos y las herramientas. | Se abre en cualquier ordenador y se puede leer todo. Basta para volver a montar el proyecto en otro sitio. |
| `app-teatre-cine-AAAA-MM-DD.bundle` | El proyecto entero con **todo su historial**: cada cambio desde el primer día, con su explicación, y las dos ramas (`main`, la versión aceptada, y la rama de trabajo de Claude). | Permite rehacer el repositorio de GitHub exactamente como estaba, en otra cuenta o en otro servicio. |
| Esta guía (`docs/copia-de-seguridad.md`) | Qué hay, qué falta y cómo restaurarlo. | También está dentro del zip y del bundle. |

Lo decidido y cómo está hecho todo está escrito dentro del proyecto. Así, cualquier sesión nueva de
Claude puede seguir trabajando aunque no recuerde las conversaciones:
- `CLAUDE.md`: guía para cada sesión;
- `docs/brief.md`: decisiones de Uri;
- `docs/veracidad.md`, `docs/arquitectura.md`, `docs/clasificacion.md`, `docs/fuentes/` y `docs/pruebas/`.

## Lo que NO está en la copia, a propósito, y cómo recuperarlo

1. **Las claves secretas.** Nunca se guardan en archivos: quien tuviera la copia podría gastar tu
   crédito.
   - `ANTHROPIC_API_KEY` (la IA): está en GitHub, en Settings → Secrets and variables → Actions. Si
     se pierde, crea una clave nueva en la consola de Anthropic (console.anthropic.com → API Keys) y
     guárdala otra vez como secreto con ese nombre.
   - `TMDB_TOKEN` (datos de las películas): en themoviedb.org → Settings → API → «API Read Access
     Token». Se guarda como secreto con ese nombre.
   - En el entorno de la nube de Claude «app-teatre-cine», la misma clave de la IA se llama
     `CLAVE_IA_CARTELERA`.
2. **El crédito de la IA.** Está en tu cuenta de Anthropic (Billing), no en el proyecto.
3. **Lo que guarda cada móvil:** favoritos, planes, historial e idioma se quedan en el teléfono de
   cada persona. No pasan por ningún servidor, así que no están en el proyecto.
4. **La vista previa privada de Claude**
   (https://claude.ai/artifact/7ZSzcw6GNbXXf5idrGQw3z). Se rehace con
   `herramientas/preparar_vista_previa.py`.
5. **La publicación en Cloudflare Pages** (si ya está hecha). Si hubiera que repetirla:
   - repositorio: el de GitHub;
   - carpeta raíz: `web`;
   - comando de construcción: `npm ci && npm run build`;
   - carpeta de salida: `dist`.
6. **Las conversaciones con Claude.** Lo importante de cada una está en `CLAUDE.md` y `docs/brief.md`.

## Cómo restaurarlo si hiciera falta

### Opción A (la más fácil): pedírselo a Claude

1. En GitHub, crea un repositorio **privado** y **vacío**: botón «New», sin README ni nada más.
2. Instala en él la app de Claude (github.com/apps/claude) y comprueba en claude.ai que GitHub está
   conectado.
3. Abre una sesión de Claude Code con ese repositorio, adjunta el archivo `.bundle` y escribe:
   «Restaura el proyecto desde este bundle, con sus ramas y todo su historial, y súbelo a este
   repositorio».
4. En el repositorio nuevo, vuelve a crear los dos secretos: Settings → Secrets and variables →
   Actions → «New repository secret».
   - `ANTHROPIC_API_KEY`
   - `TMDB_TOKEN`
5. La actualización diaria vuelve a funcionar sola. Si GitHub la tuviera en pausa: pestaña
   «Actions» → «Enable workflows».

### Opción B (técnica): con git

Probado el 19/11/2026: restaura las dos ramas con todo su historial.

```
git clone --mirror app-teatre-cine-AAAA-MM-DD.bundle app-teatre-cine.git
cd app-teatre-cine.git
git push --mirror <dirección del repositorio nuevo>
```

### Opción C: sin GitHub (el «plan B» del brief)

El zip tiene todo lo necesario para hacer la actualización diaria en otro sitio y construir la app.
- Actualización diaria: con Python 3.12 o más nuevo, `pip install -r requirements.txt` y después
  `python -m pipeline.principal` (al mediodía, `python -m pipeline.principal --rapida`).
- App: con Node 22, `cd web && npm ci && npm run build`. Lo que se publica es la carpeta `web/dist`.

## Cómo comprobar que la copia está bien

- El zip se abre y dentro hay una carpeta `app-teatre-cine` con `CLAUDE.md`, `README.md`, `docs`,
  `pipeline`, `web`, `data`, `ajustes`, `tests` y `herramientas`.
- El bundle lo puede comprobar Claude con `git bundle verify`. Junto a la copia va una nota con su
  huella (un código de comprobación): si el archivo se estropea, la huella deja de coincidir.

## Cómo hacer una copia nueva (para Claude)

1. `git fetch origin '+refs/heads/*:refs/remotes/origin/*'`
2. `git branch -f main origin/main`. Hace falta porque la `main` local puede ser antigua: el
   19/11/2026 lo era, y la copia habría restaurado una versión vieja.
3. `git bundle create app-teatre-cine-AAAA-MM-DD.bundle --branches --tags` y comprobar con
   `git bundle verify`.
4. `git archive --format=zip --prefix=app-teatre-cine/ -o app-teatre-cine-AAAA-MM-DD.zip HEAD`
5. Probar la restauración (opción B) en una carpeta temporal antes de entregarla.
