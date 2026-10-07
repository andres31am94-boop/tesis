"""
Controlador de TIEMPOS FIJOS (baseline / sistema convencional).

Pide cambiar cuando el verde del eje actual alcanza su duracion fija.
No mira el trafico: asi funcionan hoy la mayoria de semaforos.
Usa el mismo SafetyGuard que usara el agente, para que la comparacion sea justa.
"""
from src.controller.safety_guard import EJES, VERDE


class ControladorTiemposFijos:
    nombre = "tiempos_fijos"

    def __init__(self, verdes_s, guard):
        for eje in EJES:
            if eje not in verdes_s:
                raise KeyError(f"Falta el verde fijo del eje '{eje}'")
            if not (guard.verde_min_s <= verdes_s[eje] <= guard.verde_max_s):
                raise ValueError(
                    f"El verde fijo de {eje} ({verdes_s[eje]} s) esta fuera de los limites de "
                    f"seguridad [{guard.verde_min_s}, {guard.verde_max_s}]"
                )
        self._verdes = dict(verdes_s)
        self._guard = guard

    @classmethod
    def desde_config(cls, config_controlador, guard):
        return cls(config_controlador["tiempos_fijos"]["verde_s"], guard)

    def pedir_cambio(self, tiempo, estado_trafico=None):
        """estado_trafico se ignora a proposito: este controlador no observa el trafico."""
        if self._guard.etapa != VERDE:
            return False
        return self._guard.tiempo_en_etapa(tiempo) >= self._verdes[self._guard.eje]
