# Estadística de la evaluación final (generado por scripts/graficas_tesis.py)

Modelo `aforo_v8` vs semáforo real; 30 semillas de evaluación (1–30) pareadas por escenario; métrica principal: tiempo de espera promedio por vehículo (s). Prueba principal: Wilcoxon de rangos con signo; tamaño del efecto: r biserial de rangos (−1 = el agente es menor en todos los pares). IC 95 % bootstrap (10 000 remuestreos, semilla 20261029).

## 1. Estadística descriptiva (espera promedio, s)

| Escenario | Controlador | n | Media | DE | Mediana | Q1 | Q3 | Mín | Máx |
|---|---|---|---|---|---|---|---|---|---|
| Bajo | Semáforo real | 30 | 15.39 | 0.48 | 15.59 | 14.94 | 15.74 | 14.52 | 16.16 |
| Bajo | Agente | 30 | 13.49 | 0.50 | 13.49 | 13.14 | 13.68 | 12.69 | 14.65 |
| Valle (no entrenado) | Semáforo real | 30 | 17.75 | 0.47 | 17.76 | 17.41 | 18.16 | 16.79 | 18.77 |
| Valle (no entrenado) | Agente | 30 | 16.04 | 0.40 | 16.01 | 15.80 | 16.20 | 15.39 | 17.10 |
| Medio | Semáforo real | 30 | 19.38 | 0.45 | 19.30 | 19.11 | 19.65 | 18.44 | 20.14 |
| Medio | Agente | 30 | 17.26 | 0.70 | 17.18 | 16.81 | 17.50 | 15.98 | 18.60 |
| Alto (pico) | Semáforo real | 30 | 54.60 | 10.59 | 55.85 | 45.13 | 62.14 | 35.25 | 74.10 |
| Alto (pico) | Agente | 30 | 33.96 | 6.71 | 31.76 | 28.93 | 37.65 | 24.41 | 52.81 |
| Jueves (pico) | Semáforo real | 30 | 23.95 | 2.27 | 23.58 | 22.12 | 24.92 | 21.14 | 31.00 |
| Jueves (pico) | Agente | 30 | 22.65 | 1.51 | 22.32 | 21.63 | 24.02 | 19.74 | 25.15 |

## 2. Prueba principal y tamaño del efecto

| Escenario | Cambio entre medianas (%) | Mediana de la diferencia por semilla (s) [IC 95 %] | Mediana del cambio por semilla (%) [IC 95 %] | Mejor en | Wilcoxon p | r |
|---|---|---|---|---|---|---|
| Bajo | -13.4 | -1.86 [-2.21, -1.57] | -12.3 [-14.0, -10.5] | 30/30 | 1.86e-09 | -1.00 |
| Valle (no entrenado) | -9.8 | -1.69 [-1.96, -1.53] | -9.5 [-10.6, -8.9] | 30/30 | 1.86e-09 | -1.00 |
| Medio | -11.0 | -2.14 [-2.46, -1.91] | -11.3 [-12.6, -10.0] | 30/30 | 1.86e-09 | -1.00 |
| Alto (pico) | -43.1 | -19.31 [-22.00, -17.74] | -37.0 [-38.5, -34.9] | 30/30 | 1.86e-09 | -1.00 |
| Jueves (pico) | -5.3 | -0.83 [-1.23, -0.40] | -3.5 [-5.1, -1.9] | 26/30 | 0.000111 | -0.76 |

Nota: el cambio entre medianas compara la mediana del agente con la del real (la cifra que se reporta como resultado principal); la mediana del cambio por semilla resume las 30 comparaciones pareadas y lleva su IC.

## 3. Sensibilidad (supuestos)

Shapiro-Wilk sobre las diferencias pareadas (p < 0.05 = no normales: justifica Wilcoxon); t pareada y d de Cohen (dz) como comprobación; prueba de signos (no usa magnitudes).

| Escenario | Shapiro-Wilk p | t pareada p | dz | Prueba de signos p |
|---|---|---|---|---|
| Bajo | 0.607 | 1.49e-15 | -2.83 | 1.86e-09 |
| Valle (no entrenado) | 0.857 | 7.99e-16 | -2.89 | 1.86e-09 |
| Medio | 0.815 | 3.22e-16 | -3.00 | 1.86e-09 |
| Alto (pico) | 0.0289 | 2.95e-17 | -3.28 | 1.86e-09 |
| Jueves (pico) | 0.00111 | 0.00117 | -0.66 | 5.95e-05 |

