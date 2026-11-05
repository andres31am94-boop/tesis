"""
Fase 9.4 / 12: LAZO EN VIVO de la maqueta.

  camara -> YOLO (hotwheels_v2) + NMS + ByteTrack -> zonas por brazo (ContadorZonas)
         -> escala SUMO (EscaladorMaqueta) -> controlador (agente aforo_v9 o tiempos fijos) -> SafetyGuard
         -> "LUZ <fase>" al ESP32 -> el ESP32 confirma (OK) -> los LEDs cambian.

Cada cuadro se procesa con YOLO; cada SEGUNDO (reloj real con camara, reloj del video con un archivo) se toma el
ultimo estado de las zonas, el controlador decide (el agente: al verde minimo y luego cada 5 s) y el SafetyGuard
fija la luz. La luz se envia al ESP32 cada segundo (latido): si Python o la camara fallan, el ESP32 deja de recibir
latidos y a los 5 s pasa solo a intermitente (watchdog del firmware semaforo_obediente).

Uso (desde la carpeta tesis):
  # prueba sin ESP32 con un video (--repetir: lo reproduce en bucle para tener mas de 15 s)
  .\\.venv\\Scripts\\python.exe -m src.maqueta.lazo_camara --fuente data\\raw\\hotwheels\\prueba_alturas\\un_metro.MOV ^
        --zonas config\\zonas_prueba_1m.yaml --duracion_s 120 --repetir
  # maqueta: camara 0 (o la que corresponda), ESP32 en COM4, mostrando la imagen
  .\\.venv\\Scripts\\python.exe -m src.maqueta.lazo_camara --fuente 0 --zonas config\\zonas_camara.yaml --puerto COM4 --mostrar
  opciones: --controlador qlearning|tiempos_fijos  --modelo aforo_v9  --conf 0.40  --grabar (guarda el video anotado)
Salida: results/maqueta/lazo/<fecha_hora>_<controlador>/ (por_segundo.csv, cambios.csv, resumen.json, lazo.mp4)
"""
import argparse
import csv
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import yaml
from torchvision.ops import nms
from ultralytics import YOLO

from src.agent.codificador_estado import CodificadorEstado
from src.agent.qlearning import TablaQ
from src.common.configuracion import CARPETA_TESIS, cargar_interseccion
from src.communication.esp32_serial import ConexionESP32
from src.controller.qlearning_controlador import ControladorQLearning
from src.controller.safety_guard import SafetyGuard
from src.controller.tiempos_fijos import ControladorTiemposFijos
from src.simulation.lazo_hardware import ErrorLazo, enviar_y_confirmar, esperar_listo, leer_pendientes
from src.vision.escala_maqueta import EscaladorMaqueta, capacidades_zona_sumo
from src.vision.zonas import ContadorZonas, VehiculoSeguido

sys.path.insert(0, str(CARPETA_TESIS / "scripts"))
from ver_zonas import cargar_zonas, dibujar_zonas  # noqa: E402
from src.common.registro_computo import registrar_ejecucion

PESOS_POR_DEFECTO = CARPETA_TESIS / "results" / "vision" / "entrenamiento" / "hotwheels_v2" / "weights" / "best.pt"
COLOR_LUZ = {"verde": (0, 200, 0), "amarillo": (0, 210, 255), "todo_rojo": (0, 0, 230)}


def leer_yaml(ruta):
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))


def crear_controlador(nombre, modelo, config_interseccion):
    config_controlador = leer_yaml(CARPETA_TESIS / "config" / "controlador.yaml")
    if nombre == "qlearning":
        tabla = TablaQ.cargar(CARPETA_TESIS / "models" / modelo / "tabla_q.json")
        config_agente = tabla.metadatos["config_agente"]
        guard = SafetyGuard.desde_config(config_controlador, config_agente.get("perfil_seguridad", "norma"))
        codificador = CodificadorEstado(config_interseccion, config_agente)
        controlador = ControladorQLearning(tabla, codificador, guard, config_agente["intervalo_decision_s"],
                                           config_controlador["tiempos_fijos"]["verde_s"])
        return controlador, guard, codificador
    guard = SafetyGuard.desde_config(config_controlador, "real")
    return ControladorTiemposFijos.desde_config(config_controlador, guard), guard, None


def abrir_fuente(fuente):
    es_camara = fuente.isdigit()
    if es_camara:
        # DirectShow: backend que usan las camaras virtuales de Windows (iPhone como camara web). Se pide 1920x1080,
        # la misma proporcion 16:9 del video con que se midio el area visible (102 x 68 cm a 1 m).
        captura = cv2.VideoCapture(int(fuente), cv2.CAP_DSHOW)
        captura.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        captura.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    else:
        captura = cv2.VideoCapture(str(Path(fuente).resolve()))
    if not captura.isOpened():
        raise RuntimeError(f"No se pudo abrir la fuente de video '{fuente}'")
    return captura, es_camara


