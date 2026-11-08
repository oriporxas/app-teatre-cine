"""Comprueba que la estructura preparada para crecer se mantiene:
ciudades con zona horaria/moneda/idiomas, fuentes como piezas independientes
y modelo de IA por tarea."""

import datetime as dt
import os
import unittest
from unittest import mock

from pipeline import ajustes, fuentes, salas
from pipeline.fuentes.base import id_global


class TestCiudades(unittest.TestCase):
    def test_barcelona_tiene_todo_lo_necesario(self):
        bcn = ajustes.ciudades()["barcelona"]
        self.assertEqual((bcn.pais, bcn.zona_horaria, bcn.moneda), ("ES", "Europe/Madrid", "EUR"))
        self.assertIn("ca", bcn.idiomas)
        self.assertIn("es", bcn.idiomas)
        self.assertIsInstance(bcn.hoy(), dt.date)

    def test_todas_las_fuentes_de_cada_ciudad_existen(self):
        for ciudad in ajustes.ciudades().values():
            for nombre in ciudad.fuentes:
                modulo = fuentes.cargar(nombre)
                self.assertEqual(modulo.NOMBRE, nombre)


class TestIA(unittest.TestCase):
    def test_cada_tarea_tiene_su_modelo(self):
        tareas = ajustes.tareas_ia()
        for nombre in ("clasificar", "revisar_dudosos"):
            self.assertTrue(tareas[nombre].modelo.startswith("claude-"))
        self.assertIsNotNone(tareas["revisar_dudosos"].umbral_confianza)

    def test_se_puede_cambiar_el_modelo_sin_tocar_el_codigo(self):
        ajustes.tareas_ia.cache_clear()
        try:
            with mock.patch.dict(os.environ, {"IA_CLASIFICAR_MODELO": "claude-sonnet-5-5"}):
                self.assertEqual(ajustes.tareas_ia()["clasificar"].modelo, "claude-sonnet-5-5")
        finally:
            ajustes.tareas_ia.cache_clear()


class TestFormatoComun(unittest.TestCase):
    def test_id_unico_en_el_mundo(self):
        self.assertEqual(id_global("open_data_bcn", "123"), "open_data_bcn:123")

    def test_salas_no_dependen_de_la_fuente(self):
        def act(clave, casa, interior):
            return {"ciudad": "x", "lugar": {"clave": clave, "nombre_casa": casa, "sala_interior": interior}}
        s = salas.consolidar([act("x:1", "Teatre A", "Sala Gran"), act("x:1", "Teatre A", "Sala Petita"),
                              act("x:2", None, None)])
        self.assertEqual(s["x:1"]["nombre"], "Teatre A")
        self.assertEqual(s["x:1"]["salas_interiores"], ["Sala Gran", "Sala Petita"])
        self.assertFalse(s["x:2"]["nombre_verificado"])


if __name__ == "__main__":
    unittest.main()
