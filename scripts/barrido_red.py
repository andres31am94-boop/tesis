"""
Barrido de sensibilidad de la RED (paso 6 de calibracion).

Para cada combinacion de config/barrido_red.yaml (posicion del cambio de carriles x forma de juntarse) construye una
red propia con netconvert (mismos pasos que sumo/network: geometria + conexiones), comprueba que el semaforo siga con
12 movimientos, corre el semaforo REAL (tiempos fijos) y calcula el GEH por brazo.
No modifica la red oficial (sumo/network/acacias.net.xml). Salida en results/calibracion/barrido_red/.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\barrido_red.py
"""
import csv
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import sumolib

from barrido_calibracion import (BRAZOS, CARPETA_TESIS, GEH_MAXIMO, cargar_interseccion, flujos_aforo,  # noqa: E402
                                 flujos_simulados, geh, leer_yaml, simular)

CARPETA_RED = CARPETA_TESIS / "sumo" / "network"
CARPETA_SALIDA = CARPETA_TESIS / "results" / "calibracion" / "barrido_red"
MOVIMIENTOS_SEMAFORO = 12


def ajustes_variante(posicion, tipo_union):
    """Copia de ajustes.edg.xml cambiando solo la posicion del cambio de carriles y la forma de juntarse."""
    texto = (CARPETA_RED / "ajustes.edg.xml").read_text(encoding="utf-8")
    texto, n1 = re.subn(r'<split pos="-[0-9.]+" lanes="0 1"', f'<split pos="-{posicion}" lanes="0 1"', texto)
    tipo = "zipper" if tipo_union == "zipper" else "priority"
    texto, n2 = re.subn(r'<split pos="[0-9.]+" lanes="0" type="\w+"', f'<split pos="{posicion}" lanes="0" type="{tipo}"', texto)
    if (n1, n2) != (1, 1):
        sys.exit(f"ERROR: no se encontraron los cambios de carril en ajustes.edg.xml ({n1}, {n2})")
    return texto


def conexiones_extra(tipo_union):
    """Para 'carril_termina' el carril izquierdo de la salida no continua: sus vehiculos deben cambiarse antes."""
    if tipo_union == "zipper":
        return None
    return ('<connections>\n'
            '    <delete from="1414166243" to="puente_hacia_villavicencio" fromLane="1" toLane="0"/>\n'
            '</connections>\n')


def construir_red(carpeta, posicion, tipo_union):
    netconvert = sumolib.checkBinary("netconvert")
    ruta_ajustes = carpeta / "ajustes.edg.xml"
    ruta_ajustes.write_text(ajustes_variante(posicion, tipo_union), encoding="utf-8")
    ruta_geometria = carpeta / "geometria.net.xml"
    ruta_red = carpeta / "red.net.xml"
    subprocess.run([netconvert, "-c", str(CARPETA_RED / "acacias_ajustes.netccfg"),
                    "--edge-files", f"{CARPETA_RED / 'accesos.edg.xml'},{ruta_ajustes}",
                    "--output-file", str(ruta_geometria)], check=True)
    archivos_conexiones = [str(CARPETA_RED / "correcciones.con.xml")]
    extra = conexiones_extra(tipo_union)
    if extra:
        ruta_extra = carpeta / "union.con.xml"
        ruta_extra.write_text(extra, encoding="utf-8")
        archivos_conexiones.append(str(ruta_extra))
    subprocess.run([netconvert, "-c", str(CARPETA_RED / "acacias_conexiones.netccfg"),
                    "--sumo-net-file", str(ruta_geometria), "--connection-files", ",".join(archivos_conexiones),
                    "--output-file", str(ruta_red)], check=True)
    semaforo = cargar_interseccion()["semaforo_id"]
    movimientos = [c for c in ET.parse(ruta_red).getroot().iter("connection") if c.get("tl") == semaforo]
    if len(movimientos) != MOVIMIENTOS_SEMAFORO:
        sys.exit(f"ERROR: la red {ruta_red} tiene {len(movimientos)} movimientos en el semaforo (se esperan 12)")
    return ruta_red


def preparar_config(escenario, ruta_red, carpeta):
    texto = (CARPETA_TESIS / "sumo" / "configs" / f"{escenario}.sumocfg").read_text(encoding="utf-8")
    texto = texto.replace("../network/acacias.net.xml", ruta_red.as_posix())
    texto = texto.replace(f"../routes/{escenario}.rou.xml",
                          (CARPETA_TESIS / "sumo" / "routes" / f"{escenario}.rou.xml").as_posix())
    ruta = carpeta / f"{escenario}.sumocfg"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def main():
    barrido = leer_yaml("barrido_red.yaml")
    configs = (cargar_interseccion(), leer_yaml("controlador.yaml"), leer_yaml("experimento.yaml"))
    inicio, fin = configs[2]["calentamiento_s"], configs[2]["duracion_demanda_s"]
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    filas, descripcion = [], {}
    variantes = [(p, t) for t in barrido["tipos_union"] for p in barrido["posiciones_cambio_m"]]
    print(f"{len(variantes)} redes x {len(barrido['escenarios'])} escenarios, semilla {barrido['semilla']}")
    for numero, (posicion, tipo_union) in enumerate(variantes, start=1):
        nombre = f"r{numero:02d}"
        descripcion[nombre] = {"posicion_cambio_m": posicion, "tipo_union": tipo_union}
        carpeta = CARPETA_SALIDA / nombre
        carpeta.mkdir(exist_ok=True)
        ruta_red = construir_red(carpeta, posicion, tipo_union)
        for escenario in barrido["escenarios"]:
            reloj = time.time()
            ruta_tripinfo = carpeta / f"{escenario}_tripinfo.xml"
            _, _, _, cierre = simular(preparar_config(escenario, ruta_red, carpeta), barrido["semilla"], False,
                                      "tiempos_fijos", configs, ruta_tripinfo)
            simulado, contado = flujos_simulados(ruta_tripinfo, inicio, fin), flujos_aforo(escenario)
            valores = {b: geh(simulado[b], contado[b]) for b in BRAZOS}
            for b in BRAZOS:
                filas.append({"red": nombre, "posicion_cambio_m": posicion, "tipo_union": tipo_union,
                              "escenario": escenario, "brazo": b, "aforo_veh_h": round(contado[b]),
                              "simulado_veh_h": round(simulado[b]), "geh": round(valores[b], 2),
                              "sin_terminar": cierre["vehiculos_sin_terminar"]})
            cumplen = sum(v < GEH_MAXIMO for v in valores.values())
            print(f"{nombre} {posicion:>5} m {tipo_union:<15}| {escenario:<11} | " +
                  " ".join(f"{b} {simulado[b]:5.0f} (GEH {valores[b]:4.1f})" for b in BRAZOS) +
                  f" | cumplen {cumplen}/4 | {time.time() - reloj:4.0f} s")
    with open(CARPETA_SALIDA / "redes.json", "w", encoding="utf-8") as archivo:
        json.dump({"semilla": barrido["semilla"], "redes": descripcion}, archivo, indent=2)
    with open(CARPETA_SALIDA / "resultados.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"\nGuardado en {CARPETA_SALIDA}")


if __name__ == "__main__":
    main()
