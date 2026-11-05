"""
Genera los escenarios desbalanceados de config/escenarios_desbalanceados.yaml a partir de los escenarios REALES ya
generados (sumo/routes/<base>.rou.xml y sumo/configs/<base>.sumocfg, de scripts/generar_escenarios_aforo.py).

Para cada flujo del escenario base (un brazo x giro x tipo) y cada tramo de tiempo, escribe un flujo con
probabilidad = probabilidad_base * factor_del_brazo, entre desde_s y hasta_s. Todo lo demas (tipos de vehiculo,
calibracion, red, subcarriles, teleport) se copia del escenario base sin cambios.

Uso (desde la carpeta tesis):  python scripts/generar_escenarios_desbalanceados.py
Salida: sumo/routes/<escenario>.rou.xml, sumo/configs/<escenario>.sumocfg y sumo/demanda/<escenario>_resumen.csv
"""
import csv
import re
from pathlib import Path

import yaml
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # carpeta tesis (para src.common.registro_computo)
from src.common.registro_computo import registrar_ejecucion  # noqa: E402

CARPETA_TESIS = Path(__file__).resolve().parents[1]
CARPETA_SUMO = CARPETA_TESIS / "sumo"
PATRON_FLUJO = re.compile(r'<flow id="(?P<id>[^"]+)"(?P<antes>.*?) begin="0" end="3600" '
                          r'from="acceso_(?P<brazo>\w+)"(?P<medio>.*?) probability="(?P<p>[\d.]+)"(?P<despues>.*?)/>')
BRAZOS = ("norte", "sur", "este", "oeste")
EJE = {"norte": "cra23", "sur": "cra23", "este": "dg15", "oeste": "dg15"}


def generar(nombre, datos):
    base = datos["base"]
    texto_base = (CARPETA_SUMO / "routes" / f"{base}.rou.xml").read_text(encoding="utf-8")
    flujos_base = list(PATRON_FLUJO.finditer(texto_base))
    if not flujos_base:
        raise ValueError(f"No se encontraron flujos en {base}.rou.xml")
    if texto_base.count("<flow") != len(flujos_base):
        raise ValueError(f"{base}.rou.xml tiene flujos con un formato distinto al esperado")

    lineas, resumen = [], []
    for numero, tramo in enumerate(datos["tramos"]):
        factores = tramo["factores"]
        if set(factores) != set(BRAZOS):
            raise ValueError(f"{nombre}: el tramo {numero} debe dar factor para {BRAZOS}")
        por_brazo = dict.fromkeys(BRAZOS, 0.0)
        for flujo in flujos_base:
            brazo = flujo["brazo"]
            probabilidad = float(flujo["p"]) * factores[brazo]
            if probabilidad > 1:
                raise ValueError(f"{nombre}: {flujo['id']} supera 3600 veh/h")
            if probabilidad == 0:
                continue
            por_brazo[brazo] += probabilidad * 3600
            lineas.append(f'    <flow id="{flujo["id"]}_t{numero}"{flujo["antes"]} begin="{tramo["desde_s"]}" '
                          f'end="{tramo["hasta_s"]}" from="acceso_{brazo}"{flujo["medio"]} '
                          f'probability="{probabilidad:.6f}"{flujo["despues"]}/>')
        for brazo in BRAZOS:
            resumen.append({"tramo": numero, "desde_s": tramo["desde_s"], "hasta_s": tramo["hasta_s"], "brazo": brazo,
                            "eje": EJE[brazo], "factor": factores[brazo], "vehiculos_hora": round(por_brazo[brazo])})

    inicio = texto_base.index("<routes>") + len("<routes>")
    tipos = "".join(l + "\n" for l in texto_base[inicio:].splitlines() if "<vType" in l)
    rutas = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             "<!-- Generado por scripts/generar_escenarios_desbalanceados.py: NO editar a mano. -->\n"
             f"<!-- Escenario DERIVADO (no medido) {nombre}: {datos['descripcion']}. Base: {base}.rou.xml -->\n"
             "<routes>\n" + tipos + "\n".join(lineas) + "\n</routes>\n")
    (CARPETA_SUMO / "routes" / f"{nombre}.rou.xml").write_text(rutas, encoding="utf-8")

    config = (CARPETA_SUMO / "configs" / f"{base}.sumocfg").read_text(encoding="utf-8")
    if f"../routes/{base}.rou.xml" not in config:
        raise ValueError(f"{base}.sumocfg no apunta a {base}.rou.xml")
    config = config.replace(f"../routes/{base}.rou.xml", f"../routes/{nombre}.rou.xml")
    config = re.sub(r"<!--.*?-->", f"<!-- Escenario DERIVADO {nombre} (scripts/generar_escenarios_desbalanceados.py): "
                    f"{datos['descripcion']} -->", config, count=1, flags=re.S)
    (CARPETA_SUMO / "configs" / f"{nombre}.sumocfg").write_text(config, encoding="utf-8")

    with open(CARPETA_SUMO / "demanda" / f"{nombre}_resumen.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(resumen[0]))
        escritor.writeheader()
        escritor.writerows(resumen)
    return resumen


def main():
    registrar_ejecucion()
    config = yaml.safe_load((CARPETA_TESIS / "config" / "escenarios_desbalanceados.yaml").read_text(encoding="utf-8"))
    for nombre, datos in config["escenarios"].items():
        resumen = generar(nombre, datos)
        print(f"{nombre}  (base {datos['base']})")
        for numero in sorted({fila["tramo"] for fila in resumen}):
            filas = [f for f in resumen if f["tramo"] == numero]
            cra = sum(f["vehiculos_hora"] for f in filas if f["eje"] == "cra23")
            dg = sum(f["vehiculos_hora"] for f in filas if f["eje"] == "dg15")
            print(f"   {filas[0]['desde_s']:>4}-{filas[0]['hasta_s']:<4} s: Cra 23 {cra:>5} veh/h | Dg 15 {dg:>5} veh/h | "
                  + ", ".join(f"{f['brazo']} {f['vehiculos_hora']}" for f in filas))


if __name__ == "__main__":
    main()
