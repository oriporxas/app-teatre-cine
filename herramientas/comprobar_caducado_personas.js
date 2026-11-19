const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'], deviceScaleFactor: 1, timezoneId: 'Europe/Madrid' });
  const p = await ctx.newPage();
  await p.clock.setFixedTime(new Date('2026-11-19T18:30:00+01:00'));
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  const base = 'http://127.0.0.1:4173/';
  const ok = (c, m) => console.log((c ? 'OK  ' : 'FALLO ') + m);
  await p.goto(base + '#inicio'); await p.waitForTimeout(1500);
  const titulos = await p.locator('.fila-inicio .seccion-titulo').allInnerTexts();
  ok(titulos.some((x) => /pronto en el cine/i.test(x)) && titulos.some((x) => /pronto en el teatro/i.test(x)), 'Inicio: dos filas de «Empieza pronto»: ' + titulos.join(' | '));
  ok(titulos.some((x) => /próximos eventos/i.test(x)), 'Inicio: fila de próximos eventos');
  ok(await p.locator('a.enlace-caducados-inicio').count() === 1, 'Inicio: enlace a lo caducado');
  await p.screenshot({ path: 'capturas/v10-inicio.png', fullPage: true });
  // Eventos → Teatro con el filtro de eventos
  await p.goto(base + '#eventos'); await p.waitForTimeout(800);
  ok(p.url().endsWith('#cartelera') && (await p.locator('.chip[aria-pressed="true"]').allInnerTexts()).some((x) => /Eventos/.test(x)), 'Ver todo de eventos abre Teatro con el filtro de eventos');
  // Cine: eventos de cine arriba
  await p.goto(base + '#cine'); await p.waitForTimeout(1000);
  ok(await p.locator('.eventos-cine .ticket').count() > 0, 'Cine: fila de eventos de cine (' + await p.locator('.eventos-cine .ticket').count() + ')');
  await p.screenshot({ path: 'capturas/v10-cine.png' });
  // Caducados
  await p.goto(base + '#caducados'); await p.waitForTimeout(800);
  const nCad = await p.locator('.fila-resultado.caducada').count();
  ok(nCad > 0, 'Apartado de caducados con ' + nCad + ' cosas; filtros: ' + (await p.locator('.chip').allInnerTexts()).join(','));
  await p.screenshot({ path: 'capturas/v10-caducados.png', fullPage: true });
  await p.locator('.chip', { hasText: 'Películas' }).click();
  ok(await p.locator('.fila-resultado.caducada').count() > 0, 'filtro de películas caducadas');
  await p.locator('.fila-resultado.caducada').first().click(); await p.waitForTimeout(600);
  ok(await p.locator('.etiqueta.caducado').count() > 0, 'la ficha de una película caducada lleva «Caducado»');
  await p.screenshot({ path: 'capturas/v10-peli-caducada.png' });
  // Buscar algo caducado
  const nombre = await p.evaluate(async () => (await (await fetch('./datos/barcelona.json')).json()).caducados[0].nombre);
  await p.goto(base + '#buscar'); await p.waitForTimeout(400);
  await p.locator('#buscar-todo').fill(nombre.slice(0, 14)); await p.waitForTimeout(500);
  ok(/caducado \(último mes\)/i.test(await p.locator('main').innerText()), `al buscar «${nombre.slice(0, 14)}» sale lo caducado`);
  await p.screenshot({ path: 'capturas/v10-buscar.png' });
  // Persona con ficha ampliada (cine)
  const per = await p.evaluate(async () => {
    for (let n = 0; n < 16; n++) {
      const d = await (await fetch(`./datos/barcelona-personas-${n}.json`)).json();
      const k = Object.keys(d.personas).find((x) => x.startsWith('t') && d.personas[x].conocida && d.personas[x].nacimiento);
      if (k) return k;
    }
  });
  await p.goto(base + '#persona-' + per); await p.waitForTimeout(1500);
  const txt = await p.locator('main').innerText();
  ok(/Nació/.test(txt) && /trabajos destacados/i.test(txt), 'persona de cine con nacimiento y trabajos (' + per + ')');
  await p.screenshot({ path: 'capturas/v10-persona.png', fullPage: true });
  console.log('errores JS:', errs);
  await b.close();
})();
