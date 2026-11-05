"""
Fase 9: traduce lo que la camara ve en la MAQUETA a la escala de la intersección real que el agente aprendió en SUMO.

Problema: en SUMO la zona de camara de cada brazo son los ultimos 100 m con 2 carriles (~26 vehiculos). En la maqueta
un brazo se llena con unos pocos carros (p. ej. 5). Si el agente recibiera "5", creeria que la cola es baja.

Solucion (ocupacion relativa): la misma FRACCION de calle llena en la maqueta = la misma fraccion de zona llena en SUMO.
    vehiculos_equivalentes = round( min(carros, capacidad_brazo) / capacidad_brazo * capacidad_zona_sumo )

Entra: EstadoTrafico con los conteos de la camara (ContadorZonas) y la capacidad en carros de cada brazo de la maqueta.
Sale: EstadoTrafico con vehiculos_zona y detenidos_zona en "vehiculos equivalentes" (lo que el agente entiende).
"""
from dataclasses import replace

from src.common.estado import EstadoTrafico


def capacidad_zona_sumo(config_interseccion):
    """Vehiculos que caben en la zona de camara de un brazo en SUMO (carriles * metros / espacio por vehiculo)."""
    return (config_interseccion["carriles_zona_camara"] * config_interseccion["zona_camara_m"]
            / config_interseccion["espacio_por_vehiculo_m"])


class EscaladorMaqueta:
    def __init__(self, capacidad_carros, capacidad_sumo):
        if capacidad_sumo <= 0:
            raise ValueError("La capacidad de la zona en SUMO debe ser positiva")
        for brazo, capacidad in capacidad_carros.items():
            if capacidad <= 0:
                raise ValueError(f"Capacidad del brazo '{brazo}' debe ser positiva: {capacidad}")
        self.capacidad_carros = dict(capacidad_carros)
        self.capacidad_sumo = capacidad_sumo

    def equivalentes(self, brazo, carros):
        capacidad = self.capacidad_carros[brazo]
        return round(min(carros, capacidad) / capacidad * self.capacidad_sumo)

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
