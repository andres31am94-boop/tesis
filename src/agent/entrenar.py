"""
Entrena el agente Q-Learning en SUMO.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe -m src.agent.entrenar --escenario prueba --episodios 3 --nombre prueba_corta

Cada episodio = una hora simulada con una semilla distinta (semillas de ENTRENAMIENTO, nunca
las de evaluacion). Al terminar cada episodio se guardan:
  models/<nombre>/tabla_q.json             la tabla aprendida (con sus parametros)
  models/<nombre>/curva_aprendizaje.csv    una fila por episodio
"""
import argparse
import csv
import time

import yaml

from src.agent.entorno_sumo import EntornoSumo
from src.agent.qlearning import CAMBIAR, TablaQ, epsilon_lineal
from src.common.configuracion import CARPETA_TESIS, cargar_interseccion

CARPETA_CONFIG = CARPETA_TESIS / "config"
CARPETA_MODELOS = CARPETA_TESIS / "models"


def leer_yaml(nombre):
    with open(CARPETA_CONFIG / nombre, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def main():
    parser = argparse.ArgumentParser(description="Entrena el agente Q-Learning.")
    parser.add_argument("--escenario", required=True)
    parser.add_argument("--episodios", type=int, required=True)
    parser.add_argument("--nombre", required=True, help="nombre de la carpeta en models/")
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

    entorno = EntornoSumo(CARPETA_TESIS / "sumo" / "configs" / f"{args.escenario}.sumocfg",
                          config_interseccion, config_controlador, config_agente, config_experimento,
                          usar_gui=args.gui)
    tabla = TablaQ(entorno.codificador.numero_estados, aprendizaje["alfa"], aprendizaje["gamma"],
                   semilla=semilla_base)

    carpeta = CARPETA_MODELOS / args.nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_curva = carpeta / "curva_aprendizaje.csv"
    columnas = ["episodio", "semilla", "epsilon", "recompensa_total", "detenidos_promedio",
                "decisiones", "pedidos_de_cambio", "verdes_cra23", "verdes_dg15", "segundos_reloj"]
    metadatos = {"escenario": args.escenario, "config_agente": config_agente,
                 "config_controlador": config_controlador, "config_experimento": config_experimento}

    try:
        with open(ruta_curva, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=columnas)
            escritor.writeheader()
            for episodio in range(args.episodios):
                semilla = semilla_base + episodio
                epsilon = epsilon_lineal(episodio, aprendizaje["epsilon_inicial"],
                                         aprendizaje["epsilon_final"], aprendizaje["episodios_decaimiento"])
                inicio_reloj = time.perf_counter()

                estado = entorno.reset(semilla)
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
                    "episodio": episodio, "semilla": semilla, "epsilon": round(epsilon, 4),
                    "recompensa_total": recompensa_total,
                    "detenidos_promedio": round(entorno.detenidos_episodio / max(entorno.segundos_episodio, 1), 3),
                    "decisiones": decisiones, "pedidos_de_cambio": pedidos,
                    "verdes_cra23": verdes.count("cra23"), "verdes_dg15": verdes.count("dg15"),
                    "segundos_reloj": round(time.perf_counter() - inicio_reloj, 1),
                }
                escritor.writerow(fila)
                archivo.flush()
                tabla.guardar(carpeta / "tabla_q.json", {**metadatos, "episodios_entrenados": episodio + 1})
                print(f"ep {episodio:4d} | semilla {semilla} | eps {epsilon:.3f} | "
                      f"recompensa {recompensa_total:10.0f} | detenidos prom. {fila['detenidos_promedio']:6.2f} | "
                      f"decisiones {decisiones:4d} | {fila['segundos_reloj']:5.1f} s")
    finally:
        entorno.close()

    estados_visitados = sum(1 for fila in tabla.visitas if sum(fila) > 0)
    print(f"\nTabla guardada en: {carpeta / 'tabla_q.json'}")
    print(f"Estados visitados: {estados_visitados} de {tabla.numero_estados}")


if __name__ == "__main__":
    main()
