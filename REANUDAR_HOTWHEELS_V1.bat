@echo off
REM Fase 7.2: entrenamiento YOLO26n con Hot-wheels-recognition v1 (20%% del train, 8 epocas, lote 8, CPU, semilla 0).
REM Estimado con la prueba de tiempo: ~35 min por epoca -> ~4,5-5 h. Salida en results\vision\entrenamiento_hotwheels_v1_log.txt
REM Si se interrumpe: usar REANUDAR_HOTWHEELS_V1.bat
cd /d "%~dp0"
echo Reanudando el entrenamiento de YOLO. Puede minimizar esta ventana, pero NO la cierre ni apague el PC.
.venv\Scripts\python.exe -u scripts\entrenar_yolo.py --datos data\raw\datasets_comunidad\hot-wheels-recognition_v1\data_tesis.yaml --nombre hotwheels_v1 --reanudar >> results\vision\entrenamiento_hotwheels_v1_log.txt 2>&1
echo Terminado (codigo %errorlevel%).
pause
