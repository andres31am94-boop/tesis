"""
Comparacion final: semaforo real vs agente (y la referencia del semaforo real con el todo-rojo de la norma).

Corre cada controlador con las MISMAS semillas de evaluacion (config/agente.yaml: semillas.evaluacion, nunca usadas
al entrenar) en cada escenario, y guarda una fila por corrida en results/comparacion/<modelo>/corridas.csv.
Con la misma semilla, todos los controladores reciben exactamente los mismos vehiculos: los resultados son PAREADOS.

Se puede interrumpir y volver a correr: las corridas ya guardadas no se repiten.
Despues: scripts/analizar_comparacion.py (mediana, diferencia, Wilcoxon, graficas).

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\comparar_controladores.py --modelo aforo_v2
  .\\.venv\\Scripts\\python.exe scripts\\comparar_controladores.py --modelo aforo_v2 --escenarios aforo_bajo --semillas 1 2
"""
import argparse
import csv
import statistics
import sys
import tempfile
import time
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))

from src.common.configuracion import cargar_interseccion  # noqa: E402
from src.metrics.metricas import leer_tripinfo, resumir_colas, resumir_verdes, resumir_viajes  # noqa: E402
from src.simulation.ejecutar_escenario import CARPETA_ESCENARIOS, leer_yaml, simular  # noqa: E402

ESCENARIOS = ["aforo_bajo", "aforo_valle_manana", "aforo_medio", "aforo_alto", "aforo_pico_jueves"]
CONTROLADORES = ["tiempos_fijos", "tiempos_fijos_norma", "qlearning"]
CICLO_RECOMENDADO_MAX_S = 120  # Manual de Senalizacion Vial 2024, 4.8.6


def resumir_ciclos(historial_verdes, inicio, fin):
    """Ciclo = tiempo entre dos inicios consecutivos del verde de la Cra 23."""
    inicios = [t for eje, t, _ in historial_verdes if eje == "cra23" and inicio <= t < fin]
    ciclos = [b - a for a, b in zip(inicios, inicios[1:])]
    if not ciclos:
        return {"ciclo_promedio_s": None, "ciclo_minimo_s": None, "ciclo_maximo_s": None,
                "ciclos_menores_60_pct": None, "ciclos_mayores_120_pct": None}
    # Manual 2024 (cap. 4): ciclos recomendados entre 60 y 120 s
    return {"ciclo_promedio_s": statistics.fmean(ciclos), "ciclo_minimo_s": min(ciclos), "ciclo_maximo_s": max(ciclos),
            "ciclos_menores_60_pct": 100 * sum(c < 60 for c in ciclos) / len(ciclos),
            "ciclos_mayores_120_pct": 100 * sum(c > CICLO_RECOMENDADO_MAX_S for c in ciclos) / len(ciclos)}


def una_corrida(escenario, semilla, controlador, modelo, configs, ruta_log=None):
    config_interseccion, _, config_experimento = configs
    inicio, fin = config_experimento["calentamiento_s"], config_experimento["duracion_demanda_s"]
    with tempfile.TemporaryDirectory() as carpeta_temporal:  # el tripinfo se borra al terminar
        ruta_tripinfo = Path(carpeta_temporal) / "tripinfo.xml"
        filas, guard, ctrl, cierre = simular(CARPETA_ESCENARIOS / f"{escenario}.sumocfg", semilla, False, controlador,
                                             configs, ruta_tripinfo, modelo if controlador == "qlearning" else None,
                                             zona="al_decidir", ruta_log=ruta_log)
        viajes = leer_tripinfo(ruta_tripinfo)
    fila = {"escenario": escenario, "semilla": semilla, "controlador": controlador}
    fila.update(resumir_viajes(viajes, inicio, fin))
    brazos = list(config_interseccion["brazos"])
    fila.update(resumir_colas(filas, brazos, inicio, fin))
    # Espera EN EL CRUCE: vehiculo-segundos detenidos en los 4 brazos (zona de medicion, sin la Calle 18 ni los accesos)
    # dentro de la ventana, dividido por los vehiculos medidos. La espera total de tripinfo incluye tambien el rojo
    # de la Calle 18, que es igual para todos los controladores y diluye las diferencias.
    segundos_detenidos = sum(sum(f[f"detenidos_{b}"] for b in brazos) for f in filas if inicio <= f["tiempo"] < fin)
    fila["espera_cruce_promedio_s"] = segundos_detenidos / fila["vehiculos_medidos"]
    fila.update(resumir_verdes(guard.historial_verdes, inicio, fin))
    fila.update(resumir_ciclos(guard.historial_verdes, inicio, fin))
    fila["vehiculos_sin_terminar"] = cierre["vehiculos_sin_terminar"]
    fila["teletransportes"] = cierre["teletransportes"]
    fila["desatascos_calle18"] = cierre["desatascos_calle18"]
    fila["desfase_calle18_s"] = cierre["desfase_calle18_s"]
    fila["decisiones_respaldo"] = getattr(ctrl, "decisiones_respaldo", "")
    fila["decisiones"] = getattr(ctrl, "decisiones", "")
    return fila


