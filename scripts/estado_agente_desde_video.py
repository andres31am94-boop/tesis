"""
Fase 9, paso 2: conteos de la camara -> estado que ve el agente (sin decidir todavia).

Lee el conteo por segundo de scripts/contar_zonas_video.py y, cada --intervalo segundos (5 s, como decide el agente):
  1. arma el EstadoTrafico con lo que vio la camara (carros presentes y detenidos por brazo),
  2. lo traduce a la escala de SUMO (src/vision/escala_maqueta.py: ocupacion relativa),
  3. lo pasa por el MISMO codificador del agente aforo_v8 (mismos cortes) y muestra el nivel de cada eje.
El eje en verde aun no existe (lo decide el agente en el paso 3), por eso se muestran los dos niveles de cada eje:
  "si en rojo" (detenidos, cortes de cola) y "si en verde" (presentes, cortes de presentes).

Uso (desde la carpeta tesis):
  python scripts/estado_agente_desde_video.py --conteo results/vision/conteo_zonas/un_metro/conteo_por_segundo.csv
                                              --zonas config/zonas_prueba_1m.yaml
Salida: estado_agente.csv junto al conteo.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))

from src.agent.codificador_estado import nivel  # noqa: E402
from src.common.estado import EstadoBrazo, EstadoTrafico  # noqa: E402
from src.vision.escala_maqueta import EscaladorMaqueta, capacidad_zona_sumo  # noqa: E402

NOMBRES_NIVEL = ["vacia", "baja", "media", "alta", "muy_alta"]
EJES = {"cra23": ["norte", "sur"], "dg15": ["este", "oeste"]}


def main():
    parser = argparse.ArgumentParser(description="Conteo de la camara -> niveles de estado del agente")
    parser.add_argument("--conteo", required=True, help="conteo_por_segundo.csv de contar_zonas_video.py")
    parser.add_argument("--zonas", required=True, help="yaml de zonas con capacidad_carros")
    parser.add_argument("--agente", default=str(CARPETA_TESIS / "models" / "aforo_v8" / "tabla_q.json"))
    parser.add_argument("--intervalo", type=int, default=5)
    argumentos = parser.parse_args()

    config_zonas = yaml.safe_load(Path(argumentos.zonas).read_text(encoding="utf-8"))
    config_interseccion = yaml.safe_load((CARPETA_TESIS / "config" / "interseccion.yaml").read_text(encoding="utf-8"))
    estado_agente = json.loads(Path(argumentos.agente).read_text(encoding="utf-8"))["metadatos"]["config_agente"]["estado"]
    cortes_cola, cortes_presentes = estado_agente["cortes_detenidos_zona"], estado_agente["cortes_presentes_zona_verde"]
    escalador = EscaladorMaqueta(config_zonas["capacidad_carros"], capacidad_zona_sumo(config_interseccion))

    with open(argumentos.conteo, encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    salida = []
    print(f"Capacidad de la zona en SUMO: {escalador.capacidad_sumo:.1f} veh. | capacidad maqueta: "
          f"{escalador.capacidad_carros} | cortes cola {cortes_cola} | cortes presentes {cortes_presentes}\n")
    for fila in filas:
        segundo = int(fila["segundo"])
        if segundo % argumentos.intervalo:
            continue
        brazos = {b: EstadoBrazo(vehiculos=int(fila[f"presentes_{b}"]), detenidos=int(fila[f"detenidos_{b}"]),
                                 cola_relativa=0.0, vehiculos_zona=int(fila[f"presentes_{b}"]),
                                 detenidos_zona=int(fila[f"detenidos_{b}"])) for b in escalador.capacidad_carros}
        camara = EstadoTrafico(tiempo=float(segundo), brazos=brazos)
        escalado = escalador.escalar(camara)
        registro = {"segundo": segundo}
        texto = [f"t={segundo:>3}s"]
        for eje, nombres in EJES.items():
            carros_det = max(camara.brazos[b].detenidos_zona for b in nombres)
            carros_pres = max(camara.brazos[b].vehiculos_zona for b in nombres)
            equiv_det = max(escalado.brazos[b].detenidos_zona for b in nombres)
            equiv_pres = max(escalado.brazos[b].vehiculos_zona for b in nombres)
            nivel_rojo = NOMBRES_NIVEL[nivel(equiv_det, cortes_cola)]
            nivel_verde = NOMBRES_NIVEL[nivel(equiv_pres, cortes_presentes)]
            registro.update({f"{eje}_carros_detenidos": carros_det, f"{eje}_carros_presentes": carros_pres,
                             f"{eje}_equiv_detenidos": equiv_det, f"{eje}_equiv_presentes": equiv_pres,
                             f"{eje}_nivel_si_rojo": nivel_rojo, f"{eje}_nivel_si_verde": nivel_verde})
            texto.append(f"{eje}: {carros_pres} carros ({carros_det} det.) -> equiv {equiv_pres} ({equiv_det} det.) "
                         f"| rojo={nivel_rojo}, verde={nivel_verde}")
        salida.append(registro)
        print("  ".join(texto))

    ruta = Path(argumentos.conteo).with_name("estado_agente.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(salida[0]))
        escritor.writeheader()
        escritor.writerows(salida)
    print(f"\nGuardado: {ruta}")


if __name__ == "__main__":
    main()
