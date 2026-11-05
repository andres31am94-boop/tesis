"""
Fase 9: traduce lo que la camara ve en la MAQUETA a la escala de la interseccion real que el agente aprendio en SUMO.

Problema: en SUMO la zona de camara de cada brazo son los ultimos 100 m antes de la linea de pare. En la maqueta un
brazo se llena con unos pocos carros. Si el agente recibiera "4", creeria que la cola es baja.

Solucion (ocupacion relativa): la misma FRACCION de brazo lleno en la maqueta = la misma fraccion de zona llena en SUMO.
    vehiculos_equivalentes = round( min(carros, capacidad_maqueta) / capacidad_maqueta * capacidad_sumo_del_brazo )

La capacidad SUMO es POR BRAZO y sale de la red (sumo/network/acacias.net.xml), igual que la calcula SumoSource:
largo de los carriles dentro de la zona / espacio por vehiculo (7.5 m). Asi el brazo norte, que tiene 41 m de 2
carriles + el puente de 1 carril, vale ~18.7 vehiculos y los demas (2 carriles en toda la zona) ~26.7.

Entra: EstadoTrafico con los conteos de la camara (ContadorZonas) y la capacidad en carros de cada brazo de la maqueta.
Sale: EstadoTrafico con vehiculos_zona y detenidos_zona en "vehiculos equivalentes" (lo que el agente entiende).
"""
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

from src.common.estado import EstadoTrafico

RED_SUMO = Path(__file__).resolve().parents[2] / "sumo" / "network" / "acacias.net.xml"


def capacidades_zona_sumo(config_interseccion, ruta_red=RED_SUMO):
    """{brazo: vehiculos que caben en su zona de camara en SUMO}. Recorre los tramos de cada brazo desde la linea de
    pare hacia atras y suma (largo dentro de la zona x numero de carriles) / espacio_por_vehiculo_m."""
    zona = float(config_interseccion["zona_camara_m"])
    espacio = float(config_interseccion["espacio_por_vehiculo_m"])
    tramos = {}
    for edge in ET.parse(ruta_red).getroot().iter("edge"):
        if edge.get("function") != "internal":
            carriles = edge.findall("lane")
            tramos[edge.get("id")] = (float(carriles[0].get("length")), len(carriles))
    capacidades = {}
    for brazo, datos in config_interseccion["brazos"].items():
        distancia, metros_carril = 0.0, 0.0
        for edge in datos["edges"]:
            if edge not in tramos:
                raise ValueError(f"El tramo '{edge}' del brazo '{brazo}' no esta en {ruta_red}")
            largo, carriles = tramos[edge]
            dentro = max(0.0, min(largo, zona - distancia))
            metros_carril += dentro * carriles
            distancia += largo
        capacidades[brazo] = metros_carril / espacio
    return capacidades


class EscaladorMaqueta:
    def __init__(self, capacidad_carros, capacidad_sumo):
        """capacidad_carros: {brazo: carros que llenan el brazo en la maqueta}.
        capacidad_sumo: {brazo: vehiculos de su zona en SUMO} (o un numero, igual para todos los brazos)."""
        if not isinstance(capacidad_sumo, dict):
            capacidad_sumo = dict.fromkeys(capacidad_carros, capacidad_sumo)
        for brazo, capacidad in capacidad_carros.items():
            if capacidad <= 0:
                raise ValueError(f"Capacidad del brazo '{brazo}' en la maqueta debe ser positiva: {capacidad}")
            if capacidad_sumo.get(brazo, 0) <= 0:
                raise ValueError(f"Falta o no es positiva la capacidad SUMO del brazo '{brazo}'")
        self.capacidad_carros = dict(capacidad_carros)
        self.capacidad_sumo = {brazo: capacidad_sumo[brazo] for brazo in capacidad_carros}

    def equivalentes(self, brazo, carros):
        capacidad = self.capacidad_carros[brazo]
        return round(min(carros, capacidad) / capacidad * self.capacidad_sumo[brazo])

    def escalar(self, estado: EstadoTrafico) -> EstadoTrafico:
        brazos = {}
        for nombre, datos in estado.brazos.items():
            presentes = self.equivalentes(nombre, datos.vehiculos_zona)
            detenidos = self.equivalentes(nombre, datos.detenidos_zona)
            brazos[nombre] = replace(datos, vehiculos=presentes, detenidos=detenidos,
                                     cola_relativa=min(datos.detenidos_zona, self.capacidad_carros[nombre])
                                     / self.capacidad_carros[nombre],
                                     vehiculos_zona=presentes, detenidos_zona=detenidos)
        return EstadoTrafico(tiempo=estado.tiempo, brazos=brazos)