def main():
    parser = argparse.ArgumentParser(description="Corre la comparacion final (corridas pareadas por semilla).")
    parser.add_argument("--modelo", required=True, help="carpeta del agente en models/")
    parser.add_argument("--escenarios", nargs="+", default=ESCENARIOS)
    parser.add_argument("--semillas", nargs="+", type=int, help="por defecto: semillas.evaluacion de config/agente.yaml")
    parser.add_argument("--controladores", nargs="+", default=CONTROLADORES, choices=CONTROLADORES)
    parser.add_argument("--carpeta", help="nombre de la carpeta de resultados (por defecto, el del modelo). "
                                          "Para VALIDACION usar otra, p. ej. aforo_v4_validacion")
    args = parser.parse_args()

    semillas = args.semillas or leer_yaml("agente.yaml")["semillas"]["evaluacion"]
    configs = (cargar_interseccion(), leer_yaml("controlador.yaml"), leer_yaml("experimento.yaml"))
    if not (CARPETA_TESIS / "models" / args.modelo / "tabla_q.json").exists():
        sys.exit(f"ERROR: no existe models/{args.modelo}/tabla_q.json")

    carpeta = CARPETA_TESIS / "results" / "comparacion" / (args.carpeta or args.modelo)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "corridas.csv"
    hechas = set()
    columnas = None
    if ruta.exists():
        with open(ruta, encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            columnas = lector.fieldnames
            hechas = {(f["escenario"], int(f["semilla"]), f["controlador"]) for f in lector}

    pendientes = [(e, s, c) for e in args.escenarios for s in semillas for c in args.controladores
                  if (e, s, c) not in hechas]
    print(f"Modelo {args.modelo}: {len(pendientes)} corridas pendientes ({len(hechas)} ya guardadas)")
    for numero, (escenario, semilla, controlador) in enumerate(pendientes, start=1):
        reloj = time.time()
        carpeta_logs = carpeta / "avisos_sumo"  # un log por corrida: donde y cuando hubo teleports (auditoria)
        carpeta_logs.mkdir(exist_ok=True)
        fila = una_corrida(escenario, semilla, controlador, args.modelo, configs,
                           ruta_log=carpeta_logs / f"{escenario}_s{semilla}_{controlador}.log")
        fila["segundos_reloj"] = round(time.time() - reloj, 1)  # tiempo de computo (metodologia)
        if columnas is None:
            columnas = list(fila)
            with open(ruta, "w", newline="", encoding="utf-8") as archivo:
                csv.DictWriter(archivo, fieldnames=columnas).writeheader()
        with open(ruta, "a", newline="", encoding="utf-8") as archivo:  # una fila a la vez: si se corta, no se pierde
            csv.DictWriter(archivo, fieldnames=columnas, extrasaction="ignore").writerow(fila)
        print(f"[{numero}/{len(pendientes)}] {escenario:<18} s{semilla:<3} {controlador:<20} espera "
              f"{fila['espera_total_promedio_s']:7.2f} s | cola {fila['detenidos_promedio_total']:6.2f} | "
              f"ciclo {fila['ciclo_promedio_s'] or 0:5.0f} s | {time.time() - reloj:5.0f} s")
    print(f"\nGuardado en {ruta}")


if __name__ == "__main__":
    main()
