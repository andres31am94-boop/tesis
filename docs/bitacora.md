# Bitácora del proyecto

Registro de lo que se hizo, qué funcionó, qué falló y qué se decidió.

## 2026-10-03 — Fase 0: planificación
- Análisis del proyecto, riesgos, arquitectura, MVP y hoja de ruta → `docs/fases/00_fase0_planificacion.md`.
- **Decisión:** ML = Aprendizaje por Refuerzo (Q-Learning con tabla; DQN solo si hace falta), según el anteproyecto aprobado. Se descarta el enfoque supervisado de la v1 del plan.
- **Decisión:** se agrega un prototipo físico a escala (cámara + YOLO + ESP32) como demostración.

## 2026-10-04 — Respuestas de la directora y entorno
- Directora: aprueba el prototipo físico; se mantiene el título; mínimo 6 objetivos específicos; no requiere trámite formal; la hipótesis puede reformularse → `docs/anteproyecto/ajustes_anteproyecto.md`.
- Sustentación: principios de febrero de 2027. Hoja de ruta ajustada a 17 semanas.
- Repositorio GitHub: `tesis`, público.
- Verificación del entorno con `scripts/check_entorno.ps1` → `docs/entorno/reporte_entorno.txt` y análisis en `docs/entorno/analisis_entorno.md`.
  - Sin GPU NVIDIA (Intel UHD): YOLO correrá en CPU.
  - SUMO no instalado. Python 3.11.5 disponible. Git y Arduino IDE instalados.
- Repositorio publicado: https://github.com/andres31am94-boop/tesis (primer commit `1ecafe9`).
  - Problema: el `push` fallaba con "Not Found" porque la URL del remoto había quedado sin `/tesis.git`. Solución: `git remote set-url origin https://github.com/andres31am94-boop/tesis.git`.
- Entorno virtual `.venv` creado con Python 3.11.5 (verificado en `.venv/pyvenv.cfg`).
- SUMO 1.27.1 instalado con instalador oficial de Windows; `SUMO_HOME` configurado (verificado con `check_entorno.ps1`, reporte 2026-10-04 22:00).

