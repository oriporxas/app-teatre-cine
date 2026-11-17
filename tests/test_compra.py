"""Enlace de compra: la página de la obra en la web de la sala, nunca una obra equivocada."""
import unittest

from pipeline import compra

PORTADA = """<nav><a href="/ca/entrades">Entrades</a><a href="/ca/cartellera">Cartellera</a></nav>
<a href="/ca/cartellera/c/332-el-mago-pop.html">El Mago Pop</a>
<a href="/ca/cartellera/c/332-el-mago-pop.html?goto=funcions">Comprar entrades</a>
<a href="/es/cartelera/c/332-el-mago-pop.html"></a>
<a href="/ca/cartellera/c/400-la-gavina.html">La gavina</a>"""


class TestCompra(unittest.TestCase):
    def test_portada(self):
        for u in ("https://www.teatreromea.cat/", "http://www.tantarantana.com", "https://x.cat/ca/", "https://x.cat/?lang=ca"):
            self.assertTrue(compra.es_portada(u), u)
        self.assertFalse(compra.es_portada("https://x.cat/ca/obra/la-gavina"))

    def test_elige_la_obra_de_ahora(self):
        web = "https://www.teatrevictoria.com/"
        c = compra.enlaces(PORTADA, web) + [("https://www.teatrevictoria.com/ca/cartellera/c/252-el-mago-pop.html", "")]
        self.assertEqual(compra.elegir("El Mago Pop", c, web), "https://www.teatrevictoria.com/ca/cartellera/c/332-el-mago-pop.html")

    def test_no_adivina(self):
        web = "https://sala.cat/"
        c = [("https://sala.cat/obra/hamlet-2025", ""), ("https://sala.cat/obra/hamlet-2026", "")]
        self.assertIsNone(compra.elegir("Hamlet", c, web))  # dos páginas posibles: mejor la portada
        self.assertIsNone(compra.elegir("Hamlet", [("https://altra.cat/hamlet", "Hamlet")], web))  # otra web
        self.assertIsNone(compra.elegir("La gavina", [("https://sala.cat/obra/gavines", "Gavines")], web))

    def test_titulos_largos_acortados(self):
        web = "https://teatreapolo.com"
        c = [("https://teatreapolo.com/cartelera/el-brujo-la-segunda-venida-de-cristo/", "El Brujo – La segunda venida de Cristo")]
        self.assertEqual(compra.elegir("La segunda venida de Cristo o el yo de la rubia", c, web), c[0][0])

    def test_boton_propio(self):
        pagina = """<header><a href="https://sala.cat/entrades">Entrades</a></header><h1>La gavina</h1>
        <a href="https://tickets.example.com/events/123">Comprar entrades</a><footer><a href="/reserves">Reserves</a></footer>"""
        self.assertTrue(compra.habla_de(pagina, "La gavina"))
        self.assertEqual(compra.boton_compra(pagina, "https://sala.cat/obra/la-gavina", set()), "https://tickets.example.com/events/123")
        # Con el título, el botón tiene que nombrar la obra (si no, se usa la página de la obra).
        self.assertIsNone(compra.boton_compra(pagina, "https://sala.cat/obra/la-gavina", set(), "La gavina"))
        nombra = pagina.replace("events/123", "events/la-gavina-123")
        self.assertEqual(compra.boton_compra(nombra, "https://sala.cat/obra/la-gavina", set(), "La gavina"),
                         "https://tickets.example.com/events/la-gavina-123")
        dos = pagina + '<a href="https://tickets.example.com/events/124">Comprar</a>'
        self.assertIsNone(compra.boton_compra(dos, "https://sala.cat/obra/la-gavina", set()))  # varias sesiones: la página de la obra

    def test_boton_de_otra_obra(self):
        # Error del 17/11/2026: en la página de «Vamos a tener que ir al psicólogo…», el único botón
        # de compra era de «El nuevo musical de los 80s y 90s».
        pagina = '<h1>Vamos a tener que ir al psicólogo después de esto</h1><a href="https://teatre.cat/ca/musicales/el-nuevo-musical-de-los-80s-90s">Entrades</a>'
        self.assertIsNone(compra.boton_compra(pagina, "https://teatre.cat/ca/humor/vamos-a-tener", set(),
                                              "Vamos a tener que ir al psicólogo después de esto"))

    def test_sin_seguimiento(self):
        self.assertEqual(compra.limpia("https://x.koobin.cat/obra?_gl=1%2Aabc&utm_source=x&id=3"), "https://x.koobin.cat/obra?id=3")


if __name__ == "__main__":
    unittest.main()
