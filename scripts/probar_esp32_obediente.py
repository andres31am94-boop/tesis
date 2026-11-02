"""
Prueba del paso 10.5a: ESP32 OBEDIENTE (Python decide la luz; el ESP32 la enciende y solo tiene 2 frenos).

Partes (comprobadas con los mensajes del propio ESP32; dura ~1 minuto):
  1. Obedece: secuencia normal de luces enviada cada segundo -> un OK por cada cambio.
     Se mide la LATENCIA (envio de la orden -> confirmacion OK del ESP32) con el reloj del PC.
  2. Nombre de luz desconocido -> ERROR y la luz no cambia.
  3. Freno 1 (conflicto): de VERDE_DG15 directo a VERDE_CRA23 -> ERROR, amarillo automatico de la Dg 15,
     intermitente CONFLICTO, y no acepta seguir (hay que reiniciar).
  4. Freno 2 (Python se calla) con la Cra 23 en verde -> amarillo automatico ~5 s despues del ultimo mensaje,
     intermitente SIN_PC ~3 s despues.
  5. Recuperacion: en intermitente rechaza un verde; acepta TODO_ROJO -> MODO NORMAL; luego obedece de nuevo.

Uso (desde la carpeta tesis, con Arduino IDE / Monitor Serie CERRADO):
  .\\.venv\\Scripts\\python.exe scripts\\probar_esp32_obediente.py --puerto COM4
"""
import argparse
import statistics
import sys
import time
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))  # para importar src.*

from src.communication.esp32_serial import ConexionESP32  # noqa: E402

SECUENCIA_NORMAL = [("VERDE_DG15", 5), ("AMARILLO_DG15", 3), ("TODO_ROJO", 3),
                    ("VERDE_CRA23", 5), ("AMARILLO_CRA23", 3), ("VERDE_DG15", 3)]
WATCHDOG_ESPERADO_S = 5.0
AMARILLO_ESPERADO_S = 3.0
TOLERANCIA_S = 0.5

inicio_prueba = time.time()
resultados = []


def reloj():
    return time.time() - inicio_prueba


def registrar(descripcion, correcto):
    resultados.append((descripcion, correcto))
    print(f"            >>> [{'OK' if correcto else 'FALLA'}] {descripcion}")


def escuchar(conexion, segundos):
    """Lee mensajes durante 'segundos'. Devuelve [(tiempo_pc, mensaje)]."""
    recibidos = []
    fin = time.time() + segundos
    while time.time() < fin:
        mensaje = conexion.leer_mensaje()
        if mensaje is not None:
            recibidos.append((reloj(), mensaje))
            print(f"[PC {reloj():6.2f} s] ESP32: {mensaje.texto}")
    return recibidos


def mantener_luz(conexion, luz, segundos):
    """Envia la luz cada segundo durante 'segundos' (como hara el controlador). Devuelve (t_primer_envio, mensajes)."""
    recibidos = []
    t_primer_envio = None
    for _ in range(segundos):
        if t_primer_envio is None:
            t_primer_envio = reloj()
            print(f"[PC {t_primer_envio:6.2f} s] PC -> ESP32: LUZ {luz}")
        conexion.enviar_luz(luz)
        recibidos += escuchar(conexion, 1.0)
    return t_primer_envio, recibidos


def buscar(recibidos, tipo, contiene=""):
    for t, mensaje in recibidos:
        if mensaje.tipo == tipo and contiene in mensaje.texto:
            return t, mensaje
    return None, None


def esperar_listo(conexion):
    recibidos = escuchar(conexion, 3.0)
    t, _ = buscar(recibidos, "LISTO")
    return t is not None


