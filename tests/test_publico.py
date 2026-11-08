"""A quién va dirigida una actividad y nivel de la formación (ejemplos inventados)."""

import unittest

from pipeline import publico


class TestPublico(unittest.TestCase):
    def test_rango_de_edades_en_el_titulo(self):
        r = publico.leer("Taller 'Teatre' (de 6 a 12 anys)", es_formacion=True)
        self.assertEqual((r["publico"], r["edad_minima"], r["edad_maxima"]), ("infantil", 6, 12))

    def test_guion_en_el_titulo(self):
        self.assertEqual(publico.leer("Taller de circ (8-11 anys)")["edad_maxima"], 11)

    def test_a_partir_de(self):
        r = publico.leer("Taller 'Màgia' (a partir de 12 anys)")
        self.assertEqual((r["publico"], r["edad_minima"]), ("juvenil y adultos", 12))

    def test_adultos_y_nivel_avanzado(self):
        r = publico.leer("Taller 'Màgia adults avançat'",
                         "Per a persones que ja tenen coneixements previs.", es_formacion=True)
        self.assertEqual((r["publico"], r["nivel"]), ("adultos", "avanzado"))

    def test_iniciacion(self):
        r = publico.leer("Taller de clown", "Un taller d'iniciació. No cal experiència prèvia.", es_formacion=True)
        self.assertEqual(r["nivel"], "iniciación")

    def test_edades_del_publico_en_la_descripcion(self):
        r = publico.leer('Taller "Cervells"', "Adreçat a nens i nenes de 8 a 12 anys.")
        self.assertEqual((r["publico"], r["edad_minima"], r["edad_maxima"]), ("infantil", 8, 12))

    def test_edades_de_los_participantes_no_son_el_publico(self):
        r = publico.leer("Festival de Màgia Jove",
                         "Una plataforma d'exhibició per als i les joves il·lusionistes d'entre 14 i 25 anys.")
        self.assertIsNone(r["publico"])

    def test_edat_recomanada(self):
        r = publico.leer('Espectacle "Bombolles"', "Edat recomanada: a partir de 3 anys.")
        self.assertEqual((r["publico"], r["edad_minima"]), ("familiar", 3))

    def test_familiar_y_castellano(self):
        self.assertEqual(publico.leer('Espectacle familiar "Ona"')["publico"], "familiar")
        self.assertEqual(publico.leer("Taller", "Para niños y niñas de 4 a 6 años.")["publico"], "infantil")

    def test_precio_por_adulto_no_es_el_publico(self):
        self.assertIsNone(publico.leer('Espectacle "Nit"', "Entrada: 10 € per adult i 5 € per infant.")["publico"])

    def test_palabras_del_nombre_de_la_obra_no_son_el_publico(self):
        self.assertIsNone(publico.leer('Espectacle "Adultos sin remedio"')["publico"])
        self.assertIsNone(publico.leer('Espectacle "Adolescents"')["publico"])
        self.assertEqual(publico.leer('Espectacle "Nit de riure" (per a adults)')["publico"], "adultos")

    def test_edad_minima_de_un_espectaculo(self):
        self.assertEqual(publico.leer('Dansa "Fum"', "Edat recomanada: a partir de 8 anys.")["publico"],
                         "todos los públicos")

    def test_etiqueta(self):
        self.assertEqual(publico.etiqueta({"publico": "infantil", "edad_minima": 6, "edad_maxima": 12,
                                           "nivel": "iniciación"}), "infantil (6–12 años) · nivel iniciación")


if __name__ == "__main__":
    unittest.main()
