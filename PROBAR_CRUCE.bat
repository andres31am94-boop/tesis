@echo off
REM Fase 8: segunda foto cercana del cruce (8 carros), modelos epoca 1 y 2.
cd /d "%~dp0"
.venv\Scripts\python.exe -u scripts\evaluar_yolo_hotwheels.py --pesos results\vision\entrenamiento\hotwheels_v1_epoca1\weights\best.pt --conf 0.40 --nms_iou 0.5 > results\vision\cruce_cerca2_log.txt 2>&1
.venv\Scripts\python.exe -u scripts\evaluar_yolo_hotwheels.py --pesos results\vision\entrenamiento\hotwheels_v1_epoca2\weights\best.pt --conf 0.25 --nms_iou 0.5 >> results\vision\cruce_cerca2_log.txt 2>&1
