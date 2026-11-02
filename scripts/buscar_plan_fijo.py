"""
MEJOR PLAN FIJO POSIBLE por busqueda en la simulacion (2026-10-29).

Pregunta que responde: "el agente gana solo porque el semaforo real esta mal programado?". El metodo de Webster no sirvio
como respuesta (no ve la reduccion a 1 carril antes del puente; ver docs/bitacora.md). Aqui se prueba, en la MISMA
simulacion, una rejilla de planes fijos para CADA escenario y se elige el que da menos espera. Como se elige conociendo
la demanda exacta de cada hora, es el mejor caso posible para un semaforo de tiempos fijos.

Rejilla (dentro de la capa de seguridad: verde Cra 23 20-70 s, Dg 15 15-25 s; mismos amarillo y todo-rojo del real):
  verde Cra 23 = 30, 35, ..., 70 s   x   verde Dg 15 = 15, 20, 25 s   -> 27 planes por escenario
Seleccion: menor espera promedio (media de las semillas de VALIDACION 101-103: las de evaluacion 1-30 no se usan aqui).
Despues el plan elegido se evalua con las semillas 1-30, igual que el agente (controlador "tiempos_fijos_optimo").

Uso (desde la carpeta tesis; reanudable: si se corta, el mismo comando sigue donde iba):
  .\\.venv\\Scripts\\python.exe scripts\\buscar_plan_fijo.py
Salidas:
  results/plan_fijo_optimo/busqueda.csv   una fila por corrida (plan x escenario x semilla)
  config/plan_fijo_optimo.yaml            el mejor plan de cada escenario + resumen de la rejilla
"""
import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comparar_controladores import ESCENARIOS, una_corrida  # noqa: E402
from src.common.configuracion import cargar_interseccion  # noqa: E402
from src.simulation.ejecutar_escenario import leer_yaml  # noqa: E402

COLUMNAS = ["escenario", "verde_cra23_s", "verde_dg15_s", "semilla", "espera_total_promedio_s",
            "tiempo_viaje_promedio_s", "throughput_veh_h", "vehiculos_sin_terminar", "teletransportes", "segundos_reloj"]


def main():
    parser = argparse.ArgumentParser(description="Busca el mejor plan fijo por escenario en la simulacion.")
    parser.add_argument("--escenarios", nargs="+", default=ESCENARIOS)
    parser.add_argument("--semillas", nargs="+", type=int, default=[101, 102, 103])
    parser.add_argument("--cra23", nargs="+", type=int, default=list(range(30, 71, 5)))
    parser.add_argument("--dg15", nargs="+", type=int, default=[15, 20, 25])
    args = parser.parse_args()
    evaluacion = set(leer_yaml("agente.yaml")["semillas"]["evaluacion"])
    if evaluacion & set(args.semillas):
        sys.exit("ERROR: la busqueda no puede usar semillas de evaluacion (1-30)")

    configs = (cargar_interseccion(), leer_yaml("controlador.yaml"), leer_yaml("experimento.yaml"))
    carpeta = CARPETA_TESIS / "results" / "plan_fijo_optimo"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "busqueda.csv"
    hechas = set()
    if ruta.exists():
        with open(ruta, encoding="utf-8") as archivo:
            hechas = {(f["escenario"], int(f["verde_cra23_s"]), int(f["verde_dg15_s"]), int(f["semilla"]))
                      for f in csv.DictReader(archivo)}
    else:
        with open(ruta, "w", newline="", encoding="utf-8") as archivo:
            csv.DictWriter(archivo, fieldnames=COLUMNAS).writeheader()

    pendientes = [(e, c, d, s) for e in args.escenarios for c in args.cra23 for d in args.dg15 for s in args.semillas
                  if (e, c, d, s) not in hechas]
    print(f"{len(pendientes)} corridas pendientes ({len(hechas)} ya guardadas)")
    for numero, (escenario, cra23, dg15, semilla) in enumerate(pendientes, start=1):
        reloj = time.time()
        fila = una_corrida(escenario, semilla, "tiempos_fijos_plan", None, configs,
                           verdes_fijos={"cra23": cra23, "dg15": dg15})
        salida = {"escenario": escenario, "verde_cra23_s": cra23, "verde_dg15_s": dg15, "semilla": semilla,
                  **{k: fila[k] for k in COLUMNAS[4:-1]}, "segundos_reloj": round(time.time() - reloj, 1)}
        with open(ruta, "a", newline="", encoding="utf-8") as archivo:
            csv.DictWriter(archivo, fieldnames=COLUMNAS).writerow(salida)
        print(f"[{numero}/{len(pendientes)}] {escenario:<18} Cra23 {cra23:2d} s / Dg15 {dg15:2d} s | s{semilla} | "
              f"espera {fila['espera_total_promedio_s']:7.2f} s | {salida['segundos_reloj']:4.0f} s")

    # --- seleccion --------------------------------------------------------------------------------------------
    with open(ruta, encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    seguridad = configs[1]["seguridad"]
    planes, rejilla = {}, {}
    for escenario in args.escenarios:
        medias = {}
        for cra23 in args.cra23:
            for dg15 in args.dg15:
                valores = [float(f["espera_total_promedio_s"]) for f in filas
                           if f["escenario"] == escenario and int(f["verde_cra23_s"]) == cra23
                           and int(f["verde_dg15_s"]) == dg15 and int(f["semilla"]) in args.semillas]
                if len(valores) == len(args.semillas):
                    medias[(cra23, dg15)] = statistics.fmean(valores)
        (mejor_c, mejor_d), espera = min(medias.items(), key=lambda kv: kv[1])
        ciclo = mejor_c + mejor_d + sum(seguridad["amarillo_s"] + seguridad["todo_rojo_s"][e] for e in ("cra23", "dg15"))
        borde = mejor_c in (min(args.cra23), max(args.cra23)) or mejor_d in (min(args.dg15), max(args.dg15))
        planes[escenario] = {"verde_s": {"cra23": mejor_c, "dg15": mejor_d}, "ciclo_s": ciclo,
                             "espera_media_validacion_s": round(espera, 2), "en_borde_de_la_rejilla": borde}
        rejilla[escenario] = {f"{c}/{d}": round(v, 2) for (c, d), v in sorted(medias.items())}
        aviso = "  (en el borde de la rejilla: limite de la capa de seguridad o ampliar la rejilla)" if borde else ""
        print(f"{escenario:<20} mejor plan Cra23 {mejor_c} s / Dg15 {mejor_d} s (ciclo {ciclo} s), "
              f"espera media {espera:.2f} s{aviso}")
    salida = {"descripcion": "Mejor plan fijo por escenario, elegido por busqueda en la simulacion "
                             "(scripts/buscar_plan_fijo.py; no editar).",
              "criterio": "menor espera total promedio, media de las semillas de validacion",
              "semillas_busqueda": args.semillas, "rejilla_cra23_s": args.cra23, "rejilla_dg15_s": args.dg15,
              "planes": planes, "espera_media_por_plan_s": rejilla}
    (CARPETA_TESIS / "config" / "plan_fijo_optimo.yaml").write_text(
        yaml.safe_dump(salida, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("Guardado en config/plan_fijo_optimo.yaml")


if __name__ == "__main__":
    main()
