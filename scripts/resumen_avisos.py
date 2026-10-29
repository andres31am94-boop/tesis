"""
Auditoria de atascos: resume los avisos de SUMO guardados por corrida (teleports y frenadas de emergencia), por carril.
Sirve para encontrar DONDE se traban los vehiculos sin revisar cada corrida en sumo-gui.

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\resumen_avisos.py results\\comparacion\\aforo_v7_validacion\\avisos_sumo
  .\\.venv\\Scripts\\python.exe scripts\\resumen_avisos.py results\\aforo_pico_jueves\\tiempos_fijos\\semilla_110
"""
import re
import sys
from collections import Counter
from pathlib import Path

TELEPORT = re.compile(r"Teleporting vehicle '([^']+)'; ([^,]+), lane='([^']+)', time=([0-9]+(?:\.[0-9]+)?)")
FRENADA = re.compile(r"emergency braking on lane '([^']+)'.*time=([0-9]+(?:\.[0-9]+)?)")


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: resumen_avisos.py <carpeta con archivos .log>")
    carpeta = Path(sys.argv[1])
    logs = sorted(carpeta.glob("*.log"))
    if not logs:
        sys.exit(f"No hay archivos .log en {carpeta}")
    total_carril, total_motivo, frenadas = Counter(), Counter(), Counter()
    print(f"{'corrida':<45}{'teleports':>10}  primer teleport (tiempo, carril, motivo)")
    for log in logs:
        texto = log.read_text(encoding="utf-8", errors="replace")
        teleports = TELEPORT.findall(texto)
        for _, motivo, carril, _ in teleports:
            total_carril[carril] += 1
            total_motivo[motivo] += 1
        for carril, _ in FRENADA.findall(texto):
            frenadas[carril] += 1
        primero = f"{teleports[0][3]} s, {teleports[0][2]}, {teleports[0][1]}" if teleports else "-"
        if teleports:
            print(f"{log.stem:<45}{len(teleports):>10}  {primero}")
    print("\nTeleports por carril:", dict(total_carril.most_common()))
    print("Teleports por motivo:", dict(total_motivo.most_common()))
    print("Frenadas de emergencia por carril:", dict(frenadas.most_common()))


if __name__ == "__main__":
    main()
