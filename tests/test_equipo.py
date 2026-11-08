import unittest

from pipeline import equipo

FICHA = """Una obra sobre la memòria.
Direcció: Anna Prova
Intèrprets: Joan Exemple i Marta Exemple.
Il.luminació: Pere Llum
Edat recomanada: a partir de 8 anys
Durada: 60 minuts"""


class TestEquipo(unittest.TestCase):
    def test_lee_solo_los_papeles(self):
        self.assertEqual(equipo.leer(FICHA), [["direcció", "Anna Prova"], ["intèrprets", "Joan Exemple i Marta Exemple"],
                                              ["il·luminació", "Pere Llum"]])

    def test_sin_ficha_artistica(self):
        self.assertEqual(equipo.leer("Un espectacle per a tota la família. Durada: 50 minuts"), [])

    def test_quita_la_ficha_de_la_descripcion(self):
        self.assertEqual(equipo.sin_creditos(FICHA),
                         "Una obra sobre la memòria.\nEdat recomanada: a partir de 8 anys\nDurada: 60 minuts")

    def test_dos_papeles_en_una_linea(self):
        self.assertEqual(equipo.leer("Traducció: Anna Prova IL·LUMINACIÓ Pere Llum"),
                         [["traducció", "Anna Prova"], ["il·luminació", "Pere Llum"]])


class TestFormatos(unittest.TestCase):
    def test_varios_papeles_en_una_linea(self):
        self.assertEqual(equipo.leer("Fitxa artística\nDirecció: Anna Prova; Músics: Pere Exemple (piano); Intèrpret: Joan Exemple."),
                         [["direcció", "Anna Prova"], ["intèrpret", "Joan Exemple"], ["músics", "Pere Exemple (piano)"]])

    def test_papel_y_personas_en_lineas_distintas(self):
        self.assertEqual(equipo.leer("Una obra.\nDramatúrgia\nAnna Prova\nINTÈRPRETS\nJoan Exemple i Marta Exemple"),
                         [["dramatúrgia", "Anna Prova"], ["intèrprets", "Joan Exemple i Marta Exemple"]])

    def test_en_el_titulo(self):
        self.assertEqual(equipo.leer("", 'Teatre "Una obra", text i direcció Anna Prova'), [["text i direcció", "Anna Prova"]])
        self.assertEqual(equipo.leer("", 'Espectacle "Una obra", amb Joan Exemple'), [["amb", "Joan Exemple"]])
        self.assertEqual(equipo.leer("", "Espectacle 'Una obra', de la Cia. Prova"), [["companyia", "Cia. Prova"]])

    def test_en_una_frase_explicita(self):
        self.assertEqual(equipo.leer("A càrrec de Joan Exemple, amb la direcció de Anna Prova."),
                         [["direcció", "Anna Prova"], ["a càrrec de", "Joan Exemple"]])

    def test_no_salta_de_linea(self):
        self.assertEqual(equipo.leer("Amb la Cia. Prova\nUn embolic de fils."), [["companyia", "Cia. Prova"]])

    def test_sin_creditos_no_inventa(self):
        self.assertEqual(equipo.leer("Una història de Nadal plena d'emoció, música i tendresa."), [])


if __name__ == "__main__":
    unittest.main()
