const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch();
  for (const [hora, nombre] of [['2026-11-19T18:30:00+01:00', 'tarde'], ['2026-11-19T10:00:00+01:00', 'manana']]) {
    const ctx = await b.newContext({ ...devices['iPhone 13'], deviceScaleFactor: 1, timezoneId: 'Europe/Madrid' });
    const p = await ctx.newPage();
    const errs = []; p.on('pageerror', (e) => errs.push(e.message));
    await p.clock.setFixedTime(new Date(hora));
    await p.goto('http://127.0.0.1:4173/#inicio'); await p.waitForTimeout(1500);
    const filas = await p.locator('.empieza-pronto .pronto-fila').evaluateAll((els) => els.map((el) => {
      const h = el.querySelector('h3').innerText;
      const n = el.querySelectorAll('.ticket').length;
      const mins = [...el.querySelectorAll('.ticket-cuando')].map((x) => x.innerText);
      const nada = el.querySelector('.pronto-nada')?.innerText || '';
      return `${h}: ${n} ${nada} ${mins.slice(-1)}`;
    }));
    console.log(nombre, '|', await p.locator('.empieza-pronto > .fila-cabecera h2').innerText(), '|', filas.join(' || '), '| errores:', errs.length);
    await p.locator('.empieza-pronto').screenshot({ path: `capturas/v12-pronto-${nombre}.png` });
    await ctx.close();
  }
  await b.close();
})();
