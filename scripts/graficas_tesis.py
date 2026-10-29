"""
Figuras y estadistica de la tesis a partir de los resultados GUARDADOS (no corre simulaciones).

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\graficas_tesis.py
Opcional (figuras 10-11, dinamica en el tiempo): antes, correr el semaforo real y el agente con la semilla 1:
  .\\.venv\\Scripts\\python.exe -m src.simulation.ejecutar_escenario --escenario aforo_alto --controlador tiempos_fijos --semilla 1
  .\\.venv\\Scripts\\python.exe -m src.simulation.ejecutar_escenario --escenario aforo_alto --controlador qlearning --modelo aforo_v8 --semilla 1
  (igual con aforo_bajo)

Salida: docs/figuras/*.png y docs/figuras/estadistica_evaluacion_final.md

Pruebas estadisticas (evaluacion final, 30 semillas pareadas por escenario):
  - Wilcoxon de rangos con signo (principal) + r biserial de rangos (tamano del efecto); Holm en las secundarias.
  - IC 95 % bootstrap de la mediana de las diferencias pareadas (10 000 remuestreos, semilla fija).
  - Sensibilidad: Shapiro-Wilk de las diferencias, t pareada y d de Cohen (dz); prueba de signos.
Reproducible: mismos archivos de entrada -> mismas figuras y mismas cifras.
"""
import csv
import json
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from scipy.stats import binomtest, rankdata, shapiro, ttest_rel, wilcoxon  # noqa: E402

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))
SALIDA = CARPETA_TESIS / "docs" / "figuras"
COMPARACION = CARPETA_TESIS / "results" / "comparacion"

ESCENARIOS = ["aforo_bajo", "aforo_valle_manana", "aforo_medio", "aforo_alto", "aforo_pico_jueves"]
NOMBRE_ESC = {"aforo_bajo": "Bajo", "aforo_valle_manana": "Valle (no entrenado)", "aforo_medio": "Medio",
              "aforo_alto": "Alto (pico)", "aforo_pico_jueves": "Jueves (pico)"}
