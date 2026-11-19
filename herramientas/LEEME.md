# Herramientas de trabajo

Programas que Claude usa para comprobar la app y preparar la vista previa. No forman parte de la
app ni de la actualización diaria; están aquí para que la copia de seguridad del proyecto sea completa.

| Archivo | Para qué sirve |
|---|---|
| `comprobar_app.js` | Comprobación general de la app en tres móviles (iPhone SE, iPhone 13, Pixel 7): nada se sale de la pantalla, sin errores, cine, planes, catalán… |
| `comprobar_visto_historial.js` | «Visto» / «Hecho», historial, Agenda, Guardado y que lo empezado desaparezca. |
| `comprobar_caducado_personas.js` | Caducado del último mes, eventos de cine, buscador y fichas de personas. |
| `comprobar_empieza_pronto.js` | «Empieza pronto» (cine, escena y eventos) por la tarde y por la mañana. |
| `preparar_vista_previa.py` | Copia la app construida y los datos para la vista previa privada de Claude. |
| `vista-previa-plantilla.html` | La página que carga la app en esa vista previa. |
| `llenar_personas.py` | Rellena de una vez las fichas ampliadas de personas (sin el tope diario). |

Cómo se usan las comprobaciones (desde la carpeta `web/`): `npm run build`, después
`npx vite preview --port 4173` y, en otra ventana, `node ../herramientas/comprobar_app.js <carpeta>`
(la carpeta es donde se guardan las capturas, con una subcarpeta `capturas/`). Necesitan Playwright
con Chromium.
