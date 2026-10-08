"""
Codificador de estado: convierte lo que observa el sistema (EstadoTrafico + fase)
en un NUMERO de estado para la tabla Q.

Estado = (nivel de cola Cra 23, nivel de cola Dg 15, eje en verde, nivel de tiempo en verde)

Para cada eje se usa la cola relativa del brazo MAS cargado: el brazo norte (puente)
tiene poca capacidad y un promedio con el sur escondería que se esta llenando.
Funciona igual con datos de SUMO o de la camara: solo necesita EstadoTrafico.
"""
from bisect import bisect_right

from src.controller.safety_guard import EJES


def nivel(valor, cortes):
    """Indice del intervalo: cortes [0.1, 0.3, 0.6] -> 0.05->0, 0.1->1, 0.45->2, 0.9->3."""
    return bisect_right(cortes, valor)


class CodificadorEstado:
    def __init__(self, config_interseccion, config_agente):
        self._brazos_por_eje = {eje: [] for eje in EJES}
        for nombre, datos in config_interseccion["brazos"].items():
            self._brazos_por_eje[datos["eje"]].append(nombre)
        for eje, brazos in self._brazos_por_eje.items():
            if not brazos:
                raise ValueError(f"El eje '{eje}' no tiene brazos en la configuracion.")

        self._cortes_cola = list(config_agente["estado"]["cortes_cola_relativa"])
        self._cortes_tiempo = list(config_agente["estado"]["cortes_tiempo_verde_s"])
        for cortes in (self._cortes_cola, self._cortes_tiempo):
            if cortes != sorted(cortes):
                raise ValueError(f"Los cortes deben estar en orden creciente: {cortes}")

        self.niveles_cola = len(self._cortes_cola) + 1
        self.niveles_tiempo = len(self._cortes_tiempo) + 1
        self.numero_estados = self.niveles_cola * self.niveles_cola * len(EJES) * self.niveles_tiempo

    def cola_eje(self, estado_trafico, eje):
        return max(estado_trafico.brazos[b].cola_relativa for b in self._brazos_por_eje[eje])

    def componentes(self, estado_trafico, eje_en_verde, tiempo_en_verde):
        return (
            nivel(self.cola_eje(estado_trafico, "cra23"), self._cortes_cola),
            nivel(self.cola_eje(estado_trafico, "dg15"), self._cortes_cola),
            EJES.index(eje_en_verde),
            nivel(tiempo_en_verde, self._cortes_tiempo),
        )

    def indice(self, componentes):
        cola_cra, cola_dg, eje, tiempo = componentes
        return ((cola_cra * self.niveles_cola + cola_dg) * len(EJES) + eje) * self.niveles_tiempo + tiempo

    def codificar(self, estado_trafico, eje_en_verde, tiempo_en_verde):
        return self.indice(self.componentes(estado_trafico, eje_en_verde, tiempo_en_verde))

    def describir(self, indice):
        """Texto legible de un estado (para mostrar la tabla aprendida)."""
        tiempo = indice % self.niveles_tiempo
        resto = indice // self.niveles_tiempo
        eje = resto % len(EJES)
        resto //= len(EJES)
        cola_dg = resto % self.niveles_cola
        cola_cra = resto // self.niveles_cola
        nombres_cola = ["vacia", "baja", "media", "alta"] if self.niveles_cola == 4 else [str(i) for i in range(self.niveles_cola)]
        return (f"cola Cra23={nombres_cola[cola_cra]}, cola Dg15={nombres_cola[cola_dg]}, "
                f"verde={EJES[eje]}, tiempo_verde=nivel {tiempo}")
