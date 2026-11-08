# App (fase 2)

Web instalable en el móvil (PWA) hecha con React y Vite. No tiene servidor
propio: cada noche `pipeline/exportar_web.py` escribe la cartelera de cada
ciudad en `public/datos/<ciudad>.json` y el móvil la descarga y busca dentro.

- `src/datos.ts`: forma de la cartelera (lo que no se sabe no viene).
- `src/filtros.ts`: búsqueda y filtros (decisiones de Uri en `docs/brief.md`).
- `src/textos.ts`: textos en castellano y catalán.
- `src/App.tsx`: pantallas (cartelera, ficha, «Más filtros», mapa y favoritos
  pendientes). La dirección (`#ficha-…`, `#mapa`) dice qué pantalla se ve, así
  funciona el botón «atrás» del móvil.
- `public/sw.js`: permite abrirla sin conexión con la última cartelera.

Probarla en el ordenador:

```bash
cd web && npm install && npm run dev
```

Preparar la versión para publicar (queda en `web/dist/`):

```bash
cd web && npm run check && npm run build
```
