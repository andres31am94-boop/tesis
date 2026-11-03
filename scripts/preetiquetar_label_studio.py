"""
Fase 7, paso 7.4: PRE-ETIQUETADO. El modelo actual propone las cajas de cada imagen de entrenamiento y se genera un
archivo de tareas para Label Studio; los autores solo CORRIGEN (borrar cajas malas, agregar carros no vistos, ajustar
bordes). Las propuestas se importan como "predicciones": no cuentan como etiquetas hasta que una persona las revisa y
las envia (Submit).

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\preetiquetar_label_studio.py
Salida: data/raw/hotwheels/tareas_label_studio.json (se importa en Label Studio).
Las imagenes se sirven desde el PC (Label Studio "local files"), raiz = data/raw/hotwheels; nada se sube a internet.
"""
import argparse
import json
from pathlib import Path

import cv2
from torchvision.ops import nms
from ultralytics import YOLO

CARPETA_TESIS = Path(__file__).resolve().parents[1]
RAIZ_ARCHIVOS = CARPETA_TESIS / "data" / "raw" / "hotwheels"
CARPETA_IMAGENES = RAIZ_ARCHIVOS / "cuadros_entrenamiento"
ETIQUETA = "Car"


def main():
    parser = argparse.ArgumentParser(description="Genera tareas de Label Studio con cajas propuestas por el modelo")
    parser.add_argument("--pesos", default=str(CARPETA_TESIS / "results" / "vision" / "entrenamiento" /
                                               "hotwheels_v1_epoca2" / "weights" / "best.pt"))
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--nms_iou", type=float, default=0.5)
    argumentos = parser.parse_args()

    modelo = YOLO(argumentos.pesos)
    tareas, total_cajas = [], 0
    imagenes = sorted(CARPETA_IMAGENES.glob("*.jpg"))
    for ruta in imagenes:
        imagen = cv2.imread(str(ruta))
        alto, ancho = imagen.shape[:2]
        resultado = modelo.predict(imagen, conf=argumentos.conf, verbose=False)[0]
        if len(resultado.boxes):
            resultado = resultado[nms(resultado.boxes.xyxy, resultado.boxes.conf, argumentos.nms_iou)]
        cajas = []
        for (x1, y1, x2, y2), confianza in zip(resultado.boxes.xyxy.tolist(), resultado.boxes.conf.tolist()):
            cajas.append({"from_name": "label", "to_name": "image", "type": "rectanglelabels",
                          "original_width": ancho, "original_height": alto, "score": round(confianza, 3),
                          "value": {"x": 100 * x1 / ancho, "y": 100 * y1 / alto, "width": 100 * (x2 - x1) / ancho,
                                    "height": 100 * (y2 - y1) / alto, "rotation": 0, "rectanglelabels": [ETIQUETA]}})
        total_cajas += len(cajas)
        relativa = ruta.relative_to(RAIZ_ARCHIVOS).as_posix()
        tareas.append({"data": {"image": f"/data/local-files/?d={relativa}"},
                       "predictions": [{"model_version": Path(argumentos.pesos).parent.parent.name, "result": cajas}]})
        print(f"{ruta.name}: {len(cajas)} cajas propuestas")
    salida = RAIZ_ARCHIVOS / "tareas_label_studio.json"
    salida.write_text(json.dumps(tareas, indent=1), encoding="utf-8")
    print(f"\n{len(tareas)} imagenes, {total_cajas} cajas propuestas -> {salida}")


if __name__ == "__main__":
    main()
