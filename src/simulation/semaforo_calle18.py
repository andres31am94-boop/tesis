"""
Semaforo de la Carrera 23 con Calle 18 (~260 m al norte): semaforo FIJO del entorno, no lo controla el agente.

Tiempos medidos en config/semaforo_calle18.yaml. El DESFASE (en que punto de su ciclo esta cuando empieza la
simulacion) no se ha medido: si desfase_s es null, se elige al azar con la semilla de la corrida, de modo que
cada semilla repite su desfase y el conjunto de semillas cubre desfases distintos.
"""
import random

import traci

from src.common.configuracion import CARPETA_TESIS

ID_SEMAFORO = "calle18"
PROGRAMA = "medido"


def cargar_config():
    import yaml
    with open(CARPETA_TESIS / "config" / "semaforo_calle18.yaml", encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def duraciones(config):
    t = config["tiempos_cra23_s"]
    return [t["verde"], t["amarillo"], t["rojo"]]


def fase_para_desfase(duraciones_fases, desfase_s):
    """Fase (indice) y segundos que le quedan cuando el ciclo va en el segundo 'desfase_s'.
    Ej.: [58, 3, 41] y desfase 60 -> fase 1 (amarillo) con 1 s restante."""
    posicion = desfase_s % sum(duraciones_fases)
    for indice, duracion in enumerate(duraciones_fases):
        if posicion < duracion:
            return indice, duracion - posicion
        posicion -= duracion
    raise AssertionError("no deberia llegar aqui")


def configurar(semilla, config=None):
    """Activa el programa medido con su desfase. Devuelve el desfase usado (s) o None si esta desactivado."""
    config = config or cargar_config()
    if not config["activo"]:
        return None
    if ID_SEMAFORO not in traci.trafficlight.getIDList():
        raise ValueError("config/semaforo_calle18.yaml esta activo pero la red no tiene el semaforo 'calle18': "
                         "reconstruye la red (generar_accesos.py + netconvert).")
    fases = duraciones(config)
    desfase = config["desfase_s"]
    if desfase is None:
        desfase = random.Random(semilla).randrange(sum(fases))
    traci.trafficlight.setProgram(ID_SEMAFORO, PROGRAMA)
    indice, restante = fase_para_desfase(fases, desfase)
    traci.trafficlight.setPhase(ID_SEMAFORO, indice)
    traci.trafficlight.setPhaseDuration(ID_SEMAFORO, restante)
    return desfase
