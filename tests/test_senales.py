"""Comprueba los criterios generales de la capa de señales con ejemplos
inventados (no con espectáculos reales concretos)."""

import unittest

from pipeline import senales


def actividad(titulo, descripcion="", sala=None, lugar=None):
    """Una actividad mínima en el formato común (pipeline/fuentes/base.py)."""
    return {"titulo": titulo, "descripcion": {"ca": descripcion} if descripcion else {},
            "lugar": {"nombre_en_fuente": sala, "tipo_de_lugar": lugar}}


class TestSenales(unittest.TestCase):
    def test_magia_en_el_titulo(self):
        r = senales.analizar(actividad('Espectacle de màgia "Tot és possible"'))
        self.assertEqual((r["tipo"], r["magia"]), ("magia", "principal"))

    def test_magia_solo_por_la_descripcion(self):
        r = senales.analizar(actividad('Espectacle "Desaparicions"',
                                       "Un espectacle d'il·lusionisme i mentalisme on res és el que sembla."))
        self.assertEqual(r["tipo"], "magia")

    def test_magia_por_el_artista(self):
        r = senales.analizar(actividad('Espectacle "Bon dia", a càrrec del Mag Exemple'))
        self.assertEqual(r["tipo"], "magia")

    def test_adjetivo_magico_no_es_magia(self):
        r = senales.analizar(actividad('Espectacle familiar "La nit més màgica"',
                                       "Un conte musical per a tota la família amb titelles."))
        self.assertNotEqual(r["tipo"], "magia")
        self.assertEqual(r["magia"], "no")

    def test_magia_ambiental_en_la_descripcion(self):
        r = senales.analizar(actividad('Espectacle "El ballet d\'hivern"',
                                       "Un ballet ple de bellesa, màgia i encant que transmet la màgia i l'esperit de Nadal."))
        self.assertEqual(r["magia"], "no")

    def test_metafora(self):
        r = senales.analizar(actividad('Contacontes "La màgia de la ciència"'))
        self.assertNotEqual(r["tipo"], "magia")

    def test_taller_de_magia_es_formacion(self):
        r = senales.analizar(actividad("Taller 'Màgia' (de 6 a 12 anys)"))
        self.assertEqual((r["tipo"], r["subtipo"], r["magia"]), ("evento", "formación", "tema"))

    def test_circo_con_numeros_de_magia(self):
        r = senales.analizar(actividad(
            'Espectacle "Pista"', "Un espectacle de circ amb acrobàcies, malabars, clown i números de màgia."))
        self.assertEqual((r["tipo"], r["magia"]), ("circo", "incluye"))

    def test_hipnosis_es_dudosa(self):
        r = senales.analizar(actividad('Espectacle "Dorm"', "Un show d'hipnosi amb voluntaris del públic."))
        self.assertEqual(r["tipo"], "magia")
        self.assertLessEqual(r["confianza"], 0.5)

    def test_personajes_del_cuento_no_son_magia_ni_hipnosis(self):
        r = senales.analizar(actividad(
            'Espectacle de titelles "El circ dels animals"',
            "Qui triarà la rateta? El gos equilibrista, l'ase mag o el gat hipnotitzador? Titelles per a tota la família."))
        self.assertNotEqual(r["tipo"], "magia")

    def test_escapisme_como_evasion(self):
        r = senales.analizar(actividad('"Ones". Sessions de dansa escènica',
                                       "Una peça de dansa sobre l'escapisme i la necessitat de fugir de la rutina."))
        self.assertEqual(r["magia"], "no")

    def test_cuento_con_magia_en_el_titulo_no_es_magia(self):
        r = senales.analizar(actividad('Explica\'m un conte: "Un conte de coratge i màgia"',
                                       "Dos germans s'endinsen en un bosc ple d'encanteris i una bruixa."))
        self.assertEqual((r["tipo"], r["magia"]), ("otro", "no"))

    def test_cuento_con_trucos_es_dudoso(self):
        r = senales.analizar(actividad('Contacontes "El drac fa màgia"',
                                       "Una aventura plena de trucs. Al final descobriràs si portes un petit mag a dins."))
        self.assertEqual(r["magia"], "incluye")
        self.assertLessEqual(r["confianza"], 0.5)

    def test_taller_con_personaje_mago_es_dudoso(self):
        r = senales.analizar(actividad("Taller 'L'aventura del mag Exemple (6 a 8 anys)'",
                                       "Un conte amb experiments: descobrirem que la ciència i la màgia estan a prop."))
        self.assertLessEqual(r["confianza"], 0.5)

    def test_taller_con_trucos_de_magia_es_tema(self):
        r = senales.analizar(actividad('Taller de ciència "Cervells"',
                                       "Mitjançant trucs de màgia i il·lusions, veurem com els mags enganyen el cervell."))
        self.assertEqual((r["tipo"], r["magia"]), ("evento", "tema"))

    def test_concierto_y_exposicion_fuera(self):
        self.assertEqual(senales.analizar(actividad("Concert de piano"))["tipo"], "otro")
        self.assertEqual(senales.analizar(actividad("Exposició 'Fonts màgiques'"))["tipo"], "otro")

    def test_festival_de_magia(self):
        r = senales.analizar(actividad("Festival de Màgia d'Exemple 2026"))
        self.assertEqual((r["tipo"], r["subtipo"], r["magia"]), ("evento", "festival", "tema"))

    def test_festival_con_ordinal_delante(self):
        r = senales.analizar(actividad("12è Festival de Màgia d'Exemple"))
        self.assertEqual((r["tipo"], r["subtipo"]), ("evento", "festival"))

    def test_gala_de_premios(self):
        r = senales.analizar(actividad('Gala "Nit del Circ - Premis Exemple 2026"'))
        self.assertEqual((r["tipo"], r["subtipo"]), ("evento", "premios"))

    def test_magia_como_sustantivo_en_la_descripcion(self):
        r = senales.analizar(actividad(
            'Espectacle familiar "El gran viatge"',
            "Un dels mags més poderosos examinarà el jove mag. Una producció on la màgia més espectacular "
            "es barreja amb el teatre."))
        self.assertEqual(r["tipo"], "magia")


if __name__ == "__main__":
    unittest.main()
