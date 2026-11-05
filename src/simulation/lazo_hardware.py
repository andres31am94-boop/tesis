"""
HARDWARE EN EL LAZO (hardware-in-the-loop), pasos 10.5b y 10.5c.

El semaforo fisico (ESP32 + LEDs) controla el cruce SIMULADO en SUMO, en tiempo real (1 s simulado = 1 s de reloj):

  cada segundo:  SUMO avanza 1 s -> Python lee el trafico -> controlador + SafetyGuard deciden la luz
                 -> Python envia "LUZ <luz>" al ESP32 -> el ESP32 la enciende y responde "OK"
                 -> SOLO ENTONCES Python pone esa luz en el semaforo de SUMO.
  Asi SUMO muestra la luz que el semaforo fisico CONFIRMO encender. Si el ESP32 no confirma, o activa un freno
  (AUTO / MODO INTERMITENTE / ERROR), la corrida se detiene con un error: no se sigue con luces distintas.

Partes de la corrida:
  1. Avance rapido (sin ESP32, sin esperar al reloj) hasta --inicio_s, para que el cruce ya tenga trafico.
  2. Lazo con el ESP32 durante --duracion_s, a ritmo de reloj real (--velocidad 1).
  3. (--comparar) La MISMA corrida sin ESP32 y sin esperar al reloj (simulacion pura, misma semilla). Si el lazo no
     altera nada, las dos deben dar exactamente las mismas luces y detenidos segundo a segundo.

Uso (desde la carpeta tesis, con Arduino IDE / Monitor Serie CERRADO):
  .\\.venv\\Scripts\\python.exe -m src.simulation.lazo_hardware --escenario aforo_alto --semilla 1 ^
      --controlador tiempos_fijos --puerto COM4 --inicio_s 900 --duracion_s 300 --gui --comparar
  (agente: --controlador qlearning --modelo aforo_v8)

Resultados en results/hardware/lazo/<escenario>_<controlador>_s<semilla>_t<inicio>-<fin>/:
  series_lazo.csv     luz y detenidos por brazo en cada segundo (corrida con el ESP32)
  cambios_lazo.csv    cada cambio de luz: tiempo simulado, latencia de confirmacion del ESP32 (ms)
  series_pura.csv     lo mismo sin ESP32 (solo con --comparar)
  resumen.json        parametros, latencias, retraso respecto al reloj, resultado de la comparacion
"""
import argparse
import csv
import json
import platform
import statistics
import time
from datetime import datetime

import traci

from src.common.configuracion import cargar_interseccion
from src.communication.esp32_serial import ConexionESP32
from src.controller.safety_guard import SafetyGuard
from src.simulation import desatascador as modulo_desatascador
from src.simulation import semaforo_calle18
from src.simulation.ejecutar_escenario import (CARPETA_ESCENARIOS, CARPETA_RESULTADOS, CONTROLADORES,
                                               crear_controlador, leer_yaml, perfil_seguridad)
from src.simulation.sesion_sumo import sesion_sumo
from src.simulation.sumo_actuator import SumoActuator
from src.simulation.sumo_source import SumoSource
from src.common.registro_computo import registrar_ejecucion

ESPERA_CONFIRMACION_S = 0.5   # tiempo maximo para que el ESP32 confirme un cambio de luz
ESPERA_LISTO_S = 4.0


class ErrorLazo(RuntimeError):
    """El semaforo fisico no confirmo una luz o activo un freno: la simulacion ya no seria fiel."""


def esperar_listo(conexion):
    fin = time.monotonic() + ESPERA_LISTO_S
    while time.monotonic() < fin:
        mensaje = conexion.leer_mensaje()
        if mensaje is not None and mensaje.tipo == "LISTO":
            return
    raise ErrorLazo(f"El ESP32 no envio LISTO en {ESPERA_LISTO_S} s (revise el puerto y el firmware semaforo_obediente)")


def revisar_mensaje(mensaje):
    if mensaje.tipo in ("ERROR", "AUTO", "MODO"):
        raise ErrorLazo(f"El ESP32 activo un freno o rechazo una orden: '{mensaje.texto}'")


def enviar_y_confirmar(conexion, fase):
    """Envia la luz y espera el OK del ESP32. Devuelve la latencia en ms (reloj del PC)."""
    luz = fase.upper()
    inicio = time.monotonic()
    conexion.enviar_luz(luz)
    while time.monotonic() - inicio < ESPERA_CONFIRMACION_S:
        mensaje = conexion.leer_mensaje()
        if mensaje is None:
            continue
        revisar_mensaje(mensaje)
        if mensaje.tipo == "OK" and mensaje.partes[1] == luz:
            return (time.monotonic() - inicio) * 1000
    raise ErrorLazo(f"El ESP32 no confirmo la luz {luz} en {ESPERA_CONFIRMACION_S} s")


def leer_pendientes(conexion):
    while conexion.hay_mensajes():
        mensaje = conexion.leer_mensaje()
        if mensaje is not None:
            revisar_mensaje(mensaje)


