"""Pruebas del desfase del semaforo de la Calle 18 (sin SUMO)."""
import unittest

from src.simulation.semaforo_calle18 import fase_para_desfase

FASES = [58, 3, 41]  # verde, amarillo, rojo medidos (ciclo 102 s)


class TestDesfase(unittest.TestCase):
    def test_inicio_de_ciclo(self):
        self.assertEqual(fase_para_desfase(FASES, 0), (0, 58))

    def test_dentro_de_cada_fase(self):
        self.assertEqual(fase_para_desfase(FASES, 57), (0, 1))
        self.assertEqual(fase_para_desfase(FASES, 58), (1, 3))
        self.assertEqual(fase_para_desfase(FASES, 60), (1, 1))
        self.assertEqual(fase_para_desfase(FASES, 61), (2, 41))
        self.assertEqual(fase_para_desfase(FASES, 101), (2, 1))

    def test_desfase_mayor_que_el_ciclo_da_la_vuelta(self):
        self.assertEqual(fase_para_desfase(FASES, 102 + 60), (1, 1))


if __name__ == "__main__":
    unittest.main()
