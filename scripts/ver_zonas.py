"""
Fase 8: dibuja las zonas de config/zonas_camara.yaml sobre una imagen para verificar que cubren el carril de
llegada de cada brazo. Uso:
  .\\.venv\\Scripts\\python.exe scripts\\ver_zonas.py --imagen data\\raw\\hotwheels\\cruce_vacio.jpg
Salida: results/vision/zonas/zonas_<imagen>.jpg
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[1]
COLORES = {"norte": (255, 128, 0), "sur": (0, 200, 255), "este": (0, 220, 0), "oeste": (255, 0, 255)}


def cargar_zonas(ruta=CARPETA_TESIS / "config" / "zonas_camara.yaml"):
    with open(ruta, encoding="utf-8") as archivo:
        config = yaml.safe_load(archivo)
    zonas = {nombre: [tuple(p) for p in puntos] for nombre, puntos in config["zonas"].items() if puntos}
    if not zonas:
        raise ValueError(f"No hay zonas definidas en {ruta}")
    return zonas, config


def dibujar_zonas(imagen, zonas, conteos=None):
    """conteos opcional: {brazo: (presentes, detenidos)} para escribirlos junto a cada zona."""
    alto, ancho = imagen.shape[:2]
    capa = imagen.copy()
    for nombre, puntos in zonas.items():
        poligono = np.array([[int(x * ancho), int(y * alto)] for x, y in puntos], dtype=np.int32)
        color = COLORES.get(nombre, (255, 255, 255))
        cv2.fillPoly(capa, [poligono], color)
        cv2.polylines(imagen, [poligono], True, color, 3)
        x, y = poligono.mean(axis=0).astype(int)
        texto = nombre if conteos is None else f"{nombre}: {conteos[nombre][0]} ({conteos[nombre][1]} det.)"
        cv2.putText(imagen, texto, (x - 60, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 5)
        cv2.putText(imagen, texto, (x - 60, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    return cv2.addWeighted(capa, 0.25, imagen, 0.75, 0)


def main():
    parser = argparse.ArgumentParser(description="Dibuja las zonas de camara sobre una imagen")
    parser.add_argument("--imagen", required=True)
    argumentos = parser.parse_args()
    imagen = cv2.imread(str(Path(argumentos.imagen).resolve()))
    if imagen is None:
        raise FileNotFoundError(f"No se pudo abrir {argumentos.imagen}")
    zonas, _ = cargar_zonas()
    salida = CARPETA_TESIS / "results" / "vision" / "zonas"
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / f"zonas_{Path(argumentos.imagen).stem}.jpg"
    cv2.imwrite(str(ruta), dibujar_zonas(imagen, zonas))
    print(f"Guardado: {ruta}")


if __name__ == "__main__":
    main()
