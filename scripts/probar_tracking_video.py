"""
Fase 7, paso 7.3: YOLO + tracking (ByteTrack) sobre un video. Cada vehiculo recibe un NUMERO (id) que debe
mantenerse mientras este en cuadro; asi no se cuenta dos veces el mismo carro.

Mide (para la tesis):
  - ids distintos que aparecieron en todo el video (idealmente = carros reales; si es mayor, el tracker
    "perdio" carros y les dio un id nuevo: cambios de identidad),
  - vehiculos detectados por cuadro (minimo, maximo, promedio),
  - velocidad de procesamiento en este PC (cuadros por segundo).
Guarda el video con cajas e ids dibujados en results/vision/tracking/.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\probar_tracking_video.py --pesos results\\vision\\entrenamiento\\hotwheels_v1\\weights\\best.pt --video data\\raw\\hotwheels\\video_IMG_0566.mov
  opciones: --conf 0.40 --nms_iou 0.5 --tracker bytetrack.yaml (o botsort.yaml) --cada 1 (1 de cada N cuadros)

NMS antes del tracker: el modelo de pocas epocas da 2-3 cajas encimadas por carro; si llegan asi al tracker, el
mismo carro recibe varios ids. Se registra un "callback" de Ultralytics que aplica NMS justo despues de la
deteccion y ANTES del tracker (los callbacks corren en el orden en que se agregan).
"""
import argparse
import json
import statistics
import time
from pathlib import Path

import cv2
from torchvision.ops import nms
from ultralytics import YOLO

CARPETA_TESIS = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Prueba de YOLO + tracking sobre un video")
    parser.add_argument("--pesos", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--conf", type=float, default=0.40)
    parser.add_argument("--nms_iou", type=float, default=0.5, help="IoU para quitar cajas duplicadas (0 = no)")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--tracker", default="bytetrack.yaml", help="bytetrack.yaml o botsort.yaml (de Ultralytics)")
    parser.add_argument("--cada", type=int, default=1, help="procesar 1 de cada N cuadros (aligera la CPU)")
    argumentos = parser.parse_args()

    ruta_video = Path(argumentos.video).resolve()
    video = cv2.VideoCapture(str(ruta_video))
    if not video.isOpened():
        raise RuntimeError(f"OpenCV no pudo abrir {ruta_video}")
    fps_video = video.get(cv2.CAP_PROP_FPS) or 30.0
    ancho = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    nombre_corrida = f"{Path(argumentos.pesos).resolve().parent.parent.name}_{ruta_video.stem}_{Path(argumentos.tracker).stem}"
    carpeta = CARPETA_TESIS / "results" / "vision" / "tracking" / nombre_corrida
    carpeta.mkdir(parents=True, exist_ok=True)
    salida = cv2.VideoWriter(str(carpeta / "tracking.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                             fps_video / argumentos.cada, (ancho, alto))

    modelo = YOLO(str(Path(argumentos.pesos).resolve()))
    if argumentos.nms_iou:
        def quitar_duplicados(predictor):
            for i, resultado in enumerate(predictor.results):
                if len(resultado.boxes):
                    predictor.results[i] = resultado[nms(resultado.boxes.xyxy, resultado.boxes.conf, argumentos.nms_iou)]
        modelo.add_callback("on_predict_postprocess_end", quitar_duplicados)   # antes que el del tracker
    ids_vistos, por_cuadro, tiempos_ms = set(), [], []
    indice = 0
    while True:
        correcto, cuadro = video.read()
        if not correcto:
            break
        indice += 1
        if (indice - 1) % argumentos.cada:
            continue
        inicio = time.perf_counter()
        resultado = modelo.track(cuadro, persist=True, tracker=argumentos.tracker, conf=argumentos.conf,
                                 imgsz=argumentos.imgsz, verbose=False)[0]
        tiempos_ms.append((time.perf_counter() - inicio) * 1000)
        ids = [] if resultado.boxes.id is None else [int(i) for i in resultado.boxes.id]
        ids_vistos.update(ids)
        por_cuadro.append(len(resultado.boxes))
        salida.write(resultado.plot())
    video.release()
    salida.release()

    if not por_cuadro:
        raise RuntimeError("El video no tiene cuadros legibles")
    resumen = {
        "video": str(ruta_video), "pesos": argumentos.pesos, "tracker": argumentos.tracker, "conf": argumentos.conf,
        "nms_iou": argumentos.nms_iou,
        "cuadros_procesados": len(por_cuadro), "fps_video": round(fps_video, 2), "resolucion": [ancho, alto],
        "ids_distintos": len(ids_vistos),
        "detectados_por_cuadro": {"min": min(por_cuadro), "max": max(por_cuadro),
                                  "promedio": round(statistics.mean(por_cuadro), 2)},
        "ms_por_cuadro": {"mediana": round(statistics.median(tiempos_ms), 1), "max": round(max(tiempos_ms), 1)},
        "fps_procesamiento": round(1000 / statistics.median(tiempos_ms), 2),
    }
    with open(carpeta / "resumen.json", "w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, indent=2, ensure_ascii=False)
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    print(f"\nVideo con ids en: {carpeta / 'tracking.mp4'}")


if __name__ == "__main__":
    main()
