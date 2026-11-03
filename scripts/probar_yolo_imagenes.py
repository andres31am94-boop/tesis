"""
Fase 7, paso 7.1: ¿YOLO detecta los Hot Wheels? Prueba con fotos/videos propios, SIN entrenar nada.

Para cada imagen de data/raw/hotwheels/ (y el primer cuadro de cada video):
  - corre el modelo YOLO preentrenado (COCO) con un umbral de confianza bajo, para ver TODO lo que encuentra;
  - imprime cada deteccion: clase, confianza y si es una clase de vehiculo (car, motorcycle, bus, truck);
  - mide el tiempo de inferencia en ESTE PC (CPU);
  - guarda la imagen con las cajas dibujadas en results/vision/prueba_hotwheels/.
Lo que hay que comparar a mano: cuantos Hot Wheels hay en la foto vs. cuantos detecto como vehiculo.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\probar_yolo_imagenes.py
  .\\.venv\\Scripts\\python.exe scripts\\probar_yolo_imagenes.py --modelo yolo26s.pt --conf 0.05
  YOLO-World (vocabulario abierto: se le dice en texto que buscar, sin entrenar):
  .\\.venv\\Scripts\\python.exe scripts\\probar_yolo_imagenes.py --modelo yolov8s-worldv2.pt --clases "toy car"
El modelo se descarga la primera vez a models/yolo/ (los .pt no se suben a GitHub; se documenta el nombre y la version).
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2
from ultralytics import YOLO, __version__ as version_ultralytics

CARPETA_TESIS = Path(__file__).resolve().parents[1]
CARPETA_ENTRADA = CARPETA_TESIS / "data" / "raw" / "hotwheels"
CARPETA_SALIDA = CARPETA_TESIS / "results" / "vision" / "prueba_hotwheels"
CARPETA_PESOS = CARPETA_TESIS / "models" / "yolo"
CLASES_VEHICULO = {"car", "motorcycle", "bus", "truck"}   # clases del dataset COCO relevantes para trafico
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".heic", ".bmp"}
EXTENSIONES_VIDEO = {".mp4", ".mov", ".avi"}


def leer_imagenes(carpeta):
    """Devuelve [(nombre, imagen BGR)]: cada foto y el primer cuadro de cada video."""
    imagenes = []
    for ruta in sorted(carpeta.iterdir()):
        sufijo = ruta.suffix.lower()
        if sufijo in EXTENSIONES_IMAGEN:
            imagen = cv2.imread(str(ruta))
            if imagen is None:
                print(f"AVISO: OpenCV no pudo abrir {ruta.name} (si es .HEIC, exportela como JPG desde el iPhone)")
                continue
            imagenes.append((ruta.name, imagen))
        elif sufijo in EXTENSIONES_VIDEO:
            video = cv2.VideoCapture(str(ruta))
            correcto, cuadro = video.read()
            video.release()
            if not correcto:
                print(f"AVISO: no se pudo leer el video {ruta.name}")
                continue
            imagenes.append((f"{ruta.stem}_cuadro0.jpg", cuadro))
    return imagenes


def main():
    parser = argparse.ArgumentParser(description="Prueba de YOLO preentrenado con fotos de Hot Wheels")
    parser.add_argument("--modelo", default="yolo26n.pt", help="pesos de Ultralytics (n = nano, s = small, ...)")
    parser.add_argument("--conf", type=float, default=0.10, help="umbral de confianza (bajo a proposito)")
    parser.add_argument("--imgsz", type=int, default=640, help="tamano de entrada de la red (pixeles)")
    parser.add_argument("--clases", nargs="+", help="solo YOLO-World: textos a buscar, p. ej. \"toy car\"")
    argumentos = parser.parse_args()

    imagenes = leer_imagenes(CARPETA_ENTRADA)
    if not imagenes:
        sys.exit(f"No hay fotos ni videos en {CARPETA_ENTRADA}")
    CARPETA_PESOS.mkdir(parents=True, exist_ok=True)
    es_world = "world" in argumentos.modelo
    if es_world and not argumentos.clases:
        sys.exit("YOLO-World necesita --clases, p. ej. --clases \"toy car\"")
    carpeta_salida = CARPETA_SALIDA / Path(argumentos.modelo).stem
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    modelo = YOLO(str(CARPETA_PESOS / argumentos.modelo))
    clases_vehiculo = CLASES_VEHICULO
    if es_world:
        modelo.set_classes(argumentos.clases)   # todo lo que encuentre es una de estas clases
        clases_vehiculo = set(argumentos.clases)
    print(f"Ultralytics {version_ultralytics} | modelo {argumentos.modelo} | conf >= {argumentos.conf} | "
          f"imgsz {argumentos.imgsz} | dispositivo: CPU")
    modelo.predict(imagenes[0][1], conf=argumentos.conf, imgsz=argumentos.imgsz, verbose=False)   # calentamiento

    resumen = []
    for nombre, imagen in imagenes:
        inicio = time.perf_counter()
        resultado = modelo.predict(imagen, conf=argumentos.conf, imgsz=argumentos.imgsz, verbose=False)[0]
        milisegundos = (time.perf_counter() - inicio) * 1000

        detecciones = []
        for caja in resultado.boxes:
            clase = resultado.names[int(caja.cls)]
            detecciones.append({"clase": clase, "confianza": round(float(caja.conf), 3),
                                "es_vehiculo": clase in clases_vehiculo})
        vehiculos = [d for d in detecciones if d["es_vehiculo"]]
        alto, ancho = imagen.shape[:2]
        print(f"\n{nombre} ({ancho}x{alto}) - inferencia {milisegundos:.0f} ms - "
              f"{len(vehiculos)} vehiculos de {len(detecciones)} detecciones")
        for d in sorted(detecciones, key=lambda d: -d["confianza"]):
            print(f"   {'VEHICULO' if d['es_vehiculo'] else 'otro    '}  {d['clase']:<14} {d['confianza']:.2f}")

        cv2.imwrite(str(carpeta_salida / f"detecciones_{Path(nombre).stem}.jpg"), resultado.plot())
        resumen.append({"imagen": nombre, "ancho": ancho, "alto": alto, "inferencia_ms": round(milisegundos, 1),
                        "detecciones": detecciones})

    with open(carpeta_salida / "resumen.json", "w", encoding="utf-8") as archivo:
        json.dump({"ultralytics": version_ultralytics, "modelo": argumentos.modelo, "conf": argumentos.conf,
                   "imgsz": argumentos.imgsz, "clases_texto": argumentos.clases, "resultados": resumen}, archivo, indent=2, ensure_ascii=False)
    print(f"\nImagenes con cajas y resumen.json en: {carpeta_salida}")
    print("Anote cuantos Hot Wheels hay realmente en cada foto para comparar con 'vehiculos'.")


if __name__ == "__main__":
    main()
