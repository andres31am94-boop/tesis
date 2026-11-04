"""
Fase 7, paso 7.2: entrena (ajuste fino / transferencia de aprendizaje) YOLO26n para detectar carros de juguete.

Parte de los pesos yolo26n.pt (preentrenados en COCO) y los ajusta con un dataset en formato YOLO (data.yaml).
Dataset inicial: "Hot-wheels-recognition" v1 (Roboflow Universe, group-project-konh2, CC BY 4.0), 1 clase.

Como el PC no tiene GPU, primero se hace una PRUEBA CORTA para medir cuanto tarda una epoca:
  .\\.venv\\Scripts\\python.exe scripts\\entrenar_yolo.py --datos <ruta>\\data.yaml --epocas 1 --fraccion 0.05 --nombre prueba_tiempo
Entrenamiento completo (los valores se deciden despues de medir el tiempo):
  .\\.venv\\Scripts\\python.exe scripts\\entrenar_yolo.py --datos <ruta>\\data.yaml --epocas 30 --fraccion 1.0 --nombre hotwheels_v1

Si se interrumpe (se apaga el PC o se cierra la ventana), se continua desde la ultima epoca guardada con:
  .\\.venv\\Scripts\\python.exe scripts\\entrenar_yolo.py --datos <ruta>\\data.yaml --nombre hotwheels_v1 --reanudar

Resultados (curvas, matriz de confusion, mAP, precision, recall y pesos best.pt / last.pt) en
results/vision/entrenamiento/<nombre>/. Los .pt no se suben a GitHub (se documentan); el resto si.
"""
import argparse
import json
import platform
import time
from datetime import datetime
from pathlib import Path

from ultralytics import YOLO, __version__ as version_ultralytics

CARPETA_TESIS = Path(__file__).resolve().parents[1]
CARPETA_PESOS = CARPETA_TESIS / "models" / "yolo"
CARPETA_RESULTADOS = CARPETA_TESIS / "results" / "vision" / "entrenamiento"
SEMILLA = 0   # reproducibilidad (Ultralytics fija las semillas de Python, NumPy y PyTorch)


def main():
    parser = argparse.ArgumentParser(description="Ajuste fino de YOLO26n con carros de juguete")
    parser.add_argument("--datos", required=True, help="ruta al data.yaml del dataset")
    parser.add_argument("--modelo", default="yolo26n.pt",
                        help="pesos de partida: nombre en models/yolo/ o ruta a un best.pt ya entrenado")
    parser.add_argument("--epocas", type=int, default=30)
    parser.add_argument("--fraccion", type=float, default=1.0, help="fraccion del conjunto de entrenamiento a usar")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--lote", type=int, default=16, help="imagenes por lote (batch)")
    parser.add_argument("--nombre", required=True, help="nombre de la corrida (carpeta de resultados)")
    parser.add_argument("--reanudar", action="store_true",
                        help="continua una corrida interrumpida desde su last.pt (mismos parametros)")
    argumentos = parser.parse_args()

    if argumentos.reanudar:
        ultimo = CARPETA_RESULTADOS / argumentos.nombre / "weights" / "last.pt"
        if not ultimo.exists():
            raise FileNotFoundError(f"No hay {ultimo} para reanudar")
        inicio = time.time()
        YOLO(str(ultimo)).train(resume=True)
        print(f"\nReanudacion terminada en {(time.time() - inicio) / 60:.1f} min.")
        return

    ruta_datos = Path(argumentos.datos).resolve()
    if not ruta_datos.exists():
        raise FileNotFoundError(f"No existe {ruta_datos}")

    ruta_modelo = Path(argumentos.modelo)
    if not ruta_modelo.exists():
        ruta_modelo = CARPETA_PESOS / argumentos.modelo
    if not ruta_modelo.exists():
        raise FileNotFoundError(f"No existen los pesos de partida {argumentos.modelo}")
    modelo = YOLO(str(ruta_modelo))
    inicio = time.time()
    modelo.train(data=str(ruta_datos), epochs=argumentos.epocas, imgsz=argumentos.imgsz, batch=argumentos.lote,
                 fraction=argumentos.fraccion, device="cpu", seed=SEMILLA, deterministic=True,
                 project=str(CARPETA_RESULTADOS), name=argumentos.nombre, exist_ok=False, plots=True)
    minutos = (time.time() - inicio) / 60

    carpeta = Path(modelo.trainer.save_dir)   # Ultralytics agrega -2, -3... si el nombre ya existe
    registro = {"fecha": datetime.now().isoformat(timespec="seconds"), "ultralytics": version_ultralytics,
                "python": platform.python_version(), "procesador": platform.processor(), "dispositivo": "cpu",
                "datos": str(ruta_datos), "modelo_inicial": argumentos.modelo, "epocas": argumentos.epocas,
                "fraccion": argumentos.fraccion, "imgsz": argumentos.imgsz, "lote": argumentos.lote,
                "semilla": SEMILLA, "minutos_entrenamiento": round(minutos, 1)}
    with open(carpeta / "registro_entrenamiento.json", "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)
    print(f"\nEntrenamiento terminado en {minutos:.1f} min. Resultados en {carpeta}")
    print(f"Mejores pesos: {carpeta / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    main()