## 2026-10-04 — Fase 1: intersección de referencia
- Entorno cerrado: `traci` y `sumolib` 1.27.1 instalados en `.venv` (verificado por los autores).
- Intersección de referencia: **Carrera 23 con Diagonal 15, Acacías (Meta)**, coordenadas aprox. 3.990091, -73.765749. Mapa en `docs/fases/img/interseccion_mapa.png`.
- Se detecta que el marco geográfico del anteproyecto habla de Villavicencio → propuesta de corrección en `docs/anteproyecto/ajustes_anteproyecto.md`.
- Decisión de método para la red: importar de OpenStreetMap con `osmWebWizard`, guardar el archivo original y limpiar con `netconvert` (opción híbrida).
- Decisión: marco geográfico = **solo Acacías** (Opción 2). Borrador en `ajustes_anteproyecto.md`, con datos a completar desde fuentes oficiales.
- Datos de campo confirmados por los autores: el cruce **tiene semáforo** (tiempos aún sin medir) y **cada vía tiene un carril por sentido**.
- Pendiente de campo: medir con cronómetro los tiempos actuales de verde, amarillo y rojo (baseline real).
- Problema: `osmWebWizard` no arrancaba porque el comando `..\.venv\...` se ejecutó desde `tesis\` en lugar de `tesis\sumo\`.

## 2026-10-05 — Fase 1: importación de la red desde OpenStreetMap
- `osmWebWizard` falló con HTTP 504 (servidor Overpass saturado). Solución: exportar el área desde openstreetmap.org → `sumo/network/osm/acacias_cra23_diag15.osm`.
- Hallazgo: OSM modela la Carrera 23 y la Diagonal 15 como calzadas separadas con 2 carriles por sentido, pero los autores reportan 1 carril por sentido → **pendiente verificar en Street View/sitio**.
- Red v1 (`netconvert -c acacias.netccfg`): se generó, pero al revisar `acacias.net.xml` se encontró:
  1. **No se creó el semáforo del cruce**: en OSM las señales están sobre los accesos (6–11 m), no sobre el nodo del cruce.
  2. La Carrera 23 quedó a **100 km/h** (tipo `highway.primary` del mapa de tipos por defecto).
  3. Se incluyeron la Carrera 24 y la Calle 16A, que agregan cruces sin control.
- Red v2 (config actualizada): semáforo declarado explícitamente con `tls.set`, tipos de vía propios a 50 km/h (`tipos_vias.typ.xml`, provisional), eliminación de la Carrera 24 y la Calle 16A.
- Red v2 verificada: netconvert `Success.`; semáforo creado (`cluster_12995046887_9702926134`, 16 conexiones); 4 brazos; 50 km/h. Capturas en `docs/fases/img/red_sumo_v2_*.png`.
  - Longitud de los brazos de llegada: norte 110 m (1 carril), sur 188 m (2), este 331 m (2), oeste 231 m (2) — carriles según OSM, pendiente verificar.
  - Programa por defecto de netconvert: 6 fases, ciclo de 90 s, incluida una fase de giro a la izquierda protegido para la Carrera 23 y sin todo-rojo. Es provisional; se reemplaza en la Fase 3.
  - Error encontrado: había una vuelta en U permitida en la Carrera 23 sur (calzadas separadas en OSM). Se corrige en v3 con `correcciones.con.xml`.
- Verificación con Street View (autores, 2026-10-05):
  - **Carrera 23**: una sola calzada, doble línea amarilla, **1 carril por sentido** → OSM estaba mal al sur del cruce (2 calzadas de 2 carriles).
  - **Diagonal 15**: calzadas separadas por un separador pequeño; sin líneas de carril, pero caben 2 vehículos lado a lado por sentido → se mantienen 2 carriles (aproximación de modelado).
- Red v3 en dos pasos: `acacias.netccfg` (OSM → `acacias_osm.net.xml`) y `acacias_ajustes.netccfg` (carriles + vuelta en U → `acacias.net.xml`). El mapa OSM original no se modifica.
- **Corrección de la verificación anterior** (nuevas capturas de Street View): la Carrera 23 **al sur** del cruce sí tiene calzadas separadas con **2 carriles por sentido** (flechas pintadas: interior = izquierda, exterior = recto); solo **al norte** (puente) tiene 1 carril por sentido. → OSM era correcto; se revierte la reducción de carriles. `ajustes.edg.xml` queda sin cambios (solo documenta la verificación). El paso 2 se mantiene para eliminar la vuelta en U.
- **Red final v3 VALIDADA** (`sumo/network/acacias.net.xml`): paso 1 y paso 2 con `Success.`; verificado en el archivo: 15 movimientos controlados por el semáforo, **sin vuelta en U**; 50 km/h en todas las vías. Captura: `docs/fases/img/red_sumo_v3_final.png`.

  | Brazo de llegada | Edge | Carriles | Largo |
  |---|---|---|---|
  | Norte (Cra 23, puente) | `-642480900` | 1 | 110 m |
  | Sur (Cra 23) | `807940779` | 2 (interior: izquierda; exterior: recto/derecha) | 188 m |
  | Este (Dg 15) | `816899410#0` | 2 | 331 m |
  | Oeste (Dg 15) | `44411778#0` | 2 | 231 m |

## 2026-10-05 — Decisión: demanda basada en aforo real
- Los autores deciden definir la demanda de los escenarios a partir de un **aforo en campo** (no con proporciones supuestas).
- Planilla: `docs/aforo/planilla_aforo.xlsx` (hojas: Instrucciones, Aforo, Semaforo, Resumen con fórmulas, Hoja_campo imprimible). Fórmulas verificadas con datos de prueba.
- Mientras llega el aforo se avanza en la Fase 2 (TraCI) con una **demanda de prueba** marcada explícitamente como no válida para resultados.
- **Giro a la izquierda prohibido** en los 4 brazos (informado por los autores, 2026-10-05): solo recto o derecha.
  - Planilla de aforo actualizada: se eliminan las columnas de giro a la izquierda; si se observa alguna infracción se anota en Observaciones.
  - Red: `correcciones.con.xml` elimina los 4 giros a la izquierda y asigna el carril interior de la Cra 23 sur a "recto" (flechas pintadas). Pendiente regenerar la red (pasos 1 y 2) y verificar.
  - Nota: en la foto de Street View de la Cra 23 sur, la flecha curva vista desde la cámara corresponde a **giro a la derecha** para el conductor que llega (la imagen está "de frente"); la interpretación anterior como izquierda era incorrecta.

