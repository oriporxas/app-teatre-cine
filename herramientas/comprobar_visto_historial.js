const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'], deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  const base = 'http://127.0.0.1:4173/';
  const ok = (c, m) => console.log((c ? 'OK  ' : 'FALLO ') + m);
  await p.goto(base + '#inicio'); await p.waitForTimeout(1200);
  ok((await p.locator('.nav a').allInnerTexts()).join(',') === 'Inicio,Teatro,Cine,Agenda,Noticias', 'barra con 5 pestañas: ' + (await p.locator('.nav a').allInnerTexts()).join(','));
  // Ficha de una obra de teatro: marcar como vista
  await p.goto(base + '#cartelera'); await p.waitForSelector('.tarjeta');
  const primera = p.locator('a.tarjeta').first();
  const nombre = (await primera.locator('.tarjeta-nombre').innerText()).trim();
  await primera.click(); await p.waitForSelector('.boton-marca');
  const antes = await p.locator('.boton-marca').innerText();
  await p.locator('.boton-marca').click();
  const despues = await p.locator('.boton-marca').innerText();
  ok(/Marcar como/.test(antes) && /Vist[ao]|Hecho/.test(despues), `ficha: «${antes.trim()}» → «${despues.trim()}» (${nombre})`);
  await p.screenshot({ path: 'capturas/v9-ficha.png' });
  // Tarjeta en la cartelera con la marca
  await p.goto(base + '#cartelera'); await p.waitForSelector('.tarjeta');
  ok(await p.locator('a.tarjeta').first().locator('.marca-hecho').count() === 1, 'la tarjeta lleva la marca');
  // Película
  await p.goto(base + '#cine'); await p.waitForSelector('.tarjeta-peli');
  await p.locator('.tarjeta-peli').first().click(); await p.waitForSelector('.boton-marca');
  await p.locator('.boton-marca').click();
  ok((await p.locator('.boton-marca').innerText()).includes('Vista'), 'película marcada como vista');
  // Plan con dos funciones: marcar una y el plan entero
  const obra = await p.evaluate(async () => {
    const r = await fetch('./datos/barcelona.json'); const d = await r.json();
    const e = d.espectaculos.find((x) => x.tipo === 'eventos' && x.funciones.length) || d.espectaculos[1];
    return { id: e.id, nombre: e.nombre, tipo: e.tipo, dia: e.funciones[0][0], hora: e.funciones[0][1] };
  });
  await p.evaluate((o) => {
    localStorage.setItem('planes', JSON.stringify([{ id: 'pprueba', nombre: 'Fin de semana', creado: '2026-11-19', items: [
      { id: o.id, dia: o.dia, hora: o.hora, nombre: o.nombre, ciudad: 'barcelona', zona: 'Europe/Madrid', clase: o.tipo }] }]));
  }, obra);
  await p.goto(base + '#plan-pprueba'); await p.reload(); await p.waitForSelector('.plan-item');
  await p.locator('.plan-item .check').first().click();
  ok(await p.locator('.plan-item.tachado').count() === 1, `función del plan tachada (${obra.tipo}: «${await p.locator('.plan-item .check').first().getAttribute('title')}»)`);
  await p.locator('.boton-marca.grande').click();
  ok((await p.locator('.boton-marca.grande').innerText()).includes('Hecho'), 'plan marcado como hecho');
  ok(await p.locator('h2.tachado').count() === 1, 'título del plan tachado');
  await p.screenshot({ path: 'capturas/v9-plan.png', fullPage: true });
  await p.goto(base + '#planes'); await p.waitForTimeout(500);
  ok((await p.locator('main').innerText()).includes('Planes hechos'), 'sección «Planes hechos»');
  await p.screenshot({ path: 'capturas/v9-planes.png' });
  // Historial
  await p.goto(base + '#historial'); await p.waitForTimeout(500);
  const filas = await p.locator('.fila-historial').count();
  ok(filas === 4, `historial con 4 cosas (${filas})`);
  await p.screenshot({ path: 'capturas/v9-historial.png', fullPage: true });
  await p.locator('.chip', { hasText: 'Cine' }).click();
  ok(await p.locator('.fila-historial').count() === 1, 'filtro Cine');
  // La pestaña Agenda recuerda el último apartado
  await p.goto(base + '#inicio'); await p.waitForTimeout(300);
  ok((await p.locator('.nav a').nth(3).getAttribute('href')) === '#historial', 'Agenda recuerda el último apartado');
  // Guardado: lo visto al final, tachado
  await p.goto(base + '#cartelera'); await p.waitForSelector('.tarjeta');
  await p.locator('a.tarjeta').first().click(); await p.waitForSelector('.boton-corazon');
  await p.locator('.boton-corazon').click();
  await p.goto(base + '#favoritos'); await p.waitForTimeout(400);
  ok(await p.locator('.tarjeta.tachado').count() === 1 && (await p.locator('main').innerText()).includes('Ya vistos'), 'guardado: lo visto, tachado al final');
  await p.screenshot({ path: 'capturas/v9-guardado.png' });
  // Quitar del historial
  await p.goto(base + '#historial'); await p.waitForTimeout(300);
  await p.locator('.fila-historial button').first().click();
  ok(await p.locator('.fila-historial').count() === 3, 'quitar la marca desde el historial');
  // Catalán
  await p.evaluate(() => localStorage.setItem('idioma', 'ca'));
  // Caducado: a las 23:30 no sale nada de hoy que ya haya empezado
  const ctx2 = await b.newContext({ ...devices['iPhone 13'], deviceScaleFactor: 1, timezoneId: 'Europe/Madrid' });
  const p2 = await ctx2.newPage();
  await p2.clock.setFixedTime(new Date('2026-11-19T23:30:00+01:00'));
  await p2.goto(base + '#cartelera'); await p2.waitForSelector('.tarjeta');
  await p2.locator('.chip', { hasText: 'Hoy' }).first().click(); await p2.waitForTimeout(400);
  const cuando = await p2.locator('.tarjeta .cuando').allInnerTexts();
  const malas = cuando.filter((c) => /Hoy/.test(c) && /(\d\d):(\d\d)/.test(c) && c.match(/(\d\d):(\d\d)/)[0] < '23:30');
  ok(malas.length === 0, `a las 23:30, ninguna función de hoy ya empezada (${cuando.length} tarjetas; malas: ${malas.slice(0, 3)})`);
  console.log('errores JS:', errs);
  await b.close();
})();
