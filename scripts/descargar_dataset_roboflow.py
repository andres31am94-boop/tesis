"""
Fase 7: descarga un dataset publico de Roboflow Universe en formato YOLO (para entrenar YOLO26 con Ultralytics).

La clave API NO va en el codigo ni en GitHub: se lee de la variable de entorno ROBOFLOW_API_KEY.
En PowerShell (solo para esa ventana):
  $env:ROBOFLOW_API_KEY = "su_clave"        (Roboflow -> Settings -> API Keys -> Private API Key)

Uso (desde la carpeta tesis). Los datos del dataset salen de su direccion:
  https://universe.roboflow.com/<workspace>/<proyecto>/dataset/<version>
  .\\.venv\\Scripts\\python.exe scripts\\descargar_dataset_roboflow.py --workspace yolo-ansk1 --proyecto toy-car-ertgd --version 1

Destino: data/raw/datasets_comunidad/<proyecto>_v<version>/ (data/raw no se sube a GitHub).
Requiere: pip install roboflow
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
CARPETA_DESTINO = CARPETA_TESIS / "data" / "raw" / "datasets_comunidad"


def contar_archivos(carpeta, extensiones):
    return sum(1 for ruta in carpeta.rglob("*") if ruta.suffix.lower() in extensiones)


def main():
    parser = argparse.ArgumentParser(description="Descarga un dataset de Roboflow Universe en formato YOLO")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--proyecto", required=True)
    parser.add_argument("--version", type=int, required=True)
    parser.add_argument("--formato", default="yolov8", help="formato de exportacion de Roboflow (yolov8 sirve para YOLO26)")
    argumentos = parser.parse_args()

    clave = os.environ.get("ROBOFLOW_API_KEY")
    if not clave:
        sys.exit("Falta la variable de entorno ROBOFLOW_API_KEY (ver instrucciones al inicio del script).")

    from roboflow import Roboflow   # se importa aqui para que el mensaje anterior salga aunque falte la libreria

    destino = CARPETA_DESTINO / f"{argumentos.proyecto}_v{argumentos.version}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    proyecto = Roboflow(api_key=clave).workspace(argumentos.workspace).project(argumentos.proyecto)
    proyecto.version(argumentos.version).download(argumentos.formato, location=str(destino))

    imagenes = contar_archivos(destino, {".jpg", ".jpeg", ".png", ".bmp", ".webp"})
    etiquetas = contar_archivos(destino, {".txt"})
    origen = {"fuente": "Roboflow Universe",
              "url": f"https://universe.roboflow.com/{argumentos.workspace}/{argumentos.proyecto}/dataset/{argumentos.version}",
              "formato": argumentos.formato, "fecha_descarga": datetime.now().isoformat(timespec="seconds"),
              "imagenes": imagenes, "archivos_txt": etiquetas,
              "licencia": "REVISAR en la pagina del dataset y anotarla aqui"}
    with open(destino / "origen_dataset.json", "w", encoding="utf-8") as archivo:
        json.dump(origen, archivo, indent=2, ensure_ascii=False)
    print(f"\nDescargado en: {destino}")
    print(f"Imagenes: {imagenes} | archivos .txt (etiquetas): {etiquetas}")
    print("Revise data.yaml (clases) y anote la licencia en origen_dataset.json.")


if __name__ == "__main__":
    main()