## 2026-10-06 — Red sin giros a la izquierda (verificada) y demanda de prueba
- Red regenerada por los autores; verificado en `acacias.net.xml`: **12 movimientos** (solo recto y derecha), sin vuelta en U, carril interior de la Cra 23 sur → recto. Semáforo por defecto: **2 fases** (Cra 23 / Dg 15), verde 42 s + amarillo 3 s cada una, ciclo 90 s, **sin todo-rojo** (se agregará en la Fase 3).
  - En la Cra 23 sur → norte los dos carriles se juntan en el único carril del puente: el carril exterior cede el paso al interior (estado `g`).
- Demanda **de prueba (inventada)**: `sumo/demanda/prueba_*.csv` → `scripts/generar_demanda.py` → `sumo/routes/prueba.rou.xml`; escenario `sumo/configs/prueba.sumocfg` (semilla 42). Total 1200 veh/h. **No válida para resultados**: se reemplaza con el aforo.
- **Fase 1 VALIDADA** (2026-10-06): `sumo-gui -c sumo/configs/prueba.sumocfg` carga red y rutas sin advertencias; los vehículos se detienen en rojo y avanzan en verde. Captura: `docs/fases/img/sim_prueba_fase1.png`.

## 2026-10-06 — Fase 2, paso 1: lectura del estado con TraCI
- Script `src/simulation/paso1_leer_estado.py`: abre `prueba.sumocfg` con TraCI y cada 30 s imprime vehículos y detenidos por brazo, más el estado del semáforo. Solo lectura. Pendiente de ejecución por los autores.
- Paso 1 **VALIDADO**: salida coherente con el semáforo (el eje en rojo acumula detenidos; el eje en verde, ~0). Orden de las 12 letras del estado de luces confirmado: 3 por brazo → norte, este, sur, oeste. La simulación continúa tras t = 3600 s hasta que salen los vehículos que ya estaban en la red.

## 2026-10-06 — Fase 2, paso 2: control del semáforo desde Python
- Script `src/simulation/paso2_controlar_semaforo.py`: aplica con `setRedYellowGreenState` una secuencia propia de 6 fases **con todo-rojo** (tiempos SOLO de prueba: verde Dg 60 s, verde Cra 20 s, amarillo 3 s, todo-rojo 2 s) y verifica cada segundo que SUMO tenga las luces ordenadas. Pendiente de ejecución.
- Paso 1, resumen final (demanda de PRUEBA): fin en t = 3666 s; 1232 vehículos completaron su recorrido (demanda nominal 1200 veh/h durante 3600 s; llegadas aleatorias). Todos los que entraron salieron: sin bloqueos.
- Paso 2 **VALIDADO**: los cambios de fase ocurren exactamente en 0, 60, 63, 65, 85, 88, 90… s; **600 de 600 segundos** comprobados en los que SUMO tuvo las luces ordenadas por Python; el todo-rojo funciona. Observación (datos de prueba, no es resultado): con 20 s de verde la Cra 23 acumula 14–24 detenidos durante su rojo y los despeja dentro de su verde; la Dg 15 acumula 3–6.

## 2026-10-06 — Fase 2, paso 3: módulos de la arquitectura
- `config/interseccion.yaml`: IDs del semáforo y brazos, luces de cada fase, 7,5 m por vehículo (valores por defecto de SUMO para automóvil: 5 m + 2,5 m).
- `src/common/estado.py` (EstadoTrafico/EstadoBrazo, incluye **cola relativa** = detenidos / capacidad), `src/common/configuracion.py`.
- `src/simulation/sesion_sumo.py`, `sumo_source.py` (lee), `sumo_actuator.py` (aplica y verifica luces).
- Prueba de regresión `src/simulation/paso3_modulos.py`: misma secuencia del paso 2; con la misma semilla sus líneas "t = …" deben ser idénticas. Pendiente de ejecución.
- `requirements.txt` creado (traci/sumolib 1.27.1, pyyaml).
