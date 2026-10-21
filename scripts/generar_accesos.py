"""
Genera los TRAMOS DE ACCESO aguas arriba de cada brazo de llegada (calibracion, paso 3).

Problema que resuelve:
  Los brazos de la red son cortos (norte 110 m). Cuando la cola llega al inicio del brazo,
  SUMO no puede insertar mas vehiculos y los deja esperando FUERA de la red (retraso de
  entrada). Al empezar el verde, esa cola "virtual" no avanza como una cola real: el brazo se
  vacia en ~15 s y el resto del verde la linea de pare queda sin vehiculos, aunque haya cientos
  esperando. En la realidad la cola continua por el puente y la linea de pare descarga todo el verde.

Solucion: agregar antes de cada brazo un tramo recto de "longitud_m" (config/calibracion.yaml)
con el mismo numero de carriles, para que la cola se forme DENTRO de la red.
Los brazos originales NO cambian: el estado del agente se sigue midiendo solo en ellos
(como lo haria una camara que ve una zona limitada).

Entrada: sumo/network/acacias_osm.net.xml, config/interseccion.yaml, config/calibracion.yaml
Salida:  sumo/network/accesos.nod.xml y sumo/network/accesos.edg.xml
         (los usa acacias_ajustes.netccfg)

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\generar_accesos.py
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[1]
RED_OSM = CARPETA_TESIS / "sumo" / "network" / "acacias_osm.net.xml"
SALIDA_NODOS = CARPETA_TESIS / "sumo" / "network" / "accesos.nod.xml"
SALIDA_EDGES = CARPETA_TESIS / "sumo" / "network" / "accesos.edg.xml"


def cargar_yaml(nombre):
    with open(CARPETA_TESIS / "config" / nombre, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def main():
    accesos = cargar_yaml("calibracion.yaml").get("accesos", {"activo": False})
    brazos = cargar_yaml("interseccion.yaml")["brazos"]
    raiz = ET.parse(RED_OSM).getroot()
    edges = {e.get("id"): e for e in raiz.findall("edge")}
    nodos = {j.get("id"): j for j in raiz.findall("junction")}

    lineas_nodos = ['<?xml version="1.0" encoding="UTF-8"?>',
                    "<!-- Generado por scripts/generar_accesos.py: NO editar a mano. -->", "<nodes>"]
    lineas_edges = ['<?xml version="1.0" encoding="UTF-8"?>',
                    "<!-- Generado por scripts/generar_accesos.py: NO editar a mano. -->", "<edges>"]
    if accesos["activo"]:
        longitud = float(accesos["longitud_m"])
        for brazo, datos in brazos.items():
            edge = edges.get(datos["edge"])
            if edge is None:
                sys.exit(f"ERROR: el edge {datos['edge']} del brazo {brazo} no existe en {RED_OSM.name}")
            nodo_inicio = nodos[edge.get("from")]
            if nodo_inicio.get("type") != "dead_end":
                sys.exit(f"ERROR: el brazo {brazo} ya tiene algo antes ({nodo_inicio.get('type')}); revisar")
            # Direccion del primer segmento del brazo, invertida: el acceso se prolonga hacia afuera.
            carril = edge.find("lane")
            (x1, y1), (x2, y2) = [tuple(map(float, p.split(","))) for p in carril.get("shape").split()[:2]]
            dx, dy = x1 - x2, y1 - y2
            norma = math.hypot(dx, dy)
            x0, y0 = float(nodo_inicio.get("x")), float(nodo_inicio.get("y"))
            xn, yn = x0 + longitud * dx / norma, y0 + longitud * dy / norma
            numero_carriles = len(edge.findall("lane"))
            velocidad = carril.get("speed")
            lineas_nodos.append(f'    <node id="inicio_acceso_{brazo}" x="{xn:.2f}" y="{yn:.2f}" type="priority"/>')
            lineas_edges.append(f'    <edge id="acceso_{brazo}" from="inicio_acceso_{brazo}" to="{edge.get("from")}" '
                                f'numLanes="{numero_carriles}" speed="{velocidad}" priority="10"/>')
            print(f"acceso_{brazo:<6} {longitud:.0f} m, {numero_carriles} carril(es) -> antes de {datos['edge']}")
    else:
        print("Accesos desactivados en config/calibracion.yaml: se escriben archivos vacios.")
    lineas_nodos.append("</nodes>")
    lineas_edges.append("</edges>")
    SALIDA_NODOS.write_text("\n".join(lineas_nodos) + "\n", encoding="utf-8")
    SALIDA_EDGES.write_text("\n".join(lineas_edges) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
