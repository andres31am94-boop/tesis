@echo off
REM Prueba VISUAL de los 4 semaforos: repetir cada vez que se arme o desarme la maqueta.
REM Responda en esta ventana lo que ve en cada semaforo. Guarda el reporte en results\hardware.
cd /d "%~dp0..\.."
.venv\Scripts\python.exe scripts\probar_semaforos_visual.py --puerto COM4
pause
