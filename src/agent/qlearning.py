"""
Tabla Q y regla de aprendizaje Q-Learning (Watkins y Dayan, 1992; Sutton y Barto, 2018).

    Q(s,a) <- Q(s,a) + alfa * [ r + gamma * max_a' Q(s',a') - Q(s,a) ]

Descuento (aprendizaje.descuento en config/agente.yaml):
  "por_decision" (iteraciones 1-4): gamma se aplica una vez por decision, dure lo que dure el paso.
  "por_segundo"  (iteracion 4b, formulacion semi-Markov; Bradtke y Duff, 1995): los pasos duran distinto (mantener 5 s;
      cambiar desde la Dg 15 = 3 s amarillo + 20 s todo-rojo + 15 s verde minimo = 38 s). La recompensa del paso se
      descuenta segundo a segundo, r = sum_t gamma^t * r_t, y el futuro se descuenta gamma^(segundos del paso):
          Q(s,a) <- Q(s,a) + alfa * [ r + gamma^d * max_a' Q(s',a') - Q(s,a) ]
      Asi un paso largo no se cobra "de golpe" frente a varios pasos cortos que cubren el mismo tiempo.

Acciones: 0 = MANTENER el verde actual, 1 = CAMBIAR (pedirlo al SafetyGuard).
Sin dependencias externas: la tabla es pequena (estados x 2) y se guarda en JSON.
"""
import json
import os
import random

MANTENER, CAMBIAR = 0, 1
DESCUENTOS = ("por_decision", "por_segundo")
ACCIONES = (MANTENER, CAMBIAR)
NOMBRES_ACCIONES = {MANTENER: "mantener", CAMBIAR: "cambiar"}


def suma_descontada(valores_por_segundo, gamma):
    """sum_t gamma^t * valor_t (t = 0, 1, ...): recompensa de un paso con descuento por segundo."""
    return sum(valor * gamma ** t for t, valor in enumerate(valores_por_segundo))


def epsilon_lineal(episodio, inicial, final, episodios_decaimiento):
    """Epsilon baja en linea recta de 'inicial' a 'final' y luego se queda en 'final'."""
    if episodio >= episodios_decaimiento:
        return final
    return inicial + (final - inicial) * episodio / episodios_decaimiento


class TablaQ:
    def __init__(self, numero_estados, alfa, gamma, semilla=0, descuento="por_decision"):
        if not (0 < alfa <= 1) or not (0 <= gamma < 1):
            raise ValueError(f"Se requiere 0 < alfa <= 1 y 0 <= gamma < 1 (alfa={alfa}, gamma={gamma})")
        if descuento not in DESCUENTOS:
            raise ValueError(f"descuento debe ser uno de {DESCUENTOS} (recibido {descuento})")
        self.numero_estados = numero_estados
        self.alfa = alfa
        self.gamma = gamma
        self.descuento = descuento
        self.q = [[0.0 for _ in ACCIONES] for _ in range(numero_estados)]
        self.visitas = [[0 for _ in ACCIONES] for _ in range(numero_estados)]
        self._azar = random.Random(semilla)

    def reiniciar_azar(self, semilla):
        """Fija el generador de azar (exploracion y desempates). El entrenamiento lo llama al inicio de cada
        episodio con una semilla propia del episodio: asi entrenar de seguido o por paquetes da lo mismo."""
        self._azar = random.Random(semilla)

    def mejor_accion(self, estado):
        valores = self.q[estado]
        mejor = max(valores)
        empatadas = [a for a in ACCIONES if valores[a] == mejor]
        return self._azar.choice(empatadas)  # desempate al azar (evita sesgo hacia una accion)

    def elegir_accion(self, estado, epsilon):
        """epsilon-greedy: con probabilidad epsilon explora (accion al azar), si no explota."""
        if self._azar.random() < epsilon:
            return self._azar.choice(ACCIONES)
        return self.mejor_accion(estado)

    def factor_futuro(self, segundos):
        """Cuanto pesa el valor del estado siguiente: gamma (por decision) o gamma^segundos (por segundo)."""
        if self.descuento == "por_segundo":
            if segundos < 1:
                raise ValueError(f"Un paso dura al menos 1 s (recibido {segundos})")
            return self.gamma ** segundos
        return self.gamma

    def actualizar(self, estado, accion, recompensa, estado_siguiente, terminal, segundos=1, accion_siguiente=None):
        """segundos = duracion del paso; solo se usa con descuento "por_segundo".
        accion_siguiente: si se da, el futuro se valora con Q(s', esa accion) en vez de max_a' Q(s', a'). Se usa en la
        fase "plan" del arranque: alli se quiere el valor de SEGUIR EL PLAN (evaluacion de la politica), y el max
        tomaria la otra accion, que aun vale 0 (nunca probada) y haria parecer el futuro gratis."""
        if accion_siguiente is None:
            futuro = max(self.q[estado_siguiente])
        else:
            futuro = self.q[estado_siguiente][accion_siguiente]
        objetivo = recompensa if terminal else recompensa + self.factor_futuro(segundos) * futuro
        self.q[estado][accion] += self.alfa * (objetivo - self.q[estado][accion])
        self.visitas[estado][accion] += 1

    def iniciar_desde_plan(self, acciones_plan, margen):
        """Arranque desde el semaforo real (iteracion 4b). Tras unos episodios en que el agente SIGUE el plan fijo (y
        aprende el valor de esas acciones), la otra accion de cada estado se iguala a la del plan con un pequeno
        castigo: Q(s, otra) = Q(s, plan) * (1 + margen). Asi la politica inicial es exactamente el plan real y el
        agente solo se aparta de el cuando la experiencia muestra que la otra accion es mejor.
        Estados nunca visitados: Q(s, plan) = 0 y Q(s, otra) = -1 (desempate a favor del plan)."""
        if len(acciones_plan) != self.numero_estados:
            raise ValueError("Se necesita una accion del plan por estado.")
        if margen < 0:
            raise ValueError(f"El margen no puede ser negativo (recibido {margen})")
        for estado, plan in enumerate(acciones_plan):
            otra = 1 - plan
            if self.visitas[estado][plan] > 0:
                self.q[estado][otra] = self.q[estado][plan] * (1 + margen) - 1e-9  # siempre estrictamente peor
            else:
                self.q[estado][plan], self.q[estado][otra] = 0.0, -1.0

    def guardar(self, ruta, metadatos=None):
        datos = {"alfa": self.alfa, "gamma": self.gamma, "descuento": self.descuento, "q": self.q,
                 "visitas": self.visitas, "metadatos": metadatos or {}}
        # Se escribe primero en un archivo temporal y luego se reemplaza: si el programa se corta a mitad de la
        # escritura, la tabla anterior queda intacta (nunca un archivo a medio escribir).
        ruta_temporal = f"{ruta}.tmp"
        with open(ruta_temporal, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=1)
        os.replace(ruta_temporal, ruta)

    @classmethod
    def cargar(cls, ruta):
        with open(ruta, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        # los modelos anteriores a la iteracion 4b no guardaban "descuento": eran por decision
        tabla = cls(len(datos["q"]), datos["alfa"], datos["gamma"], descuento=datos.get("descuento", "por_decision"))
        tabla.q = datos["q"]
        tabla.visitas = datos["visitas"]
        tabla.metadatos = datos.get("metadatos", {})
        return tabla
