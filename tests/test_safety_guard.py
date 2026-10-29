"""
Pruebas automaticas de la capa de seguridad y del controlador de tiempos fijos.
No necesitan SUMO.  Uso (desde la carpeta tesis):
    .\\.venv\\Scripts\\python.exe -m unittest discover -s tests -t . -v
"""
import unittest

from src.controller.safety_guard import SafetyGuard
from src.controller.tiempos_fijos import ControladorTiemposFijos

VERDE_MIN, VERDE_MAX, AMARILLO, TODO_ROJO = 10, 60, 3, 2


def nuevo_guard():
    return SafetyGuard(VERDE_MIN, VERDE_MAX, AMARILLO, TODO_ROJO, eje_inicial="dg15")


def simular(guard, segundos, decidir):
    """Ejecuta el guard segundo a segundo. decidir(t) -> bool. Devuelve la fase en cada segundo."""
    fases = [guard.iniciar(0)]
    for t in range(1, segundos + 1):
        fases.append(guard.paso(t, decidir(t)))
    return fases


def duraciones(fases):
    """Comprime la lista de fases en [(fase, segundos), ...]."""
    bloques = []
    for fase in fases:
        if bloques and bloques[-1][0] == fase:
            bloques[-1][1] += 1
        else:
            bloques.append([fase, 1])
    return [tuple(b) for b in bloques]


class TestSafetyGuard(unittest.TestCase):
    def test_verde_minimo_por_eje(self):
        # 2026-10-28: Cra 23 no puede terminar antes de 20 s; Dg 15 si a los 15 s -> ciclo minimo 20+3+0+15+3+20 = 61 s
        guard = SafetyGuard({"cra23": 20, "dg15": 15}, {"cra23": 70, "dg15": 25}, 3, {"cra23": 0, "dg15": 20},
                            eje_inicial="cra23")
        bloques = duraciones(simular(guard, 120, decidir=lambda t: True))   # pide cambiar siempre
        self.assertEqual(bloques[:6], [("verde_cra23", 20), ("amarillo_cra23", 3), ("verde_dg15", 15),
                                       ("amarillo_dg15", 3), ("todo_rojo", 20), ("verde_cra23", 20)])

    def test_verde_maximo_por_eje(self):
        # Iteracion 4b: Cra 23 hasta 70 s, Dg 15 hasta 25 s; nadie pide cambiar -> cada verde dura su maximo
        guard = SafetyGuard(15, {"cra23": 70, "dg15": 25}, 3, {"cra23": 0, "dg15": 20}, eje_inicial="dg15")
        bloques = duraciones(simular(guard, 200, decidir=lambda t: False))
        self.assertEqual(bloques[:4], [("verde_dg15", 25), ("amarillo_dg15", 3), ("todo_rojo", 20), ("verde_cra23", 70)])
        self.assertEqual(guard.verde_max("cra23"), 70)

    def test_verde_maximo_por_eje_incompleto_da_error(self):
        with self.assertRaises(ValueError):
            SafetyGuard(15, {"cra23": 70}, 3, 0)
        with self.assertRaises(ValueError):
            SafetyGuard(30, {"cra23": 70, "dg15": 25}, 3, 0)   # verde minimo mayor que un maximo

    def test_tiempos_fijos_validan_contra_el_maximo_de_su_eje(self):
        guard = SafetyGuard(15, {"cra23": 70, "dg15": 25}, 3, 0)
        ControladorTiemposFijos({"cra23": 55, "dg15": 20}, guard)          # el plan real cabe
        with self.assertRaises(ValueError):
            ControladorTiemposFijos({"cra23": 55, "dg15": 30}, guard)      # 30 s > 25 s de la Dg 15

    def test_no_cambia_antes_del_verde_minimo(self):
        guard = nuevo_guard()
        fases = simular(guard, 30, decidir=lambda t: True)  # el "controlador" pide cambiar SIEMPRE
        primer_bloque = duraciones(fases)[0]
        self.assertEqual(primer_bloque, ("verde_dg15", VERDE_MIN))
        self.assertGreater(guard.cambios_rechazados, 0)

    def test_fuerza_cambio_en_verde_maximo(self):
        guard = nuevo_guard()
        fases = simular(guard, 100, decidir=lambda t: False)  # nunca pide cambiar
        self.assertEqual(duraciones(fases)[0], ("verde_dg15", VERDE_MAX))
        self.assertEqual(guard.cambios_forzados, 1)

    def test_amarillo_y_todo_rojo_completos_entre_verdes(self):
        guard = nuevo_guard()
        fases = simular(guard, 400, decidir=lambda t: True)
        bloques = duraciones(fases)
        verdes = [i for i, (f, _) in enumerate(bloques) if f.startswith("verde")]
        for a, b in zip(verdes, verdes[1:]):
            eje_a = bloques[a][0].split("_")[1]
            self.assertEqual(bloques[a + 1], (f"amarillo_{eje_a}", AMARILLO))
            self.assertEqual(bloques[a + 2], ("todo_rojo", TODO_ROJO))
            self.assertEqual(b, a + 3)

    def test_nunca_dos_verdes_seguidos_ni_mismo_eje_repetido(self):
        guard = nuevo_guard()
        fases = simular(guard, 1000, decidir=lambda t: t % 7 == 0)  # peticiones "caoticas"
        verdes = [f for f, _ in duraciones(fases) if f.startswith("verde")]
        for actual, siguiente in zip(verdes, verdes[1:]):
            self.assertNotEqual(actual, siguiente, "el mismo eje recibio dos verdes seguidos")

    def test_todo_verde_respeta_limites(self):
        guard = nuevo_guard()
        simular(guard, 3000, decidir=lambda t: t % 13 == 0)
        for eje, inicio, duracion in guard.historial_verdes:
            self.assertGreaterEqual(duracion, VERDE_MIN, f"verde de {eje} en t={inicio}")
            self.assertLessEqual(duracion, VERDE_MAX, f"verde de {eje} en t={inicio}")

    def test_configuracion_invalida(self):
        with self.assertRaises(ValueError):
            SafetyGuard(verde_min_s=30, verde_max_s=20, amarillo_s=3, todo_rojo_s=2)
        with self.assertRaises(ValueError):
            SafetyGuard(verde_min_s=10, verde_max_s=60, amarillo_s=0, todo_rojo_s=2)
        with self.assertRaises(ValueError):
            SafetyGuard(verde_min_s=10, verde_max_s=60, amarillo_s=3, todo_rojo_s=2, eje_inicial="x")

    def test_todo_rojo_distinto_segun_el_eje(self):
        # Como el cruce real: tras el verde de la Cra 23 casi no hay todo-rojo; tras la Dg 15, ~20 s
        guard = SafetyGuard(10, 60, 3, {"cra23": 0, "dg15": 20}, eje_inicial="cra23")
        control = ControladorTiemposFijos({"cra23": 55, "dg15": 20}, guard)
        fases = simular(guard, 2 * 101, decidir=lambda t: control.pedir_cambio(t))
        self.assertEqual(
            duraciones(fases)[:5],
            [("verde_cra23", 55), ("amarillo_cra23", 3), ("verde_dg15", 20),
             ("amarillo_dg15", 3), ("todo_rojo", 20)],
        )
        with self.assertRaises(ValueError):
            SafetyGuard(10, 60, 3, {"cra23": 0})          # falta un eje
        with self.assertRaises(ValueError):
            SafetyGuard(10, 60, 3, {"cra23": -1, "dg15": 20})

    def test_paso_sin_iniciar_da_error(self):
        with self.assertRaises(RuntimeError):
            nuevo_guard().paso(1, False)