def correr(escenario, semilla, nombre_controlador, modelo, inicio_s, duracion_s, usar_gui=False, puerto=None,
           velocidad=1.0):
    """Corre la simulacion. Con puerto=None es la simulacion pura (sin ESP32 ni reloj).
    Devuelve (filas de la ventana [inicio_s, inicio_s + duracion_s], cambios, info)."""
    config_interseccion = cargar_interseccion()
    config_controlador = leer_yaml("controlador.yaml")
    archivo_escenario = CARPETA_ESCENARIOS / f"{escenario}.sumocfg"
    fin_s = inicio_s + duracion_s
    filas, cambios, retrasos_ms = [], [], []
    conexion = None

    with sesion_sumo(archivo_escenario, usar_gui=usar_gui, semilla=semilla, retraso_gui_ms=0):
        semaforo_calle18.configurar(semilla)
        desatascador = modulo_desatascador.crear_desde_config()
        fuente = SumoSource(config_interseccion)
        actuador = SumoActuator(config_interseccion)
        guard = SafetyGuard.desde_config(config_controlador, perfil_seguridad(nombre_controlador, modelo))
        controlador = crear_controlador(nombre_controlador, config_controlador, guard, config_interseccion, modelo,
                                        escenario=escenario)
        tiempo = traci.simulation.getTime()
        fase = guard.iniciar(tiempo)
        actuador.aplicar(fase)

        try:
            reloj_inicio = None
            while tiempo < fin_s:
                if traci.simulation.getMinExpectedNumber() == 0:
                    raise ErrorLazo(f"La simulacion se quedo sin vehiculos en t={tiempo:.0f} s (antes de {fin_s} s)")
                en_lazo = tiempo >= inicio_s
                if en_lazo and reloj_inicio is None:
                    reloj_inicio = time.monotonic()
                    tiempo_lazo_inicio = tiempo
                    if puerto is not None:
                        print(f"t={tiempo:.0f} s: conectando con el ESP32 en {puerto}...")
                        conexion = ConexionESP32(puerto)
                        esperar_listo(conexion)
                        if fase == "todo_rojo":
                            conexion.enviar_luz(fase)   # el ESP32 arranca en todo rojo: no hay cambio que confirmar
                            latencia = None
                        else:
                            latencia = round(enviar_y_confirmar(conexion, fase), 2)
                        cambios.append({"tiempo": tiempo, "luz": fase, "latencia_ms": latencia})
                        print(f"t={tiempo:.0f} s: ESP32 sincronizado en {fase.upper()}. Lazo en tiempo real "
                              f"durante {duracion_s} s.")
                        reloj_inicio = time.monotonic()
                if en_lazo and puerto is not None:
                    objetivo = reloj_inicio + (tiempo - tiempo_lazo_inicio) / velocidad
                    espera = objetivo - time.monotonic()
                    if espera > 0:
                        time.sleep(espera)
                    elif espera < 0:
                        retrasos_ms.append(-espera * 1000)   # el paso empezo tarde respecto al reloj

                traci.simulationStep()
                tiempo = traci.simulation.getTime()
                if desatascador is not None:
                    desatascador.paso(tiempo)
                actuador.verificar()

                incluir_zona = True
                estado = fuente.leer_estado(incluir_zona=incluir_zona)
                if tiempo > inicio_s:
                    fila = {"tiempo": tiempo, "fase": fase}
                    fila.update({f"detenidos_{n}": b.detenidos for n, b in estado.brazos.items()})
                    fila.update({f"detenidos_zona_{n}": b.detenidos_zona for n, b in estado.brazos.items()})
                    filas.append(fila)

                nueva_fase = guard.paso(tiempo, controlador.pedir_cambio(tiempo, estado))
                if conexion is not None:
                    leer_pendientes(conexion)
                    if nueva_fase != fase:
                        latencia = enviar_y_confirmar(conexion, nueva_fase)
                        cambios.append({"tiempo": tiempo, "luz": nueva_fase, "latencia_ms": round(latencia, 2)})
                        print(f"t={tiempo:.0f} s: {nueva_fase.upper():<15} confirmado por el ESP32 en {latencia:.1f} ms")
                    else:
                        conexion.enviar_luz(nueva_fase)   # latido: el ESP32 sabe que Python sigue vivo
                elif tiempo > inicio_s and nueva_fase != fase:
                    cambios.append({"tiempo": tiempo, "luz": nueva_fase, "latencia_ms": None})
                if nueva_fase != fase:
                    actuador.aplicar(nueva_fase)
                    fase = nueva_fase
        finally:
            if conexion is not None:
                conexion.cerrar()   # sin latidos, el ESP32 pasara a intermitente a los 5 s (comportamiento esperado)

    info = {"retraso_reloj_max_ms": round(max(retrasos_ms), 1) if retrasos_ms else 0.0,
            "pasos_atrasados": len(retrasos_ms)}
    return filas, cambios, info


