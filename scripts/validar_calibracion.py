"""
Valida la CALIBRACION del modelo: compara, brazo por brazo, el flujo que la simulacion
logra atender con el flujo contado en el aforo (vehiculos que cruzaron la linea de pare).

Indicador GEH (comun en calibracion de modelos de trafico):
    GEH = sqrt( 2 * (M - C)^2 / (M + C) )      M = flujo simulado, C = flujo contado (veh/h)
Criterio usado: GEH < 5 en cada brazo.

Requiere haber corrido antes el escenario con el semaforo real (tiempos_fijos), por ejemplo:
  .\\.venv\\Scripts\\python.exe -m src.simulation.ejecutar_escenario --escenario aforo_alto --semilla 1
Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\validar_calibracion.py --escenario aforo_alto --semilla 1
"""
import argparse
import csv
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
BRAZOS = ["norte", "sur", "este", "oeste"]
GEH_MAXIMO = 5.0


def geh(simulado, contado):
    if simulado + contado == 0:
        return 0.0
    return math.sqrt(2 * (simulado - contado) ** 2 / (simulado + contado))


def main():
    parser = argparse.ArgumentParser(description="Compara flujos simulados con el aforo (GEH).")
    parser.add_argument("--escenario", required=True)
    parser.add_argument("--semilla", type=int, required=True)
    parser.add_argument("--controlador", default="tiempos_fijos")
    args = parser.parse_args()

    contado = {b: 0.0 for b in BRAZOS}
    with open(CARPETA_TESIS / "sumo" / "demanda" / f"{args.escenario}_flujos.csv", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            contado[fila["brazo_llegada"]] += float(fila["vehiculos_hora"])

    carpeta = CARPETA_TESIS / "results" / args.escenario / args.controlador / f"semilla_{args.semilla}"
    with open(carpeta / "resumen.json", encoding="utf-8") as archivo:
        inicio, fin = json.load(archivo)["ventana_medicion_s"]
    horas = (fin - inicio) / 3600.0

    atendidos = {b: 0 for b in BRAZOS}
    for viaje in ET.parse(carpeta / "tripinfo.xml").getroot().iter("tripinfo"):
        brazo = viaje.get("id").split("_")[0]          # los ids son <brazo>_<movimiento>_<tipo>.<n>
        if brazo in atendidos and inicio <= float(viaje.get("arrival")) < fin:
            atendidos[brazo] += 1

    print(f"Calibracion: {args.escenario} | {args.controlador} | semilla {args.semilla} | ventana {inicio}-{fin} s")
    print(f"{'brazo':<7}{'aforo (veh/h)':>15}{'simulado (veh/h)':>18}{'diferencia':>12}{'GEH':>7}  resultado")
    cumplen = 0
    for brazo in BRAZOS:
        simulado = atendidos[brazo] / horas
        valor = geh(simulado, contado[brazo])
        ok = valor < GEH_MAXIMO
        cumplen += ok
        print(f"{brazo:<7}{contado[brazo]:>15.0f}{simulado:>18.0f}{(simulado - contado[brazo]) / contado[brazo]:>11.0%}"
              f"{valor:>7.1f}  {'OK' if ok else 'NO CUMPLE'}")
    print(f"\nBrazos que cumplen GEH < {GEH_MAXIMO:.0f}: {cumplen} de {len(BRAZOS)}")
    if cumplen < len(BRAZOS):
        sys.exit(1)


if __name__ == "__main__":
    main()
