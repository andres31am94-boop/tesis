"""
Fase 7: evalua un modelo YOLO entrenado con las fotos PROPIAS de Hot Wheels (data/raw/hotwheels/), que el modelo
nunca vio durante el entrenamiento. Compara cuantos carros detecta con cuantos hay realmente (conteo_real.json).

Metricas por imagen y totales:
  detectados, reales, error = detectados - reales, y el error absoluto medio (MAE).
  (Es una evaluacion de CONTEO, que es lo que necesita el agente. La evaluacion por cajas -mAP- se hace con el
   conjunto de prueba del dataset y, despues, con fotos de la maqueta etiquetadas.)

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\evaluar_yolo_hotwheels.py --pesos results\\vision\\entrenamiento\\<corrida>\\weights\\best.pt
  opciones: --conf 0.25 (umbral) --imgsz 640 --nms_iou 0.5 (quita cajas duplicadas; 0 = no aplicar)

Cajas duplicadas: YOLO26 no usa NMS por defecto (su cabeza "uno a uno" deberia dar una caja por objeto). Con pocas
epocas de entrenamiento todavia produce 2-3 cajas casi encimadas sobre el mismo carro. --nms_iou aplica la
supresion de no maximos clasica: si dos cajas se solapan mas que ese IoU (interseccion/union), se queda la de mayor
confianza.
Salida: results/vision/evaluacion_hotwheels/<corrida>_conf<umbral>/ (imagenes con cajas + resumen.json)
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS / "scripts"))

import cv2  # noqa: E402
import torch  # noqa: E402
from torchvision.ops import nms  # noqa: E402
from ultralytics import YOLO  # noqa: E402

from probar_yolo_imagenes import CARPETA_ENTRADA, leer_imagenes  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # carpeta tesis (para src.common.registro_computo)
from src.common.registro_computo import registrar_ejecucion  # noqa: E402


def main():
    registrar_ejecucion()
    parser = argparse.ArgumentParser(description="Evalua el conteo de un modelo YOLO con las fotos propias")
    parser.add_argument("--pesos", required=True, help="ruta a best.pt")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--nms_iou", type=float, default=0.0, help="IoU para quitar duplicados (0 = no aplicar)")
    argumentos = parser.parse_args()

    ruta_pesos = Path(argumentos.pesos).resolve()
    conteo_real = json.loads((CARPETA_ENTRADA / "conteo_real.json").read_text(encoding="utf-8"))
    corrida = ruta_pesos.parent.parent.name
    carpeta_salida = CARPETA_TESIS / "results" / "vision" / "evaluacion_hotwheels" / (f"{corrida}_conf{argumentos.conf}" + (f"_nms{argumentos.nms_iou}" if argumentos.nms_iou else "")
                     + (f"_img{argumentos.imgsz}" if argumentos.imgsz != 640 else ""))
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    modelo = YOLO(str(ruta_pesos))
    imagenes = leer_imagenes(CARPETA_ENTRADA)
    modelo.predict(imagenes[0][1], conf=argumentos.conf, imgsz=argumentos.imgsz, verbose=False)   # calentamiento

    filas = []
    print(f"Modelo {ruta_pesos} | conf >= {argumentos.conf} | imgsz {argumentos.imgsz} | nms_iou {argumentos.nms_iou}\n")
    print(f"{'imagen':<32}{'reales':>7}{'detect.':>9}{'error':>7}{'ms':>7}")
    for nombre, imagen in imagenes:
        if nombre not in conteo_real:
            print(f"{nombre:<32} (sin conteo real, se omite)")
            continue
        inicio = time.perf_counter()
        resultado = modelo.predict(imagen, conf=argumentos.conf, imgsz=argumentos.imgsz, verbose=False)[0]
        milisegundos = (time.perf_counter() - inicio) * 1000
        if argumentos.nms_iou and len(resultado.boxes):
            conservar = nms(resultado.boxes.xyxy, resultado.boxes.conf, argumentos.nms_iou)
            resultado = resultado[conservar]
        detectados = len(resultado.boxes)
        reales = conteo_real[nombre]
        confianzas = [round(float(c), 3) for c in resultado.boxes.conf]
        filas.append({"imagen": nombre, "reales": reales, "detectados": detectados, "error": detectados - reales,
                      "inferencia_ms": round(milisegundos, 1), "confianzas": confianzas})
        print(f"{nombre:<32}{reales:>7}{detectados:>9}{detectados - reales:>+7}{milisegundos:>7.0f}")
        cv2.imwrite(str(carpeta_salida / f"detecciones_{Path(nombre).stem}.jpg"), resultado.plot())

    mae = statistics.mean(abs(f["error"]) for f in filas)
    total_reales = sum(f["reales"] for f in filas)
    total_detectados = sum(f["detectados"] for f in filas)
    print(f"\nTotal reales {total_reales} | detectados {total_detectados} | error absoluto medio por imagen {mae:.2f}")
    with open(carpeta_salida / "resumen.json", "w", encoding="utf-8") as archivo:
        json.dump({"pesos": str(ruta_pesos), "conf": argumentos.conf, "imgsz": argumentos.imgsz,
                   "nms_iou": argumentos.nms_iou,
                   "error_absoluto_medio": round(mae, 3), "total_reales": total_reales,
                   "total_detectados": total_detectados, "imagenes": filas}, archivo, indent=2, ensure_ascii=False)
    print(f"Imagenes con cajas y resumen en: {carpeta_salida}")


if __name__ == "__main__":
    main()