# Paleta validada (skill dataviz, scripts/validate_palette.js): categorica en orden fijo
COLOR_ESC = dict(zip(ESCENARIOS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
COLOR_REAL, COLOR_QL = "#eb6834", "#2a78d6"     # semaforo real / agente
TINTA, TINTA_2, REJILLA, SUPERFICIE = "#0b0b0b", "#52514e", "#e6e5df", "#fcfcfb"
NOMBRE_CTRL = {"tiempos_fijos": "Semáforo real", "qlearning": "Agente Q-Learning"}

# metrica -> (nombre, mayor es mejor)
METRICAS = {
    "espera_total_promedio_s": ("Espera promedio (s)", False),
    "espera_cruce_promedio_s": ("Espera en el cruce (s/veh)", False),
    "detenidos_promedio_total": ("Detenidos promedio", False),
    "tiempo_viaje_promedio_s": ("Tiempo de viaje (s)", False),
    "tiempo_perdido_promedio_s": ("Tiempo perdido (s)", False),
    "velocidad_promedio_kmh": ("Velocidad (km/h)", True),
    "throughput_veh_h": ("Throughput (veh/h)", True),
}
PRINCIPAL = "espera_total_promedio_s"
ALFA = 0.05
RNG = np.random.default_rng(20261029)


def estilo(ax, titulo=None, ylabel=None, xlabel=None):
    if titulo:
        ax.set_title(titulo, loc="left", fontsize=10.5, color=TINTA)
    if ylabel:
        ax.set_ylabel(ylabel, color=TINTA_2, fontsize=9)
    if xlabel:
        ax.set_xlabel(xlabel, color=TINTA_2, fontsize=9)
    ax.set_facecolor(SUPERFICIE)
    ax.grid(axis="y", color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#c9c7bf")
    ax.tick_params(colors=TINTA_2, labelsize=8.5)


def guardar(figura, nombre, titulo):
    figura.suptitle(titulo, x=0.01, y=1.03, ha="left", va="bottom", fontsize=12.5, color=TINTA)
    figura.patch.set_facecolor(SUPERFICIE)
    ruta = SALIDA / nombre
    figura.savefig(ruta, dpi=170, bbox_inches="tight", facecolor=SUPERFICIE)
    plt.close(figura)
    print(f"  {ruta.relative_to(CARPETA_TESIS)}")


def leer_corridas(carpeta):
    with open(COMPARACION / carpeta / "corridas.csv", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    datos = {}
    for f in filas:
        datos.setdefault((f["escenario"], f["controlador"]), {})[int(f["semilla"])] = f
    return datos


def pares(datos, escenario, metrica):
    real, ql = datos[(escenario, "tiempos_fijos")], datos[(escenario, "qlearning")]
    semillas = sorted(set(real) & set(ql))
    x = np.array([float(ql[s][metrica]) for s in semillas])
    y = np.array([float(real[s][metrica]) for s in semillas])
    return semillas, x, y


def biserial(diferencias):
    no_nulas = [d for d in diferencias if d != 0]
    if not no_nulas:
        return 0.0
    rangos = rankdata([abs(d) for d in no_nulas])
    pos = sum(r for r, d in zip(rangos, no_nulas) if d > 0)
    neg = sum(r for r, d in zip(rangos, no_nulas) if d < 0)
    return (pos - neg) / (pos + neg)


def holm(valores_p):
    orden = sorted(range(len(valores_p)), key=lambda i: valores_p[i])
    ajustados, maximo = [0.0] * len(valores_p), 0.0
    for posicion, i in enumerate(orden):
        maximo = max(maximo, min(1.0, (len(valores_p) - posicion) * valores_p[i]))
        ajustados[i] = maximo
    return ajustados


def ic_bootstrap_mediana(valores, n=10000):
    muestras = RNG.choice(valores, size=(n, len(valores)), replace=True)
    medianas = np.median(muestras, axis=1)
    return np.percentile(medianas, 2.5), np.percentile(medianas, 97.5)


# ---------------------------------------------------------------------------------------------------------------
def fig_calibracion():
    ruta = CARPETA_TESIS / "results" / "calibracion" / "validacion_sin_calle18" / "resultados.csv"
    if not ruta.exists():
        print("  (sin validacion_sin_calle18: se omite la figura de calibracion)")
        return None
    with open(ruta, encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    figura, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), gridspec_kw={"width_ratios": [1.3, 1]})
    maximo = 1700
    m = np.linspace(1, maximo, 300)
    # GEH = 5  <=>  |sim - aforo| = 5 * sqrt((sim + aforo) / 2): se resuelve sim para cada aforo
    for signo in (1, -1):
        banda = [c + signo * x for c, x in zip(m, [5 * np.sqrt(c) for c in m])]   # aproximacion: (s+c)/2 ~ c
        ax1.plot(m, banda, color=TINTA_2, linewidth=1, linestyle="--")
    ax1.plot([0, maximo], [0, maximo], color=TINTA_2, linewidth=1)
    for esc in ESCENARIOS:
        propias = [f for f in filas if f["escenario"] == esc]
        ax1.scatter([float(f["aforo_veh_h"]) for f in propias], [float(f["simulado_veh_h"]) for f in propias],
                    s=22, color=COLOR_ESC[esc], edgecolor=SUPERFICIE, linewidth=0.8, label=NOMBRE_ESC[esc], zorder=3)
    ax1.text(1250, 1250 + 5 * np.sqrt(1250) + 25, "GEH = 5", color=TINTA_2, fontsize=8, rotation=38)
    ax1.set_xlim(0, maximo)
    ax1.set_ylim(0, maximo)
    estilo(ax1, "Flujo simulado vs aforado (brazo × escenario × semilla)", "simulado (veh/h)", "aforo de campo (veh/h)")
    ax1.legend(frameon=False, fontsize=8, loc="upper left")
    geh = [float(f["geh"]) for f in filas]
    ax2.hist(geh, bins=np.arange(0, 5.5, 0.5), color=COLOR_QL, edgecolor=SUPERFICIE, linewidth=2)
    ax2.axvline(5, color=TINTA_2, linestyle="--", linewidth=1)
    ax2.text(4.9, ax2.get_ylim()[1] * 0.9, "umbral 5", ha="right", fontsize=8, color=TINTA_2)
    estilo(ax2, f"Distribución del GEH (n = {len(geh)}; {sum(g < 5 for g in geh)}/{len(geh)} < 5)",
           "comparaciones", "GEH")
    guardar(figura, "fig01_calibracion_geh.png", "Calibración de la red: la simulación reproduce los aforos")
    return {"n": len(geh), "cumplen": sum(g < 5 for g in geh), "media": statistics.fmean(geh), "max": max(geh)}


def fig_espera_pareada(datos):
    figura, ejes = plt.subplots(1, 5, figsize=(14, 4.6), sharey=False)
    for ax, esc in zip(ejes, ESCENARIOS):
        _, ql, real = pares(datos, esc, PRINCIPAL)
        for a, b in zip(real, ql):
            ax.plot([0, 1], [a, b], color="#c9c7bf", linewidth=0.8, zorder=1)
        ax.scatter(np.zeros(len(real)), real, s=16, color=COLOR_REAL, zorder=2, edgecolor=SUPERFICIE, linewidth=0.6)
        ax.scatter(np.ones(len(ql)), ql, s=16, color=COLOR_QL, zorder=2, edgecolor=SUPERFICIE, linewidth=0.6)
        for x, v, c in ((0, np.median(real), COLOR_REAL), (1, np.median(ql), COLOR_QL)):
            ax.plot([x - 0.18, x + 0.18], [v, v], color=TINTA, linewidth=2, zorder=3)
            ax.text(x + (0.22 if x else -0.22), v, f"{v:.1f}", ha="left" if x else "right", va="center",
                    fontsize=8.5, color=TINTA)
        cambio = 100 * (np.median(ql) - np.median(real)) / np.median(real)
        ax.set_xticks([0, 1], ["Real", "Agente"])
        ax.set_xlim(-0.6, 1.6)
        estilo(ax, f"{NOMBRE_ESC[esc]}\nmediana {cambio:+.1f} %", "espera promedio (s)" if esc == ESCENARIOS[0] else None)
    guardar(figura, "fig02_espera_pareada.png",
            "Espera promedio por vehículo, misma semilla (línea) con el semáforo real y con el agente — 30 semillas")


def fig_cambio_porcentual(datos, resumen):
    figura, ax = plt.subplots(figsize=(10, 4.8))
    for i, esc in enumerate(ESCENARIOS):
        _, ql, real = pares(datos, esc, PRINCIPAL)
        cambio = 100 * (ql - real) / real
        ax.boxplot([cambio], positions=[i], widths=0.45, showfliers=False, patch_artist=True,
                   boxprops={"facecolor": COLOR_ESC[esc] + "33", "edgecolor": COLOR_ESC[esc]},
                   medianprops={"color": TINTA, "linewidth": 1.8}, whiskerprops={"color": COLOR_ESC[esc]},
                   capprops={"color": COLOR_ESC[esc]})
        ax.scatter(i + RNG.uniform(-0.15, 0.15, len(cambio)), cambio, s=12, color=COLOR_ESC[esc], zorder=3,
                   edgecolor=SUPERFICIE, linewidth=0.5)
        bajo, alto = resumen[esc]["ic_pct"]
        ax.text(i, max(cambio) + 2, f"{np.median(cambio):+.1f} %\nIC95 [{bajo:+.1f}, {alto:+.1f}]",
                ha="center", fontsize=8, color=TINTA)
    ax.axhline(0, color=TINTA_2, linewidth=1)
    ax.set_xticks(range(len(ESCENARIOS)), [NOMBRE_ESC[e] for e in ESCENARIOS])
    estilo(ax, "Bajo 0 = el agente espera menos que el semáforo real en esa semilla",
           "cambio en la espera (%)")
    guardar(figura, "fig03_cambio_porcentual.png",
            "Cambio de la espera del agente respecto al semáforo real, por semilla (mediana e IC 95 % bootstrap)")


def fig_mapa_metricas(tabla):
    nombres = list(METRICAS)
    matriz = np.array([[tabla[(e, m)]["mejora_pct"] for e in ESCENARIOS] for m in nombres])
    limite = max(10, np.nanmax(np.abs(matriz)))
    # divergente: naranja (peor) - gris - azul (mejor)
    mapa = LinearSegmentedColormap.from_list("div", ["#c2491b", "#f2b58f", "#ecebe6", "#9fc3ef", "#1f5ea8"])
    figura, ax = plt.subplots(figsize=(10, 4.8))
    ax.imshow(matriz, cmap=mapa, vmin=-limite, vmax=limite, aspect="auto")
    for i, m in enumerate(nombres):
        for j, e in enumerate(ESCENARIOS):
            celda = tabla[(e, m)]
            marca = "*" if celda["significativo"] else ""
            ax.text(j, i, f"{celda['mejora_pct']:+.1f}{marca}", ha="center", va="center", fontsize=9,
                    color="#ffffff" if abs(celda["mejora_pct"]) > 0.6 * limite else TINTA)
    ax.set_xticks(range(len(ESCENARIOS)), [NOMBRE_ESC[e] for e in ESCENARIOS], fontsize=8.5)
    ax.set_yticks(range(len(nombres)), [METRICAS[m][0] for m in nombres], fontsize=8.5)
    ax.tick_params(colors=TINTA_2, length=0)
    for lado in ax.spines.values():
        lado.set_visible(False)
    ax.set_title("Valor = mejora de la mediana (%), positivo = mejor para el agente · * significativo (Holm, α = 0.05)",
                 loc="left", fontsize=9.5, color=TINTA_2)
    guardar(figura, "fig04_mapa_metricas.png", "Todas las métricas en todos los escenarios")


def fig_tiempos_semaforo(datos):
    columnas = [("verde_promedio_cra23_s", "Verde Cra 23 (s)"), ("verde_promedio_dg15_s", "Verde Dg 15 (s)"),
                ("ciclo_promedio_s", "Ciclo (s)")]
    figura, ejes = plt.subplots(1, 3, figsize=(14, 4.4))
    x = np.arange(len(ESCENARIOS))
    for ax, (col, nombre) in zip(ejes, columnas):
        for k, (ctrl, color) in enumerate((("tiempos_fijos", COLOR_REAL), ("qlearning", COLOR_QL))):
            valores = [statistics.fmean(float(f[col]) for f in datos[(e, ctrl)].values()) for e in ESCENARIOS]
            barras = ax.bar(x + (k - 0.5) * 0.38, valores, width=0.36, color=color, label=NOMBRE_CTRL[ctrl],
                            edgecolor=SUPERFICIE, linewidth=2)
            for b, v in zip(barras, valores):
                ax.text(b.get_x() + b.get_width() / 2, v * 1.01 + 0.3, f"{v:.0f}", ha="center", va="bottom",
                        fontsize=7.5, color=TINTA)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
        if col == "ciclo_promedio_s":
            ax.axhspan(60, 120, color=COLOR_ESC["aforo_medio"], alpha=0.08)
            ax.text(len(ESCENARIOS) - 0.5, 121, "rango del Manual 60–120 s", ha="right", fontsize=7.5, color=TINTA_2)
        ax.set_xticks(x, [NOMBRE_ESC[e].split(" ")[0] for e in ESCENARIOS])
        estilo(ax, nombre)
    figura.legend(*ejes[0].get_legend_handles_labels(), frameon=False, fontsize=9, ncol=2, loc="lower center",
                  bbox_to_anchor=(0.5, -0.06))
    guardar(figura, "fig05_tiempos_semaforo.png",
            "Cómo reparte el tiempo cada controlador (promedio de 30 semillas)")


def fig_colas_brazo(datos):
    brazos = ["norte", "sur", "este", "oeste"]
    figura, ejes = plt.subplots(1, 5, figsize=(15, 4.2), sharey=True)
    x = np.arange(len(brazos))
    for ax, esc in zip(ejes, ESCENARIOS):
        for k, (ctrl, color) in enumerate((("tiempos_fijos", COLOR_REAL), ("qlearning", COLOR_QL))):
            valores = [statistics.fmean(float(f[f"cola_promedio_{b}"]) for f in datos[(esc, ctrl)].values())
                       for b in brazos]
            ax.bar(x + (k - 0.5) * 0.38, valores, width=0.36, color=color, label=NOMBRE_CTRL[ctrl],
                   edgecolor=SUPERFICIE, linewidth=2)
        ax.set_xticks(x, ["N", "S", "E", "O"])
        estilo(ax, NOMBRE_ESC[esc], "vehículos detenidos (promedio)" if esc == ESCENARIOS[0] else None)
    figura.legend(*ejes[0].get_legend_handles_labels(), frameon=False, fontsize=9, ncol=2, loc="lower center",
                  bbox_to_anchor=(0.5, -0.07))
    guardar(figura, "fig06_colas_por_brazo.png", "Cola promedio por brazo (N, S = Cra 23; E, O = Dg 15)")


def fig_evolucion():
    versiones = [("aforo_v2", "v2"), ("aforo_v3", "v3"), ("aforo_v4_validacion", "v4"), ("aforo_v5_validacion", "v5"),
                 ("aforo_v6_validacion", "v6"), ("aforo_v7_validacion", "v7"), ("aforo_v8_validacion", "v8"),
                 ("evaluacion_final", "v8\nfinal")]
    disponibles = [(c, n) for c, n in versiones if (COMPARACION / c / "corridas.csv").exists()]
    figura, ax = plt.subplots(figsize=(11, 4.8))
    finales = []
    for esc in ESCENARIOS:
        xs, ys = [], []
        for i, (carpeta, _) in enumerate(disponibles):
            datos = leer_corridas(carpeta)
            if (esc, "qlearning") not in datos or (esc, "tiempos_fijos") not in datos:
                continue
            _, ql, real = pares(datos, esc, PRINCIPAL)
            xs.append(i)
            ys.append(100 * (np.median(ql) - np.median(real)) / np.median(real))
        ax.plot(xs, ys, color=COLOR_ESC[esc], linewidth=2, marker="o", markersize=5, label=NOMBRE_ESC[esc])
        finales.append((ys[-1], xs[-1], esc))
    ax.axhline(0, color=TINTA_2, linewidth=1)
    ax.set_xticks(range(len(disponibles)), [n for _, n in disponibles])
    ax.set_yscale("symlog", linthresh=20)
    # etiquetas del valor final, separadas en la escala del eje para que no se superpongan
    transformar = ax.get_yscale() and ax.yaxis.get_transform()
    previo = None
    for y, x, esc in sorted(finales):
        y_t = transformar.transform(y)
        if previo is not None and y_t - previo < 0.3:
            y_t = previo + 0.3
        previo = y_t
        ax.text(x + 0.12, transformar.inverted().transform(y_t), f"{NOMBRE_ESC[esc].split(' ')[0]} {y:+.0f} %",
                fontsize=8, color=TINTA, va="center")
    ax.set_xlim(-0.3, len(disponibles) - 0.2)
    estilo(ax, "Bajo 0 = mejor que el semáforo real. v2–v3: semillas 1–30 con redes anteriores; v4–v8: validación "
               "(101–110); final: evaluación (1–30)", "cambio de la espera (mediana, %)")
    ax.title.set_fontsize(8.5)
    ax.legend(frameon=False, fontsize=8, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.14))
    guardar(figura, "fig07_evolucion_iteraciones.png",
            "Evolución del agente por iteración (redes y reglas distintas: es historia del desarrollo, no comparación)")


def fig_politica():
    ruta = CARPETA_TESIS / "models" / "aforo_v8" / "tabla_q.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    from src.agent.codificador_estado import CodificadorEstado
    from src.common.configuracion import cargar_interseccion
    from src.controller.safety_guard import EJES
    config = datos["metadatos"]["config_agente"]
    cod = CodificadorEstado(cargar_interseccion(), config)
    n, nt = cod.niveles_cola, cod.niveles_tiempo
    q, visitas = datos["q"], datos["visitas"]
    nombres = ["vacía", "baja", "media", "alta", "muy alta"][:n]
    cortes_t = config["estado"]["cortes_tiempo_verde_s"]
    plan = datos["metadatos"]["config_controlador"]["tiempos_fijos"]["verde_s"]
    figura, ejes = plt.subplots(2, nt, figsize=(13, 8.6))
    for i_eje, eje in enumerate(EJES):
        c = cortes_t[eje]
        etiquetas_t = [f"< {c[0]} s"] + [f"{a}–{b} s" for a, b in zip(c, c[1:])] + [f"≥ {c[-1]} s"]
        for i_t in range(nt):
            ax = ejes[i_eje][i_t]
            ax.set_facecolor(SUPERFICIE)
            for v in range(n):          # fila: eje en verde (presentes)
                for r in range(n):      # columna: eje en rojo (detenidos)
                    n_cra, n_dg = (v, r) if eje == "cra23" else (r, v)
                    s = ((n_cra * n + n_dg) * len(EJES) + i_eje) * nt + i_t
                    total = sum(visitas[s])
                    if total == 0:
                        color, texto = "#ffffff", "·"
                    else:
                        cambia = q[s][1] > q[s][0]
                        color = COLOR_REAL if cambia else COLOR_QL
                        texto = f"{'C' if cambia else 'M'}\n{total}"
                    ax.add_patch(plt.Rectangle((r, n - 1 - v), 0.94, 0.94, color=color,
                                               alpha=0.85 if total else 1, ec=REJILLA))
                    ax.text(r + 0.47, n - 1 - v + 0.47, texto, ha="center", va="center", fontsize=7,
                            color="#ffffff" if total else TINTA_2)
            if all(sum(visitas[((a * n + b) * len(EJES) + i_eje) * nt + i_t]) == 0 for a in range(n) for b in range(n)):
                ax.text(n / 2, n / 2, f"no ocurre:\nverde máximo de {eje.upper()} = "
                        f"{datos['metadatos']['config_controlador']['seguridad']['verde_max_s'][eje]} s",
                        ha="center", va="center", fontsize=10, color=TINTA_2,
                        bbox={"facecolor": SUPERFICIE, "edgecolor": REJILLA})
            ax.set_xlim(0, n)
            ax.set_ylim(0, n)
            ax.set_xticks(np.arange(n) + 0.47, nombres, fontsize=7, rotation=30)
            ax.set_yticks(np.arange(n) + 0.47, nombres[::-1], fontsize=7)
            for lado in ax.spines.values():
                lado.set_visible(False)
            ax.tick_params(length=0, colors=TINTA_2)
            otro = EJES[1 - i_eje]
            ax.set_title(f"Verde en {eje.upper()}, lleva {etiquetas_t[i_t]} (plan: {plan[eje]} s)", loc="left",
                         fontsize=9, color=TINTA)
            ax.set_xlabel(f"cola de {otro.upper()} (en rojo)", fontsize=8, color=TINTA_2)
            if i_t == 0:
                ax.set_ylabel(f"vehículos en {eje.upper()} (en verde)", fontsize=8, color=TINTA_2)
    visitados = sum(1 for v in visitas if sum(v) > 0)
    figura.text(0.01, -0.01, f"M = mantener el verde (azul) · C = cambiar (naranja) · número = veces que el agente vivió "
                f"esa situación · '·' = nunca la vivió (usa el plan real). Estados visitados: {visitados} de "
                f"{len(visitas)}.", fontsize=8.5, color=TINTA_2)
    figura.tight_layout()
    guardar(figura, "fig08_politica_aprendida.png", "Política aprendida por el agente (modelo aforo_v8)")
    return visitados, len(visitas)


def fig_series():
    hechas = []
    for esc in ("aforo_bajo", "aforo_alto"):
        rutas = {ctrl: CARPETA_TESIS / "results" / esc / carpeta / "semilla_1" / "series.csv"
                 for ctrl, carpeta in (("tiempos_fijos", "tiempos_fijos"), ("qlearning", "qlearning_aforo_v8"))}
        if not all(r.exists() for r in rutas.values()):
            print(f"  (faltan series de {esc} semilla 1: se omiten las figuras de dinamica; ver la ayuda del script)")
            continue
        figura, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6.2), gridspec_kw={"height_ratios": [2.2, 1]},
                                          sharex=True)
        for k, (ctrl, color) in enumerate((("tiempos_fijos", COLOR_REAL), ("qlearning", COLOR_QL))):
            with open(rutas[ctrl], encoding="utf-8") as archivo:
                filas = [f for f in csv.DictReader(archivo) if 300 <= float(f["tiempo"]) <= 3600]
            t = np.array([float(f["tiempo"]) for f in filas])
            total = np.array([sum(float(f[f"detenidos_{b}"]) for b in ("norte", "sur", "este", "oeste")) for f in filas])
            suave = np.convolve(total, np.ones(60) / 60, mode="same")
            ax1.plot(t / 60, suave, color=color, linewidth=2, label=NOMBRE_CTRL[ctrl])
            # linea de tiempo de fases: una franja por controlador entre los minutos 30 y 40
            tramo = [(float(f["tiempo"]), f["fase"]) for f in filas if 1800 <= float(f["tiempo"]) <= 2400]
            for tiempo, fase in tramo:
                c = {"verde_cra23": "#1baf7a", "verde_dg15": "#6250d6"}.get(fase, "#d8d6cf")
                ax2.add_patch(plt.Rectangle((tiempo / 60, k), 1 / 60, 0.8, color=c, linewidth=0))
        ax1.legend(frameon=False, fontsize=8.5)
        estilo(ax1, "Vehículos detenidos en los 4 brazos (media móvil de 60 s)", "detenidos")
        ax2.set_ylim(-0.1, 1.9)
        ax2.set_xlim(ax1.get_xlim())
        ax2.set_yticks([0.4, 1.4], ["Real", "Agente"])
        estilo(ax2, "Fases entre los minutos 30 y 40: verde Cra 23 (aqua), verde Dg 15 (violeta), cambio (gris)",
               xlabel="minuto de la simulación")
        ax2.grid(False)
        guardar(figura, f"fig{'10' if esc == 'aforo_bajo' else '11'}_dinamica_{esc}.png",
                f"Dinámica de una corrida — {NOMBRE_ESC[esc]}, semilla 1")
        hechas.append(esc)
    return hechas


