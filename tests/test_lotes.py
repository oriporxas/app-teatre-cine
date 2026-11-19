"""Peticiones a la IA por lotes (mitad de precio): enviar, recoger otro día, repetir los rechazos.
Con una IA simulada: estas pruebas no gastan nada."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

from pipeline import ia


def uso(entrada=1000, salida=200):
    return NS(input_tokens=entrada, output_tokens=salida, cache_read_input_tokens=0, cache_creation_input_tokens=0)


class IAFalsa:
    """Imita client.messages.batches: guarda lo enviado y responde lo que se le diga."""

    def __init__(self):
        self.enviados = []
        self.estado = "in_progress"
        self.respuestas = {}  # custom_id -> resultado
        self.cancelados = []
        self.messages = NS(batches=NS(create=self._crear, retrieve=self._mirar, results=self._resultados, cancel=self._cancelar))

    def _cancelar(self, id_):
        """Lo ya contestado se queda; lo demás pasa a «cancelado» (no se cobra)."""
        self.cancelados.append(id_)
        n = int(id_.removeprefix("lote")) - 1
        for r in self.enviados[n]:
            self.respuestas.setdefault(r["custom_id"], NS(type="canceled"))
        self.estado = "ended"

    def _crear(self, requests):
        self.enviados.append(list(requests))
        return NS(id=f"lote{len(self.enviados)}", processing_status="in_progress")

    def _mirar(self, id_):
        return NS(id=id_, processing_status=self.estado)

    def _resultados(self, id_):
        n = int(id_.removeprefix("lote")) - 1
        for r in self.enviados[n]:
            yield NS(custom_id=r["custom_id"], result=self.respuestas[r["custom_id"]])


def bien(datos: dict, stop="end_turn"):
    return NS(type="succeeded", message=NS(usage=uso(), stop_reason=stop,
                                           content=[NS(type="text", text=json.dumps(datos))]))


class TestLotes(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.dir.name)
        self.cli = IAFalsa()
        ia.GASTO.usd, ia.GASTO.por_tarea, ia.GASTO.tope = 0.0, {}, 10.0
        self.parches = [mock.patch.object(ia, "disponible", lambda: True), mock.patch.object(ia, "cliente", lambda: self.cli),
                        mock.patch.object(ia, "directo_hasta", lambda: 0)]  # aquí se prueban los lotes
        for p in self.parches:
            p.start()

    def tearDown(self):
        for p in self.parches:
            p.stop()
        ia.GASTO.usd, ia.GASTO.por_tarea, ia.GASTO.tope = 0.0, {}, None
        self.dir.cleanup()

    def enviar(self, lotes, peticiones):
        lotes.enviar(self.cli, modelo="claude-haiku-5-5", esfuerzo="low", sistema="S", esquema={"type": "object"},
                     peticiones=peticiones)

    def test_lo_que_no_llega_a_tiempo_se_pregunta_al_momento(self):
        """Uri (19/11/2026): lo nuevo tiene que detectarse rápido, no horas después."""
        lotes = ia.Lotes("prueba", self.carpeta)
        self.enviar(lotes, {"a": ("mensaje A", {"obra": "A"}), "b": ("mensaje B", {"obra": "B"})})
        # La IA ya ha contestado A pero no B cuando se acaba la espera.
        cid_a = self.cli.enviados[0][0]["custom_id"]
        self.cli.respuestas[cid_a] = bien({"ok": "A por lotes"})
        with mock.patch.object(ia, "pedir_json", return_value={"ok": "B normal"}) as normal, \
                mock.patch.object(ia.time, "sleep", lambda s: None):
            lotes.esperar(0)
        self.assertEqual(self.cli.cancelados, ["lote1"])
        normal.assert_called_once()  # solo B, a precio completo
        self.assertEqual(sorted(d["obra"] for _, d in lotes.recogidas), ["A", "B"])
        self.assertEqual(lotes.datos_en_curso(), [])

    def test_si_la_ejecucion_se_corta_lo_recoge_la_siguiente(self):
        lotes = ia.Lotes("prueba", self.carpeta)
        self.enviar(lotes, {"a": ("mensaje A", {"obra": "A"}), "b": ("mensaje B", {"obra": "B"})})
        lotes.esperar(0, rescatar=False)
        self.assertEqual(lotes.recogidas, [])
        self.assertEqual(sorted(d["obra"] for d in lotes.datos_en_curso()), ["A", "B"])  # no se vuelven a pedir
        # Al día siguiente la IA ya ha contestado: se recoge al abrir, a mitad de precio.
        for r in self.cli.enviados[0]:
            self.cli.respuestas[r["custom_id"]] = bien({"ok": r["params"]["messages"][0]["content"]})
        self.cli.estado = "ended"
        manana = ia.Lotes("prueba", self.carpeta)
        self.assertEqual(sorted(d["obra"] for _, d in manana.recogidas), ["A", "B"])
        self.assertEqual(manana.datos_en_curso(), [])
        precio_normal = (1000 * 0.10 + 200 * 0.50) / 1e6
        self.assertAlmostEqual(ia.GASTO.usd, 2 * precio_normal * 0.5)

    def test_un_rechazo_se_repite_por_la_via_normal(self):
        lotes = ia.Lotes("prueba", self.carpeta)
        self.enviar(lotes, {"a": ("mensaje A", {"obra": "A"})})
        cid = self.cli.enviados[0][0]["custom_id"]
        self.cli.respuestas[cid] = bien({}, stop="refusal")
        self.cli.estado = "ended"
        with mock.patch.object(ia, "pedir_json", return_value={"ok": "normal"}) as normal:
            lotes.esperar(1)
        normal.assert_called_once()
        self.assertEqual(lotes.recogidas, [({"ok": "normal"}, {"obra": "A"})])

    def test_pocas_peticiones_van_directas(self):
        """Con pocas preguntas (o al mediodía) no se espera a un lote: la respuesta llega al momento."""
        lotes = ia.Lotes("prueba", self.carpeta)
        with mock.patch.object(ia, "directo_hasta", lambda: 3), \
                mock.patch.object(ia, "pedir_json", return_value={"ok": "directa"}) as normal:
            self.enviar(lotes, {"a": ("mensaje A", {"obra": "A"})})
        normal.assert_called_once()
        self.assertEqual(self.cli.enviados, [])  # ningún lote
        self.assertEqual(lotes.recogidas, [({"ok": "directa"}, {"obra": "A"})])

    def test_tope_de_gasto(self):
        ia.GASTO.usd = 99.0
        lotes = ia.Lotes("prueba", self.carpeta)
        with self.assertRaises(ia.TopeDeGasto):
            self.enviar(lotes, {"a": ("mensaje A", {"obra": "A"})})
        self.assertEqual(self.cli.enviados, [])


class TestClasificarPorLotes(unittest.TestCase):
    def test_respuesta_de_otro_dia_solo_si_la_obra_no_ha_cambiado(self):
        from pipeline import clasificar_ia
        cache, informe = {}, {"errores": 0, "enviadas": 0, "tokens_entrada": 0, "tokens_salida": 0, "tokens_cache": 0,
                              "tokens_cache_escritura": 0}
        respuesta = {"clasificaciones": [
            {"id": "x1", "tipo": "teatro", "magia": "no", "confianza": 0.9, "subtipo": None, "generos": [], "motivo": ""},
            {"id": "x2", "tipo": "magia", "magia": "si", "confianza": 0.9, "subtipo": "mentalismo", "generos": [], "motivo": ""}]}
        lotes = mock.MagicMock()
        lotes.datos_en_curso.return_value = []
        # Se preguntó con la versión «h1» de las dos; hoy x2 ha cambiado su texto («h2-nueva»).
        lotes.recogidas = [(respuesta, {"huellas": {"x1": "h1", "x2": "h1"}})]
        lotes.informe = {"enviadas": 0, "recogidas": 1, "en_curso": 0, "repetidas_normal": 0, "errores": 0,
                         "tokens_entrada": 0, "tokens_salida": 0, "tokens_cache": 0, "tokens_cache_escritura": 0}
        tarea = NS(nombre="clasificar", modelo="claude-sonnet-5-5", esfuerzo="medium", por_peticion=10,
                   maximo_por_ejecucion=100)
        with mock.patch.object(clasificar_ia.ia, "Lotes", return_value=lotes):
            clasificar_ia._por_lotes(tarea, "S", {}, {"x1": "h1", "x2": "h2-nueva"}, [], cache, Path("."), informe)
        self.assertEqual(list(cache), ["x1"])  # x2 se volverá a preguntar con su texto nuevo


if __name__ == "__main__":
    unittest.main()