def guardar_csv(ruta, filas):
    if not filas:
        return
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def main():
    registrar_ejecucion()
    parser = argparse.ArgumentParser(description="Hardware en el lazo: el ESP32 controla el cruce simulado en SUMO.")
    parser.add_argument("--escenario", required=True, help="nombre del .sumocfg en sumo/configs, p. ej. aforo_alto")
    parser.add_argument("--semilla", type=int, required=True)
    parser.add_argument("--controlador", default="tiempos_fijos", choices=CONTROLADORES)
    parser.add_argument("--modelo", help="solo para qlearning: carpeta del modelo en models/ (p. ej. aforo_v8)")
    parser.add_argument("--puerto", required=True, help="puerto serie del ESP32, p. ej. COM4")
    parser.add_argument("--inicio_s", type=int, default=900, help="segundo simulado en que empieza el lazo")
    parser.add_argument("--duracion_s", type=int, default=300, help="segundos de lazo en tiempo real")
    parser.add_argument("--velocidad", type=float, default=1.0, help="1 = tiempo real")
    parser.add_argument("--gui", action="store_true", help="mostrar sumo-gui")
    parser.add_argument("--comparar", action="store_true", help="repetir sin ESP32 y comparar segundo a segundo")
    args = parser.parse_args()

    nombre = args.controlador if args.controlador != "qlearning" else f"qlearning_{args.modelo}"
    carpeta = (CARPETA_RESULTADOS / "hardware" / "lazo" /
               f"{args.escenario}_{nombre}_s{args.semilla}_t{args.inicio_s}-{args.inicio_s + args.duracion_s}")
    carpeta.mkdir(parents=True, exist_ok=True)

    print(f"Escenario {args.escenario} | {nombre} | semilla {args.semilla} | lazo t={args.inicio_s}-"
          f"{args.inicio_s + args.duracion_s} s | velocidad x{args.velocidad}")
    filas_lazo, cambios_lazo, info = correr(args.escenario, args.semilla, args.controlador, args.modelo,
                                            args.inicio_s, args.duracion_s, args.gui, args.puerto, args.velocidad)
    guardar_csv(carpeta / "series_lazo.csv", filas_lazo)
    guardar_csv(carpeta / "cambios_lazo.csv", cambios_lazo)
    latencias = [c["latencia_ms"] for c in cambios_lazo if c["latencia_ms"] is not None]
    resumen = {
        "escenario": args.escenario, "controlador": nombre, "semilla": args.semilla,
        "ventana_s": [args.inicio_s, args.inicio_s + args.duracion_s], "velocidad": args.velocidad,
        "puerto": args.puerto,
        "cambios_de_luz": len(cambios_lazo),
        "latencia_confirmacion_ms": {"media": round(statistics.mean(latencias), 2), "maxima": max(latencias),
                                     "n": len(latencias)},
        "retraso_respecto_al_reloj": info,
        "entorno": {"python": platform.python_version(), "fecha": datetime.now().isoformat(timespec="seconds")},
    }
    print(f"\nCambios de luz confirmados por el ESP32: {len(cambios_lazo)} | latencia media "
          f"{resumen['latencia_confirmacion_ms']['media']} ms, maxima {resumen['latencia_confirmacion_ms']['maxima']} ms")
    print(f"Pasos que llegaron tarde al reloj: {info['pasos_atrasados']} (retraso maximo {info['retraso_reloj_max_ms']} ms)")

    if args.comparar:
        print("\nComparando con la simulacion pura (sin ESP32, misma semilla)...")
        filas_pura, cambios_pura, _ = correr(args.escenario, args.semilla, args.controlador, args.modelo,
                                             args.inicio_s, args.duracion_s)
        guardar_csv(carpeta / "series_pura.csv", filas_pura)
        segundos_distintos = [a["tiempo"] for a, b in zip(filas_lazo, filas_pura) if a != b]
        cambios_iguales = ([(c["tiempo"], c["luz"]) for c in cambios_lazo[1:]] ==
                           [(c["tiempo"], c["luz"]) for c in cambios_pura])
        identicas = len(filas_lazo) == len(filas_pura) and not segundos_distintos and cambios_iguales
        resumen["comparacion_con_simulacion_pura"] = {
            "segundos_comparados": min(len(filas_lazo), len(filas_pura)),
            "segundos_distintos": len(segundos_distintos),
            "primeros_segundos_distintos": segundos_distintos[:10],
            "mismos_cambios_de_luz": cambios_iguales,
            "identicas": identicas,
        }
        print(f"Segundos comparados: {resumen['comparacion_con_simulacion_pura']['segundos_comparados']} | "
              f"distintos: {len(segundos_distintos)} | mismos cambios de luz: {cambios_iguales}")
        print("RESULTADO: lazo con ESP32 IDENTICO a la simulacion pura" if identicas
              else "RESULTADO: HAY DIFERENCIAS entre el lazo y la simulacion pura (revisar)")

    with open(carpeta / "resumen.json", "w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, indent=2, ensure_ascii=False)
    print(f"\nResultados en: {carpeta}")


if __name__ == "__main__":
    main()
