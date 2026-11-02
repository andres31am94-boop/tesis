"""
Plan de TIEMPOS FIJOS OPTIMIZADO por el metodo de Webster (1958), uno por escenario de aforo (2026-10-29).

Para que sirve: responde la pregunta "el agente gana solo porque el semaforo real esta mal programado?". Webster es el
metodo clasico para calcular el mejor plan fijo cuando se conoce la demanda. Como aqui se calcula con la demanda EXACTA de
cada escenario (aforo de esa hora), es el mejor caso posible para un semaforo de tiempos fijos (en la realidad un plan
fijo no sabe exactamente que hora es ni cuanta demanda llegara).

Formulas (Webster; ver Manual de Senalizacion Vial / HCM):
  y_i  = flujo critico de la fase i / flujo de saturacion   (flujo en vehiculos equivalentes; carril critico)
  Y    = y_cra23 + y_dg15
  L    = tiempo perdido por ciclo = intervalos de cambio (amarillo + todo-rojo) + perdida de arranque por fase
  C0   = (1.5 L + 5) / (1 - Y)                    ciclo optimo
  g_i  = (C0 - L) * y_i / Y                       verde efectivo de cada fase
  verde mostrado = g_i + perdida de arranque (el todo-rojo y el amarillo ya estan en L)
Despues se ajusta a la capa de seguridad (verde minimo y maximo por eje) y se redondea al segundo.

Supuestos (declarados, no medidos en campo): flujo de saturacion 1800 veh. equivalentes/h/carril; equivalencias carro 1,
moto 0.33, bus 2, camion 2; 2 carriles por brazo cerca del cruce; perdida de arranque 2 s por fase.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\plan_webster.py
Salida: config/plan_webster.yaml (lo lee el controlador "tiempos_fijos_webster")
"""
import csv
from pathlib import Path

import yaml

CARPETA_TESIS = Path(__file__).resolve().parents[1]
ESCENARIOS = ["aforo_bajo", "aforo_valle_manana", "aforo_medio", "aforo_alto", "aforo_pico_jueves"]
EQUIVALENTES = {"carro": 1.0, "moto": 0.33, "bus": 2.0, "camion": 2.0}
SATURACION_POR_CARRIL = 1800.0
PERDIDA_ARRANQUE_S = 2.0


def main():
    with open(CARPETA_TESIS / "config" / "interseccion.yaml", encoding="utf-8") as archivo:
        brazos = yaml.safe_load(archivo)["brazos"]
    with open(CARPETA_TESIS / "config" / "controlador.yaml", encoding="utf-8") as archivo:
        seguridad = yaml.safe_load(archivo)["seguridad"]
    ejes = sorted({d["eje"] for d in brazos.values()})
    carriles = {b: 2 for b in brazos}   # 2 carriles por brazo en la llegada al cruce (red: ajustes.edg.xml)
    amarillo, todo_rojo = seguridad["amarillo_s"], seguridad["todo_rojo_s"]
    perdido = sum(amarillo + todo_rojo[e] for e in ejes) + PERDIDA_ARRANQUE_S * len(ejes)
    planes = {}
    print(f"Tiempo perdido por ciclo L = {perdido:.0f} s")
    for escenario in ESCENARIOS:
        flujo = {b: 0.0 for b in brazos}
        with open(CARPETA_TESIS / "sumo" / "demanda" / f"{escenario}_flujos.csv", encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                flujo[fila["brazo_llegada"]] += float(fila["vehiculos_hora"]) * EQUIVALENTES[fila["tipo"]]
        y = {e: max(flujo[b] / (carriles[b] * SATURACION_POR_CARRIL) for b in brazos if brazos[b]["eje"] == e)
             for e in ejes}
        y_total = sum(y.values())
        if y_total >= 1:
            raise ValueError(f"{escenario}: Y = {y_total:.2f} >= 1 (sobresaturado, Webster no aplica)")
        ciclo = (1.5 * perdido + 5) / (1 - y_total)
        verdes = {}
        for e in ejes:
            mostrado = (ciclo - perdido) * y[e] / y_total + PERDIDA_ARRANQUE_S
            ajustado = min(max(mostrado, seguridad["verde_min_s"][e]), seguridad["verde_max_s"][e])
            verdes[e] = int(round(ajustado))
        ciclo_final = sum(verdes[e] + amarillo + todo_rojo[e] for e in ejes)
        planes[escenario] = {
            "verde_s": verdes, "ciclo_s": ciclo_final,
            "calculo": {"flujo_equivalente_veh_h": {b: round(v) for b, v in flujo.items()},
                        "y": {e: round(v, 3) for e, v in y.items()}, "Y": round(y_total, 3),
                        "ciclo_optimo_webster_s": round(ciclo, 1),
                        "verde_webster_s": {e: round((ciclo - perdido) * y[e] / y_total + PERDIDA_ARRANQUE_S, 1)
                                            for e in ejes}},
        }
        print(f"{escenario:<20} Y = {y_total:.3f} | C0 = {ciclo:5.1f} s | verdes {verdes} | ciclo final {ciclo_final} s")
    salida = {
        "descripcion": "Plan fijo optimizado por Webster por escenario (generado por scripts/plan_webster.py; no editar).",
        "supuestos": {"saturacion_veh_eq_h_carril": SATURACION_POR_CARRIL, "equivalentes": EQUIVALENTES,
                      "perdida_arranque_s": PERDIDA_ARRANQUE_S, "tiempo_perdido_ciclo_s": perdido,
                      "carriles_por_brazo": carriles},
        "planes": planes,
    }
    ruta = CARPETA_TESIS / "config" / "plan_webster.yaml"
    ruta.write_text(yaml.safe_dump(salida, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Guardado en {ruta}")


if __name__ == "__main__":
    main()
