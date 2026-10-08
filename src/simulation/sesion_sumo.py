"""Abre y cierra una simulacion de SUMO controlada por TraCI."""
import os
from contextlib import contextmanager
from pathlib import Path

if "SUMO_HOME" not in os.environ:
    raise EnvironmentError("La variable SUMO_HOME no esta definida. Revisa la instalacion de SUMO.")

import sumolib  # noqa: E402
import traci    # noqa: E402


def iniciar_sumo(archivo_config, usar_gui=False, semilla=None, retraso_gui_ms=100, argumentos_extra=None):
    """Arranca SUMO controlado por TraCI. Quien lo llama debe cerrarlo con traci.close()."""
    archivo_config = Path(archivo_config)
    if not archivo_config.exists():
        raise FileNotFoundError(f"No se encuentra la configuracion de SUMO: {archivo_config}")

    binario = sumolib.checkBinary("sumo-gui" if usar_gui else "sumo")
    comando = [binario, "-c", str(archivo_config)]
    if semilla is not None:
        comando += ["--seed", str(semilla)]  # reemplaza la semilla del .sumocfg
    if usar_gui:
        comando += ["--start", "--quit-on-end", "--delay", str(retraso_gui_ms)]
    if argumentos_extra:
        comando += [str(argumento) for argumento in argumentos_extra]  # p. ej. salidas de SUMO
    traci.start(comando)


@contextmanager
def sesion_sumo(archivo_config, usar_gui=False, semilla=None, retraso_gui_ms=100, argumentos_extra=None):
    """
    Uso:
        with sesion_sumo("sumo/configs/prueba.sumocfg"):
            ... traci.simulationStep() ...
    La conexion se cierra siempre al salir del bloque, incluso si hay un error
    (el error no se oculta: se sigue mostrando).
    """
    iniciar_sumo(archivo_config, usar_gui, semilla, retraso_gui_ms, argumentos_extra)
    try:
        yield
    finally:
        traci.close()
