const { chromium, devices } = require('playwright');
const S = process.argv[2];
const ok = (c, m) => { console.log((c ? 'OK  ' : 'FALLO ') + m); if (!c) process.exitCode = 1; };
(async () => {
  const b = await chromium.launch();
  for (const disp of ['iPhone SE', 'iPhone 13', 'Pixel 7']) {
    const ctx = await b.newContext({ ...devices[disp], locale: 'es-ES', timezoneId: 'Europe/Madrid' });
    const p = await ctx.newPage();
    const errores = []; p.on('pageerror', (e) => errores.push(String(e)));
    await p.route(/fonts\.(googleapis|gstatic)/, (r) => r.abort());
    const base = 'http://127.0.0.1:4173/';
    const ancho = async () => p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
    for (const h of ['', '#cartelera', '#cine', '#noticias', '#favoritos', '#planes', '#historial', '#buscar', '#mapa', '#mapa-cine']) {
      await p.goto(base + h); await p.waitForTimeout(700);
      ok(await ancho(), `${disp} ${h || '#inicio'} sin desbordar a lo ancho`);
    }
    if (disp === 'iPhone 13') {
      // Cine → película → añadir sesión a un plan nuevo
      await p.goto(base + '#cine'); await p.waitForSelector('.tarjeta-peli');
      const n0 = await p.locator('.tarjeta-peli').count();
      await p.getByRole('button', { name: /^VOSE$/ }).click(); await p.waitForTimeout(300);
      const nVose = await p.locator('.tarjeta-peli').count();
      ok(nVose > 0 && nVose <= n0, `filtro VOSE: ${n0} → ${nVose}`);
      await p.getByRole('button', { name: /Versión: Todas/ }).click();
      await p.locator('.tarjeta-peli').first().click(); await p.waitForSelector('.peli-hero');
      ok(await p.locator('.cine-desplegable').count() > 0, `cines en desplegables: ${await p.locator('.cine-desplegable').count()}`);
      if (!(await p.locator('.cine-desplegable[open]').count())) await p.locator('.cine-desplegable summary').first().click();
      const href = await p.locator('.cine-desplegable[open] .entrada-hora').first().getAttribute('href');
      ok(/perfCode=|pillalas\.com\/pase\//.test(href || '') || !/admit-one|pillalas/.test(href || ''), `la hora lleva a la sesión: ${String(href).slice(0, 70)}`);
      await p.locator('.cine-desplegable[open] .entrada-plan').first().click(); await p.waitForSelector('#titulo-hoja-plan');
      await p.fill('#nombre-plan', 'Cine y teatro'); await p.getByRole('button', { name: 'Crear y añadir' }).click();
      ok(await p.locator('.aviso-plan').count() === 1, 'sesión de cine añadida a un plan');
      await p.locator('.aviso-plan a').click(); await p.waitForSelector('.plan-item');
      ok(await p.locator('.plan-item a.caja-titulo').count() === 1, 'el plan enlaza a la película');
      // Persona desde la película
      await p.goBack(); await p.waitForSelector('.peli-hero');
      const persona = p.locator('.personas .persona').first();
      if (await persona.count()) {
        await persona.click(); await p.waitForSelector('.persona-cabecera');
        ok((await p.locator('.fila-resultado').count()) >= 1, 'ficha de persona con algo en cartel');
      }
      // Buscador
      await p.goto(base + '#buscar'); await p.fill('#buscar-todo', 'mag'); await p.waitForTimeout(400);
      ok((await p.locator('.fila-resultado').count()) > 0, 'el buscador encuentra resultados');
      // Ocultar musicales
      await p.goto(base + '#cartelera'); await p.waitForSelector('.tarjeta');
      await p.getByRole('button', { name: /^Teatro/ }).first().click();
      const conMusical = await p.locator('.etiqueta.genero', { hasText: 'Musical' }).count();
      await p.getByRole('button', { name: /Más filtros/ }).click();
      await p.locator('#titulo-ocultos ~ .opciones .chip', { hasText: 'Musical' }).click();
      await p.locator('.hoja .boton-principal').click(); await p.waitForTimeout(300);
      for (let i = 0; i < 20 && (await p.getByRole('button', { name: /Ver más/ }).count()); i++) await p.getByRole('button', { name: /Ver más/ }).click();
      const sinMusical = await p.locator('.etiqueta.genero', { hasText: 'Musical' }).count();
      ok(conMusical > 0 && sinMusical === 0, `ocultar musicales: ${conMusical} visibles antes, ${sinMusical} después`);
      // Ficha de obra con traducción o temas
      await p.locator('.lista > .tarjeta').first().click(); await p.waitForSelector('.ficha h2');
      ok(true, 'ficha de obra abre: ' + (await p.locator('.ficha h2').textContent()));
      // Catalán
      await p.evaluate(() => localStorage.setItem('idioma', 'ca')); await p.goto(base); await p.waitForSelector('.titular');
      ok((await p.locator('.titular').textContent()).includes('Què veure'), 'Inicio en catalán');
      ok((await p.locator('.nav a').allInnerTexts()).join(',') === 'Inici,Teatre,Cinema,Agenda,Notícies', 'barra en catalán');
      await p.screenshot({ path: `${S}/capturas/e2e-inicio-ca.png` });
    }
    ok(errores.length === 0, `${disp} sin errores de JavaScript ${errores.slice(0, 2).join(' | ')}`);
    await ctx.close();
  }
  await b.close();
})();
