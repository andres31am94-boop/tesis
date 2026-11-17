"""
Prueba VISUAL de los 4 semaforos de la maqueta (S1-S4). Repetible: hacerla cada vez que se arma o desarma la maqueta.

Por que existe: probar_esp32_obediente.py solo comprueba que el ESP32 RESPONDE por USB; no puede saber si cada LED
prendio en el semaforo correcto. Aqui el PC pone cada luz del cruce, la MANTIENE encendida (latido cada 1 s, asi el
freno SIN_PC del ESP32 no se activa) y la persona confirma lo que ve en cada semaforo.

Usa el firmware vigente (hardware/esp32/semaforo_obediente); no hay que cargar otro programa en el ESP32.
Como el firmware maneja los semaforos por eje (S1+S2 = Cra 23, S3+S4 = Dg 15), se recorren 5 luces que encienden los
12 LEDs al menos una vez: TODO_ROJO, VERDE_CRA23, AMARILLO_CRA23, VERDE_DG15, AMARILLO_DG15.

Salidas:
  results/hardware/prueba_visual_semaforos_<fecha_hora>.txt   reporte completo de esta prueba
  results/hardware/registro_pruebas_semaforos.csv              historial (una fila por LED y prueba)

Uso (desde la carpeta tesis, con Arduino IDE / Monitor Serie CERRADO):
  .\\.venv\\Scripts\\python.exe scripts\\probar_semaforos_visual.py --puerto COM4
"""
import argparse
import csv
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))  # para importar src.*

from src.communication.esp32_serial import ConexionESP32  # noqa: E402

CARPETA_RESULTADOS = CARPETA_TESIS / "results" / "hardware"
REGISTRO_CSV = CARPETA_RESULTADOS / "registro_pruebas_semaforos.csv"

SEMAFOROS = {
    "S1": "Cra 23 sur",
    "S2": "Cra 23 norte",
    "S3": "Dg 15 oeste",
    "S4": "Dg 15 este",
}
# Que color debe mostrar cada semaforo con cada luz del cruce (igual que COLOR_CRA23 / COLOR_DG15 del firmware).
PASOS = [
    ("TODO_ROJO",      {"S1": "ROJO",     "S2": "ROJO",     "S3": "ROJO",     "S4": "ROJO"}),
    ("VERDE_CRA23",    {"S1": "VERDE",    "S2": "VERDE",    "S3": "ROJO",     "S4": "ROJO"}),
    ("AMARILLO_CRA23", {"S1": "AMARILLO", "S2": "AMARILLO", "S3": "ROJO",     "S4": "ROJO"}),
    ("TODO_ROJO",      None),   # transicion obligatoria: no se pregunta (ya se reviso en el paso 1)
    ("VERDE_DG15",     {"S1": "ROJO",     "S2": "ROJO",     "S3": "VERDE",    "S4": "VERDE"}),
    ("AMARILLO_DG15",  {"S1": "ROJO",     "S2": "ROJO",     "S3": "AMARILLO", "S4": "AMARILLO"}),
    ("TODO_ROJO",      None),   # se deja el cruce en rojo al terminar
]
ESPERA_LISTO_S = 6.0
ESPERA_OK_S = 2.0
PERIODO_LATIDO_S = 1.0


class Latido(threading.Thread):
    """Envia la luz actual cada segundo (el ESP32 lo exige) y guarda todo lo que responde el ESP32."""

    def __init__(self, conexion, luz_inicial):
        super().__init__(daemon=True)
        self.conexion = conexion
        self.luz = luz_inicial
        self.mensajes = []          # (segundos desde el inicio, texto)
        self.candado = threading.Lock()
        self.detener = threading.Event()
        self.inicio = time.time()

    def poner_luz(self, luz):
        with self.candado:
            self.luz = luz
            self.conexion.enviar_luz(luz)

    def run(self):
        while not self.detener.is_set():
            with self.candado:
                self.conexion.enviar_luz(self.luz)
            limite = time.time() + PERIODO_LATIDO_S
            while time.time() < limite and not self.detener.is_set():
                mensaje = self.conexion.leer_mensaje()
                if mensaje:
                    self.mensajes.append((round(time.time() - self.inicio, 2), mensaje.texto))


def esperar_listo(conexion):
    limite = time.time() + ESPERA_LISTO_S
    while time.time() < limite:
        mensaje = conexion.leer_mensaje()
        if mensaje and mensaje.tipo == "LISTO":
            return True
    return False


def esperar_ok(latido, luz, desde_indice):
    limite = time.time() + ESPERA_OK_S
    while time.time() < limite:
        for _, texto in latido.mensajes[desde_indice:]:
            if texto.startswith("OK") and texto.endswith(luz):
                return True
            if texto.startswith("ERROR") or texto.startswith("MODO INTERMITENTE"):
                return False
        time.sleep(0.05)
    return False


def preguntar_si_no(texto):
    while True:
        respuesta = input(texto + " [s/n]: ").strip().lower()
        if respuesta in ("s", "n"):
            return respuesta == "s"
        print("   Escriba s o n.")


