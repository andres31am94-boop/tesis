"""
Resumen de la escala experimental (para la METODOLOGIA de la tesis): cuantas horas de trafico se simularon y cuanto
tiempo de computo se uso. Lee solo lo que esta guardado en la carpeta (no estima nada que no este medido).

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\resumen_computo.py
Crea docs/resumen_computo.md

Criterios:
  - Una corrida = una hora de demanda simulada (3600 s; el vaciado posterior no se cuenta).
  - Calibracion: resultados.csv tiene una fila por brazo (4 por corrida).
  - Entrenamiento: una fila por episodio en models/*/curva_aprendizaje.csv (incluye pruebas y modelos descartados).
    Las copias de otro entrenamiento (COPIAS) no se suman dos veces.
  - Tiempo de computo: solo donde se registro (columna segundos_reloj). Las corridas anteriores al 2026-10-27 de
    comparacion y calibracion no lo registraban: se informan aparte, sin inventar su duracion.
"""
import csv
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
COPIAS = {"aforo_v2_150"}  # primeros 150 episodios de aforo_v2 (bitacora, 2026-10-24)


def leer(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def segundos(filas):
    medidos = [float(f["segundos_reloj"]) for f in filas if f.get("segundos_reloj")]
    return sum(medidos), len(medidos)


def main():
    lineas = ["# Escala experimental (generado por scripts/resumen_computo.py)", "",
              "| Grupo | Carpeta | Horas simuladas | Computo medido (h) | Corridas con computo medido |",
              "|---|---|---|---|---|"]
    total_h, total_s, sin_medir = 0, 0.0, 0
    grupos = [("Calibracion", sorted((CARPETA_TESIS / "results" / "calibracion").glob("*/resultados.csv")), 4),
              ("Comparacion", sorted((CARPETA_TESIS / "results" / "comparacion").glob("*/corridas.csv")), 1),
              ("Entrenamiento", sorted((CARPETA_TESIS / "models").glob("**/curva_aprendizaje.csv")), 1)]
    for grupo, rutas, filas_por_corrida in grupos:
        for ruta in rutas:
            nombre = ruta.parent.name
            if nombre in COPIAS:
                continue
            filas = leer(ruta)
            corridas = len(filas) // filas_por_corrida
            s, n = segundos(filas)
            n //= filas_por_corrida
            s /= filas_por_corrida  # en calibracion cada brazo repite el tiempo de la corrida
            total_h += corridas
            total_s += s
            sin_medir += corridas - n
            lineas.append(f"| {grupo} | {nombre} | {corridas} | {s / 3600:.1f} | {n} de {corridas} |")
    lineas += ["", f"**Total: {total_h} horas de trafico simuladas** (= {total_h / 24:.0f} dias continuos).",
               f"Computo medido: {total_s / 3600:.1f} h; {sin_medir} corridas sin registro de duracion "
               "(anteriores a que se guardara)."]
    salida = CARPETA_TESIS / "docs" / "resumen_computo.md"
    salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas[-3:]))
    print(f"Guardado en {salida}")


if __name__ == "__main__":
    main()
