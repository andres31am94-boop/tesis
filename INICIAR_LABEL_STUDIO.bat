@echo off
REM Fase 7.4: abre Label Studio en el navegador (http://localhost:8080). Las imagenes se leen desde el PC.
REM No cierre esta ventana mientras etiqueta.
cd /d "%~dp0"
set LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
set LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=%~dp0data\raw\hotwheels
set LABEL_STUDIO_BASE_DATA_DIR=%~dp0data\label_studio
.venv_label\Scripts\label-studio.exe start --port 8080
pause
