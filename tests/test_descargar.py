"""Descargas de datos abiertos: reintentos ante un «prohibido» pasajero y error con la dirección."""
import io
import unittest
import urllib.error
from unittest import mock

from pipeline.fuentes.open_data_bcn import descargar as d


def error(codigo):
    return urllib.error.HTTPError("https://x", codigo, "no", {}, io.BytesIO(b""))


class TestDescargar(unittest.TestCase):
    def test_403_pasajero_se_reintenta(self):
        # 18/11/2026: la API respondió 403 a GitHub un rato (antes y después funcionaba).
        with mock.patch.object(d, "_pedir", side_effect=[error(403), b"ok"]), mock.patch.object(d.time, "sleep") as dormir:
            self.assertEqual(d._pedir_con_reintentos("https://api/x"), b"ok")
        dormir.assert_called_once_with(30)

    def test_403_que_sigue_se_deja_y_dice_la_direccion(self):
        with mock.patch.object(d, "_pedir", side_effect=[error(403)] * 3), mock.patch.object(d.time, "sleep"):
            with self.assertRaisesRegex(d.ErrorDescarga, r"https://api/x .*403"):
                d._pedir_con_reintentos("https://api/x")

    def test_404_no_se_reintenta(self):
        with mock.patch.object(d, "_pedir", side_effect=[error(404), b"ok"]) as pedir, mock.patch.object(d.time, "sleep"):
            with self.assertRaises(d.ErrorDescarga):
                d._pedir_con_reintentos("https://api/x")
        self.assertEqual(pedir.call_count, 1)


if __name__ == "__main__":
    unittest.main()
