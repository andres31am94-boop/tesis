@echo off
REM Sube a GitHub los avances. Excluye el entrenamiento hotwheels_v2 mientras sigue en curso.
cd /d "%~dp0"
(
git add -A -- . ":(exclude)results/vision/entrenamiento/hotwheels_v2" ":(exclude)results/vision/entrenamiento_hotwheels_v2_log.txt"
git status --short
git commit -m "Fase 7.4-7.5: evaluacion del modelo final hotwheels_v1, Label Studio (117 imagenes propias corregidas), conversion a YOLO y dataset combinado para reentrenar" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01NSfkFfRDfUTDbj3sqLx43G"
git push
git log --oneline -1
) > results\subir_avances_log.txt 2>&1
echo FIN >> results\subir_avances_log.txt
type results\subir_avances_log.txt
pause
