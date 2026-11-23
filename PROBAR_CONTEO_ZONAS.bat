@echo off
REM Fase 8: prueba de CONTEO con carros quietos en las zonas. Camara 1 (msmf) durante 30 s, sin ESP32.
REM Comparar el conteo por zona (por_segundo.csv) con el conteo manual de los autores.
cd /d "%~dp0"
.venv\Scripts\python.exe -u -m src.maqueta.lazo_camara --fuente 1 --zonas config\zonas_camara.yaml --duracion_s 30 --grabar > results\prueba_conteo_zonas_log.txt 2>&1
echo FIN >> results\prueba_conteo_zonas_log.txt
type results\prueba_conteo_zonas_log.txt
pause
