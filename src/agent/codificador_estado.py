"""
Codificador de estado: convierte lo que observa el sistema (EstadoTrafico + fase)
en un NUMERO de estado para la tabla Q.

Estado = (nivel Cra 23, nivel Dg 15, eje en verde, nivel de tiempo en verde)

Dos modos (config/agente.yaml: estado.modo):
  "detenidos" (iteracion 1): el nivel de cada eje = vehiculos DETENIDOS en la zona de camara.
  "presentes_en_verde" (iteracion 2): el eje en ROJO se describe con sus detenidos (su cola); el eje en VERDE con los
      vehiculos PRESENTES en su zona (moviendose o detenidos), porque durante el verde casi nadie esta detenido y con
      detenidos el agente no podia saber si el verde se estaba aprovechando (como la deteccion de un control actuado).

Cola de un eje = vehiculos DETENIDOS en la zona de camara (ultimos zona_camara_m metros antes de la linea
de pare) del brazo MAS cargado del eje: un promedio con el otro brazo escondería que uno se esta llenando.
Funciona igual con datos de SUMO o de la camara: solo necesita EstadoTrafico.
"""
from bisect import bisect_right

from src.controller.safety_guard import EJES


def nivel(valor, cortes):
    """Indice del intervalo: cortes [2, 6, 12] -> 0->0, 2->1, 7->2, 20->3."""
    return bisect_right(cortes, valor)


class CodificadorEstado:
    def __init__(self, config_interseccion, config_agente):
        self._brazos_por_eje = {eje: [] for eje in EJES}
        for nombre, datos in config_interseccion["brazos"].items():
            self._brazos_por_eje[datos["eje"]].append(nombre)
        for eje, brazos in self._brazos_por_eje.items():
            if not brazos:
                raise ValueError(f"El eje '{eje}' no tiene brazos en la configuracion.")

        self._modo = config_agente["estado"].get("modo", "detenidos")
        if self._modo not in ("detenidos", "presentes_en_verde"):
            raise ValueError(f"Modo de estado desconocido: {self._modo}")
        self._cortes_cola = list(config_agente["estado"]["cortes_detenidos_zona"])
        self._cortes_presentes = (list(config_agente["estado"]["cortes_presentes_zona_verde"])
                                  if self._modo == "presentes_en_verde" else self._cortes_cola)
        if len(self._cortes_presentes) != len(self._cortes_cola):
            raise ValueError("Los cortes de presentes y de detenidos deben dar el mismo numero de niveles.")
        # Cortes del tiempo en verde: una lista (iguales para ambos ejes) o {eje: lista} (iteracion 4b: alineados con
        # el plan del semaforo real, p. ej. Cra 23 [45, 55] y Dg 15 [20, 30]). Todos los ejes con el mismo numero de niveles.
        cortes_tiempo = config_agente["estado"]["cortes_tiempo_verde_s"]
        if not isinstance(cortes_tiempo, dict):
            cortes_tiempo = {eje: cortes_tiempo for eje in EJES}
        if set(cortes_tiempo) != set(EJES):
            raise ValueError(f"cortes_tiempo_verde_s debe definirse para los ejes {EJES}")
        self._cortes_tiempo = {eje: list(cortes) for eje, cortes in cortes_tiempo.items()}
        if len({len(c) for c in self._cortes_tiempo.values()}) != 1:
            raise ValueError("Los cortes de tiempo de cada eje deben dar el mismo numero de niveles.")
        for cortes in (self._cortes_cola, self._cortes_presentes, *self._cortes_tiempo.values()):
            if cortes != sorted(cortes):
                raise ValueError(f"Los cortes deben estar en orden creciente: {cortes}")

        self.niveles_cola = len(self._cortes_cola) + 1
        self.niveles_tiempo = len(self._cortes_tiempo[EJES[0]]) + 1
        self.numero_estados = self.niveles_cola * self.niveles_cola * len(EJES) * self.niveles_tiempo

    def cola_eje(self, estado_trafico, eje):
        return max(estado_trafico.brazos[b].detenidos_zona for b in self._brazos_por_eje[eje])

    def presentes_eje(self, estado_trafico, eje):
        return max(estado_trafico.brazos[b].vehiculos_zona for b in self._brazos_por_eje[eje])

    def nivel_eje(self, estado_trafico, eje, eje_en_verde):
        if self._modo == "presentes_en_verde" and eje == eje_en_verde:
            return nivel(self.presentes_eje(estado_trafico, eje), self._cortes_presentes)
        return nivel(self.cola_eje(estado_trafico, eje), self._cortes_cola)

    def componentes(self, estado_trafico, eje_en_verde, tiempo_en_verde):
        return (
            self.nivel_eje(estado_trafico, "cra23", eje_en_verde),
            self.nivel_eje(estado_trafico, "dg15", eje_en_verde),
            EJES.index(eje_en_verde),
            nivel(tiempo_en_verde, self._cortes_tiempo[eje_en_verde]),
        )

    def nivel_tiempo(self, eje, tiempo_en_verde):
        return nivel(tiempo_en_verde, self._cortes_tiempo[eje])

    def accion_plan(self, indice, verdes_plan_s):
        """Accion del semaforo de tiempos fijos en este estado: CAMBIAR (1) si el nivel de tiempo ya alcanzo el verde
        del plan para el eje en verde, si no MANTENER (0). Exacto si los cortes incluyen el verde del plan."""
        tiempo = indice % self.niveles_tiempo
        eje = EJES[(indice // self.niveles_tiempo) % len(EJES)]
        return 1 if tiempo >= self.nivel_tiempo(eje, verdes_plan_s[eje]) else 0

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
        nombres = {4: ["vacia", "baja", "media", "alta"], 5: ["vacia", "baja", "media", "alta", "muy_alta"]}
        nombres_cola = nombres.get(self.niveles_cola, [str(i) for i in range(self.niveles_cola)])
        return (f"cola Cra23={nombres_cola[cola_cra]}, cola Dg15={nombres_cola[cola_dg]}, "
                f"verde={EJES[eje]}, tiempo_verde=nivel {tiempo}")
