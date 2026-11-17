"""Lector de webs de salas: lo que dice la IA solo vale si está escrito en la página."""
import datetime as dt
import unittest

from pipeline.fuentes import webs_salas as w

HOY = dt.date(2026, 11, 17)
PAGINA = """<html><nav><a href="/agenda">Agenda</a></nav><h2>NOVEMBRE</h2>
<div><h3>La Botiga dels horrors</h3><p>Dv 20 i Ds 21 de novembre, a les 20.30 h. Entrades: 12 € (anticipada 10 €)</p>
<a href="https://entrades.example.com/botiga">Compra</a></div>
<div><h3>Concert de Nadal</h3><p>Diumenge 21/12 a les 18:00</p></div></html>"""


class TestWebsSalas(unittest.TestCase):
    def setUp(self):
        self.texto, self.enlaces = w.texto_pagina(PAGINA, "https://sala.cat/")

    def obra(self, **k):
        base = {"titulo": "La Botiga dels horrors", "cita_titulo": "La Botiga dels horrors", "descripcion": "",
                "funciones": [{"fecha": "2026-11-20", "hora": "20:30", "cita": "Dv 20 i Ds 21 de novembre, a les 20.30 h"}],
                "cita_precio": "Entrades: 12 € (anticipada 10 €)", "enlace": "https://entrades.example.com/botiga", "idioma": "ca"}
        return base | k

    def test_obra_correcta(self):
        v = w.verificar_obra(self.obra(), self.texto, self.enlaces, HOY)
        self.assertEqual([(f["fecha"], f["hora"]) for f in v["funciones"]], [("2026-11-20", "20:30")])
        self.assertEqual((v["precio"]["minimo"], v["precio"]["maximo"]), (10, 12))  # lo lee el programa, no la IA
        self.assertEqual(v["enlace"], "https://entrades.example.com/botiga")

    def test_fecha_que_no_dice_la_cita(self):
        o = self.obra(funciones=[{"fecha": "2026-11-27", "hora": "20:30", "cita": "Dv 20 i Ds 21 de novembre, a les 20.30 h"}])
        self.assertIsNone(w.verificar_obra(o, self.texto, self.enlaces, HOY))  # el 27 no sale en la cita

    def test_cita_inventada(self):
        o = self.obra(funciones=[{"fecha": "2026-11-20", "hora": "20:30", "cita": "Divendres 20 de novembre a les 20.30"}])
        self.assertIsNone(w.verificar_obra(o, self.texto, self.enlaces, HOY))  # no está en la página

    def test_hora_que_no_dice_la_cita(self):
        o = self.obra(funciones=[{"fecha": "2026-11-20", "hora": "21:00", "cita": "Dv 20 i Ds 21 de novembre, a les 20.30 h"}])
        self.assertIsNone(w.verificar_obra(o, self.texto, self.enlaces, HOY)["funciones"][0]["hora"])

    def test_mes_en_otro_sitio_y_formato_numerico(self):
        o = self.obra(titulo="Concert de Nadal", cita_titulo="Concert de Nadal", cita_precio="", enlace="",
                      funciones=[{"fecha": "2026-12-21", "hora": "18:00", "cita": "Diumenge 21/12 a les 18:00"}])
        self.assertEqual(w.verificar_obra(o, self.texto, self.enlaces, HOY)["funciones"][0]["hora"], "18:00")
        o2 = self.obra(funciones=[{"fecha": "2026-11-21", "hora": "", "cita": "NOVEMBRE … Ds 21"}])
        self.assertEqual(len(w.verificar_obra(o2, self.texto, self.enlaces, HOY)["funciones"]), 1)

    def test_titulo_y_enlace_inventados(self):
        self.assertIsNone(w.verificar_obra(self.obra(titulo="Hamlet", cita_titulo="Hamlet"), self.texto, self.enlaces, HOY))
        self.assertIsNone(w.verificar_obra(self.obra(enlace="https://otra.cat/x"), self.texto, self.enlaces, HOY)["enlace"])

    def test_fecha_pasada_o_lejana(self):
        o = self.obra(funciones=[{"fecha": "2025-11-20", "hora": "", "cita": "Dv 20 i Ds 21 de novembre"}])
        self.assertIsNone(w.verificar_obra(o, self.texto, self.enlaces, HOY))

    def test_un_periodo_no_son_dos_funciones(self):
        # Error del 17/11/2026: «del 19 al 29 de novembre» salía como funciones del 19 y del 29.
        texto, enlaces = w.texto_pagina("<h3>Con vista al mar</h3><p>Del 19 al 29 de novembre. De dijous a dissabte a les 20 h</p>", "https://s.cat/")
        o = self.obra(titulo="Con vista al mar", cita_titulo="Con vista al mar", cita_precio="", enlace="",
                      funciones=[{"fecha": "2026-11-19", "hora": "", "cita": "Del 19 al 29 de novembre"},
                                 {"fecha": "2026-11-29", "hora": "", "cita": "Del 19 al 29 de novembre"}])
        self.assertIsNone(w.verificar_obra(o, texto, enlaces, HOY))
        # Con el periodo y los días de la semana, las funciones las calcula el programa:
        o["periodo"] = {"inicio": "2026-11-19", "fin": "2026-11-29", "cita": "Del 19 al 29 de novembre",
                        "cita_horario": "De dijous a dissabte a les 20 h"}
        v = w.verificar_obra(o, texto, enlaces, HOY)
        self.assertEqual([(f["fecha"], f["hora"]) for f in v["funciones"]],
                         [("2026-11-19", "20:00"), ("2026-11-20", "20:00"), ("2026-11-21", "20:00"),
                          ("2026-11-26", "20:00"), ("2026-11-27", "20:00"), ("2026-11-28", "20:00")])
        # Sin días de la semana no se inventa nada:
        o["periodo"]["cita_horario"] = ""
        self.assertIsNone(w.verificar_obra(o, texto, enlaces, HOY))

    def test_web_compartida_por_dos_salas(self):
        # Error del 17/11/2026: los dos locales de The Comedy Clubhouse tienen la misma web y cada
        # espectáculo salía en los dos. Solo va a la sala que nombra la página.
        a, b = "The Comedy Clubhouse *Canvis Nous", "The Comedy Clubhouse *Laietana & Nikki's"
        self.assertEqual(w.propias(a, [b]), {"canvis", "nous"})
        self.assertEqual(w.propias(b, [a]), {"laietana", "nikki"})


if __name__ == "__main__":
    unittest.main()
