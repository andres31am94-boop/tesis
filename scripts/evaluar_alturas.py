"""
Fase 7.6 (decision de la maqueta): evalua la deteccion a distintas alturas de camara (60, 80, 100 cm).

Para cada video de data/raw/hotwheels/prueba_alturas/ toma un cuadro cada --cada_s segundos, detecta con YOLO
(+ NMS) y guarda: la imagen con cajas (para contar a mano los carros reales y verificar) y un resumen.json con
detecciones por cuadro, confianzas, tamano de las cajas en pixeles y tiempo de inferencia.
La comparacion con el numero REAL de carros se hace contando a mano en las imagenes (se registra aparte).

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\evaluar_alturas.py --pesos results\\vision\\entrenamiento\\hotwheels_v2\\weights\\best.pt
Salida: results/vision/prueba_alturas/<corrida>_conf<c>/<video>/  (las .jpg no se suben: salen pies/manos)
"""
import argparse
import json
import statistics
import time
from pathlib import Path

import cv2
from torchvision.ops import nms
from ultralytics import YOLO
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # carpeta tesis (para src.common.registro_computo)
from src.common.registro_computo import registrar_ejecucion  # noqa: E402

CARPETA_TESIS = Path(__file__).resolve().parents[1]
CARPETA_VIDEOS = CARPETA_TESIS / "data" / "raw" / "hotwheels" / "prueba_alturas"
ALTURAS_CM = {"60_centimetros": 60, "80_centimetros": 80, "un_metro": 100}


def main():
    registrar_ejecucion()
    parser = argparse.ArgumentParser(description="Deteccion de Hot Wheels a distintas alturas de camara")
    parser.add_argument("--pesos", required=True)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--nms_iou", type=float, default=0.5)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--cada_s", type=float, default=1.0, help="segundos entre cuadros evaluados")
    argumentos = parser.parse_args()

    ruta_pesos = Path(argumentos.pesos).resolve()
    corrida = ruta_pesos.parent.parent.name
    salida = (CARPETA_TESIS / "results" / "vision" / "prueba_alturas" /
              (f"{corrida}_conf{argumentos.conf}" + (f"_img{argumentos.imgsz}" if argumentos.imgsz != 640 else "")))
    modelo = YOLO(str(ruta_pesos))
    resumen = {"pesos": str(ruta_pesos), "conf": argumentos.conf, "nms_iou": argumentos.nms_iou,
               "imgsz": argumentos.imgsz, "cada_s": argumentos.cada_s, "videos": {}}

    for video in sorted(CARPETA_VIDEOS.glob("*.MOV")):
        carpeta = salida / video.stem
        carpeta.mkdir(parents=True, exist_ok=True)
        captura = cv2.VideoCapture(str(video))
        fps = captura.get(cv2.CAP_PROP_FPS)
        total = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
        paso = max(1, round(fps * argumentos.cada_s))
        cuadros = []
        for indice in range(0, total, paso):
            captura.set(cv2.CAP_PROP_POS_FRAMES, indice)
            correcto, imagen = captura.read()
            if not correcto:
                break
            inicio = time.perf_counter()
            resultado = modelo.predict(imagen, conf=argumentos.conf, imgsz=argumentos.imgsz, verbose=False)[0]
            milisegundos = (time.perf_counter() - inicio) * 1000
            if len(resultado.boxes):
                resultado = resultado[nms(resultado.boxes.xyxy, resultado.boxes.conf, argumentos.nms_iou)]
            lados = [max(x2 - x1, y2 - y1) for x1, y1, x2, y2 in resultado.boxes.xyxy.tolist()]
            segundo = round(indice / fps, 2)
            cv2.imwrite(str(carpeta / f"t{segundo:05.1f}s.jpg"), resultado.plot())
            cuadros.append({"segundo": segundo, "detectados": len(resultado.boxes),
                            "confianzas": [round(float(c), 3) for c in resultado.boxes.conf],
                            "lado_mayor_px": [round(l) for l in lados], "inferencia_ms": round(milisegundos, 1)})
        captura.release()
        todos_lados = [l for c in cuadros for l in c["lado_mayor_px"]]
        resumen["videos"][video.stem] = {
            "altura_cm": ALTURAS_CM.get(video.stem), "resolucion": f"{imagen.shape[1]}x{imagen.shape[0]}",
            "cuadros_evaluados": len(cuadros),
            "detecciones_promedio": round(statistics.mean(c["detectados"] for c in cuadros), 2),
            "lado_mayor_px_mediana": statistics.median(todos_lados) if todos_lados else None,
            "inferencia_ms_mediana": statistics.median(c["inferencia_ms"] for c in cuadros), "cuadros": cuadros}
        print(f"{video.stem:<16} cuadros {len(cuadros):>3} | detecciones por cuadro "
              f"{[c['detectados'] for c in cuadros]}")

    salida.mkdir(parents=True, exist_ok=True)
    (salida / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nImagenes y resumen en {salida}")


if __name__ == "__main__":
    main()
