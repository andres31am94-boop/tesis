"""Pruebas del codificador de estado y de la tabla Q (sin SUMO)."""
import itertools
import tempfile
import unittest
from pathlib import Path

from src.agent.codificador_estado import CodificadorEstado, nivel
from src.agent.qlearning import CAMBIAR, MANTENER, TablaQ, epsilon_lineal, suma_descontada
from src.common.estado import EstadoBrazo, EstadoTrafico

CONFIG_INTERSECCION = {"brazos": {
    "norte": {"edges": ["n"], "eje": "cra23"}, "sur": {"edges": ["s"], "eje": "cra23"},
    "este": {"edges": ["e"], "eje": "dg15"}, "oeste": {"edges": ["o"], "eje": "dg15"},
}}
CONFIG_AGENTE = {"estado": {"cortes_detenidos_zona": [2, 6, 12], "cortes_tiempo_verde_s": [20, 40]}}


def estado_con_colas(norte, sur, este, oeste):
    """Estado con esos vehiculos detenidos en la zona de camara de cada brazo."""
    brazos = {n: EstadoBrazo(vehiculos=c, detenidos=c, cola_relativa=0.0, vehiculos_zona=c, detenidos_zona=c)
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
        # norte con 15 detenidos y sur vacio: el eje Cra 23 debe verse "alto" (nivel 3); Dg 15 max(1, 4) = 4 -> "baja"
        componentes = self.cod.componentes(estado_con_colas(15, 0, 1, 4), "dg15", 12)
        self.assertEqual(componentes, (3, 1, 1, 0))

    def test_indices_unicos_y_en_rango(self):
        indices = {self.cod.indice(c) for c in itertools.product(range(4), range(4), range(2), range(3))}
        self.assertEqual(indices, set(range(self.cod.numero_estados)))

    def test_describir_es_inverso_del_indice(self):
        indice = self.cod.indice((3, 0, 0, 2))
        self.assertEqual(self.cod.describir(indice),
                         "cola Cra23=alta, cola Dg15=vacia, verde=cra23, tiempo_verde=nivel 2")

    def test_cortes_desordenados_dan_error(self):
        malo = {"estado": {"cortes_detenidos_zona": [6, 2], "cortes_tiempo_verde_s": [20, 40]}}
        with self.assertRaises(ValueError):
            CodificadorEstado(CONFIG_INTERSECCION, malo)


class TestCodificadorPresentesEnVerde(unittest.TestCase):
    """Iteracion 2: el eje en verde se describe con los vehiculos presentes; el eje en rojo, con los detenidos."""
    CONFIG = {"estado": {"cortes_detenidos_zona": [1, 4, 9], "modo": "presentes_en_verde",
                         "cortes_presentes_zona_verde": [1, 5, 10], "cortes_tiempo_verde_s": [20, 40]}}

    def estado(self, presentes, detenidos):
        brazos = {n: EstadoBrazo(vehiculos=0, detenidos=0, cola_relativa=0.0,
                                 vehiculos_zona=presentes[n], detenidos_zona=detenidos[n])
                  for n in ["norte", "sur", "este", "oeste"]}
        return EstadoTrafico(tiempo=0, brazos=brazos)

    def test_eje_en_verde_usa_presentes_y_el_rojo_usa_detenidos(self):
        cod = CodificadorEstado(CONFIG_INTERSECCION, self.CONFIG)
        # Cra 23 en verde: 12 vehiculos moviendose en el norte pero 0 detenidos -> nivel "alta" (antes se veia "vacia")
        estado = self.estado(presentes={"norte": 12, "sur": 3, "este": 2, "oeste": 0},
                             detenidos={"norte": 0, "sur": 0, "este": 2, "oeste": 0})
        self.assertEqual(cod.componentes(estado, "cra23", 25), (3, 1, 0, 1))
        # La misma situacion con la Dg 15 en verde: la Cra 23 (en rojo) se mide por detenidos -> "vacia"
        self.assertEqual(cod.componentes(estado, "dg15", 25), (0, 1, 1, 1))

    def test_modo_desconocido_da_error(self):
        malo = {"estado": {**self.CONFIG["estado"], "modo": "otro"}}
        with self.assertRaises(ValueError):
            CodificadorEstado(CONFIG_INTERSECCION, malo)


class TestCortesDeTiempoPorEje(unittest.TestCase):
    """Iteracion 4b: niveles de tiempo alineados con el plan real (Cra 23 55 s, Dg 15 20 s)."""
    def setUp(self):
        config = {"estado": {"cortes_detenidos_zona": [2, 6, 12],
                             "cortes_tiempo_verde_s": {"cra23": [45, 55], "dg15": [20, 30]}}}
        self.cod = CodificadorEstado(CONFIG_INTERSECCION, config)

    def test_mismo_numero_de_estados(self):
        self.assertEqual(self.cod.numero_estados, 96)

    def test_niveles_distintos_por_eje(self):
        e = estado_con_colas(0, 0, 0, 0)
        self.assertEqual(self.cod.componentes(e, "cra23", 50)[3], 1)
        self.assertEqual(self.cod.componentes(e, "cra23", 55)[3], 2)
        self.assertEqual(self.cod.componentes(e, "dg15", 15)[3], 0)
        self.assertEqual(self.cod.componentes(e, "dg15", 20)[3], 1)

    def test_accion_plan_reproduce_55_20(self):
        e = estado_con_colas(3, 3, 3, 3)
        plan = {"cra23": 55, "dg15": 20}
        for eje, tiempo, esperado in [("cra23", 15, MANTENER), ("cra23", 50, MANTENER), ("cra23", 55, CAMBIAR),
                                      ("dg15", 15, MANTENER), ("dg15", 20, CAMBIAR)]:
            self.assertEqual(self.cod.accion_plan(self.cod.codificar(e, eje, tiempo), plan), esperado, (eje, tiempo))

    def test_niveles_distintos_en_numero_dan_error(self):
        malo = {"estado": {"cortes_detenidos_zona": [2, 6, 12], "cortes_tiempo_verde_s": {"cra23": [45, 55], "dg15": [20]}}}
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

    def test_reiniciar_azar_repite_las_mismas_decisiones(self):
        # Base de entrenar por paquetes: con la misma semilla del episodio, las decisiones al azar se repiten.
        tabla = TablaQ(numero_estados=1, alfa=0.1, gamma=0.9)
        tabla.reiniciar_azar(1005)
        primera = [tabla.elegir_accion(0, epsilon=0.5) for _ in range(100)]
        tabla.reiniciar_azar(1005)
        segunda = [tabla.elegir_accion(0, epsilon=0.5) for _ in range(100)]
        self.assertEqual(primera, segunda)

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

    def test_descuento_por_segundo(self):
        # Iteracion 4b: el futuro pesa gamma^(segundos del paso); por decision, gamma sin importar la duracion
        por_segundo = TablaQ(numero_estados=2, alfa=1.0, gamma=0.99, descuento="por_segundo")
        por_decision = TablaQ(numero_estados=2, alfa=1.0, gamma=0.99)
        for tabla in (por_segundo, por_decision):
            tabla.q[1] = [-100.0, -200.0]
            tabla.actualizar(0, CAMBIAR, -10, 1, terminal=False, segundos=38)
        self.assertAlmostEqual(por_segundo.q[0][CAMBIAR], -10 + 0.99 ** 38 * -100)
        self.assertAlmostEqual(por_decision.q[0][CAMBIAR], -10 + 0.99 * -100)
        with self.assertRaises(ValueError):
            por_segundo.actualizar(0, CAMBIAR, -10, 1, terminal=False, segundos=0)

    def test_suma_descontada(self):
        self.assertAlmostEqual(suma_descontada([4, 4, 4], 0.5), 4 + 2 + 1)
        self.assertAlmostEqual(suma_descontada([7], 0.9), 7)
        # 5 pasos de 1 s descontados = 1 paso de 5 s descontado (coherencia de la formulacion semi-Markov)
        valores = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
        g = 0.99
        self.assertAlmostEqual(suma_descontada(valores, g),
                               suma_descontada(valores[:5], g) + g ** 5 * suma_descontada(valores[5:], g))

    def test_guardar_y_cargar_conserva_el_descuento(self):
        tabla = TablaQ(numero_estados=1, alfa=0.1, gamma=0.99, descuento="por_segundo")
        ruta = Path(tempfile.mkdtemp()) / "tabla.json"
        tabla.guardar(ruta)
        self.assertEqual(TablaQ.cargar(ruta).descuento, "por_segundo")

    def test_actualizar_con_accion_siguiente_del_plan(self):
        # en la fase plan el futuro es Q(s', accion del plan), no el maximo (la otra accion vale 0 sin probarse)
        tabla = TablaQ(numero_estados=2, alfa=1.0, gamma=0.5)
        tabla.q[1] = [-40.0, 0.0]          # plan en s' = mantener (-40); cambiar nunca probado (0)
        tabla.actualizar(0, MANTENER, -10, 1, terminal=False, accion_siguiente=MANTENER)
        self.assertAlmostEqual(tabla.q[0][MANTENER], -10 + 0.5 * -40)
        tabla.actualizar(0, CAMBIAR, -10, 1, terminal=False)               # sin accion_siguiente: max = 0
        self.assertAlmostEqual(tabla.q[0][CAMBIAR], -10)

    def test_iniciar_desde_plan(self):
        tabla = TablaQ(numero_estados=3, alfa=0.1, gamma=0.99)
        tabla.q[0] = [-100.0, 0.0]          # plan = mantener, visitado en la fase plan
        tabla.visitas[0] = [5, 0]
        tabla.q[1] = [0.0, -50.0]           # plan = cambiar, visitado
        tabla.visitas[1] = [0, 3]
        tabla.iniciar_desde_plan([MANTENER, CAMBIAR, CAMBIAR], margen=0.01)
        self.assertLess(tabla.q[0][CAMBIAR], tabla.q[0][MANTENER])
        self.assertAlmostEqual(tabla.q[0][CAMBIAR], -101.0, places=6)
        self.assertLess(tabla.q[1][MANTENER], tabla.q[1][CAMBIAR])
        self.assertEqual(tabla.q[2], [-1.0, 0.0])   # nunca visitado: desempate a favor del plan (cambiar)
        self.assertEqual([tabla.mejor_accion(s) for s in range(3)], [MANTENER, CAMBIAR, CAMBIAR])

    def test_parametros_invalidos(self):
        with self.assertRaises(ValueError):
            TablaQ(numero_estados=1, alfa=0.1, gamma=0.9, descuento="por_minuto")
        with self.assertRaises(ValueError):
            TablaQ(numero_estados=1, alfa=0, gamma=0.9)
        with self.assertRaises(ValueError):
            TablaQ(numero_estados=1, alfa=0.1, gamma=1.0)


if __name__ == "__main__":
    unittest.main()
