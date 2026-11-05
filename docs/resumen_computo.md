# Escala experimental (generado por scripts/resumen_computo.py)

Computo MEDIDO = duracion registrada por los scripts. Computo ESTIMADO = solo para corridas sin registro: cantidad de corridas x promedio medido por corrida en su mismo grupo (se indica en la tabla).

| Grupo | Carpeta | Horas simuladas | Computo medido (h) | Corridas medidas | Estimado sin registro (h) |
|---|---|---|---|---|---|
| Calibracion | barrido_4b | 16 | 0.0 | 0 de 16 | 0.4 |
| Calibracion | barrido_conductor | 12 | 0.0 | 0 de 12 | 0.3 |
| Calibracion | barrido_red | 12 | 0.0 | 0 de 12 | 0.3 |
| Calibracion | validacion_calle18 | 25 | 0.0 | 0 de 25 | 0.6 |
| Calibracion | validacion_conductor | 40 | 0.0 | 0 de 40 | 1.0 |
| Calibracion | validacion_desatasco | 25 | 0.4 | 25 de 25 | - |
| Calibracion | validacion_dg15 | 25 | 0.0 | 0 de 25 | 0.6 |
| Calibracion | validacion_jueves | 5 | 0.0 | 0 de 5 | 0.1 |
| Calibracion | validacion_puente | 25 | 0.0 | 0 de 25 | 0.6 |
| Calibracion | validacion_sin_calle18 | 25 | 0.9 | 25 de 25 | - |
| Calibracion | validacion_sin_empuje | 25 | 0.6 | 25 de 25 | - |
| Calibracion | validacion_transicion | 25 | 0.0 | 0 de 25 | 0.6 |
| Comparacion | aforo_v2 | 450 | 0.0 | 0 de 450 | 3.2 |
| Comparacion | aforo_v3 | 450 | 0.0 | 0 de 450 | 3.2 |
| Comparacion | aforo_v4_validacion | 150 | 0.0 | 0 de 150 | 1.1 |
| Comparacion | aforo_v5_validacion | 100 | 0.0 | 0 de 100 | 0.7 |
| Comparacion | aforo_v6_validacion | 100 | 1.3 | 100 de 100 | - |
| Comparacion | aforo_v7_validacion | 100 | 0.6 | 100 de 100 | - |
| Comparacion | aforo_v8_validacion | 100 | 0.4 | 100 de 100 | - |
| Comparacion | aforo_v8_validacion_desb | 40 | 0.2 | 40 de 40 | - |
| Comparacion | aforo_v9_validacion | 180 | 0.9 | 180 de 180 | - |
| Comparacion | evaluacion_final | 600 | 4.6 | 600 de 600 | - |
| Comparacion | prueba_6semillas_aforo_v2 | 18 | 0.0 | 0 de 18 | 0.1 |
| Entrenamiento | aforo_v5_gamma095_norma | 13 | 0.3 | 13 de 13 | - |
| Entrenamiento | aforo_v2 | 240 | 3.7 | 240 de 240 | - |
| Entrenamiento | aforo_v3 | 240 | 3.4 | 240 de 240 | - |
| Entrenamiento | aforo_v4 | 240 | 2.2 | 240 de 240 | - |
| Entrenamiento | aforo_v5 | 240 | 3.3 | 240 de 240 | - |
| Entrenamiento | aforo_v6 | 320 | 3.4 | 320 de 320 | - |
| Entrenamiento | aforo_v7 | 320 | 2.1 | 320 de 320 | - |
| Entrenamiento | aforo_v8 | 320 | 1.9 | 320 de 320 | - |
| Entrenamiento | aforo_v9 | 640 | 3.6 | 640 de 640 | - |
| Entrenamiento | prueba_200 | 200 | 0.6 | 200 de 200 | - |
| Entrenamiento | prueba_aforo | 4 | 0.2 | 4 de 4 | - |
| Entrenamiento | prueba_aforo_rapida | 4 | 0.1 | 4 de 4 | - |
| Entrenamiento | prueba_corta | 3 | 0.0 | 3 de 3 | - |
| Entrenamiento | prueba_paquetes | 4 | 0.1 | 4 de 4 | - |
| Entrenamiento | prueba_paquetes2 | 4 | 0.1 | 4 de 4 | - |
| Entrenamiento | prueba_seguido | 4 | 0.1 | 4 de 4 | - |
| Entrenamiento | prueba_seguido2 | 4 | 0.1 | 4 de 4 | - |
| Corridas sueltas | results/<escenario>/... (10 escenarios) | 20 | 0.0 | 0 de 20 | 0.1 |

**Total: 5368 horas de trafico simuladas** (= 224 dias continuos).
Computo de simulacion: **35.2 h medidas** + **~13.3 h estimadas** (1373 corridas sin registro, anteriores a que se guardara la duracion; promedio medido por corrida: Calibracion 93 s, Comparacion 26 s, Entrenamiento 32 s).

## Vision, hardware y maqueta

| Tipo | Carpeta | Detalle | Computo medido (h) |
|---|---|---|---|
| Entrenamiento YOLO (CPU) | hotwheels_v1 | 8 epocas, fraccion 0.2 | 6.3 |
| Entrenamiento YOLO (CPU) | hotwheels_v2 | 10 epocas, fraccion 1.0 | 2.7 |
| Entrenamiento YOLO (CPU) | prueba_tiempo-2 | 1 epocas, fraccion 0.05 | 0.3 |
| Hardware en el lazo (tiempo real) | aforo_alto_qlearning_aforo_v8_s1_t900-1200 | ESP32 + SUMO | 0.08 |
| Hardware en el lazo (tiempo real) | aforo_alto_tiempos_fijos_s1_t900-1200 | ESP32 + SUMO | 0.08 |
| Lazo de la maqueta | 20261105_160449_qlearning | 120 s de video, 10.67 cuadros/s | - |

Computo medido en vision y hardware: 9.5 h. No incluye evaluaciones cortas de YOLO, etiquetado manual en Label Studio ni pruebas sin registro de duracion.
Estimado de lo no registrado en vision (antes del 2026-11-05): ~1 h (unas 15 evaluaciones de YOLO de 1-3 min, pruebas de tracking y conteo de 1-10 min, pre-etiquetado y prueba de alturas; aproximacion de los tutores, no medicion).
El tiempo de trabajo de las personas (campo, aforo, etiquetado, montaje) va en docs/registro_tiempo_dedicado.md.

## Registro de cada ejecucion (desde 2026-11-05, results/registro_computo.csv)

| Script | Ejecuciones | Computo (h) |
|---|---|---|
| analizar_validacion_v9.py | 1 | 0.00 |
| resumen_computo.py | 1 | 0.00 |

Total registrado: 0.00 h en 2 ejecuciones. (Para no contar dos veces, este total NO se suma a las tablas de arriba: las corridas de simulacion y los entrenamientos ya aparecen alli.)
