import unittest

from pipeline.exportar_web import _item, _sin_vacios, limpiar_titulo


class TestTitulos(unittest.TestCase):
    def test_comillas_y_artista(self):
        self.assertEqual(limpiar_titulo('Espectacle de màgia "Detalls", a càrrec de Exemple Pérez'),
                         ("Detalls", "Exemple Pérez"))
        self.assertEqual(limpiar_titulo('Espectacle "Nit", amb el Mago Exemple'), ("Nit", "Mago Exemple"))

    def test_apostrofo_dentro_del_nombre(self):
        self.assertEqual(limpiar_titulo('Espectacle "L’hora d’en Pere"')[0], "L’hora d’en Pere")

    def test_comillas_simples(self):
        self.assertEqual(limpiar_titulo("Taller 'Màgia' (de 6 a 12 anys)")[0], "Màgia")

    def test_lo_de_despues_no_es_el_artista(self):
        self.assertEqual(limpiar_titulo("Taller 'Màgia' (de 6 a 12 anys) *NOU*"), ("Màgia", None))
        self.assertEqual(limpiar_titulo("Espectacle \"Exemple\", d'Anna Prova"), ("Exemple", "Anna Prova"))

    def test_si_lo_de_delante_es_parte_del_nombre_se_deja_entero(self):
        titulo = 'Homenatge als 40 anys de "Una pel·lícula", de Exemple Pérez'
        self.assertEqual(limpiar_titulo(titulo), (titulo, None))
        self.assertEqual(limpiar_titulo("Matí de les escoles. Espectacle 'Prova'")[0], "Prova")

    def test_de_solo_con_nombre_propio(self):
        self.assertEqual(limpiar_titulo('Espectacle "Prova" de Bea Exemple'), ("Prova", "Bea Exemple"))
        self.assertEqual(limpiar_titulo('Espectacle "Prova" D\'aquí surten coses'), ("Prova", None))

    def test_formato_solo_palabra_entera(self):
        self.assertEqual(limpiar_titulo("Espectacles familiars al parc")[0], "Espectacles familiars al parc")

    def test_comillas_sueltas(self):
        self.assertEqual(limpiar_titulo("Espectacle ''prova\"")[0], "prova")

    def test_comillas_mezcladas(self):
        self.assertEqual(limpiar_titulo('Espectacle "Les Coses”, amb Anna Prova'), ("Les Coses", "Anna Prova"))

    def test_sin_comillas(self):
        self.assertEqual(limpiar_titulo("Teatre familiar La gran aventura")[0], "La gran aventura")


class TestSoloLoQueSeSabe(unittest.TestCase):
    def test_quita_lo_desconocido(self):
        self.assertEqual(_sin_vacios({"id": "x", "duracion": None, "idiomas": [], "gratis": False, "nombre": "A"}),
                         {"id": "x", "nombre": "A"})


def _ficha(**cambios):
    base = {"id": "x", "titulo": 'Musical "Prova"', "tipo": "musical", "subtipo": None, "generos": ["musical"],
            "magia": "no", "confianza": 0.85, "proximas_funciones": [{"fecha": "2026-11-20", "hora": "20:00"}],
            "descripcion": {}, "precio": {}, "direccion": {}, "coordenadas": {},
            "fuentes": [{"nombre": "Guia", "url": "https://guia.barcelona.cat/x"}]}
    return base | cambios


class TestMusicales(unittest.TestCase):
    def test_teatro_musical_seguro_sale_en_teatro_con_su_etiqueta(self):
        item = _item(_ficha())
        self.assertEqual((item["tipo"], item["generos"]), ("teatro", ["musical"]))

    def test_sin_seguridad_no_sale(self):
        # «Espectacle musical» sin más puede ser un concierto: espera a que la IA lo lea.
        self.assertIsNone(_item(_ficha(generos=[])))

    def test_el_genero_solo_en_teatro(self):
        self.assertNotIn("generos", _item(_ficha(tipo="circo", generos=[])))


if __name__ == "__main__":
    unittest.main()
