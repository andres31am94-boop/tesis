"""
Genera el archivo de rutas de SUMO (.rou.xml) a partir de dos tablas CSV:
  - flujos: vehiculos/hora por brazo de llegada y movimiento (recto / derecha)
  - tipos:  proporcion de carro, moto, bus y camion

Uso (desde la carpeta tesis):
  python scripts/generar_demanda.py --flujos sumo/demanda/prueba_flujos.csv \
      --tipos sumo/demanda/prueba_tipos.csv --salida sumo/routes/prueba.rou.xml --duracion 3600

Las llegadas son aleatorias: cada segundo aparece un vehiculo con probabilidad
(vehiculos_hora / 3600). El azar lo controla la semilla de SUMO (--seed en el .sumocfg),
asi que la misma semilla reproduce exactamente el mismo trafico.
"""
import argparse
import csv
import sys
from pathlib import Path

# Edges de la red acacias.net.xml (verificados el 2026-10-06).
# (brazo de llegada, movimiento) -> (edge de llegada, edge de salida)
MOVIMIENTOS = {
    ("norte", "recto"):   ("-642480900",  "642480899"),
    ("norte", "derecha"): ("-642480900",  "1414166244"),
    ("sur", "recto"):     ("807940779",   "1414166243"),
    ("sur", "derecha"):   ("807940779",   "1414166246#0"),
    ("este", "recto"):    ("816899410#0", "1414166244"),
    ("este", "derecha"):  ("816899410#0", "1414166243"),
    ("oeste", "recto"):   ("44411778#0",  "1414166246#0"),
    ("oeste", "derecha"): ("44411778#0",  "642480899"),
}

# Tipos de vehiculo. vClass y guiShape son nombres predefinidos de SUMO.
# Las demas propiedades (largo, aceleracion, etc.) usan los valores por defecto de SUMO para cada vClass.
TIPOS_SUMO = {
    "carro":  {"vClass": "passenger",  "guiShape": "passenger"},
    "moto":   {"vClass": "motorcycle", "guiShape": "motorcycle"},
    "bus":    {"vClass": "bus",        "guiShape": "bus"},
    "camion": {"vClass": "truck",      "guiShape": "truck"},
}

TOLERANCIA_SUMA = 1e-6


def leer_flujos(ruta):
    flujos = []
    with open(ruta, newline="", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            clave = (fila["brazo_llegada"].strip().lower(), fila["movimiento"].strip().lower())
            if clave not in MOVIMIENTOS:
                sys.exit(f"ERROR: movimiento no permitido o mal escrito en {ruta}: {clave}")
            vehiculos_hora = float(fila["vehiculos_hora"])
            if vehiculos_hora < 0 or vehiculos_hora > 3600:
                sys.exit(f"ERROR: vehiculos_hora fuera de rango (0-3600) en {clave}: {vehiculos_hora}")
            flujos.append((clave, vehiculos_hora))
    return flujos


def leer_tipos(ruta):
    tipos = {}
    with open(ruta, newline="", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            tipo = fila["tipo"].strip().lower()
            if tipo not in TIPOS_SUMO:
                sys.exit(f"ERROR: tipo de vehiculo desconocido en {ruta}: {tipo}")
            tipos[tipo] = float(fila["proporcion"])
    suma = sum(tipos.values())
    if abs(suma - 1.0) > TOLERANCIA_SUMA:
        sys.exit(f"ERROR: las proporciones de {ruta} suman {suma}, deben sumar 1.0")
    return tipos


def generar_xml(flujos, tipos, duracion, origen_flujos, origen_tipos):
    lineas = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!-- Generado por scripts/generar_demanda.py: NO editar a mano. -->",
        f"<!-- Flujos: {origen_flujos} | Tipos: {origen_tipos} | Duracion: {duracion} s -->",
        "<routes>",
        '    <vTypeDistribution id="mezcla">',
    ]
    for tipo, proporcion in tipos.items():
        atributos = TIPOS_SUMO[tipo]
        lineas.append(
            f'        <vType id="{tipo}" vClass="{atributos["vClass"]}" '
            f'guiShape="{atributos["guiShape"]}" probability="{proporcion}"/>'
        )
    lineas.append("    </vTypeDistribution>")
    for (brazo, movimiento), vehiculos_hora in flujos:
        if vehiculos_hora == 0:
            continue
        edge_llegada, edge_salida = MOVIMIENTOS[(brazo, movimiento)]
        probabilidad = vehiculos_hora / 3600.0
        lineas.append(
            f'    <flow id="{brazo}_{movimiento}" type="mezcla" begin="0" end="{duracion}" '
            f'from="{edge_llegada}" to="{edge_salida}" probability="{probabilidad:.6f}" '
            f'departLane="best" departSpeed="max"/>'
        )
    lineas.append("</routes>")
    return "\n".join(lineas) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Genera el .rou.xml de SUMO desde tablas CSV.")
    parser.add_argument("--flujos", required=True)
    parser.add_argument("--tipos", required=True)
    parser.add_argument("--salida", required=True)
    parser.add_argument("--duracion", type=int, default=3600, help="segundos simulados con llegadas")
    args = parser.parse_args()

    flujos = leer_flujos(args.flujos)
    tipos = leer_tipos(args.tipos)
    xml = generar_xml(flujos, tipos, args.duracion, args.flujos, args.tipos)
    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(xml, encoding="utf-8")

    total = sum(v for _, v in flujos)
    print(f"Archivo generado: {args.salida}")
    print(f"Flujos: {len(flujos)} | Demanda total: {total:.0f} vehiculos/hora")


if __name__ == "__main__":
    main()
