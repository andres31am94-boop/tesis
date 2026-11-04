@echo off
REM Continua el entrenamiento hotwheels_v2 desde la ultima epoca guardada.
cd /d "%~dp0"
.venv\Scripts\python.exe -u scripts\entrenar_yolo.py --datos data\processed\hotwheels_combinado\data.yaml --nombre hotwheels_v2 --reanudar >> results\vision\entrenamiento_hotwheels_v2_log.txt 2>&1
echo TERMINADO.
pause
