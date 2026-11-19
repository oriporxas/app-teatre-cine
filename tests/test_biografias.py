"""Fichas de personas (TMDB y Wikidata): las de teatro solo si la coincidencia es segura."""
import unittest
from types import SimpleNamespace as NS
from unittest import mock

from pipeline import biografias

CIUDAD = NS(id="prueba", pais="ES", idiomas=("es", "ca"))


def resultado(id_, nombre, dep, idiomas=("es",)):
    return {"id": id_, "name": nombre, "known_for_department": dep,
            "known_for": [{"original_language": l} for l in idiomas]}


class TestBiografias(unittest.TestCase):
    def test_clave_y_trozo_como_la_app(self):
        # web/src/Buscar.tsx: slug(); web/src/Buscar.tsx: trozoPersona()
        self.assertEqual(biografias.slug("Clàudia Benito"), "claudia-benito")
        self.assertEqual(biografias.slug("Marcel·lí Antúnez"), "marcel-li-antunez")
        self.assertEqual(biografias.trozo("n-claudia-benito"), sum(map(ord, "n-claudia-benito")) % 16)

    def test_biografia_corta_por_una_frase(self):
        larga = "Primera frase de la biografía. " * 40
        b = biografias._bio(larga)
        self.assertLessEqual(len(b), biografias.MAX_BIO)
        self.assertTrue(b.endswith("."))

    def buscar(self, resultados, humanos=1, lugar="Barcelona, Spain"):
        def get(ruta, **p):
            return {"results": resultados} if ruta == "/search/person" else None
        with mock.patch.object(biografias.tmdb, "_get", get), \
                mock.patch.object(biografias, "detalles_tmdb", lambda i: {"tmdb": i, "lugar": lugar}), \
                mock.patch.object(biografias.personas, "humanos_con_nombre", lambda n: humanos):
            return biografias.buscar_escena("Anna Puig", {"Intèrprets"}, CIUDAD)

    def test_una_sola_actriz_con_ese_nombre(self):
        self.assertEqual(self.buscar([resultado(1, "Anna Puig", "Acting")])[:2], (1, "ok"))

    def test_perfil_vacio_no_cuenta(self):
        """Caso real (Nil Cardoner): TMDB tiene un segundo perfil sin ningún trabajo."""
        r = [resultado(1, "Anna Puig", "Acting"), {"id": 2, "name": "Anna Puig", "known_for_department": "Acting", "known_for": []}]
        self.assertEqual(self.buscar(r)[:2], (1, "ok"))

    def test_varias_personas_no_se_adivina(self):
        """Caso real (Marta Pérez): varias actrices con el mismo nombre."""
        r = [resultado(1, "Anna Puig", "Acting"), resultado(2, "Anna Puig", "Acting")]
        self.assertEqual(self.buscar(r)[:2], (None, "varias"))

    def test_el_oficio_tiene_que_encajar(self):
        """Caso real (Laura Garcia, de vestuario): una intérprete no es la directora de fotografía."""
        self.assertEqual(self.buscar([resultado(1, "Anna Puig", "Camera")])[:2], (None, "ninguna"))

    def test_nombre_comun_en_wikidata(self):
        self.assertEqual(self.buscar([resultado(1, "Anna Puig", "Acting")], humanos=3)[:2], (None, "nombre común"))

    def test_otro_pais(self):
        r = [resultado(1, "Anna Puig", "Acting", idiomas=("en",))]
        self.assertEqual(self.buscar(r, lugar="Ohio, USA")[:2], (None, "otro país"))

    def test_trabajos_mas_vistos(self):
        c = {"cast": [{"title": "Película", "release_date": "2021-03-01", "vote_count": 50, "character": "Ana"},
                      {"name": "Serie", "first_air_date": "2019-01-01", "vote_count": 80, "media_type": "tv", "character": "Laia"},
                      {"title": "Desconocida", "vote_count": 0}]}
        self.assertEqual(biografias._conocida(c), [["Serie", 2019, "serie", "Laia"], ["Película", 2021, "pelicula", "Ana"]])


if __name__ == "__main__":
    unittest.main()
