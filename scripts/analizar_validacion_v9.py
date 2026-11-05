"""
Analisis de la VALIDACION de aforo_v9 (semillas 101-110): por escenario, mediana de la espera total promedio y
prueba de Wilcoxon de rangos con signo EXACTA (pareada por semilla, bilateral) para:
  tiempos fijos vs v9,  y  v8 vs v9.
v8 se toma de results/comparacion/aforo_v8_validacion (escenarios del aforo) y aforo_v8_validacion_desb (desbalanceados).
No usa scipy: con n = 10 se enumeran los 2^10 signos posibles (p exacto).
Uso: python scripts/analizar_validacion_v9.py  -> results/comparacion/aforo_v9_validacion/resumen_validacion.md
"""
import csv
import itertools
import statistics
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # carpeta tesis (para src.common.registro_computo)
from src.common.registro_computo import registrar_ejecucion  # noqa: E402

CARPETA = Path(__file__).resolve().parents[1] / "results" / "comparacion"
METRICA = "espera_total_promedio_s"
ESCENARIOS = ["aforo_bajo", "aforo_valle_manana", "aforo_medio", "aforo_alto", "aforo_pico_jueves",
              "desb_dg15_cargada", "desb_cra23_sola", "desb_nocturno", "desb_alternante"]


def leer(carpeta, controlador):
    ruta = CARPETA / carpeta / "corridas.csv"
    if not ruta.exists():
        return {}
    with open(ruta, encoding="utf-8") as archivo:
        return {(f["escenario"], int(f["semilla"])): float(f[METRICA])
                for f in csv.DictReader(archivo) if f["controlador"] == controlador}


def wilcoxon_exacto(a, b):
    """p bilateral exacto de Wilcoxon de rangos con signo (diferencias b - a; ceros descartados)."""
    diferencias = [y - x for x, y in zip(a, b) if y != x]
    n = len(diferencias)
    if n == 0:
        return 1.0
    orden = sorted(range(n), key=lambda i: abs(diferencias[i]))
    rangos = [0.0] * n
    i = 0
    while i < n:   # rangos promedio en empates
        j = i
        while j + 1 < n and abs(diferencias[orden[j + 1]]) == abs(diferencias[orden[i]]):
            j += 1
        for k in range(i, j + 1):
            rangos[orden[k]] = (i + j) / 2 + 1
        i = j + 1
    w_mas = sum(r for r, d in zip(rangos, diferencias) if d > 0)
    total = sum(rangos)
    observado = min(w_mas, total - w_mas)
    extremos = sum(1 for signos in itertools.product((0, 1), repeat=n)
                   if min(s := sum(r for r, z in zip(rangos, signos) if z), total - s) <= observado + 1e-9)
    return extremos / 2 ** n


def comparar(base, nuevo, escenario):
    semillas = sorted(s for (e, s) in base if e == escenario and (e, s) in nuevo)
    if not semillas:
        return None
    a = [base[(escenario, s)] for s in semillas]
    b = [nuevo[(escenario, s)] for s in semillas]
    mediana_a, mediana_b = statistics.median(a), statistics.median(b)
    return {"n": len(semillas), "base": mediana_a, "nuevo": mediana_b,
            "dif_pct": 100 * (mediana_b - mediana_a) / mediana_a, "p": wilcoxon_exacto(a, b),
            "mejor": sum(y < x for x, y in zip(a, b))}


def main():
    registrar_ejecucion()
    fijos = leer("aforo_v9_validacion", "tiempos_fijos")
    v9 = leer("aforo_v9_validacion", "qlearning")
    v8 = {**leer("aforo_v8_validacion", "qlearning"), **leer("aforo_v8_validacion_desb", "qlearning")}
    lineas = ["# Validación aforo_v9 (semillas 101–110, espera total promedio por vehículo, s)", "",
              "Mediana por escenario; diferencia relativa de medianas; p = Wilcoxon exacto pareado por semilla (bilateral).", "",
              "| Escenario | Fijos | v9 | v9 vs fijos | p | v9 mejor en | v8 | v9 vs v8 | p | v9 mejor en |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for escenario in ESCENARIOS:
        c1, c2 = comparar(fijos, v9, escenario), comparar(v8, v9, escenario)
        if c1 is None:
            continue
        fila = (f"| {escenario} | {c1['base']:.2f} | {c1['nuevo']:.2f} | {c1['dif_pct']:+.1f} % | {c1['p']:.3f} | "
                f"{c1['mejor']}/{c1['n']} | ")
        fila += (f"{c2['base']:.2f} | {c2['dif_pct']:+.1f} % | {c2['p']:.3f} | {c2['mejor']}/{c2['n']} |" if c2
                 else "– | – | – | – |")
        lineas.append(fila)
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "aforo_v9_validacion" / "resumen_validacion.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
