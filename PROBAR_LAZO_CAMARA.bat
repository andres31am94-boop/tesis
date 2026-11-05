@echo off
REM Prueba del lazo en vivo SIN ESP32: video de 1 m en bucle durante 120 s, agente aforo_v9, guarda el video anotado.
cd /d "%~dp0"
.venv\Scripts\python.exe -u -m src.maqueta.lazo_camara --fuente data\raw\hotwheels\prueba_alturas\un_metro.MOV --zonas config\zonas_prueba_1m.yaml --duracion_s 120 --repetir --grabar > results\prueba_lazo_camara_log.txt 2>&1
echo FIN_PRUEBA_LAZO >> results\prueba_lazo_camara_log.txt
type results\prueba_lazo_camara_log.txt
pause
