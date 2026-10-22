"""SumoSource: LEE el estado del trafico desde SUMO y lo entrega como EstadoTrafico.

Cada brazo se mide sobre uno o varios tramos (edges) consecutivos, definidos en config/interseccion.yaml
(brazos.<nombre>.edges, desde la linea de pare hacia atras). Ademas se cuenta lo que hay en la ZONA DE CAMARA:
los ultimos "zona_camara_m" metros antes de la linea de pare (mismo largo para todos los brazos).
"""
import traci

VELOCIDAD_DETENIDO_MS = 0.1  # mismo umbral que usa SUMO para "halting" (getLastStepHaltingNumber)

from src.common.estado import EstadoBrazo, EstadoTrafico


class SumoSource:
    def __init__(self, config):
        self._edges = {nombre: list(datos["edges"]) for nombre, datos in config["brazos"].items()}
        self._espacio_por_vehiculo = float(config["espacio_por_vehiculo_m"])
        self._zona_camara_m = float(config["zona_camara_m"])

        edges_en_red = set(traci.edge.getIDList())
        for nombre, edges in self._edges.items():
            for edge in edges:
                if edge not in edges_en_red:
                    raise ValueError(f"El edge '{edge}' del brazo '{nombre}' no existe en la red.")

        self._capacidad = {nombre: sum(self._calcular_capacidad(edge) for edge in edges)
                           for nombre, edges in self._edges.items()}
        # Distancia desde la linea de pare hasta el FINAL de cada tramo (0 para el primero) y largo del tramo.
        self._tramos = {}
        for nombre, edges in self._edges.items():
            distancia_al_pare, tramos = 0.0, []
            for edge in edges:
                largo = traci.lane.getLength(f"{edge}_0")
                tramos.append((edge, distancia_al_pare, largo))
                distancia_al_pare += largo
            self._tramos[nombre] = tramos

    def _calcular_capacidad(self, edge):
        """Vehiculos que caben en cola en el tramo: largo total de sus carriles / espacio por vehiculo."""
        numero_carriles = traci.edge.getLaneNumber(edge)
        largo_total = sum(traci.lane.getLength(f"{edge}_{indice}") for indice in range(numero_carriles))
        return largo_total / self._espacio_por_vehiculo

    @property
    def capacidad(self):
        return dict(self._capacidad)

    def _contar_zona(self, nombre):
        """Vehiculos y detenidos a no mas de zona_camara_m de la linea de pare."""
        vehiculos, detenidos = 0, 0
        for edge, distancia_fin_tramo, largo in self._tramos[nombre]:
            if distancia_fin_tramo >= self._zona_camara_m:
                break
            for vehiculo in traci.edge.getLastStepVehicleIDs(edge):
                distancia_al_pare = distancia_fin_tramo + largo - traci.vehicle.getLanePosition(vehiculo)
                if distancia_al_pare <= self._zona_camara_m:
                    vehiculos += 1
                    detenidos += traci.vehicle.getSpeed(vehiculo) < VELOCIDAD_DETENIDO_MS
        return vehiculos, detenidos

    def leer_estado(self, incluir_zona=True):
        """incluir_zona=False omite la zona de camara (queda en None): es la parte costosa, porque consulta
        la posicion de cada vehiculo. El entrenamiento la pide solo en los instantes de decision."""
        brazos = {}
        for nombre, edges in self._edges.items():
            detenidos = sum(traci.edge.getLastStepHaltingNumber(edge) for edge in edges)
            vehiculos_zona, detenidos_zona = self._contar_zona(nombre) if incluir_zona else (None, None)
            brazos[nombre] = EstadoBrazo(
                vehiculos=sum(traci.edge.getLastStepVehicleNumber(edge) for edge in edges),
                detenidos=detenidos,
                cola_relativa=detenidos / self._capacidad[nombre],
                vehiculos_zona=vehiculos_zona,
                detenidos_zona=detenidos_zona,
            )
        return EstadoTrafico(tiempo=traci.simulation.getTime(), brazos=brazos)
