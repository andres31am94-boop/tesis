@echo off
REM Evalua el modelo FINAL (best.pt = epoca 5, mAP50 0.614) con las fotos propias, con NMS, a conf 0.25 y 0.40.
cd /d "%~dp0"
echo Evaluando modelo final... (tarda 1-2 minutos)
.venv\Scripts\python.exe -u scripts\evaluar_yolo_hotwheels.py --pesos results\vision\entrenamiento\hotwheels_v1\weights\best.pt --conf 0.25 --nms_iou 0.5 > results\vision\evaluacion_final_log.txt 2>&1
.venv\Scripts\python.exe -u scripts\evaluar_yolo_hotwheels.py --pesos results\vision\entrenamiento\hotwheels_v1\weights\best.pt --conf 0.40 --nms_iou 0.5 >> results\vision\evaluacion_final_log.txt 2>&1
echo LISTO. Ya puedes cerrar esta ventana.
pause
