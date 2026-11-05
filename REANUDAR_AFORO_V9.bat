@echo off
REM Continua aforo_v9 desde el ultimo episodio completo.
cd /d "%~dp0"
.venv\Scripts\python.exe -u -m src.agent.entrenar --escenarios aforo_bajo aforo_medio aforo_alto aforo_pico_jueves desb_dg15_cargada desb_cra23_sola desb_nocturno desb_alternante --episodios 640 --nombre aforo_v9 --continuar >> results\entrenamiento_aforo_v9_log.txt 2>&1
echo FIN_ENTRENAMIENTO >> results\entrenamiento_aforo_v9_log.txt
pause
