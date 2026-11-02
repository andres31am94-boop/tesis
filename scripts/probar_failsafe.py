"""
Prueba del paso 10.4 (fail-safe): que hace el ESP32 cuando Python deja de responder y cuando vuelve.

Secuencia (todo con los mensajes del propio ESP32; tiempos reales, ~6.5 minutos):
  A. Python responde normal 2 veces (CRA23 30 s, DG15 15 s)                       -> OK
  B. Python deja de responder (simula que el programa del PC se colgo)
       verdes 1 a 4 sin respuesta -> plan real (55 / 20 s)                        -> SIN_RESPUESTA ... 1..4
       5.o verde sin respuesta    -> intermitente (amarillo Cra 23, rojo Dg 15)  -> MODO INTERMITENTE SIN_PC
  C. Se deja destellar 15 s (mirar los LEDs: 1 destello por segundo)
  D. Python vuelve: responde VERDE CRA23 30 a la siguiente solicitud
       -> MODO NORMAL, todo rojo 20 s, Cra 23 verde 30 s

Uso (desde la carpeta tesis, con Arduino IDE / Monitor Serie CERRADO):
  .\\.venv\\Scripts\\python.exe scripts\\probar_failsafe.py --puerto COM4
"""
import argparse
import sys
import time
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))  # para importar src.*

from src.communication.esp32_serial import ConexionESP32  # noqa: E402

RESPUESTAS_NORMALES = [("CRA23", 30), ("DG15", 15)]
VERDES_PLAN_ESPERADOS = [("CRA23", 55), ("DG15", 20), ("CRA23", 55), ("DG15", 20)]
SEGUNDOS_EN_INTERMITENTE = 15
VERDE_AL_VOLVER_S = 30
LIMITE_PRUEBA_S = 540


def main():
    parser = argparse.ArgumentParser(description="Prueba del modo a prueba de fallas del ESP32 (paso 10.4)")
    parser.add_argument("--puerto", required=True, help="Puerto serie del ESP32, por ejemplo COM4")
    argumentos = parser.parse_args()

    conexion = ConexionESP32(argumentos.puerto)
    print(f"Conectado a {argumentos.puerto}. Esperando LISTO...")

    etapa = "A_NORMAL"
    respuestas_enviadas = 0
    sin_respuesta_vistos = []        # (eje, segundos, contador)
    inicio_intermitente_pc = None
    resultados = []
    inicio = time.time()

    def registrar(descripcion, correcto):
        resultados.append((descripcion, correcto))
        print(f"            >>> [{'OK' if correcto else 'FALLA'}] {descripcion}")

    try:
        while time.time() - inicio < LIMITE_PRUEBA_S:
            mensaje = conexion.leer_mensaje()
            ahora = time.time() - inicio
            if mensaje is not None:
                print(f"[PC {ahora:6.1f} s] ESP32: {mensaje.texto}")

            if etapa == "A_NORMAL" and mensaje is not None and mensaje.tipo == "SOLICITUD":
                eje, segundos = RESPUESTAS_NORMALES[respuestas_enviadas]
                print(f"            PC -> ESP32: VERDE {eje} {segundos}")
                conexion.enviar_verde(eje, segundos)
                respuestas_enviadas += 1
                if respuestas_enviadas == len(RESPUESTAS_NORMALES):
                    etapa = "B_SIN_PC"
                    print("            PC: desde ahora NO responde (simula falla del PC)")

            elif etapa == "B_SIN_PC" and mensaje is not None:
                if mensaje.tipo == "SIN_RESPUESTA":
                    sin_respuesta_vistos.append((mensaje.partes[0], int(mensaje.partes[1]), int(mensaje.partes[2])))
                elif mensaje.tipo == "MODO" and mensaje.partes[0] == "INTERMITENTE":
                    esperado = [(eje, s, i + 1) for i, (eje, s) in enumerate(VERDES_PLAN_ESPERADOS)]
                    registrar(f"Plan real durante la falla: esperado {esperado}, visto {sin_respuesta_vistos}",
                              sin_respuesta_vistos == esperado)
                    registrar(f"Pasa a intermitente por SIN_PC (visto: {' '.join(mensaje.partes)})",
                              mensaje.partes[1:] == ["SIN_PC"])
                    etapa = "C_INTERMITENTE"
                    inicio_intermitente_pc = time.time()
                    print(f"            PC: mire los LEDs {SEGUNDOS_EN_INTERMITENTE} s: amarillo Cra 23 y rojo Dg 15 destellando")

            elif etapa == "C_INTERMITENTE":
                if time.time() - inicio_intermitente_pc >= SEGUNDOS_EN_INTERMITENTE:
                    etapa = "D_VUELVE"
                    print("            PC: vuelve a responder")

            elif etapa == "D_VUELVE" and mensaje is not None:
                if mensaje.tipo == "SOLICITUD" and mensaje.partes[0] == "CRA23":
                    print(f"            PC -> ESP32: VERDE CRA23 {VERDE_AL_VOLVER_S}")
                    conexion.enviar_verde("CRA23", VERDE_AL_VOLVER_S)
                    etapa = "E_RECUPERACION"

            elif etapa == "E_RECUPERACION" and mensaje is not None:
                if mensaje.tipo == "MODO":
                    registrar("Sale de intermitente (MODO NORMAL)", mensaje.partes == ["NORMAL"])
                elif mensaje.tipo == "FASE" and mensaje.partes[2] == "TODO_ROJO_PEATONES":
                    registrar(f"Transicion segura: todo rojo {mensaje.partes[3]} s antes del verde",
                              mensaje.partes[3] == "20")
                elif mensaje.tipo == "FASE" and mensaje.partes[2] == "CRA23_VERDE":
                    registrar(f"Retoma con Cra 23 verde {mensaje.partes[3]} s (pedido {VERDE_AL_VOLVER_S})",
                              int(mensaje.partes[3]) == VERDE_AL_VOLVER_S)
                    break
    finally:
        conexion.cerrar()

    print("\n===== RESULTADO =====")
    for descripcion, correcto in resultados:
        print(f"  [{'OK' if correcto else 'FALLA'}] {descripcion}")
    esperados = 5
    if len(resultados) < esperados:
        print(f"  [FALLA] Solo se verificaron {len(resultados)} de {esperados} casos (etapa final: {etapa})")
    todo_bien = len(resultados) >= esperados and all(correcto for _, correcto in resultados)
    print("PRUEBA SUPERADA" if todo_bien else "PRUEBA CON FALLAS")
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
