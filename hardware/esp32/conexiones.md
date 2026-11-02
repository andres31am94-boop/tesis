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
