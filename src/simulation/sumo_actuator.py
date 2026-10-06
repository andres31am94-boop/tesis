"""SumoActuator: APLICA las luces del semaforo en SUMO y verifica que se cumplan."""
import traci

LETRAS_VALIDAS = set("Ggyr")


class SumoActuator:
    def __init__(self, config):
        self._id_semaforo = config["semaforo_id"]
        self._luces = dict(config["luces"])

        if self._id_semaforo not in traci.trafficlight.getIDList():
            raise ValueError(f"El semaforo '{self._id_semaforo}' no existe en la red.")
        numero_movimientos = len(traci.trafficlight.getControlledLinks(self._id_semaforo))
        for nombre, luces in self._luces.items():
            if len(luces) != numero_movimientos:
                raise ValueError(
                    f"Fase '{nombre}': {len(luces)} letras, pero el semaforo controla {numero_movimientos} movimientos."
                )
            letras_raras = set(luces) - LETRAS_VALIDAS
            if letras_raras:
                raise ValueError(f"Fase '{nombre}': letras no validas {letras_raras}")

        self._luces_ordenadas = None

    def aplicar(self, nombre_fase):
        if nombre_fase not in self._luces:
            raise KeyError(f"Fase desconocida '{nombre_fase}'. Fases validas: {list(self._luces)}")
        luces = self._luces[nombre_fase]
        traci.trafficlight.setRedYellowGreenState(self._id_semaforo, luces)
        self._luces_ordenadas = luces
        return luces

    def verificar(self):
        """Lanza un error si SUMO no tiene exactamente las luces ordenadas."""
        if self._luces_ordenadas is None:
            return
        luces_en_sumo = traci.trafficlight.getRedYellowGreenState(self._id_semaforo)
        if luces_en_sumo != self._luces_ordenadas:
            raise RuntimeError(
                f"t = {traci.simulation.getTime()}: se ordeno '{self._luces_ordenadas}' "
                f"pero SUMO tiene '{luces_en_sumo}'"
            )
