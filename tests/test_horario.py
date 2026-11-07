import datetime as dt
import unittest

from pipeline import horario

TABLA = (
    '<table class="timetable-table"><tr class="timetable-header"><th class="weekdays">Dies</th>'
    '<th class="hours">Hores</th><th class="prices">Preus</th><th class="description">Observacions</th></tr>'
    '<tr><td class="timetable-day" rowspan=1><div>21 febrer i <p style="margin:0">14 març</p></div></td>'
    '<td class="timetable-hour" rowspan=1><div>a les 11.00&nbsp;h i <p style="margin:0">a les 12.45&nbsp;h</p></div></td>'
    '<td class="timetable-price" rowspan=2><div>Entrada general: 18 € (+ despeses de gestió)</div></td>'
    '<td class="timetable-description" rowspan=2><div>Durada: 50 minuts. En català.</div></td></tr>'
    '<tr><td class="timetable-day" rowspan=1><div>Dijous, divendres i dissabte</div></td>'
    '<td class="timetable-hour" rowspan=1><div>a les 19.30&nbsp;h</div></td></tr></table>'
)


class TestHorario(unittest.TestCase):
    def test_tabla_con_rowspan(self):
        filas = horario.leer_tabla(TABLA)
        self.assertEqual(len(filas), 2)
        self.assertIn("18 €", filas[1]["precios"])  # la celda de precio ocupa dos filas

    def test_dias_semana(self):
        d = horario.leer_dias("De dimarts a dissabte excepte 25 desembre",
                              dt.date(2026, 11, 1), dt.date(2027, 1, 31))
        self.assertEqual(d["semana"], [1, 2, 3, 4, 5])
        self.assertEqual(d["excepto"], ["2026-12-25"])

    def test_fechas_con_anyo_deducido(self):
        d = horario.leer_dias("5 novembre, 3 desembre i 21 gener", dt.date(2026, 11, 5), dt.date(2027, 1, 21))
        self.assertEqual(d["fechas"], ["2026-11-05", "2026-12-03", "2027-01-21"])

    def test_horas(self):
        self.assertEqual(horario.leer_horas("a les 11.00 h, a les 12.45 h i a les 16.00 h"),
                         [{"inicio": "11:00"}, {"inicio": "12:45"}, {"inicio": "16:00"}])
        self.assertEqual(horario.leer_horas("de 09.00 h a 15.30 h"), [{"inicio": "09:00", "fin": "15:30"}])

    def test_precios(self):
        self.assertEqual(horario.leer_precios("Entrada general de: 17 a 19 €")["minimo"], 17)
        self.assertEqual(horario.leer_precios("Entrada general de: 17 a 19 €")["maximo"], 19)
        self.assertTrue(horario.leer_precios("Entrada Gratuïta")["gratis"])
        self.assertIsNone(horario.leer_precios("Cal inscripció prèvia"))

    def test_duracion_e_idioma(self):
        self.assertEqual(horario.leer_duracion("Durada: 1 hora i 15 minuts"), 75)
        self.assertEqual(horario.leer_duracion("Durada: 70 minuts"), 70)
        self.assertEqual(horario.leer_idiomas("Espectacle en castellà"), ["castellano"])
        self.assertEqual(horario.leer_idiomas("Espectacle sense text"), ["sin_texto"])

    def test_funciones(self):
        r = horario.interpretar(TABLA, "2027-02-21", "2027-03-20", hoy=dt.date(2027, 2, 1))
        funciones = r["proximas_funciones"]
        self.assertIn({"fecha": "2027-02-21", "hora": "11:00"}, funciones)
        self.assertIn({"fecha": "2027-03-14", "hora": "12:45"}, funciones)
        self.assertIn({"fecha": "2027-02-25", "hora": "19:30"}, funciones)  # jueves
        self.assertEqual(r["duracion_minutos"], 50)
        self.assertEqual(r["idiomas"], ["catalan"])


if __name__ == "__main__":
    unittest.main()
