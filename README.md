# Sistema de semaforización inteligente basado en Machine Learning

Proyecto de grado — Ingeniería Informática
Corporación Universitaria Autónoma de Nariño, Extensión Villavicencio

**Autores:** Sebastián Stiven Chaves Montenegro · Joseph Andrés Mendoza Barbosa
**Directora:** Mónica Adriana Rubio Carrillo

## Descripción

Este proyecto controla un semáforo con un agente de **Aprendizaje por Refuerzo (Q-Learning)** que decide en cada momento si mantener o cambiar la fase. Una **capa de seguridad** limita esas decisiones: verde mínimo y máximo, amarillo y todo-rojo.

- **Simulación (SUMO + TraCI):** el agente aprende y se compara contra un semáforo de tiempos fijos.
- **Prototipo físico a escala:** una cámara con YOLO observa vehículos en miniatura, el mismo agente decide y un ESP32 controla semáforos de LEDs.

> Prototipo académico. No controla infraestructura vial real.

## Estado del proyecto

| Fase | Descripción | Estado |
|---|---|---|
| 0 | Planificación y arquitectura | VALIDADO |
| 1 | Intersección en SUMO (Cra 23 × Dg 15, Acacías) con aforos reales (5 escenarios, oct-2026) | VALIDADO |
| 1b | Calibración con los aforos (GEH < 5 por brazo) | VALIDADO: 100/100 con GEH < 5 (red final, 5 escenarios × 4 brazos × 5 semillas; máx. 4.8) |
| 2 | Python + TraCI | VALIDADO |
| 3 | Baseline: semáforo real (Cra 23 55 s, Dg 15 20 s, ciclo 101 s) + capa de seguridad | VALIDADO |
| 4–6 | Agente Q-Learning, entrenamiento y control adaptativo | VALIDADO: modelo final `aforo_v8`, evaluación final con 30 semillas por escenario |
| 13 (simulado) | Experimentos y evaluación estadística | VALIDADO (ver Resultados) |
| 7–9 | Visión artificial (YOLO + tracking) | EN DESARROLLO |
| 10–12 | ESP32, maqueta e integración | EN DESARROLLO (materiales listos; plano en `hardware/maqueta_diseno.html`) |
| 14 | Documentación de tesis | EN DESARROLLO |

Estados: PLANIFICADO → EN DESARROLLO → IMPLEMENTADO → PROBADO → VALIDADO.

## Documentación

- [Fase 0 — Planificación y arquitectura](docs/fases/00_fase0_planificacion.md)
- [Ajustes al anteproyecto](docs/anteproyecto/ajustes_anteproyecto.md)
- [Entorno de desarrollo](docs/entorno/analisis_entorno.md)
- [Bitácora](docs/bitacora.md)
- [Figuras de la evaluación final, explicadas](docs/figuras/README.md)
- [Estadística de la evaluación final](docs/figuras/estadistica_evaluacion_final.md)
- [Escala del trabajo experimental (horas simuladas y de cómputo)](docs/resumen_computo.md)

## Resultados (parte simulada)

Evaluación final: modelo `aforo_v8` contra el semáforo real, 5 escenarios de aforo × 30 semillas pareadas (semillas
1–30, no usadas en el diseño), 300 horas simuladas. Métrica principal: tiempo de espera promedio por vehículo.
Prueba de Wilcoxon de rangos con signo (pareada).

| Escenario | Semáforo real (mediana) | Agente (mediana) | Cambio | p | Mejora en |
|---|---|---|---|---|---|
| Bajo | 15.6 s | 13.5 s | −13.4 % | < 0.001 | 30/30 |
| Valle (no visto en entrenamiento) | 17.8 s | 16.0 s | −9.8 % | < 0.001 | 30/30 |
| Medio | 19.3 s | 17.2 s | −11.0 % | < 0.001 | 30/30 |
| Alto (hora pico) | 55.9 s | 31.8 s | −43.1 % | < 0.001 | 30/30 |
| Jueves (hora pico) | 23.6 s | 22.3 s | −5.3 % | < 0.001 | 26/30 |

Sin vehículos sin terminar en ninguna corrida; el flujo de vehículos no disminuye; ciclos del agente de 61–121 s
(Manual de Señalización Vial 2024). Limitaciones: ver [figuras](docs/figuras/README.md#límites-de-estos-resultados).

## Cómo reproducir

Requisitos: SUMO 1.27.1, Python 3 con `requirements.txt` en `.venv`. Desde la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .                                # pruebas
.\.venv\Scripts\python.exe scripts\generar_accesos.py                                         # red
netconvert -c sumo\network\acacias_ajustes.netccfg
netconvert -c sumo\network\acacias_conexiones.netccfg
.\.venv\Scripts\python.exe scripts\generar_escenarios_aforo.py                                # escenarios
.\.venv\Scripts\python.exe -m src.agent.entrenar --escenarios aforo_bajo aforo_medio aforo_alto aforo_pico_jueves --episodios 320 --nombre aforo_v8
.\.venv\Scripts\python.exe scripts\comparar_controladores.py --modelo aforo_v8 --carpeta evaluacion_final --controladores tiempos_fijos qlearning
.\.venv\Scripts\python.exe scripts\analizar_comparacion.py --modelo evaluacion_final
.\.venv\Scripts\python.exe scripts\graficas_tesis.py
```

Cada corrida es determinista dada su semilla y su configuración (`config/`).

