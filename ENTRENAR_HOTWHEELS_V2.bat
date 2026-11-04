@echo off
REM Fase 7.5: reentrena YOLO partiendo del modelo hotwheels_v1 (best.pt, epoca 5) con fotos PROPIAS (x5) + 1000 publicas.
REM Validacion: video propio v0580. Dataset armado con scripts\preparar_dataset_combinado.py
REM Si se interrumpe: REANUDAR_HOTWHEELS_V2.bat
cd /d "%~dp0"
echo Entrenando hotwheels_v2 (10 epocas, ~2-3 horas en CPU). No cierre esta ventana ni suspenda el PC.
.venv\Scripts\python.exe -u scripts\entrenar_yolo.py --datos data\processed\hotwheels_combinado\data.yaml --modelo results\vision\entrenamiento\hotwheels_v1\weights\best.pt --epocas 10 --lote 8 --nombre hotwheels_v2 > results\vision\entrenamiento_hotwheels_v2_log.txt 2>&1
echo TERMINADO. Revise results\vision\entrenamiento_hotwheels_v2_log.txt
pause