def main():
    parser = argparse.ArgumentParser(description="Prueba visual de los 4 semaforos de la maqueta")
    parser.add_argument("--puerto", default="COM4")
    argumentos = parser.parse_args()

    fecha = datetime.now()
    print("=== PRUEBA VISUAL DE LOS 4 SEMAFOROS ===")
    nota = input("Nota de esta prueba (ej: 'antes de desarmar', 'despues de armar'); Enter para omitir: ").strip()

    conexion = ConexionESP32(argumentos.puerto)
    if not esperar_listo(conexion):
        print("ERROR: el ESP32 no envio LISTO. Revise el cable USB, el puerto y que tenga el firmware semaforo_obediente.")
        conexion.cerrar()
        sys.exit(1)
    print(f"Conectado a {argumentos.puerto}: ESP32 LISTO (todo en rojo).\n")

    latido = Latido(conexion, "TODO_ROJO")
    latido.start()

    resultados = []     # (semaforo, color, correcto, observacion, luz_del_cruce)
    luz_anterior = "TODO_ROJO"
    for numero, (luz, esperado) in enumerate(PASOS, start=1):
        if luz != luz_anterior:
            indice = len(latido.mensajes)
            latido.poner_luz(luz)
            if not esperar_ok(latido, luz, indice):
                print(f"ERROR: el ESP32 no confirmo {luz}. Mensajes recibidos:")
                for t, texto in latido.mensajes[indice:]:
                    print(f"   [{t} s] {texto}")
                latido.detener.set()
                conexion.cerrar()
                sys.exit(1)
            luz_anterior = luz
        if esperado is None:
            time.sleep(1.0)
            continue

        print(f"--- Paso {numero}: luz del cruce {luz} (se queda encendida hasta que responda) ---")
        for semaforo, color in esperado.items():
            correcto = preguntar_si_no(f"  {semaforo} ({SEMAFOROS[semaforo]}): solo el {color} encendido?")
            observacion = ""
            if not correcto:
                observacion = input("     Que vio? (ej: apagado, prende amarillo, dos LEDs): ").strip()
            resultados.append((semaforo, color, correcto, observacion, luz))
        print()

    latido.detener.set()
    latido.join(timeout=2)
    conexion.cerrar()

    # Resumen por LED: un LED queda OK solo si todas sus revisiones fueron correctas.
    resumen = {}
    for semaforo, color, correcto, observacion, luz in resultados:
        clave = (semaforo, color)
        anterior = resumen.get(clave, (True, []))
        notas = anterior[1] + ([f"{luz}: {observacion or 'sin detalle'}"] if not correcto else [])
        resumen[clave] = (anterior[0] and correcto, notas)

    lineas = [
        "Prueba visual de los 4 semaforos (scripts/probar_semaforos_visual.py)",
        f"Fecha: {fecha:%Y-%m-%d %H:%M}",
        f"Puerto: {argumentos.puerto} | Firmware: hardware/esp32/semaforo_obediente",
        f"Nota: {nota or '-'}",
        "",
        "Semaforo  Acceso          ROJO      AMARILLO  VERDE",
    ]
    for semaforo, acceso in SEMAFOROS.items():
        celdas = []
        for color in ("ROJO", "AMARILLO", "VERDE"):
            correcto, _ = resumen[(semaforo, color)]
            celdas.append(("OK" if correcto else "FALLA").ljust(10))
        lineas.append(f"{semaforo.ljust(10)}{acceso.ljust(16)}{''.join(celdas)}")
    fallas = [(clave, notas) for clave, (correcto, notas) in resumen.items() if not correcto]
    lineas.append("")
    if fallas:
        lineas.append(f"RESULTADO: {len(fallas)} LED(s) con falla")
        for (semaforo, color), notas in fallas:
            lineas.append(f"  {semaforo} {color}: " + " | ".join(notas))
        lineas.append("Revise el cable de ese LED en hardware/esp32/conexiones.md (colores de cada modulo).")
    else:
        lineas.append("RESULTADO: los 12 LEDs OK")
    lineas.append("")
    lineas.append("Respuestas una por una:")
    for semaforo, color, correcto, observacion, luz in resultados:
        lineas.append(f"  {luz:15} {semaforo} {color:9} {'OK' if correcto else 'FALLA'} {observacion}")
    lineas.append("")
    lineas.append("Mensajes del ESP32:")
    lineas += [f"  [{t} s] {texto}" for t, texto in latido.mensajes]

    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    reporte = CARPETA_RESULTADOS / f"prueba_visual_semaforos_{fecha:%Y-%m-%d_%H%M}.txt"
    reporte.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    nuevo = not REGISTRO_CSV.exists()
    with REGISTRO_CSV.open("a", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        if nuevo:
            escritor.writerow(["fecha", "nota", "semaforo", "acceso", "color", "resultado", "observacion"])
        for (semaforo, color), (correcto, notas) in resumen.items():
            escritor.writerow([f"{fecha:%Y-%m-%d %H:%M}", nota, semaforo, SEMAFOROS[semaforo], color,
                               "OK" if correcto else "FALLA", " | ".join(notas)])

    print("\n".join(lineas[:12 + len(fallas)]))
    print(f"\nReporte guardado en {reporte.relative_to(CARPETA_TESIS)}")
    print(f"Historial actualizado: {REGISTRO_CSV.relative_to(CARPETA_TESIS)}")
    print("Al cerrar, el ESP32 queda en intermitente (SIN_PC): es lo esperado sin Python.")


if __name__ == "__main__":
    main()
