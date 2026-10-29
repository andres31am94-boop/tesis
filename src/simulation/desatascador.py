"""
Desatascador del semaforo de la Calle 18 (2026-10-27).

Problema (artefacto del modelo de subcarriles de SUMO, ver docs/bitacora.md): en la fila del carril unico hacia la
Calle 18 las motos desplazan a carros y buses de lado hasta sacarlos parcialmente del carril; al llegar al cruce interno
del semaforo (0.1 m) el vehiculo no puede enderezarse y queda quieto PARA SIEMPRE, aunque el semaforo este en verde y no
tenga nada adelante. La cola que se forma detras llega hasta la interseccion principal.

Criterio (dato de campo de los autores: con el verde de la Calle 18 pasan todos los vehiculos):
  un vehiculo que esta EN la linea de pare del semaforo de la Calle 18 (o ya dentro de su cruce interno),
  con la luz de su movimiento en VERDE, SIN ningun vehiculo adelante a menos de 'distancia_libre_m',
  y QUIETO durante 'segundos_quieto' seguidos  ->  es el artefacto: se le traslada al inicio del tramo de salida.
Un vehiculo real en esa situacion arranca en 2-3 s; por eso el criterio no toca colas reales. Solo actua en el semaforo
de la Calle 18: la interseccion principal (Cra 23 x Dg 15) conserva el comportamiento normal de SUMO (teleport a 300 s).
Cada traslado se cuenta y se registra (tiempo, vehiculo, carril) para reportarlo por controlador.
"""
import traci as _traci

ID_SEMAFORO = "calle18"