class TestPerfilesDeSeguridad(unittest.TestCase):
    CONFIG = {"seguridad": {"verde_min_s": 15, "verde_max_s": 60, "amarillo_s": 3,
                            "todo_rojo_s": {"cra23": 0, "dg15": 20}, "eje_inicial": "cra23"},
              "seguridad_norma": {"todo_rojo_s": {"cra23": 2, "dg15": 20}}}

    def todo_rojo_tras_cra23(self, guard):
        # Arranca en verde Cra 23 y pide cambiar siempre: verde minimo (15 s), amarillo (3 s) y luego el todo-rojo.
        bloques = duraciones(simular(guard, 25, lambda t: True))
        siguiente = bloques[2]  # (fase despues del amarillo, segundos)
        return siguiente[1] if siguiente[0] == "todo_rojo" else 0

    def test_perfil_real_usa_el_todo_rojo_medido(self):
        guard = SafetyGuard.desde_config(self.CONFIG, "real")
        self.assertEqual(guard.verde_min("cra23"), 15)
        self.assertEqual(self.todo_rojo_tras_cra23(guard), 0)

    def test_perfil_norma_cambia_solo_el_todo_rojo(self):
        real = SafetyGuard.desde_config(self.CONFIG, "real")
        norma = SafetyGuard.desde_config(self.CONFIG, "norma")
        self.assertEqual((norma.verde_min_por_eje, norma.verde_max_por_eje), (real.verde_min_por_eje, real.verde_max_por_eje))
        self.assertEqual(self.todo_rojo_tras_cra23(norma), 2)

    def test_perfil_desconocido_da_error(self):
        with self.assertRaises(ValueError):
            SafetyGuard.desde_config(self.CONFIG, "otro")


class TestTiemposFijos(unittest.TestCase):
    def test_ciclo_exacto(self):
        guard = nuevo_guard()
        control = ControladorTiemposFijos({"cra23": 20, "dg15": 40}, guard)
        fases = simular(guard, 2 * (40 + 3 + 2 + 20 + 3 + 2), decidir=lambda t: control.pedir_cambio(t))
        self.assertEqual(
            duraciones(fases)[:6],
            [("verde_dg15", 40), ("amarillo_dg15", 3), ("todo_rojo", 2),
             ("verde_cra23", 20), ("amarillo_cra23", 3), ("todo_rojo", 2)],
        )
        self.assertEqual(guard.cambios_forzados, 0)
        self.assertEqual(guard.cambios_rechazados, 0)

    def test_rechaza_verde_fuera_de_limites(self):
        with self.assertRaises(ValueError):
            ControladorTiemposFijos({"cra23": 5, "dg15": 40}, nuevo_guard())
        with self.assertRaises(ValueError):
            ControladorTiemposFijos({"cra23": 20, "dg15": 90}, nuevo_guard())


if __name__ == "__main__":
    unittest.main()
