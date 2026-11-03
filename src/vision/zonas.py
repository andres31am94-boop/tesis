"""
Fase 8: convierte las detecciones con identidad (YOLO + tracking) en el ESTADO DEL TRAFICO que usa el agente.

Entrada (cada cuadro de video): lista de vehiculos seguidos (id del tracker, caja x1, y1, x2, y2 en pixeles).
Salida: EstadoTrafico, el mismo "idioma comun" que produce SumoSource, con, por cada brazo:
  vehiculos_zona  = vehiculos cuyo punto de referencia esta dentro del poligono de la zona de camara del brazo
  detenidos_zona  = de esos, los que llevan "quietos" al menos `ventana_detenido_s` segundos
                    (su punto se movio menos de `umbral_movimiento` en esa ventana)
Asi el agente recibe lo mismo que en SUMO, sin saber si los datos vienen de la simulacion o de la camara.

Decisiones (a validar con la maqueta):
  - Las zonas se definen en coordenadas NORMALIZADAS (0 a 1 respecto al ancho y alto de la imagen), para que no
    dependan de la resolucion de la camara.
  - Punto de referencia de un vehiculo: el CENTRO de su caja (con camara cenital es donde esta el carro; con
    camara inclinada se podria usar el centro del borde inferior: parametro `punto_referencia`).
  - "Detenido" se mide con el desplazamiento del punto en una ventana de tiempo, no con la velocidad instantanea,
    porque la caja de YOLO "tiembla" algunos pixeles aunque el carro este quieto.
  - En la maqueta no existen "brazo completo" ni "aguas arriba": vehiculos/detenidos del brazo = los de la zona, y
    detenidos_aguas_arriba = None (solo se usaba en la recompensa del entrenamiento, no para decidir).
"""
from collections import deque
from dataclasses import dataclass, field

from src.common.estado import EstadoBrazo, EstadoTrafico


def punto_en_poligono(x, y, poligono):
    """Algoritmo de rayo (ray casting): cuenta cuantas veces una semirrecta horizontal desde (x, y) cruza los
    lados del poligono; si es impar, el punto esta dentro. Poligono = lista de (x, y) en orden."""
    dentro = False
    cantidad = len(poligono)
    for i in range(cantidad):
        x1, y1 = poligono[i]
        x2, y2 = poligono[(i + 1) % cantidad]
        if (y1 > y) != (y2 > y):
            x_cruce = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_cruce:
                dentro = not dentro
    return dentro


@dataclass(frozen=True)
class VehiculoSeguido:
    id_seguimiento: int
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class _Historial:
    posiciones: deque = field(default_factory=deque)   # (tiempo_s, x_norm, y_norm)


class ContadorZonas:
    def __init__(self, zonas, ventana_detenido_s=1.0, umbral_movimiento=0.01, punto_referencia="centro",
                 olvidar_tras_s=2.0):
        """
        zonas: {nombre_brazo: [(x, y), ...]} poligonos en coordenadas normalizadas (0-1).
        ventana_detenido_s: segundos que debe estar quieto para contar como detenido.
        umbral_movimiento: desplazamiento maximo (normalizado, fraccion del lado mayor de la imagen) en la ventana.
        olvidar_tras_s: se borra el historial de un id que no aparece hace mas de este tiempo.
        """
        if not zonas:
            raise ValueError("Se necesita al menos una zona")
        for nombre, poligono in zonas.items():
            if len(poligono) < 3:
                raise ValueError(f"La zona '{nombre}' necesita al menos 3 vertices")
            for x, y in poligono:
                if not (0 <= x <= 1 and 0 <= y <= 1):
                    raise ValueError(f"La zona '{nombre}' tiene un vertice fuera de 0-1: ({x}, {y})")
        if punto_referencia not in ("centro", "base"):
            raise ValueError("punto_referencia debe ser 'centro' o 'base'")
        if ventana_detenido_s <= 0 or umbral_movimiento <= 0:
            raise ValueError("ventana_detenido_s y umbral_movimiento deben ser positivos")
        self._zonas = {nombre: list(poligono) for nombre, poligono in zonas.items()}
        self._ventana = ventana_detenido_s
        self._umbral = umbral_movimiento
        self._punto = punto_referencia
        self._olvidar = olvidar_tras_s
        self._historiales = {}

    def _referencia_normalizada(self, vehiculo, ancho, alto):
        x = (vehiculo.x1 + vehiculo.x2) / 2
        y = (vehiculo.y1 + vehiculo.y2) / 2 if self._punto == "centro" else vehiculo.y2
        return x / ancho, y / alto

    def _esta_detenido(self, historial, tiempo, escala_x, escala_y):
        """Quieto si cubre al menos la ventana y ningun punto de la ventana se aleja mas del umbral del actual."""
        posiciones = historial.posiciones
        if not posiciones or tiempo - posiciones[0][0] < self._ventana:
            return False
        _, x_actual, y_actual = posiciones[-1]
        for t, x, y in posiciones:
            if tiempo - t > self._ventana:
                continue
            distancia = (((x - x_actual) * escala_x) ** 2 + ((y - y_actual) * escala_y) ** 2) ** 0.5
            if distancia > self._umbral:
                return False
        return True

    def actualizar(self, tiempo, vehiculos, ancho, alto):
        """tiempo en segundos; vehiculos: lista de VehiculoSeguido; ancho/alto de la imagen en pixeles.
        Devuelve EstadoTrafico con vehiculos_zona y detenidos_zona por brazo."""
        # La distancia se mide relativa al lado mayor, para que "1 %" signifique lo mismo en x y en y.
        lado_mayor = max(ancho, alto)
        escala_x, escala_y = ancho / lado_mayor, alto / lado_mayor
        conteo = {nombre: [0, 0] for nombre in self._zonas}
        vistos = set()
        for vehiculo in vehiculos:
            x, y = self._referencia_normalizada(vehiculo, ancho, alto)
            historial = self._historiales.setdefault(vehiculo.id_seguimiento, _Historial())
            historial.posiciones.append((tiempo, x, y))
            while historial.posiciones and tiempo - historial.posiciones[0][0] > self._ventana + 1.0:
                historial.posiciones.popleft()
            vistos.add(vehiculo.id_seguimiento)
            for nombre, poligono in self._zonas.items():
                if punto_en_poligono(x, y, poligono):
                    conteo[nombre][0] += 1
                    if self._esta_detenido(historial, tiempo, escala_x, escala_y):
                        conteo[nombre][1] += 1
                    break   # un vehiculo cuenta en una sola zona
        for id_seguimiento in list(self._historiales):
            ultima = self._historiales[id_seguimiento].posiciones
            if id_seguimiento not in vistos and (not ultima or tiempo - ultima[-1][0] > self._olvidar):
                del self._historiales[id_seguimiento]

        brazos = {nombre: EstadoBrazo(vehiculos=presentes, detenidos=detenidos, cola_relativa=0.0,
                                      vehiculos_zona=presentes, detenidos_zona=detenidos,
                                      detenidos_aguas_arriba=None)
                  for nombre, (presentes, detenidos) in conteo.items()}
        return EstadoTrafico(tiempo=tiempo, brazos=brazos)
