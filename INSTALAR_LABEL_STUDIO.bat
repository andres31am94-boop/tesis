@echo off
REM Fase 7.4 (una sola vez): instala Label Studio en un entorno aparte (.venv_label) para no mezclar versiones con el proyecto.
REM El detalle queda en results\vision\instalar_label_studio_log.txt
cd /d "%~dp0"
echo Instalando Label Studio (puede tardar 5-15 minutos)...
.venv\Scripts\python.exe -m venv .venv_label > results\vision\instalar_label_studio_log.txt 2>&1
.venv_label\Scripts\python.exe -m pip install --upgrade pip >> results\vision\instalar_label_studio_log.txt 2>&1
.venv_label\Scripts\python.exe -m pip install label-studio >> results\vision\instalar_label_studio_log.txt 2>&1
.venv_label\Scripts\label-studio.exe --version >> results\vision\instalar_label_studio_log.txt 2>&1
echo FIN_INSTALACION >> results\vision\instalar_label_studio_log.txt
echo.
echo Instalacion terminada. Ahora ejecute PRE_ETIQUETAR.bat
pause
