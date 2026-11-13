"""Plantilla de perforación de los semáforos (orientación: Cra 23 vertical, puente ABAJO; origen arriba-izquierda, mm).
Salida: hardware/maqueta/puntos_semaforos.{pdf,png}"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

SALIDA = Path(__file__).resolve().parents[1] / "hardware" / "maqueta"
A, L = 800, 1100
CRA = (280, 520); DG = (430, 670)
# (x, y, hacia dónde mira, qué tráfico controla)
SEM = {"S1": (255, 405, "arriba", "llega por arriba (Cra 23 sur)"),
       "S4": (545, 405, "derecha", "llega por la derecha (Dg 15)"),
       "S3": (255, 695, "izquierda", "llega por la izquierda (Dg 15)"),
       "S2": (545, 705, "abajo", "llega por abajo, del puente (Cra 23 norte)")}
FLECHA = {"arriba": (0, -60), "abajo": (0, 60), "izquierda": (-60, 0), "derecha": (60, 0)}

fig, ax = plt.subplots(figsize=(8.27, 11.69))
ax.add_patch(Rectangle((0, 0), A, L, fc="#5a9e5a", ec="k", lw=1.5))
g = "#cfcfcf"
ax.add_patch(Polygon([(280, 0), (520, 0), (520, 842), (460, 882), (460, L), (340, L), (340, 882), (280, 842)], fc=g, ec="none"))
ax.add_patch(Rectangle((0, DG[0]), A, DG[1] - DG[0], fc=g, ec="none"))
ax.text(400, L - 25, "PUENTE", ha="center", weight="bold", fontsize=9)
for n, (x, y, mira, txt) in SEM.items():
    ax.add_patch(Circle((x, y), 12, fc="#d62728", ec="k", lw=1.2))
    ax.plot([x - 22, x + 22], [y, y], color="k", lw=0.6); ax.plot([x, x], [y - 22, y + 22], color="k", lw=0.6)
    dx, dy = FLECHA[mira]
    ax.add_patch(FancyArrowPatch((x, y), (x + dx, y + dy), arrowstyle="-|>", mutation_scale=12, lw=1.5, color="#1f4e79"))
    izq = x < 400
    ax.text(x + (-30 if izq else 30), y + (-30 if y < 550 else 45), f"{n}  ({x}, {y})\nmira hacia {mira}\n{txt}",
            ha="right" if izq else "left", va="center", fontsize=8, weight="bold",
            bbox=dict(fc="w", ec="k", lw=0.5, alpha=0.9))
# cotas desde los bordes de la calle (forma práctica de medir)
for (x0, y0, x1, y1, t, off) in [(255, 405, 280, 405, "25", (0, 14)), (255, 405, 255, 430, "25", (-14, 0)),
                                  (545, 705, 520, 705, "25", (0, 14)), (545, 705, 545, 670, "35", (14, 0))]:
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="<->", mutation_scale=6, lw=0.7))
    ax.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], t, fontsize=7, ha="center", va="center")
ax.add_patch(FancyArrowPatch((0, -30), (A, -30), arrowstyle="<->", mutation_scale=8, lw=0.8)); ax.text(400, -48, "800", ha="center", fontsize=8)
ax.add_patch(FancyArrowPatch((-30, 0), (-30, L), arrowstyle="<->", mutation_scale=8, lw=0.8)); ax.text(-50, 550, "1100", rotation=90, va="center", fontsize=8)
ax.set_xlim(-80, A + 40); ax.set_ylim(L + 230, -90); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Puntos para taladrar los semáforos (Ø 8 mm) — mm desde la esquina superior izquierda\n"
             "Tabla con la Cra 23 vertical y el PUENTE ABAJO", fontsize=10, weight="bold")
ax.text(0, L + 70, "Cómo medir: cada hueco va en la esquina del pasto, a 2,5 cm del borde de cada calle\n"
        "(S2 a 3,5 cm de la Dg 15). Antes de taladrar, presentar el semáforo y marcar el centro del poste;\n"
        "taladrar con un taco de madera debajo para que no se astille la pintura por la cara de abajo.\n"
        "Las etiquetas S1–S4 coinciden con los pines del ESP32 (hardware/esp32/conexiones.md).",
        fontsize=8, va="top")
SALIDA.mkdir(parents=True, exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(SALIDA / f"puntos_semaforos.{ext}", dpi=150 if ext == "png" else None, bbox_inches="tight")
print("ok")
