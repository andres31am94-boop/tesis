"""
Grafica la curva de aprendizaje de un entrenamiento.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe -m src.agent.graficar_curva --nombre prueba_200

Lee  models/<nombre>/curva_aprendizaje.csv
Crea models/<nombre>/curva_aprendizaje.png  (3 paneles con el mismo eje X: episodio)
  1. Recompensa total por episodio (linea clara) y su media movil (linea oscura)
  2. Detenidos promedio por segundo
  3. Epsilon (cuanto exploraba el agente)
Se usan paneles separados en lugar de un segundo eje Y: cada medida tiene su propia escala.
"""
import argparse
import csv
import json

import matplotlib

matplotlib.use("Agg")  # genera el PNG sin abrir ventanas
import matplotlib.pyplot as plt  # noqa: E402

from src.common.configuracion import CARPETA_TESIS  # noqa: E402

COLOR_SERIE = "#2a78d6"        # azul (serie principal)
COLOR_SERIE_CLARA = "#9ec5f4"  # mismo azul, paso claro (datos crudos)
COLOR_TEXTO = "#3d3d3a"
COLOR_REJILLA = "#e6e5df"
VENTANA_MEDIA_MOVIL = 10


def media_movil(valores, ventana):
    salida = []
    for i in range(len(valores)):
        tramo = valores[max(0, i - ventana + 1): i + 1]
        salida.append(sum(tramo) / len(tramo))
    return salida


def estilo(ax, titulo, etiqueta_y):
    ax.set_title(titulo, loc="left", fontsize=11, color=COLOR_TEXTO)
    ax.set_ylabel(etiqueta_y, color=COLOR_TEXTO)
    ax.grid(axis="y", color=COLOR_REJILLA, linewidth=0.8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(COLOR_REJILLA)
    ax.tick_params(colors=COLOR_TEXTO, labelsize=9)


def main():
    parser = argparse.ArgumentParser(description="Grafica la curva de aprendizaje.")
    parser.add_argument("--nombre", required=True)
    args = parser.parse_args()

    carpeta = CARPETA_TESIS / "models" / args.nombre
    with open(carpeta / "curva_aprendizaje.csv", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas:
        raise ValueError("La curva esta vacia.")

    episodios = [int(f["episodio"]) for f in filas]
    recompensa = [float(f["recompensa_total"]) for f in filas]
    detenidos = [float(f["detenidos_promedio"]) for f in filas]
    epsilon = [float(f["epsilon"]) for f in filas]

    figura, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 9), sharex=True,
                                            gridspec_kw={"height_ratios": [3, 2, 1.2]})
    ax1.plot(episodios, recompensa, color=COLOR_SERIE_CLARA, linewidth=1, label="por episodio")
    ax1.plot(episodios, media_movil(recompensa, VENTANA_MEDIA_MOVIL), color=COLOR_SERIE, linewidth=2,
             label=f"media movil ({VENTANA_MEDIA_MOVIL} episodios)")
    ax1.legend(frameon=False, fontsize=9, loc="lower right")
    estilo(ax1, "Recompensa total por episodio (mas alto = menos vehiculos detenidos)", "recompensa")

    ax2.plot(episodios, detenidos, color=COLOR_SERIE_CLARA, linewidth=1, label="por episodio")
    ax2.plot(episodios, media_movil(detenidos, VENTANA_MEDIA_MOVIL), color=COLOR_SERIE, linewidth=2,
             label=f"media movil ({VENTANA_MEDIA_MOVIL} episodios)")
    ax2.legend(frameon=False, fontsize=9, loc="upper right")
    estilo(ax2, "Vehiculos detenidos promedio por segundo (mas bajo = mejor)", "detenidos")

    ax3.plot(episodios, epsilon, color=COLOR_SERIE, linewidth=2)
    ax3.set_ylim(0, 1.05)
    estilo(ax3, "Exploracion (epsilon): 1 = decide al azar, 0 = usa lo aprendido", "epsilon")
    ax3.set_xlabel("episodio (1 episodio = 1 hora simulada)", color=COLOR_TEXTO)

    escenario = "desconocido"
    ruta_tabla = carpeta / "tabla_q.json"
    if ruta_tabla.exists():
        with open(ruta_tabla, encoding="utf-8") as archivo:
            escenario = json.load(archivo).get("metadatos", {}).get("escenario", "desconocido")
    figura.suptitle(f"Curva de aprendizaje — modelo {args.nombre} | escenario: {escenario}",
                    fontsize=12, color=COLOR_TEXTO, x=0.02, ha="left")
    figura.tight_layout()
    ruta_png = carpeta / "curva_aprendizaje.png"
    figura.savefig(ruta_png, dpi=150)
    print(f"Grafica guardada en: {ruta_png}")

    n = min(VENTANA_MEDIA_MOVIL, len(filas))
    print(f"Promedio primeros {n} episodios: recompensa {sum(recompensa[:n]) / n:10.0f} | "
          f"detenidos {sum(detenidos[:n]) / n:.2f}")
    print(f"Promedio ultimos  {n} episodios: recompensa {sum(recompensa[-n:]) / n:10.0f} | "
          f"detenidos {sum(detenidos[-n:]) / n:.2f}")


if __name__ == "__main__":
    main()
