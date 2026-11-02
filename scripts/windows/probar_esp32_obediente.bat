@echo off
REM Paso 10.5a: prueba del ESP32 obediente. Guarda la salida en results\hardware.
cd /d "%~dp0..\.."
echo Ejecutando prueba del ESP32 (1 minuto aprox)... no cierre esta ventana.
.venv\Scripts\python.exe scripts\probar_esp32_obediente.py --puerto COM4 > results\hardware\prueba_10_5a_obediente.txt 2>&1
echo Terminado. Resultado en results\hardware\prueba_10_5a_obediente.txt
timeout /t 5
