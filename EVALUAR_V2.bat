@echo off
REM Evalua hotwheels_v2: (1) deteccion a 60/80/100 cm, (2) conteo en fotos propias y del cruce (conf 0.25 y 0.40, NMS 0.5).
cd /d "%~dp0"
echo Evaluando hotwheels_v2... (3-6 minutos)
.venv\Scripts\python.exe -u scripts\evaluar_alturas.py --pesos results\vision\entrenamiento\hotwheels_v2\weights\best.pt > results\vision\evaluar_alturas_log.txt 2>&1
.venv\Scripts\python.exe -u scripts\evaluar_yolo_hotwheels.py --pesos results\vision\entrenamiento\hotwheels_v2\weights\best.pt --conf 0.25 --nms_iou 0.5 > results\vision\evaluacion_v2_log.txt 2>&1
.venv\Scripts\python.exe -u scripts\evaluar_yolo_hotwheels.py --pesos results\vision\entrenamiento\hotwheels_v2\weights\best.pt --conf 0.40 --nms_iou 0.5 >> results\vision\evaluacion_v2_log.txt 2>&1
echo FIN_EVALUACION_V2 >> results\vision\evaluacion_v2_log.txt
echo LISTO.
pause
