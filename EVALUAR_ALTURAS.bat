@echo off
REM Fase 7.6: deteccion a 60, 80 y 100 cm con el modelo hotwheels_v2 (decide la altura de camara y la tabla).
cd /d "%~dp0"
.venv\Scripts\python.exe -u scripts\evaluar_alturas.py --pesos results\vision\entrenamiento\hotwheels_v2\weights\best.pt > results\vision\evaluar_alturas_log.txt 2>&1
type results\vision\evaluar_alturas_log.txt
pause
