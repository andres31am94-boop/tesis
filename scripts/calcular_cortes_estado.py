"""
Calcula los CORTES del estado del agente (vacia / baja / media / alta) a partir de las colas reales.

Lee series.csv de las corridas del semaforo real (tiempos fijos) en los 4 escenarios del aforo y toma, cada
segundo de la ventana de medicion, los vehiculos detenidos en la zona de camara del brazo mas cargado de cada eje
(lo mismo que ve el agente). Propone los cortes con cuantiles de esos valores, para que cada nivel aparezca
con frecuencia suficiente y el agente pueda aprender que hacer en cada uno.

Regla:
  - "vacia" = 0 detenidos (primer corte = 1).
  - Los otros cortes = percentiles de los segundos CON cola (> 0), juntando ambos ejes: por defecto 33 y 67
    (4 niveles). Iteracion 6 (2026-10-27): --percentiles 33 67 90 agrega el nivel "muy alta" (5 niveles), porque con
    "alta" = 9 o mas el agente no distinguia una cola de 10 de una de 35 (validacion de aforo_v6, jueves).

Modo "presentes" (iteracion 2): en vez de los detenidos, usa los vehiculos PRESENTES en la zona de camara del eje
que esta en VERDE (solo los segundos de verde). Misma regla para los cortes.

Uso (desde la carpeta tesis; requiere haber corrido los escenarios con la semilla indicada):
  .\\.venv\\Scripts\\python.exe scripts\\calcular_cortes_estado.py --semilla 1
  .\\.venv\\Scripts\\python.exe scripts\\calcular_cortes_estado.py --modo presentes --escenarios aforo_bajo aforo_medio aforo_alto
"""
import argparse
import csv
import sys
from bisect import bisect_right
from pathlib import Path

import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[1]
ESCENARIOS = ["aforo_bajo", "aforo_valle_manana", "aforo_medio", "aforo_alto"]
NOMBRES_NIVEL = ["vacia", "baja", "media", "alta", "muy_alta"]


def percentil(valores_ordenados, p):
    return valores_ordenados[round(p / 100 * (len(valores_ordenados) - 1))]


def main():
    parser = argparse.ArgumentParser(description="Propone los cortes del estado con las colas reales.")
    parser.add_argument("--semilla", type=int, default=1)
    parser.add_argument("--modo", choices=["detenidos", "presentes"], default="detenidos")
    parser.add_argument("--escenarios", nargs="+", default=ESCENARIOS)
    parser.add_argument("--percentiles", nargs="+", type=float, default=[33, 67],
                        help="percentiles de los segundos con cola para los cortes despues de 'vacia' (max. 3)")
    args = parser.parse_args()
    columna = "detenidos_zona" if args.modo == "detenidos" else "vehiculos_zona"

    with open(CARPETA_TESIS / "config" / "interseccion.yaml", encoding="utf-8") as archivo:
        brazos = yaml.safe_load(archivo)["brazos"]
    with open(CARPETA_TESIS / "config" / "experimento.yaml", encoding="utf-8") as archivo:
        experimento = yaml.safe_load(archivo)
    inicio, fin = experimento["calentamiento_s"], experimento["duracion_demanda_s"]
    ejes = {}
    for nombre, datos in brazos.items():
        ejes.setdefault(datos["eje"], []).append(nombre)

    valores = {eje: [] for eje in ejes}
    for escenario in args.escenarios:
        ruta = CARPETA_TESIS / "results" / escenario / "tiempos_fijos" / f"semilla_{args.semilla}" / "series.csv"
        if not ruta.exists():
            sys.exit(f"ERROR: falta {ruta}. Corre primero el escenario {escenario} con la semilla {args.semilla}.")
        with open(ruta, encoding="utf-8") as archivo:
            filas = [f for f in csv.DictReader(archivo) if inicio <= float(f["tiempo"]) < fin]
        if f"{columna}_norte" not in filas[0]:
            sys.exit(f"ERROR: {ruta} no tiene columnas {columna}_*; vuelve a correr el escenario.")
        print(f"\n{escenario}:")
        for eje, nombres in ejes.items():
            propias = filas if args.modo == "detenidos" else [f for f in filas if f["fase"] == f"verde_{eje}"]
            serie = sorted(max(int(f[f"{columna}_{n}"]) for n in nombres) for f in propias)
            valores[eje] += serie
            print(f"  {eje:<6} cero {100 * serie.count(0) / len(serie):3.0f} % | p50 {percentil(serie, 50):3d} | "
                  f"p75 {percentil(serie, 75):3d} | p90 {percentil(serie, 90):3d} | p99 {percentil(serie, 99):3d} | "
                  f"max {serie[-1]:3d}")

    con_cola = sorted(v for eje in valores for v in valores[eje] if v > 0)
    if len(args.percentiles) > len(NOMBRES_NIVEL) - 2:
        sys.exit(f"ERROR: como maximo {len(NOMBRES_NIVEL) - 2} percentiles")
    cortes = [1] + [percentil(con_cola, p) for p in args.percentiles]
    cortes[1] = max(2, cortes[1])
    if cortes != sorted(set(cortes)):
        sys.exit(f"ERROR: los cortes calculados no son crecientes: {cortes}")
    print(f"\nCortes propuestos ({'detenidos' if args.modo == 'detenidos' else 'vehiculos presentes del eje en verde'} "
          f"en la zona de camara): {cortes}")
    print("Frecuencia de cada nivel con esos cortes (todos los escenarios):")
    for eje, serie in valores.items():
        conteo = [0] * (len(cortes) + 1)
        for v in serie:
            conteo[bisect_right(cortes, v)] += 1
        print(f"  {eje:<6} " + "  ".join(f"{NOMBRES_NIVEL[i]} {100 * c / len(serie):3.0f} %" for i, c in enumerate(conteo)))


if __name__ == "__main__":
    main()
