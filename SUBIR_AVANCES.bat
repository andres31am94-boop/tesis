@echo off
REM Sube a GitHub los avances (las fotos/videos propios quedan fuera por .gitignore).
cd /d "%~dp0"
(
git add -A
git status --short
git commit -m "Registro automatico de computo en 20 scripts (results/registro_computo.csv), resumen de computo con estimado de lo no medido, registro del tiempo dedicado por los autores, protocolo de experimentos de la maqueta v1" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01NSfkFfRDfUTDbj3sqLx43G"
git push
git log --oneline -1
) > results\subir_avances_log.txt 2>&1
echo FIN >> results\subir_avances_log.txt
type results\subir_avances_log.txt
pause
