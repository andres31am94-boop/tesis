@echo off
REM Fase 9 paso 2: video de prueba a 1 m -> YOLO (hotwheels_v2) + tracking + zonas -> conteo por segundo -> estado del agente.
cd /d "%~dp0"
echo Procesando video de 1 m (1-3 minutos)...
.venv\Scripts\python.exe -u scripts\contar_zonas_video.py --pesos results\vision\entrenamiento\hotwheels_v2\weights\best.pt --video data\raw\hotwheels\prueba_alturas\un_metro.MOV --zonas config\zonas_prueba_1m.yaml --conf 0.40 --cada 2 > results\vision\paso9_2_log.txt 2>&1
.venv\Scripts\python.exe -u scripts\estado_agente_desde_video.py --conteo results\vision\conteo_zonas\un_metro\conteo_por_segundo.csv --zonas config\zonas_prueba_1m.yaml >> results\vision\paso9_2_log.txt 2>&1
echo FIN_PASO_9_2 >> results\vision\paso9_2_log.txt
type results\vision\paso9_2_log.txt
pause
