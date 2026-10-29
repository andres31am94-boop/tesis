"""
Analiza la comparacion final (results/comparacion/<modelo>/corridas.csv).

Para cada escenario y cada metrica compara el agente contra el semaforo real (y contra la referencia con el todo-rojo
de la norma), usando las corridas PAREADAS por semilla:
  - mediana de cada controlador y diferencia relativa de las medianas (%)
  - prueba de rangos con signo de Wilcoxon (bilateral), alfa = 0.05
  - tamano del efecto: correlacion biserial de rangos para pares (r, de -1 a 1; |r| >= 0.5 se considera grande)
  - Metrica PRINCIPAL (hipotesis): tiempo de espera promedio. Metricas SECUNDARIAS: correccion de Holm por escenario
    y comparacion (controla el aumento de falsos positivos al hacer varias pruebas).

Salidas en results/comparacion/<modelo>/:
  resultados.csv        una fila por escenario x comparacion x metrica
  resultados.md         la misma tabla, lista para la tesis
  espera_<escenario>.png  diagrama de cajas del tiempo de espera por controlador

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\analizar_comparacion.py --modelo aforo_v2
Requiere SciPy: .\\.venv\\Scripts\\python.exe -m pip install scipy
"""
import argparse
import csv
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.stats import rankdata, wilcoxon  # noqa: E402

CARPETA_TESIS = Path(__file__).resolve().parents[1]
ALFA = 0.05
PRINCIPAL = "espera_total_promedio_s"
# metrica: (nombre legible, True si MAYOR es mejor)
METRICAS = {
    "espera_total_promedio_s": ("Tiempo de espera promedio (s)", False),
    "espera_cruce_promedio_s": ("Espera en el cruce (s/veh)", False),
    "detenidos_promedio_total": ("Vehiculos detenidos promedio (cola)", False),
    "tiempo_viaje_promedio_s": ("Tiempo de viaje promedio (s)", False),
    "tiempo_perdido_promedio_s": ("Tiempo perdido promedio (s)", False),
    "velocidad_promedio_kmh": ("Velocidad promedio (km/h)", True),
    "throughput_veh_h": ("Throughput (veh/h)", True),
}
COMPARACIONES = [("qlearning", "tiempos_fijos"), ("qlearning", "tiempos_fijos_norma"),
                 ("tiempos_fijos_norma", "tiempos_fijos")]
NOMBRES = {"tiempos_fijos": "Semaforo real", "tiempos_fijos_norma": "Real + todo-rojo norma",
           "qlearning": "Agente Q-Learning"}
COLORES = {"tiempos_fijos": "#7f8c8d", "tiempos_fijos_norma": "#e07b1f", "qlearning": "#2a78d6"}


def biserial_de_rangos(diferencias):
    """Correlacion biserial de rangos para pares: (suma rangos positivos - suma negativos) / suma total.
    Se ignoran las diferencias exactamente 0 (igual que Wilcoxon por defecto)."""
    no_nulas = [d for d in diferencias if d != 0]
    if not no_nulas:
        return 0.0
    rangos = rankdata([abs(d) for d in no_nulas])
    positivos = sum(r for r, d in zip(rangos, no_nulas) if d > 0)
    negativos = sum(r for r, d in zip(rangos, no_nulas) if d < 0)
    return (positivos - negativos) / (positivos + negativos)


def holm(valores_p):
    """Valores p ajustados por Holm-Bonferroni (mismo orden de entrada)."""
    orden = sorted(range(len(valores_p)), key=lambda i: valores_p[i])
    ajustados, maximo = [0.0] * len(valores_p), 0.0
    for posicion, i in enumerate(orden):
        maximo = max(maximo, min(1.0, (len(valores_p) - posicion) * valores_p[i]))
        ajustados[i] = maximo
    return ajustados


