"""SumoSource: LEE el estado del trafico desde SUMO y lo entrega como EstadoTrafico."""
import traci

from src.common.estado import EstadoBrazo, EstadoTrafico


class SumoSource:
    def __init__(self, config):
        self._edges = {nombre: datos["edge"] for nombre, datos in config["brazos"].items()}
        self._espacio_por_vehiculo = float(config["espacio_por_vehiculo_m"])

        edges_en_red = set(traci.edge.getIDList())
        for nombre, edge in self._edges.items():
            if edge not in edges_en_red:
                raise ValueError(f"El edge '{edge}' del brazo '{nombre}' no existe en la red.")

        self._capacidad = {nombre: self._calcular_capacidad(edge) for nombre, edge in self._edges.items()}

    def _calcular_capacidad(self, edge):
        """Vehiculos que caben en cola en el tramo: largo total de sus carriles / espacio por vehiculo."""
        numero_carriles = traci.edge.getLaneNumber(edge)
        largo_total = sum(traci.lane.getLength(f"{edge}_{indice}") for indice in range(numero_carriles))
        return largo_total / self._espacio_por_vehiculo

    @property
    def capacidad(self):
        return dict(self._capacidad)

    def leer_estado(self):
        brazos = {}
        for nombre, edge in self._edges.items():
            detenidos = traci.edge.getLastStepHaltingNumber(edge)
            brazos[nombre] = EstadoBrazo(
                vehiculos=traci.edge.getLastStepVehicleNumber(edge),
                detenidos=detenidos,
                cola_relativa=detenidos / self._capacidad[nombre],
            )
        return EstadoTrafico(tiempo=traci.simulation.getTime(), brazos=brazos)
