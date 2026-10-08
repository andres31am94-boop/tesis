"""
Entorno de entrenamiento: el "juego" en el que practica el agente.

    estado = entorno.reset(semilla)            # empieza un dia nuevo de trafico
    while not terminado:
        accion = agente.elegir(estado)         # 0 mantener / 1 cambiar
        estado, recompensa, terminado, info = entorno.step(accion)

Cuando decide el agente: solo durante un verde, y solo despues del verde minimo
(antes de eso el SafetyGuard no permitiria cambiar). Durante amarillo y todo-rojo
la simulacion avanza sola.

Recompensa de cada paso: -(suma de vehiculos detenidos en los 4 brazos, segundo a
segundo, durante todo el paso). Si el paso incluye una transicion (amarillo + todo-rojo
+ verde minimo del otro eje), esos segundos tambien cuentan: son consecuencia de cambiar.
"""
import traci

from src.agent.codificador_estado import CodificadorEstado
from src.agent.qlearning import CAMBIAR
from src.controller.safety_guard import VERDE, SafetyGuard
from src.simulation.sesion_sumo import iniciar_sumo
from src.simulation.sumo_actuator import SumoActuator
from src.simulation.sumo_source import SumoSource


class EntornoSumo:
    def __init__(self, archivo_escenario, config_interseccion, config_controlador, config_agente,
                 config_experimento, usar_gui=False):
        self._archivo = archivo_escenario
        self._config_interseccion = config_interseccion
        self._config_controlador = config_controlador
        self._intervalo = int(config_agente["intervalo_decision_s"])
        self._fin_episodio = float(config_experimento["duracion_demanda_s"])
        self._usar_gui = usar_gui
        self.codificador = CodificadorEstado(config_interseccion, config_agente)
        self._abierto = False

    # --- interfaz del entorno ----------------------------------------------------
    def reset(self, semilla):
        self.close()
        iniciar_sumo(self._archivo, usar_gui=self._usar_gui, semilla=semilla)
        self._abierto = True
        self._fuente = SumoSource(self._config_interseccion)
        self._actuador = SumoActuator(self._config_interseccion)
        self.guard = SafetyGuard.desde_config(self._config_controlador)
        self._tiempo = traci.simulation.getTime()
        self._fase = self.guard.iniciar(self._tiempo)
        self._actuador.aplicar(self._fase)
        self._estado_trafico = self._fuente.leer_estado()

        detenidos, _ = self._avanzar_hasta_decision(pedir_cambio=False)
        self.detenidos_episodio = detenidos
        self.segundos_episodio = 0
        return self._estado_actual()

    def step(self, accion):
        if not self._abierto:
            raise RuntimeError("Llama a reset() antes de step().")
        detenidos, segundos = self._avanzar_hasta_decision(pedir_cambio=(accion == CAMBIAR))
        self.detenidos_episodio += detenidos
        self.segundos_episodio += segundos
        terminado = self._tiempo >= self._fin_episodio
        info = {"tiempo": self._tiempo, "segundos": segundos, "detenidos": detenidos}
        return self._estado_actual(), -float(detenidos), terminado, info

    def close(self):
        if self._abierto:
            traci.close()
            self._abierto = False

    # --- interno -----------------------------------------------------------------
    def _en_punto_de_decision(self):
        return self.guard.etapa == VERDE and self.guard.tiempo_en_etapa(self._tiempo) >= self.guard.verde_min_s

    def _avanzar_un_segundo(self, pedir_cambio):
        traci.simulationStep()
        self._tiempo = traci.simulation.getTime()
        self._actuador.verificar()
        self._estado_trafico = self._fuente.leer_estado()
        nueva_fase = self.guard.paso(self._tiempo, pedir_cambio)
        if nueva_fase != self._fase:
            self._actuador.aplicar(nueva_fase)
            self._fase = nueva_fase
        return sum(brazo.detenidos for brazo in self._estado_trafico.brazos.values())

    def _avanzar_hasta_decision(self, pedir_cambio):
        """Avanza al menos un intervalo y luego hasta el siguiente momento en que el agente puede decidir."""
        detenidos, segundos = 0, 0
        while self._tiempo < self._fin_episodio:
            # la peticion de cambio se entrega solo en el primer segundo (instante de la decision)
            detenidos += self._avanzar_un_segundo(pedir_cambio and segundos == 0)
            segundos += 1
            if segundos >= self._intervalo and self._en_punto_de_decision():
                break
        return detenidos, segundos

    def _estado_actual(self):
        return self.codificador.codificar(
            self._estado_trafico, self.guard.eje, self.guard.tiempo_en_etapa(self._tiempo)
        )
