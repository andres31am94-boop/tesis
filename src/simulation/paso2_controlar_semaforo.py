"""
Fase 2 - Paso 2: CONTROLAR el semaforo desde Python con TraCI.

Que hace:
  - Ignora el programa del semaforo que trae la red y aplica, desde Python, una secuencia
    de fases propia (con todo-rojo), usando traci.trafficlight.setRedYellowGreenState().
  - En CADA segundo comprueba que SUMO tiene exactamente las luces que Python ordeno.
    Si no coinciden, se detiene con un error (asi demostramos que el control es real).
  - En cada cambio de fase imprime el tiempo, la fase y los detenidos por eje.

Los tiempos de este script son SOLO DE PRUEBA (no son los del semaforo real).

Ubicacion: tesis/src/simulation/paso2_controlar_semaforo.py
Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe src\\simulation\\paso2_controlar_semaforo.py
  .\\.venv\\Scripts\\python.exe src\\simulation\\paso2_controlar_semaforo.py --gui
"""
import argparse
import os
import sys
from pathlib import Path

if "SUMO_HOME" not in os.environ:
    sys.exit("ERROR: la variable SUMO_HOME no esta definida. Revisa la instalacion de SUMO.")

import sumolib  # noqa: E402
import traci    # noqa: E402

CARPETA_TESIS = Path(__file__).resolve().parents[2]
ARCHIVO_CONFIG = CARPETA_TESIS / "sumo" / "configs" / "prueba.sumocfg"
ID_SEMAFORO = "cluster_12995046887_9702926134"

# Orden de las 12 letras (verificado en el paso 1): 3 por brazo -> norte, este, sur, oeste.
# G = verde con prioridad, g = verde cediendo el paso, y = amarillo, r = rojo.
FASES_PRUEBA = [
    # (nombre,             luces,          duracion en s)
    ("VERDE Dg 15",        "rrrGGGrrrGGG", 60),
    ("AMARILLO Dg 15",     "rrryyyrrryyy", 3),
    ("TODO ROJO",          "rrrrrrrrrrrr", 2),
    ("VERDE Cra 23",       "GGGrrrGgGrrr", 20),
    ("AMARILLO Cra 23",    "yyyrrryyyrrr", 3),
    ("TODO ROJO",          "rrrrrrrrrrrr", 2),
]

EDGES_CRA_23 = ["-642480900", "807940779"]    # llegadas norte y sur
EDGES_DG_15 = ["816899410#0", "44411778#0"]   # llegadas este y oeste

DURACION_PRUEBA = 600  # segundos simulados (suficiente para ver ~6 ciclos)


def construir_comando(usar_gui):
    binario = sumolib.checkBinary("sumo-gui" if usar_gui else "sumo")
    comando = [binario, "-c", str(ARCHIVO_CONFIG)]
    if usar_gui:
        comando += ["--start", "--quit-on-end", "--delay", "100"]
    return comando


def verificar_semaforo():
    """El largo de cada cadena de luces debe coincidir con los movimientos del semaforo."""
    if ID_SEMAFORO not in traci.trafficlight.getIDList():
        raise ValueError(f"El semaforo '{ID_SEMAFORO}' no existe en la red.")
    numero_movimientos = len(traci.trafficlight.getControlledLinks(ID_SEMAFORO))
    for nombre, luces, _ in FASES_PRUEBA:
        if len(luces) != numero_movimientos:
            raise ValueError(
                f"La fase '{nombre}' tiene {len(luces)} letras, pero el semaforo "
                f"controla {numero_movimientos} movimientos."
            )


def detenidos(edges):
    return sum(traci.edge.getLastStepHaltingNumber(edge) for edge in edges)


def aplicar_fase(indice, tiempo):
    nombre, luces, duracion = FASES_PRUEBA[indice]
    traci.trafficlight.setRedYellowGreenState(ID_SEMAFORO, luces)
    print(
        f"t = {tiempo:5.0f} s -> {nombre:<16} '{luces}' por {duracion:>2} s | "
        f"detenidos Cra 23: {detenidos(EDGES_CRA_23):>2}  Dg 15: {detenidos(EDGES_DG_15):>2}"
    )
    return tiempo + duracion  # momento en que termina esta fase


def main():
    parser = argparse.ArgumentParser(description="Controla el semaforo de SUMO desde Python.")
    parser.add_argument("--gui", action="store_true", help="abrir sumo-gui para ver la simulacion")
    args = parser.parse_args()

    if not ARCHIVO_CONFIG.exists():
        sys.exit(f"ERROR: no se encuentra {ARCHIVO_CONFIG}")

    traci.start(construir_comando(args.gui))
    try:
        verificar_semaforo()
        tiempo = traci.simulation.getTime()
        indice_fase = 0
        fin_fase = aplicar_fase(indice_fase, tiempo)
        luces_ordenadas = FASES_PRUEBA[indice_fase][1]
        segundos_verificados = 0

        while tiempo < DURACION_PRUEBA and traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            tiempo = traci.simulation.getTime()

            # Comprobacion: SUMO debe tener EXACTAMENTE las luces que Python ordeno.
            luces_en_sumo = traci.trafficlight.getRedYellowGreenState(ID_SEMAFORO)
            if luces_en_sumo != luces_ordenadas:
                raise RuntimeError(
                    f"t = {tiempo}: Python ordeno '{luces_ordenadas}' pero SUMO tiene '{luces_en_sumo}'"
                )
            segundos_verificados += 1

            if tiempo >= fin_fase:
                indice_fase = (indice_fase + 1) % len(FASES_PRUEBA)
                fin_fase = aplicar_fase(indice_fase, tiempo)
                luces_ordenadas = FASES_PRUEBA[indice_fase][1]

        print(f"\nFin de la prueba en t = {tiempo:.0f} s")
        print(f"Segundos en que se comprobo que SUMO obedecio a Python: {segundos_verificados}")
    finally:
        traci.close()


if __name__ == "__main__":
    main()
