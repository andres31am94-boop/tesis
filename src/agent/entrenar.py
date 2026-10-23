"""
Entrena el agente Q-Learning en SUMO, de seguido o POR PAQUETES.

Uso (desde la carpeta tesis):
  # primer paquete: los primeros 50 de 200 episodios
  .\\.venv\\Scripts\\python.exe -m src.agent.entrenar --escenarios aforo_bajo aforo_valle_manana aforo_medio aforo_alto --episodios 200 --paquete 50 --nombre aforo_v1
  # siguientes paquetes: el mismo comando + --continuar (sigue donde quedo, hasta llegar a 200)
  .\\.venv\\Scripts\\python.exe -m src.agent.entrenar --escenarios aforo_bajo aforo_valle_manana aforo_medio aforo_alto --episodios 200 --paquete 50 --nombre aforo_v1 --continuar

  --episodios  total de episodios del entrenamiento (define la semilla, el escenario y el epsilon de cada uno)
  --paquete    cuantos episodios correr en esta ejecucion (si se omite, corre todos los que faltan)
  --continuar  carga la tabla guardada y sigue desde el ultimo episodio COMPLETO

Cada episodio = una hora simulada con una semilla distinta (semillas de ENTRENAMIENTO, nunca las de evaluacion).
Con varios escenarios se ROTAN: el episodio k usa escenarios[k % n].
Todo lo que depende del episodio k (semilla de SUMO, escenario, epsilon y el azar de la exploracion) se calcula a
partir de k: entrenar de seguido o por paquetes produce exactamente la misma tabla.
Al terminar CADA episodio se guardan:
  models/<nombre>/tabla_q.json             la tabla aprendida (con sus parametros y episodios completos)
  models/<nombre>/curva_aprendizaje.csv    una fila por episodio
Si el programa se corta (error, apagado, Ctrl+C), se pierde solo el episodio en curso.
"""
import argparse
import csv
import sys
import time

import yaml

from src.agent.entorno_sumo import EntornoSumo
from src.agent.qlearning import CAMBIAR, TablaQ, epsilon_lineal
from src.common.configuracion import CARPETA_TESIS, cargar_interseccion

CARPETA_CONFIG = CARPETA_TESIS / "config"
CARPETA_MODELOS = CARPETA_TESIS / "models"
COLUMNAS = ["episodio", "escenario", "semilla", "epsilon", "recompensa_total", "detenidos_promedio",
            "decisiones", "pedidos_de_cambio", "verdes_cra23", "verdes_dg15", "segundos_reloj"]


