"""
Estado del trafico: el "idioma comun" del sistema.

Lo producen las FUENTES de datos (hoy SumoSource; en la maqueta, CameraSource)
y lo consumen el controlador y el agente. Asi el agente no necesita saber
si los datos vienen de la simulacion o de la camara.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EstadoBrazo:
    # Brazo COMPLETO (todos los tramos de la zona de medicion). Lo usan la recompensa y las metricas.
    vehiculos: int        # vehiculos presentes en el brazo
    detenidos: int        # vehiculos detenidos en el brazo
    cola_relativa: float  # detenidos / capacidad del brazo (0 = vacio, 1 = lleno; informativo)
    # ZONA DE CAMARA: los ultimos "zona_camara_m" metros antes de la linea de pare, igual para todos los brazos.
    # Es lo que ve el agente para decidir (y lo que podra medir la camara en la maqueta).
    # None = no se midio en este segundo (el entrenamiento solo la mide cuando el agente decide, para ir mas rapido).
    vehiculos_zona: int | None
    detenidos_zona: int | None
    # Detenidos en los tramos AGUAS ARRIBA del brazo (accesos y tramo de la Calle 18), fuera de la zona de medicion.
    # Solo existe en simulacion: lo usa la recompensa del entrenamiento (iteracion 3); la camara no lo mide.
    detenidos_aguas_arriba: int | None = None


@dataclass(frozen=True)
class EstadoTrafico:
    tiempo: float                    # segundos desde el inicio
    brazos: dict[str, EstadoBrazo]   # "norte", "sur", "este", "oeste"

    def detenidos_de(self, nombres_brazos):
        return sum(self.brazos[nombre].detenidos for nombre in nombres_brazos)
