# Lista de componentes de la parte física (maqueta)

Versión 2026-10-21. Criterio: lo mínimo necesario. No se agrega hardware sin una función clara.

## Ya disponible
| Componente | Uso |
|---|---|
| ESP32 | Controlador de los semáforos: recibe la fase desde Python por USB (serial) y enciende los LEDs |
| Arduino UNO | No es necesario. Queda de respaldo (por ejemplo, si el ESP32 se daña) |
| iPhone 14 (DroidCam por USB) | Cámara para las pruebas de YOLO |
| PC | Corre YOLO, el agente y la comunicación con el ESP32 |

## Comprar AHORA (barato; no depende de ninguna prueba)
| # | Componente | Cantidad | Por qué |
|---|---|---|---|
| 1 | Módulo semáforo LED (rojo, amarillo, verde, con resistencias incluidas) | 4 + 1 de repuesto | Un semáforo por brazo. Ya trae resistencias y parece un semáforo |
| 1b | *Alternativa a 1:* LEDs de 5 mm rojo, amarillo y verde, más resistencias de 220 Ω | 6 de cada color + 15 resistencias | Si no consiguen los módulos |
| 2 | Protoboard de 830 puntos | 1 | Conexiones sin soldar |
| 3 | Cables Dupont macho-hembra **de 30 cm** | 1 paquete (40) | Llevar las señales del ESP32 a los semáforos de las esquinas |
| 4 | Cables Dupont macho-macho | 1 paquete (40) | Conexiones en la protoboard |
| 5 | Cable USB **de datos** para el ESP32 (micro-USB o USB-C, según la placa) | 1 | Alimentación y comunicación con el PC; algunos cables solo cargan |
| 6 | Multímetro básico (opcional) | 1 | Diagnosticar conexiones; útil, no obligatorio |

No hace falta fuente de alimentación aparte: 12 LEDs consumen poco y el ESP32 se alimenta por el USB del PC.

## Comprar DESPUÉS de probar YOLO con carritos que ya tengan en casa
| # | Componente | Cantidad | Por qué |
|---|---|---|---|
| 7 | Carritos a control remoto de aspecto **realista** (escala parecida entre ellos, ~1:43 a 1:24) | 4 a 6 | Vehículos que se mueven; los manejan personas que respetan el semáforo de la maqueta. El aspecto realista ayuda a que YOLO los reconozca |
| 8 | Webcam USB 1080p | 1 | Cámara fija para la maqueta final y la sustentación (el iPhone queda de respaldo) |

## Maqueta
| # | Material | Cantidad | Por qué |
|---|---|---|---|
| 9 | Tablero de MDF o triplex (~100 × 100 cm; el tamaño final depende de los carritos) | 1 | Base de la intersección |
| 10 | Pintura gris u oscura mate, pintura o cinta blanca para líneas | 1 de cada uno | Vías y demarcación; lo mate evita reflejos en la cámara |
| 11 | Soporte de cámara cenital: trípode con brazo, o tubos de PVC con abrazadera | 1 | La cámara va arriba, mirando hacia abajo, viendo los 4 brazos |
| 12 | Lámpara LED de luz blanca uniforme | 1 o 2 | Luz pareja y sin sombras fuertes; mejora la detección y la hace repetible |

## Por qué en ese orden
El riesgo principal de la parte física es que YOLO no reconozca carros de juguete (riesgo R3 de la Fase 0).
Antes de comprar los carritos y la webcam, se prueba YOLO con el iPhone y carritos que ya tengan.
Si los detecta bien, se compran carritos parecidos. Si no, se decide entre otros carritos o reentrenar YOLO con fotos propias.