def main():
    parser = argparse.ArgumentParser(description="Analiza la comparacion final con Wilcoxon.")
    parser.add_argument("--modelo", required=True, help="carpeta en results/comparacion/ (modelo o carpeta de validacion)")
    args = parser.parse_args()
    carpeta = CARPETA_TESIS / "results" / "comparacion" / args.modelo
    with open(carpeta / "corridas.csv", encoding="utf-8") as archivo:
        corridas = list(csv.DictReader(archivo))

    datos = {}  # (escenario, controlador) -> {semilla: fila}
    for fila in corridas:
        datos.setdefault((fila["escenario"], fila["controlador"]), {})[int(fila["semilla"])] = fila
    escenarios = list(dict.fromkeys(f["escenario"] for f in corridas))

    resultados = []
    for escenario in escenarios:
        for nuevo, base in COMPARACIONES:
            a, b = datos.get((escenario, nuevo), {}), datos.get((escenario, base), {})
            semillas = sorted(set(a) & set(b))
            if len(semillas) < 6:
                continue  # muy pocos pares para la prueba
            filas_comp = []
            for metrica, (nombre, mayor_mejor) in METRICAS.items():
                x = [float(a[s][metrica]) for s in semillas]
                y = [float(b[s][metrica]) for s in semillas]
                diferencias = [xi - yi for xi, yi in zip(x, y)]
                p = 1.0 if all(d == 0 for d in diferencias) else wilcoxon(x, y).pvalue
                med_x, med_y = statistics.median(x), statistics.median(y)
                filas_comp.append({
                    "escenario": escenario, "comparacion": f"{NOMBRES[nuevo]} vs {NOMBRES[base]}", "metrica": nombre,
                    "tipo": "principal" if metrica == PRINCIPAL else "secundaria", "pares": len(semillas),
                    f"mediana_nuevo": round(med_x, 2), "mediana_base": round(med_y, 2),
                    "diferencia_pct": round(100 * (med_x - med_y) / med_y, 1) if med_y else None,
                    "mejora": ("si" if (med_x > med_y) == mayor_mejor and med_x != med_y else "no"),
                    "p_wilcoxon": p, "r_biserial": round(biserial_de_rangos(diferencias), 2)})
            secundarias = [f for f in filas_comp if f["tipo"] == "secundaria"]
            for f, p_aj in zip(secundarias, holm([f["p_wilcoxon"] for f in secundarias])):
                f["p_ajustado"] = p_aj
            for f in filas_comp:
                f.setdefault("p_ajustado", f["p_wilcoxon"])
                f["significativo"] = "si" if f["p_ajustado"] < ALFA else "no"
                f["p_wilcoxon"], f["p_ajustado"] = f"{f['p_wilcoxon']:.4g}", f"{f['p_ajustado']:.4g}"
            resultados += filas_comp

    with open(carpeta / "resultados.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(resultados[0]))
        escritor.writeheader()
        escritor.writerows(resultados)
    columnas = list(resultados[0])
    lineas = ["| " + " | ".join(columnas) + " |", "|" + "---|" * len(columnas)]
    lineas += ["| " + " | ".join(str(f[c]) for c in columnas) + " |" for f in resultados]
    (carpeta / "resultados.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    for escenario in escenarios:
        controladores = [c for c in NOMBRES if (escenario, c) in datos]
        valores = [[float(f[PRINCIPAL]) for f in datos[(escenario, c)].values()] for c in controladores]
        figura, ax = plt.subplots(figsize=(7, 4.5))
        cajas = ax.boxplot(valores, patch_artist=True, widths=0.5)
        for caja, c in zip(cajas["boxes"], controladores):
            caja.set_facecolor(COLORES[c])
            caja.set_alpha(0.6)
        ax.set_xticks(range(1, len(controladores) + 1), [NOMBRES[c] for c in controladores])
        ax.set_ylabel("Tiempo de espera promedio (s)")
        ax.set_title(f"{escenario}: una caja = {len(valores[0])} semillas (mas bajo = mejor)", loc="left", fontsize=11)
        ax.grid(axis="y", color="#e6e5df")
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        figura.tight_layout()
        figura.savefig(carpeta / f"espera_{escenario}.png", dpi=150)
        plt.close(figura)

    print(f"{'escenario':<20}{'comparacion':<45}{'mediana nuevo':>14}{'mediana base':>13}{'dif %':>7}{'p':>10}{'r':>6}  signif.")
    for f in resultados:
        if f["tipo"] == "principal":
            print(f"{f['escenario']:<20}{f['comparacion']:<45}{f['mediana_nuevo']:>14}{f['mediana_base']:>13}"
                  f"{f['diferencia_pct']:>7}{f['p_wilcoxon']:>10}{f['r_biserial']:>6}  {f['significativo']}")
    print(f"\nTabla completa: {carpeta / 'resultados.md'} | graficas: espera_<escenario>.png")


if __name__ == "__main__":
    main()
