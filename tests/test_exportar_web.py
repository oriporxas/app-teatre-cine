import unittest

from pipeline.exportar_web import _sin_vacios, limpiar_titulo


class TestTitulos(unittest.TestCase):
    def test_comillas_y_artista(self):
        self.assertEqual(limpiar_titulo('Espectacle de màgia "Detalls", a càrrec de Exemple Pérez'),
                         ("Detalls", "Exemple Pérez"))
        self.assertEqual(limpiar_titulo('Espectacle "Nit", amb el Mago Exemple'), ("Nit", "Mago Exemple"))

    def test_apostrofo_dentro_del_nombre(self):
        self.assertEqual(limpiar_titulo('Espectacle "L’hora d’en Pere"')[0], "L’hora d’en Pere")

    def test_comillas_simples(self):
        self.assertEqual(limpiar_titulo("Taller 'Màgia' (de 6 a 12 anys)")[0], "Màgia")

    def test_sin_comillas(self):
        self.assertEqual(limpiar_titulo("Teatre familiar La gran aventura")[0], "La gran aventura")


class TestSoloLoQueSeSabe(unittest.TestCase):
    def test_quita_lo_desconocido(self):
        self.assertEqual(_sin_vacios({"id": "x", "duracion": None, "idiomas": [], "gratis": False, "nombre": "A"}),
                         {"id": "x", "nombre": "A"})


if __name__ == "__main__":
    unittest.main()
