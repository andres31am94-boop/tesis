"""
Fase 8: video de la maqueta -> YOLO + NMS + ByteTrack -> conteo por brazo (ContadorZonas) -> datos para el agente.

Por cada SEGUNDO de video guarda, para cada brazo: vehiculos presentes en su zona y vehiculos detenidos
(quietos >= ventana_s). Es lo mismo que el agente recibe de SUMO (vehiculos_zona, detenidos_zona).

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\contar_zonas_video.py --pesos <best.pt> --video data\\raw\\hotwheels\\<video>
  opciones: --conf 0.40 --nms_iou 0.5 --tracker bytetrack.yaml --cada 1
Salida en results/vision/conteo_zonas/<video>/: conteo_por_segundo.csv, conteo.mp4 (zonas y conteos dibujados),
resumen.json. Para medir el error: contar a mano algunos segundos del video y compararlos con el CSV.
"""
import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))
sys.path.insert(0, str(CARPETA_TESIS / "scripts"))

import cv2  # noqa: E402
from torchvision.ops import nms  # noqa: E402
from ultralytics import YOLO  # noqa: E402

from src.vision.zonas import ContadorZonas, VehiculoSeguido  # noqa: E402
from ver_zonas import cargar_zonas, dibujar_zonas  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Conteo de vehiculos por brazo en un video de la maqueta")
    parser.add_argument("--pesos", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--conf", type=float, default=0.40)
    parser.add_argument("--nms_iou", type=float, default=0.5)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--tracker", default="bytetrack.yaml")
    parser.add_argument("--cada", type=int, default=1, help="procesar 1 de cada N cuadros")
    argumentos = parser.parse_args()

    zonas, config = cargar_zonas()
    contador = ContadorZonas(zonas, ventana_detenido_s=config["deteccion_detenido"]["ventana_s"],
                             umbral_movimiento=config["deteccion_detenido"]["umbral_movimiento"],
                             punto_referencia=config.get("punto_referencia", "centro"))

    ruta_video = Path(argumentos.video).resolve()
    video = cv2.VideoCapture(str(ruta_video))
    if not video.isOpened():
        raise RuntimeError(f"OpenCV no pudo abrir {ruta_video}")
    fps = video.get(cv2.CAP_PROP_FPS) or 30.0
    ancho = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    carpeta = CARPETA_TESIS / "results" / "vision" / "conteo_zonas" / ruta_video.stem
    carpeta.mkdir(parents=True, exist_ok=True)
    salida = cv2.VideoWriter(str(carpeta / "conteo.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps / argumentos.cada,
                             (ancho, alto))

    modelo = YOLO(str(Path(argumentos.pesos).resolve()))
    if argumentos.nms_iou:
        def quitar_duplicados(predictor):
            for i, resultado in enumerate(predictor.results):
                if len(resultado.boxes):
                    predictor.results[i] = resultado[nms(resultado.boxes.xyxy, resultado.boxes.conf, argumentos.nms_iou)]
        modelo.add_callback("on_predict_postprocess_end", quitar_duplicados)

    filas, tiempos_ms, segundo_anterior, indice = [], [], -1, 0
    while True:
        correcto, cuadro = video.read()
        if not correcto:
            break
        indice += 1
        if (indice - 1) % argumentos.cada:
            continue
        tiempo = (indice - 1) / fps
        inicio = time.perf_counter()
        resultado = modelo.track(cuadro, persist=True, tracker=argumentos.tracker, conf=argumentos.conf,
                                 imgsz=argumentos.imgsz, verbose=False)[0]
        vehiculos = []
        if resultado.boxes.id is not None:
            for (x1, y1, x2, y2), id_seguimiento in zip(resultado.boxes.xyxy.tolist(), resultado.boxes.id.tolist()):
                vehiculos.append(VehiculoSeguido(int(id_seguimiento), x1, y1, x2, y2))
        estado = contador.actualizar(tiempo, vehiculos, ancho, alto)
        tiempos_ms.append((time.perf_counter() - inicio) * 1000)

        conteos = {n: (b.vehiculos_zona, b.detenidos_zona) for n, b in estado.brazos.items()}
        salida.write(dibujar_zonas(resultado.plot(), zonas, conteos))
        if int(tiempo) != segundo_anterior:   # una fila por segundo (primer cuadro de cada segundo)
            segundo_anterior = int(tiempo)
            fila = {"segundo": int(tiempo)}
            for nombre, (presentes, detenidos) in conteos.items():
                fila[f"presentes_{nombre}"] = presentes
                fila[f"detenidos_{nombre}"] = detenidos
            filas.append(fila)
    video.release()
    salida.release()
    if not filas:
        raise RuntimeError("El video no tiene cuadros legibles")

    with open(carpeta / "conteo_por_segundo.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    resumen = {"video": str(ruta_video), "pesos": argumentos.pesos, "conf": argumentos.conf,
               "nms_iou": argumentos.nms_iou, "tracker": argumentos.tracker, "segundos": len(filas),
               "ms_por_cuadro_mediana": round(statistics.median(tiempos_ms), 1),
               "fps_procesamiento": round(1000 / statistics.median(tiempos_ms), 2)}
    with open(carpeta / "resumen.json", "w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, indent=2, ensure_ascii=False)
    for fila in filas:
        print(fila)
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    print(f"\nResultados en {carpeta}")


if __name__ == "__main__":
    main()
