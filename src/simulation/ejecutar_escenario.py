"""
Ejecuta UNA corrida completa: escenario de SUMO + controlador + capa de seguridad,
y guarda las metricas.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe -m src.simulation.ejecutar_escenario --escenario prueba --semilla 42
  (agregar --gui para verla en sumo-gui)

Resultados en results/<escenario>/<controlador>/semilla_<n>/:
  resumen.json     metricas de la corrida + parametros usados (reproducibilidad)
  series.csv       fase y detenidos por brazo en cada segundo
  tripinfo.xml     salida original de SUMO (un registro por vehiculo)
"""
import argparse
import csv
import json
import platform
from datetime import datetime
from pathlib import Path

import traci
import yaml

from src.agent.codificador_estado import CodificadorEstado
from src.agent.qlearning import TablaQ
from src.common.configuracion import CARPETA_TESIS, cargar_interseccion
from src.controller.qlearning_controlador import ControladorQLearning
from src.controller.safety_guard import SafetyGuard
from src.controller.tiempos_fijos import ControladorTiemposFijos
from src.metrics.metricas import leer_tripinfo, resumir_colas, resumir_verdes, resumir_viajes
from src.simulation import desatascador as modulo_desatascador
from src.simulation import semaforo_calle18
from src.simulation.sesion_sumo import sesion_sumo
from src.simulation.sumo_actuator import SumoActuator
from src.simulation.sumo_source import SumoSource

CARPETA_CONFIG = CARPETA_TESIS / "config"
CARPETA_ESCENARIOS = CARPETA_TESIS / "sumo" / "configs"
CARPETA_RESULTADOS = CARPETA_TESIS / "results"
CARPETA_MODELOS = CARPETA_TESIS / "models"
CONTROLADORES = ["tiempos_fijos", "tiempos_fijos_norma", "qlearning"]
# Perfil de seguridad de cada controlador (config/controlador.yaml):
#   tiempos_fijos       semaforo real tal cual (todo-rojo medido)              -> "real"
#   tiempos_fijos_norma semaforo real con el todo-rojo del Manual (referencia) -> "norma"
#   qlearning           el perfil CON EL QUE SE ENTRENO (perfil_seguridad en la config del modelo; los modelos
#                       anteriores a la iteracion 4b no lo guardaban: usaban "norma")
PERFIL_SEGURIDAD = {"tiempos_fijos": "real", "tiempos_fijos_norma": "norma"}


def perfil_seguridad(nombre_controlador, modelo=None):
    if nombre_controlador != "qlearning":
        return PERFIL_SEGURIDAD[nombre_controlador]
    if modelo is None:
        raise ValueError("El controlador qlearning necesita --modelo (carpeta en models/).")
    config_agente = TablaQ.cargar(CARPETA_MODELOS / modelo / "tabla_q.json").metadatos.get("config_agente") or {}
    return config_agente.get("perfil_seguridad", "norma")