def main():
    parser = argparse.ArgumentParser(description="Prueba del ESP32 obediente (paso 10.5a)")
    parser.add_argument("--puerto", required=True, help="Puerto serie del ESP32, por ejemplo COM4")
    argumentos = parser.parse_args()

    conexion = ConexionESP32(argumentos.puerto)
    try:
        print(f"Conectado a {argumentos.puerto}.")
        registrar("Arranque: el ESP32 envia LISTO", esperar_listo(conexion))

        # ---- 1. Obedece + latencia ----
        print("\n--- 1. Secuencia normal (una orden por segundo) ---")
        latencias_ms = []
        oks_correctos = 0
        for luz, segundos in SECUENCIA_NORMAL:
            t_envio, recibidos = mantener_luz(conexion, luz, segundos)
            t_ok, _ = buscar(recibidos, "OK", luz)
            if t_ok is not None:
                oks_correctos += 1
                latencias_ms.append((t_ok - t_envio) * 1000)
        registrar(f"Obedece la secuencia: {oks_correctos}/{len(SECUENCIA_NORMAL)} cambios confirmados con OK",
                  oks_correctos == len(SECUENCIA_NORMAL))
        if latencias_ms:
            print(f"            Latencia orden->OK (ms): media {statistics.mean(latencias_ms):.1f}, "
                  f"maxima {max(latencias_ms):.1f}, n={len(latencias_ms)}  (incluye la lectura cada 0.1 s del PC)")

        # ---- 2. Luz desconocida ----
        print("\n--- 2. Nombre desconocido ---")
        conexion.enviar_texto("LUZ AZUL")
        print(f"[PC {reloj():6.2f} s] PC -> ESP32: LUZ AZUL")
        recibidos = escuchar(conexion, 1.0)
        t_err, _ = buscar(recibidos, "ERROR", "desconocida")
        t_ok, _ = buscar(recibidos, "OK")
        registrar("Luz desconocida rechazada (ERROR) sin cambiar la luz", t_err is not None and t_ok is None)

        # ---- 3. Conflicto ----
        print("\n--- 3. Freno 1: VERDE_DG15 -> VERDE_CRA23 sin amarillo ---")
        conexion.enviar_luz("VERDE_DG15")   # latido: sigue en verde Dg 15
        t_envio = reloj()
        conexion.enviar_luz("VERDE_CRA23")
        print(f"[PC {t_envio:6.2f} s] PC -> ESP32: LUZ VERDE_CRA23 (prohibido a proposito)")
        recibidos = escuchar(conexion, 4.5)
        t_err, _ = buscar(recibidos, "ERROR", "prohibida")
        t_auto, _ = buscar(recibidos, "AUTO", "AMARILLO_DG15")
        t_int, _ = buscar(recibidos, "MODO", "CONFLICTO")
        registrar("Transicion prohibida rechazada (ERROR)", t_err is not None)
        registrar("Amarillo automatico de la Dg 15 antes del intermitente", t_auto is not None)
        amarillo_s = (t_int - t_auto) if (t_int and t_auto) else None
        registrar(f"Intermitente CONFLICTO tras el amarillo (amarillo medido: {amarillo_s and round(amarillo_s, 2)} s)",
                  amarillo_s is not None and abs(amarillo_s - AMARILLO_ESPERADO_S) <= TOLERANCIA_S)
        print("            Mire los LEDs: amarillo Cra 23 y rojo Dg 15 destellando")
        conexion.enviar_luz("TODO_ROJO")
        recibidos = escuchar(conexion, 3.0)
        t_err, _ = buscar(recibidos, "ERROR", "reinicie")
        registrar("Intermitente por CONFLICTO no se recupera sin reiniciar", t_err is not None)

        # ---- 4. Python se calla ----
        print("\n--- 4. Freno 2: Python deja de enviar con la Cra 23 en verde ---")
        conexion.reiniciar()
        registrar("Reinicio por RTS: LISTO", esperar_listo(conexion))
        mantener_luz(conexion, "VERDE_CRA23", 3)
        t_ultimo = reloj() - 1.0   # el ultimo envio fue al comienzo del ultimo segundo escuchado
        print(f"            PC: deja de enviar (ultimo mensaje en t={t_ultimo:.2f} s)")
        recibidos = escuchar(conexion, 10.0)
        t_auto, _ = buscar(recibidos, "AUTO", "AMARILLO_CRA23")
        t_int, _ = buscar(recibidos, "MODO", "SIN_PC")
        espera_s = (t_auto - t_ultimo) if t_auto else None
        registrar(f"Amarillo automatico de la Cra 23 tras el silencio (medido: {espera_s and round(espera_s, 2)} s, "
                  f"esperado {WATCHDOG_ESPERADO_S} s)",
                  espera_s is not None and abs(espera_s - WATCHDOG_ESPERADO_S) <= TOLERANCIA_S + 0.2)
        amarillo_s = (t_int - t_auto) if (t_int and t_auto) else None
        registrar(f"Intermitente SIN_PC tras el amarillo (amarillo medido: {amarillo_s and round(amarillo_s, 2)} s)",
                  amarillo_s is not None and abs(amarillo_s - AMARILLO_ESPERADO_S) <= TOLERANCIA_S)

        # ---- 5. Recuperacion ----
        print("\n--- 5. Recuperacion ---")
        conexion.enviar_luz("VERDE_DG15")
        print(f"[PC {reloj():6.2f} s] PC -> ESP32: LUZ VERDE_DG15 (debe rechazarse en intermitente)")
        recibidos = escuchar(conexion, 1.0)
        t_err, _ = buscar(recibidos, "ERROR", "TODO_ROJO")
        registrar("En intermitente rechaza un verde directo", t_err is not None)
        _, recibidos = mantener_luz(conexion, "TODO_ROJO", 2)
        t_normal, _ = buscar(recibidos, "MODO", "NORMAL")
        registrar("Con TODO_ROJO vuelve a MODO NORMAL", t_normal is not None)
        _, recibidos = mantener_luz(conexion, "VERDE_DG15", 3)
        t_ok, _ = buscar(recibidos, "OK", "VERDE_DG15")
        registrar("Despues de recuperarse obedece de nuevo (OK VERDE_DG15)", t_ok is not None)
        conexion.enviar_luz("AMARILLO_DG15")
        escuchar(conexion, 1.0)
        conexion.enviar_luz("TODO_ROJO")
        escuchar(conexion, 0.5)
    finally:
        conexion.cerrar()

    print("\n===== RESULTADO =====")
    for descripcion, correcto in resultados:
        print(f"  [{'OK' if correcto else 'FALLA'}] {descripcion}")
    todo_bien = all(correcto for _, correcto in resultados)
    print("PRUEBA SUPERADA" if todo_bien else "PRUEBA CON FALLAS")
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
