"""
Fase 2 - Paso 1: conectar Python con SUMO mediante TraCI y LEER el estado del trafico.

Que hace:
  1. Abre la simulacion de prueba (sumo/configs/prueba.sumocfg) controlada desde Python.
  2. Avanza la simulacion segundo a segundo.
  3. Cada INTERVALO_REPORTE segundos imprime, por cada brazo de llegada:
       - vehiculos presentes en el carril de llegada
       - vehiculos detenidos (velocidad < 0.1 m/s, definicion de SUMO)
     y el estado del semaforo.
  4. NO cambia nada: solo observa. (El control del semaforo es el Paso 2.)

Ubicacion: tesis/src/simulation/paso1_leer_estado.py
Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe src\\simulation\\paso1_leer_estado.py          (sin ventana, rapido)
  .\\.venv\\Scripts\\python.exe src\\simulation\\paso1_leer_estado.py --gui    (con sumo-gui)
"""
import argparse
import os
import sys
from pathlib import Path

# --- Verificaciones previas: errores claros en lugar de fallos misteriosos ---
if "SUMO_HOME" not in os.environ:
    sys.exit("ERROR: la variable SUMO_HOME no esta definida. Revisa la instalacion de SUMO.")

import sumolib  # noqa: E402  (se importa despues de verificar SUMO_HOME)
import traci    # noqa: E402

# --- Constantes del escenario (no "numeros magicos" sueltos en el codigo) ---
CARPETA_TESIS = Path(__file__).resolve().parents[2]
ARCHIVO_CONFIG = CARPETA_TESIS / "sumo" / "configs" / "prueba.sumocfg"

ID_SEMAFORO = "cluster_12995046887_9702926134"

# Brazo de llegada -> edge de llegada en acacias.net.xml (verificado 2026-10-06)
EDGES_LLEGADA = {
    "norte (Cra 23)": "-642480900",
    "sur   (Cra 23)": "807940779",
    "este  (Dg 15)":  "816899410#0",
    "oeste (Dg 15)":  "44411778#0",
}

INTERVALO_REPORTE = 30  # segundos simulados entre cada reporte


def construir_comando(usar_gui):
    """Arma el comando para arrancar SUMO (con o sin ventana)."""
    binario = sumolib.checkBinary("sumo-gui" if usar_gui else "sumo")
    comando = [binario, "-c", str(ARCHIVO_CONFIG)]
    if usar_gui:
        # --start: arranca sin pulsar Run; --quit-on-end: cierra la ventana al terminar
        comando += ["--start", "--quit-on-end", "--delay", "50"]
    return comando


def verificar_red():
    """Comprueba que los IDs del codigo existen en la red cargada."""
    edges_en_red = set(traci.edge.getIDList())
    for brazo, edge in EDGES_LLEGADA.items():
        if edge not in edges_en_red:
            raise ValueError(f"El edge '{edge}' del brazo {brazo} no existe en la red.")
    if ID_SEMAFORO not in traci.trafficlight.getIDList():
        raise ValueError(f"El semaforo '{ID_SEMAFORO}' no existe en la red.")


def imprimir_reporte(tiempo):
    fase = traci.trafficlight.getPhase(ID_SEMAFORO)
    estado_luces = traci.trafficlight.getRedYellowGreenState(ID_SEMAFORO)
    print(f"\nt = {tiempo:6.0f} s | semaforo: fase {fase}, luces '{estado_luces}'")
    print(f"   {'brazo':<16}{'vehiculos':>10}{'detenidos':>11}")
    for brazo, edge in EDGES_LLEGADA.items():
        vehiculos = traci.edge.getLastStepVehicleNumber(edge)
        detenidos = traci.edge.getLastStepHaltingNumber(edge)
        print(f"   {brazo:<16}{vehiculos:>10}{detenidos:>11}")


def main():
    parser = argparse.ArgumentParser(description="Lee el estado del trafico desde SUMO con TraCI.")
    parser.add_argument("--gui", action="store_true", help="abrir sumo-gui para ver la simulacion")
    args = parser.parse_args()

    if not ARCHIVO_CONFIG.exists():
        sys.exit(f"ERROR: no se encuentra {ARCHIVO_CONFIG}")

    print(f"Abriendo SUMO con: {ARCHIVO_CONFIG}")
    traci.start(construir_comando(args.gui))
    try:
        verificar_red()
        total_llegados = 0
        # getMinExpectedNumber(): vehiculos en la red + los que aun faltan por entrar.
        # Cuando llega a 0, ya no queda nada que simular.
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()  # avanza 1 segundo (paso por defecto de SUMO)
            total_llegados += traci.simulation.getArrivedNumber()
            tiempo = traci.simulation.getTime()
            if tiempo % INTERVALO_REPORTE == 0:
                imprimir_reporte(tiempo)
        print(f"\nFin de la simulacion en t = {traci.simulation.getTime():.0f} s")
        print(f"Vehiculos que completaron su recorrido: {total_llegados}")
    finally:
        # Se cierra la conexion siempre, incluso si hubo un error (el error igual se muestra).
        traci.close()


if __name__ == "__main__":
    main()
