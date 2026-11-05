@echo off
REM aforo_v9, paso 1: verifica que los 4 escenarios desbalanceados corren bien en SUMO (semilla 1, tiempos fijos y agente v8).
cd /d "%~dp0"
echo Verificando escenarios desbalanceados (5-10 minutos)...
(
for %%E in (desb_dg15_cargada desb_cra23_sola desb_nocturno desb_alternante) do (
  .venv\Scripts\python.exe -m src.simulation.ejecutar_escenario --escenario %%E --controlador tiempos_fijos --semilla 1
  .venv\Scripts\python.exe -m src.simulation.ejecutar_escenario --escenario %%E --controlador qlearning --modelo aforo_v8 --semilla 1
)
) > results\verificar_escenarios_desb_log.txt 2>&1
echo FIN_VERIFICACION >> results\verificar_escenarios_desb_log.txt
echo LISTO.
pause
