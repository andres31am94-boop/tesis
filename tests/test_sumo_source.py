"""Pruebas de SumoSource con un 'traci' falso (no necesitan abrir SUMO).

Comprueban que un brazo medido sobre VARIOS tramos suma vehiculos, detenidos y capacidad de todos ellos.
"""
import unittest
from types import SimpleNamespace
from unittest import mock

from src.simulation import sumo_source

LARGOS = {"a_0": 30.0, "a_1": 30.0, "b_0": 60.0, "c_0": 75.0}       # largo de cada carril (m)
CARRILES = {"a": 2, "b": 1, "c": 1}
VEHICULOS = {"a": 5, "b": 3, "c": 2}
DETENIDOS = {"a": 4, "b": 2, "c": 1}


def traci_falso():
    return SimpleNamespace(
        edge=SimpleNamespace(getIDList=lambda: list(CARRILES), getLaneNumber=lambda e: CARRILES[e],
                             getLastStepHaltingNumber=lambda e: DETENIDOS[e],
                             getLastStepVehicleNumber=lambda e: VEHICULOS[e]),
        lane=SimpleNamespace(getLength=lambda carril: LARGOS[carril]),
        simulation=SimpleNamespace(getTime=lambda: 42.0),
    )


CONFIG = {"espacio_por_vehiculo_m": 7.5,
          "brazos": {"norte": {"edges": ["a", "b"], "eje": "cra23"}, "sur": {"edges": ["c"], "eje": "cra23"}}}


class TestSumoSource(unittest.TestCase):
    def test_brazo_con_varios_tramos_suma_todo(self):
        with mock.patch.object(sumo_source, "traci", traci_falso()):
            fuente = sumo_source.SumoSource(CONFIG)
            estado = fuente.leer_estado()
        # capacidad norte = (30 + 30 + 60) m / 7.5 m = 16 vehiculos; sur = 75 / 7.5 = 10
        self.assertAlmostEqual(fuente.capacidad["norte"], 16.0)
        self.assertAlmostEqual(fuente.capacidad["sur"], 10.0)
        self.assertEqual(estado.brazos["norte"].vehiculos, 8)
        self.assertEqual(estado.brazos["norte"].detenidos, 6)
        self.assertAlmostEqual(estado.brazos["norte"].cola_relativa, 6 / 16)
        self.assertEqual(estado.brazos["sur"].detenidos, 1)
        self.assertEqual(estado.tiempo, 42.0)

    def test_tramo_inexistente_da_error_claro(self):
        config = {"espacio_por_vehiculo_m": 7.5, "brazos": {"norte": {"edges": ["a", "no_existe"], "eje": "cra23"}}}
        with mock.patch.object(sumo_source, "traci", traci_falso()):
            with self.assertRaisesRegex(ValueError, "no_existe"):
                sumo_source.SumoSource(config)


if __name__ == "__main__":
    unittest.main()