def dibujar_estado(imagen, fase, segundo, texto_decision):
    color = next((c for clave, c in COLOR_LUZ.items() if fase.startswith(clave)), (255, 255, 255))
    cv2.rectangle(imagen, (0, 0), (imagen.shape[1], 60), (0, 0, 0), -1)
    cv2.putText(imagen, f"t={segundo:>4}s  {fase.upper()}", (15, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
    cv2.putText(imagen, texto_decision, (560, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return imagen


def main():
    registrar_ejecucion()
    parser = argparse.ArgumentParser(description="Lazo en vivo de la maqueta: camara -> agente -> ESP32")
    parser.add_argument("--fuente", required=True, help="indice de camara (0, 1, ...) o ruta a un video")
    parser.add_argument("--zonas", required=True, help="yaml con zonas y capacidad_carros")
    parser.add_argument("--pesos", default=str(PESOS_POR_DEFECTO))
    parser.add_argument("--controlador", default="qlearning", choices=["qlearning", "tiempos_fijos"])
    parser.add_argument("--modelo", default="aforo_v9", help="agente (models/): aforo_v9 = adaptacion de v8 a la maqueta")
    parser.add_argument("--conf", type=float, default=0.40)
    parser.add_argument("--nms_iou", type=float, default=0.5)
    parser.add_argument("--puerto", help="puerto del ESP32 (p. ej. COM4); sin el, solo consola")
    parser.add_argument("--duracion_s", type=int, help="detener despues de estos segundos")
    parser.add_argument("--repetir", action="store_true", help="con un archivo de video: reproducirlo en bucle (pruebas)")
    parser.add_argument("--mostrar", action="store_true", help="ventana con la imagen anotada (tecla q para salir)")
    parser.add_argument("--grabar", action="store_true", help="guardar el video anotado (lazo.mp4)")
    argumentos = parser.parse_args()

    config_interseccion = cargar_interseccion()
    zonas, config_zonas = cargar_zonas(Path(argumentos.zonas).resolve())
    contador = ContadorZonas(zonas, ventana_detenido_s=config_zonas["deteccion_detenido"]["ventana_s"],
                             umbral_movimiento=config_zonas["deteccion_detenido"]["umbral_movimiento"],
                             punto_referencia=config_zonas.get("punto_referencia", "centro"))
    escalador = EscaladorMaqueta(config_zonas["capacidad_carros"], capacidades_zona_sumo(config_interseccion))
    controlador, guard, codificador = crear_controlador(argumentos.controlador, argumentos.modelo, config_interseccion)

    modelo_yolo = YOLO(str(Path(argumentos.pesos).resolve()))

    def quitar_duplicados(predictor):
        for i, resultado in enumerate(predictor.results):
            if len(resultado.boxes):
                predictor.results[i] = resultado[nms(resultado.boxes.xyxy, resultado.boxes.conf, argumentos.nms_iou)]
    modelo_yolo.add_callback("on_predict_postprocess_end", quitar_duplicados)

    captura, es_camara = abrir_fuente(argumentos.fuente)
    fps_video = captura.get(cv2.CAP_PROP_FPS) or 30.0
    nombre_corrida = f"{datetime.now():%Y%m%d_%H%M%S}_{argumentos.controlador}"
    carpeta = CARPETA_TESIS / "results" / "maqueta" / "lazo" / nombre_corrida
    carpeta.mkdir(parents=True, exist_ok=True)
    escritor_video = None

    conexion = None
    if argumentos.puerto:
        print(f"Conectando con el ESP32 en {argumentos.puerto}...")
        conexion = ConexionESP32(argumentos.puerto)
        esperar_listo(conexion)

    filas, cambios, ms_cuadro = [], [], []
    fase = guard.iniciar(0)
    if conexion is not None:
        conexion.enviar_luz(fase.upper())
    cambios.append({"segundo": 0, "luz": fase, "latencia_ms": None})
    print(f"t=   0s  {fase.upper()}  (inicio)")
    segundo_procesado = 0
    estado_camara = None
    texto_decision = ""
    cuadros = 0
    inicio_reloj = time.monotonic()
    try:
        while True:
            correcto, cuadro = captura.read()
            if not correcto:
                if not es_camara and argumentos.repetir:
                    captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    correcto, cuadro = captura.read()
                if not correcto:
                    if es_camara:
                        raise ErrorLazo("La camara dejo de entregar imagenes (el ESP32 pasara a intermitente en 5 s)")
                    print("Fin del video.")
                    break
            cuadros += 1
            tiempo = (time.monotonic() - inicio_reloj) if es_camara else cuadros / fps_video
            antes = time.perf_counter()
            resultado = modelo_yolo.track(cuadro, persist=True, tracker="bytetrack.yaml", conf=argumentos.conf,
                                          verbose=False)[0]
            vehiculos = []
            if resultado.boxes.id is not None:
                for (x1, y1, x2, y2), id_seg in zip(resultado.boxes.xyxy.tolist(), resultado.boxes.id.tolist()):
                    vehiculos.append(VehiculoSeguido(int(id_seg), x1, y1, x2, y2))
            alto, ancho = cuadro.shape[:2]
            estado_camara = contador.actualizar(tiempo, vehiculos, ancho, alto)
            ms_cuadro.append((time.perf_counter() - antes) * 1000)

            # Un paso del controlador por cada segundo cumplido (si el procesamiento se atrasa, se ponen al dia
            # con el ultimo estado: el SafetyGuard espera exactamente una llamada por segundo).
            while segundo_procesado + 1 <= tiempo:
                segundo_procesado += 1
                estado = escalador.escalar(estado_camara)
                decide = argumentos.controlador == "qlearning" and controlador.va_a_decidir(segundo_procesado)
                respaldos_antes = getattr(controlador, "decisiones_respaldo", 0)
                visto = (codificador.describir(codificador.codificar(estado, guard.eje,
                                                                     guard.tiempo_en_etapa(segundo_procesado)))
                         if decide else "")
                pedir = controlador.pedir_cambio(segundo_procesado, estado)
                respaldo = decide and getattr(controlador, "decisiones_respaldo", 0) > respaldos_antes
                nueva_fase = guard.paso(segundo_procesado, pedir)
                latencia = None
                if conexion is not None:
                    leer_pendientes(conexion)
                    if nueva_fase != fase:
                        latencia = round(enviar_y_confirmar(conexion, nueva_fase), 2)
                    else:
                        conexion.enviar_luz(nueva_fase.upper())   # latido
                if decide:
                    texto_decision = f"{'CAMBIAR' if pedir else 'MANTENER'}{' (respaldo)' if respaldo else ''}"
                    print(f"t={segundo_procesado:>4}s  {fase:<15} ve: {visto} -> {texto_decision}")
                if nueva_fase != fase:
                    cambios.append({"segundo": segundo_procesado, "luz": nueva_fase, "latencia_ms": latencia})
                    print(f"t={segundo_procesado:>4}s  ==> {nueva_fase.upper()}"
                          + (f"  (ESP32 confirmo en {latencia} ms)" if latencia is not None else ""))
                fila = {"segundo": segundo_procesado, "fase": nueva_fase,
                        "decision": texto_decision if decide else "", "estado_visto": visto}
                for brazo, datos in estado_camara.brazos.items():
                    fila[f"carros_{brazo}"] = datos.vehiculos_zona
                    fila[f"detenidos_{brazo}"] = datos.detenidos_zona
                    fila[f"equiv_{brazo}"] = estado.brazos[brazo].vehiculos_zona
                filas.append(fila)
                fase = nueva_fase

            if argumentos.mostrar or argumentos.grabar:
                conteos = {n: (b.vehiculos_zona, b.detenidos_zona) for n, b in estado_camara.brazos.items()}
                imagen = dibujar_estado(dibujar_zonas(resultado.plot(), zonas, conteos), fase, segundo_procesado,
                                        texto_decision)
                if argumentos.grabar:
                    if escritor_video is None:
                        escritor_video = cv2.VideoWriter(str(carpeta / "lazo.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                                         10, (ancho, alto))
                    escritor_video.write(imagen)
                if argumentos.mostrar:
                    cv2.imshow("Lazo maqueta (q para salir)", cv2.resize(imagen, (ancho * 720 // alto, 720)))
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
            if argumentos.duracion_s and segundo_procesado >= argumentos.duracion_s:
                break
    finally:
        captura.release()
        if escritor_video is not None:
            escritor_video.release()
        if argumentos.mostrar:
            cv2.destroyAllWindows()
        if conexion is not None:
            conexion.cerrar()   # sin latidos, el ESP32 pasa a intermitente a los 5 s (comportamiento esperado)

        if filas:
            for nombre, datos in (("por_segundo.csv", filas), ("cambios.csv", cambios)):
                with open(carpeta / nombre, "w", newline="", encoding="utf-8") as archivo:
                    escritor = csv.DictWriter(archivo, fieldnames=list(datos[0]))
                    escritor.writeheader()
                    escritor.writerows(datos)
            resumen = {"fuente": argumentos.fuente, "zonas": argumentos.zonas, "pesos": argumentos.pesos,
                       "controlador": argumentos.controlador,
                       "modelo": argumentos.modelo if argumentos.controlador == "qlearning" else None,
                       "conf": argumentos.conf, "puerto": argumentos.puerto, "segundos": segundo_procesado,
                       "cuadros": cuadros, "ms_por_cuadro_mediana": round(statistics.median(ms_cuadro), 1),
                       "cuadros_por_segundo": round(1000 / statistics.median(ms_cuadro), 2),
                       "verdes": [(eje, round(d)) for eje, _, d in guard.historial_verdes],
                       "decisiones": getattr(controlador, "decisiones", None),
                       "decisiones_respaldo": getattr(controlador, "decisiones_respaldo", None),
                       "latencias_esp32_ms": [c["latencia_ms"] for c in cambios if c["latencia_ms"] is not None]}
            (carpeta / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
            print(json.dumps({k: v for k, v in resumen.items() if k != "latencias_esp32_ms"}, ensure_ascii=False))
            print(f"Resultados en {carpeta}")


if __name__ == "__main__":
    main()
