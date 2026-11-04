"""
Fase 7.4: convierte la exportacion JSON de Label Studio (cajas corregidas por los autores) al formato YOLO.

Formato YOLO: por cada imagen un .txt con una linea por caja:  clase x_centro y_centro ancho alto  (0-1, relativos).
Label Studio guarda x, y (esquina superior izquierda), ancho y alto en PORCENTAJE (0-100).

Division entrenamiento/validacion POR VIDEO (no al azar): los cuadros de un mismo video son casi iguales; si se
mezclan, la validacion mediria memoria y no generalizacion. El video de validacion se elige con --video_val.

Uso (desde la carpeta tesis):
  python scripts/convertir_label_studio_a_yolo.py --exportacion data/label_studio/media/export/1/<archivo>.json
Salida: data/processed/hotwheels_propio/{images,labels}/{train,val}/ + resumen_conversion.json
"""
import argparse
import json
import shutil
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
CARPETA_IMAGENES = CARPETA_TESIS / "data" / "raw" / "hotwheels" / "cuadros_entrenamiento"
CARPETA_SALIDA = CARPETA_TESIS / "data" / "processed" / "hotwheels_propio"
CLASES = {"Car": 0}


def caja_a_yolo(valor):
    """Label Studio (x, y, ancho, alto en %, esquina sup. izq.) -> YOLO (centro x, centro y, ancho, alto en 0-1)."""
    if valor.get("rotation", 0) != 0:
        raise ValueError(f"Caja rotada ({valor['rotation']} grados): YOLO no admite cajas rotadas")
    x, y, ancho, alto = (valor[k] / 100 for k in ("x", "y", "width", "height"))
    # recortar a la imagen por si una caja se dibujo un poco por fuera
    x1, y1, x2, y2 = max(0.0, x), max(0.0, y), min(1.0, x + ancho), min(1.0, y + alto)
    return (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1


def main():
    parser = argparse.ArgumentParser(description="Label Studio JSON -> dataset YOLO")
    parser.add_argument("--exportacion", required=True)
    parser.add_argument("--video_val", default="v0580", help="prefijo de los cuadros que van a validacion")
    argumentos = parser.parse_args()

    tareas = json.loads(Path(argumentos.exportacion).read_text(encoding="utf-8"))
    if CARPETA_SALIDA.exists():
        shutil.rmtree(CARPETA_SALIDA)
    resumen = {"exportacion": argumentos.exportacion, "video_val": argumentos.video_val,
               "train": {"imagenes": 0, "cajas": 0}, "val": {"imagenes": 0, "cajas": 0}, "omitidas": []}

    for tarea in tareas:
        nombre = tarea["data"]["image"].split("/")[-1]
        anotaciones = [a for a in tarea["annotations"] if not a.get("was_cancelled")]
        if len(anotaciones) != 1:
            resumen["omitidas"].append({"imagen": nombre, "anotaciones_validas": len(anotaciones)})
            continue
        lineas = []
        for region in anotaciones[0]["result"]:
            if region["type"] != "rectanglelabels":
                continue
            etiqueta = region["value"]["rectanglelabels"][0]
            xc, yc, ancho, alto = caja_a_yolo(region["value"])
            if ancho <= 0 or alto <= 0:
                raise ValueError(f"Caja vacia en {nombre}")
            lineas.append(f"{CLASES[etiqueta]} {xc:.6f} {yc:.6f} {ancho:.6f} {alto:.6f}")

        particion = "val" if nombre.startswith(argumentos.video_val) else "train"
        (CARPETA_SALIDA / "images" / particion).mkdir(parents=True, exist_ok=True)
        (CARPETA_SALIDA / "labels" / particion).mkdir(parents=True, exist_ok=True)
        shutil.copy2(CARPETA_IMAGENES / nombre, CARPETA_SALIDA / "images" / particion / nombre)
        (CARPETA_SALIDA / "labels" / particion / f"{Path(nombre).stem}.txt").write_text(
            "\n".join(lineas) + ("\n" if lineas else ""), encoding="utf-8")   # .txt vacio = imagen sin carros
        resumen[particion]["imagenes"] += 1
        resumen[particion]["cajas"] += len(lineas)

    (CARPETA_SALIDA / "resumen_conversion.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False),
                                                           encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