class Desatascador:
    def __init__(self, segundos_quieto=20, distancia_libre_m=15.0, margen_linea_pare_m=3.0, margen_salida_m=3.0,
                 traci_mod=None):
        if segundos_quieto < 5:
            raise ValueError("segundos_quieto debe ser >= 5 (un vehiculo real tarda 2-3 s en arrancar)")
        self.segundos_quieto = segundos_quieto
        self.distancia_libre_m = distancia_libre_m
        self.margen_linea_pare_m = margen_linea_pare_m
        self.margen_salida_m = margen_salida_m
        self._traci = traci_mod or _traci
        self._quieto = {}          # vehiculo -> segundos seguidos cumpliendo el criterio
        self.eventos = []          # (tiempo, vehiculo, carril donde estaba, carril de destino)
        # Diagnostico: vehiculos quietos 60 s en la linea de pare SIN que el desatasco actue, con el motivo
        # (luz y lider). Sirve para entender bloqueos que el criterio no cubre. (tiempo, vehiculo, carril, luz, lider)
        self.diagnostico = []
        self._quieto_total = {}
        # movimientos del semaforo: indice de luz -> (carril de llegada, carril de salida, carril interno)
        self._movimientos = {}
        for indice, enlaces in enumerate(self._traci.trafficlight.getControlledLinks(ID_SEMAFORO)):
            for llegada, salida, interno in enlaces:
                self._movimientos[indice] = (llegada, salida, interno)
        # 2026-10-28: salidas LIBRES = carriles de salida que terminan la red (sin conexiones siguientes; aqui el tramo
        # despues de la Calle 18 hacia Villavicencio). Nada puede detener alli a un vehiculo: si uno queda quieto
        # 'segundos_quieto' es el mismo artefacto (validacion de aforo_v7, jueves s108: un vehiculo quieto justo
        # despues del semaforo dejaba sin desatascar a los de atras, porque tenian a alguien "adelante").
        self._salidas_libres = sorted({salida for _, salida, _ in self._movimientos.values()
                                       if not self._traci.lane.getLinks(salida)})

    def _candidatos(self):
        """(vehiculo, indice de luz, carril de salida) de los vehiculos en la linea de pare o en el cruce interno."""
        t = self._traci
        for indice, (llegada, salida, interno) in self._movimientos.items():
            for vehiculo in t.lane.getLastStepVehicleIDs(interno):
                yield vehiculo, indice, salida
            en_llegada = t.lane.getLastStepVehicleIDs(llegada)
            if en_llegada:
                primero = max(en_llegada, key=t.vehicle.getLanePosition)   # el mas cercano a la linea de pare
                if t.vehicle.getLanePosition(primero) >= t.lane.getLength(llegada) - self.margen_linea_pare_m:
                    yield primero, indice, salida

    def paso(self, tiempo):
        """Llamar una vez por segundo simulado. Devuelve cuantos vehiculos se destrabaron en este segundo."""
        t = self._traci
        luces = t.trafficlight.getRedYellowGreenState(ID_SEMAFORO)
        vistos, trasladados = set(), 0
        for vehiculo, indice, salida in self._candidatos():
            vistos.add(vehiculo)
            lider = t.vehicle.getLeader(vehiculo, self.distancia_libre_m)
            # "Nadie adelante": sin lider, lider lejos, o lider con distancia NEGATIVA = esta AL LADO (no adelante).
            # 2026-10-28 (v7, jueves s108): un carro y una moto quedaron lado a lado en la linea de pare (misma posicion,
            # cada uno en su mitad del carril, sin bloqueo lateral) y en verde ninguno arrancaba durante 300 s; cada uno
            # veia al otro como "lider" y el desatasco no actuaba. Es el bloqueo mutuo que describieron los autores.
            nadie_adelante = lider is None or lider[1] > self.distancia_libre_m or lider[1] < 0
            atascado = luces[indice] in "Gg" and t.vehicle.getSpeed(vehiculo) < 0.1 and nadie_adelante
            self._quieto[vehiculo] = self._quieto.get(vehiculo, 0) + 1 if atascado else 0
            quieto = t.vehicle.getSpeed(vehiculo) < 0.1
            self._quieto_total[vehiculo] = self._quieto_total.get(vehiculo, 0) + 1 if quieto else 0
            if self._quieto_total[vehiculo] == 60:
                self.diagnostico.append((tiempo, vehiculo, t.vehicle.getLaneID(vehiculo), luces[indice], lider))
            if self._quieto[vehiculo] >= self.segundos_quieto:
                self.eventos.append((tiempo, vehiculo, t.vehicle.getLaneID(vehiculo), salida))
                # se ubica con TODO su largo dentro del tramo de salida (+ margen): si quedara en la posicion 0.1, su parte
                # trasera seguiria dentro del cruce y chocaria con el vehiculo que estaba trabado a su lado
                # (prueba real jueves s110: "junction collision" con un camion, gap -7.4 m).
                posicion = min(t.vehicle.getLength(vehiculo) + self.margen_salida_m, t.lane.getLength(salida) - 1.0)
                t.vehicle.moveTo(vehiculo, salida, posicion)
                self._quieto.pop(vehiculo)
                trasladados += 1
        for salida in self._salidas_libres:
            quietos = [v for v in t.lane.getLastStepVehicleIDs(salida) if t.vehicle.getSpeed(v) < 0.1]
            for vehiculo in quietos:
                vistos.add(vehiculo)
                self._quieto[vehiculo] = self._quieto.get(vehiculo, 0) + 1
            listos = [v for v in quietos if self._quieto[v] >= self.segundos_quieto]
            if listos:
                # solo el de MAS ADELANTE: los de atras estan quietos por el y arrancan solos
                vehiculo = max(listos, key=t.vehicle.getLanePosition)
                largo_salida = t.lane.getLength(salida)
                posicion = min(t.vehicle.getLanePosition(vehiculo) + t.vehicle.getLength(vehiculo)
                               + self.margen_salida_m, largo_salida - 1.0)
                self.eventos.append((tiempo, vehiculo, salida, salida))
                t.vehicle.moveTo(vehiculo, salida, posicion)
                self._quieto.pop(vehiculo)
                trasladados += 1
        for vehiculo in list(self._quieto_total):
            if vehiculo not in vistos:
                del self._quieto_total[vehiculo]
        for vehiculo in list(self._quieto):     # olvida a los que ya no estan en la linea de pare
            if vehiculo not in vistos:
                del self._quieto[vehiculo]
        return trasladados


def crear_desde_config(traci_mod=None):
    """Lee config/calibracion.yaml (seccion desatasco_calle18). Devuelve None si esta desactivado o no hay Calle 18."""
    import yaml
    from src.common.configuracion import CARPETA_TESIS
    with open(CARPETA_TESIS / "config" / "calibracion.yaml", encoding="utf-8") as archivo:
        config = yaml.safe_load(archivo).get("desatasco_calle18", {"activo": False})
    t = traci_mod or _traci
    if not config["activo"] or ID_SEMAFORO not in t.trafficlight.getIDList():
        return None
    return Desatascador(config["segundos_quieto"], config["distancia_libre_m"], traci_mod=t)
