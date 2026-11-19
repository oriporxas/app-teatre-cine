"""Eventos de cine: festivales, ciclos, cinefórums, premios y talleres salen como eventos; las
proyecciones sueltas siguen en la cartelera de cine."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

from pipeline import eventos_cine


class TestEventosCine(unittest.TestCase):
    def test_festival_si_proyeccion_no(self):
        actividades = {
            "a1": {"titulo": "33a Festival de Cinema Independent de Barcelona", "descripcion": {"ca": "Festival amb 80 films."}},
            "a2": {"titulo": "Projecció \"Los domingos\"", "descripcion": {"ca": "Projecció de la pel·lícula."}},
            "a3": {"titulo": "Taller 'Guió de curtmetratge'", "descripcion": {"ca": "Aprèn a escriure un curt."}},
            "a4": {"titulo": "Exposició de fotografia", "descripcion": {"ca": "Fotografies del barri."}},
        }
        final = {"a1": {"tipo": "cine", "confianza": 0.9}, "a2": {"tipo": "cine", "confianza": 0.9},
                 "a3": {"tipo": "otro", "disciplina": None, "confianza": 0.9}, "a4": {"tipo": "otro", "confianza": 0.95}}
        # a4 no menciona el cine: ni se pregunta.
        self.assertEqual(eventos_cine._candidatas(actividades, final), ["a1", "a2", "a3"])

        respuesta = {"actividades": [{"id": "a1", "tipo": "festival", "confianza": 0.95},
                                     {"id": "a2", "tipo": "proyección", "confianza": 0.9},
                                     {"id": "a3", "tipo": "formación", "confianza": 0.9}]}

        class LotesFalsos:
            def __init__(self, *a, **k):
                self.recogidas = []

            def datos_en_curso(self):
                return []

            def enviar(self, cli, peticiones, **k):
                self.recogidas = [(respuesta, d) for _, d in peticiones.values()]

            def esperar(self):
                pass

        tarea = NS(nombre="eventos_cine", modelo="claude-haiku-5-5", esfuerzo="low", por_peticion=20,
                   maximo_por_ejecucion=100, activa=True, por_lotes=True)
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(eventos_cine.config, "carpeta_cache", lambda c, p: Path(d)), \
                mock.patch.object(eventos_cine.ajustes, "tareas_ia", lambda: {"eventos_cine": tarea}), \
                mock.patch.object(eventos_cine.ia, "disponible", lambda: True), \
                mock.patch.object(eventos_cine.ia, "Lotes", LotesFalsos):
            informe = {}
            eventos_cine.revisar(actividades, final, NS(id="prueba"), informe)
        self.assertEqual((final["a1"]["tipo"], final["a1"]["disciplina"], final["a1"]["subtipo"]), ("evento", "cine", "festival"))
        self.assertEqual(final["a2"]["tipo"], "cine")  # la proyección sigue en la cartelera de cine
        self.assertEqual((final["a3"]["tipo"], final["a3"]["subtipo"]), ("evento", "formación"))
        self.assertEqual(informe["ia"]["eventos_cine"]["eventos"], 2)


if __name__ == "__main__":
    unittest.main()
