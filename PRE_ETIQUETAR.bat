@echo off
REM Fase 7.4: el modelo propone las cajas de las 117 imagenes (archivo de tareas para Label Studio).
cd /d "%~dp0"
.venv\Scripts\python.exe -u scripts\preetiquetar_label_studio.py
echo.
echo Listo. Ahora ejecute INICIAR_LABEL_STUDIO.bat
pause