# ---------------------------------------------------------------------------------------------------------------
def estadistica(datos):
    tabla, resumen = {}, {}
    for esc in ESCENARIOS:
        filas_esc = []
        for metrica, (nombre, mayor_mejor) in METRICAS.items():
            semillas, ql, real = pares(datos, esc, metrica)
            dif = ql - real
            p = 1.0 if np.all(dif == 0) else wilcoxon(ql, real).pvalue
            med_q, med_r = np.median(ql), np.median(real)
            cambio = 100 * (med_q - med_r) / med_r
            filas_esc.append({"metrica": metrica, "p": p, "r": biserial(dif), "cambio_pct": cambio,
                              "mejora_pct": cambio if mayor_mejor else -cambio, "principal": metrica == PRINCIPAL})
        secundarias = [f for f in filas_esc if not f["principal"]]
        for f, p_aj in zip(secundarias, holm([f["p"] for f in secundarias])):
            f["p_aj"] = p_aj
        for f in filas_esc:
            f.setdefault("p_aj", f["p"])
            f["significativo"] = f["p_aj"] < ALFA
            tabla[(esc, f["metrica"])] = f
        semillas, ql, real = pares(datos, esc, PRINCIPAL)
        dif = ql - real
        cambio_pct = 100 * dif / real
        resumen[esc] = {
            "n": len(semillas), "real": real, "ql": ql, "dif": dif,
            "ic_s": ic_bootstrap_mediana(dif), "ic_pct": ic_bootstrap_mediana(cambio_pct),
            "shapiro_p": shapiro(dif).pvalue, "t_p": ttest_rel(ql, real).pvalue,
            "dz": float(np.mean(dif) / np.std(dif, ddof=1)),
            "signos_p": binomtest(int(np.sum(dif < 0)), int(np.sum(dif != 0)), 0.5).pvalue,
            "mejor": int(np.sum(dif < 0)),
        }
    return tabla, resumen


