@echo off
REM Fase 7.4 (una sola vez): instala Label Studio en un entorno aparte (.venv_label) para no mezclar versiones con el proyecto.
cd /d "%~dp0"
.venv\Scripts\python.exe -m venv .venv_label
.venv_label\Scripts\python.exe -m pip install --upgrade pip
.venv_label\Scripts\python.exe -m pip install label-studio
echo.
echo Instalacion terminada. Ahora ejecute PRE_ETIQUETAR.bat
pause
