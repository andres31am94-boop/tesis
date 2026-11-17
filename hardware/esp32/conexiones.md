# Conexiones ESP32 ↔ semáforos de la maqueta

## Hardware
- Placa: ESP32 DevKit de 30 pines (módulo ESP-WROOM-32, USB-C).
- 4 módulos semáforo (pines GND, R, Y, G; cada LED trae su resistencia en el módulo).

## Mapa de pines

| Semáforo | Acceso | R (rojo) | Y (amarillo) | G (verde) |
|---|---|---|---|---|
| S1 | Cra 23 sur | D32 | D33 | D25 |
| S2 | Cra 23 norte | D26 | D27 | D13 |
| S3 | Dg 15 oeste | D23 | D22 | D21 |
| S4 | Dg 15 este | D19 | D18 | D17 (TX2) |

GND de los 4 módulos → riel GND de la protoboard → pin GND del ESP32.
Pines de reserva: D4, D16 (RX2).

**Falla del 2026-11-17 (resuelta):** el amarillo del S3 no prendía. Al intercambiar los cables de D22 y D23 la falla siguió a la posición del D22, lo que hizo pensar en el pin; la causa real fue un cable Dupont con la cabeza (conector) despegada. Se cambió el cable y el amarillo quedó en D22. Lección: antes de culpar un pin, revisar que la cabeza de cada cable esté firme. Diagnóstico con `scripts/probar_semaforos_visual.py` y el programa de taller `prueba_todos_iguales`.

## Colores de los cables de cada módulo (registro real, 2026-11-17)

Los colores no siguen un patrón: cada cable lleva una etiqueta de cinta cerca de la punta del ESP32 ("S1-R", "S1-Y", …).

| Semáforo | R → pin | Y → pin | G → pin | GND |
|---|---|---|---|---|
| S1 | Rojo → D32 | Rosa → D33 | Amarillo → D25 | Café |
| S2 | Gris → D26 | Blanco → D27 | Negro → D13 | Morado |
| S3 | Amarillo → D23 | Verde → D22 | Azul → D21 | Rosa |
| S4 | Gris → D19 | Blanco → D18 | Negro → D17 | Morado |

Cuidado:
- En S2 y S4 el cable **negro** es el verde (G), no GND.
- S2 y S4 usan los mismos colores: si se mezclan sus cables, se cruzan los dos accesos.
- El rosa es Y en S1 y GND en S3.

## Pines que NO se usan y por qué
| Pin | Motivo |
|---|---|
| D34, D35, VP (36), VN (39) | Solo entrada: no pueden encender LEDs. |
| D12 | Pin de arranque: si está en ALTO al encender, la placa no arranca. |
| D2, D15, D5 | Pines de arranque: se evitan por precaución. |
| D14 | Emite pulsos al arrancar (el LED parpadearía). |
| RX0, TX0 | Comunicación USB con el PC (Python los usará en el paso 10.3). |

Fuente: documentación de Espressif sobre pines de arranque (strapping pins) del ESP32.

## Fases
Cra 23 (S1 + S2) y Dg 15 (S3 + S4) funcionan como dos grupos. Nunca pueden estar en verde los dos grupos a la vez: esa regla se programa en el ESP32 (paso 10.4), no solo en Python.
