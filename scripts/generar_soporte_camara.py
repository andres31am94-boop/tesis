"""Genera el plano del soporte de la cámara para la maqueta (tabla 80 x 110 cm).

Orientación del plano = la de la maqueta pintada: tabla vertical (80 cm de ancho, 110 cm de alto),
Cra 23 vertical, puente ABAJO, Dg 15 horizontal. Origen: esquina superior izquierda, mm.

Salida: hardware/maqueta/soporte_camara.{pdf,png,svg}
Uso:    python scripts/generar_soporte_camara.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "hardware" / "maqueta"

# --- Geometría de la tabla (mm) ---
ANCHO_TABLA, ALTO_TABLA = 800, 1100
CRA23_X = (280, 520)          # calzada Cra 23 (vertical)
DG15_Y = (430, 670)           # calzada Dg 15 (horizontal)
PUENTE_INICIO_Y, PUENTE_FIN_Y = 842, 882   # estrechamiento hacia el puente (abajo)
PUENTE_X = (340, 460)
CENTRO = (400, 550)           # centro del cruce = punto bajo el lente

# --- Cámara ---
ALTURA_LENTE = 1000           # mm sobre la superficie de la tabla
CAMPO_LARGO, CAMPO_CORTO = 1020, 680   # medido con el iPhone a 1 m (lado largo paralelo a la Cra 23)

# --- Soporte ---
POSTE = 40                    # sección del listón 4 x 4 cm
POSTE_CENTRO = (ANCHO_TABLA + POSTE / 2, 250)   # fuera del canto derecho, frente al lote verde superior
RETIRO_BASE, LISTON_BASE = 80, 45                # la base está 80 mm adentro del borde (ver base_maqueta.pdf)
UNION = RETIRO_BASE                               # pieza que une el pie del poste con el larguero de la base
LENTE_A_BRAZO = 45            # grosor celular + pinza (aprox.)
BRAZO_ALTO = 40
POSTE_INF, POSTE_SUP = 700, 700
ALTURA_BASE = 70             # bastidor bajo la tabla (ver base_maqueta.pdf)


def dibujar_planta(ax):
    ax.add_patch(Rectangle((0, 0), ANCHO_TABLA, ALTO_TABLA, fc="#5a9e5a", ec="k", lw=1.5))
    gris = "#c9c9c9"
    ax.add_patch(Rectangle((CRA23_X[0], 0), CRA23_X[1] - CRA23_X[0], PUENTE_INICIO_Y, fc=gris, ec="none"))
    ax.add_patch(Polygon([(CRA23_X[0], PUENTE_INICIO_Y), (CRA23_X[1], PUENTE_INICIO_Y),
                          (PUENTE_X[1], PUENTE_FIN_Y), (PUENTE_X[0], PUENTE_FIN_Y)], fc=gris, ec="none"))
    ax.add_patch(Rectangle((PUENTE_X[0], PUENTE_FIN_Y), PUENTE_X[1] - PUENTE_X[0],
                           ALTO_TABLA - PUENTE_FIN_Y, fc=gris, ec="none"))
    ax.add_patch(Rectangle((0, DG15_Y[0]), ANCHO_TABLA, DG15_Y[1] - DG15_Y[0], fc=gris, ec="none"))
    ax.text(CENTRO[0], ALTO_TABLA - 40, "PUENTE", ha="center", fontsize=8, weight="bold")
    ax.text(CENTRO[0] + 40, 120, "Cra 23", ha="center", fontsize=8, rotation=90)
    ax.text(90, DG15_Y[0] + 40, "Dg 15", fontsize=8)

    # Campo de visión de la cámara
    x0, y0 = CENTRO[0] - CAMPO_CORTO / 2, CENTRO[1] - CAMPO_LARGO / 2
    ax.add_patch(Rectangle((x0, y0), CAMPO_CORTO, CAMPO_LARGO, fc="none", ec="#d62728", lw=1.6, ls="--"))
    ax.text(x0 + 10, y0 + 25, f"lo que ve la cámara a 1 m\n≈ {CAMPO_CORTO/10:.0f} × {CAMPO_LARGO/10:.0f} cm",
            color="#d62728", fontsize=7.5, va="top")

    # Poste (atornillado a la base) y brazo
    px, py = POSTE_CENTRO
    x_larguero = ANCHO_TABLA - RETIRO_BASE - LISTON_BASE
    ax.add_patch(Rectangle((x_larguero, 0), LISTON_BASE, ALTO_TABLA, fc="none", ec="#5a3510", lw=1, ls=":"))
    ax.text(x_larguero - 8, 1000, "larguero derecho de la base\n(debajo de la tabla)", fontsize=7, ha="right",
            color="#5a3510")
    ax.add_patch(Rectangle((ANCHO_TABLA - UNION, py - POSTE / 2), UNION, POSTE, fc="#d8b07a", ec="k", lw=1,
                           ls="--"))
    ax.add_patch(Rectangle((px - POSTE / 2, py - POSTE / 2), POSTE, POSTE, fc="#8b5a2b", ec="k", lw=1))
    ax.annotate("poste 4×4 cm\npegado al borde,\natornillado a la\nbase con la pieza\nde unión (8 cm,\npor DEBAJO de\nla tabla)",
                (px + 5, py + 15), (ANCHO_TABLA + 40, py + 120), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.plot([px, CENTRO[0]], [py, CENTRO[1]], color="#8b5a2b", lw=7, solid_capstyle="butt", alpha=0.85)
    largo = ((px - CENTRO[0]) ** 2 + (py - CENTRO[1]) ** 2) ** 0.5
    ax.text((px + CENTRO[0]) / 2 - 60, (py + CENTRO[1]) / 2 - 70, f"brazo: {largo/10:.0f} cm\nentre ejes",
            fontsize=7.5, rotation=-35.5, color="#5a3510", weight="bold")
    ax.add_patch(Circle(CENTRO, 14, fc="#d62728", ec="k"))
    ax.annotate("LENTE sobre el centro\ndel cruce (400, 550)", CENTRO, (CENTRO[0] - 360, CENTRO[1] - 330),
                fontsize=7.5, weight="bold", arrowprops=dict(arrowstyle="->", lw=0.9))

    # Cotas
    def cota(p1, p2, texto, desplaz=(0, 0), **kw):
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="<->", mutation_scale=8, lw=0.8))
        ax.text((p1[0] + p2[0]) / 2 + desplaz[0], (p1[1] + p2[1]) / 2 + desplaz[1], texto,
                fontsize=7.5, ha="center", va="center", **kw)
    cota((0, -40), (ANCHO_TABLA, -40), "800", (0, -22))
    cota((-45, 0), (-45, ALTO_TABLA), "1100", (-25, 0), rotation=90)
    cota((0, CENTRO[1]), (CENTRO[0], CENTRO[1]), "400", (-120, -18))
    cota((ANCHO_TABLA + 110, 0), (ANCHO_TABLA + 110, py), f"{py}", (22, 0), rotation=90)
    cota((CENTRO[0] - 120, 0), (CENTRO[0] - 120, CENTRO[1]), "550", (-22, -150), rotation=90)

    ax.set_xlim(-160, ANCHO_TABLA + 330)
    ax.set_ylim(ALTO_TABLA + 60, -110)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("1. VISTA DESDE ARRIBA (planta) — medidas en mm, origen arriba-izquierda", fontsize=10,
                 weight="bold", loc="left")


def dibujar_alzado(ax):
    """Corte vertical a lo largo del brazo (brazo 'desdoblado')."""
    largo_brazo = ((POSTE_CENTRO[0] - CENTRO[0]) ** 2 + (POSTE_CENTRO[1] - CENTRO[1]) ** 2) ** 0.5
    espesor_tabla = 15
    # mesa y tabla
    y_piso = -espesor_tabla - ALTURA_BASE
    ax.add_patch(Rectangle((-80, y_piso - 25), largo_brazo + 260, 25, fc="#bbbbbb", ec="k", lw=0.8))
    ax.text(-70, y_piso - 15, "mesa", fontsize=7, va="center")
    # bastidor de la base (80 mm adentro del borde)
    ax.add_patch(Rectangle((largo_brazo + 20 - 80 - 45, y_piso), 45, ALTURA_BASE, fc="#c9a26b", ec="k", lw=0.8))
    ax.text(largo_brazo + 20 - 170, y_piso + 30, "bastidor\n7 cm", fontsize=6.5, ha="right")
    ax.add_patch(Rectangle((0, -espesor_tabla), largo_brazo + 20, espesor_tabla, fc="#5a9e5a", ec="k", lw=1))
    ax.text(40, -espesor_tabla / 2, "tabla", fontsize=7, va="center", color="w")
    x_poste = largo_brazo + 20 + POSTE / 2   # el poste queda pegado al canto de la tabla

    base_y = -espesor_tabla - 0  # el poste se apoya en la mesa (y = -espesor - 0 sobre la mesa)
    y_mesa = y_piso
    # poste inferior y superior (solapados)
    ax.add_patch(Rectangle((x_poste - POSTE / 2, y_mesa), POSTE, POSTE_INF, fc="#a0703c", ec="k", lw=1))
    brazo_y = ALTURA_LENTE + LENTE_A_BRAZO
    sup_y0 = brazo_y - POSTE_SUP          # el brazo descansa sobre el poste superior
    solape = y_mesa + POSTE_INF - sup_y0
    ax.add_patch(Rectangle((x_poste + POSTE / 2, sup_y0), POSTE, POSTE_SUP, fc="#8b5a2b", ec="k", lw=1))
    for i in range(9):
        ax.add_patch(Circle((x_poste + POSTE, sup_y0 + 40 + i * 25), 4, fc="w", ec="k", lw=0.6))
    for yy in (y_mesa + POSTE_INF - 60, y_mesa + POSTE_INF - 190):
        ax.add_patch(Circle((x_poste + POSTE, yy), 7, fc="#4a6fa5", ec="k", lw=0.8))
    ax.annotate("2 pernos 1/4\" con mariposa;\nagujeros cada 25 mm en el\nposte superior → ajuste de altura",
                (x_poste + POSTE + 8, y_mesa + POSTE_INF - 120), (x_poste + 290, y_mesa + POSTE_INF - 330),
                fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    # pieza de unión poste ↔ larguero de la base (por debajo de la tabla)
    x_ini = largo_brazo + 20 - UNION
    ax.add_patch(Rectangle((x_ini, y_piso), UNION, 40, fc="#d8b07a", ec="k"))
    for xe, sgn in ((x_ini, 1), (largo_brazo + 20, -1)):
        ax.add_patch(Polygon([(xe, y_piso + 40), (xe + sgn * 25, y_piso + 40), (xe, y_piso + 65)], fc="#888",
                             ec="k", lw=0.6))
    ax.annotate("pieza de unión 4×4 × 8 cm + 2 escuadras:\nel poste queda ATORNILLADO a la base\n"
                "(si se mueve la maqueta, la cámara se mueve con ella)",
                (x_ini + UNION / 2, y_piso + 20), (largo_brazo - 420, 230), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8))

    tope = sup_y0 + POSTE_SUP
    ax.add_patch(Rectangle((-30, brazo_y), x_poste + POSTE * 1.5 + 30, BRAZO_ALTO, fc="#8b5a2b", ec="k", lw=1))
    # refuerzo diagonal
    ax.add_patch(Polygon([(x_poste + POSTE / 2, brazo_y - 220), (x_poste + POSTE / 2, brazo_y - 190),
                          (x_poste + POSTE / 2 - 190, brazo_y), (x_poste + POSTE / 2 - 220, brazo_y)],
                         fc="#c48a4a", ec="k", lw=0.8))
    ax.text(x_poste - 175, brazo_y - 165, "refuerzo 45°\n(o escuadra\nmetálica)", fontsize=7)
    # celular y pinza
    ax.add_patch(Rectangle((-30, ALTURA_LENTE + 10), 70, LENTE_A_BRAZO - 10, fc="#444", ec="k"))
    ax.add_patch(Rectangle((-75, ALTURA_LENTE), 160, 10, fc="#222", ec="k"))
    ax.add_patch(Polygon([(0, ALTURA_LENTE), (-250, 0), (250, 0)], fc="#d62728", alpha=0.08, ec="#d62728",
                         ls="--", lw=0.8))
    ax.annotate("celular con la PANTALLA HACIA ARRIBA\n(cámara trasera mirando a la tabla)\nen pinza con rosca 1/4\"", (0, ALTURA_LENTE + 5),
                (-300, ALTURA_LENTE - 260), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    # plomada
    ax.plot([0, 0], [ALTURA_LENTE, 25], color="k", lw=0.6, ls=":")
    ax.add_patch(Circle((0, 25), 9, fc="#777", ec="k"))
    ax.text(15, 110, "plomada (hilo + tuerca):\ncae en el centro del cruce", fontsize=7)

    # cotas
    def cota_v(x, y1, y2, texto, lado=1):
        ax.add_patch(FancyArrowPatch((x, y1), (x, y2), arrowstyle="<->", mutation_scale=8, lw=0.9))
        ax.text(x + lado * 12, (y1 + y2) / 2, texto, fontsize=8, rotation=90, ha="center", va="center",
                weight="bold")
    cota_v(-120, 0, ALTURA_LENTE, "1000 mm: lente → superficie de la tabla", lado=-1)
    cota_v(x_poste + 200, y_mesa, tope, f"≈ {tope - y_mesa:.0f} mm desde la mesa (solape ≈ {solape/10:.0f} cm)")
    ax.add_patch(FancyArrowPatch((0, brazo_y + 80), (x_poste, brazo_y + 80), arrowstyle="<->",
                                 mutation_scale=8, lw=0.9))
    ax.text(x_poste / 2, brazo_y + 100, f"{largo_brazo:.0f} mm entre lente y eje del poste (brazo de 60 cm)",
            ha="center", fontsize=8, weight="bold")

    ax.set_xlim(-330, x_poste + 640)
    ax.set_ylim(-150, brazo_y + 230)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("2. VISTA DE LADO (a lo largo del brazo)", fontsize=10, weight="bold", loc="left")


MATERIALES = [
    "Poste inferior: listón 4×4 cm, 70 cm (la base sube la tabla 7 cm)",
    "Poste superior: listón 4×4 cm, 70 cm, con agujeros de 7 mm cada 25 mm",
    "Brazo: listón 4×4 cm (o 4×2), 60 cm",
    "Refuerzo: listón 30 cm cortado a 45° o escuadra metálica 15 cm",
    "Pieza de unión: listón 4×4 cm, 8 cm (del poste al larguero de la base)",
    "2 escuadras metálicas + tornillos de 1\" para la unión",
    "3 pernos 1/4\" × 3\" + arandelas + tuercas mariposa",
    "Pinza para celular con rosca 1/4\" (tipo trípode) + tornillo 1/4\"",
    "Hilo y una tuerca (plomada); bridas para el cable USB",
    "Nivel (sirve la app del celular)",
]
PASOS = [
    "Armar el poste: inferior + superior solapados ~25 cm con 2 pernos.",
    "Con la maqueta ya sobre su base: poner el poste pegado al borde derecho, frente al",
    "   lote verde de arriba (y = 250 mm), apoyado en la mesa, y unirlo al larguero con",
    "   la pieza de 8 cm y las 2 escuadras (por debajo de la tabla).",
    "Montar el brazo encima del poste con 1 perno (gira para apuntar).",
    "Celular: pantalla hacia arriba, cámara trasera hacia la tabla;",
    "   lado largo de la imagen a lo largo de la Cra 23.",
    "Con la plomada colgando del LENTE, girar el brazo hasta que caiga en (400, 550).",
    "Atornillar el refuerzo diagonal (deja el brazo fijo).",
    "Nivelar el celular y verificar 1000 mm del lente a la tabla.",
    "Probar encuadre en el PC (DroidCam): bordes de la imagen ~4–6 cm dentro de",
    "   la tabla. Si no, subir/bajar un agujero (25 mm) el poste superior.",
    "Pasar el cable USB por el brazo y el poste con bridas (sin que cuelgue en la vista).",
]


def main():
    fig = plt.figure(figsize=(16.5, 11.7))  # A3 horizontal
    ax1 = fig.add_axes([0.01, 0.06, 0.40, 0.88])
    ax2 = fig.add_axes([0.41, 0.36, 0.58, 0.60])
    ax3 = fig.add_axes([0.42, 0.02, 0.57, 0.33])
    dibujar_planta(ax1)
    dibujar_alzado(ax2)
    ax3.axis("off")
    ax3.text(0, 1, "3. MATERIALES", fontsize=10, weight="bold", va="top")
    for i, m in enumerate(MATERIALES):
        ax3.text(0, 0.9 - i * 0.085, "• " + m, fontsize=8.2, va="top")
    ax3.text(0.47, 1, "4. MONTAJE (en orden)", fontsize=10, weight="bold", va="top")
    for i, p in enumerate(PASOS):
        ax3.text(0.47, 0.9 - i * 0.075, p, fontsize=8.2, va="top")
    fig.suptitle("Soporte de la cámara — maqueta 80 × 110 cm (orientación: Cra 23 vertical, puente abajo)",
                 fontsize=13, weight="bold", x=0.01, ha="left", y=0.995)
    fig.text(0.01, 0.015, "Altura de 1 m y campo ≈ 68 × 102 cm medidos con el iPhone grabando video. Con DroidCam el "
             "campo puede cambiar (16:9 vs 4:3): se confirma con la prueba de encuadre y se ajusta la altura.",
             fontsize=8, style="italic")
    SALIDA.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png", "svg"):
        fig.savefig(SALIDA / f"soporte_camara.{ext}", dpi=150 if ext == "png" else None)
    print("Plano generado en", SALIDA)


if __name__ == "__main__":
    main()
