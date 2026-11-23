@echo off
REM Fase 8: prueba con la TABLA VACIA (sin carros). Camara 1 (msmf) durante 60 s, sin ESP32.
REM Esperado: 0 carros en todas las zonas. Si cuenta sombras o cables, queda registrado en por_segundo.csv.
cd /d "%~dp0"
.venv\Scripts\python.exe -u -m src.maqueta.lazo_camara --fuente 1 --zonas config\zonas_camara.yaml --duracion_s 60 --grabar > results\prueba_tabla_vacia_log.txt 2>&1
echo FIN >> results\prueba_tabla_vacia_log.txt
type results\prueba_tabla_vacia_log.txt
pause
