"""Pruebas del desatascador de la Calle 18 con un 'traci' falso (sin SUMO): actua SOLO en el artefacto."""
import unittest
from types import SimpleNamespace

from src.simulation.desatascador import Desatascador


class TraciFalso:
    """Un movimiento (indice 0): llegada 'L_0' (200 m) -> interno ':j_0_0' -> salida 'S_0'."""
    def __init__(self):
        self.luz = "G"
        self.vehiculos = {}     # id -> dict(carril, pos, vel, lider)
        self.movidos = []
        t = self
        self.trafficlight = SimpleNamespace(getControlledLinks=lambda i: [[("L_0", "S_0", ":j_0_0")]],
                                            getRedYellowGreenState=lambda i: t.luz)
        self.salida_termina_red = True
        self.lane = SimpleNamespace(getLength=lambda c: 200.0,
                                    getLinks=lambda c: [] if (c == "S_0" and t.salida_termina_red) else ["x"],
                                    getLastStepVehicleIDs=lambda c: [v for v, d in t.vehiculos.items() if d["carril"] == c])
        self.vehicle = SimpleNamespace(getLanePosition=lambda v: t.vehiculos[v]["pos"],
                                       getSpeed=lambda v: t.vehiculos[v]["vel"],
                                       getLeader=lambda v, d: t.vehiculos[v]["lider"],
                                       getLaneID=lambda v: t.vehiculos[v]["carril"],
                                       getLength=lambda v: 12.0,
                                       moveTo=lambda v, c, p: t.movidos.append((v, c, p)))


def correr(traci, segundos):
    d = Desatascador(segundos_quieto=20, traci_mod=traci)
    return d, sum(d.paso(s) for s in range(segundos))


class TestDesatascador(unittest.TestCase):
    def test_vehiculo_trabado_en_verde_y_sin_nadie_adelante_se_traslada(self):
        t = TraciFalso()
        t.vehiculos["bus"] = dict(carril=":j_0_0", pos=0.1, vel=0.0, lider=None)
        d, n = correr(t, 25)
        self.assertEqual(n, 1)
        self.assertEqual(t.movidos, [("bus", "S_0", 15.0)])   # bus de 12 m + 3 m de margen: fuera del cruce
        self.assertEqual(d.eventos[0][1:], ("bus", ":j_0_0", "S_0"))

    def test_no_actua_antes_del_tiempo(self):
        t = TraciFalso()
        t.vehiculos["bus"] = dict(carril=":j_0_0", pos=0.1, vel=0.0, lider=None)
        _, n = correr(t, 19)
        self.assertEqual(n, 0)

    def test_no_actua_en_rojo(self):
        # esperar en rojo en la linea de pare es normal
        t = TraciFalso()
        t.luz = "r"
        t.vehiculos["carro"] = dict(carril="L_0", pos=199.0, vel=0.0, lider=None)
        _, n = correr(t, 60)
        self.assertEqual(n, 0)

    def test_no_actua_si_hay_alguien_adelante(self):
        # cola real: el de adelante tampoco avanza
        t = TraciFalso()
        t.vehiculos["carro"] = dict(carril="L_0", pos=199.0, vel=0.0, lider=("otro", 2.0))
        _, n = correr(t, 60)
        self.assertEqual(n, 0)

    def test_bloqueo_mutuo_lado_a_lado_se_resuelve(self):
        # carro y moto en la misma posicion, cada uno "ve" al otro como lider con distancia negativa (esta al lado)
        t = TraciFalso()
        t.vehiculos["carro"] = dict(carril="L_0", pos=200.0, vel=0.0, lider=("moto", -4.0))
        t.vehiculos["moto"] = dict(carril="L_0", pos=200.0, vel=0.0, lider=("carro", -2.0))
        _, n = correr(t, 20)
        self.assertEqual(n, 1)          # se adelanta uno; el otro queda libre y arranca solo

    def test_no_actua_lejos_de_la_linea_de_pare(self):
        t = TraciFalso()
        t.vehiculos["carro"] = dict(carril="L_0", pos=150.0, vel=0.0, lider=None)
        _, n = correr(t, 60)
        self.assertEqual(n, 0)

    def test_el_conteo_se_reinicia_si_se_mueve(self):
        t = TraciFalso()
        t.vehiculos["carro"] = dict(carril=":j_0_0", pos=0.1, vel=0.0, lider=None)
        d = Desatascador(segundos_quieto=20, traci_mod=t)
        for s in range(15):
            d.paso(s)
        t.vehiculos["carro"]["vel"] = 2.0      # arranco
        d.paso(15)
        t.vehiculos["carro"]["vel"] = 0.0
        self.assertEqual(sum(d.paso(s) for s in range(16, 30)), 0)   # solo 14 s seguidos

    def test_vehiculo_quieto_en_la_salida_libre_se_adelanta(self):
        # tramo de salida que termina la red: nada puede detener alli a un vehiculo
        t = TraciFalso()
        t.vehiculos["carro"] = dict(carril="S_0", pos=5.0, vel=0.0, lider=None)
        t.vehiculos["moto"] = dict(carril="S_0", pos=1.0, vel=0.0, lider=None)
        _, n = correr(t, 20)    # (el traci falso no mueve a nadie: en SUMO la moto arrancaria sola)
        self.assertEqual(n, 1)
        self.assertEqual(t.movidos, [("carro", "S_0", 20.0)])   # solo el de adelante: 5 + 12 + 3

    def test_salida_que_sigue_a_otra_via_no_se_toca(self):
        # si la salida conecta con otra via (ej. el brazo norte hacia el cruce), una cola alli es real
        t = TraciFalso()
        t.salida_termina_red = False
        t.vehiculos["carro"] = dict(carril="S_0", pos=5.0, vel=0.0, lider=None)
        _, n = correr(t, 60)
        self.assertEqual(n, 0)

    def test_no_permite_umbral_irreal(self):
        with self.assertRaises(ValueError):
            Desatascador(segundos_quieto=2, traci_mod=TraciFalso())


if __name__ == "__main__":
    unittest.main()
