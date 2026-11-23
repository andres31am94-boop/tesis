@echo off
REM Graba un video de la maqueta para reentrenar YOLO. Responda las preguntas en esta ventana.
REM Los videos quedan en data\raw\maqueta\videos (NO se suben a GitHub).
cd /d "%~dp0"
.venv\Scripts\python.exe -u scripts\grabar_maqueta.py
pause
