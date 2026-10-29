"""
Entorno de entrenamiento: el "juego" en el que practica el agente.

    estado = entorno.reset(semilla)            # empieza un dia nuevo de trafico
    while not terminado:
        accion = agente.elegir(estado)         # 0 mantener / 1 cambiar
        estado, recompensa, terminado, info = entorno.step(accion)

Cuando decide el agente: solo durante un verde, y solo despues del verde minimo
(antes de eso el SafetyGuard no permitiria cambiar). Durante amarillo y todo-rojo
la simulacion avanza sola.

Recompensa de cada paso (con recompensa.incluir_aguas_arriba, tambien los detenidos en los tramos aguas arriba de
cada brazo; ver config/agente.yaml): -(suma de vehiculos detenidos en los 4 brazos, segundo a
segundo, durante todo el paso). Si el paso incluye una transicion (amarillo + todo-rojo
+ verde minimo del otro eje), esos segundos tambien cuentan: son consecuencia de cambiar.
Con aprendizaje.descuento = "por_segundo" la recompensa del paso es -(sum_t gamma^t * detenidos_t) (ver qlearning.py).
El perfil de seguridad del agente sale de config/agente.yaml (perfil_seguridad: "real" o "norma").
"""
import traci

from src.agent.codificador_estado import CodificadorEstado
from src.agent.qlearning import CAMBIAR, MANTENER
from src.controller.safety_guard import VERDE, SafetyGuard
from src.simulation import desatascador as modulo_desatascador
from src.simulation import semaforo_calle18
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
        # Iteracion 3: la recompensa incluye la cola aguas arriba (fuera de la zona de medicion)
        self._recompensa_aguas_arriba = config_agente.get("recompensa", {}).get("incluir_aguas_arriba", False)
        # Iteracion 4b: tambien los vehiculos que YA deberian haber entrado a la red y no caben (acceso lleno). SUMO los
        # deja esperando fuera de la red: no aparecen como detenidos en ningun tramo. Solo se usa para ENTRENAR (la
        # recompensa no existe en la maqueta; el estado si debe poder medirse con la camara).
        self._recompensa_pendientes = config_agente.get("recompensa", {}).get("incluir_entrada_pendiente", False)
        # Iteracion 4b: perfil de seguridad y descuento configurables (antes: siempre "norma" y por decision)
        self._perfil_seguridad = config_agente.get("perfil_seguridad", "norma")
        aprendizaje = config_agente.get("aprendizaje", {})
        self._descuento_por_segundo = aprendizaje.get("descuento", "por_decision") == "por_segundo"
        self._gamma = aprendizaje.get("gamma")
        if self._descuento_por_segundo and not (0 <= (self._gamma or -1) < 1):
            raise ValueError(f"descuento por_segundo requiere 0 <= gamma < 1 (gamma={self._gamma})")
        self._config_calle18 = semaforo_calle18.cargar_config()
        self._abierto = False

    # --- interfaz del entorno ----------------------------------------------------
    def reset(self, semilla, archivo_escenario=None):
        """Empieza un episodio. archivo_escenario permite cambiar de escenario entre episodios."""
        self.close()
        if archivo_escenario is not None:
            self._archivo = archivo_escenario
        iniciar_sumo(self._archivo, usar_gui=self._usar_gui, semilla=semilla)
        self._abierto = True
        self.desfase_calle18 = semaforo_calle18.configurar(semilla, self._config_calle18)
        self._desatascador = modulo_desatascador.crear_desde_config()
        self._fuente = SumoSource(self._config_interseccion)
        self._actuador = SumoActuator(self._config_interseccion)
        self.guard = SafetyGuard.desde_config(self._config_controlador, self._perfil_seguridad)
        self._tiempo = traci.simulation.getTime()
        self._fase = self.guard.iniciar(self._tiempo)
        self._actuador.aplicar(self._fase)
        self._estado_trafico = self._fuente.leer_estado()
        # antes de avanzar: _avanzar_un_segundo ya los va sumando (error del 2026-10-28: se iniciaba despues)
        self.teletransportes_episodio = 0  # vehiculos que SUMO saco de un atasco (auditoria del entrenamiento)

        detenidos, _, _ = self._avanzar_hasta_decision(pedir_cambio=False)
        self.detenidos_episodio = detenidos
        self.segundos_episodio = 0
        return self._estado_actual()

    def step(self, accion):
        if not self._abierto:
            raise RuntimeError("Llama a reset() antes de step().")
        detenidos, segundos, detenidos_descontados = self._avanzar_hasta_decision(pedir_cambio=(accion == CAMBIAR))
        self.detenidos_episodio += detenidos
        self.segundos_episodio += segundos
        terminado = self._tiempo >= self._fin_episodio
        # El episodio solo termina por TIEMPO (el trafico sigue): es un corte, no un estado final ("truncado").
        info = {"tiempo": self._tiempo, "segundos": segundos, "detenidos": detenidos, "truncado": terminado}
        recompensa = -float(detenidos_descontados if self._descuento_por_segundo else detenidos)
        return self._estado_actual(), recompensa, terminado, info

    @property
    def desatascos_episodio(self):
        return len(self._desatascador.eventos) if self._desatascador is not None else 0

    def accion_plan(self, verdes_plan_s):
        """Lo que haria el semaforo de tiempos fijos ahora: cambiar si el verde actual ya alcanzo su duracion."""
        return CAMBIAR if self.guard.tiempo_en_etapa(self._tiempo) >= verdes_plan_s[self.guard.eje] else MANTENER

    def close(self):
        if self._abierto:
            traci.close()
            self._abierto = False

    # --- interno -----------------------------------------------------------------
    def _en_punto_de_decision(self):
        return self.guard.etapa == VERDE and self.guard.tiempo_en_etapa(self._tiempo) >= self.guard.verde_min(self.guard.eje)

    def _avanzar_un_segundo(self, pedir_cambio):
        traci.simulationStep()
        self._tiempo = traci.simulation.getTime()
        self.teletransportes_episodio += traci.simulation.getStartingTeleportNumber()
        if self._desatascador is not None:
            self._desatascador.paso(self._tiempo)
        self._actuador.verificar()
        # Cada segundo solo se necesitan los detenidos de los brazos (recompensa); la zona de camara se mide al decidir.
        self._estado_trafico = self._fuente.leer_estado(incluir_zona=False)
        nueva_fase = self.guard.paso(self._tiempo, pedir_cambio)
        if nueva_fase != self._fase:
            self._actuador.aplicar(nueva_fase)
            self._fase = nueva_fase
        brazos = self._estado_trafico.brazos.values()
        if self._recompensa_aguas_arriba:
            detenidos = sum(b.detenidos + b.detenidos_aguas_arriba for b in brazos)
        else:
            detenidos = sum(b.detenidos for b in brazos)
        if self._recompensa_pendientes:
            detenidos += len(traci.simulation.getPendingVehicles())
        return detenidos

    def _avanzar_hasta_decision(self, pedir_cambio):
        """Avanza al menos un intervalo y luego hasta el siguiente momento en que el agente puede decidir."""
        detenidos, segundos, detenidos_descontados = 0, 0, 0.0
        while self._tiempo < self._fin_episodio:
            # la peticion de cambio se entrega solo en el primer segundo (instante de la decision)
            detenidos_segundo = self._avanzar_un_segundo(pedir_cambio and segundos == 0)
            detenidos += detenidos_segundo
            if self._descuento_por_segundo:
                detenidos_descontados += detenidos_segundo * self._gamma ** segundos  # = suma_descontada()
            segundos += 1
            if segundos >= self._intervalo and self._en_punto_de_decision():
                break
        self._estado_trafico = self._fuente.leer_estado(incluir_zona=True)  # lo que ve el agente para decidir
        return detenidos, segundos, detenidos_descontados

    def _estado_actual(self):
        return self.codificador.codificar(
            self._estado_trafico, self.guard.eje, self.guard.tiempo_en_etapa(self._tiempo)
        )
