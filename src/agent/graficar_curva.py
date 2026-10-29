"""
Grafica la curva de aprendizaje de un entrenamiento.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe -m src.agent.graficar_curva --nombre aforo_v1

Lee  models/<nombre>/curva_aprendizaje.csv
Crea models/<nombre>/curva_aprendizaje.png  (2 paneles con el mismo eje X: episodio)
  1. Vehiculos detenidos promedio por segundo, UNA LINEA POR ESCENARIO (cada escenario tiene su propio nivel de
     trafico; mezclarlos en una sola linea esconderia si el agente mejora). Puntos = cada episodio;
     linea = media movil de los episodios de ese escenario.
  2. Epsilon (cuanto exploraba el agente)
"""
import argparse
import csv

import matplotlib

matplotlib.use("Agg")  # genera el PNG sin abrir ventanas
import matplotlib.pyplot as plt  # noqa: E402

from src.common.configuracion import CARPETA_TESIS  # noqa: E402

COLOR_SERIE = "#2a78d6"        # azul (serie principal)
COLOR_SERIE_CLARA = "#9ec5f4"  # mismo azul, paso claro (datos crudos)
COLOR_TEXTO = "#3d3d3a"
COLOR_REJILLA = "#e6e5df"
VENTANA_MEDIA_MOVIL = 5   # episodios del MISMO escenario
# Colores categoricos (uno por escenario), distinguibles tambien en escala de grises por su luminosidad
COLORES_ESCENARIO = ["#2a78d6", "#e07b1f", "#2e9e5b", "#8e44ad", "#7f8c8d"]


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
    escenarios = list(dict.fromkeys(f.get("escenario", "unico") for f in filas))  # en orden de aparicion

    figura, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7.5), sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})
    print(f"{'escenario':<20}{'episodios':>10}{'detenidos (primeros ' + str(VENTANA_MEDIA_MOVIL) + ')':>26}"
          f"{'detenidos (ultimos ' + str(VENTANA_MEDIA_MOVIL) + ')':>26}")
    for color, escenario in zip(COLORES_ESCENARIO, escenarios):
        propias = [f for f in filas if f.get("escenario", "unico") == escenario]
        episodios = [int(f["episodio"]) for f in propias]
        detenidos = [float(f["detenidos_promedio"]) for f in propias]
        ax1.scatter(episodios, detenidos, color=color, s=10, alpha=0.35)
        ax1.plot(episodios, media_movil(detenidos, VENTANA_MEDIA_MOVIL), color=color, linewidth=2, label=escenario)
        n = min(VENTANA_MEDIA_MOVIL, len(detenidos))
        print(f"{escenario:<20}{len(propias):>10}{sum(detenidos[:n]) / n:>26.2f}{sum(detenidos[-n:]) / n:>26.2f}")
    ax1.legend(frameon=False, fontsize=9, loc="upper right")
    estilo(ax1, f"Detenidos promedio por segundo (mas bajo = mejor) · linea: media de {VENTANA_MEDIA_MOVIL} "
                f"episodios del mismo escenario", "detenidos")
    ax1.title.set_fontsize(10)

    todos = [int(f["episodio"]) for f in filas]
    ax2.plot(todos, [float(f["epsilon"]) for f in filas], color=COLOR_SERIE, linewidth=2)
    ax2.set_ylim(0, 1.05)
    estilo(ax2, "Exploracion (epsilon): 1 = decide al azar, 0 = usa lo aprendido", "epsilon")
    ax2.set_xlabel("episodio (1 episodio = 1 hora simulada)", color=COLOR_TEXTO)

    figura.suptitle(f"Curva de aprendizaje — modelo {args.nombre}", fontsize=12, color=COLOR_TEXTO, x=0.02, ha="left")
    figura.tight_layout()
    ruta_png = carpeta / "curva_aprendizaje.png"
    figura.savefig(ruta_png, dpi=150)
    print(f"\nGrafica guardada en: {ruta_png}")


if __name__ == "__main__":
    main()
