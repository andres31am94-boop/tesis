"""
SafetyGuard: maquina de fases SEGURA del semaforo.

Es la unica pieza que decide QUE luces se encienden. Los controladores (tiempos fijos
o agente) solo PIDEN "cambiar" o "mantener"; el SafetyGuard decide si se puede:

    verde(eje A) --> amarillo(eje A) --> todo_rojo --> verde(eje B) --> ...

Reglas que nunca se rompen:
  1. Un verde no termina antes de verde_min (se ignora la peticion de cambio).
  2. Un verde termina obligatoriamente al llegar a verde_max.
  3. Amarillo y todo-rojo se cumplen completos, siempre.
  4. Nunca hay dos ejes en verde: el orden de etapas es fijo.

No usa TraCI: es logica pura, por eso se puede probar sin SUMO (tests/test_safety_guard.py)
y servira igual para el ESP32 de la maqueta.
"""

EJES = ("cra23", "dg15")
VERDE, AMARILLO, TODO_ROJO = "verde", "amarillo", "todo_rojo"


class SafetyGuard:
    def __init__(self, verde_min_s, verde_max_s, amarillo_s, todo_rojo_s, eje_inicial="dg15"):
        if not (0 < verde_min_s <= verde_max_s):
            raise ValueError(f"Se requiere 0 < verde_min ({verde_min_s}) <= verde_max ({verde_max_s})")
        if amarillo_s <= 0:
            raise ValueError(f"El amarillo debe ser mayor que 0 (recibido {amarillo_s})")
        if todo_rojo_s < 0:
            raise ValueError(f"El todo-rojo no puede ser negativo (recibido {todo_rojo_s})")
        if eje_inicial not in EJES:
            raise ValueError(f"Eje inicial desconocido: {eje_inicial}. Validos: {EJES}")

        self.verde_min_s = verde_min_s
        self.verde_max_s = verde_max_s
        self.amarillo_s = amarillo_s
        self.todo_rojo_s = todo_rojo_s

        self._eje = eje_inicial          # eje en verde, o el que acaba de tenerlo (en amarillo/todo-rojo)
        self._etapa = VERDE
        self._inicio_etapa = None        # se fija en iniciar()

        # Registro para metricas y para la tesis
        self.historial_verdes = []       # lista de (eje, inicio_s, duracion_s)
        self.cambios_rechazados = 0      # peticiones de cambio antes de verde_min
        self.cambios_forzados = 0        # verdes cortados por llegar a verde_max

    @classmethod
    def desde_config(cls, config_controlador):
        s = config_controlador["seguridad"]
        return cls(s["verde_min_s"], s["verde_max_s"], s["amarillo_s"], s["todo_rojo_s"], s["eje_inicial"])

    # --- consultas -------------------------------------------------------------
    @property
    def eje(self):
        return self._eje

    @property
    def etapa(self):
        return self._etapa

    def tiempo_en_etapa(self, tiempo):
        return tiempo - self._inicio_etapa

    def fase_actual(self):
        """Nombre de la fase tal como esta en config/interseccion.yaml (luces)."""
        if self._etapa == TODO_ROJO:
            return "todo_rojo"
        return f"{self._etapa}_{self._eje}"

    # --- operacion -------------------------------------------------------------
    def iniciar(self, tiempo):
        self._inicio_etapa = tiempo
        return self.fase_actual()

    def paso(self, tiempo, pedir_cambio):
        """
        Se llama UNA vez por segundo simulado. Devuelve la fase que debe estar encendida.
        pedir_cambio: True si el controlador quiere terminar el verde actual.
        """
        if self._inicio_etapa is None:
            raise RuntimeError("Llama a iniciar() antes de paso().")
        duracion = self.tiempo_en_etapa(tiempo)

        if self._etapa == VERDE:
            if duracion >= self.verde_max_s:
                if not pedir_cambio:
                    self.cambios_forzados += 1
                self._terminar_verde(tiempo)
            elif pedir_cambio:
                if duracion >= self.verde_min_s:
                    self._terminar_verde(tiempo)
                else:
                    self.cambios_rechazados += 1
        elif self._etapa == AMARILLO:
            if duracion >= self.amarillo_s:
                if self.todo_rojo_s > 0:
                    self._pasar_a(TODO_ROJO, tiempo)
                else:
                    self._iniciar_verde_siguiente(tiempo)
        elif self._etapa == TODO_ROJO:
            if duracion >= self.todo_rojo_s:
                self._iniciar_verde_siguiente(tiempo)

        return self.fase_actual()

    # --- transiciones internas -------------------------------------------------
    def _pasar_a(self, etapa, tiempo):
        self._etapa = etapa
        self._inicio_etapa = tiempo

    def _terminar_verde(self, tiempo):
        self.historial_verdes.append((self._eje, self._inicio_etapa, tiempo - self._inicio_etapa))
        self._pasar_a(AMARILLO, tiempo)

    def _iniciar_verde_siguiente(self, tiempo):
        self._eje = EJES[1] if self._eje == EJES[0] else EJES[0]
        self._pasar_a(VERDE, tiempo)
