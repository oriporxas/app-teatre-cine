"""Verificador: cada error que ha visto Uri se convierte en una prueba que no puede volver a fallar."""
import datetime as dt
import unittest
from unittest import mock

from pipeline import verificar


class Ciudad:
    id = "prueba"
    nombre = "Barcelona"


MAPA = {"areas": [{"nombre": "x", "anillos": [[[2.10, 41.35], [2.22, 41.35], [2.22, 41.45], [2.10, 41.45]]]}]}


def ficha(**k):
    base = {"id": "a", "titulo": "Obra", "inicio": "2026-11-15", "fin": "2026-12-30", "descripcion": {"ca": "Direcció: Anna Puig."},
            "horario": [{"precios": "Entrada general de: 24.95 a 34.95 €"}]}
    return base | k


def item(**k):
    base = {"id": "a", "nombre": "Obra", "funciones": [["2026-11-20", "20:30"]], "sala": "Teatre X", "sala_id": "s1",
            "lat": 41.39, "lon": 2.16, "precio_min": 24.95, "precio_max": 34.95, "equipo": [["Direcció", "Anna Puig"]]}
    return base | k


class TestVerificar(unittest.TestCase):
    def comprobar(self, items, fichas):
        with mock.patch.object(verificar, "_guardar", lambda c, p, reg, n: dict(reg.cuenta)):
            return verificar.escena(Ciudad(), items, fichas, MAPA, dt.date(2026, 11, 17))

    def test_ficha_correcta_no_se_toca(self):
        it = item()
        self.assertEqual(self.comprobar([it], [ficha()]), {})
        self.assertEqual((it["precio_min"], it["precio_max"]), (24.95, 34.95))

    def test_precio_que_no_esta_en_la_fuente(self):
        # Error de Uri (17/11/2026): «Magia i comèdia al Bosc de les Fades» a 95 € (era 24,95 €).
        it = item(precio_min=95.0, precio_max=95.0)
        self.assertEqual(self.comprobar([it], [ficha()]), {"precio": 1})
        self.assertNotIn("precio_min", it)

    def test_funcion_fuera_del_periodo(self):
        # «De Perras y Criadas»: funciones de 2027 en una obra que acaba el 30/12/2026.
        it = item(funciones=[["2026-11-20", "20:30"], ["2027-10-30", "19:30"]])
        self.assertEqual(self.comprobar([it], [ficha()]), {"fecha": 1})
        self.assertEqual(it["funciones"], [["2026-11-20", "20:30"]])

    def test_hora_improbable(self):
        it = item(funciones=[["2026-11-20", "04:30"]])
        self.comprobar([it], [ficha()])
        self.assertEqual(it["funciones"], [["2026-11-20"]])

    def test_lugar_y_mapa(self):
        it = item(sala="Barcelona", lat=40.4, lon=-3.7)
        r = self.comprobar([it], [ficha()])
        self.assertEqual(r, {"sala": 1, "ubicacion": 1})
        self.assertNotIn("sala", it)
        self.assertNotIn("lat", it)

    def test_equipo_que_no_esta_en_el_texto(self):
        it = item(equipo=[["Direcció", "Anna Puig"], ["Intèrprets", "Persona Inventada"]])
        self.comprobar([it], [ficha()])
        self.assertEqual(it["equipo"], [["Direcció", "Anna Puig"]])

    def test_sin_funciones_futuras_no_sale(self):
        items = [item(funciones=[["2027-10-30", "19:30"]])]
        self.comprobar(items, [ficha()])
        self.assertEqual(items, [])

    def test_cine(self):
        datos = {"cines": [{"id": "c1", "nombre": "Cine"}, {"id": "c2", "nombre": "Barcelona", "direccion": "Carrer X 1"}],
                 "peliculas": [{"id": "p", "titulo": "Peli", "sesiones": [
                     ["c1", "2026-11-18", "20:00"], ["c9", "2026-11-18", "20:00"], ["c1", "2027-01-01", "20:00"], ["c1", "2026-11-18", "25:00"]]}]}
        with mock.patch.object(verificar, "_guardar", lambda c, p, reg, n: dict(reg.cuenta)):
            r = verificar.cine(Ciudad(), datos, dt.date(2026, 11, 17), 14)
        self.assertEqual(r, {"sala": 1, "cine": 1, "fecha": 1, "hora": 1})
        self.assertEqual(datos["peliculas"][0]["sesiones"], [["c1", "2026-11-18", "20:00"]])
        self.assertEqual(datos["cines"][1]["nombre"], "Carrer X 1")


if __name__ == "__main__":
    unittest.main()
