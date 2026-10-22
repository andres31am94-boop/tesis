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
| 1 | Intersección en SUMO (Cra 23 × Dg 15, Acacías) | VALIDADO. Aforo real cargado (4 escenarios, oct-2026) |
| 1b | Calibración con el aforo (GEH < 5 por brazo) | VALIDADO: 4 escenarios × 4 brazos × 5 semillas = 80/80 con GEH < 5 (máx. 3.9). Ver `docs/bitacora.md` y `config/calibracion.yaml` |
| 2 | Python + TraCI | VALIDADO |
| 3 | Baseline de tiempos fijos + capa de seguridad | VALIDADO con los tiempos medidos del semáforo real (Cra 23: 55 s verde; Dg 15: 20 s verde; ciclo 101 s) |
| 4–6 | Entorno RL, entrenamiento y control adaptativo | IMPLEMENTADO con demanda de prueba (Q-Learning tabular); pendiente reentrenar con escenarios calibrados |
| 7–9 | Visión artificial (YOLO + tracking) | PLANIFICADO |
| 10–12 | ESP32, maqueta e integración | PLANIFICADO |
| 13–14 | Experimentos y documentación | PLANIFICADO |

Estados: PLANIFICADO → EN DESARROLLO → IMPLEMENTADO → PROBADO → VALIDADO.

## Documentación

- [Fase 0 — Planificación y arquitectura](docs/fases/00_fase0_planificacion.md)
- [Ajustes al anteproyecto](docs/anteproyecto/ajustes_anteproyecto.md)
- [Entorno de desarrollo](docs/entorno/analisis_entorno.md)
- [Bitácora](docs/bitacora.md)
