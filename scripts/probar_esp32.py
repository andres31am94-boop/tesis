"""
Prueba del paso 10.3: Python decide la duracion de cada verde y el ESP32 la ejecuta respetando sus limites.

Que comprueba (automaticamente, con los mensajes del propio ESP32):
  1. Un comando invalido se rechaza con ERROR.
  2. Un verde dentro de los limites se acepta (OK) y el verde dura eso.
  3. Un verde fuera de los limites se recorta (AJUSTADO) al maximo/minimo.
  4. Si Python no responde, el ESP32 usa el plan real (SIN_RESPUESTA).

Respuestas programadas (una por SOLICITUD, en orden):
  CRA23 30  -> OK, 30 s
  DG15 15   -> OK, 15 s
  CRA23 100 -> AJUSTADO a 70 s (maximo de la Cra 23)
  DG15 5    -> AJUSTADO a 15 s (minimo de la Dg 15)
  CRA23 ... -> no responde -> SIN_RESPUESTA, plan real 55 s
Duracion aproximada: 4.5 minutos.

Uso (desde la carpeta tesis, con el Monitor Serie de Arduino CERRADO):
  .\\.venv\\Scripts\\python.exe scripts\\probar_esp32.py --puerto COM4
"""
import argparse
import sys
import time
from pathlib import Path

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))  # para importar src.*

from src.communication.esp32_serial import ConexionESP32  # noqa: E402

# (eje que se espera en la solicitud, segundos que se envian, segundos que debe aplicar el ESP32)
RESPUESTAS_PROGRAMADAS = [
    ("CRA23", 30, 30),
    ("DG15", 15, 15),
    ("CRA23", 100, 70),
    ("DG15", 5, 15),
    ("CRA23", None, 55),   # None = no responder
]
VERDE_POR_FASE = {"CRA23_VERDE": "CRA23", "DG15_VERDE": "DG15"}
LIMITE_PRUEBA_S = 360


def main():
    parser = argparse.ArgumentParser(description="Prueba de comunicacion PC -> ESP32 (paso 10.3)")
    parser.add_argument("--puerto", required=True, help="Puerto serie del ESP32, por ejemplo COM4")
    argumentos = parser.parse_args()

    conexion = ConexionESP32(argumentos.puerto)
    print(f"Conectado a {argumentos.puerto}. Esperando LISTO...")

    indice_respuesta = 0
    verdes_esperados = []        # (eje, segundos) en el orden en que deben ocurrir
    resultados = []              # (descripcion, paso_la_prueba)
    comando_invalido_enviado = False
    inicio = time.time()

    try:
        while time.time() - inicio < LIMITE_PRUEBA_S:
            mensaje = conexion.leer_mensaje()
            if mensaje is None:
                continue
            print(f"[PC {time.time() - inicio:6.1f} s] ESP32: {mensaje.texto}")

            if mensaje.tipo == "LISTO" and not comando_invalido_enviado:
                print("            PC -> ESP32: HOLA (comando invalido a proposito)")
                conexion.enviar_texto("HOLA")
                comando_invalido_enviado = True

            elif mensaje.tipo == "ERROR" and comando_invalido_enviado and len(resultados) == 0:
                resultados.append(("Comando invalido rechazado con ERROR", True))

            elif mensaje.tipo == "SOLICITUD":
                if indice_respuesta >= len(RESPUESTAS_PROGRAMADAS):
                    break   # ya se probaron todos los casos
                eje_esperado, segundos, aplicado_esperado = RESPUESTAS_PROGRAMADAS[indice_respuesta]
                eje_pedido = mensaje.partes[0]
                if eje_pedido != eje_esperado:
                    resultados.append((f"Solicitud {indice_respuesta + 1}: se esperaba {eje_esperado}, llego {eje_pedido}", False))
                if segundos is None:
                    print("            PC: (no responde a proposito)")
                else:
                    print(f"            PC -> ESP32: VERDE {eje_pedido} {segundos}")
                    conexion.enviar_verde(eje_pedido, segundos)
                verdes_esperados.append((eje_pedido, aplicado_esperado))
                indice_respuesta += 1

            elif mensaje.tipo == "FASE" and mensaje.partes[2] in VERDE_POR_FASE and verdes_esperados:
                eje = VERDE_POR_FASE[mensaje.partes[2]]
                duracion = int(mensaje.partes[3])
                eje_esperado, duracion_esperada = verdes_esperados.pop(0)
                correcto = (eje == eje_esperado and duracion == duracion_esperada)
                resultados.append((f"Verde {eje}: esperado {duracion_esperada} s, ESP32 aplico {duracion} s", correcto))
                if len(resultados) >= 1 + len(RESPUESTAS_PROGRAMADAS):
                    break
    finally:
        conexion.cerrar()

    print("\n===== RESULTADO =====")
    for descripcion, correcto in resultados:
        print(f"  [{'OK' if correcto else 'FALLA'}] {descripcion}")
    esperados = 1 + len(RESPUESTAS_PROGRAMADAS)
    if len(resultados) < esperados:
        print(f"  [FALLA] Solo se verificaron {len(resultados)} de {esperados} casos (tiempo agotado o desconexion)")
    todo_bien = len(resultados) >= esperados and all(correcto for _, correcto in resultados)
    print("PRUEBA SUPERADA" if todo_bien else "PRUEBA CON FALLAS")
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
