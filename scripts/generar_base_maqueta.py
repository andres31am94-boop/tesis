"""Genera el plano de la base (bastidor) de la maqueta, donde va el ESP32 debajo de la tabla.

Orientación = la de la maqueta pintada: tabla vertical 80 x 110 cm, Cra 23 vertical, puente ABAJO.
Origen: esquina superior izquierda, mm.

Salida: hardware/maqueta/base_maqueta.{pdf,png,svg}
Uso:    python scripts/generar_base_maqueta.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "hardware" / "maqueta"

ANCHO_TABLA, ALTO_TABLA = 800, 1100
ESPESOR_TABLA = 15            # medir la tabla real
CRA23_X = (280, 520)
DG15_Y = (430, 670)
PUENTE_INICIO_Y, PUENTE_FIN_Y = 842, 882
PUENTE_X = (340, 460)
CENTRO = (400, 550)

# Bastidor: listón 45 x 70 mm puesto de canto
RETIRO = 80                   # distancia del borde de la tabla al bastidor (deja pasar la unión del poste)
LISTON_ANCHO, ALTURA_BASE = 45, 70
TRAVESANOS_Y = (300, 800)     # travesaños intermedios (fuera de la zona del ESP32)
MUESCA_Y, MUESCA = 550, 25    # salida del cable USB en el larguero izquierdo

# Semáforos (base del poste) y electrónica
SEMAFOROS = {"S1": (255, 405), "S4": (545, 405), "S3": (255, 695), "S2": (545, 705)}
PROTOBOARD = (165, 55)        # protoboard de 830 puntos
POSTE_CAMARA_Y = 250


def dibujar_planta(ax):
    gris, verde = "#d4d4d4", "#a9cfa9"
    ax.add_patch(Rectangle((0, 0), ANCHO_TABLA, ALTO_TABLA, fc=verde, ec="k", lw=1.5, alpha=0.55))
    ax.add_patch(Rectangle((CRA23_X[0], 0), CRA23_X[1] - CRA23_X[0], PUENTE_INICIO_Y, fc=gris, ec="none", alpha=0.6))
    ax.add_patch(Polygon([(CRA23_X[0], PUENTE_INICIO_Y), (CRA23_X[1], PUENTE_INICIO_Y),
                          (PUENTE_X[1], PUENTE_FIN_Y), (PUENTE_X[0], PUENTE_FIN_Y)], fc=gris, ec="none", alpha=0.6))
    ax.add_patch(Rectangle((PUENTE_X[0], PUENTE_FIN_Y), PUENTE_X[1] - PUENTE_X[0], ALTO_TABLA - PUENTE_FIN_Y,
                           fc=gris, ec="none", alpha=0.6))
    ax.add_patch(Rectangle((0, DG15_Y[0]), ANCHO_TABLA, DG15_Y[1] - DG15_Y[0], fc=gris, ec="none", alpha=0.6))
    ax.text(CENTRO[0], ALTO_TABLA - 30, "PUENTE", ha="center", fontsize=8, weight="bold")

    madera = dict(fc="#c9a26b", ec="#5a3510", lw=1.2, hatch="///", alpha=0.9)
    x0, y0 = RETIRO, RETIRO
    x1, y1 = ANCHO_TABLA - RETIRO, ALTO_TABLA - RETIRO
    ax.add_patch(Rectangle((x0, y0), LISTON_ANCHO, y1 - y0, **madera))                      # larguero izq.
    ax.add_patch(Rectangle((x1 - LISTON_ANCHO, y0), LISTON_ANCHO, y1 - y0, **madera))      # larguero der.
    for y in (y0, y1 - LISTON_ANCHO):                                                      # cabezales
        ax.add_patch(Rectangle((x0 + LISTON_ANCHO, y), x1 - x0 - 2 * LISTON_ANCHO, LISTON_ANCHO, **madera))
    for y in TRAVESANOS_Y:                                                                 # travesaños
        ax.add_patch(Rectangle((x0 + LISTON_ANCHO, y - LISTON_ANCHO / 2), x1 - x0 - 2 * LISTON_ANCHO,
                               LISTON_ANCHO, **madera))
    # muesca para el USB
    ax.add_patch(Rectangle((x0 - 2, MUESCA_Y - MUESCA / 2), LISTON_ANCHO + 4, MUESCA, fc="w", ec="#d62728", lw=1.2))
    ax.annotate("muesca 25×25 mm\npara el cable USB", (x0, MUESCA_Y), (-150, MUESCA_Y + 150), fontsize=7.5,
                color="#d62728", arrowprops=dict(arrowstyle="->", lw=0.8, color="#d62728"))

    # electrónica bajo el cruce
    pw, ph = PROTOBOARD
    ax.add_patch(Rectangle((CENTRO[0] - pw / 2, CENTRO[1] - ph / 2), pw, ph, fc="#f2f2f2", ec="k", lw=1))
    ax.add_patch(Rectangle((CENTRO[0] - 28, CENTRO[1] - 24), 56, 48, fc="#1f4e79", ec="k", lw=1))
    ax.text(CENTRO[0], CENTRO[1], "ESP32", color="w", fontsize=7, ha="center", va="center", weight="bold")
    ax.annotate("ESP32 + protoboard\n(pegados DEBAJO de la tabla,\nbajo el centro del cruce)", (CENTRO[0] + pw / 2, CENTRO[1] - 10),
                (CENTRO[0] - 110, CENTRO[1] + 345), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    # cable USB
    ax.plot([CENTRO[0] - pw / 2, x0 + LISTON_ANCHO + 30, x0 - 60], [CENTRO[1], MUESCA_Y, MUESCA_Y],
            color="#555", lw=2.2)
    ax.text(x0 - 120, MUESCA_Y - 18, "al PC", fontsize=7.5)

    # semáforos: hueco y cable
    for nombre, (x, y) in SEMAFOROS.items():
        ax.plot([x, CENTRO[0] + (-30 if x < CENTRO[0] else 30)], [y, CENTRO[1] + (-20 if y < CENTRO[1] else 20)],
                color="#e07b00", lw=1.4, ls="--")
        ax.add_patch(Circle((x, y), 9, fc="k", ec="k"))
        ax.text(x + (-22 if x < CENTRO[0] else 22), y + (-18 if y < CENTRO[1] else 30), f"{nombre}\nØ 8 mm",
                fontsize=7, ha="right" if x < CENTRO[0] else "left", weight="bold")

    # poste de la cámara atornillado a la base
    ax.add_patch(Rectangle((ANCHO_TABLA - RETIRO, POSTE_CAMARA_Y - 20), RETIRO, 40, fc="#d8b07a", ec="k", ls="--"))
    ax.add_patch(Rectangle((ANCHO_TABLA, POSTE_CAMARA_Y - 20), 40, 40, fc="#8b5a2b", ec="k"))
    ax.annotate("poste de la cámara,\natornillado al larguero\ncon pieza de unión 4×4 × 8 cm\n+ 2 escuadras (bajo la tabla)",
                (ANCHO_TABLA - RETIRO / 2, POSTE_CAMARA_Y), (ANCHO_TABLA + 50, POSTE_CAMARA_Y - 230), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8))

    def cota(p1, p2, texto, desplaz=(0, 0), **kw):
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="<->", mutation_scale=8, lw=0.8))
        ax.text((p1[0] + p2[0]) / 2 + desplaz[0], (p1[1] + p2[1]) / 2 + desplaz[1], texto, fontsize=7.5,
                ha="center", va="center", **kw)
    cota((0, -40), (ANCHO_TABLA, -40), "800", (0, -22))
    cota((-45, 0), (-45, ALTO_TABLA), "1100", (-25, 0), rotation=90)
    cota((0, 40), (RETIRO, 40), "80", (0, -18))
    cota((x0, y1 + 40), (x1, y1 + 40), f"bastidor {x1 - x0}", (0, 22))
    cota((ANCHO_TABLA + 130, y0), (ANCHO_TABLA + 130, y1), f"bastidor {y1 - y0}", (22, 0), rotation=90)
    for y in TRAVESANOS_Y:
        ax.text(x1 - LISTON_ANCHO - 10, y - LISTON_ANCHO / 2 - 8, f"travesaño y = {y}", fontsize=7, ha="right")

    ax.set_xlim(-200, ANCHO_TABLA + 260)
    ax.set_ylim(ALTO_TABLA + 100, -110)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("1. VISTA DESDE ARRIBA (tabla transparente) — mm, origen arriba-izquierda", fontsize=10,
                 weight="bold", loc="left")


def dibujar_corte(ax):
    """Corte horizontal por el centro del cruce (y = 550), visto de frente."""
    y_mesa = 0
    y_tabla = y_mesa + ALTURA_BASE
    ax.add_patch(Rectangle((-120, y_mesa - 25), ANCHO_TABLA + 300, 25, fc="#bbbbbb", ec="k", lw=0.8))
    ax.text(-110, y_mesa - 13, "mesa", fontsize=7, va="center")
    ax.add_patch(Rectangle((0, y_tabla), ANCHO_TABLA, ESPESOR_TABLA, fc="#5a9e5a", ec="k", lw=1))
    ax.text(15, y_tabla + 4, "tabla", fontsize=6.5, color="w")
    madera = dict(fc="#c9a26b", ec="#5a3510", lw=1, hatch="///")
    ax.add_patch(Rectangle((RETIRO, y_mesa), LISTON_ANCHO, ALTURA_BASE, **madera))
    ax.add_patch(Rectangle((ANCHO_TABLA - RETIRO - LISTON_ANCHO, y_mesa), LISTON_ANCHO, ALTURA_BASE, **madera))
    ax.add_patch(Rectangle((RETIRO - 1, y_tabla - MUESCA), LISTON_ANCHO + 2, MUESCA, fc="w", ec="#d62728", lw=1))
    # escuadras
    for x, s in ((RETIRO + LISTON_ANCHO, 1), (ANCHO_TABLA - RETIRO - LISTON_ANCHO, -1)):
        ax.add_patch(Polygon([(x, y_tabla), (x + s * 30, y_tabla), (x, y_tabla - 30)], fc="#888", ec="k", lw=0.6))
    ax.annotate("escuadra metálica + tornillo corto\n(no atraviesa la tabla)", (RETIRO + LISTON_ANCHO + 12, y_tabla - 12),
                (RETIRO + 70, y_tabla - 140), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.7))
    # semáforos S2 y S1 (en este corte se ven los de la fila superior proyectados)
    for x in (255, 545):
        ax.add_patch(Rectangle((x - 4, y_tabla + ESPESOR_TABLA), 8, 80, fc="#222", ec="k"))
        ax.add_patch(Rectangle((x - 10, y_tabla + ESPESOR_TABLA + 55), 20, 32, fc="#333", ec="k"))
        for k, c in enumerate(("#d62728", "#f2c200", "#2ca02c")):
            ax.add_patch(Circle((x, y_tabla + ESPESOR_TABLA + 81 - k * 10), 3.2, fc=c, ec="none"))
        ax.plot([x, x], [y_tabla + ESPESOR_TABLA, y_tabla - 25], color="#e07b00", lw=1.4)
        ax.plot([x, CENTRO[0] + (-35 if x < CENTRO[0] else 35)], [y_tabla - 25, y_tabla - 35], color="#e07b00",
                lw=1.4, ls="--")
    # protoboard + ESP32 colgando bajo la tabla
    pw = PROTOBOARD[0]
    ax.add_patch(Rectangle((CENTRO[0] - pw / 2, y_tabla - 10), pw, 10, fc="#f2f2f2", ec="k"))
    ax.add_patch(Rectangle((CENTRO[0] - 28, y_tabla - 25), 56, 15, fc="#1f4e79", ec="k"))
    ax.text(CENTRO[0], y_tabla - 18, "ESP32", color="w", fontsize=6, ha="center", va="center")
    ax.annotate("protoboard pegada con doble faz\nbajo la tabla; ESP32 + cables\nocupan ≈ 4 cm hacia abajo",
                (CENTRO[0] + pw / 2, y_tabla - 8), (CENTRO[0] + 130, y_tabla - 120), fontsize=7,
                arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.plot([CENTRO[0] - pw / 2, RETIRO + LISTON_ANCHO, RETIRO, -100],
            [y_tabla - 15, y_tabla - 15, y_tabla - 15, y_tabla - 15], color="#555", lw=2)
    ax.text(-100, y_tabla - 35, "USB al PC\n(por la muesca)", fontsize=7)
    ax.annotate("cables del semáforo\npor huecos de 8 mm", (545, y_tabla + 5), (600, y_tabla + 150), fontsize=7,
                arrowprops=dict(arrowstyle="->", lw=0.7))

    def cota_v(x, y_a, y_b, texto):
        ax.add_patch(FancyArrowPatch((x, y_a), (x, y_b), arrowstyle="<->", mutation_scale=8, lw=0.8))
        ax.text(x + 12, (y_a + y_b) / 2, texto, fontsize=7.5, va="center", weight="bold")
    cota_v(ANCHO_TABLA + 30, y_mesa, y_tabla, "70 mm libres\n(bastidor)")
    cota_v(ANCHO_TABLA + 30, y_tabla, y_tabla + ESPESOR_TABLA, f"{ESPESOR_TABLA} mm tabla (medir)")

    ax.set_xlim(-180, ANCHO_TABLA + 230)
    ax.set_ylim(-60, y_tabla + 230)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("2. CORTE POR EL CENTRO DEL CRUCE (de frente)", fontsize=10, weight="bold", loc="left")


MATERIALES = [
    f"Listón 45×70 mm (≈ 2×3\"), puesto de canto:",
    f"   2 largueros de {ALTO_TABLA - 2 * RETIRO} mm",
    f"   4 piezas de {ANCHO_TABLA - 2 * RETIRO - 2 * LISTON_ANCHO} mm (2 cabezales + 2 travesaños)",
    "8 escuadras metálicas pequeñas + tornillos de 1/2\" (no atraviesan la tabla)",
    "Unión del poste de la cámara: listón 4×4 de 8 cm + 2 escuadras",
    "Tornillos de 2½\" o puntillas + cola blanca para armar el bastidor",
    "4 tacos de goma o fieltro bajo las esquinas (no se desliza)",
    "Broca de 8 mm (huecos de los semáforos) y serrucho/formón (muesca USB)",
    "Cinta doble faz gruesa para la protoboard; bridas o grapas para cables",
]
PASOS = [
    "Medir el espesor real de la tabla y verificar que el bastidor quede 80 mm",
    "   adentro del borde por los 4 lados.",
    "Armar el rectángulo (largueros + cabezales) y los 2 travesaños; revisar escuadra.",
    "Hacer la muesca de 25×25 mm en el larguero izquierdo, a la altura del cruce.",
    "Marcar dónde quedan los 4 semáforos y perforar Ø 8 mm en la base de cada poste.",
    "Poner la tabla boca abajo sobre algo blando (no rayar la pintura), centrar el",
    "   bastidor y fijarlo con las escuadras.",
    "Pegar protoboard + ESP32 bajo el centro del cruce y pasar los cables por los",
    "   huecos (conexiones en hardware/esp32/conexiones.md). Rotular cada cable.",
    "Sacar el USB por la muesca; voltear la tabla y probar los LEDs antes de seguir.",
]


def main():
    fig = plt.figure(figsize=(16.5, 11.7))
    ax1 = fig.add_axes([0.01, 0.04, 0.42, 0.90])
    ax2 = fig.add_axes([0.45, 0.47, 0.54, 0.47])
    ax3 = fig.add_axes([0.46, 0.03, 0.53, 0.40])
    dibujar_planta(ax1)
    dibujar_corte(ax2)
    ax3.axis("off")
    ax3.text(0, 1, "3. MATERIALES", fontsize=10, weight="bold", va="top")
    for i, m in enumerate(MATERIALES):
        ax3.text(0, 0.9 - i * 0.075, ("• " if not m.startswith("   ") else "") + m, fontsize=8.2, va="top")
    ax3.text(0.5, 1, "4. MONTAJE (en orden)", fontsize=10, weight="bold", va="top")
    for i, p in enumerate(PASOS):
        ax3.text(0.5, 0.9 - i * 0.075, p, fontsize=8.2, va="top")
    ax3.text(0, 0.12, "Por qué así: el bastidor deja 7 cm libres bajo la tabla para el ESP32, la protoboard y los cables;\n"
             "queda 8 cm adentro del borde: no se ve desde los lados y por ahí pasa la pieza que une el poste de la\n"
             "cámara con la base; el ESP32 va bajo el centro del cruce porque desde ahí los 4 semáforos quedan a ≈ 20 cm (cables\n"
             "Dupont cortos). Al subir la tabla 7 cm, el poste inferior de la cámara pasa de 60 a 70 cm.",
             fontsize=8, va="top", style="italic")
    fig.suptitle("Base de la maqueta (bastidor) y ubicación del ESP32 — orientación: Cra 23 vertical, puente abajo",
                 fontsize=13, weight="bold", x=0.01, ha="left", y=0.995)
    SALIDA.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png", "svg"):
        fig.savefig(SALIDA / f"base_maqueta.{ext}", dpi=150 if ext == "png" else None)
    print("Plano generado en", SALIDA)


if __name__ == "__main__":
    main()