def escribir_markdown(datos, tabla, resumen, calibracion, politica, series):
    def d(v):
        return f"{v:.2f}"
    lin = ["# Estadística de la evaluación final (generado por scripts/graficas_tesis.py)", "",
           "Modelo `aforo_v8` vs semáforo real; 30 semillas de evaluación (1–30) pareadas por escenario; "
           "métrica principal: tiempo de espera promedio por vehículo (s). Prueba principal: Wilcoxon de rangos con "
           "signo; tamaño del efecto: r biserial de rangos (−1 = el agente es menor en todos los pares). "
           "IC 95 % bootstrap (10 000 remuestreos, semilla 20261029).", "",
           "## 1. Estadística descriptiva (espera promedio, s)", "",
           "| Escenario | Controlador | n | Media | DE | Mediana | Q1 | Q3 | Mín | Máx |", "|---|---|---|---|---|---|---|---|---|---|"]
    for esc in ESCENARIOS:
        for ctrl, valores in (("Semáforo real", resumen[esc]["real"]), ("Agente", resumen[esc]["ql"])):
            q1, q3 = np.percentile(valores, [25, 75])
            lin.append(f"| {NOMBRE_ESC[esc]} | {ctrl} | {len(valores)} | {d(np.mean(valores))} | "
                       f"{d(np.std(valores, ddof=1))} | {d(np.median(valores))} | {d(q1)} | {d(q3)} | "
                       f"{d(np.min(valores))} | {d(np.max(valores))} |")
    lin += ["", "## 2. Prueba principal y tamaño del efecto", "",
            "| Escenario | Cambio entre medianas (%) | Mediana de la diferencia por semilla (s) [IC 95 %] | "
            "Mediana del cambio por semilla (%) [IC 95 %] | Mejor en | Wilcoxon p | r |",
            "|---|---|---|---|---|---|---|"]
    for esc in ESCENARIOS:
        r, t = resumen[esc], tabla[(esc, PRINCIPAL)]
        cambio_semilla = np.median(100 * r["dif"] / r["real"])
        lin.append(f"| {NOMBRE_ESC[esc]} | {t['cambio_pct']:+.1f} | {d(np.median(r['dif']))} "
                   f"[{d(r['ic_s'][0])}, {d(r['ic_s'][1])}] | {cambio_semilla:+.1f} "
                   f"[{r['ic_pct'][0]:+.1f}, {r['ic_pct'][1]:+.1f}] | {r['mejor']}/{r['n']} | {t['p']:.3g} | {t['r']:.2f} |")
    lin += ["", "Nota: el cambio entre medianas compara la mediana del agente con la del real (la cifra que se reporta como "
            "resultado principal); la mediana del cambio por semilla resume las 30 comparaciones pareadas y lleva su IC."]
    lin += ["", "## 3. Sensibilidad (supuestos)", "",
            "Shapiro-Wilk sobre las diferencias pareadas (p < 0.05 = no normales: justifica Wilcoxon); t pareada y d de "
            "Cohen (dz) como comprobación; prueba de signos (no usa magnitudes).", "",
            "| Escenario | Shapiro-Wilk p | t pareada p | dz | Prueba de signos p |", "|---|---|---|---|---|"]
    for esc in ESCENARIOS:
        r = resumen[esc]
        lin.append(f"| {NOMBRE_ESC[esc]} | {r['shapiro_p']:.3g} | {r['t_p']:.3g} | {r['dz']:.2f} | {r['signos_p']:.3g} |")
    lin += ["", "## 4. Todas las métricas (cambio de la mediana, %; p de Wilcoxon, ajustado por Holm en secundarias)", "",
            "| Métrica | " + " | ".join(NOMBRE_ESC[e] for e in ESCENARIOS) + " |", "|---|" + "---|" * len(ESCENARIOS)]
    for m, (nombre, _) in METRICAS.items():
        celdas = []
        for e in ESCENARIOS:
            t = tabla[(e, m)]
            celdas.append(f"{t['cambio_pct']:+.1f} % (p={t['p_aj']:.2g}{' *' if t['significativo'] else ''})")
        lin.append(f"| {nombre} | " + " | ".join(celdas) + " |")
    lin += ["", "## 5. Calidad de las corridas y cumplimiento", "",
            "| Escenario | Controlador | Teleports (30 corr.) | Corridas con vehículos sin terminar | Ciclo prom. (s) | "
            "Ciclo mín.–máx. (s) | % ciclos > 120 s |", "|---|---|---|---|---|---|---|"]
    for esc in ESCENARIOS:
        for ctrl in ("tiempos_fijos", "qlearning"):
            filas = list(datos[(esc, ctrl)].values())
            lin.append(f"| {NOMBRE_ESC[esc]} | {NOMBRE_CTRL[ctrl]} | {int(sum(float(f['teletransportes']) for f in filas))} | "
                       f"{sum(float(f['vehiculos_sin_terminar']) > 0 for f in filas)} | "
                       f"{statistics.fmean(float(f['ciclo_promedio_s']) for f in filas):.1f} | "
                       f"{min(float(f['ciclo_minimo_s']) for f in filas):.0f}–{max(float(f['ciclo_maximo_s']) for f in filas):.0f} | "
                       f"{statistics.fmean(float(f['ciclos_mayores_120_pct']) for f in filas):.1f} |")
    if calibracion:
        lin += ["", "## 6. Calibración (red final)", "",
                f"{calibracion['cumplen']}/{calibracion['n']} comparaciones con GEH < 5; GEH medio "
                f"{calibracion['media']:.2f}; máximo {calibracion['max']:.2f}."]
    lin += ["", "## 7. Política aprendida", "", f"Estados visitados en el entrenamiento: {politica[0]} de {politica[1]}."]
    lin += ["", "## Figuras", ""] + [f"- `{p.name}`" for p in sorted(SALIDA.glob("fig*.png"))]
    if not series:
        lin += ["", "Figuras 10–11 (dinámica en el tiempo) no generadas: faltan las corridas con series (ver el script)."]
    (SALIDA / "estadistica_evaluacion_final.md").write_text("\n".join(lin) + "\n", encoding="utf-8")
    print(f"  {(SALIDA / 'estadistica_evaluacion_final.md').relative_to(CARPETA_TESIS)}")


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    datos = leer_corridas("evaluacion_final")
    tabla, resumen = estadistica(datos)
    print("Figuras:")
    calibracion = fig_calibracion()
    fig_espera_pareada(datos)
    fig_cambio_porcentual(datos, resumen)
    fig_mapa_metricas(tabla)
    fig_tiempos_semaforo(datos)
    fig_colas_brazo(datos)
    fig_evolucion()
    politica = fig_politica()
    series = fig_series()
    escribir_markdown(datos, tabla, resumen, calibracion, politica, series)


if __name__ == "__main__":
    main()
