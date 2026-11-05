"""
Fase 9, paso 3: el agente aforo_v8 DECIDE con lo que ve la camara (sin ESP32 todavia).

Cada segundo:  conteo por brazo (carros) -> escala SUMO (EscaladorMaqueta) -> controlador -> SafetyGuard -> luz.
  - El controlador es el MISMO de la simulacion (ControladorQLearning con la tabla congelada de aforo_v8): decide al
    cumplirse el verde minimo y luego cada 5 s si MANTENER o CAMBIAR. El SafetyGuard (tiempos reales: verde min/max,
    amarillo, todo-rojo) tiene la ultima palabra.
  - Con --comparar se corre tambien el semaforo de TIEMPOS FIJOS (55 s / 20 s) con la misma entrada.

Entrada: un CSV por segundo con presentes_<brazo> y detenidos_<brazo> (el de scripts/contar_zonas_video.py o un
GUION de prueba). Limitacion de esta prueba (lazo ABIERTO): la entrada no reacciona a las luces (los carros de un video
o de un guion no avanzan cuando el agente da verde). Sirve para verificar la LOGICA de decision; el lazo cerrado es
con la maqueta (carros movidos segun la luz).

Uso (desde la carpeta tesis):
  python scripts/decidir_desde_conteo.py --conteo config/guiones_prueba/desbalance.csv --zonas config/zonas_prueba_1m.yaml --comparar
Salida: decisiones_<controlador>.csv junto al CSV de entrada (o en --salida).
"""
import argparse
import csv
import sys
from pathlib import Path

import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))

from src.agent.codificador_estado import CodificadorEstado  # noqa: E402
from src.agent.qlearning import TablaQ  # noqa: E402
from src.common.configuracion import cargar_interseccion  # noqa: E402
from src.common.estado import EstadoBrazo, EstadoTrafico  # noqa: E402
from src.controller.qlearning_controlador import ControladorQLearning  # noqa: E402
from src.controller.safety_guard import SafetyGuard  # noqa: E402
from src.controller.tiempos_fijos import ControladorTiemposFijos  # noqa: E402
from src.vision.escala_maqueta import EscaladorMaqueta, capacidades_zona_sumo  # noqa: E402

BRAZOS = ("norte", "sur", "este", "oeste")


def leer_yaml(ruta):
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))


def estados_desde_csv(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            brazos = {b: EstadoBrazo(vehiculos=int(fila[f"presentes_{b}"]), detenidos=int(fila[f"detenidos_{b}"]),
                                     cola_relativa=0.0, vehiculos_zona=int(fila[f"presentes_{b}"]),
                                     detenidos_zona=int(fila[f"detenidos_{b}"])) for b in BRAZOS}
            yield EstadoTrafico(tiempo=float(fila["segundo"]), brazos=brazos)


def correr(nombre, estados, escalador, config_controlador, tabla, codificador, config_agente):
    perfil = config_agente.get("perfil_seguridad", "norma") if nombre == "qlearning" else "real"
    guard = SafetyGuard.desde_config(config_controlador, perfil)
    if nombre == "qlearning":
        controlador = ControladorQLearning(tabla, codificador, guard, config_agente["intervalo_decision_s"],
                                           config_controlador["tiempos_fijos"]["verde_s"])
    else:
        controlador = ControladorTiemposFijos.desde_config(config_controlador, guard)
    filas = []
    fase = None
    for estado_camara in estados:
        tiempo = estado_camara.tiempo
        if fase is None:
            fase = guard.iniciar(tiempo)
            continue
        estado = escalador.escalar(estado_camara)
        decide = nombre == "qlearning" and controlador.va_a_decidir(tiempo)
        descripcion = ""
        if decide:
            descripcion = codificador.describir(codificador.codificar(estado, guard.eje, guard.tiempo_en_etapa(tiempo)))
        en_verde_desde = guard.tiempo_en_etapa(tiempo)
        respaldos_antes = getattr(controlador, "decisiones_respaldo", 0)
        pedir = controlador.pedir_cambio(tiempo, estado)
        respaldo = decide and getattr(controlador, "decisiones_respaldo", 0) > respaldos_antes
        nueva_fase = guard.paso(tiempo, pedir)
        fila = {"segundo": int(tiempo), "fase": fase, "s_en_etapa": int(en_verde_desde),
                "decision": ("CAMBIAR" if pedir else "MANTENER") if decide else "", "estado_visto": descripcion,
                "respaldo_plan_fijo": int(respaldo)}
        fila.update({f"carros_{b}": estado_camara.brazos[b].vehiculos_zona for b in BRAZOS})
        filas.append(fila)
        if decide or nueva_fase != fase:
            texto = f"t={int(tiempo):>4}s  {fase:<15} ({int(en_verde_desde):>2} s)"
            if decide:
                texto += f"  ve: {descripcion} -> {fila['decision']}" + ("  [RESPALDO: estado nunca visto]" if respaldo else "")
            if nueva_fase != fase:
                texto += f"  ==> {nueva_fase.upper()}"
            print(texto)
        fase = nueva_fase
    verdes = [(eje, round(duracion)) for eje, _, duracion in guard.historial_verdes]
    return filas, verdes, controlador


def main():
    parser = argparse.ArgumentParser(description="El agente decide con conteos de la camara (lazo abierto)")
    parser.add_argument("--conteo", required=True)
    parser.add_argument("--zonas", required=True)
    parser.add_argument("--modelo", default="aforo_v9", help="agente de la maqueta: aforo_v9 (adaptacion de v8)")
    parser.add_argument("--comparar", action="store_true", help="tambien tiempos fijos (55/20 s)")
    argumentos = parser.parse_args()

    config_zonas = leer_yaml(argumentos.zonas)
    config_interseccion = cargar_interseccion()
    config_controlador = leer_yaml(CARPETA_TESIS / "config" / "controlador.yaml")
    tabla = TablaQ.cargar(CARPETA_TESIS / "models" / argumentos.modelo / "tabla_q.json")
    config_agente = tabla.metadatos["config_agente"]
    codificador = CodificadorEstado(config_interseccion, config_agente)
    escalador = EscaladorMaqueta(config_zonas["capacidad_carros"], capacidades_zona_sumo(config_interseccion))

    controladores = ["qlearning"] + (["tiempos_fijos"] if argumentos.comparar else [])
    for nombre in controladores:
        print(f"\n===== {nombre.upper()} =====")
        filas, verdes, controlador = correr(nombre, estados_desde_csv(argumentos.conteo), escalador,
                                            config_controlador, tabla, codificador, config_agente)
        print(f"Verdes dados (eje, segundos): {verdes}")
        if nombre == "qlearning":
            print(f"Decisiones: {controlador.decisiones} | pidio cambiar: {controlador.pedidos_de_cambio} | "
                  f"con respaldo (estado nunca visto): {controlador.decisiones_respaldo}")
        ruta = Path(argumentos.conteo).with_name(f"decisiones_{Path(argumentos.conteo).stem}_{nombre}.csv")
        with open(ruta, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
            escritor.writeheader()
            escritor.writerows(filas)
        print(f"Guardado: {ruta}")


if __name__ == "__main__":
    main()
