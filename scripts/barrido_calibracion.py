"""
Barrido de calibracion (paso 4).

Corre el semaforo REAL (tiempos fijos) con todas las combinaciones de parametros de
config/barrido_calibracion.yaml y calcula el GEH de cada brazo contra el aforo.
No modifica los escenarios oficiales: cada combinacion escribe sus propios archivos en
results/calibracion/barrido/<combinacion>/.

Salida:
  results/calibracion/barrido/combinaciones.json   que parametros tiene cada combinacion
  results/calibracion/barrido/resultados.csv       combinacion, escenario, brazo, aforo, simulado, GEH

Uso (desde la carpeta tesis; puede tardar varios minutos):
  .\\.venv\\Scripts\\python.exe scripts\\barrido_calibracion.py
"""
import csv
import itertools
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))  # para importar src.*

from src.common.configuracion import cargar_interseccion  # noqa: E402
from src.simulation.ejecutar_escenario import leer_yaml, simular  # noqa: E402

CARPETA_BARRIDO = CARPETA_TESIS / "results" / "calibracion" / "barrido"
BRAZOS = ["norte", "sur", "este", "oeste"]
GEH_MAXIMO = 5.0


def geh(simulado, contado):
    return 0.0 if simulado + contado == 0 else (2 * (simulado - contado) ** 2 / (simulado + contado)) ** 0.5


def flujos_aforo(escenario):
    contado = {b: 0.0 for b in BRAZOS}
    with open(CARPETA_TESIS / "sumo" / "demanda" / f"{escenario}_flujos.csv", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            contado[fila["brazo_llegada"]] += float(fila["vehiculos_hora"])
    return contado


def flujos_simulados(ruta_tripinfo, inicio, fin):
    """Igual que scripts/validar_calibracion.py: vehiculos que terminaron dentro de la ventana."""
    atendidos = {b: 0 for b in BRAZOS}
    for viaje in ET.parse(ruta_tripinfo).getroot().iter("tripinfo"):
        brazo = viaje.get("id").split("_")[0]
        if brazo in atendidos and inicio <= float(viaje.get("arrival")) < fin:
            atendidos[brazo] += 1
    horas = (fin - inicio) / 3600.0
    return {b: n / horas for b, n in atendidos.items()}


def preparar_escenario(escenario, parametros, carpeta):
    """Copia rutas y .sumocfg del escenario oficial cambiando solo los atributos de los vType."""
    rutas = ET.parse(CARPETA_TESIS / "sumo" / "routes" / f"{escenario}.rou.xml")
    for vtype in rutas.getroot().iter("vType"):
        for (tipo, atributo), valor in parametros.items():
            if vtype.get("id") == tipo:
                vtype.set(atributo, str(valor))
    ruta_rutas = carpeta / f"{escenario}.rou.xml"
    rutas.write(ruta_rutas, encoding="utf-8", xml_declaration=True)

    texto = (CARPETA_TESIS / "sumo" / "configs" / f"{escenario}.sumocfg").read_text(encoding="utf-8")
    texto = texto.replace("../network/acacias.net.xml", (CARPETA_TESIS / "sumo" / "network" / "acacias.net.xml").as_posix())
    texto = texto.replace(f"../routes/{escenario}.rou.xml", ruta_rutas.as_posix())
    ruta_config = carpeta / f"{escenario}.sumocfg"
    ruta_config.write_text(texto, encoding="utf-8")
    return ruta_config


def main():
    barrido = leer_yaml("barrido_calibracion.yaml")
    configs = (cargar_interseccion(), leer_yaml("controlador.yaml"), leer_yaml("experimento.yaml"))
    inicio, fin = configs[2]["calentamiento_s"], configs[2]["duracion_demanda_s"]
    claves = [(f["tipo"], f["atributo"]) for f in barrido["factores"]]
    combinaciones = list(itertools.product(*[f["niveles"] for f in barrido["factores"]]))

    CARPETA_BARRIDO.mkdir(parents=True, exist_ok=True)
    descripcion = {}
    filas = []
    print(f"{len(combinaciones)} combinaciones x {len(barrido['escenarios'])} escenarios, semilla {barrido['semilla']}")
    for numero, niveles in enumerate(combinaciones, start=1):
        nombre = f"c{numero:02d}"
        parametros = dict(zip(claves, niveles))
        descripcion[nombre] = {f"{t}.{a}": v for (t, a), v in parametros.items()}
        carpeta = CARPETA_BARRIDO / nombre
        carpeta.mkdir(exist_ok=True)
        for escenario in barrido["escenarios"]:
            ruta_config = preparar_escenario(escenario, parametros, carpeta)
            ruta_tripinfo = carpeta / f"{escenario}_tripinfo.xml"
            reloj = time.time()
            _, _, _, cierre = simular(ruta_config, barrido["semilla"], False, "tiempos_fijos", configs, ruta_tripinfo)
            simulado = flujos_simulados(ruta_tripinfo, inicio, fin)
            contado = flujos_aforo(escenario)
            valores = {b: geh(simulado[b], contado[b]) for b in BRAZOS}
            for b in BRAZOS:
                filas.append({"combinacion": nombre, "escenario": escenario, "brazo": b,
                              "aforo_veh_h": round(contado[b]), "simulado_veh_h": round(simulado[b]),
                              "geh": round(valores[b], 2), "sin_terminar": cierre["vehiculos_sin_terminar"]})
            cumplen = sum(v < GEH_MAXIMO for v in valores.values())
            print(f"{nombre} {descripcion[nombre]} | {escenario:<11} | " +
                  " ".join(f"{b} {simulado[b]:5.0f} (GEH {valores[b]:4.1f})" for b in BRAZOS) +
                  f" | cumplen {cumplen}/4 | {time.time() - reloj:4.0f} s")

    with open(CARPETA_BARRIDO / "combinaciones.json", "w", encoding="utf-8") as archivo:
        json.dump({"semilla": barrido["semilla"], "combinaciones": descripcion}, archivo, indent=2)
    with open(CARPETA_BARRIDO / "resultados.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"\nGuardado en {CARPETA_BARRIDO}")


if __name__ == "__main__":
    main()