def leer_yaml(nombre):
    with open(CARPETA_CONFIG / nombre, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def preparar_continuacion(carpeta, metadatos, ruta_curva):
    """Carga la tabla guardada y comprueba que se este continuando EL MISMO entrenamiento."""
    ruta_tabla = carpeta / "tabla_q.json"
    if not ruta_tabla.exists():
        sys.exit(f"ERROR: --continuar pero no existe {ruta_tabla}. Quita --continuar para empezar.")
    tabla = TablaQ.cargar(ruta_tabla)
    guardados = tabla.metadatos
    for clave in ("escenarios", "episodios_totales", "config_agente", "config_controlador", "config_experimento"):
        if guardados.get(clave) != metadatos[clave]:
            sys.exit(f"ERROR: '{clave}' no coincide con el entrenamiento guardado en {carpeta}. "
                     "No se puede continuar con otra configuracion: usa otro --nombre.")
    hechos = guardados["episodios_entrenados"]
    with open(ruta_curva, encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    if len(filas) != hechos:
        sys.exit(f"ERROR: la tabla dice {hechos} episodios y la curva tiene {len(filas)} filas. Revisar a mano.")
    return tabla, hechos


def main():
    parser = argparse.ArgumentParser(description="Entrena el agente Q-Learning (de seguido o por paquetes).")
    parser.add_argument("--escenarios", nargs="+", required=True, help="uno o varios .sumocfg de sumo/configs (se rotan)")
    parser.add_argument("--episodios", type=int, required=True, help="total de episodios del entrenamiento")
    parser.add_argument("--paquete", type=int, help="episodios a correr en esta ejecucion (por defecto, todos los que faltan)")
    parser.add_argument("--nombre", required=True, help="nombre de la carpeta en models/")
    parser.add_argument("--continuar", action="store_true", help="seguir un entrenamiento guardado")
    parser.add_argument("--gui", action="store_true", help="ver el entrenamiento (muy lento)")
    args = parser.parse_args()

    config_interseccion = cargar_interseccion()
    config_controlador = leer_yaml("controlador.yaml")
    config_agente = leer_yaml("agente.yaml")
    config_experimento = leer_yaml("experimento.yaml")
    aprendizaje = config_agente["aprendizaje"]
    semilla_base = config_agente["semillas"]["entrenamiento_desde"]
    if set(range(semilla_base, semilla_base + args.episodios)) & set(config_agente["semillas"]["evaluacion"]):
        raise ValueError("Las semillas de entrenamiento se cruzan con las de evaluacion.")

    archivos = [CARPETA_TESIS / "sumo" / "configs" / f"{nombre}.sumocfg" for nombre in args.escenarios]
    for archivo in archivos:
        if not archivo.exists():
            raise FileNotFoundError(f"No existe el escenario {archivo}")

    carpeta = CARPETA_MODELOS / args.nombre
    ruta_curva = carpeta / "curva_aprendizaje.csv"
    metadatos = {"escenarios": args.escenarios, "episodios_totales": args.episodios, "config_agente": config_agente,
                 "config_controlador": config_controlador, "config_experimento": config_experimento}

    entorno = EntornoSumo(archivos[0], config_interseccion, config_controlador, config_agente, config_experimento,
                          usar_gui=args.gui)
    if args.continuar:
        tabla, primer_episodio = preparar_continuacion(carpeta, metadatos, ruta_curva)
        modo_curva = "a"
    else:
        if (carpeta / "tabla_q.json").exists():
            sys.exit(f"ERROR: ya existe un entrenamiento en {carpeta}. Usa --continuar para seguirlo "
                     "u otro --nombre para empezar uno nuevo (asi nunca se borra progreso por error).")
        carpeta.mkdir(parents=True, exist_ok=True)
        tabla = TablaQ(entorno.codificador.numero_estados, aprendizaje["alfa"], aprendizaje["gamma"])
        primer_episodio = 0
        modo_curva = "w"

    ultimo_episodio = args.episodios if args.paquete is None else min(args.episodios, primer_episodio + args.paquete)
    if primer_episodio >= args.episodios:
        print(f"El entrenamiento '{args.nombre}' ya tiene los {args.episodios} episodios. Nada que hacer.")
        return
    print(f"Entrenamiento '{args.nombre}': episodios {primer_episodio} a {ultimo_episodio - 1} "
          f"(de {args.episodios} en total)")

    try:
        with open(ruta_curva, modo_curva, newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
            if modo_curva == "w":
                escritor.writeheader()
            for episodio in range(primer_episodio, ultimo_episodio):
                semilla = semilla_base + episodio
                escenario = args.escenarios[episodio % len(args.escenarios)]
                epsilon = epsilon_lineal(episodio, aprendizaje["epsilon_inicial"],
                                         aprendizaje["epsilon_final"], aprendizaje["episodios_decaimiento"])
                tabla.reiniciar_azar(semilla)
                inicio_reloj = time.perf_counter()

                estado = entorno.reset(semilla, archivos[episodio % len(archivos)])
                recompensa_total, decisiones, pedidos = 0.0, 0, 0
                terminado = False
                while not terminado:
                    accion = tabla.elegir_accion(estado, epsilon)
                    estado_siguiente, recompensa, terminado, _ = entorno.step(accion)
                    tabla.actualizar(estado, accion, recompensa, estado_siguiente, terminado)
                    estado = estado_siguiente
                    recompensa_total += recompensa
                    decisiones += 1
                    pedidos += accion == CAMBIAR

                verdes = [eje for eje, _, _ in entorno.guard.historial_verdes]
                fila = {
                    "episodio": episodio, "escenario": escenario, "semilla": semilla, "epsilon": round(epsilon, 4),
                    "recompensa_total": recompensa_total,
                    "detenidos_promedio": round(entorno.detenidos_episodio / max(entorno.segundos_episodio, 1), 3),
                    "decisiones": decisiones, "pedidos_de_cambio": pedidos,
                    "verdes_cra23": verdes.count("cra23"), "verdes_dg15": verdes.count("dg15"),
                    "segundos_reloj": round(time.perf_counter() - inicio_reloj, 1),
                }
                # Primero la tabla (escritura segura) y despues la fila de la curva: si se corta entre ambas,
                # --continuar lo detecta porque no coinciden los conteos.
                tabla.guardar(carpeta / "tabla_q.json", {**metadatos, "episodios_entrenados": episodio + 1})
                escritor.writerow(fila)
                archivo.flush()
                print(f"ep {episodio:4d} | {escenario:<18} | semilla {semilla} | eps {epsilon:.3f} | "
                      f"recompensa {recompensa_total:10.0f} | detenidos prom. {fila['detenidos_promedio']:6.2f} | "
                      f"decisiones {decisiones:4d} | {fila['segundos_reloj']:5.1f} s")
    finally:
        entorno.close()

    estados_visitados = sum(1 for fila in tabla.visitas if sum(fila) > 0)
    print(f"\nTabla guardada en: {carpeta / 'tabla_q.json'}")
    print(f"Episodios completos: {ultimo_episodio} de {args.episodios} | "
          f"estados visitados: {estados_visitados} de {tabla.numero_estados}")
    if ultimo_episodio < args.episodios:
        print("Para seguir: el mismo comando con --continuar")


if __name__ == "__main__":
    main()
