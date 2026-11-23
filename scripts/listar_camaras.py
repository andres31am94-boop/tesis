"""
Busca las camaras que OpenCV ve en este PC (indices 0 a --max) y guarda un cuadro de cada una, para saber que
indice usar en src/maqueta/lazo_camara.py --fuente <indice> (p. ej. el iPhone como camara web).
Uso: .\\.venv\\Scripts\\python.exe scripts\\listar_camaras.py
Salida: results/maqueta/camaras/camara_<backend>_<indice>.jpg y, en consola, la resolucion y los cuadros por segundo.
Prueba los dos motores de video de Windows: DSHOW (DirectShow) y MSMF (Media Foundation). Algunas camaras virtuales
(p. ej. DroidCam Client reciente) solo entregan imagen por uno de ellos; el otro devuelve un cuadro de "cargando".
"""
import argparse
import time
from pathlib import Path

import cv2
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # carpeta tesis (para src.common.registro_computo)
from src.common.registro_computo import registrar_ejecucion  # noqa: E402

CARPETA = Path(__file__).resolve().parents[1] / "results" / "maqueta" / "camaras"


def main():
    registrar_ejecucion()
    parser = argparse.ArgumentParser(description="Lista las camaras disponibles y guarda un cuadro de cada una")
    parser.add_argument("--max", type=int, default=5)
    parser.add_argument("--ancho", type=int, default=1920, help="resolucion pedida (la camara puede dar otra)")
    parser.add_argument("--alto", type=int, default=1080)
    argumentos = parser.parse_args()
    CARPETA.mkdir(parents=True, exist_ok=True)
    for nombre_backend, backend in (("dshow", cv2.CAP_DSHOW), ("msmf", cv2.CAP_MSMF)):
        for indice in range(argumentos.max + 1):
            probar_camara(nombre_backend, backend, indice, argumentos)


def probar_camara(nombre_backend, backend, indice, argumentos):
    etiqueta = f"camara {indice} ({nombre_backend})"
    captura = cv2.VideoCapture(indice, backend)
    if not captura.isOpened():
        print(f"{etiqueta}: no disponible")
        return
    captura.set(cv2.CAP_PROP_FRAME_WIDTH, argumentos.ancho)
    captura.set(cv2.CAP_PROP_FRAME_HEIGHT, argumentos.alto)
    for _ in range(10):          # descartar los primeros cuadros (ajuste de exposicion)
        captura.read()
    inicio, cuadros, imagen = time.monotonic(), 0, None
    while time.monotonic() - inicio < 2:
        correcto, cuadro = captura.read()
        if correcto:
            cuadros, imagen = cuadros + 1, cuadro
    captura.release()
    if imagen is None:
        print(f"{etiqueta}: abre pero no entrega imagen")
        return
    ruta = CARPETA / f"camara_{nombre_backend}_{indice}.jpg"
    cv2.imwrite(str(ruta), imagen)
    print(f"{etiqueta}: {imagen.shape[1]}x{imagen.shape[0]}, ~{cuadros / 2:.0f} cuadros/s -> {ruta}")


if __name__ == "__main__":
    main()
