"""Pruebas del codificador de estado y de la tabla Q (sin SUMO)."""
import itertools
import tempfile
import unittest
from pathlib import Path

from src.agent.codificador_estado import CodificadorEstado, nivel
from src.agent.qlearning import CAMBIAR, MANTENER, TablaQ, epsilon_lineal
from src.common.estado import EstadoBrazo, EstadoTrafico

CONFIG_INTERSECCION = {"brazos": {
    "norte": {"edge": "n", "eje": "cra23"}, "sur": {"edge": "s", "eje": "cra23"},
    "este": {"edge": "e", "eje": "dg15"}, "oeste": {"edge": "o", "eje": "dg15"},
}}
CONFIG_AGENTE = {"estado": {"cortes_cola_relativa": [0.1, 0.3, 0.6], "cortes_tiempo_verde_s": [20, 40]}}


def estado_con_colas(norte, sur, este, oeste):
    brazos = {n: EstadoBrazo(vehiculos=0, detenidos=0, cola_relativa=c)
              for n, c in zip(["norte", "sur", "este", "oeste"], [norte, sur, este, oeste])}
    return EstadoTrafico(tiempo=0, brazos=brazos)


class TestCodificador(unittest.TestCase):
    def setUp(self):
        self.cod = CodificadorEstado(CONFIG_INTERSECCION, CONFIG_AGENTE)

    def test_niveles_en_los_bordes(self):
        cortes = [0.1, 0.3, 0.6]
        self.assertEqual([nivel(v, cortes) for v in (0.0, 0.0999, 0.1, 0.3, 0.59, 0.6, 2.0)],
                         [0, 0, 1, 2, 2, 3, 3])

    def test_numero_de_estados(self):
        self.assertEqual(self.cod.numero_estados, 4 * 4 * 2 * 3)

    def test_usa_el_brazo_mas_cargado(self):
        # norte casi lleno (0.9) y sur vacio: el eje Cra 23 debe verse "alto" (nivel 3)
        componentes = self.cod.componentes(estado_con_colas(0.9, 0.0, 0.05, 0.2), "dg15", 12)
        self.assertEqual(componentes, (3, 1, 1, 0))

    def test_indices_unicos_y_en_rango(self):
        indices = {self.cod.indice(c) for c in itertools.product(range(4), range(4), range(2), range(3))}
        self.assertEqual(indices, set(range(self.cod.numero_estados)))

    def test_describir_es_inverso_del_indice(self):
        indice = self.cod.indice((3, 0, 0, 2))
        self.assertEqual(self.cod.describir(indice),
                         "cola Cra23=alta, cola Dg15=vacia, verde=cra23, tiempo_verde=nivel 2")

    def test_cortes_desordenados_dan_error(self):
        malo = {"estado": {"cortes_cola_relativa": [0.6, 0.1], "cortes_tiempo_verde_s": [20, 40]}}
        with self.assertRaises(ValueError):
            CodificadorEstado(CONFIG_INTERSECCION, malo)


class TestTablaQ(unittest.TestCase):
    def test_actualizacion_q_learning(self):
        tabla = TablaQ(numero_estados=3, alfa=0.1, gamma=0.9)
        tabla.actualizar(0, CAMBIAR, -10, 1, terminal=False)        # 0 + 0.1*(-10 + 0.9*0 - 0)
        self.assertAlmostEqual(tabla.q[0][CAMBIAR], -1.0)
        tabla.q[1] = [-2.0, -5.0]                                    # max Q(s'=1) = -2
        tabla.actualizar(0, CAMBIAR, -10, 1, terminal=False)        # -1 + 0.1*(-10 + 0.9*-2 - (-1))
        self.assertAlmostEqual(tabla.q[0][CAMBIAR], -1 + 0.1 * (-10 - 1.8 + 1))
        tabla.actualizar(2, MANTENER, -4, 1, terminal=True)         # terminal: sin futuro
        self.assertAlmostEqual(tabla.q[2][MANTENER], -0.4)
        self.assertEqual(tabla.visitas[0][CAMBIAR], 2)

    def test_sin_exploracion_elige_la_mejor(self):
        tabla = TablaQ(numero_estados=1, alfa=0.1, gamma=0.9)
        tabla.q[0] = [-3.0, -1.0]
        self.assertTrue(all(tabla.elegir_accion(0, epsilon=0.0) == CAMBIAR for _ in range(50)))

    def test_exploracion_total_usa_ambas_acciones(self):
        tabla = TablaQ(numero_estados=1, alfa=0.1, gamma=0.9, semilla=1)
        tabla.q[0] = [-3.0, -1.0]
        self.assertEqual({tabla.elegir_accion(0, epsilon=1.0) for _ in range(200)}, {MANTENER, CAMBIAR})

    def test_guardar_y_cargar(self):
        tabla = TablaQ(numero_estados=2, alfa=0.2, gamma=0.8)
        tabla.q[1] = [-1.5, -0.5]
        ruta = Path(tempfile.mkdtemp()) / "tabla.json"
        tabla.guardar(ruta, {"nota": "prueba"})
        copia = TablaQ.cargar(ruta)
        self.assertEqual(copia.q, tabla.q)
        self.assertEqual((copia.alfa, copia.gamma), (0.2, 0.8))
        self.assertEqual(copia.metadatos["nota"], "prueba")

    def test_epsilon_lineal(self):
        self.assertAlmostEqual(epsilon_lineal(0, 1.0, 0.05, 150), 1.0)
        self.assertAlmostEqual(epsilon_lineal(75, 1.0, 0.05, 150), 0.525)
        self.assertAlmostEqual(epsilon_lineal(500, 1.0, 0.05, 150), 0.05)

    def test_parametros_invalidos(self):
        with self.assertRaises(ValueError):
            TablaQ(numero_estados=1, alfa=0, gamma=0.9)
        with self.assertRaises(ValueError):
            TablaQ(numero_estados=1, alfa=0.1, gamma=1.0)


if __name__ == "__main__":
    unittest.main()
