"""
Tabla Q y regla de aprendizaje Q-Learning (Watkins y Dayan, 1992; Sutton y Barto, 2018).

    Q(s,a) <- Q(s,a) + alfa * [ r + gamma * max_a' Q(s',a') - Q(s,a) ]

Acciones: 0 = MANTENER el verde actual, 1 = CAMBIAR (pedirlo al SafetyGuard).
Sin dependencias externas: la tabla es pequena (estados x 2) y se guarda en JSON.
"""
import json
import os
import random

MANTENER, CAMBIAR = 0, 1
ACCIONES = (MANTENER, CAMBIAR)
NOMBRES_ACCIONES = {MANTENER: "mantener", CAMBIAR: "cambiar"}


def epsilon_lineal(episodio, inicial, final, episodios_decaimiento):
    """Epsilon baja en linea recta de 'inicial' a 'final' y luego se queda en 'final'."""
    if episodio >= episodios_decaimiento:
        return final
    return inicial + (final - inicial) * episodio / episodios_decaimiento


class TablaQ:
    def __init__(self, numero_estados, alfa, gamma, semilla=0):
        if not (0 < alfa <= 1) or not (0 <= gamma < 1):
            raise ValueError(f"Se requiere 0 < alfa <= 1 y 0 <= gamma < 1 (alfa={alfa}, gamma={gamma})")
        self.numero_estados = numero_estados
        self.alfa = alfa
        self.gamma = gamma
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

    def actualizar(self, estado, accion, recompensa, estado_siguiente, terminal):
        objetivo = recompensa if terminal else recompensa + self.gamma * max(self.q[estado_siguiente])
        self.q[estado][accion] += self.alfa * (objetivo - self.q[estado][accion])
        self.visitas[estado][accion] += 1

    def guardar(self, ruta, metadatos=None):
        datos = {"alfa": self.alfa, "gamma": self.gamma, "q": self.q,
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
        tabla = cls(len(datos["q"]), datos["alfa"], datos["gamma"])
        tabla.q = datos["q"]
        tabla.visitas = datos["visitas"]
        tabla.metadatos = datos.get("metadatos", {})
        return tabla
