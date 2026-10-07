"""
Ejecuta UNA corrida completa: escenario de SUMO + controlador + capa de seguridad,
y guarda las metricas.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe -m src.simulation.ejecutar_escenario --escenario prueba --semilla 42
  (agregar --gui para verla en sumo-gui)

Resultados en results/<escenario>/<controlador>/semilla_<n>/:
  resumen.json     metricas de la corrida + parametros usados (reproducibilidad)
  series.csv       fase y detenidos por brazo en cada segundo
  tripinfo.xml     salida original de SUMO (un registro por vehiculo)
"""
import argparse
import csv
import json
import platform
from datetime import datetime
from pathlib import Path

import traci
import yaml

from src.common.configuracion import CARPETA_TESIS, cargar_interseccion
from src.controller.safety_guard import SafetyGuard
from src.controller.tiempos_fijos import ControladorTiemposFijos
from src.metrics.metricas import leer_tripinfo, resumir_colas, resumir_verdes, resumir_viajes
from src.simulation.sesion_sumo import sesion_sumo
from src.simulation.sumo_actuator import SumoActuator
from src.simulation.sumo_source import SumoSource

CARPETA_CONFIG = CARPETA_TESIS / "config"
CARPETA_ESCENARIOS = CARPETA_TESIS / "sumo" / "configs"
CARPETA_RESULTADOS = CARPETA_TESIS / "results"
CONTROLADORES = ["tiempos_fijos"]  # el agente se agregara en la Fase 6


def leer_yaml(nombre):
    with open(CARPETA_CONFIG / nombre, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def crear_controlador(nombre, config_controlador, guard):
    if nombre == "tiempos_fijos":
        return ControladorTiemposFijos.desde_config(config_controlador, guard)
    raise ValueError(f"Controlador desconocido: {nombre}. Disponibles: {CONTROLADORES}")


def simular(archivo_escenario, semilla, usar_gui, nombre_controlador, configs, ruta_tripinfo):
    """Corre la simulacion y devuelve (filas por segundo, guard, info de cierre)."""
    config_interseccion, config_controlador, config_experimento = configs
    limite = config_experimento["duracion_demanda_s"] + config_experimento["margen_vaciado_s"]
    filas = []

    with sesion_sumo(archivo_escenario, usar_gui=usar_gui, semilla=semilla,
                     argumentos_extra=["--tripinfo-output", ruta_tripinfo]):
        fuente = SumoSource(config_interseccion)
        actuador = SumoActuator(config_interseccion)
        guard = SafetyGuard.desde_config(config_controlador)
        controlador = crear_controlador(nombre_controlador, config_controlador, guard)

        tiempo = traci.simulation.getTime()
        fase = guard.iniciar(tiempo)
        actuador.aplicar(fase)

        while traci.simulation.getMinExpectedNumber() > 0 and tiempo < limite:
            traci.simulationStep()
            tiempo = traci.simulation.getTime()
            actuador.verificar()

            estado = fuente.leer_estado()
            fila = {"tiempo": tiempo, "fase": fase}
            fila.update({f"detenidos_{n}": b.detenidos for n, b in estado.brazos.items()})
            filas.append(fila)

            nueva_fase = guard.paso(tiempo, controlador.pedir_cambio(tiempo, estado))
            if nueva_fase != fase:
                actuador.aplicar(nueva_fase)
                fase = nueva_fase

        cierre = {
            "tiempo_final_s": tiempo,
            "vehiculos_sin_terminar": traci.simulation.getMinExpectedNumber(),
            "version_sumo": traci.getVersion()[1],
        }
    return filas, guard, cierre


def main():
    parser = argparse.ArgumentParser(description="Ejecuta un escenario y guarda sus metricas.")
    parser.add_argument("--escenario", required=True, help="nombre del .sumocfg en sumo/configs (sin extension)")
    parser.add_argument("--controlador", default="tiempos_fijos", choices=CONTROLADORES)
    parser.add_argument("--semilla", type=int, required=True)
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()

    archivo_escenario = CARPETA_ESCENARIOS / f"{args.escenario}.sumocfg"
    configs = (cargar_interseccion(), leer_yaml("controlador.yaml"), leer_yaml("experimento.yaml"))
    config_interseccion, config_controlador, config_experimento = configs

    carpeta_salida = CARPETA_RESULTADOS / args.escenario / args.controlador / f"semilla_{args.semilla}"
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    ruta_tripinfo = carpeta_salida / "tripinfo.xml"

    print(f"Escenario: {args.escenario} | controlador: {args.controlador} | semilla: {args.semilla}")
    filas, guard, cierre = simular(archivo_escenario, args.semilla, args.gui, args.controlador, configs, ruta_tripinfo)

    inicio = config_experimento["calentamiento_s"]
    fin = config_experimento["duracion_demanda_s"]
    brazos = list(config_interseccion["brazos"])
    metricas = {}
    metricas.update(resumir_viajes(leer_tripinfo(ruta_tripinfo), inicio, fin))
    metricas.update(resumir_colas(filas, brazos, inicio, fin))
    metricas.update(resumir_verdes(guard.historial_verdes, inicio, fin))
    metricas["cambios_rechazados"] = guard.cambios_rechazados
    metricas["cambios_forzados"] = guard.cambios_forzados

    with open(carpeta_salida / "series.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    resumen = {
        "escenario": args.escenario,
        "controlador": args.controlador,
        "semilla": args.semilla,
        "ventana_medicion_s": [inicio, fin],
        "metricas": metricas,
        "cierre": cierre,
        "parametros": {"controlador": config_controlador, "experimento": config_experimento},
        "entorno": {"python": platform.python_version(), "fecha": datetime.now().isoformat(timespec="seconds")},
    }
    with open(carpeta_salida / "resumen.json", "w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, indent=2, ensure_ascii=False)

    print(f"\nResultados guardados en: {carpeta_salida}")
    print(f"Ventana de medicion: {inicio}-{fin} s | fin de simulacion: {cierre['tiempo_final_s']:.0f} s | "
          f"vehiculos sin terminar: {cierre['vehiculos_sin_terminar']}")
    print("\nMetricas:")
    for clave, valor in metricas.items():
        print(f"   {clave:<32} {valor:10.2f}" if isinstance(valor, float) else f"   {clave:<32} {valor:>10}")


if __name__ == "__main__":
    main()
