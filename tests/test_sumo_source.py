"""Pruebas de SumoSource con un 'traci' falso (no necesitan abrir SUMO).

Comprueban que un brazo medido sobre VARIOS tramos suma vehiculos, detenidos y capacidad de todos ellos.
"""
import unittest
from types import SimpleNamespace
from unittest import mock

from src.simulation import sumo_source

LARGOS = {"a_0": 60.0, "a_1": 60.0, "b_0": 60.0, "c_0": 75.0}       # largo de cada carril (m)
CARRILES = {"a": 2, "b": 1, "c": 1, "d": 1}
VEHICULOS = {"a": 5, "b": 3, "c": 2, "d": 9}
DETENIDOS = {"a": 4, "b": 2, "c": 1, "d": 7}  # "d" = tramo aguas arriba del norte
# Vehiculos individuales (para la zona de camara): tramo -> [(posicion en el carril, velocidad)]
# Brazo norte = a (60 m de largo, pegado a la linea de pare) + b (60 m, antes de a).
POSICIONES = {"a": [(55.0, 0.0), (10.0, 0.0), (5.0, 8.0)],   # a 5 m, 50 m y 55 m del pare
              "b": [(40.0, 0.0), (5.0, 0.0)],                # a 60+20 = 80 m y 60+55 = 115 m del pare
              "c": [(70.0, 0.0)]}


def traci_falso():
    vehiculos = {f"{e}.{i}": datos for e, lista in POSICIONES.items() for i, datos in enumerate(lista)}
    return SimpleNamespace(
        edge=SimpleNamespace(getIDList=lambda: list(CARRILES), getLaneNumber=lambda e: CARRILES[e],
                             getLastStepHaltingNumber=lambda e: DETENIDOS[e],
                             getLastStepVehicleNumber=lambda e: VEHICULOS[e],
                             getLastStepVehicleIDs=lambda e: [v for v in vehiculos if v.startswith(f"{e}.")]),
        lane=SimpleNamespace(getLength=lambda carril: LARGOS[carril]),
        vehicle=SimpleNamespace(getLanePosition=lambda v: vehiculos[v][0], getSpeed=lambda v: vehiculos[v][1]),
        simulation=SimpleNamespace(getTime=lambda: 42.0),
    )


CONFIG = {"espacio_por_vehiculo_m": 7.5, "zona_camara_m": 100,
          "brazos": {"norte": {"edges": ["a", "b"], "eje": "cra23"}, "sur": {"edges": ["c"], "eje": "cra23"}}}


class TestSumoSource(unittest.TestCase):
    def test_brazo_con_varios_tramos_suma_todo(self):
        with mock.patch.object(sumo_source, "traci", traci_falso()):
            fuente = sumo_source.SumoSource(CONFIG)
            estado = fuente.leer_estado()
        # capacidad norte = (60 + 60 + 60) m / 7.5 m = 24 vehiculos; sur = 75 / 7.5 = 10
        self.assertAlmostEqual(fuente.capacidad["norte"], 24.0)
        self.assertAlmostEqual(fuente.capacidad["sur"], 10.0)
        self.assertEqual(estado.brazos["norte"].vehiculos, 8)
        self.assertEqual(estado.brazos["norte"].detenidos, 6)
        self.assertAlmostEqual(estado.brazos["norte"].cola_relativa, 6 / 24)
        self.assertEqual(estado.brazos["sur"].detenidos, 1)
        self.assertEqual(estado.tiempo, 42.0)

    def test_zona_de_camara_cuenta_solo_los_ultimos_metros(self):
        with mock.patch.object(sumo_source, "traci", traci_falso()):
            estado = sumo_source.SumoSource(CONFIG).leer_estado()
        # norte: dentro de 100 m estan los de 5, 50, 55 (este en movimiento) y 80 m; el de 115 m queda fuera
        self.assertEqual(estado.brazos["norte"].vehiculos_zona, 4)
        self.assertEqual(estado.brazos["norte"].detenidos_zona, 3)
        # sur: un vehiculo detenido a 75 - 70 = 5 m del pare
        self.assertEqual(estado.brazos["sur"].detenidos_zona, 1)

    def test_aguas_arriba_se_cuenta_aparte(self):
        config = {"espacio_por_vehiculo_m": 7.5, "zona_camara_m": 100,
                  "brazos": {"norte": {"edges": ["a", "b"], "eje": "cra23", "edges_aguas_arriba": ["d"]},
                             "sur": {"edges": ["c"], "eje": "cra23"}}}
        with mock.patch.object(sumo_source, "traci", traci_falso()):
            estado = sumo_source.SumoSource(config).leer_estado()
        self.assertEqual(estado.brazos["norte"].detenidos, 6)               # el brazo no cambia
        self.assertEqual(estado.brazos["norte"].detenidos_aguas_arriba, 7)  # la cola de afuera, aparte
        self.assertEqual(estado.brazos["sur"].detenidos_aguas_arriba, 0)    # sin tramos aguas arriba

    def test_sin_zona_deja_none_y_mantiene_el_brazo_completo(self):
        with mock.patch.object(sumo_source, "traci", traci_falso()):
            estado = sumo_source.SumoSource(CONFIG).leer_estado(incluir_zona=False)
        self.assertIsNone(estado.brazos["norte"].detenidos_zona)
        self.assertEqual(estado.brazos["norte"].detenidos, 6)

    def test_tramo_inexistente_da_error_claro(self):
        config = {"espacio_por_vehiculo_m": 7.5, "zona_camara_m": 100, "brazos": {"norte": {"edges": ["a", "no_existe"], "eje": "cra23"}}}
        with mock.patch.object(sumo_source, "traci", traci_falso()):
            with self.assertRaisesRegex(ValueError, "no_existe"):
                sumo_source.SumoSource(config)


if __name__ == "__main__":
    unittest.main()
