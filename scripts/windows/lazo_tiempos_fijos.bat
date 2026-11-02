@echo off
REM Paso 10.5b: hardware en el lazo con el semaforo de tiempos fijos (aforo_alto, semilla 1, t=900-1200 s).
REM La salida se guarda en results\hardware\lazo_tiempos_fijos_log.txt
cd /d "%~dp0..\.."
echo Hardware en el lazo en curso (unos 7 minutos)... no cierre esta ventana.
.venv\Scripts\python.exe -u -m src.simulation.lazo_hardware --escenario aforo_alto --semilla 1 --controlador tiempos_fijos --puerto COM4 --inicio_s 900 --duracion_s 300 --gui --comparar > results\hardware\lazo_tiempos_fijos_log.txt 2>&1
echo Terminado (codigo %errorlevel%). Ver results\hardware\lazo_tiempos_fijos_log.txt
pause
