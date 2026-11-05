@echo off
REM Validacion de aforo_v9 (semillas 101-110): v9 vs tiempos fijos en 9 escenarios; v8 en los 4 desbalanceados (para comparar v8 vs v9).
REM Se puede interrumpir y volver a ejecutar: las corridas guardadas no se repiten.
cd /d "%~dp0"
echo Validando aforo_v9 (~2-3 horas). No apague ni suspenda el PC.
.venv\Scripts\python.exe -u scripts\comparar_controladores.py --modelo aforo_v9 --escenarios aforo_bajo aforo_valle_manana aforo_medio aforo_alto aforo_pico_jueves desb_dg15_cargada desb_cra23_sola desb_nocturno desb_alternante --semillas 101 102 103 104 105 106 107 108 109 110 --controladores tiempos_fijos qlearning --carpeta aforo_v9_validacion > results\validacion_aforo_v9_log.txt 2>&1
.venv\Scripts\python.exe -u scripts\comparar_controladores.py --modelo aforo_v8 --escenarios desb_dg15_cargada desb_cra23_sola desb_nocturno desb_alternante --semillas 101 102 103 104 105 106 107 108 109 110 --controladores qlearning --carpeta aforo_v8_validacion_desb >> results\validacion_aforo_v9_log.txt 2>&1
echo FIN_VALIDACION >> results\validacion_aforo_v9_log.txt
echo TERMINADO.
pause
