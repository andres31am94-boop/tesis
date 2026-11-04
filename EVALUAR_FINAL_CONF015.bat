@echo off
REM Evalua el modelo final con umbral bajo (conf 0.15), porque a 0.25 y 0.40 se queda corto contando.
cd /d "%~dp0"
echo Evaluando modelo final con conf 0.15...
.venv\Scripts\python.exe -u scripts\evaluar_yolo_hotwheels.py --pesos results\vision\entrenamiento\hotwheels_v1\weights\best.pt --conf 0.15 --nms_iou 0.5 > results\vision\evaluacion_final_conf015_log.txt 2>&1
echo LISTO.
pause
