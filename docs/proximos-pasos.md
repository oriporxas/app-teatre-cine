# Próximos pasos

Escrito el 19/11/2026, al terminar el primer borrador completo de la app. Para consultarlo cuando
quieras avanzar en el proyecto.

## 1. Lo que tienes que hacer tú, por orden

1. **Recargar el crédito de la IA (urgente).** Quedaban unos 3,75 $ el 19/11, que dan para una
   semana más o menos. Se hace en la consola de Anthropic (console.anthropic.com), en «Billing».
   - Un día normal cuesta unos 0,30–0,45 $, unos 10–14 $ al mes.
   - Si se acaba, la app sigue funcionando, pero lo nuevo dudoso no sale hasta que la IA lo lea y
     las noticias dejan de resumirse.
2. **Publicar la app en Cloudflare Pages** (ya hiciste el primer paso, la cuenta).
   1. Entra en dash.cloudflare.com → «Workers & Pages» → «Create» → pestaña «Pages» → «Connect to
      Git».
   2. Conecta GitHub y elige **solo** el repositorio `oriporxas/app-teatre-cine`.
   3. Configuración:
      - nombre del proyecto: uno poco evidente, porque la dirección será `nombre.pages.dev`;
      - «Root directory»: `web`;
      - «Build command»: `npm ci && npm run build`;
      - «Build output directory»: `dist`.
   4. «Save and Deploy» y espera unos minutos.
   5. En el iPhone, abre la dirección con Safari → botón Compartir → «Añadir a pantalla de inicio».

   Desde entonces se publica sola con cada actualización. Si alguna pantalla de Cloudflare no
   coincide con estos pasos, manda una captura a Claude.
3. **Probar la app unos días en el móvil** y apuntar lo que falle o quieras cambiar, mejor con
   capturas. Así se hizo cada revisión hasta ahora.
4. **Guardar la copia de seguridad** (zip, bundle y nota del 19/11/2026) en dos sitios distintos.
   Pide una copia nueva después de cambios grandes, por ejemplo una vez al mes.
5. **Decisiones pendientes, cuando quieras:**
   - el nombre de la app (mientras, «Cartelera Barcelona»);
   - el presupuesto mensual de la IA;
   - si quieres que solo tú puedas entrar en la app: Cloudflare Access es gratis, pero pide tarjeta.

## 2. Lo que hace la app sola (no tienes que hacer nada)

- **Dos actualizaciones al día:** la completa a las 06:17 y la rápida a las 14:17, hora de
  Barcelona en invierno (una hora más en verano). GitHub suele retrasarlas hasta una hora. Si la de
  la mañana falla, la del mediodía hace la completa.
- **Al abrir la app,** el móvil recoge la última versión ya preparada. Lo que ya ha empezado
  desaparece al momento, y lo terminado pasa a «Caducado» durante un mes.
- **Fichas de personas:** quedan unos 800 nombres de teatro por mirar; se completan poco a poco
  cada día (gratis).
- **El apartado «Caducado»** se irá llenando hasta cubrir un mes entero.

## 3. Próximos pasos del proyecto (para pedírselos a Claude)

La prioridad sigue siendo teatro, magia, circo y eventos en Barcelona hasta que funcione muy bien.

1. **Revisar las primeras actualizaciones con todo lo nuevo:** tiempo, coste real por día y errores.
   Pídelo así: «revisa las actualizaciones de estos días».
2. **Salas que se escapan:** 72 de las 161 salas oficiales aún no tienen ninguna actividad en
   nuestras fuentes (muchas son escuelas o asociaciones). Se puede ampliar el lector de webs de
   salas. Lista en `data/ciudades/barcelona/cobertura.json`.
3. **Cines sin horarios:** 17 de 25 (Cinesa, Yelmo, Girona, Filmoteca, Zumzeig…). Sus webs no dejan
   leer los horarios: hace falta un proveedor de horarios (de pago) o un acuerdo con ellos.
4. **Más fuentes (fase 5):** agenda cultural de la Generalitat, festivales y plataformas de venta
   de entradas.
5. **Compartir un plan con un enlace** que lo abra en la app de quien lo recibe. Se puede hacer en
   cuanto la app esté publicada.
6. **Avisos y cuenta (fase 4):** alertas de estrenos, últimas funciones y cambios en tus planes, y
   favoritos y planes guardados en la nube para no perderlos al cambiar de móvil. Necesitan
   cuentas y un pequeño servidor.
7. **Críticas:** un extracto breve de cada crítica, con enlace al medio.
8. **Más disciplinas,** si quieres: danza, conciertos… Hoy están fuera por decisión tuya.
9. **A largo plazo:** otras ciudades y, si va bien, convertirlo en negocio (ver `docs/brief.md`).

## 4. Cómo retomar el trabajo

- Abre una sesión de Claude Code con el repositorio y di qué quieres hacer. Claude lee `CLAUDE.md`
  y `docs/brief.md`, donde está todo lo decidido.
- Para aceptar cada cambio: el enlace del PR → «Merge pull request» → «Confirm merge».
- Vista previa privada: https://claude.ai/artifact/7ZSzcw6GNbXXf5idrGQw3z
- Si algo va mal con GitHub: `docs/copia-de-seguridad.md`.
