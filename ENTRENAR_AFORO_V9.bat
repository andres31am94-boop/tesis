@echo off
REM aforo_v9: MISMA configuracion del agente que aforo_v8 (config/agente.yaml) + 4 escenarios desbalanceados derivados.
REM 8 escenarios rotados x 80 episodios cada uno = 640 episodios (v8: 4 x 80 = 320). Si se interrumpe: REANUDAR_AFORO_V9.bat
cd /d "%~dp0"
echo Entrenando aforo_v9 (~3-4 horas). No apague ni suspenda el PC.
.venv\Scripts\python.exe -u -m src.agent.entrenar --escenarios aforo_bajo aforo_medio aforo_alto aforo_pico_jueves desb_dg15_cargada desb_cra23_sola desb_nocturno desb_alternante --episodios 640 --nombre aforo_v9 > results\entrenamiento_aforo_v9_log.txt 2>&1
echo FIN_ENTRENAMIENTO >> results\entrenamiento_aforo_v9_log.txt
echo TERMINADO.
pause
