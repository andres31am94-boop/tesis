"""
Controlador Q-LEARNING: usa la tabla Q YA ENTRENADA para decidir (sin seguir aprendiendo).

- Decide en los mismos momentos que durante el entrenamiento: al cumplirse el verde minimo
  y luego cada intervalo_decision_s mientras dure el verde.
- Siempre elige la mejor accion de la tabla (epsilon = 0): la tabla esta congelada.
- RESPALDO: si el estado actual nunca fue visitado en el entrenamiento (0 visitas),
  la tabla no sabe nada de el; en ese caso actua como el plan de tiempos fijos
  y se cuenta en decisiones_respaldo.
- Igual que el baseline, solo PIDE cambiar: el SafetyGuard tiene la ultima palabra.
"""
from src.agent.qlearning import CAMBIAR
from src.controller.safety_guard import VERDE
from src.controller.tiempos_fijos import ControladorTiemposFijos


class ControladorQLearning:
    nombre = "qlearning"

    def __init__(self, tabla, codificador, guard, intervalo_decision_s, verdes_respaldo_s):
        if tabla.numero_estados != codificador.numero_estados:
            raise ValueError(
                f"La tabla tiene {tabla.numero_estados} estados pero el codificador define "
                f"{codificador.numero_estados}: la tabla se entreno con otra configuracion."
            )
        self._tabla = tabla
        self._codificador = codificador
        self._guard = guard
        self._intervalo = intervalo_decision_s
        self._respaldo = ControladorTiemposFijos(verdes_respaldo_s, guard)
        self._ultima_decision = None
        self._en_respaldo = False   # True si la ultima decision de ESTE verde uso el plan fijo
        self.decisiones = 0
        self.decisiones_respaldo = 0
        self.pedidos_de_cambio = 0

    def _toca_decidir(self, tiempo):
        tiempo_en_verde = self._guard.tiempo_en_etapa(tiempo)
        if tiempo_en_verde < self._guard.verde_min_s:
            return False
        inicio_verde = tiempo - tiempo_en_verde
        primera_de_este_verde = self._ultima_decision is None or self._ultima_decision < inicio_verde
        return primera_de_este_verde or tiempo - self._ultima_decision >= self._intervalo

    def pedir_cambio(self, tiempo, estado_trafico):
        if self._guard.etapa != VERDE:
            self._en_respaldo = False
            return False
        if not self._toca_decidir(tiempo):
            # Entre decisiones: si estamos en respaldo, el plan fijo se revisa CADA segundo
            # (si no, un verde fijo de 42 s terminaria en la siguiente decision, a los 45 s).
            return self._en_respaldo and self._respaldo.pedir_cambio(tiempo)
        self._ultima_decision = tiempo
        self.decisiones += 1

        estado = self._codificador.codificar(estado_trafico, self._guard.eje, self._guard.tiempo_en_etapa(tiempo))
        if sum(self._tabla.visitas[estado]) == 0:
            self.decisiones_respaldo += 1
            self._en_respaldo = True
            return self._respaldo.pedir_cambio(tiempo)
        self._en_respaldo = False

        cambiar = self._tabla.mejor_accion(estado) == CAMBIAR
        self.pedidos_de_cambio += cambiar
        return cambiar
