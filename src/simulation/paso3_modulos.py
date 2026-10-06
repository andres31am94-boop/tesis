"""
Fase 2 - Paso 3: la misma prueba del paso 2, pero usando los modulos de la arquitectura
(configuracion, SumoSource, SumoActuator, sesion_sumo).

Prueba de que el reordenamiento no rompio nada: con la misma semilla, las lineas que
empiezan con "t =" deben ser IDENTICAS a las del paso 2.

Los tiempos de las fases son SOLO DE PRUEBA.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe -m src.simulation.paso3_modulos
  .\\.venv\\Scripts\\python.exe -m src.simulation.paso3_modulos --gui
"""
import argparse

import traci

from src.common.configuracion import CARPETA_TESIS, cargar_interseccion
from src.simulation.sesion_sumo import sesion_sumo
from src.simulation.sumo_actuator import SumoActuator
from src.simulation.sumo_source import SumoSource

ARCHIVO_ESCENARIO = CARPETA_TESIS / "sumo" / "configs" / "prueba.sumocfg"
DURACION_PRUEBA = 600

# (nombre de la fase en config/interseccion.yaml, nombre para imprimir, duracion de PRUEBA en s)
SECUENCIA_PRUEBA = [
    ("verde_dg15",     "VERDE Dg 15",     60),
    ("amarillo_dg15",  "AMARILLO Dg 15",  3),
    ("todo_rojo",      "TODO ROJO",       2),
    ("verde_cra23",    "VERDE Cra 23",    20),
    ("amarillo_cra23", "AMARILLO Cra 23", 3),
    ("todo_rojo",      "TODO ROJO",       2),
]


def main():
    parser = argparse.ArgumentParser(description="Prueba de los modulos SumoSource y SumoActuator.")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()

    config = cargar_interseccion()
    brazos_cra23 = [n for n, d in config["brazos"].items() if d["eje"] == "cra23"]
    brazos_dg15 = [n for n, d in config["brazos"].items() if d["eje"] == "dg15"]

    with sesion_sumo(ARCHIVO_ESCENARIO, usar_gui=args.gui):
        fuente = SumoSource(config)
        actuador = SumoActuator(config)

        print("Capacidad de cada brazo (vehiculos en cola):")
        for nombre, capacidad in fuente.capacidad.items():
            print(f"   {nombre:<6} {capacidad:6.1f}")
        print()

        def cambiar_a(indice, tiempo):
            fase, etiqueta, duracion = SECUENCIA_PRUEBA[indice]
            luces = actuador.aplicar(fase)
            estado = fuente.leer_estado()
            print(
                f"t = {tiempo:5.0f} s -> {etiqueta:<16} '{luces}' por {duracion:>2} s | "
                f"detenidos Cra 23: {estado.detenidos_de(brazos_cra23):>2}  "
                f"Dg 15: {estado.detenidos_de(brazos_dg15):>2}"
            )
            return tiempo + duracion

        tiempo = traci.simulation.getTime()
        indice = 0
        fin_fase = cambiar_a(indice, tiempo)
        segundos_verificados = 0

        while tiempo < DURACION_PRUEBA and traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            tiempo = traci.simulation.getTime()
            actuador.verificar()
            segundos_verificados += 1
            if tiempo >= fin_fase:
                indice = (indice + 1) % len(SECUENCIA_PRUEBA)
                fin_fase = cambiar_a(indice, tiempo)

        estado_final = fuente.leer_estado()
        print(f"\nFin de la prueba en t = {tiempo:.0f} s")
        print(f"Segundos en que se comprobo que SUMO obedecio a Python: {segundos_verificados}")
        print("Cola relativa al final (detenidos / capacidad):")
        for nombre, brazo in estado_final.brazos.items():
            print(f"   {nombre:<6} {brazo.cola_relativa:5.2f}")


if __name__ == "__main__":
    main()
