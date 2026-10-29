"""
Muestra en forma legible lo que aprendio un agente (su tabla Q) y lo guarda en models/<modelo>/politica.md.

Para cada situacion (estado) dice que accion prefiere el agente y cuantas veces la vivio al entrenar:
  M = mantener el verde   C = cambiar   . = nunca la vivio (ahi el agente usa el plan fijo de respaldo)

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\ver_tabla_q.py --modelo aforo_v3
"""
import argparse
import json
import sys
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
NIVELES = ["vacia", "baja", "media", "alta", "muy_alta"]
EJES = ["cra23", "dg15"]


def main():
    parser = argparse.ArgumentParser(description="Muestra la politica aprendida por el agente.")
    parser.add_argument("--modelo", required=True)
    args = parser.parse_args()
    ruta = CARPETA_TESIS / "models" / args.modelo / "tabla_q.json"
    if not ruta.exists():
        sys.exit(f"ERROR: no existe {ruta}")
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    q, visitas = datos["q"], datos["visitas"]
    estado_cfg = datos["metadatos"]["config_agente"]["estado"]
    modo = estado_cfg.get("modo", "detenidos")
    # cortes de tiempo: una lista para ambos ejes o {eje: lista} (iteracion 4b); niveles de cola: 4 o 5 (iteracion 6)
    cortes_t = estado_cfg["cortes_tiempo_verde_s"]
    if not isinstance(cortes_t, dict):
        cortes_t = {eje: cortes_t for eje in EJES}
    niveles = len(estado_cfg["cortes_detenidos_zona"]) + 1
    nombres = NIVELES[:niveles] if niveles <= len(NIVELES) else [str(i) for i in range(niveles)]
    n_tiempos = len(cortes_t[EJES[0]]) + 1
    if len(q) != niveles ** 2 * len(EJES) * n_tiempos:
        sys.exit(f"ERROR: la tabla tiene {len(q)} estados; se esperaban {niveles ** 2 * len(EJES) * n_tiempos}.")

    lineas = [f"# Politica aprendida — modelo {args.modelo}", "",
              f"- Episodios de entrenamiento: {datos['metadatos'].get('episodios_entrenados')}",
              f"- Modo de estado: {modo}. Cortes de detenidos: {estado_cfg['cortes_detenidos_zona']}"
              + (f"; cortes de presentes (eje en verde): {estado_cfg.get('cortes_presentes_zona_verde')}"
                 if modo == "presentes_en_verde" else ""),
              "- Celda: accion preferida (M mantener / C cambiar) y veces que el agente vivio esa situacion; "
              "'.' = nunca la vivio (usa el plan fijo).", ""]
    for i_eje, eje in enumerate(EJES):
        otro = EJES[1 - i_eje]
        medida_verde = "presentes" if modo == "presentes_en_verde" else "detenidos"
        c = cortes_t[eje]
        tiempos = [f"menos de {c[0]} s"] + [f"{a}-{b} s" for a, b in zip(c, c[1:])] + [f"{c[-1]} s o mas"]
        for i_t, nombre_t in enumerate(tiempos):
            lineas += [f"## Verde en {eje}, lleva {nombre_t}", "",
                       f"Filas: {eje} (en verde, {medida_verde}). Columnas: {otro} (en rojo, detenidos).", "",
                       "| " + eje + " \\ " + otro + " | " + " | ".join(nombres) + " |", "|---|" + "---|" * niveles]
            for n_verde in range(niveles):
                celdas = []
                for n_rojo in range(niveles):
                    n_cra, n_dg = (n_verde, n_rojo) if eje == "cra23" else (n_rojo, n_verde)
                    s = ((n_cra * niveles + n_dg) * len(EJES) + i_eje) * n_tiempos + i_t
                    total = sum(visitas[s])
                    celdas.append("." if total == 0 else f"{'M' if q[s][0] >= q[s][1] else 'C'} ({total})")
                lineas.append(f"| {nombres[n_verde]} | " + " | ".join(celdas) + " |")
            lineas.append("")
    texto = "\n".join(lineas) + "\n"
    (ruta.parent / "politica.md").write_text(texto, encoding="utf-8")
    print(texto)
    print(f"Guardado en {ruta.parent / 'politica.md'}")


if __name__ == "__main__":
    main()
