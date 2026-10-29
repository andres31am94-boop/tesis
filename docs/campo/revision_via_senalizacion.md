# Revisión de la vía y la señalización del modelo (Cra 23 × Dg 15, Acacías)

Fecha: 2026-10-25. Antes de entrenar la iteración 3 se revisa, elemento por elemento, qué representa el modelo de SUMO y de
dónde sale cada dato. Estado: ✔ medido u observado · ≈ aproximado o supuesto declarado · ❓ por confirmar en campo.
Respondan los ❓ debajo de cada pregunta al final (`R:`).

## 1. Geometría y carriles

| Elemento | En el modelo | Fuente | Estado |
|---|---|---|---|
| Llegada norte (desde Villavicencio) | Puente de 1 carril (59.6 m) + 2 carriles junto al semáforo (41.4 m); ancho 3.5 m | Respuestas de campo, foto satelital, OSM | ✔ / ≈ (punto de cambio de carriles: 53.8 m, sensibilidad hecha) |
| Salida hacia Villavicencio | 2 carriles (41.4 m) → se juntan alternándose → puente de 1 carril → Calle 18 | Campo + OSM | ✔ / ≈ |
| Llegada sur (desde Acacías) | 2 carriles, 187.6 m, 3.5 m, calzada separada | Campo (Street View, fotos), satélite | ✔ |
| Salida hacia Acacías | 2 carriles, 107 m (termina en el borde de la red) | OSM | ✔ |
| Llegada este (Dg 15) | 2 carriles, 329 m, **3.2 m (valor por defecto de SUMO)** | OSM | ❓ ancho |
| Llegada oeste (Dg 15) | 2 carriles, 227 m, **3.2 m (por defecto)** | OSM | ❓ ancho |
| Dg 15: carriles | 2 por sentido, aunque **no hay líneas de carril** | Respuesta de campo ("caben 2 lado a lado") | ≈ |
| Tramos de acceso | 500 m antes de cada brazo (para que la cola se forme dentro de la red) | Decisión de modelación | ≈ (declarado) |
| Pendiente del puente | **No se modela** (SUMO plano) | — | ❓ |

## 2. Movimientos permitidos

| Elemento | En el modelo | Fuente | Estado |
|---|---|---|---|
| Giro a la izquierda | Prohibido en los 4 brazos | Observación de los autores | ✔ observado / ❓ ¿hay señal de prohibición? |
| Giro a la derecha | Permitido en los 4 brazos, solo con verde | Observación | ✔ |
| Giro a la derecha en rojo | **No** se modela (la Ley 769, art. 118, lo permite salvo señal) | Observación: no se hace | ❓ ¿hay señal? |
| Vuelta en U | Prohibida | Observación | ✔ |
| Carriles de la llegada sur | Izquierdo: recto (tiene flecha de giro izquierdo pintada, pero no se gira); derecho: recto y derecha | Street View + observación | ✔ |
| Llegada norte | Carril derecho: recto y derecha; izquierdo: recto | Supuesto | ≈ |

## 3. Semáforos

| Elemento | En el modelo | Fuente | Estado |
|---|---|---|---|
| Fases | 2: Cra 23 / Dg 15 (sin flechas) | Observación | ✔ |
| Semáforo real | Cra 23: verde 55, amarillo 3, todo-rojo 0 · Dg 15: verde 20, amarillo 3, todo-rojo 20 · ciclo 101 s | Medido (varios días y horas) | ✔ (ciclo medido 100–103 s) |
| Agente: verde mínimo / máximo | 15 s / 60 s | Manual 2004 (15 s); diseño (60 s) | ≈ |
| Agente: todo-rojo tras la Cra 23 | 2 s (tiempo de seguridad del Manual 2024, 4.4.4) | Estimación propia con la fórmula | ≈ |
| Semáforo de la Calle 18 (~260 m al norte) | Fijo: verde 58, amarillo 3, rojo 41; misma luz para los dos sentidos; desfase al azar por semilla | Medido (jueves 22) | ✔ tiempos / ≈ desfase / ❓ tráfico de la Calle 18 |
| Peatones | **No se modelan**; cruzan en el todo-rojo de 20 s | Observación | ≈ (declarado) |

## 4. Velocidad, operación y otros

| Elemento | En el modelo | Fuente | Estado |
|---|---|---|---|
| Velocidad máxima | 50 km/h en todas las vías | Ley 2251 de 2022 (urbana) | ❓ ¿hay señales de 30 km/h o resaltos cerca (hospital, colegio)? |
| Paraderos de bus | No hay | Campo | ✔ |
| Carros estacionados | No hay | Campo | ✔ |
| Motos | Avanzan entre vehículos detenidos hasta la línea de pare | Campo + interpretación del art. 94 | ≈ (declarado) |
| Vehículos | Carro, moto (Boxer 2.0 × 0.75 m), bus (12 m), camión (7.1 m) | Ficha del fabricante, SUMO | ≈ (bus y camión: valores de SUMO) |
| Otras restricciones aguas abajo en la Dg 15 | Ninguna (las salidas terminan a 225–326 m) | — | ❓ |

## 5. Preguntas para los autores (❓)

1. **Ancho de la Dg 15:** en Google Maps, ancho de cada calzada (este y oeste) cerca del cruce.
   R (2026-10-25): el mismo que los carriles de la Cra 23 → 3.5 m (aplicado en ajustes.edg.xml).
2. **Pendiente del puente:** ¿se nota subida o bajada? ¿Los camiones y buses arrancan más despacio ahí?
   R (2026-10-25): de Villavicencio hacia Acacías hay una subida, no drástica pero notoria → no se modela (SUMO plano; el modelo Krauss no usa la pendiente). Limitación declarada; la calibración con el aforo absorbe en parte su efecto.
3. **Señal de prohibido girar a la izquierda:** ¿existe en algún brazo, o solo es costumbre?
   R (2026-10-25): prohibido → coincide con el modelo.
4. **Giro a la derecha en rojo:** ¿hay alguna señal que lo prohíba o lo permita? ¿Alguien lo hace?
   R (2026-10-25): prohibido → coincide con el modelo (no se modela).
5. **Velocidad:** ¿hay señales de 30 km/h, zona escolar, zona de hospital o resaltos (policías acostados) cerca del cruce?
   R (2026-10-25): no hay señales → 50 km/h (Ley 2251 de 2022) se mantiene.
6. **Dg 15 hacia el este y el oeste:** ¿hay otro semáforo, glorieta o cuello de botella a menos de ~400 m que haga devolver la cola?
   R (2026-10-25): no → sin restricciones aguas abajo en la Dg 15.
7. **Calle 18:** ¿pasa mucho tráfico por la Calle 18, cruzando la Cra 23? (en el modelo no hay tráfico transversal)
   R (2026-10-25): no mucho tráfico cruzando → se mantiene sin tráfico transversal (supuesto declarado).
8. **Llegada norte, junto al semáforo:** ¿los que giran a la derecha (hacia la Dg 15) usan el lado derecho, y los que siguen recto cualquiera de los dos?
   R (2026-10-25): sí → coincide con el modelo (carril derecho: derecha y recto).
