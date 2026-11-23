@echo off
REM Sube a GitHub los avances (las fotos/videos propios quedan fuera por .gitignore).
cd /d "%~dp0"
(
git add -A
git status --short
git commit -m "Camara de la maqueta: zonas reales y capacidad medida, prueba de tabla vacia y de conteo, grabacion para reentrenar YOLO (sesion A), registro de computo y de horas" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01NSfkFfRDfUTDbj3sqLx43G"
git push
git log --oneline -1
) > results\subir_avances_log.txt 2>&1
echo FIN >> results\subir_avances_log.txt
type results\subir_avances_log.txt
pause
