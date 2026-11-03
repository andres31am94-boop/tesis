@echo off
REM Fase 7.2: prueba de tiempo de entrenamiento YOLO26n (1 epoca, 5% de las imagenes, lote 8, CPU).
REM Salida en results\vision\entrenamiento_prueba_tiempo_log.txt
cd /d "%~dp0..\.."
echo Entrenamiento de prueba en curso... no cierre esta ventana.
.venv\Scripts\python.exe -u scripts\entrenar_yolo.py --datos data\raw\datasets_comunidad\hot-wheels-recognition_v1\data_tesis.yaml --epocas 1 --fraccion 0.05 --lote 8 --nombre prueba_tiempo > results\vision\entrenamiento_prueba_tiempo_log.txt 2>&1
echo Terminado (codigo %errorlevel%).
