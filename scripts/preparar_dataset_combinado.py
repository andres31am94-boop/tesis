"""
Fase 7.5: arma el dataset para el reentrenamiento = imagenes PROPIAS (etiquetadas en Label Studio) + una muestra
del dataset PUBLICO (Hot-wheels-recognition v1).

Por que combinar:
  - Solo propias (89 imagenes): el modelo podria "olvidar" lo aprendido y sobreajustarse a 3 videos.
  - Solo publicas: ya vimos que no basta para el piso, la cinta y la vista de la maqueta.
Por que repetir las propias: con 1000 publicas y 89 propias, las propias serian el 8 % de cada epoca y pesarian
poco. Se copian REPETICIONES veces (cada copia recibe un aumento de datos distinto en cada epoca).

Validacion = solo imagenes propias del video v0580 (el dominio que importa: la maqueta). Asi best.pt se elige por
como funciona en NUESTRO escenario, no en el publico.

Uso (desde la carpeta tesis):  python scripts/preparar_dataset_combinado.py
Salida: data/processed/hotwheels_combinado/ (train.txt, val.txt, data.yaml, copias repetidas, resumen.json)
"""
import argparse
import json
import random
import shutil
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
RUTA_WINDOWS_TESIS = "C:/Users/andre/Documents/tesis"   # el entrenamiento corre en Windows: las listas usan esa ruta
PROPIO = CARPETA_TESIS / "data" / "processed" / "hotwheels_propio"
PUBLICO = CARPETA_TESIS / "data" / "raw" / "datasets_comunidad" / "hot-wheels-recognition_v1" / "train"
SALIDA = CARPETA_TESIS / "data" / "processed" / "hotwheels_combinado"
SEMILLA = 0


def ruta_windows(ruta):
    return RUTA_WINDOWS_TESIS + "/" + ruta.relative_to(CARPETA_TESIS).as_posix()


def main():
    parser = argparse.ArgumentParser(description="Dataset combinado propio + publico")
    parser.add_argument("--repeticiones", type=int, default=5)
    parser.add_argument("--n_publicas", type=int, default=1000)
    argumentos = parser.parse_args()

    # Se puede ejecutar varias veces: las copias que ya existen no se repiten (copiar es lento en este PC).
    (SALIDA / "propias_repetidas" / "images").mkdir(parents=True, exist_ok=True)
    (SALIDA / "propias_repetidas" / "labels").mkdir(parents=True, exist_ok=True)

    lista_train = []
    propias = sorted((PROPIO / "images" / "train").glob("*.jpg"))
    for imagen in propias:
        etiqueta = PROPIO / "labels" / "train" / f"{imagen.stem}.txt"
        for r in range(argumentos.repeticiones):
            destino = SALIDA / "propias_repetidas" / "images" / f"{imagen.stem}_r{r}.jpg"
            if not destino.exists():
                shutil.copy2(imagen, destino)
            shutil.copy2(etiqueta, SALIDA / "propias_repetidas" / "labels" / f"{imagen.stem}_r{r}.txt")
            lista_train.append(ruta_windows(destino))

    publicas = sorted((PUBLICO / "images").glob("*.jpg"))
    muestra = random.Random(SEMILLA).sample(publicas, argumentos.n_publicas)
    for imagen in muestra:
        if not (PUBLICO / "labels" / f"{imagen.stem}.txt").exists():
            raise FileNotFoundError(f"Imagen publica sin etiqueta: {imagen.name}")
        lista_train.append(ruta_windows(imagen))

    lista_val = [ruta_windows(i) for i in sorted((PROPIO / "images" / "val").glob("*.jpg"))]

    (SALIDA / "train.txt").write_text("\n".join(lista_train) + "\n", encoding="utf-8")
    (SALIDA / "val.txt").write_text("\n".join(lista_val) + "\n", encoding="utf-8")
    (SALIDA / "data.yaml").write_text(
        f"# Generado por scripts/preparar_dataset_combinado.py\n"
        f"path: {ruta_windows(SALIDA)}\ntrain: train.txt\nval: val.txt\nnc: 1\nnames: ['Car']\n", encoding="utf-8")
    resumen = {"semilla": SEMILLA, "repeticiones_propias": argumentos.repeticiones,
               "propias_unicas": len(propias), "propias_en_train": len(propias) * argumentos.repeticiones,
               "publicas_disponibles": len(publicas), "publicas_muestreadas": len(muestra),
               "train_total": len(lista_train), "val_propias_v0580": len(lista_val),
               "fraccion_propia_en_train": round(len(propias) * argumentos.repeticiones / len(lista_train), 3)}
    (SALIDA / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
