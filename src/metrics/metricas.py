"""
Calculo de metricas de desempeno a partir de las salidas de SUMO.

Fuente principal: archivo tripinfo de SUMO (un registro por vehiculo que termino su recorrido).
Campos usados (definidos por SUMO):
  depart       instante real en que el vehiculo entro a la red (s)
  departDelay  tiempo que espero FUERA de la red porque no habia espacio para entrar (s)
  arrival      instante en que salio de la red (s)
  duration     tiempo de viaje dentro de la red (s)
  routeLength  distancia recorrida (m)
  waitingTime  tiempo detenido dentro de la red (velocidad < 0.1 m/s) (s)
  timeLoss     tiempo perdido respecto a viajar a la velocidad deseada (s)
"""
import statistics
import xml.etree.ElementTree as ET

SEGUNDOS_POR_HORA = 3600.0
MS_A_KMH = 3.6


def leer_tripinfo(ruta):
    viajes = []
    for elemento in ET.parse(ruta).getroot().iter("tripinfo"):
        depart = float(elemento.get("depart"))
        retraso_entrada = float(elemento.get("departDelay"))
        viajes.append({
            "id": elemento.get("id"),
            "tipo": elemento.get("vType"),
            "salida_programada": depart - retraso_entrada,  # cuando QUERIA entrar
            "retraso_entrada": retraso_entrada,
            "llegada": float(elemento.get("arrival")),
            "duracion": float(elemento.get("duration")),
            "distancia": float(elemento.get("routeLength")),
            "espera_en_red": float(elemento.get("waitingTime")),
            "tiempo_perdido": float(elemento.get("timeLoss")),
        })
    return viajes


def resumir_viajes(viajes, inicio_ventana, fin_ventana):
    """
    Metricas de los vehiculos que QUERIAN entrar dentro de la ventana de medicion
    [inicio_ventana, fin_ventana). Se usa la hora programada (no la real) para que un
    controlador que deja vehiculos esperando afuera no "esconda" esos vehiculos.
    """
    medidos = [v for v in viajes if inicio_ventana <= v["salida_programada"] < fin_ventana]
    if not medidos:
        raise ValueError("No hay vehiculos dentro de la ventana de medicion.")

    horas_ventana = (fin_ventana - inicio_ventana) / SEGUNDOS_POR_HORA
    salidas_en_ventana = sum(1 for v in viajes if inicio_ventana <= v["llegada"] < fin_ventana)

    def promedio(clave):
        return statistics.fmean(v[clave] for v in medidos)

    return {
        "vehiculos_medidos": len(medidos),
        "espera_total_promedio_s": statistics.fmean(v["espera_en_red"] + v["retraso_entrada"] for v in medidos),
        "espera_en_red_promedio_s": promedio("espera_en_red"),
        "retraso_entrada_promedio_s": promedio("retraso_entrada"),
        "tiempo_viaje_promedio_s": promedio("duracion"),
        "tiempo_perdido_promedio_s": promedio("tiempo_perdido"),
        "velocidad_promedio_kmh": statistics.fmean(
            v["distancia"] / v["duracion"] * MS_A_KMH for v in medidos if v["duracion"] > 0
        ),
        "throughput_veh_h": salidas_en_ventana / horas_ventana,
    }


def resumir_colas(filas, nombres_brazos, inicio_ventana, fin_ventana):
    """filas: lista de dicts con 'tiempo' y 'detenidos_<brazo>' (una por segundo)."""
    en_ventana = [f for f in filas if inicio_ventana <= f["tiempo"] < fin_ventana]
    if not en_ventana:
        raise ValueError("No hay registros de cola dentro de la ventana de medicion.")
    resumen = {}
    for brazo in nombres_brazos:
        valores = [f[f"detenidos_{brazo}"] for f in en_ventana]
        resumen[f"cola_promedio_{brazo}"] = statistics.fmean(valores)
        resumen[f"cola_maxima_{brazo}"] = max(valores)
    totales = [sum(f[f"detenidos_{b}"] for b in nombres_brazos) for f in en_ventana]
    resumen["detenidos_promedio_total"] = statistics.fmean(totales)
    return resumen


def resumir_verdes(historial_verdes, inicio_ventana, fin_ventana):
    """historial_verdes: lista de (eje, inicio_s, duracion_s) del SafetyGuard."""
    resumen = {}
    for eje in sorted({eje for eje, _, _ in historial_verdes}):
        duraciones = [d for e, inicio, d in historial_verdes if e == eje and inicio_ventana <= inicio < fin_ventana]
        if duraciones:
            resumen[f"verde_promedio_{eje}_s"] = statistics.fmean(duraciones)
            resumen[f"verdes_{eje}"] = len(duraciones)
    return resumen
