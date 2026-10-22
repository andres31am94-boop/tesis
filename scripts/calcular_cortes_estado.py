"""
Calcula los CORTES del estado del agente (vacia / baja / media / alta) a partir de las colas reales.

Lee series.csv de las corridas del semaforo real (tiempos fijos) en los 4 escenarios del aforo y toma, cada
segundo de la ventana de medicion, los vehiculos detenidos en la zona de camara del brazo mas cargado de cada eje
(lo mismo que ve el agente). Propone los cortes con cuantiles de esos valores, para que cada nivel aparezca
con frecuencia suficiente y el agente pueda aprender que hacer en cada uno.

Regla:
  - "vacia" = 0 detenidos (primer corte = 1).
  - Los otros dos cortes = percentiles 33 y 67 de los segundos CON cola (> 0), juntando ambos ejes.

Uso (desde la carpeta tesis; requiere haber corrido los 4 escenarios con la semilla indicada):
  .\\.venv\\Scripts\\python.exe scripts\\calcular_cortes_estado.py --semilla 1
"""
import argparse
import csv
import sys
from bisect import bisect_right
from pathlib import Path

import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[1]
ESCENARIOS = ["aforo_bajo", "aforo_valle_manana", "aforo_medio", "aforo_alto"]
NOMBRES_NIVEL = ["vacia", "baja", "media", "alta"]


def percentil(valores_ordenados, p):
    return valores_ordenados[round(p / 100 * (len(valores_ordenados) - 1))]


def main():
    parser = argparse.ArgumentParser(description="Propone los cortes del estado con las colas reales.")
    parser.add_argument("--semilla", type=int, default=1)
    args = parser.parse_args()

    with open(CARPETA_TESIS / "config" / "interseccion.yaml", encoding="utf-8") as archivo:
        brazos = yaml.safe_load(archivo)["brazos"]
    with open(CARPETA_TESIS / "config" / "experimento.yaml", encoding="utf-8") as archivo:
        experimento = yaml.safe_load(archivo)
    inicio, fin = experimento["calentamiento_s"], experimento["duracion_demanda_s"]
    ejes = {}
    for nombre, datos in brazos.items():
        ejes.setdefault(datos["eje"], []).append(nombre)

    valores = {eje: [] for eje in ejes}
    for escenario in ESCENARIOS:
        ruta = CARPETA_TESIS / "results" / escenario / "tiempos_fijos" / f"semilla_{args.semilla}" / "series.csv"
        if not ruta.exists():
            sys.exit(f"ERROR: falta {ruta}. Corre primero el escenario {escenario} con la semilla {args.semilla}.")
        with open(ruta, encoding="utf-8") as archivo:
            filas = [f for f in csv.DictReader(archivo) if inicio <= float(f["tiempo"]) < fin]
        if "detenidos_zona_norte" not in filas[0]:
            sys.exit(f"ERROR: {ruta} no tiene columnas detenidos_zona_*; vuelve a correr el escenario.")
        print(f"\n{escenario}:")
        for eje, nombres in ejes.items():
            serie = sorted(max(int(f[f"detenidos_zona_{n}"]) for n in nombres) for f in filas)
            valores[eje] += serie
            print(f"  {eje:<6} cero {100 * serie.count(0) / len(serie):3.0f} % | p50 {percentil(serie, 50):3d} | "
                  f"p75 {percentil(serie, 75):3d} | p90 {percentil(serie, 90):3d} | p99 {percentil(serie, 99):3d} | "
                  f"max {serie[-1]:3d}")

    con_cola = sorted(v for eje in valores for v in valores[eje] if v > 0)
    cortes = [1, max(2, percentil(con_cola, 33)), percentil(con_cola, 67)]
    if cortes != sorted(set(cortes)):
        sys.exit(f"ERROR: los cortes calculados no son crecientes: {cortes}")
    print(f"\nCortes propuestos (detenidos en la zona de camara): {cortes}")
    print("Frecuencia de cada nivel con esos cortes (todos los escenarios):")
    for eje, serie in valores.items():
        conteo = [0] * (len(cortes) + 1)
        for v in serie:
            conteo[bisect_right(cortes, v)] += 1
        print(f"  {eje:<6} " + "  ".join(f"{NOMBRES_NIVEL[i]} {100 * c / len(serie):3.0f} %" for i, c in enumerate(conteo)))


if __name__ == "__main__":
    main()
