"""Género de las obras de teatro: solo cuando el texto lo dice claramente."""
import unittest

from pipeline import genero


class TestGenero(unittest.TestCase):
    def g(self, titulo, desc="", subtipo=None):
        return genero.leer(titulo, desc, subtipo)

    def test_etiqueta_al_principio(self):
        self.assertEqual(self.g('Teatre "Obra"', "Musical. Una sàtira implacable dels nostres dies."),
                         ["musical", "comedia"])
        self.assertEqual(self.g('Teatre "Obra"', "Teatre musical. 90 minuts. Castellà"), ["musical"])
        self.assertEqual(self.g('Teatre "Obra"', "A càrrec de la Cia. X\nTeatre-musical. 75 minuts. Català"), ["musical"])
        self.assertEqual(self.g('Teatre "Obra"', "Sinopsi\nGènere: Comèdia negre\nDurada: 80 min"), ["comedia"])

    def test_frases_explicitas(self):
        self.assertEqual(self.g("X", "Crush és un musical amb música original."), ["musical"])
        self.assertEqual(self.g("X", "Una comèdia romàntica que posa sobre la taula l'amor."), ["comedia"])
        self.assertEqual(self.g("X", "L'autora ens presenta un drama íntim i punyent sobre el deute."), ["drama"])
        self.assertEqual(self.g("X", "Un espectacle de titelles per als més petits."), ["títeres"])
        self.assertEqual(self.g("X", "Una peça de teatre d'objectes per a tota la família."), ["teatro de objetos"])
        self.assertEqual(self.g("X", "Aquest thriller immobiliari et farà pensar."), ["suspense"])
        self.assertEqual(self.g("X", "Una lectura dramatitzada de l'obra."), ["lectura dramatizada"])
        self.assertEqual(self.g("X", "Una peça de teatre documental sobre l'exili."), ["teatro documental"])

    def test_humor_y_monologos(self):
        self.assertEqual(self.g("X", "Un monòleg divertit i emotiu sobre els anys 80."), ["monólogo"])
        self.assertEqual(self.g('Espectacle "Stand Up Comedy", amb X'), ["monólogo", "comedia"])
        self.assertEqual(self.g('Monòleg "Hoy se lía"', "Una nit de monòlegs d'humor."), ["monólogo", "comedia"])

    def test_titulo(self):
        self.assertEqual(self.g('Musical "Mamma Mia!"'), ["musical"])
        self.assertEqual(self.g('Teatre "Jana, el musical"'), ["musical"])
        self.assertEqual(self.g('Espectacle de titelles "Toc, toc!"'), ["títeres"])
        self.assertEqual(self.g('Lectura dramatitzada "Calla, nena"'), ["lectura dramatizada"])

    def test_palabras_sueltas_no_bastan(self):
        for desc in ("Una mica de comèdia i molta tendresa.",
                     "Parla del drama de l'habitatge a la ciutat.",
                     "Barreja titelles, cançons, humor i una alta dosi d'improvisació.",
                     "Direcció musical: Anna Prova.",
                     "Va ser una tragèdia familiar que es repeteix.",
                     "La trama del teatre de marionetes fracassa.",
                     "Els amants dels musicals ho gaudiran.",
                     "Un viatge musical per a nadons.",
                     "Inspirada en Chita Rivera, llegenda del teatre musical."):
            self.assertEqual(self.g("X", desc), [], desc)

    def test_contradiccion(self):
        # Comedia y drama a la vez, sin decir «tragicomèdia»: ninguno de los dos.
        self.assertEqual(self.g("X", "És una comèdia. També és un drama familiar."), [])
        self.assertEqual(self.g("X", "Una tragicomèdia sobre la família."), ["tragicomedia"])
        self.assertEqual(self.g("X", "Voltors és una comèdia àcida sobre un thriller immobiliari."), ["comedia"])

    def test_clown_y_maximo(self):
        self.assertEqual(self.g("X", "Un espectacle sense paraules.", "clown"), ["clown"])
        self.assertLessEqual(len(self.g('Musical "X"', "Un monòleg musical. Un espectacle de titelles.")), 2)

    def test_musical_en_senales(self):
        from pipeline import senales
        a = {"titulo": 'Espectacle "Crush"', "descripcion": {"ca": "CRUSH és un musical amb música original."},
             "lugar": {"nombre_en_fuente": "Teatre Goya"}}
        self.assertEqual(senales.analizar(a)["tipo"], "musical")


if __name__ == "__main__":
    unittest.main()