## 4. Todas las métricas (cambio de la mediana, %; p de Wilcoxon, ajustado por Holm en secundarias)

| Métrica | Bajo | Valle (no entrenado) | Medio | Alto (pico) | Jueves (pico) |
|---|---|---|---|---|---|
| Espera promedio (s) | -13.4 % (p=1.9e-09 *) | -9.8 % (p=1.9e-09 *) | -11.0 % (p=1.9e-09 *) | -43.1 % (p=1.9e-09 *) | -5.3 % (p=0.00011 *) |
| Espera en el cruce (s/veh) | -13.7 % (p=1.1e-08 *) | -10.8 % (p=1.1e-08 *) | -11.5 % (p=1.1e-08 *) | -20.2 % (p=1.1e-08 *) | -5.5 % (p=0.00038 *) |
| Detenidos promedio | -13.3 % (p=1.1e-08 *) | -11.2 % (p=1.1e-08 *) | -11.2 % (p=1.1e-08 *) | -20.7 % (p=1.1e-08 *) | -5.5 % (p=0.00038 *) |
| Tiempo de viaje (s) | -1.8 % (p=1.1e-08 *) | -1.1 % (p=3.9e-07 *) | -1.9 % (p=1.1e-08 *) | -28.4 % (p=1.1e-08 *) | -2.0 % (p=0.0024 *) |
| Tiempo perdido (s) | -7.3 % (p=1.1e-08 *) | -3.3 % (p=3.9e-07 *) | -6.3 % (p=1.1e-08 *) | -44.8 % (p=1.1e-08 *) | -4.2 % (p=0.0024 *) |
| Velocidad (km/h) | -0.1 % (p=0.39) | -1.3 % (p=5.2e-08 *) | +0.4 % (p=0.092) | +12.8 % (p=1.1e-08 *) | +0.4 % (p=0.12) |
| Throughput (veh/h) | +0.9 % (p=0.28) | +0.1 % (p=0.00071 *) | +0.2 % (p=0.028 *) | +2.0 % (p=1.7e-06 *) | -0.0 % (p=0.21) |

## 5. Calidad de las corridas y cumplimiento

| Escenario | Controlador | Teleports (30 corr.) | Corridas con vehículos sin terminar | Ciclo prom. (s) | Ciclo mín.–máx. (s) | % ciclos > 120 s |
|---|---|---|---|---|---|---|
| Bajo | Semáforo real | 1 | 0 | 101.0 | 101–101 | 0.0 |
| Bajo | Agente Q-Learning | 1 | 0 | 72.7 | 61–111 | 0.0 |
| Valle (no entrenado) | Semáforo real | 1 | 0 | 101.0 | 101–101 | 0.0 |
| Valle (no entrenado) | Agente Q-Learning | 3 | 0 | 69.8 | 61–111 | 0.0 |
| Medio | Semáforo real | 1 | 0 | 101.0 | 101–101 | 0.0 |
| Medio | Agente Q-Learning | 1 | 0 | 76.9 | 61–116 | 0.0 |
| Alto (pico) | Semáforo real | 7 | 0 | 101.0 | 101–101 | 0.0 |
| Alto (pico) | Agente Q-Learning | 2 | 0 | 98.1 | 61–121 | 0.2 |
| Jueves (pico) | Semáforo real | 4 | 0 | 101.0 | 101–101 | 0.0 |
| Jueves (pico) | Agente Q-Learning | 5 | 0 | 91.2 | 61–121 | 6.1 |

## 6. Calibración (red final)

100/100 comparaciones con GEH < 5; GEH medio 0.89; máximo 4.77.

## 7. Política aprendida

Estados visitados en el entrenamiento: 96 de 150.

## Figuras

- `fig01_calibracion_geh.png`
- `fig02_espera_pareada.png`
- `fig03_cambio_porcentual.png`
- `fig04_mapa_metricas.png`
- `fig05_tiempos_semaforo.png`
- `fig06_colas_por_brazo.png`
- `fig07_evolucion_iteraciones.png`
- `fig08_politica_aprendida.png`

Figuras 10–11 (dinámica en el tiempo) no generadas: faltan las corridas con series (ver el script).
