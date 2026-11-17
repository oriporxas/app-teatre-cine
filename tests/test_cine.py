"""Cine, noticias y la comprobación de los premios que cita la IA."""
import datetime as dt
import unittest

from pipeline.cine import lectores, salas, tmdb
from pipeline import noticias

RENOIR = """
<!-- Visible en lg y xl -->
<a href="/pelicula/dersu-uzala/">DERSU UZALA (EL CAZADOR) [WILDER CINEMA]</a>
<br><small style="color:#748294"><b> de Kurosawa, Akira </b></small>
<br><small>Versión Original subtitulada a Castellano</small>
<br><small style="color:#748294"> Duración 144 minutos </small>
<div class="pase-cartelera text-center ">
    <span style="font-size:12px">sala 03</span>
    <span><a href="https://www.pillalas.com/pase/x/1/" class="btn btn-evento">20:00</a></span>
    <div class="pase-cartelera-tag">PASE ESPECIAL</div>
</div>
<!-- end visible en lg y xl -->
<!-- Visible en md --> <a href="/pelicula/dersu-uzala/">DERSU UZALA</a> 20:00
"""


class TestLectores(unittest.TestCase):
    def test_versiones(self):
        casos = {"VOSE ATMOS": "VOSE", "DOBLADA ESP": "Castellano", "CATALÁN": "Català", "Original Catalán": "Català",
                 "Versión Original subtitulada a Castellano": "VOSE", "Versión Original Castellano": "Castellano",
                 "VOSI": "VO", "DIRECTO": None}
        for texto, esperado in casos.items():
            self.assertEqual(lectores.version(texto), esperado, texto)

    def test_renoir_un_dia(self):
        s = lectores._renoir_dia(RENOIR, "c1")
        self.assertEqual(len(s), 1)  # la versión para tabletas no duplica la sesión
        self.assertEqual(s[0]["pelicula"]["direccion"], ["Akira Kurosawa"])
        self.assertEqual((s[0]["hora"], s[0]["version"], s[0]["sala"], s[0]["especial"]), ("20:00", "VOSE", "Sala 3", "PASE ESPECIAL"))

    def test_fecha_hora(self):
        self.assertEqual(lectores._fecha_hora("20261217150000"), ("2026-12-17", "15:00"))
        self.assertEqual(lectores._fecha_hora("202611172240"), ("2026-11-17", "22:40"))


class TestSalas(unittest.TestCase):
    def test_nombres(self):
        casos = {"Cinemes Girona": "Cinemes Girona", "Cinemes Renoir *Floridablanca": "Renoir Floridablanca",
                 "Cinema Yelmo *La Maquinista": "Yelmo La Maquinista", "Mooby Bosque Multicines": "Mooby Bosque",
                 "Cinesa Diagonal *C. Lúdic Diagonal": "Cinesa Diagonal"}
        for fuente, esperado in casos.items():
            self.assertEqual(salas.nombre_limpio(fuente, None), esperado)
        self.assertEqual(salas.nombre_limpio("Sala de Cinema", "Sala de Cinema - Ateneu Barcelonès"), "Ateneu Barcelonès")


class TestTmdb(unittest.TestCase):
    def test_variantes_de_titulo(self):
        self.assertEqual(tmdb._variantes_titulo("DERSU UZALA (EL CAZADOR) [WILDER CINEMA]"),
                         ["DERSU UZALA (EL CAZADOR)", "DERSU UZALA"])

    def test_nombres_en_cualquier_orden(self):
        self.assertEqual(tmdb._palabras_nombres(["McDonagh, Martin"]), tmdb._palabras_nombres(["Martin McDonagh"]))

    def test_sin_clave_no_hace_nada(self):
        import os
        antes = os.environ.pop("TMDB_TOKEN", None)
        try:
            self.assertFalse(tmdb.disponible())
        finally:
            if antes is not None:
                os.environ["TMDB_TOKEN"] = antes


class TestNoticias(unittest.TestCase):
    def test_canal_rss(self):
        xml = """<rss><channel><item><title><![CDATA[Estrena &amp; teatre]]></title><link>https://ex.cat/a</link>
        <pubDate>Tue, 17 Nov 2026 12:09:37 +0000</pubDate><description><![CDATA[<img src="https://ex.cat/i.jpg"> Text]]></description></item>
        <item><title>Vella</title><link>https://ex.cat/b</link><pubDate>Tue, 01 Sep 2026 12:00:00 +0000</pubDate></item></channel></rss>"""
        import unittest.mock as m
        resp = m.MagicMock()
        resp.read.return_value = xml.encode()
        with m.patch("urllib.request.urlopen", return_value=resp):
            r = noticias.leer_canal({"nombre": "Ex", "url": "https://ex.cat/feed"},
                                    dt.datetime(2026, 11, 7, tzinfo=dt.timezone.utc))
        self.assertEqual(len(r), 1)  # la antigua no entra
        self.assertEqual((r[0]["titulo"], r[0]["imagen"]), ("Estrena & teatre", "https://ex.cat/i.jpg"))


class TestPremiosCitados(unittest.TestCase):
    def test_solo_si_la_cita_esta_en_el_texto(self):
        from pipeline.enriquecer_ia import _normal
        texto = _normal("Guanyadora del Premi Max 2024   al millor espectacle. Una obra sobre la família.")
        self.assertIn(_normal("Premi Max 2024 al millor espectacle"), texto)
        self.assertNotIn(_normal("Premi Butaca 2023"), texto)


if __name__ == "__main__":
    unittest.main()


class TestFichasMagos(unittest.TestCase):
    def test_json_al_final_del_texto(self):
        from pipeline.fichas_personas import _json_final
        texto = 'He buscado… {"x": 1} y al final:\n{"encontrado": true, "nombre": "Mag Prova", "premios": []}'
        self.assertEqual(_json_final(texto)["nombre"], "Mag Prova")
        self.assertIsNone(_json_final("sin json"))
