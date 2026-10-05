# Bitácora del proyecto

Registro de lo que se hizo, qué funcionó, qué falló y qué se decidió.

## 2026-10-03 — Fase 0: planificación
- Análisis del proyecto, riesgos, arquitectura, MVP y hoja de ruta → `docs/fases/00_fase0_planificacion.md`.
- **Decisión:** ML = Aprendizaje por Refuerzo (Q-Learning con tabla; DQN solo si hace falta), según el anteproyecto aprobado. Se descarta el enfoque supervisado de la v1 del plan.
- **Decisión:** se agrega un prototipo físico a escala (cámara + YOLO + ESP32) como demostración.

## 2026-10-04 — Respuestas de la directora y entorno
- Directora: aprueba el prototipo físico; se mantiene el título; mínimo 6 objetivos específicos; no requiere trámite formal; la hipótesis puede reformularse → `docs/anteproyecto/ajustes_anteproyecto.md`.
- Sustentación: principios de febrero de 2027. Hoja de ruta ajustada a 17 semanas.
- Repositorio GitHub: `tesis`, público.
- Verificación del entorno con `scripts/check_entorno.ps1` → `docs/entorno/reporte_entorno.txt` y análisis en `docs/entorno/analisis_entorno.md`.
  - Sin GPU NVIDIA (Intel UHD): YOLO correrá en CPU.
  - SUMO no instalado. Python 3.11.5 disponible. Git y Arduino IDE instalados.
