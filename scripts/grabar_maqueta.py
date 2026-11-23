"""
Graba videos de la maqueta con la camara del lazo (para reentrenar YOLO con imagenes del dominio real).

Por que: hotwheels_v2 se entreno con fotos del cruce en el piso. En la maqueta (2026-11-23) confundio casas con carros
y no vio un carro azul oscuro. Hay que ensenarle ESTA maqueta: casas, gris de la calle, sombras del techo, carros oscuros.

Dos SESIONES separadas (ideal: dias o luces distintas): A = entrenamiento, B = validacion. Los cuadros de un mismo
video nunca se reparten entre entrenamiento y validacion (se separa por video, como en hotwheels_v2).

Uso: GRABAR_MAQUETA.bat (pregunta sesion, escena y luz). Tecla q en la ventana = terminar antes.
Salida (NO se sube a GitHub: data/raw/ esta en .gitignore; pueden salir manos):
  data/raw/maqueta/videos/sesion_<A|B>/<fecha_hora>_<escena>.mp4  +  .json con duracion, cuadros y fps medidos.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

CARPETA_TESIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_TESIS))
from src.common.registro_computo import registrar_ejecucion  # noqa: E402

CARPETA_VIDEOS = CARPETA_TESIS / "data" / "raw" / "maqueta" / "videos"
INDICE_CAMARA = 1                 # DroidCam por Media Foundation (scripts/listar_camaras.py, 2026-11-23)
ANCHO, ALTO, FPS_PEDIDO = 1920, 1080, 30
ESCENAS = {
    "1": ("vacia", 30, "tabla sin carros (fondo: casas, sombras)"),
    "2": ("cola_cra23", 120, "colas en norte y sur que avanzan y cruzan"),
    "3": ("cola_dg15", 120, "colas en este y oeste que avanzan y cruzan"),
    "4": ("mixto", 180, "carros en todos los brazos, cruzando el centro y saliendo"),
    "5": ("oscuros", 120, "sobre todo carros oscuros, en todas las zonas"),
    "6": ("manos", 60, "mover carros con la mano a proposito (que aprenda que la mano no es carro)"),
    "7": ("otra_luz", 120, "trafico mixto con otra luz (lampara de lado, luz del dia...)"),
}


def preguntar(texto, opciones=None):
    while True:
        respuesta = input(texto).strip()
        if opciones is None or respuesta in opciones:
            return respuesta
        print(f"   Opciones validas: {', '.join(opciones)}")


def main():
    registrar_ejecucion()
    print("=== GRABACION DE LA MAQUETA (reentrenamiento de YOLO) ===")
    sesion = preguntar("Sesion (A = entrenamiento, B = validacion): ", ["A", "B", "a", "b"]).upper()
    print("Escenas:")
    for clave, (nombre, segundos, descripcion) in ESCENAS.items():
        print(f"  {clave}. {nombre:11} {segundos:>4} s  {descripcion}")
    escena, duracion_s, descripcion = ESCENAS[preguntar("Numero de escena: ", list(ESCENAS))]
    luz = preguntar("Luz (ej: 'techo', 'techo + lampara izquierda', 'dia'): ") or "-"
    carros = preguntar("Cuantos carros usa (Enter si no aplica): ") or "-"

    captura = cv2.VideoCapture(INDICE_CAMARA, cv2.CAP_MSMF)
    captura.set(cv2.CAP_PROP_FRAME_WIDTH, ANCHO)
    captura.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTO)
    if not captura.isOpened():
        print("ERROR: no se pudo abrir la camara 1 (msmf). Revise que DroidCam Client este abierto y transmitiendo.")
        sys.exit(1)
    correcto, cuadro = captura.read()
    if not correcto:
        print("ERROR: la camara abre pero no entrega imagen.")
        sys.exit(1)
    alto, ancho = cuadro.shape[:2]

    fecha = datetime.now()
    carpeta = CARPETA_VIDEOS / f"sesion_{sesion}"
    carpeta.mkdir(parents=True, exist_ok=True)
    base = carpeta / f"{fecha:%Y%m%d_%H%M%S}_{escena}"
    escritor = cv2.VideoWriter(str(base.with_suffix(".mp4")), cv2.VideoWriter_fourcc(*"mp4v"), FPS_PEDIDO, (ancho, alto))

    print(f"\nGrabando '{escena}' {duracion_s} s ... (q en la ventana para terminar antes)")
    for cuenta in (3, 2, 1):
        print(f"  empieza en {cuenta}...")
        time.sleep(1)
    inicio, cuadros = time.monotonic(), 0
    while time.monotonic() - inicio < duracion_s:
        correcto, cuadro = captura.read()
        if not correcto:
            print("AVISO: se perdio un cuadro de la camara")
            continue
        escritor.write(cuadro)
        cuadros += 1
        transcurrido = time.monotonic() - inicio
        vista = cv2.resize(cuadro, (960, 540))
        cv2.putText(vista, f"REC {escena}  {transcurrido:5.1f}/{duracion_s} s", (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        cv2.imshow("Grabacion maqueta (q = terminar)", vista)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    duracion_real = time.monotonic() - inicio
    captura.release()
    escritor.release()
    cv2.destroyAllWindows()

    datos = {"fecha": f"{fecha:%Y-%m-%d %H:%M:%S}", "sesion": sesion, "escena": escena, "descripcion": descripcion,
             "luz": luz, "carros": carros, "resolucion": [ancho, alto], "duracion_s": round(duracion_real, 1),
             "cuadros": cuadros, "fps_medido": round(cuadros / duracion_real, 2), "fps_archivo": FPS_PEDIDO,
             "camara": f"indice {INDICE_CAMARA}, Media Foundation (DroidCam)"}
    base.with_suffix(".json").write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nListo: {base.with_suffix('.mp4').relative_to(CARPETA_TESIS)}")
    print(f"  {cuadros} cuadros en {duracion_real:.1f} s = {datos['fps_medido']} cuadros/s medidos")
    if abs(datos["fps_medido"] - FPS_PEDIDO) > 3:
        print(f"  AVISO: el archivo dice {FPS_PEDIDO} cuadros/s pero llegaron {datos['fps_medido']}: el video se vera "
              "mas rapido o mas lento. Para entrenar no importa (se extraen cuadros sueltos).")


if __name__ == "__main__":
    main()
