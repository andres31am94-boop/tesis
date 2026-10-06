# Entorno de desarrollo — análisis (2026-10-04)

Fuente: `docs/entorno/reporte_entorno.txt`, generado con `scripts/check_entorno.ps1`.

## Lo encontrado

| Elemento | Resultado | Implicación |
|---|---|---|
| Sistema operativo | Windows 11 Home, 64 bits | SUMO tiene instalador oficial para Windows |
| CPU | Intel Core i7-10510U (portátil, 4 núcleos) | Suficiente para SUMO y entrenamiento Q-Learning |
| RAM | 7,8 GB | Justa para YOLO + SUMO a la vez; cerrar otros programas |
| Disco libre (C:) | 29,5 GB | Suficiente si se usa PyTorch versión CPU; vigilar |
| GPU | Intel UHD Graphics, **sin NVIDIA** | No hay CUDA: YOLO se ejecutará en CPU |
| Python | 3.11.5 en PATH; también 3.13 y Miniconda (3.8) | Varias versiones: usaremos un entorno virtual con 3.11 |
| pip | 25.2 (Python 3.11) | OK |
| SUMO / SUMO_HOME | **1.27.1** instalado; `SUMO_HOME = C:\Program Files (x86)\Eclipse\Sumo\` (verificado 2026-10-04) | `traci` y `sumolib` deben instalarse en la misma versión (1.27.1) |
| Git | 2.53.0 | OK |
| Librerías globales | numpy, pandas, scipy instalados; faltan matplotlib, yaml, cv2, torch, ultralytics, serial, traci, sumolib | Se instalan **dentro del entorno virtual**, no de forma global |
| Arduino IDE | Instalado (Program Files) | OK para el ESP32 |
| Cámara | Integrada "HD User Facing" | Sirve para pruebas iniciales de YOLO; la maqueta necesita una webcam USB externa en soporte cenital |

## Decisiones

**Python 3.11 en un entorno virtual (`.venv`)**
- *Problema:* hay tres instalaciones de Python. Instalar librerías "en el Python global" puede terminar en la versión equivocada.
- *Solución:* un entorno virtual dentro de la carpeta `tesis`, creado explícitamente con 3.11 (`py -3.11 -m venv .venv`).
- *Por qué 3.11:* ya está instalada y es la que responde a `python`. Es una versión madura, con soporte amplio en las librerías del proyecto (SUMO/TraCI, PyTorch, Ultralytics, OpenCV). La compatibilidad exacta se verifica al instalar.

**YOLO en CPU**
- La velocidad (FPS) en esta PC **debe medirse** en la Fase 7.
- Hipótesis: la maqueta tiene tráfico lento, así que una tasa baja de FPS podría ser suficiente. Debe comprobarse.
- Opciones si no alcanza, que se evaluarán con datos y no se adoptan aún: el modelo más pequeño, resolución menor, exportación a OpenVINO (formato optimizado para procesadores Intel, soportado por Ultralytics), o entrenar el fine-tuning en Google Colab.

**PyTorch versión CPU:** más liviana que la versión con CUDA, que de todos modos no serviría sin GPU NVIDIA.
