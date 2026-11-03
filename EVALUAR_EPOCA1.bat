@echo off
REM Evalua el modelo de la epoca 1 con NMS (quita cajas duplicadas), a dos umbrales de confianza.
cd /d "%~dp0"
.venv\Scripts\python.exe -u scripts\evaluar_yolo_hotwheels.py --pesos results\vision\entrenamiento\hotwheels_v1_epoca1\weights\best.pt --conf 0.25 --nms_iou 0.5 > results\vision\evaluacion_epoca1_nms_log.txt 2>&1
.venv\Scripts\python.exe -u scripts\evaluar_yolo_hotwheels.py --pesos results\vision\entrenamiento\hotwheels_v1_epoca1\weights\best.pt --conf 0.40 --nms_iou 0.5 >> results\vision\evaluacion_epoca1_nms_log.txt 2>&1
