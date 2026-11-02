"""
Comunicacion PC <-> ESP32 del semaforo de la maqueta por puerto serie (USB). Pasos 10.3 a 10.5.

Protocolo VIGENTE (10.5a, firmware hardware/esp32/semaforo_obediente): Python decide la luz y la envia cada segundo.
  PC -> ESP32: LUZ <VERDE_CRA23|AMARILLO_CRA23|VERDE_DG15|AMARILLO_DG15|TODO_ROJO>   (metodo enviar_luz)
  ESP32 -> PC: LISTO | OK <t_ms> <luz> | AUTO <t_ms> <luz> | MODO INTERMITENTE <motivo> | MODO NORMAL | ERROR ...

Protocolo ANTERIOR (10.3/10.4, firmware semaforo_serial y semaforo_failsafe; se conserva enviar_verde para poder
repetir esas pruebas). Se reemplazo porque el agente decide MANTENER/CAMBIAR cada 5 s y no conoce la duracion del verde
por adelantado.

Protocolo: ver hardware/esp32/semaforo_failsafe/semaforo_failsafe.ino (10.4; extiende el de semaforo_serial.ino).
  ESP32 -> PC: LISTO | FASE <t_s> <ciclo> <nombre> <s> | SOLICITUD <EJE> | OK ... | AJUSTADO ... | SIN_RESPUESTA ... | MODO INTERMITENTE <motivo> | MODO NORMAL | ERROR ...
  PC -> ESP32: VERDE <EJE> <s>

El ESP32 es quien aplica los limites de seguridad; esta clase solo transporta mensajes.
Requiere: pyserial  (pip install pyserial)
"""
import time
from dataclasses import dataclass

import serial

EJES_VALIDOS = ("CRA23", "DG15")
LUCES_VALIDAS = ("VERDE_CRA23", "AMARILLO_CRA23", "VERDE_DG15", "AMARILLO_DG15", "TODO_ROJO")


@dataclass
class MensajeESP32:
    tipo: str            # primera palabra: FASE, SOLICITUD, OK, AJUSTADO, SIN_RESPUESTA, ERROR, MODO, LISTO u OTRO
    partes: list         # palabras restantes
    texto: str           # linea completa


class ConexionESP32:
    def __init__(self, puerto: str, baudios: int = 115200, espera_lectura_s: float = 0.1):
        self.puerto_serie = serial.Serial(puerto, baudios, timeout=espera_lectura_s)
        self.reiniciar()

    def reiniciar(self):
        """Reinicia el ESP32 con las lineas RTS/DTR del adaptador USB (como hace Arduino IDE al subir un programa).
        Asi la prueba siempre empieza desde el inicio del ciclo y el primer mensaje util es "LISTO"."""
        self.puerto_serie.dtr = False   # GPIO0 en alto: arranque normal (no modo de carga)
        self.puerto_serie.rts = True    # EN en bajo: ESP32 en reinicio
        time.sleep(0.1)
        self.puerto_serie.rts = False   # suelta EN: el ESP32 arranca
        self.puerto_serie.reset_input_buffer()

    def leer_mensaje(self):
        """Devuelve el siguiente MensajeESP32, o None si no llego nada en el tiempo de espera."""
        linea_bytes = self.puerto_serie.readline()
        if not linea_bytes:
            return None
        texto = linea_bytes.decode("utf-8", errors="replace").strip()
        if not texto:
            return None
        palabras = texto.split()
        tipos_conocidos = {"LISTO", "FASE", "SOLICITUD", "OK", "AJUSTADO", "SIN_RESPUESTA", "ERROR", "MODO", "AUTO"}
        tipo = palabras[0] if palabras[0] in tipos_conocidos else "OTRO"   # OTRO = mensajes de arranque del ESP32
        return MensajeESP32(tipo=tipo, partes=palabras[1:], texto=texto)

    def enviar_verde(self, eje: str, segundos: int):
        if eje not in EJES_VALIDOS:
            raise ValueError(f"Eje no valido: {eje}. Use uno de {EJES_VALIDOS}")
        self.enviar_texto(f"VERDE {eje} {int(segundos)}")

    def enviar_luz(self, luz: str):
        """luz: nombre del protocolo (VERDE_CRA23...) o el de SafetyGuard.fase_actual() (verde_cra23...)."""
        luz = luz.upper()
        if luz not in LUCES_VALIDAS:
            raise ValueError(f"Luz no valida: {luz}. Use una de {LUCES_VALIDAS}")
        self.enviar_texto(f"LUZ {luz}")

    def enviar_texto(self, texto: str):
        """Envia una linea tal cual (se usa tambien para probar que el ESP32 rechaza comandos invalidos)."""
        self.puerto_serie.write((texto + "\n").encode("utf-8"))

    def cerrar(self):
        self.puerto_serie.close()
