"""Repite UNA corrida de un barrido en sumo-gui, con la misma semilla y el mismo desfase de la Calle 18.
Sirve para ver con los ojos donde se forma un atasco.

Uso:
  python scripts/ver_corrida.py results/calibracion/validacion_dg15/c01/aforo_valle_manana.sumocfg 4
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.configuracion import cargar_interseccion
from src.simulation.ejecutar_escenario import leer_yaml, simular


def main():
    parser = argparse.ArgumentParser(description="Ver una corrida en sumo-gui (tiempos del semaforo real).")
    parser.add_argument("sumocfg", help="ruta al .sumocfg de la corrida")
    parser.add_argument("semilla", type=int)
    args = parser.parse_args()
    ruta = Path(args.sumocfg).resolve()
    configs = (cargar_interseccion(), leer_yaml("controlador.yaml"), leer_yaml("experimento.yaml"))
    tripinfo = ruta.parent / f"diagnostico_s{args.semilla}_tripinfo.xml"
    _, _, _, cierre = simular(ruta, args.semilla, True, "tiempos_fijos", configs, tripinfo)
    print(cierre)


if __name__ == "__main__":
    main()
