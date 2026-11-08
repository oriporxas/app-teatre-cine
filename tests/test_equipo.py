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


if __name__ == "__main__":
    unittest.main()
