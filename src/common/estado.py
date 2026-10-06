"""
Estado del trafico: el "idioma comun" del sistema.

Lo producen las FUENTES de datos (hoy SumoSource; en la maqueta, CameraSource)
y lo consumen el controlador y el agente. Asi el agente no necesita saber
si los datos vienen de la simulacion o de la camara.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EstadoBrazo:
    vehiculos: int        # vehiculos presentes en el tramo de llegada
    detenidos: int        # vehiculos detenidos en el tramo de llegada
    cola_relativa: float  # detenidos / capacidad del tramo (0 = vacio, 1 = lleno)


@dataclass(frozen=True)
class EstadoTrafico:
    tiempo: float                    # segundos desde el inicio
    brazos: dict[str, EstadoBrazo]   # "norte", "sur", "este", "oeste"

    def detenidos_de(self, nombres_brazos):
        return sum(self.brazos[nombre].detenidos for nombre in nombres_brazos)
