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
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common.registro_computo import registrar_ejecucion  # noqa: E402

CARPETA_TESIS = Path(__file__).resolve().parents[1]
COPIAS = {"aforo_v2_150"}  # primeros 150 episodios de aforo_v2 (bitacora, 2026-10-24)


def leer(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def segundos(filas):
    medidos = [float(f["segundos_reloj"]) for f in filas if f.get("segundos_reloj")]
    return sum(medidos), len(medidos)


def vision_y_hardware():
    """Computo medido fuera de SUMO: entrenamientos YOLO (registro_entrenamiento.json), hardware en el lazo (tiempo
    real por diseno) y pruebas del lazo de la maqueta (segundos de video procesados)."""
    lineas = ["", "## Vision, hardware y maqueta", "",
              "| Tipo | Carpeta | Detalle | Computo medido (h) |", "|---|---|---|---|"]
    total_s = 0.0
    for registro in sorted((CARPETA_TESIS / "results" / "vision" / "entrenamiento").glob("*/registro_entrenamiento.json")):
        datos = json.loads(registro.read_text(encoding="utf-8"))
        minutos = float(datos.get("minutos_entrenamiento") or 0)
        total_s += minutos * 60
        lineas.append(f"| Entrenamiento YOLO (CPU) | {registro.parent.name} | {datos.get('epocas')} epocas, "
                      f"fraccion {datos.get('fraccion')} | {minutos / 60:.1f} |")
    for resumen in sorted((CARPETA_TESIS / "results" / "hardware" / "lazo").glob("*/resumen.json")):
        datos = json.loads(resumen.read_text(encoding="utf-8"))
        inicio, fin = datos["ventana_s"]
        segundos_lazo = float(fin) - float(inicio)   # en tiempo real: 1 s simulado = 1 s de reloj
        total_s += segundos_lazo
        lineas.append(f"| Hardware en el lazo (tiempo real) | {resumen.parent.name} | ESP32 + SUMO | {segundos_lazo / 3600:.2f} |")
    pruebas = sorted((CARPETA_TESIS / "results" / "maqueta" / "lazo").glob("*/resumen.json"))
    for resumen in pruebas:
        datos = json.loads(resumen.read_text(encoding="utf-8"))
        lineas.append(f"| Lazo de la maqueta | {resumen.parent.name} | {datos.get('segundos')} s de video, "
                      f"{datos.get('cuadros_por_segundo')} cuadros/s | - |")
    lineas += ["", f"Computo medido en vision y hardware: {total_s / 3600:.1f} h. No incluye evaluaciones cortas de YOLO, "
               "etiquetado manual en Label Studio ni pruebas sin registro de duracion.",
               "Estimado de lo no registrado en vision (antes del 2026-11-05): ~1 h (unas 15 evaluaciones de YOLO de 1-3 min, "
               "pruebas de tracking y conteo de 1-10 min, pre-etiquetado y prueba de alturas; aproximacion de los tutores, no "
               "medicion).", "El tiempo de trabajo de las personas (campo, aforo, etiquetado, montaje) va en "
               "docs/registro_tiempo_dedicado.md."]
    # Registro central (desde 2026-11-05 cada script agrega una fila: src/common/registro_computo.py)
    registro = CARPETA_TESIS / "results" / "registro_computo.csv"
    if registro.exists():
        filas = leer(registro)
        por_script = {}
        for fila in filas:
            por_script.setdefault(fila["script"], [0, 0.0])
            por_script[fila["script"]][0] += 1
            por_script[fila["script"]][1] += float(fila["segundos"])
        lineas += ["", "## Registro de cada ejecucion (desde 2026-11-05, results/registro_computo.csv)", "",
                   "| Script | Ejecuciones | Computo (h) |", "|---|---|---|"]
        lineas += [f"| {nombre} | {n} | {seg / 3600:.2f} |" for nombre, (n, seg) in sorted(por_script.items())]
        lineas += ["", f"Total registrado: {sum(v[1] for v in por_script.values()) / 3600:.2f} h en "
                   f"{sum(v[0] for v in por_script.values())} ejecuciones. (Para no contar dos veces, este total NO se suma "
                   "a las tablas de arriba: las corridas de simulacion y los entrenamientos ya aparecen alli.)"]
    return lineas


def main():
    registrar_ejecucion()
    lineas = ["# Escala experimental (generado por scripts/resumen_computo.py)", "",
              "Computo MEDIDO = duracion registrada por los scripts. Computo ESTIMADO = solo para corridas sin registro: "
              "cantidad de corridas x promedio medido por corrida en su mismo grupo (se indica en la tabla).", "",
              "| Grupo | Carpeta | Horas simuladas | Computo medido (h) | Corridas medidas | Estimado sin registro (h) |",
              "|---|---|---|---|---|---|"]
    grupos = [("Calibracion", sorted((CARPETA_TESIS / "results" / "calibracion").glob("*/resultados.csv")), 4),
              ("Comparacion", sorted((CARPETA_TESIS / "results" / "comparacion").glob("*/corridas.csv")), 1),
              ("Entrenamiento", sorted((CARPETA_TESIS / "models").glob("**/curva_aprendizaje.csv")), 1)]
    filas_tabla = []
    for grupo, rutas, filas_por_corrida in grupos:
        for ruta in rutas:
            nombre = ruta.parent.name
            if nombre in COPIAS:
                continue
            filas = leer(ruta)
            corridas = len(filas) // filas_por_corrida
            s, n = segundos(filas)
            filas_tabla.append([grupo, nombre, corridas, s / filas_por_corrida, n // filas_por_corrida])
    # Corridas sueltas de src.simulation.ejecutar_escenario (verificaciones): results/<escenario>/<controlador>/semilla_*/
    sueltas = sorted(r for r in (CARPETA_TESIS / "results").glob("*/*/semilla_*/resumen.json")
                     if r.parts[-4] not in ("calibracion", "comparacion", "hardware", "vision", "maqueta"))
    if sueltas:
        filas_tabla.append(["Corridas sueltas", f"results/<escenario>/... ({len({r.parts[-4] for r in sueltas})} escenarios)",
                            len(sueltas), 0.0, 0])
    # promedio medido por corrida en cada grupo (las sueltas se estiman con el de Comparacion: misma simulacion)
    promedio = {}
    for grupo in ("Calibracion", "Comparacion", "Entrenamiento"):
        s_total = sum(f[3] for f in filas_tabla if f[0] == grupo)
        n_total = sum(f[4] for f in filas_tabla if f[0] == grupo)
        promedio[grupo] = s_total / n_total if n_total else 0.0
    promedio["Corridas sueltas"] = promedio["Comparacion"]
    total_h = total_s = total_estimado = 0.0
    sin_medir = 0
    for grupo, nombre, corridas, s, n in filas_tabla:
        faltan = corridas - n
        estimado = faltan * promedio[grupo]
        total_h += corridas
        total_s += s
        total_estimado += estimado
        sin_medir += faltan
        lineas.append(f"| {grupo} | {nombre} | {corridas} | {s / 3600:.1f} | {n} de {corridas} | "
                      f"{estimado / 3600:.1f} |" if faltan else
                      f"| {grupo} | {nombre} | {corridas} | {s / 3600:.1f} | {n} de {corridas} | - |")
    lineas += ["", f"**Total: {total_h:.0f} horas de trafico simuladas** (= {total_h / 24:.0f} dias continuos).",
               f"Computo de simulacion: **{total_s / 3600:.1f} h medidas** + **~{total_estimado / 3600:.1f} h estimadas** "
               f"({sin_medir} corridas sin registro, anteriores a que se guardara la duracion; promedio medido por corrida: "
               + ", ".join(f"{g} {v:.0f} s" for g, v in promedio.items() if g != "Corridas sueltas") + ")."]
    lineas += vision_y_hardware()
    salida = CARPETA_TESIS / "docs" / "resumen_computo.md"
    salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas[-3:]))
    print(f"Guardado en {salida}")


if __name__ == "__main__":
    main()
