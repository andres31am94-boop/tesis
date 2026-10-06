"""Lectura de los archivos de configuracion (carpeta config/)."""
from pathlib import Path

import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[2]
ARCHIVO_INTERSECCION = CARPETA_TESIS / "config" / "interseccion.yaml"

CLAVES_OBLIGATORIAS = ["semaforo_id", "espacio_por_vehiculo_m", "brazos", "luces"]


def cargar_interseccion(ruta=ARCHIVO_INTERSECCION):
    """Devuelve la configuracion de la interseccion como diccionario."""
    with open(ruta, encoding="utf-8") as archivo:
        datos = yaml.safe_load(archivo)
    faltantes = [clave for clave in CLAVES_OBLIGATORIAS if clave not in datos]
    if faltantes:
        raise KeyError(f"Faltan claves en {ruta}: {faltantes}")
    return datos
