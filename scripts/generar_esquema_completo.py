"""Esquema completo de la maqueta montada: tabla + base (bastidor) + ESP32 + semáforos + soporte de la cámara.

Una sola hoja con vista 3D, vista lateral y lista de cortes. Mismas medidas que base_maqueta.pdf y
soporte_camara.pdf (orientación: Cra 23 vertical, puente abajo; origen arriba-izquierda; mm).

Salida: hardware/maqueta/esquema_completo_maqueta.{pdf,png}
Uso:    python scripts/generar_esquema_completo.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "hardware" / "maqueta"

ANCHO, LARGO, ESPESOR = 800, 1100, 15
ALTURA_BASE, LISTON_A, RETIRO = 70, 45, 80
TRAVESANOS_Y = (300, 800)
CENTRO = (400, 550)
SEMAFOROS = [(545, 405), (255, 405), (255, 695), (545, 695)]
POSTE, POSTE_Y = 40, 250
ALTURA_LENTE = 1000


def caja(ax, x, y, z, dx, dy, dz, color, alpha=1.0, borde="k"):
    v = [(x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
         (x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)]
    caras = [[v[0], v[1], v[2], v[3]], [v[4], v[5], v[6], v[7]], [v[0], v[1], v[5], v[4]],
             [v[2], v[3], v[7], v[6]], [v[1], v[2], v[6], v[5]], [v[0], v[3], v[7], v[4]]]
    ax.add_collection3d(Poly3DCollection(caras, facecolors=color, edgecolors=borde, linewidths=0.4, alpha=alpha))


def vista_3d(ax):
    z_tabla = ALTURA_BASE
    madera, poste_c = "#c9a26b", "#8b5a2b"
    # bastidor
    x0, x1, y0, y1 = RETIRO, ANCHO - RETIRO, RETIRO, LARGO - RETIRO
    caja(ax, x0, y0, 0, LISTON_A, y1 - y0, ALTURA_BASE, madera)
    caja(ax, x1 - LISTON_A, y0, 0, LISTON_A, y1 - y0, ALTURA_BASE, madera)
    for y in (y0, y1 - LISTON_A):
        caja(ax, x0 + LISTON_A, y, 0, x1 - x0 - 2 * LISTON_A, LISTON_A, ALTURA_BASE, madera)
    for y in TRAVESANOS_Y:
        caja(ax, x0 + LISTON_A, y - LISTON_A / 2, 0, x1 - x0 - 2 * LISTON_A, LISTON_A, ALTURA_BASE, madera)
    # electrónica bajo el cruce
    caja(ax, CENTRO[0] - 82, CENTRO[1] - 27, z_tabla - 40, 165, 55, 40, "#1f4e79")
    # tabla (semitransparente para ver la base)
    caja(ax, 0, 0, z_tabla, ANCHO, LARGO, ESPESOR, "#5a9e5a", alpha=0.35)
    # vías dibujadas encima
    zt = z_tabla + ESPESOR + 0.5
    ax.add_collection3d(Poly3DCollection([[(280, 0, zt), (520, 0, zt), (520, 842, zt), (460, 882, zt),
                                           (460, LARGO, zt), (340, LARGO, zt), (340, 882, zt), (280, 842, zt)]],
                                         facecolors="#cfcfcf", edgecolors="none", alpha=0.8))
    ax.add_collection3d(Poly3DCollection([[(0, 430, zt), (ANCHO, 430, zt), (ANCHO, 670, zt), (0, 670, zt)]],
                                         facecolors="#cfcfcf", edgecolors="none", alpha=0.8))
    # semáforos
    for x, y in SEMAFOROS:
        caja(ax, x - 4, y - 4, zt, 8, 8, 60, "#222")
        caja(ax, x - 10, y - 8, zt + 55, 20, 16, 32, "#333")
    # soporte de cámara
    px = ANCHO
    caja(ax, px, POSTE_Y - POSTE / 2, 0, POSTE, POSTE, 700, poste_c)
    caja(ax, ANCHO - RETIRO, POSTE_Y - POSTE / 2, 0, RETIRO, POSTE, 40, "#d8b07a")   # unión con la base
    caja(ax, px + POSTE, POSTE_Y - POSTE / 2, zt + ALTURA_LENTE + 45 - 700, POSTE, POSTE, 700, poste_c)
    z_brazo = zt + ALTURA_LENTE + 45
    # brazo como prisma orientado hacia el centro
    import numpy as np
    p0 = np.array([px + POSTE, POSTE_Y]); p1 = np.array(CENTRO, dtype=float)
    d = (p1 - p0) / np.linalg.norm(p1 - p0); n = np.array([-d[1], d[0]]) * 20
    base = [p0 + n, p1 + n, p1 - n, p0 - n]
    abajo = [(q[0], q[1], z_brazo) for q in base]; arriba = [(q[0], q[1], z_brazo + 40) for q in base]
    caras = [abajo, arriba] + [[abajo[i], abajo[(i + 1) % 4], arriba[(i + 1) % 4], arriba[i]] for i in range(4)]
    ax.add_collection3d(Poly3DCollection(caras, facecolors=poste_c, edgecolors="k", linewidths=0.4))
    # celular
    caja(ax, CENTRO[0] - 75, CENTRO[1] - 35, zt + ALTURA_LENTE, 150, 70, 10, "#333")
    # campo de visión (líneas)
    for cx, cy in ((60, 40), (740, 40), (740, 1060), (60, 1060)):
        ax.plot([CENTRO[0], cx], [CENTRO[1], cy], [zt + ALTURA_LENTE, zt], color="#d62728", lw=0.6, ls="--")

    ax.text(CENTRO[0], CENTRO[1], zt + ALTURA_LENTE + 120, "celular (cámara)", fontsize=8, ha="center")
    ax.text(px + 60, POSTE_Y, 500, "poste", fontsize=8)
    ax.text(x0 - 60, LARGO - 60, 10, "base (bastidor)", fontsize=8, color="#5a3510")
    ax.text(CENTRO[0] + 100, CENTRO[1] + 60, z_tabla - 60, "ESP32", fontsize=8, color="#1f4e79")
    ax.text(CENTRO[0], LARGO + 40, zt, "puente", fontsize=8, ha="center")

    ax.set_xlim(-100, 950); ax.set_ylim(-50, 1150); ax.set_zlim(0, 1250)
    ax.set_box_aspect((1050, 1200, 1250))
    ax.invert_yaxis()
    ax.view_init(elev=22, azim=-58)
    ax.set_axis_off()


def vista_base_sola(ax):
    """La base sola, sin la tabla, para que se vea qué piezas son."""
    madera = "#c9a26b"
    x0, x1, y0, y1 = RETIRO, ANCHO - RETIRO, RETIRO, LARGO - RETIRO
    caja(ax, x0, y0, 0, LISTON_A, y1 - y0, ALTURA_BASE, madera)
    caja(ax, x1 - LISTON_A, y0, 0, LISTON_A, y1 - y0, ALTURA_BASE, madera)
    for y in (y0, y1 - LISTON_A):
        caja(ax, x0 + LISTON_A, y, 0, x1 - x0 - 2 * LISTON_A, LISTON_A, ALTURA_BASE, "#b98c52")
    for y in TRAVESANOS_Y:
        caja(ax, x0 + LISTON_A, y - LISTON_A / 2, 0, x1 - x0 - 2 * LISTON_A, LISTON_A, ALTURA_BASE, "#e0bd8a")
    caja(ax, CENTRO[0] - 82, CENTRO[1] - 27, 30, 165, 55, 40, "#1f4e79", alpha=0.5)
    ax.text(x0 - 30, (y0 + y1) / 2, ALTURA_BASE + 40, "A", fontsize=12, weight="bold")
    ax.text(x1 + 10, (y0 + y1) / 2, ALTURA_BASE + 40, "A", fontsize=12, weight="bold")
    ax.text((x0 + x1) / 2, y0 - 40, ALTURA_BASE + 40, "B", fontsize=12, weight="bold")
    ax.text((x0 + x1) / 2, y1 + 20, ALTURA_BASE + 40, "B", fontsize=12, weight="bold")
    for y in TRAVESANOS_Y:
        ax.text((x0 + x1) / 2 + 150, y, ALTURA_BASE + 40, "C", fontsize=12, weight="bold")
    ax.text(CENTRO[0], CENTRO[1], 110, "ESP32 (va pegado a la tabla)", fontsize=7, ha="center", color="#1f4e79")
    ax.set_xlim(0, 800); ax.set_ylim(0, 1100); ax.set_zlim(0, 300)
    ax.set_box_aspect((800, 1100, 300))
    ax.invert_yaxis()
    ax.view_init(elev=35, azim=-58)
    ax.set_axis_off()
    ax.set_title("2. LA BASE SOLA: 6 PIEZAS (no son solo 2 palos)", fontsize=10, weight="bold", loc="left")


CORTES = [
    ("Pieza", "Material", "Cant.", "Largo", "Para qué"),
    ("A  larguero", "listón 45×70 mm", "2", "940 mm", "lados largos de la base"),
    ("B  cabezal", "listón 45×70 mm", "2", "550 mm", "cierran el rectángulo"),
    ("C  travesaño", "listón 45×70 mm", "2", "550 mm", "evitan que la tabla se combe"),
    ("D  poste inferior", "listón 40×40 mm", "1", "700 mm", "sostiene la cámara"),
    ("E  poste superior", "listón 40×40 mm", "1", "700 mm", "ajuste de altura (agujeros c/25 mm)"),
    ("F  brazo", "listón 40×40 mm", "1", "600 mm", "lleva el celular al centro"),
    ("G  refuerzo", "listón 40×40 mm", "1", "300 mm (45°)", "brazo rígido"),
    ("H  unión", "listón 40×40 mm", "1", "80 mm", "atornilla el poste a la base (bajo la tabla)"),
]
TOTALES = ("Total listón 45×70 mm: 2 × 940 + 4 × 550 = 4,08 m\n   (2 listones de 2,5 m, o 1 de 3 m + 1 de 1,5 m)\n"
           "Total listón 40×40 mm: 700 + 700 + 600 + 300 + 80 = 2,38 m\n   (1 listón de 2,5 m)\n\n"
           "Ferretería: 10 escuadras pequeñas, tornillos 1/2\", 1\" y 2½\",\n"
           "3 pernos 1/4\"×3\" con mariposa,\n"
           "4 tacos de goma, pinza de celular con rosca 1/4\",\n"
           "cinta doble faz, bridas, broca de 8 mm.")


def main():
    fig = plt.figure(figsize=(16.5, 11.7))
    ax1 = fig.add_axes([0.0, 0.25, 0.52, 0.68], projection="3d")
    ax2 = fig.add_axes([0.50, 0.42, 0.50, 0.53], projection="3d")
    ax3 = fig.add_axes([0.02, 0.02, 0.96, 0.30])
    vista_3d(ax1)
    vista_base_sola(ax2)
    ax3.axis("off")
    ax3.text(0, 1.0, "3. LISTA DE CORTES (llevar esta tabla al aserrío / ferretería)", fontsize=10, weight="bold",
             va="top")
    anchos = [0.0, 0.13, 0.25, 0.30, 0.40]
    for i, fila in enumerate(CORTES):
        for j, celda in enumerate(fila):
            ax3.text(anchos[j], 0.86 - i * 0.075, celda, fontsize=8.5, va="top", weight="bold" if i == 0 else None)
    ax3.text(0.66, 0.86, TOTALES, fontsize=8.2, va="top")
    ax3.text(0.66, 0.22, "Medidas detalladas: base_maqueta.pdf (base y ESP32)\n"
             "y soporte_camara.pdf (poste, brazo, celular).\n"
             "Medir el grosor real de la tabla antes de cortar.", fontsize=8.2, va="top", style="italic")
    fig.suptitle("Maqueta completa: tabla + base + ESP32 + semáforos + soporte de cámara", fontsize=13,
                 weight="bold", x=0.01, ha="left", y=0.995)
    fig.text(0.01, 0.955, "1. MAQUETA MONTADA (tabla transparente para ver la base)", fontsize=10, weight="bold")
    SALIDA.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(SALIDA / f"esquema_completo_maqueta.{ext}", dpi=150 if ext == "png" else None)
    print("Esquema generado en", SALIDA)


if __name__ == "__main__":
    main()
