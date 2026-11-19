"""Lo caducado del último mes (Uri, 19/11/2026): sigue en la app un mes con «Caducado»; después, fuera."""
import datetime as dt
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

from pipeline import caducados as cad

HOY = dt.date(2026, 11, 19)


def obra(id_, *fechas):
    return {"id": id_, "nombre": id_, "funciones": [[f, "20:00"] for f in fechas]}


class TestCaducados(unittest.TestCase):
    def actualizar(self, anteriores, actuales, hoy=HOY):
        return cad.actualizar(NS(id="prueba"), "escena", hoy, anteriores, actuales, cad.ultima_funcion, cad.recortar_escena)

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.parche = mock.patch.object(cad.config, "carpeta_ciudad", lambda c: Path(self.dir.name))
        self.parche.start()

    def tearDown(self):
        self.parche.stop()
        self.dir.cleanup()

    def test_lo_que_termina_pasa_a_caducado(self):
        ayer = [obra("a", "2026-11-17", "2026-11-18"), obra("b", "2026-11-18", "2026-11-25")]
        hoy = [obra("b", "2026-11-25")]
        res = self.actualizar(ayer, hoy)
        self.assertEqual([(x["id"], x["caducado"]) for x in res], [("a", "2026-11-18")])

    def test_lo_que_desaparece_con_funciones_futuras_no_ha_caducado(self):
        """Una obra cancelada o reclasificada no es «caducada»."""
        self.assertEqual(self.actualizar([obra("c", "2026-11-30")], []), [])

    def test_mas_de_un_mes_fuera(self):
        self.actualizar([obra("a", "2026-11-18")], [])
        self.assertEqual(len(self.actualizar([], [], hoy=dt.date(2026, 12, 18))), 1)  # 30 días: aún sale
        self.assertEqual(self.actualizar([], [], hoy=dt.date(2026, 12, 19)), [])     # 31 días: fuera

    def test_si_vuelve_a_cartel_deja_de_estar_caducada(self):
        self.actualizar([obra("a", "2026-11-18")], [])
        self.assertEqual(self.actualizar([], [obra("a", "2026-12-01")], hoy=dt.date(2026, 11, 20)), [])

    def test_peliculas_sin_sesiones(self):
        peli = {"id": "p1", "titulo": "Peli", "sesiones": [["c1", "2026-11-18", "18:00", None, None, None, None]]}
        res = cad.actualizar(NS(id="prueba"), "cine", HOY, [peli], [], cad.ultima_sesion, cad.recortar_cine)
        self.assertEqual(res, [{"id": "p1", "titulo": "Peli", "caducado": "2026-11-18"}])


if __name__ == "__main__":
    unittest.main()
