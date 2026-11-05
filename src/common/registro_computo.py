"""
Registro de computo: cada ejecucion de un script del proyecto agrega UNA fila a results/registro_computo.csv con
inicio, fin, duracion (s), script, argumentos, equipo y si termino bien o con error. Asi todo el tiempo de computo
queda medido (pedido de los autores, 2026-11-05) y lo resume scripts/resumen_computo.py.

Uso (una linea al empezar main()):
    from src.common.registro_computo import registrar_ejecucion
    registrar_ejecucion()
La fila se escribe al terminar el programa (atexit), tambien si termina con error o con Ctrl+C.
"""
import atexit
import csv
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

ARCHIVO = Path(__file__).resolve().parents[2] / "results" / "registro_computo.csv"
COLUMNAS = ["inicio", "fin", "segundos", "script", "argumentos", "equipo", "estado"]
_estado = {"registrado": False, "error": None}


def _capturar_error(tipo, valor, traza):
    _estado["error"] = tipo.__name__
    sys.__excepthook__(tipo, valor, traza)


def registrar_ejecucion(nombre=None):
    if _estado["registrado"]:
        return
    _estado["registrado"] = True
    inicio_reloj, inicio = time.monotonic(), datetime.now()
    script = nombre or Path(sys.argv[0]).name
    sys.excepthook = _capturar_error

    def escribir():
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
        nuevo = not ARCHIVO.exists()
        with open(ARCHIVO, "a", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
            if nuevo:
                escritor.writeheader()
            escritor.writerow({"inicio": inicio.isoformat(timespec="seconds"),
                               "fin": datetime.now().isoformat(timespec="seconds"),
                               "segundos": round(time.monotonic() - inicio_reloj, 1), "script": script,
                               "argumentos": " ".join(sys.argv[1:]), "equipo": platform.node(),
                               "estado": f"error: {_estado['error']}" if _estado["error"] else "ok"})
    atexit.register(escribir)
