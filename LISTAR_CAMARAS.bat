@echo off
REM Lista las camaras que ve el PC (iPhone como camara web incluido) y guarda un cuadro de cada una.
cd /d "%~dp0"
.venv\Scripts\python.exe -u scripts\listar_camaras.py > results\listar_camaras_log.txt 2>&1
type results\listar_camaras_log.txt
pause
