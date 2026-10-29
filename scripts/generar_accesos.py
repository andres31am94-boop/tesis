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
SALIDA_PROGRAMA_CALLE18 = CARPETA_TESIS / "sumo" / "network" / "calle18.tll.xml"
ANCHO_CARRIL_CRA23_M = 3.5  # mismo ancho medido de la Cra 23 (ajustes.edg.xml)


def cargar_yaml(nombre):
    with open(CARPETA_TESIS / "config" / nombre, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def escribir_programa_calle18(calle18):
    """Programa fijo medido del semaforo de la Calle 18 (archivo adicional que carga SUMO).
    Los 2 movimientos (un sentido y el otro de la Cra 23) tienen siempre la misma luz.
    El semaforo (tl="calle18") esta en el nodo donde termina el puente, trasladado a la Calle 18."""
    t = calle18["tiempos_cra23_s"]
    SALIDA_PROGRAMA_CALLE18.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!-- Generado por scripts/generar_accesos.py desde config/semaforo_calle18.yaml: NO editar a mano. -->\n"
        "<additional>\n"
        '    <tlLogic id="calle18" type="static" programID="medido" offset="0">\n'
        f'        <phase duration="{t["verde"]}" state="GG"/>\n'
        f'        <phase duration="{t["amarillo"]}" state="yy"/>\n'
        f'        <phase duration="{t["rojo"]}" state="rr"/>\n'
        "    </tlLogic>\n"
        "</additional>\n", encoding="utf-8")


def main():
    accesos = cargar_yaml("calibracion.yaml").get("accesos", {"activo": False})
    calle18 = cargar_yaml("semaforo_calle18.yaml")
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
            id_llegada = datos["edges"][0]  # tramo de llegada original de OSM (ver config/interseccion.yaml)
            edge = edges.get(id_llegada)
            if edge is None:
                sys.exit(f"ERROR: el edge {id_llegada} del brazo {brazo} no existe en {RED_OSM.name}")
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
            if brazo == "norte" and calle18["activo"]:
                # Semaforo de la Calle 18 sobre el acceso norte, a distancia_desde_cruce_m de nuestra linea de pare.
                largo_brazo = float(carril.get("length"))
                d = float(calle18["distancia_desde_cruce_m"]) - largo_brazo  # desde el inicio del brazo norte
                if not 0 < d < longitud:
                    sys.exit(f"ERROR: la Calle 18 quedaria a {d:.0f} m del brazo norte (debe estar entre 0 y {longitud:.0f})")
                d_fin = d + float(calle18["largo_salida_m"])
                xc, yc = x0 + d * dx / norma, y0 + d * dy / norma
                xf, yf = x0 + d_fin * dx / norma, y0 + d_fin * dy / norma
                nodo_puente = edge.get("from")
                carriles = int(calle18["carriles_por_sentido"])
                comunes = f'numLanes="{carriles}" speed="{velocidad}" priority="10" width="{ANCHO_CARRIL_CRA23_M}"'
                # 2026-10-27: el semaforo de la Calle 18 es el MISMO nodo donde termina el puente en OSM ({nodo_puente}),
                # trasladado a la posicion de la Calle 18. Antes habia un nodo aparte y dos tramos de 150 m
                # (desde_calle18 / hacia_calle18) unidos al puente por un cruce interno de 0.1 m: un vehiculo
                # desplazado de lado por las motos quedaba trabado ahi (atascos de validacion_dg15 s4 y aforo_v5).
                # Ahora el puente llega de forma continua hasta la Calle 18 (forma en puente_forma.edg.xml).
                lineas_nodos.append(f'    <node id="{nodo_puente}" x="{xc:.2f}" y="{yc:.2f}" type="traffic_light" tl="calle18"/>')
                lineas_nodos.append(f'    <node id="fin_norte" x="{xf:.2f}" y="{yf:.2f}" type="priority"/>')
                lineas_edges.append(f'    <edge id="acceso_norte" from="inicio_acceso_norte" to="{nodo_puente}" '
                                    f'numLanes="{numero_carriles}" speed="{velocidad}" priority="10"/>')
                lineas_edges.append(f'    <edge id="despues_calle18" from="{nodo_puente}" to="fin_norte" {comunes}/>')
                escribir_programa_calle18(calle18)
                print(f"acceso_norte {longitud:.0f} m con el semaforo de la Calle 18 a {d:.0f} m antes del brazo norte "
                      f"({calle18['distancia_desde_cruce_m']} m de la linea de pare); salida de {calle18['largo_salida_m']} m")
                continue
            lineas_edges.append(f'    <edge id="acceso_{brazo}" from="inicio_acceso_{brazo}" to="{edge.get("from")}" '
                                f'numLanes="{numero_carriles}" speed="{velocidad}" priority="10"/>')
            print(f"acceso_{brazo:<6} {longitud:.0f} m, {numero_carriles} carril(es) -> antes de {id_llegada}")
    else:
        print("Accesos desactivados en config/calibracion.yaml: se escriben archivos vacios.")
    lineas_nodos.append("</nodes>")
    lineas_edges.append("</edges>")
    SALIDA_NODOS.write_text("\n".join(lineas_nodos) + "\n", encoding="utf-8")
    SALIDA_EDGES.write_text("\n".join(lineas_edges) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
