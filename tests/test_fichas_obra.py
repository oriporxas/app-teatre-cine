"""Ficha completa de la obra desde su web oficial y personas de Wikidata: solo lo comprobable."""
import unittest

from pipeline import fichas_obra, personas
from pipeline.fuentes.webs_salas import texto_pagina

PAGINA = """<html><head><meta property="og:image" content="https://sala.cat/img/la-gavina-cartell.jpg"></head><body>
<h1>La gavina</h1><p>Direcció: Anna Puig. Intèrprets: Joan Mas, Laia Font i Pere Roca.</p>
<p>Durada: 1 h 30 min</p><p>Premi Max 2025 al millor espectacle.</p></body></html>"""


class TestFichasObra(unittest.TestCase):
    def setUp(self):
        self.texto, _ = texto_pagina(PAGINA, "https://sala.cat/obra/la-gavina")

    def test_cartel_propio(self):
        self.assertEqual(fichas_obra._imagen_propia(PAGINA, "https://sala.cat/obra/la-gavina"), "https://sala.cat/img/la-gavina-cartell.jpg")
        logo = PAGINA.replace("la-gavina-cartell.jpg", "logo-sala.png")
        self.assertIsNone(fichas_obra._imagen_propia(logo, "https://sala.cat/"))

    def test_solo_lo_que_esta_en_la_pagina(self):
        r = {"es_la_obra": True,
             "equipo": [{"papel": "Direcció", "personas": "Anna Puig", "cita": "Direcció: Anna Puig"},
                        {"papel": "Intèrprets", "personas": "Joan Mas, Laia Font, Pere Roca", "cita": "Intèrprets: Joan Mas, Laia Font i Pere Roca"},
                        {"papel": "Escenografia", "personas": "Persona Inventada", "cita": "Escenografia: Persona Inventada"}],
             "duracion_minutos": 90, "cita_duracion": "Durada: 1 h 30 min",
             "premios": [{"premio_es": "Premio Max 2025", "premio_ca": "Premi Max 2025", "cita": "Premi Max 2025 al millor espectacle"},
                         {"premio_es": "Premio Butaca", "premio_ca": "Premi Butaca", "cita": "Premi Butaca 2024"}]}
        v = fichas_obra.verificar(r, self.texto)
        self.assertEqual(v["equipo"], [["Direcció", "Anna Puig"], ["Intèrprets", "Joan Mas, Laia Font, Pere Roca"]])
        self.assertEqual(v["duracion"], 90)
        self.assertEqual([p["es"] for p in v["premios"]], ["Premio Max 2025"])

    def test_si_no_es_la_obra_nada(self):
        self.assertEqual(fichas_obra.verificar({"es_la_obra": False}, self.texto), {})


class TestPersonas(unittest.TestCase):
    def test_separar_nombres(self):
        self.assertEqual(personas.separar("Lluís Homar, Anna Puig i Joan Mas"), ["Lluís Homar", "Anna Puig", "Joan Mas"])
        self.assertEqual(personas.separar("Cia. La Canina"), ["Cia. La Canina"])
        self.assertEqual(personas.separar("Rigola"), [])  # un solo nombre: no se busca (demasiado ambiguo)

    def test_clave_igual_que_la_app(self):
        self.assertEqual(personas.clave("Marcel·lí Antúnez"), "marcelli-antunez")

    def test_solo_gente_de_escena(self):
        """Caso real (18/11/2026): el músico Jordi Cornudella recibió la ficha de un poeta con el mismo
        nombre. Una persona de Wikidata sin oficio de escena no sale, aunque el nombre coincida."""
        import tempfile
        from pathlib import Path
        from unittest import mock

        class Ciudad:
            id = "prueba"

        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "wikidata.json"
            hoy = __import__("datetime").date.today().isoformat()
            ruta.write_text(__import__("json").dumps({
                "jordi-cornudella": {"fecha": hoy, "v": personas.VERSION, "nombre": "Jordi Cornudella",
                                     "datos": {"wikidata": "Q1", "oficios": ["Q49757", "Q333634"]}},  # poeta, traductor
                "anna-puig": {"fecha": hoy, "v": personas.VERSION, "nombre": "Anna Puig",
                              "datos": {"wikidata": "Q2", "oficios": ["Q2259451"]}},  # actriz de teatro
                # Caso real: «Laura Garcia», de vestuario, recibía la ficha de una presentadora y actriz.
                "laura-garcia": {"fecha": hoy, "v": personas.VERSION, "nombre": "Laura Garcia",
                                 "datos": {"wikidata": "Q3", "oficios": ["Q33999", "Q13590141"]}},
                "_premios": {}}))
            items = [{"equipo": [["Música", "Jordi Cornudella"], ["Intèrprets", "Anna Puig"], ["vestuari", "Laura Garcia"]]}]
            with mock.patch.object(personas.config, "carpeta_cache", lambda c, p: Path(d)):
                salida = personas.aplicar(Ciudad(), items, {}, leer_webs=False)
        self.assertEqual(list(salida), ["anna-puig"])

    def test_el_papel_encaja_con_el_oficio(self):
        self.assertTrue(personas.encaja({"Intèrprets"}, {"Q33999"}))
        self.assertTrue(personas.encaja({"amb"}, {"Q33999"}))
        self.assertTrue(personas.encaja({"DIRECCIÓ"}, {"Q3387717"}))
        self.assertTrue(personas.encaja({"assessorament dramatùrgic"}, {"Q214917"}))
        self.assertTrue(personas.encaja({"disseny de cartell", "adaptació i direcció"}, {"Q3387717"}))
        self.assertFalse(personas.encaja({"vestuari"}, {"Q33999"}))
        self.assertFalse(personas.encaja({"Disseny de so", "espai sonor"}, {"Q33999"}))
        self.assertFalse(personas.encaja({"DIRECCIÓ"}, {"Q33999"}))  # actor, pero dirige: no se sabe

    def test_nombre_de_varias_personas_no_se_adivina(self):
        """Si en Wikidata hay dos personas con ese nombre, aunque solo una sea actriz, no se pone nada."""
        from unittest import mock

        def persona(nombre, oficio, pais="Q29"):
            return {"labels": {"es": {"value": nombre}}, "aliases": {},
                    "claims": {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q5"}}}}],
                               "P106": [{"mainsnak": {"datavalue": {"value": {"id": oficio}}}}],
                               "P27": [{"mainsnak": {"datavalue": {"value": {"id": pais}}}}]}}

        def wd(**p):
            if p["action"] == "wbsearchentities":
                return {"search": [{"id": "Q10"}, {"id": "Q11"}]}
            return {"entities": {"Q10": persona("Marta Pérez", "Q33999"), "Q11": persona("Marta Pérez", "Q11513337")}}

        with mock.patch.object(personas, "_wd", wd):
            self.assertEqual(personas._buscar("Marta Pérez"), {})

        def wd_uno(**p):
            if p["action"] == "wbsearchentities":
                return {"search": [{"id": "Q10"}]}
            return {"entities": {"Q10": persona("Lolita Flores", "Q33999")}}

        with mock.patch.object(personas, "_wd", wd_uno):
            self.assertEqual(personas._buscar("Lolita Flores")["wikidata"], "Q10")


if __name__ == "__main__":
    unittest.main()
