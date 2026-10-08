"""Pruebas del controlador Q-Learning con una tabla hecha a mano (sin SUMO)."""
import unittest

from src.agent.codificador_estado import CodificadorEstado
from src.agent.qlearning import CAMBIAR, MANTENER, TablaQ
from src.controller.qlearning_controlador import ControladorQLearning
from src.controller.safety_guard import SafetyGuard
from tests.test_agente import CONFIG_AGENTE, CONFIG_INTERSECCION, estado_con_colas

ESTADO_VACIO = estado_con_colas(0.0, 0.0, 0.0, 0.0)


def preparar(visitado=True, accion_preferida=CAMBIAR):
    guard = SafetyGuard(10, 60, 3, 2, eje_inicial="dg15")
    codificador = CodificadorEstado(CONFIG_INTERSECCION, CONFIG_AGENTE)
    tabla = TablaQ(codificador.numero_estados, alfa=0.1, gamma=0.9)
    for estado in range(codificador.numero_estados):
        tabla.q[estado] = [-1.0, -1.0]
        tabla.q[estado][accion_preferida] = 0.0
        tabla.visitas[estado] = [5, 5] if visitado else [0, 0]
    control = ControladorQLearning(tabla, codificador, guard, intervalo_decision_s=5,
                                   verdes_respaldo_s={"cra23": 42, "dg15": 42})
    return guard, control


def correr(guard, control, segundos):
    fases = [guard.iniciar(0)]
    for t in range(1, segundos + 1):
        fases.append(guard.paso(t, control.pedir_cambio(t, ESTADO_VACIO)))
    return fases


class TestControladorQLearning(unittest.TestCase):
    def test_sigue_la_tabla_y_cambia_en_el_verde_minimo(self):
        guard, control = preparar(accion_preferida=CAMBIAR)
        correr(guard, control, 15)
        self.assertEqual(guard.historial_verdes[0], ("dg15", 0, 10))  # cambia apenas se permite
        self.assertEqual(control.decisiones_respaldo, 0)

    def test_mantener_decide_cada_intervalo_hasta_el_maximo(self):
        guard, control = preparar(accion_preferida=MANTENER)
        correr(guard, control, 61)
        self.assertEqual(guard.historial_verdes[0][2], 60)      # lo corta el verde maximo
        self.assertEqual(control.decisiones, 11)                 # t=10,15,...,60
        self.assertEqual(guard.cambios_forzados, 1)

    def test_estados_no_visitados_usan_el_plan_fijo(self):
        guard, control = preparar(visitado=False, accion_preferida=CAMBIAR)
        correr(guard, control, 50)
        self.assertEqual(guard.historial_verdes[0][2], 42)       # actua como tiempos fijos (42 s)
        self.assertEqual(control.decisiones_respaldo, control.decisiones)

    def test_tabla_de_otro_tamano_da_error(self):
        guard = SafetyGuard(10, 60, 3, 2)
        codificador = CodificadorEstado(CONFIG_INTERSECCION, CONFIG_AGENTE)
        with self.assertRaises(ValueError):
            ControladorQLearning(TablaQ(5, 0.1, 0.9), codificador, guard, 5, {"cra23": 42, "dg15": 42})


if __name__ == "__main__":
    unittest.main()