def leer_yaml(nombre):
    with open(CARPETA_CONFIG / nombre, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def crear_controlador(nombre, config_controlador, guard, config_interseccion=None, modelo=None):
    if nombre in ("tiempos_fijos", "tiempos_fijos_norma"):
        return ControladorTiemposFijos.desde_config(config_controlador, guard)
    if nombre == "qlearning":
        if modelo is None:
            raise ValueError("El controlador qlearning necesita --modelo (carpeta en models/).")
        tabla = TablaQ.cargar(CARPETA_MODELOS / modelo / "tabla_q.json")
        # Se usa la configuracion del agente CON LA QUE SE ENTRENO (guardada en el modelo), no la actual: asi cada
        # modelo se evalua siempre con su propia definicion de estado aunque config/agente.yaml cambie despues.
        config_agente = tabla.metadatos.get("config_agente") or leer_yaml("agente.yaml")
        codificador = CodificadorEstado(config_interseccion, config_agente)
        return ControladorQLearning(tabla, codificador, guard, config_agente["intervalo_decision_s"],
                                    config_controlador["tiempos_fijos"]["verde_s"])
    raise ValueError(f"Controlador desconocido: {nombre}. Disponibles: {CONTROLADORES}")


def simular(archivo_escenario, semilla, usar_gui, nombre_controlador, configs, ruta_tripinfo, modelo=None,
            zona="siempre", ruta_log=None):
    """Corre la simulacion y devuelve (filas por segundo, guard, controlador, info de cierre).
    zona = "siempre": mide la zona de camara cada segundo (series.csv completo).
    zona = "al_decidir": solo cuando el controlador va a decidir (mismo resultado, mas rapido; para la comparacion)."""
    if zona not in ("siempre", "al_decidir"):
        raise ValueError(f"zona debe ser 'siempre' o 'al_decidir' (recibido {zona})")
    config_interseccion, config_controlador, config_experimento = configs
    limite = config_experimento["duracion_demanda_s"] + config_experimento["margen_vaciado_s"]
    filas = []

    extra = ["--tripinfo-output", ruta_tripinfo]
    if ruta_log is not None:
        # avisos de SUMO (teleports, frenadas de emergencia, colisiones) con carril y tiempo: auditoria de atascos
        extra += ["--error-log", ruta_log]
    with sesion_sumo(archivo_escenario, usar_gui=usar_gui, semilla=semilla, argumentos_extra=extra):
        desfase_calle18 = semaforo_calle18.configurar(semilla)
        desatascador = modulo_desatascador.crear_desde_config()   # solo actua en el semaforo de la Calle 18
        fuente = SumoSource(config_interseccion)
        actuador = SumoActuator(config_interseccion)
        guard = SafetyGuard.desde_config(config_controlador, perfil_seguridad(nombre_controlador, modelo))
        controlador = crear_controlador(nombre_controlador, config_controlador, guard,
                                        config_interseccion, modelo)

        tiempo = traci.simulation.getTime()
        fase = guard.iniciar(tiempo)
        actuador.aplicar(fase)

        teletransportes = 0  # vehiculos que SUMO saco de un atasco (>300 s quietos) o de una colision
        while traci.simulation.getMinExpectedNumber() > 0 and tiempo < limite:
            traci.simulationStep()
            tiempo = traci.simulation.getTime()
            teletransportes += traci.simulation.getStartingTeleportNumber()
            if desatascador is not None:
                desatascador.paso(tiempo)
            actuador.verificar()

            if zona == "siempre":
                incluir_zona = True
            else:
                va_a_decidir = getattr(controlador, "va_a_decidir", None)
                incluir_zona = va_a_decidir is not None and va_a_decidir(tiempo)
            estado = fuente.leer_estado(incluir_zona=incluir_zona)
            fila = {"tiempo": tiempo, "fase": fase}
            fila.update({f"detenidos_{n}": b.detenidos for n, b in estado.brazos.items()})
            fila.update({f"detenidos_zona_{n}": b.detenidos_zona for n, b in estado.brazos.items()})
            fila.update({f"vehiculos_zona_{n}": b.vehiculos_zona for n, b in estado.brazos.items()})
            filas.append(fila)

            nueva_fase = guard.paso(tiempo, controlador.pedir_cambio(tiempo, estado))
            if nueva_fase != fase:
                actuador.aplicar(nueva_fase)
                fase = nueva_fase

        cierre = {
            "tiempo_final_s": tiempo,
            "vehiculos_sin_terminar": traci.simulation.getMinExpectedNumber(),
            "version_sumo": traci.getVersion()[1],
            "desfase_calle18_s": desfase_calle18,
            "teletransportes": teletransportes,
            "desatascos_calle18": len(desatascador.eventos) if desatascador is not None else 0,
            "eventos_desatasco": desatascador.eventos if desatascador is not None else [],
            "diagnostico_desatasco": desatascador.diagnostico if desatascador is not None else [],
        }
    return filas, guard, controlador, cierre


def main():
    parser = argparse.ArgumentParser(description="Ejecuta un escenario y guarda sus metricas.")
    parser.add_argument("--escenario", required=True, help="nombre del .sumocfg en sumo/configs (sin extension)")
    parser.add_argument("--controlador", default="tiempos_fijos", choices=CONTROLADORES)
    parser.add_argument("--semilla", type=int, required=True)
    parser.add_argument("--modelo", help="solo para qlearning: carpeta del modelo en models/")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()
    nombre_resultado = args.controlador if args.controlador != "qlearning" else f"qlearning_{args.modelo}"

    archivo_escenario = CARPETA_ESCENARIOS / f"{args.escenario}.sumocfg"
    configs = (cargar_interseccion(), leer_yaml("controlador.yaml"), leer_yaml("experimento.yaml"))
    config_interseccion, config_controlador, config_experimento = configs

    carpeta_salida = CARPETA_RESULTADOS / args.escenario / nombre_resultado / f"semilla_{args.semilla}"
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    ruta_tripinfo = carpeta_salida / "tripinfo.xml"

    print(f"Escenario: {args.escenario} | controlador: {args.controlador} | semilla: {args.semilla}")
    filas, guard, controlador, cierre = simular(archivo_escenario, args.semilla, args.gui, args.controlador,
                                                configs, ruta_tripinfo, args.modelo,
                                                ruta_log=carpeta_salida / "avisos_sumo.log")

    inicio = config_experimento["calentamiento_s"]
    fin = config_experimento["duracion_demanda_s"]
    brazos = list(config_interseccion["brazos"])
    metricas = {}
    metricas.update(resumir_viajes(leer_tripinfo(ruta_tripinfo), inicio, fin))
    metricas.update(resumir_colas(filas, brazos, inicio, fin))
    metricas.update(resumir_verdes(guard.historial_verdes, inicio, fin))
    metricas["cambios_rechazados"] = guard.cambios_rechazados
    metricas["cambios_forzados"] = guard.cambios_forzados
    if args.controlador == "qlearning":
        metricas["decisiones_agente"] = controlador.decisiones
        metricas["decisiones_respaldo"] = controlador.decisiones_respaldo
        metricas["pedidos_de_cambio"] = controlador.pedidos_de_cambio

    with open(carpeta_salida / "series.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    resumen = {
        "escenario": args.escenario,
        "controlador": nombre_resultado,
        "semilla": args.semilla,
        "ventana_medicion_s": [inicio, fin],
        "metricas": metricas,
        "cierre": cierre,
        "parametros": {"controlador": config_controlador, "experimento": config_experimento},
        "entorno": {"python": platform.python_version(), "fecha": datetime.now().isoformat(timespec="seconds")},
    }
    with open(carpeta_salida / "resumen.json", "w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, indent=2, ensure_ascii=False)

    print(f"\nResultados guardados en: {carpeta_salida}")
    print(f"Ventana de medicion: {inicio}-{fin} s | fin de simulacion: {cierre['tiempo_final_s']:.0f} s | "
          f"vehiculos sin terminar: {cierre['vehiculos_sin_terminar']} | teleports: {cierre['teletransportes']} | "
          f"desatascos Calle 18: {cierre['desatascos_calle18']}")
    for tiempo_evento, vehiculo, carril, destino in cierre["eventos_desatasco"]:
        print(f"   desatasco t={tiempo_evento:.0f} s: {vehiculo} ({carril} -> {destino})")
    for tiempo_evento, vehiculo, carril, luz, lider in cierre["diagnostico_desatasco"][:15]:
        print(f"   DIAGNOSTICO t={tiempo_evento:.0f} s: {vehiculo} quieto 60 s en {carril}, luz '{luz}', lider {lider}")
    print("\nMetricas:")
    for clave, valor in metricas.items():
        print(f"   {clave:<32} {valor:10.2f}" if isinstance(valor, float) else f"   {clave:<32} {valor:>10}")


if __name__ == "__main__":
    main()
