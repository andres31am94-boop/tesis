"""Plano definitivo (versión simplificada) de la base de la maqueta + brazo de madera para la cámara.

Orientación = maqueta real: tabla vertical 80 x 110 cm, Cra 23 vertical, PUENTE ARRIBA.
Origen: esquina superior izquierda de la tabla (x a la derecha, y hacia abajo), mm. z = altura sobre la mesa.

Diseño: 8 piezas de madera (con travesaño F).
  Base (4): 2 largueros + 2 cabezales de listón 2x2" (4,5 cm libres + tacos de goma).
            El larguero DERECHO va al ras del borde de la tabla: ahí se atornilla el poste.
  Brazo (3): poste + brazo recto + refuerzo de listón 2x2". El poste queda frente al final de la Dg 15
            (sobre la línea amarilla, fuera de la tabla) para que el brazo vaya RECTO al centro del cruce.

Salida: hardware/maqueta/montaje_madera.{pdf,png}
Uso:    python scripts/generar_montaje_madera.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "hardware" / "maqueta"

# ---------- tabla (puente arriba) ----------
ANCHO, LARGO, ESPESOR_TABLA = 800, 1100, 15          # MEDIR el espesor real
CRA23_X, DG15_Y = (280, 520), (430, 670)
PUENTE_X, PUENTE_FIN_Y, PUENTE_INICIO_Y = (340, 460), 218, 258   # 1 carril por sentido entre y=0 y 218
CENTRO = (400, 550)
SEMAFOROS = {"S2": (255, 405), "S3": (545, 405), "S4": (255, 695), "S1": (545, 695)}

# ---------- base: listón pino 2x2" (4,5 x 4,5 cm), la misma sección que el brazo ----------
L_ANCHO, L_ALTO = 45, 45
RETIRO_LADOS, RETIRO_PUNTAS = 40, 85                 # COMO QUEDÓ ARMADA: base centrada, 4 cm libres a cada lado
LARGUERO = LARGO - 2 * RETIRO_PUNTAS                 # 930
X_LARG_IZQ = RETIRO_LADOS                            # 40 .. 85
X_LARG_DER = ANCHO - RETIRO_LADOS - L_ANCHO          # 715 .. 760
CABEZAL = X_LARG_DER - (X_LARG_IZQ + L_ANCHO)        # 638
MUESCA = 25
TRAVESANO_Y = 550                                  # travesaño F centrado (así quedó)
TACO_LARGO = 100                                   # taco separador entre larguero derecho y borde

# ---------- brazo: listón pino 2x2" (4,5 x 4,5 cm) ----------
P = 45
TACOS = 10                                           # patas de 1 cm
Z_TABLA = TACOS + L_ALTO + ESPESOR_TABLA             # 70
ALTURA_LENTE = 1000                                  # sobre la superficie de la tabla
LENTE_A_BRAZO = 45                                   # celular + pinza
POSTE_LARGO = 1300
BRAZO_LARGO = 550
REFUERZO = 300
POSTE_Y = CENTRO[1] + P                              # 595: el brazo va pegado a la cara del poste que mira al centro
Z_LENTE = Z_TABLA + ALTURA_LENTE                     # 1080
Z_BRAZO = Z_LENTE + LENTE_A_BRAZO                    # 1125 (cara de abajo del brazo)
X_BRAZO_FIN = ANCHO + P                              # 845
X_BRAZO_INI = X_BRAZO_FIN - BRAZO_LARGO              # 295

MADERA, MADERA2, POSTE_C = "#c9a26b", "#b98c52", "#8b5a2b"


def planta(ax):
    g = "#d4d4d4"
    ax.add_patch(Rectangle((0, 0), ANCHO, LARGO, fc="#a9cfa9", ec="k", lw=1.5, alpha=0.6))
    ax.add_patch(Polygon([(PUENTE_X[0], 0), (PUENTE_X[1], 0), (PUENTE_X[1], PUENTE_FIN_Y), (CRA23_X[1], PUENTE_INICIO_Y),
                          (CRA23_X[1], LARGO), (CRA23_X[0], LARGO), (CRA23_X[0], PUENTE_INICIO_Y),
                          (PUENTE_X[0], PUENTE_FIN_Y)], fc=g, ec="none", alpha=0.7))
    ax.add_patch(Rectangle((0, DG15_Y[0]), ANCHO, DG15_Y[1] - DG15_Y[0], fc=g, ec="none", alpha=0.7))
    ax.text(400, 30, "PUENTE", ha="center", fontsize=8, weight="bold")
    m = dict(fc=MADERA, ec="#5a3510", lw=1.1, hatch="///", alpha=0.85)
    y0 = RETIRO_PUNTAS
    ax.add_patch(Rectangle((X_LARG_IZQ, y0), L_ANCHO, LARGUERO, **m))
    ax.add_patch(Rectangle((X_LARG_DER, y0), L_ANCHO, LARGUERO, **m))
    for y in (y0, y0 + LARGUERO - L_ANCHO):
        ax.add_patch(Rectangle((X_LARG_IZQ + L_ANCHO, y), CABEZAL, L_ANCHO, **dict(m, fc=MADERA2)))
    ax.add_patch(Rectangle((X_LARG_IZQ + L_ANCHO, TRAVESANO_Y - L_ANCHO / 2), CABEZAL, L_ANCHO, **dict(m, fc="#e0bd8a")))
    ax.text(150, TRAVESANO_Y + 12, "F", fontsize=12, weight="bold")
    ax.text(X_LARG_IZQ + 6, 320, "A", fontsize=12, weight="bold"); ax.text(X_LARG_DER + 6, 320, "A", fontsize=12, weight="bold")
    ax.text(420, y0 + 32, "B", fontsize=12, weight="bold"); ax.text(420, y0 + LARGUERO - 9, "B", fontsize=12, weight="bold")
    ax.plot([CENTRO[0] - 82, -60], [CENTRO[1] + 57, CENTRO[1] + 57], color="#555", lw=2)
    ax.text(-215, CENTRO[1] + 85, "USB al PC\n(pasa por\ndebajo del\nlarguero)", fontsize=7, color="#555")
    for dx in (-20, 20):
        ax.add_patch(Circle((CENTRO[0] + dx, TRAVESANO_Y), 6, fc="w", ec="#d62728", lw=1.2, zorder=5))
    ax.annotate("2 huecos Ø8 en F\n(cables de S2 y S3)", (CENTRO[0] + 20, TRAVESANO_Y), (470, 330), fontsize=7,
                color="#d62728", arrowprops=dict(arrowstyle="->", lw=0.8, color="#d62728"))
    ax.add_patch(Rectangle((X_LARG_DER + L_ANCHO, POSTE_Y - TACO_LARGO / 2), ANCHO - X_LARG_DER - L_ANCHO, TACO_LARGO,
                           fc="#e3a35a", ec="k", lw=1, zorder=4))
    ax.annotate("taco separador 10 cm\n(atornillado al larguero)", (ANCHO - 20, POSTE_Y + 40), (ANCHO + 60, POSTE_Y + 300),
                fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    for (tx, ty) in ((62, 150), (737, 150), (62, 950), (737, 950)):
        ax.plot(tx, ty, marker="x", color="k", ms=6, mew=1.5, zorder=6)
    ax.text(95, 1000, "× tornillos 1½\" desde arriba (en el verde)", fontsize=6.8)
    ax.add_patch(Rectangle((CENTRO[0] - 82, CENTRO[1] + 30), 165, 55, fc="#f2f2f2", ec="k", zorder=3))
    ax.add_patch(Rectangle((CENTRO[0] - 28, CENTRO[1] + 33), 56, 48, fc="#1f4e79", ec="k", zorder=3))
    ax.text(CENTRO[0], CENTRO[1] + 57, "ESP32", color="w", fontsize=6.5, ha="center", va="center", weight="bold", zorder=4)
    for n, (x, y) in SEMAFOROS.items():
        ax.add_patch(Circle((x, y), 9, fc="k"))
        ax.text(x + (-14 if x < 400 else 14), y + (-14 if y < 550 else 26), n, fontsize=7.5, weight="bold",
                ha="right" if x < 400 else "left")
    # poste, brazo y refuerzo (vistos desde arriba)
    ax.add_patch(Rectangle((ANCHO, POSTE_Y - P / 2), P, P, fc=POSTE_C, ec="k", lw=1.2, zorder=5))
    ax.add_patch(Rectangle((X_BRAZO_INI, CENTRO[1] - P / 2), BRAZO_LARGO, P, fc=POSTE_C, ec="k", lw=1, alpha=0.75, zorder=4))
    ax.add_patch(Circle(CENTRO, 12, fc="#d62728", ec="k", zorder=6))
    ax.text(X_BRAZO_INI + 20, CENTRO[1] - P / 2 - 10, "D  brazo (por encima, a 1,1 m)", fontsize=7.5, color="#5a3510", weight="bold")
    ax.annotate("lente sobre el centro\ndel cruce (400, 550)", CENTRO, (130, 900), fontsize=7.5, weight="bold",
                arrowprops=dict(arrowstyle="->", lw=0.8), zorder=7)
    ax.annotate("C  poste, atornillado\nal taco separador", (ANCHO + P / 2, POSTE_Y + 20),
                (ANCHO + 70, POSTE_Y + 150), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8))

    def cota(p1, p2, t, d=(0, 0), **kw):
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="<->", mutation_scale=7, lw=0.7))
        ax.text((p1[0] + p2[0]) / 2 + d[0], (p1[1] + p2[1]) / 2 + d[1], t, fontsize=7, ha="center", va="center", **kw)
    cota((0, -35), (ANCHO, -35), "800", (0, -18))
    cota((-40, 0), (-40, LARGO), "1100", (-20, 0), rotation=90)
    cota((0, 1060), (X_LARG_IZQ, 1060), "40", (0, 14))
    cota((X_LARG_DER + L_ANCHO, 1060), (ANCHO, 1060), "40", (0, 14))
    cota((ANCHO + 110, 0), (ANCHO + 110, RETIRO_PUNTAS), "85", (20, 0))
    cota((ANCHO + 110, RETIRO_PUNTAS), (ANCHO + 110, RETIRO_PUNTAS + LARGUERO), f"A = {LARGUERO}", (22, 0), rotation=90)
    cota((X_LARG_IZQ + L_ANCHO, 140), (X_LARG_DER, 140), f"B = {CABEZAL}", (0, 14))
    cota((ANCHO + 60, 0), (ANCHO + 60, POSTE_Y), f"{POSTE_Y}", (16, 0), rotation=90)
    ax.set_xlim(-230, ANCHO + 330); ax.set_ylim(LARGO + 50, -90); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("1. DESDE ARRIBA (tabla transparente) — mm desde la esquina superior izquierda", fontsize=10,
                 weight="bold", loc="left")


def alzado(ax):
    """Vista de frente a lo largo del brazo (mirando hacia el puente)."""
    ax.add_patch(Rectangle((-80, -25), ANCHO + 330, 25, fc="#bbbbbb", ec="k", lw=0.8))
    ax.text(-70, -13, "mesa", fontsize=7, va="center")
    m = dict(fc=MADERA, ec="#5a3510", lw=1, hatch="///")
    B0, B1 = TACOS, TACOS + L_ALTO
    for x in (X_LARG_IZQ + 5, X_LARG_DER + 5):
        ax.add_patch(Rectangle((x, 0), 35, TACOS, fc="#333"))
    ax.add_patch(Rectangle((X_LARG_IZQ, B0), L_ANCHO, L_ALTO, **m))
    ax.add_patch(Rectangle((X_LARG_DER, B0), L_ANCHO, L_ALTO, **m))
    ax.add_patch(Rectangle((X_LARG_DER + L_ANCHO, B0), ANCHO - X_LARG_DER - L_ANCHO, L_ALTO, fc="#e3a35a", ec="k"))
    ax.add_patch(Rectangle((0, B1), ANCHO, ESPESOR_TABLA, fc="#5a9e5a", ec="k"))
    ax.text(15, B1 + 2, "tabla", fontsize=6.5, color="w")
    ax.add_patch(Rectangle((CENTRO[0] - 82, B1 - 30), 165, 30, fc="#1f4e79", ec="k", alpha=0.8))
    ax.text(CENTRO[0], B1 - 15, "ESP32", color="w", fontsize=6.5, ha="center", va="center")
    for x in (255, 545):
        ax.add_patch(Rectangle((x - 3, Z_TABLA), 6, 30, fc="#222"))
        ax.add_patch(Rectangle((x - 9, Z_TABLA + 30), 18, 60, fc="#111"))
    # poste
    ax.add_patch(Rectangle((ANCHO, 0), P, POSTE_LARGO, fc=POSTE_C, ec="k", lw=1.1))
    for z in (30, 55):
        ax.add_patch(Circle((ANCHO + P / 2, z), 6, fc="#4a6fa5", ec="k", lw=0.7, zorder=5))
    ax.annotate("2 tornillos 3\" poste ↔ taco separador\n(a 3 y 5,5 cm de la mesa)", (ANCHO + P, 42), (ANCHO + 90, 170), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    for i in range(9):
        ax.add_patch(Circle((ANCHO + P / 2, 1050 + i * 25), 3.5, fc="w", ec="k", lw=0.6, zorder=5))
    # brazo
    ax.add_patch(Rectangle((X_BRAZO_INI, Z_BRAZO), BRAZO_LARGO, P, fc=POSTE_C, ec="k", lw=1.1, alpha=0.9))
    for z in (Z_BRAZO + 22,):
        for dx in (12, 33):
            ax.add_patch(Circle((ANCHO + dx, z), 5, fc="#4a6fa5", ec="k", lw=0.7, zorder=6))
    ax.annotate("2 pernos 1/4\"×5\" brazo ↔ poste\n(agujeros del poste cada 25 mm\n= ajuste de altura ±10 cm)",
                (ANCHO + P, Z_BRAZO + 20), (ANCHO + 90, Z_BRAZO - 230), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    # refuerzo 45°
    ax.add_patch(Polygon([(ANCHO, Z_BRAZO - 212), (ANCHO, Z_BRAZO - 170), (ANCHO - 170, Z_BRAZO), (ANCHO - 212, Z_BRAZO)],
                         fc="#d8b07a", ec="k", lw=0.9))
    ax.text(ANCHO - 260, Z_BRAZO - 150, "E  refuerzo 45°", fontsize=7.5, weight="bold")
    # celular
    ax.add_patch(Rectangle((CENTRO[0] - 20, Z_LENTE + 10), 40, LENTE_A_BRAZO - 10, fc="#555", ec="k"))
    ax.add_patch(Rectangle((CENTRO[0] - 75, Z_LENTE), 150, 10, fc="#222", ec="k"))
    ax.add_patch(Polygon([(CENTRO[0], Z_LENTE), (CENTRO[0] - 340, Z_TABLA), (CENTRO[0] + 340, Z_TABLA)], fc="#d62728",
                         alpha=0.07, ec="#d62728", ls="--", lw=0.8))
    ax.annotate("celular: pantalla hacia ARRIBA,\ncámara trasera hacia la tabla", (CENTRO[0] - 70, Z_LENTE + 5),
                (40, Z_LENTE + 150), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.plot([CENTRO[0], CENTRO[0]], [Z_LENTE, Z_TABLA + 10], color="k", lw=0.6, ls=":")
    ax.text(CENTRO[0] + 8, 600, "plomada", fontsize=7)

    def cv(x, a, b, t, lado=1):
        ax.add_patch(FancyArrowPatch((x, a), (x, b), arrowstyle="<->", mutation_scale=7, lw=0.8))
        ax.text(x + lado * 12, (a + b) / 2, t, fontsize=7.5, rotation=90, ha="center", va="center", weight="bold")
    cv(-30, Z_TABLA, Z_LENTE, "1000: lente → tabla", -1)
    cv(-30, 0, TACOS + L_ALTO, "55", -1)
    cv(ANCHO + 300, 0, POSTE_LARGO, f"C = {POSTE_LARGO} (poste)")
    ax.add_patch(FancyArrowPatch((X_BRAZO_INI, Z_BRAZO + 80), (X_BRAZO_FIN, Z_BRAZO + 80), arrowstyle="<->",
                                 mutation_scale=7, lw=0.8))
    ax.text((X_BRAZO_INI + X_BRAZO_FIN) / 2, Z_BRAZO + 100, f"D = {BRAZO_LARGO} (brazo)", ha="center", fontsize=7.5,
            weight="bold")
    ax.set_xlim(-130, ANCHO + 360); ax.set_ylim(-60, POSTE_LARGO + 80); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("2. DE FRENTE (mirando hacia el puente) — alturas en mm desde la mesa", fontsize=10, weight="bold",
                 loc="left")


def caja(ax, x, y, z, dx, dy, dz, c, a=1.0):
    v = [(x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
         (x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)]
    f = [[v[0], v[1], v[2], v[3]], [v[4], v[5], v[6], v[7]], [v[0], v[1], v[5], v[4]],
         [v[2], v[3], v[7], v[6]], [v[1], v[2], v[6], v[5]], [v[0], v[3], v[7], v[4]]]
    ax.add_collection3d(Poly3DCollection(f, facecolors=c, edgecolors="k", linewidths=0.3, alpha=a))


def vista3d(ax):
    y0 = RETIRO_PUNTAS
    z0 = TACOS
    caja(ax, X_LARG_IZQ, y0, z0, L_ANCHO, LARGUERO, L_ALTO, MADERA)
    caja(ax, X_LARG_DER, y0, z0, L_ANCHO, LARGUERO, L_ALTO, MADERA)
    for y in (y0, y0 + LARGUERO - L_ANCHO):
        caja(ax, X_LARG_IZQ + L_ANCHO, y, z0, CABEZAL, L_ANCHO, L_ALTO, MADERA2)
    caja(ax, X_LARG_IZQ + L_ANCHO, TRAVESANO_Y - L_ANCHO / 2, z0, CABEZAL, L_ANCHO, L_ALTO, "#e0bd8a")
    caja(ax, X_LARG_DER + L_ANCHO, POSTE_Y - TACO_LARGO / 2, z0, ANCHO - X_LARG_DER - L_ANCHO, TACO_LARGO, L_ALTO, "#e3a35a")
    caja(ax, 0, 0, z0 + L_ALTO, ANCHO, LARGO, ESPESOR_TABLA, "#5a9e5a", 0.35)
    caja(ax, ANCHO, POSTE_Y - P / 2, 0, P, P, POSTE_LARGO, POSTE_C)
    caja(ax, X_BRAZO_INI, CENTRO[1] - P / 2, Z_BRAZO, BRAZO_LARGO, P, P, POSTE_C)
    caja(ax, CENTRO[0] - 75, CENTRO[1] - 35, Z_LENTE, 150, 70, 10, "#333")
    for (x, y) in SEMAFOROS.values():
        caja(ax, x - 4, y - 4, Z_TABLA, 8, 8, 90, "#111")
    ax.set_xlim(-50, 900); ax.set_ylim(-50, 1150); ax.set_zlim(0, 1350)
    ax.set_box_aspect((950, 1200, 1350)); ax.invert_yaxis(); ax.view_init(elev=20, azim=-50); ax.set_axis_off()


CORTES = [
    ("Pieza", "Material (Homecenter)", "Cant.", "Largo", "Cortes"),
    ("A  larguero", "listón 4,5×4,5 cm", "2", f"{LARGUERO} mm", "recto"),
    ("B  cabezal", "listón 4,5×4,5 cm", "2", f"{CABEZAL} mm", "recto"),
    ("C  poste", "listón 4,5×4,5 cm", "1", f"{POSTE_LARGO} mm", "recto"),
    ("D  brazo", "listón 4,5×4,5 cm", "1", f"{BRAZO_LARGO} mm", "recto"),
    ("E  refuerzo", "listón 4,5×4,5 cm", "1", f"{REFUERZO} mm", "45° ambos lados"),
    ("F  travesaño", "listón 4,5×4,5 cm", "1", f"{CABEZAL} mm", "recto (centrado)"),
    ("G  taco separador", "sobrante del listón", "1", "100 mm", "recto"),
]
COMPRA = [
    "MADERA: listones de 4,5×4,5 cm de 3 m (se usaron 3 de los 4):",
    f"  • listón 1 → A + A + B   • listón 2 → C + B + D + E   • listón 3 → F   • sobrante → G (10 cm)",
    "TORNILLERÍA (la que compraste):",
    "  • tornillos 3½\": base (8 esquinas) + travesaño F (4) + refuerzo E (2)",
    "  • tornillos 3\": taco G ↔ larguero (2) + poste C ↔ taco G (2)",
    "  • 4 tornillos 1½\" desde arriba (tabla ↔ base, en el verde, cabeza hundida y pintada)",
    "  • 2 pernos 1/4\" × 5\" + arandelas + tuercas mariposa (brazo D ↔ poste C)",
    "  • 1 tornillo 1/4\" × 2½\" + 1 tuerca 1/4\" + arandelas (pinza del celular; la tuerca la bloquea)",
    "  • 1 pinza para celular con rosca 1/4\"; 4 tacos de 1 cm; cola; cinta aislante",
    "SEMÁFOROS: pitillo ≈ 5,5 cm pintado negro mate + silicona caliente (arriba y abajo)",
    "BROCAS: 3 mm (guías), 7 mm (pernos), 8 mm (semáforos y huecos de F)",
]
PASOS = [
    "HECHO",
    "1. Base A-B-A-B con travesaño F centrado; tacos de 1 cm.",
    "2. Base centrada bajo la tabla: 4 cm a cada lado largo,",
    "   85 mm en las puntas.",
    "3. Taco G (10 cm) al larguero, lado Dg 15 derecha",
    "   (puente lejos de ti), centrado a 595 mm del borde del puente.",
    "SIGUE",
    "4. 2 huecos Ø8 en F (cables de S2 y S3). Tabla ↔ base:",
    "   4 tornillos 1½\" desde arriba en el verde (marcas ×).",
    "5. Poste C: 2 guías de 3 mm a 3 y 5,5 cm de la punta;",
    "   9 agujeros de 7 mm cada 25 mm entre 1050 y 1250 mm.",
    "   Apoyado en la mesa, vertical, 2 tornillos 3\" al taco G.",
    "6. Brazo D: 2 agujeros a 12 y 33 mm de una punta;",
    "   pernos 1/4\" × 5\" a la cara del poste que mira al puente.",
    "7. Refuerzo E a 45° (2 tornillos 3½\").",
    "8. Semáforos (pitillos) con silicona; ESP32 junto a F, del",
    "   lado de S4 y S1; USB por debajo del larguero.",
    "9. Celular en la pinza (pantalla arriba); plomada del lente",
    "   a (400, 550). Prueba de encuadre en DroidCam.",
]


def main():
    fig = plt.figure(figsize=(16.5, 11.7))
    ax1 = fig.add_axes([0.00, 0.30, 0.36, 0.64]); planta(ax1)
    ax2 = fig.add_axes([0.36, 0.38, 0.44, 0.56]); alzado(ax2)
    ax4 = fig.add_axes([0.79, 0.50, 0.21, 0.44], projection="3d"); vista3d(ax4)
    fig.text(0.80, 0.94, "3. VISTA 3D", fontsize=10, weight="bold")
    ax3 = fig.add_axes([0.02, 0.01, 0.97, 0.31]); ax3.axis("off")
    ax3.text(0, 1.0, "4. LISTA DE CORTES", fontsize=10, weight="bold", va="top")
    xs = [0.0, 0.075, 0.19, 0.225, 0.275]
    for i, fila in enumerate(CORTES):
        for j, c in enumerate(fila):
            ax3.text(xs[j], 0.90 - i * 0.075, c, fontsize=8.2, va="top", weight="bold" if i == 0 else None)
    for i, t in enumerate(COMPRA):
        ax3.text(0.355, 0.90 - i * 0.07, t, fontsize=7.6, va="top",
                 weight="bold" if t.endswith(":") or t.startswith("MADERA") or t.startswith("FERRET") or t.startswith("HERRAM") else None)
    ax3.text(0.355, 1.0, "5. LISTA DE COMPRA", fontsize=10, weight="bold", va="top")
    ax3.text(0.75, 1.0, "6. MONTAJE (en orden)", fontsize=10, weight="bold", va="top")
    for i, t in enumerate(PASOS):
        ax3.text(0.75, 0.90 - i * 0.043, t, fontsize=7.4, va="top")
    fig.suptitle("Base de la maqueta + brazo de madera para la cámara — así quedó armada (puente ARRIBA)", fontsize=13,
                 weight="bold", x=0.01, ha="left", y=0.995)
    fig.text(0.80, 0.40, "Supuestos a verificar:\n• tabla de ≈15 mm de espesor;\n• lente a 1 m (medido con el iPhone\n  grabando video; con DroidCam el\n  encuadre puede cambiar → el brazo\n  sube o baja de a 25 mm).\n\nReemplaza a base_maqueta.pdf,\nsoporte_camara.pdf y\nesquema_completo_maqueta.pdf.", fontsize=7.5, style="italic")
    SALIDA.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(SALIDA / f"montaje_madera.{ext}", dpi=150 if ext == "png" else None)
    print("ok", LARGUERO, CABEZAL, 2 * LARGUERO + 2 * CABEZAL, POSTE_LARGO + BRAZO_LARGO + REFUERZO)


if __name__ == "__main__":
    main()
