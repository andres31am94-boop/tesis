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
- Paso 3 **VALIDADO**: las 41 líneas "t = …" de `paso3_modulos` son idénticas a las del paso 2 (misma semilla) → el reordenamiento no cambió el comportamiento. Capacidades calculadas: norte 14,6 · sur 50,1 · este 88,3 · oeste 61,7 vehículos (largo de carriles ÷ 7,5 m). **Fase 2 VALIDADA.**
- **Hallazgo metodológico:** con la demanda de prueba el brazo norte (puente, 1 carril, 110 m) llega a cola relativa 0,96. Si un brazo se llena, los vehículos esperan fuera de la red y esa espera no aparece en las métricas internas → en la Fase 3 la espera de cada vehículo incluirá el **retraso de entrada** (`departDelay` de SUMO).

## 2026-10-06 — Observación cualitativa de los autores
- Según la observación de los autores, el cruce presenta congestión recurrente en **horas pico entre semana** y durante **festivales o fiestas**. Implicaciones: (1) el aforo debe incluir un día entre semana en hora pico; (2) candidato a escenario adicional: **evento/festival** (aumento temporal de demanda). Es una observación, no una medición: debe respaldarse con el aforo.

## 2026-10-06 — Fase 3, paso 1: capa de seguridad y controlador de tiempos fijos
- `config/controlador.yaml` (valores **provisionales**): verde mín. 10 s, máx. 60 s, amarillo 3 s, todo-rojo 2 s; tiempos fijos 42 s por eje (los del programa de SUMO, hasta medir el semáforo real).
- `src/controller/safety_guard.py`: máquina de fases segura (verde → amarillo → todo-rojo → verde del otro eje); registra verdes, cambios rechazados y forzados. Sin TraCI.
- `src/controller/tiempos_fijos.py`: baseline; usa el mismo SafetyGuard que usará el agente.
- `tests/test_safety_guard.py`: 9 pruebas automáticas — **9/9 OK** al ejecutarlas en el entorno de Claude (Python 3.10). Pendiente de ejecución en el PC de los autores.
- Paso 1 **VALIDADO** en el PC de los autores: 9/9 pruebas OK.

## 2026-10-06 — Fase 3, paso 2: corrida completa del baseline con métricas
- `config/experimento.yaml` (provisional): calentamiento 300 s, demanda 3600 s, margen de vaciado 1800 s.
- `src/metrics/metricas.py`: métricas desde `tripinfo` de SUMO. Ventana de medición por **hora programada de entrada** (salida real − `departDelay`), y espera total = espera en la red + retraso de entrada. Pruebas `tests/test_metricas.py` (4) → 13/13 OK en el entorno de Claude.
- `src/simulation/sesion_sumo.py`: nuevo parámetro `argumentos_extra` (para pedir salidas de SUMO como tripinfo). El comportamiento anterior no cambia.
- `src/simulation/ejecutar_escenario.py`: SUMO + SafetyGuard + controlador → `results/<escenario>/<controlador>/semilla_<n>/` (`resumen.json`, `series.csv`, `tripinfo.xml`). Pendiente de ejecución.
- Paso 2 **VALIDADO** (2026-10-06): 13/13 pruebas OK en el PC de los autores. Corrida `prueba` + `tiempos_fijos` + semilla 42 (DEMANDA DE PRUEBA, no es resultado de la tesis): verdes de 42,00 s en ambos ejes, 35 verdes por eje en la ventana 300–3600 s, 0 cambios rechazados/forzados, 0 vehículos sin terminar, 1127 vehículos medidos, retraso de entrada ≈ 0. Coherencia verificada (ciclo 94 s; tiempo perdido ≥ espera).
- **Reproducibilidad VALIDADA**: la segunda corrida con la misma semilla dio métricas idénticas.
- Estado Fase 3: funcional. Pendiente: reemplazar en `config/controlador.yaml` los tiempos provisionales por los medidos en campo y justificar los límites con la norma.

## 2026-10-07 — Fase 4, paso 1: codificador de estado y tabla Q
- Diseño del agente **aprobado por los autores**: estado = (cola relativa del brazo más cargado de cada eje en 4 niveles, eje en verde, tiempo en verde en 3 niveles) → 96 estados; acciones mantener/cambiar cada 5 s tras el verde mínimo; recompensa = −(detenidos totales acumulados en el intervalo); α 0,1, γ 0,9, ε 1,0→0,05; semillas de entrenamiento ≥ 1000 y de evaluación 1–30.
- `config/agente.yaml`, `src/agent/codificador_estado.py`, `src/agent/qlearning.py` (sin dependencias externas; tabla en JSON).
- `tests/test_agente.py`: 12 pruebas (bordes de niveles, brazo más cargado, índices únicos, fórmula de Q-Learning verificada a mano, ε-greedy, guardar/cargar). Total del proyecto: 25 pruebas → **25/25 OK** en el entorno de Claude. Pendiente en el PC de los autores.
- Paso 1 **VALIDADO** en el PC de los autores: 25/25 pruebas OK.
- Pregunta de los autores: ¿el sistema tiene memoria? Respuesta documentada: (1) lo aprendido = tabla Q guardada en JSON (persiste y se lleva a la maqueta); (2) no recuerda el pasado reciente: decide solo con el estado actual (propiedad de Markov) → posible mejora futura: agregar tendencia de la cola; (3) la tabla se congela en evaluación y en la maqueta (reproducibilidad y seguridad); aprendizaje en operación = trabajo futuro.

## 2026-10-07 — Fase 4, paso 2: entorno de entrenamiento y entrenamiento corto
- `src/simulation/sesion_sumo.py`: se separa `iniciar_sumo()` (el entorno necesita abrir/cerrar SUMO en cada episodio); `sesion_sumo` sigue funcionando igual.
- `src/agent/entorno_sumo.py`: `reset(semilla)` / `step(accion)`; el agente decide solo en verde y tras el verde mínimo; recompensa = −(detenidos acumulados durante el paso, incluidas las transiciones).
- `src/agent/entrenar.py`: entrenamiento con semillas ≥ 1000 (comprueba que no se crucen con las de evaluación); guarda `models/<nombre>/tabla_q.json` y `curva_aprendizaje.csv` tras cada episodio. Pendiente de ejecución (prueba corta de 3 episodios).
- Entrenamiento corto **VALIDADO** (3 episodios, DEMANDA DE PRUEBA): 13–17 s por episodio (→ ~200 episodios ≈ 45–55 min); ~345 decisiones por episodio; ε 1,000→0,987; 11 de 96 estados visitados (la demanda de prueba casi no produce colas altas). Las cifras de detenidos del entrenamiento **no son comparables** con el baseline (otra ventana y otras semillas): la comparación se hará con `ejecutar_escenario` con las mismas semillas.
- Propuesto a los autores: si en evaluación aparece un estado con 0 visitas, el agente actúa como el plan fijo y se registra (respaldo seguro). Pendiente de confirmación.
- Hipótesis a medir: con demanda liviana, un plan fijo de 42 s puede ser excesivo → refuerza usar como baseline el semáforo real medido y agregar un controlador por reglas.

## 2026-10-07 — Fase 4, paso 3 (preparado mientras corre el entrenamiento de 200 episodios)
- `src/agent/graficar_curva.py`: curva de aprendizaje en 3 paneles (recompensa con media móvil de 10, detenidos promedio, ε). Diseño verificado con datos ficticios (no publicados). Se agrega `matplotlib` a `requirements.txt`.
- `src/controller/qlearning_controlador.py`: usa la tabla entrenada **congelada** (ε = 0), decide en los mismos instantes que en el entrenamiento, y en estados con 0 visitas usa el plan fijo (respaldo), contando esas decisiones.
- `ejecutar_escenario.py`: nuevo controlador `qlearning` con `--modelo`; resultados en `results/<escenario>/qlearning_<modelo>/semilla_<n>/`; métricas extra: decisiones del agente, decisiones de respaldo, pedidos de cambio.
- **Error encontrado por las pruebas automáticas y corregido:** en respaldo, el plan fijo solo se consultaba cada 5 s, por lo que un verde fijo de 42 s duraba 45 s. Ahora se revisa cada segundo. `tests/test_controlador_qlearning.py` (4 pruebas) → total **29/29 OK** en el entorno de Claude.

## 2026-10-07 — Resultado del entrenamiento de 200 episodios (DEMANDA DE PRUEBA)
- 200 episodios en 36,6 min; 20 de 96 estados visitados.
- **El agente NO mejoró de forma clara.** Promedios por bloques de 25 episodios:

  | Episodios | ε inicial | Recompensa media (sd) | Detenidos prom. | % decisiones "cambiar" | Verdes Cra 23 |
  |---|---|---|---|---|---|
  | 0–24 | 1,00 | −10 681 (829) | 2,98 | 48 % | 83 |
  | 50–74 | 0,68 | −10 766 (949) | 3,00 | 39 % | 75 |
  | 100–124 | 0,37 | −11 385 (989) | 3,17 | 32 % | 68 |
  | 150–174 | 0,05 | −11 472 (1053) | 3,20 | 29 % | 64 |
  | 175–199 | 0,05 | −10 339 (941) | 2,88 | 35 % | 70 |

  Al bajar ε el agente aprendió a **cambiar menos** (verdes más largos) y eso **no redujo** los detenidos (incluso los aumentó levemente). La variación entre episodios (sd ≈ 900) es grande porque cada episodio usa otra semilla: la curva de entrenamiento no basta para juzgar; hay que evaluar con semillas fijas.

- **Diagnóstico (hipótesis a verificar una por una):**
  1. **Sesgo de la recompensa por pasos de distinta duración.** Un paso "cambiar" dura ~15 s (amarillo + todo-rojo + verde mínimo) y un "mantener" 5 s; con γ = 0,9 *por paso*, los costos futuros de mantener se descuentan antes que los de cambiar → el agente sobrevalora "mantener". Corrección propuesta: descuento por segundo (formulación semi-Markov: γ elevado a la duración del paso).
  2. **Estado poco informativo con demanda liviana.** En la corrida del baseline (semilla 42, ventana 300–3600 s), la cola relativa del eje Dg 15 estuvo en el nivel "vacía" (< 0,1) el **99 %** del tiempo (p99 = 0,113) y la de Cra 23 el 69 %. El agente casi no distingue situaciones. Corrección propuesta: recalibrar los cortes con la distribución observada (cuantiles).
  3. **Poco margen de mejora con demanda liviana**: con colas casi siempre vacías, cualquier controlador razonable rinde parecido. Se necesitan escenarios medio/alto (aforo).
- Plan: evaluar el agente actual con semillas fijas → aplicar la corrección 1 sola → reentrenar y evaluar → corrección 2 sola → reentrenar y evaluar. No cambiar varias cosas a la vez.

## 2026-10-07 — Primera evaluación del agente (1 semilla, DEMANDA DE PRUEBA — no es resultado de la tesis)
- 29/29 pruebas OK en el PC de los autores; curva graficada (`models/prueba_200/curva_aprendizaje.png`).
- Semilla de evaluación 1, misma ventana 300–3600 s:

  | Métrica | Tiempos fijos 42/42 | Q-Learning (prueba_200) |
  |---|---|---|
  | Espera total promedio (s) | 14,85 | 7,40 |
  | Tiempo de viaje promedio (s) | 53,46 | 45,43 |
  | Detenidos promedio (total) | 4,87 | 2,45 |
  | Verde promedio Cra 23 / Dg 15 (s) | 42 / 42 | 20,00 / 16,18 |
  | Decisiones del agente / de respaldo | — | 414 / 0 |

- **Interpretación (con cautela):**
  1. Una sola semilla no permite concluir nada; se requieren las 30 semillas de evaluación y prueba estadística.
  2. **Se corrige el diagnóstico anterior n.º 1**: la política aprendida NO favorece "mantener"; cambia siempre a los 20 s en Cra 23. La caída del % de "cambiar" en el entrenamiento (48 % → ~33 %) se explica por esa política (decide a los 10, 15 y 20 s y cambia en la tercera), no por un sesgo hacia mantener. El sesgo teórico por pasos de distinta duración sigue existiendo, pero los datos no muestran que esté afectando.
  3. El verde de Cra 23 es **siempre exactamente 20 s** → la política depende casi solo del tiempo, no de las colas (consistente con el diagnóstico n.º 2: el estado casi siempre es "vacío"). El agente se comporta como un **plan fijo corto**.
  4. Por lo tanto, la gran diferencia frente al baseline se debe probablemente a que **42 s de verde es demasiado para esta demanda liviana**, no a la adaptación. **El baseline 42/42 es débil**: hay que comparar contra el mejor plan fijo posible y contra el semáforo real medido.
- Implicación para el diseño experimental: la ventaja de un control adaptativo debería aparecer con demanda **desbalanceada o variable en el tiempo** (hora pico, festival); con demanda constante y balanceada un buen plan fijo es casi óptimo. Hipótesis a medir.

## 2026-10-08 — Decisiones de los autores y pausa
- **El agente elige los tiempos del semáforo** (mantener/cambiar en cada decisión); nunca se le impondrá un plan fijo. Los ~20 s observados son lo que aprendió con la demanda de prueba; se espera que cambie con la demanda real (a verificar).
- **Baseline = el semáforo real** de la Cra 23 × Dg 15, con los tiempos medidos en campo (hoja "Semaforo" de la planilla; pico y valle, 3–4 ciclos, todo-rojo y fases adicionales). Los 42/42 s actuales son provisionales. El "mejor plan fijo posible" queda solo como referencia complementaria opcional.
- Los datos de prueba no permiten conclusiones; todo se repetirá con el aforo.
- **Estado al pausar:** Fases 0–2 validadas; Fase 3 implementada y probada (tiempos provisionales); Fase 4 con entorno, entrenamiento, gráfica y controlador Q-Learning funcionando (29/29 pruebas).
- **Próximos pasos al retomar:** (1) comparación automática con las 30 semillas de evaluación + prueba estadística; (2) cargar aforo → escenarios bajo/medio/alto y variable (hora pico/festival); (3) cargar tiempos reales del semáforo en `config/controlador.yaml`; (4) recalibrar los niveles del estado con datos reales; (5) reentrenar y evaluar.
- **Pendientes de los autores:** aforo y medición del semáforo; compra de hardware; revisión del anteproyecto con la directora; verificar referencias; `git push` de los avances.

## 2026-10-20 — Medición en campo del semáforo real (autores, cronómetro del celular, varias repeticiones)
| Vía | Sentidos | Verde | Amarillo | Rojo | Ciclo (suma) |
|---|---|---|---|---|---|
| Carrera 23 | Acacías→Villavicencio y Villavicencio→Acacías (iguales) | 55 s | 3 s | 45 s | 103 s |
| Diagonal 15 | hacia el hospital y hacia el centro (iguales) | 20 s | 3 s | 77 s (1 min 17 s) | 100 s |

- Plan **muy desbalanceado** a favor de la Cra 23 (55 s vs 20 s de verde), coherente con que es la vía principal.
- **Inconsistencia a aclarar:** si solo hubiera 2 fases, el rojo de una vía ≈ verde + amarillo de la otra (+ todo-rojo). Cra 23: rojo 45 s vs 20 + 3 = 23 s de la Dg 15 → sobran ~22 s. Dg 15: rojo 77 s vs 55 + 3 = 58 s → sobran ~19 s. Es decir, hay **~20 s por ciclo en que ambas vías están en rojo** (≈10 s por transición, o un solo bloque). Posibles causas: fase peatonal exclusiva, todo-rojo largo, una fase adicional no registrada, o error de medición. Los ciclos difieren en 3 s (103 vs 100), dentro de lo esperable por reacción al cronometrar.
- Pendiente: observar un ciclo completo mirando ambos semáforos a la vez (o en video) para ubicar esos ~20 s; anotar día y hora (pico/valle) de la medición.
- `config/controlador.yaml` actualizado: tiempos fijos **55 s (Cra 23) y 20 s (Dg 15)** medidos; amarillo 3 s medido; **todo-rojo 10 s por transición como supuesto provisional** (reproduce un ciclo de 101 s, consistente con los 100–103 s medidos). Pendiente de verificación en campo: si resulta ser una fase peatonal única o un reparto distinto, se ajusta la capa de seguridad.
- Consecuencia: todos los resultados anteriores con 42/42 y todo-rojo 2 s quedan obsoletos; el agente debe reentrenarse con estos parámetros (usa las mismas transiciones del SafetyGuard).
- Planilla de aforo corregida (2026-10-20): la lista desplegable de brazos partía "Norte (Cra 23, desde el puente)" en dos opciones porque Excel usa la coma como separador. Nuevos nombres sin comas y con el sentido de viaje: Norte – Cra 23 (de Villavicencio hacia Acacías); Sur – Cra 23 (de Acacías hacia Villavicencio); Este – Dg 15 (hacia el hospital); Oeste – Dg 15 (hacia el centro). La correspondencia Este/Oeste con hospital/centro se dedujo del mapa: **pendiente de confirmar por los autores**. El archivo no tenía datos aún.

## 2026-10-20 — Aforo real cargado y verificado
- Copia intacta de lo que llenaron los autores: `docs/aforo/planilla_aforo_original_2026-10-20.xlsx`.
- Correcciones en `planilla_aforo.xlsx` (sin tocar los conteos): (1) los datos se habían llenado en la versión anterior de la planilla y el brazo norte quedó como "Norte (Cra 23" → la hoja Resumen no lo contaba; se pasaron a los nombres nuevos; (2) la columna Día tenía el número del día del mes o estaba vacía → se llenó con el día de la semana a partir de la fecha. Resumen recalculado sin errores.
- Sesiones de conteo (15 min por brazo; veh/h = conteo × 4):

  | Sesión | Tipo | Norte | Sur | Este | Oeste | Total | Simultáneo |
  |---|---|---|---|---|---|---|---|
  | Viernes 16-oct 18:00–19:00 | Pico | 1436 | 1512 | 460 | 680 | 4088 | No (brazo por brazo) |
  | Martes 20-oct 12:15–12:30 | Pico | 1336 | 1020 | 696 | 404 | 3456 | Sí |
  | Martes 20-oct 10:25–10:40 | Valle | 996 | 916 | 472 | 368 | 2752 | Sí |
  | Lunes 19-oct 20:15–21:15 | Valle | 716 | 696 | 280 | 152 | 1844 | No |

- Hallazgos: motos = 48–70 % de los vehículos según brazo; la Cra 23 lleva ~2–3 veces más tráfico que la Dg 15; giros a la derecha 4–18 %; buses y camiones relevantes en la Cra 23 (ruta 65). Observaciones de los autores: "muchas infracciones" (tipo no especificado).
- **Riesgo de modelado:** el brazo norte (1 carril) recibe ~1400 veh/h en pico, la mayoría motos. En SUMO las motos ocupan el carril como un vehículo más (no adelantan entre carros) → la simulación podría sobreestimar las colas en ese brazo. Evaluar modelo de subcarriles (sublane) para motos o declarar limitación.
- **Correspondencia de brazos CONFIRMADA por los autores** (2026-10-20): Norte = vehículos que bajan del puente (de Villavicencio hacia Acacías); Oeste = vehículos que vienen del lado del hospital hacia el cruce (van hacia el centro). Coincide con la planilla corregida: no hay que invertir conteos.
- **Infracciones:** se observaron al menos 3 por cada conteo de 15 min (giros a la izquierda prohibidos y paso en rojo), pero **no se contaron**. Decisión: no se simulan; el modelo asume cumplimiento de la norma y se declara como limitación (observación cualitativa).

## 2026-10-20 — Escenarios de demanda REAL generados
- `config/escenarios_aforo.yaml` define qué sesión del aforo usa cada escenario; `scripts/generar_escenarios_aforo.py` lee la planilla y genera `sumo/demanda/<esc>_flujos.csv`, `sumo/routes/<esc>.rou.xml` y `sumo/configs/<esc>.sumocfg`. Cada brazo conserva su propia mezcla de tipos y giros (un flujo por brazo × movimiento × tipo). Supuesto: 15 min de conteo extrapolados a 1 h de demanda constante.
- Totales generados (coinciden con la planilla): bajo 1844 · valle mañana 2752 · medio 3456 · alto 4088 veh/h.
- Se agrega `openpyxl` a `requirements.txt`. Pendiente: corrida del baseline real en cada escenario para verificar saturación (especialmente el brazo norte).

## 2026-10-20 — Semáforo real (55/20 s, todo-rojo 10 s provisional) con demanda real — semilla 1
| Escenario | Demanda (veh/h) | Throughput simulado (veh/h) | Espera total (s) | Retraso de entrada (s) | Cola máx. N / S / E / O | Sin terminar | Teleports |
|---|---|---|---|---|---|---|---|
| aforo_bajo | 1844 | 1886 | 20,6 | 0,3 | 17 / 14 / 10 / 9 | 0 | 0 |
| aforo_medio | 3456 | 2939 | 421,7 | 345,9 | 20 / 55 / 67 / 18 | 5 | 2 (buses, sur) |
| aforo_alto | 4088 | 2948 | 758,0 | 699,1 | 20 / 55 / 18 / 33 | 260 | 5 (buses/camión, sur) |

- **Hallazgo clave (calibración):** el aforo cuenta vehículos que **cruzaron** la línea de pare, es decir, lo que el cruce real **sí atendió** con su semáforo real. En la simulación, con el mismo semáforo, el cruce atiende mucho menos en medio y alto (p. ej. alto: 2948 vs 4088 veh/h) y los brazos sur (Cra 23) y este (Dg 15) colapsan. → **El modelo subestima la capacidad del cruce: no está calibrado.**
- Causas probables (a verificar una por una):
  1. **Motos** (48–70 % del tráfico) modeladas como un vehículo más dentro del carril; en la realidad van lado a lado y se filtran entre carros.
  2. **Unión de 2 carriles a 1 en el puente** (Cra 23 sur → norte): el carril exterior cede el paso al interior; los teleports de buses ("waited too long (yield)") ocurren justo ahí.
  3. Parámetros de conducción por defecto de SUMO (separación, tiempo de reacción) más conservadores que el comportamiento local.
  4. El todo-rojo supuesto (10 s por cambio) aún no verificado.
- Los teleports (SUMO saca de la red a vehículos atascados > 300 s) distorsionan las métricas: deben eliminarse con la calibración.
- **Decisión propuesta:** calibrar el modelo ANTES de entrenar al agente. Criterio: flujo atendido por brazo en la simulación ≈ conteo del aforo (estadístico GEH < 5, criterio usual de calibración de modelos de tráfico). Un agente entrenado en un modelo no calibrado aprendería un cruce que no existe.

## 2026-10-21 — Respuestas de campo y primer paso de calibración
- **Colas observadas por los autores:** viernes 6 p. m., brazo sur: ~10 vehículos en cola (carros, camiones y busetas, sin contar motos). Brazo este al mediodía y 6 p. m.: a veces no todos alcanzan a pasar en un verde (20 s). → La simulación sin calibrar exagera mucho (sur: cola promedio 29, máx. 55). Confirma la necesidad de calibrar.
- **Los ~20 s "perdidos" del ciclo, encontrados:** al terminar el verde de la Dg 15 hay **~22 s con todo en rojo** antes de que la Cra 23 pase a verde (para que despejen los vehículos de la Diagonal). Al terminar la Cra 23, la Dg 15 pasa a verde de inmediato. Cuadra con las mediciones: rojo Cra 23 (45) = 20 + 3 + TR; rojo Dg 15 (77) = 55 + 3 + TR → TR ≈ 19–22 s solo en el cambio Dg 15 → Cra 23.
- `SafetyGuard` admite ahora **todo-rojo distinto por eje** (`todo_rojo_s: {cra23: 0, dg15: 20}` en `config/controlador.yaml`); ciclo 55+3+0+20+3+20 = 101 s. Prueba nueva → **30/30 OK** (entorno de Claude).
- `scripts/validar_calibracion.py`: compara flujo atendido por brazo (simulado) vs. aforo, con el indicador **GEH** (criterio < 5).

## 2026-10-21 — Calibración, medición "antes" (v0: sin subcarriles; todo-rojo real 0/20 s)
| Escenario | Brazo | Aforo (veh/h) | Simulado (veh/h) | Dif. | GEH | |
|---|---|---|---|---|---|---|
| aforo_bajo | norte | 716 | 687 | −4 % | 1,1 | OK |
| | sur | 696 | 745 | +7 % | 1,8 | OK |
| | este | 280 | 283 | +1 % | 0,2 | OK |
| | oeste | 152 | 163 | +7 % | 0,8 | OK |
| aforo_alto | norte | 1436 | 878 | −39 % | 16,4 | NO CUMPLE |
| | sur | 1512 | 919 | −39 % | 17,0 | NO CUMPLE |
| | este | 460 | 492 | +7 % | 1,5 | OK |
| | oeste | 680 | 661 | −3 % | 0,7 | OK |

- Con tráfico bajo el modelo reproduce el aforo (4/4). Con tráfico alto **la Cra 23 atiende ~40 % menos de lo contado** en ambos sentidos (~900 veh/h cada uno). En el brazo norte el cruce real atendió 1436 veh/h por **un solo carril** con 55 s de verde por ciclo de 101 s: eso solo es posible si las motos circulan lado a lado / entre carros. El sur también termina en el carril único del puente. Alto: 269 vehículos sin terminar, 3 teleports (buses, unión de carriles del sur).
- Resultados "antes" guardados en `results/calibracion/v0_sin_subcarriles/`.
- **Paso de calibración 1:** modelo de subcarriles para motos (`config/calibracion.yaml`: resolución lateral 0,8 m; motos con `minGapLat` 0,3 m y `latAlignment` arbitrary). Escenarios regenerados con `scripts/generar_escenarios_aforo.py` (lee esa configuración). Un solo cambio respecto a v0.
- Incidente: `docs/aforo/planilla_aforo.xlsx` no estaba en la carpeta (eliminado o movido); se restauró la versión corregida del 2026-10-20 (idéntica a la entregada).
- **Paso 1 medido (con subcarriles):** aforo_alto norte 884 (GEH 16,2), sur 905 (GEH 17,4), este/oeste OK; aforo_bajo 4/4 OK. **Efecto casi nulo.** Captura de sumo-gui (autores): motos centradas, una detrás de otra.
- Diagnóstico (con `tripinfo` de v0): brazo norte → espera dentro de la red 25,6 s pero **retraso de entrada 944 s**; sur → 102,6 s y 927 s. El brazo norte descarga en fila india (~1 vehículo cada 2,2 s de verde ≈ 900 veh/h) y, como el tramo solo mide 110 m, la cola se represa fuera de la red.
- **Paso de calibración 2:** las motos entran en una posición lateral aleatoria (`departPosLat="random"` en sus flujos; `config/calibracion.yaml` → `moto_flujo`). Un solo cambio respecto al paso 1.
- Nota: la corrida con `--gui` cerrada antes de terminar dejó un `tripinfo.xml` incompleto en `results/aforo_alto/tiempos_fijos/semilla_1/`; se sobrescribe en la siguiente corrida.

### 2026-10-21 — Calibración, resultado del paso 2 y paso 3 (tramos de acceso)

**Resultado del paso 2 (motos entran en posición lateral al azar), semilla 1, ejecutado por los autores:**

| Escenario | Brazo | Aforo (veh/h) | Simulado | GEH paso 1 | GEH paso 2 |
|---|---|---|---|---|---|
| aforo_alto | norte | 1436 | 982 | 16.2 | 13.1 |
| aforo_alto | sur | 1512 | 968 | 17.4 | 15.5 |
| aforo_alto | este | 460 | 493 | — | 1.5 |
| aforo_alto | oeste | 680 | 652 | — | 1.1 |
| aforo_bajo | 4 brazos | — | — | 4/4 OK | 4/4 OK (máx. 1.9) |

aforo_alto: 68 vehículos sin terminar (antes 269), retraso de entrada promedio 632 s, espera en red 46 s.

**Diagnóstico** (series.csv, ciclo t = 1500–1610 s): durante el rojo la cola del norte llega a 16 detenidos
(el brazo de 110 m se llena); con el verde se vacía en ~15 s y queda en 0 detenidos los ~40 s restantes.
La línea de pare se queda sin vehículos mientras cientos esperan fuera de la red. El sur muestra lo mismo
(de 48 a 3 detenidos a mitad del verde). El cuello de botella es la **inserción** de vehículos en brazos
cortos, no la descarga en el cruce. En la realidad la cola sigue por el puente y descarga todo el verde.

**Paso 3 (un solo cambio):** tramo recto de 500 m antes de cada brazo (`acceso_norte`, `acceso_sur`,
`acceso_este`, `acceso_oeste`), con el mismo número de carriles que el brazo, para que la cola se forme
dentro de la red. Los brazos originales no cambian y el estado del agente se sigue midiendo solo en ellos.
Archivos: `scripts/generar_accesos.py` (nuevo), `config/calibracion.yaml` (sección `accesos`),
`sumo/network/acacias_ajustes.netccfg` (node-files, edge-files, offset.disable-normalization,
no-turnarounds), `scripts/generar_escenarios_aforo.py` (los flujos salen de `acceso_<brazo>`).
Criterio de práctica: la red simulada debe extenderse lo suficiente para contener las colas
(FHWA, *Traffic Analysis Toolbox Vol. III*). **Efecto: debe medirse.**
Consecuencia: el tiempo de viaje ahora incluye los 500 m del acceso y la espera en la cola del acceso
aparece como espera en la red (antes quedaba oculta como retraso de entrada). Afecta por igual a ambos controladores.

### 2026-10-21 — Resultado del paso 3 y corrección del diagnóstico

**Resultado del paso 3 (accesos de 500 m), semilla 1:** aforo_alto norte 981 veh/h (GEH 13.1), sur 983 (15.0),
este 1.2, oeste 1.0 → **sin mejora en el flujo atendido**. aforo_bajo 4/4 OK. La red reconstruida conserva
los 12 movimientos del semáforo en el mismo orden (verificado comparando las conexiones antes y después);
los brazos se acortaron ~1.5 m por la nueva unión con el acceso.

**Corrección:** el diagnóstico del paso 3 era incompleto. `series.csv` registra vehículos *detenidos*
(velocidad < 0.1 m/s), no vehículos presentes: 0 detenidos durante el verde no significa línea de pare vacía,
sino cola en movimiento. El paso 3 se mantiene porque representa mejor la cola real (ahora se ve como espera
en la red: 106 s en norte), pero no era la causa del déficit.

**Evidencia nueva** (tripinfo, vehículos que terminaron en la ventana): en el norte la moto espera en la red
106 s y el carro 105 s; en el sur 194 s y 204 s. **Las motos no se están filtrando entre los carros.**
Descarga del norte: 981 veh/h ≈ 27.5 vehículos por verde de 55 s (~2.1 s por vehículo); el aforo implica ~40 por verde (~1.45 s).
Causa probable: SUMO centra los carros por defecto (`latAlignment="center"`; documentación de SUMO).
Un carro de 1.8 m en un carril de 3.2 m deja 0.7 m a cada lado y no cabe una moto de 0.9 m más su separación lateral.

**Paso 4: barrido sistemático** (`scripts/barrido_calibracion.py`, `config/barrido_calibracion.yaml`).
Se prueban 2 × 2 × 2 = 8 combinaciones: alineación lateral del carro (center/right), ancho de la moto (0.9/0.8 m)
y separación lateral mínima de la moto (0.3/0.1 m), en aforo_alto y aforo_bajo, con la semilla 1.
No modifica los escenarios oficiales. Resultados en `results/calibracion/barrido/`. La combinación elegida
se valida después con varias semillas y con aforo_medio y aforo_valle_manana. **Efecto: debe medirse.**
Pendiente de campo: qué se contó como "bus" (bus grande de 12 m, buseta o microbús).

### 2026-10-21 — Respuestas de campo y paso 4a (datos físicos)

Respuestas completas en `docs/campo/preguntas_campo_2026-10-21.md`. Lo que cambia el modelo:

- **Trancón:** más frecuente en el brazo **sur** (hacia Villavicencio). A veces la fila se frena **en pleno verde**
  porque el puente (1 carril por sentido) se congestiona; a veces la cola llenó el brazo sur "de semáforo a semáforo".
- **Semáforo vecino:** Calle 18, a ~260 m al norte (corrección de los autores: no son 700 m), coordenadas
  3°59'32.9"N 73°45'54.6"W. Queda **después** del cruce para quien va hacia Villavicencio y **antes** para quien llega
  por el norte. No está en la red; sus tiempos no se han medido.
- **Puente:** la intersección es de doble carril; la reducción a 1 carril ocurre al salir del cruce hacia el puente.
- **Motos:** adelantan por ambos lados, la mayoría se ubica adelante en la línea de pare, arrancan primero;
  en el carril del puente caben 3 lado a lado ("bien pegadas, 4"). Motocarros contados como motos.
- **"Bus"** = buses intermunicipales grandes + busetas + microbuses. **"Camión"** = tractomulas, furgones grandes, camiones.
- Sin paraderos ni carros estacionados cerca. Peatones cruzan en rojo (usan el todo-rojo de 20 s).
- **Tiempos del semáforo iguales en todos los horarios medidos** → el baseline es un solo plan fijo.
- Aforo contado en la línea de pare (consistente con el GEH). Cola sobrante al final del verde: sobre todo en el
  **este**; en la Cra 23 ~4 vehículos en los momentos más cargados.
- Calzada de la Cra 23 ≈ 7 m (2 carriles).

**Marco legal relevante (Ley 769 de 2002, en el proyecto):** Art. 118 permite el giro a la derecha en rojo
respetando al peatón, salvo señal que lo prohíba (los autores no lo observan en el cruce; no se modela por ahora).
Art. 94 prohíbe a las motos adelantar por la derecha o entre vehículos. El filtrado observado es, en rigor, una
infracción, pero está incluido en los conteos del aforo. Decisión pendiente de los autores (ver abajo).

**Paso 4a (datos físicos, no ajuste libre):**
- Ancho de carril de la Cra 23 = 3.5 m (antes 3.2 m por defecto) en llegadas, salidas y accesos (`ajustes.edg.xml`;
  `accesos.edg.xml` ahora se carga primero).
- Moto 2.0 × 0.75 m (Bajaj Boxer CT100: 1965 × 752 mm, ficha del fabricante; SUMO usa 2.2 × 0.9 m).
- Resolución lateral 0.7 m: no mayor que el ancho de la moto y divide exacto el carril de 3.5 m (recomendación de SUMO).

**Paso 4b (barrido):** alineación del carro (center/right) × separación lateral de la moto (0.3/0.1) × largo del bus
(12/9 m) = 8 combinaciones, sobre la red del paso 4a. **Efecto: debe medirse.**

**Pendiente (después de calibrar):** modelar el semáforo de la Calle 18 como semáforo fijo aguas abajo
(requiere medir sus tiempos) para representar el bloqueo del puente.

### 2026-10-21 — ¿Es legal que las motos se filtren con el tráfico detenido? (consulta)

- Ley 769/2002, art. 94: las motos "no deben adelantar ... por la derecha o entre vehículos que transiten por sus
  respectivos carriles"; art. 96: deben "transitar ocupando un carril". **No hay una excepción expresa para tráfico detenido.**
- Art. 73: no se adelanta en intersecciones ni donde hay línea central continua (el puente tiene doble línea amarilla).
- Conceptos del MinTransporte (2025, no vinculantes): un obstáculo o un vehículo detenido "no habilita automáticamente
  a adelantar"; el comportamiento esperado es el mismo para motos y carros. No se encontró concepto que permita el filtrado.
- Manual de Señalización Vial 2024 (Res. 20243040045005): crea la señal SIM-03 "zona de espera adelantada para motos en
  intersección", que solo existe donde la autoridad la demarca tras un estudio técnico.
- Conclusión: el filtrado es, como mínimo, zona gris y más probablemente infracción. **No es una opinión jurídica.**
- Implicación metodológica: el modelo representa el comportamiento **observado** porque los conteos lo incluyen;
  no lo avala. Se excluyen las infracciones que **no** se contaron (pasarse el rojo). Decisión de los autores pendiente.
- **Decisión de los autores (2026-10-21):** se adopta la interpretación literal del art. 94 ("entre vehículos que
  *transiten*"). Avanzar de forma controlada entre vehículos **completamente detenidos** en rojo, hacia la línea de pare
  o una zona de espera, sin invadir el paso peatonal, no es "adelantar en movimiento". Es una interpretación de los
  autores, no un concepto oficial; se declara como supuesto en la tesis. Con ella el modelo sigue sin simular infracciones.
  Limitación: el modelo de subcarriles de SUMO también deja a las motos avanzar entre filas que se mueven despacio;
  el efecto debe estimarse.
- **Verificación de zona de espera para motos (2026-10-21):** en una imagen de Street View (2023) de la llegada de la
  Cra 23 sur aportada por los autores se ven la flecha de carril, una sola línea de pare y luego la cebra. **No hay
  zona de espera adelantada (SIM-03):** no hay segunda línea transversal ni pictograma de moto. El supuesto queda
  así: las motos avanzan entre vehículos detenidos **hasta la línea de pare**, sin invadir la cebra. La imagen es de
  Google y no se publica en el repositorio; confirmar en la próxima visita con foto propia.

### 2026-10-21 — Resultado del paso 4 (4a + barrido 4b) y paso 5 (reducción de carril en el puente)

**Paso 4a** (carril de 3.5 m en la Cra 23, moto 2.0 × 0.75 m, resolución lateral 0.7 m). Comparando c01, que conserva
los valores del paso 3, con el paso 3: norte de 981 a 1101 veh/h (GEH de 13.1 a 9.4); sur de 983 a 1067 (de 15.0 a 12.4).
**Barrido 4b** (semilla 1, aforo_alto; aforo_bajo cumple 4/4 en las 8 combinaciones):

| Comb. | carro latAlignment | moto minGapLat | bus length | norte (GEH) | sur (GEH) |
|---|---|---|---|---|---|
| c01 | center | 0.3 | 12 | 1101 (9.4) | 1067 (12.4) |
| c02 | center | 0.3 | 9 | 1082 (10.0) | 1056 (12.7) |
| c03 | center | 0.1 | 12 | 1093 (9.6) | 1016 (14.0) |
| c04 | center | 0.1 | 9 | 1108 (9.2) | 1018 (13.9) |
| c05 | right | 0.3 | 12 | 1138 (8.3) | 1068 (12.4) |
| c06 | right | 0.3 | 9 | 1179 (7.1) | 1116 (10.9) |
| c07 | right | 0.1 | 12 | 1106 (9.3) | 1082 (11.9) |
| c08 | right | 0.1 | 9 | 1108 (9.2) | 1116 (10.9) |

Lectura: los parámetros de comportamiento mueven poco el resultado (±~60 veh/h, parecido a la variación entre semillas
que todavía no se ha medido). Ninguna combinación llega a GEH < 5 en norte y sur.
**Avisos de SUMO:** frenadas de emergencia repetidas en `:cluster..._7_1` y `_7_0`, el carril interno donde los 2 carriles
del sur se juntaban **dentro del cruce**. El carril 0 tenía luz 'g' (ceder el paso) frente al carril 1 en pleno verde.
Unos pocos teletransportes de `sur_derecha_moto` en el carril 0 (atrapadas detrás de la cola del recto).

**Paso 5 (dato de campo + OSM):** la salida hacia el puente (`1414166243`) tiene ahora 2 carriles hasta el inicio del puente
(53.8 m, nodo `inicio_puente`, tipo zipper) y luego 1 carril (`puente_hacia_villavicencio`). Cada carril del sur sigue por
el suyo dentro del cruce. Cambiaron `ajustes.edg.xml`, `correcciones.con.xml` y los destinos en `scripts/generar_demanda.py`
(sur recto y este derecha terminan en `puente_hacia_villavicencio`). **Efecto: debe medirse.**

**Paso 5, ajuste con medidas de los autores (Google Maps, vista satelital):** calzada total de 15.6 m en el cruce;
a 22.6 m del cruce mide 13.1 m (6.9 m hacia el sur y 7.7 m hacia el norte); sobre el puente mide 7.5 m.
La vía **se va angostando** del cruce al puente, y **la llegada norte también tiene ~2 filas junto al semáforo**
(en el modelo tenía 1 carril). Cambios:
- La llegada norte `-642480900` tiene 2 carriles en sus últimos 38.2 m. El tramo del puente pasa a llamarse
  `puente_desde_villavicencio`. Conexiones explícitas: carril 0 → derecha y recto; carril 1 → recto (siguen siendo 3 movimientos).
- La reducción de la salida hacia el puente pasa de 53.8 m a 38.2 m.
- 38.2 m = punto medio entre 22.6 m (2 carriles completos) y 53.8 m (inicio del puente en OSM). Supuesto; sensibilidad pendiente.
- Consecuencia para el agente: la zona que mide en el brazo norte (`-642480900`) ahora son 38 m con 2 carriles.
  Pendiente: permitir que un brazo se mida sobre varios edges antes de reentrenar.
- **Incertidumbre de las medidas (aclaración de los autores):** las distancias y anchos salen de una foto satelital
  medida a mano y tienen error humano; las dos mitades a 22.6 m suman 14.6 m frente a 13.1 m de total, una diferencia
  de ~1.5 m. Se tratan como aproximadas: (1) la conclusión cualitativa (2 filas por sentido junto al cruce, 1 en el puente)
  no cambia con ±1 m; (2) los valores que dependen de la medida (punto de cambio de carriles, ancho de carril) se prueban
  con sensibilidad; (3) verificación en campo pendiente: observar cuántas filas se forman en rojo en el norte y en el sur
  (foto propia desde el andén), sin medir dentro de la vía.

**Paso 5, construcción de la red en 3 pasos:** al dividir tramos, netconvert recalculaba conexiones y reaparecían los giros a la
izquierda (15 movimientos). Ahora: `acacias.netccfg` (OSM) → `acacias_ajustes.netccfg` (geometría →
`acacias_geometria.net.xml`) → `acacias_conexiones.netccfg` (conexiones → `acacias.net.xml`). La advertencia
"Lane '1414166243_1' is not connected" del paso de geometría es esperada: se corrige en el de conexiones.
Verificado en la red final: 12 movimientos en el mismo orden; solo cambian los dos previstos (norte carril 1 → recto;
sur carril 1 → carril 1 de la salida). Ningún movimiento de la Cra 23 cede el paso, así que `verde_cra23` pasa de
"GGGrrrGgGrrr" a "GGGrrrGGGrrr" en `config/interseccion.yaml`.

### 2026-10-21 — Barrido sobre la red del paso 5 y paso 6 (sensibilidad de la red)

**Barrido 4b repetido sobre la red del paso 5** (semilla 1; aforo_bajo 4/4 en las 8 combinaciones). aforo_alto:
- **Norte: de ~1100 a 1337–1412 veh/h, GEH de 0.6 a 2.6 → CUMPLE.** La llegada norte de 2 carriles era la causa principal.
- Sur: 1184–1216 veh/h (GEH 8.0–8.9), no cumple. Este y oeste siguen OK.
- Con `carro.latAlignment=right` el norte queda en 1401–1412 en las 4 combinaciones, contra 1337–1344 con `center`:
  el efecto es consistente. minGapLat y el largo del bus no muestran efecto claro.
  **Se adopta c05:** solo `carro: latAlignment: right`; lo demás queda en sus valores previos.
- Ya no hay frenadas de emergencia dentro del cruce. Aparecen algunas en la unión hacia el puente
  (`:inicio_puente`, `1414166243_1`) y una en `:fin_puente_sur`.

**Diagnóstico del sur** (c06): 1476 de 1512 veh/h siguen recto hacia el puente de 1 carril; 17 % son buses y camiones.
Atendidos: 1181 recto. Espera en la red ~140 s, contra ~21 s en el norte. El cuello de botella es la unión de 2 a 1 carril.

**Paso 6:** barrido de sensibilidad de la red (`scripts/barrido_red.py`, `config/barrido_red.yaml`):
posición del cambio de carriles {22.6, 38.2, 53.8 m} × forma de unión {zipper, carril_termina} = 6 redes,
cada una construida con netconvert y verificada (12 movimientos). No modifica la red oficial. **Efecto: debe medirse.**
`generar_escenarios_aforo.py` ahora acepta atributos para cualquier tipo de vehículo (secciones carro/moto/bus/camion).

### 2026-10-21 — Resultado del paso 6 (sensibilidad de la red) y paso 7 (conductor)

Barrido de red (semilla 1, aforo_alto; aforo_bajo 4/4 en las 6 redes; carros a la derecha):

| Red | Posición | Unión | norte (GEH) | sur (GEH) |
|---|---|---|---|---|
| r01 | 22.6 m | zipper | 1295 (3.8) | 1177 (9.1) |
| r02 | 38.2 m | zipper | 1408 (0.7) | 1191 (8.7) |
| r03 | 53.8 m | zipper | 1432 (0.1) | 1203 (8.4) |
| r04 | 22.6 m | carril_termina | 1299 (3.7) | 1181 (9.0) |
| r05 | 38.2 m | carril_termina | 1411 (0.7) | 1124 (10.7) |
| r06 | 53.8 m | carril_termina | 1437 (0.0) | 1120 (10.8) |

- El **norte es sensible** a la posición del cambio de carriles: hasta 140 veh/h dentro del rango medido.
  Se declara como sensibilidad del modelo a una medida satelital.
- El **sur no depende** de la geometría de la unión (1120–1203): su límite está en otro lado.
- **Se adopta r03** (53.8 m, zipper): está dentro del rango medido y tiene el mejor ajuste.
  La advertencia "1414166243_1 is not connected" sale en el paso de geometría y es esperada.

**Paso 7:** barrido del comportamiento del conductor para todos los tipos de vehículo: sigma (imperfección del modelo
Krauss) {0.5, 0.25, 0.0} × minGap {2.5, 1.5 m}. Se espera que mueva solo al sur, porque los demás brazos no se saturan.
**Debe medirse.** El barrido anterior quedó en `results/calibracion/barrido_4b/` y cada barrido tiene ahora su carpeta.

### 2026-10-21 — Resultado del paso 7 (conductor) y paso 8 (validación)

Red r03 reconstruida (53.8 m, zipper). Barrido del conductor (semilla 1, aforo_alto; aforo_bajo 4/4 en todas):

| Comb. | sigma | minGap | norte (GEH) | sur (GEH) | cumplen |
|---|---|---|---|---|---|
| c01 | 0.5 | 2.5 | 1432 (0.1) | 1203 (8.4) | 3/4 |
| c02 | 0.5 | 1.5 | 1433 (0.1) | 1222 (7.8) | 3/4 |
| c03 | 0.25 | 2.5 | 1438 (0.0) | 1377 (3.6) | **4/4** |
| c04 | 0.25 | 1.5 | 1440 (0.1) | 1430 (2.1) | **4/4** |
| c05 | 0.0 | 2.5 | 1440 (0.1) | 1501 (0.3) | 4/4 |
| c06 | 0.0 | 1.5 | 1440 (0.1) | 1503 (0.2) | 4/4 |

- Como se esperaba, **sigma es lo que mueve el sur**; norte, este y oeste prácticamente no cambian, porque no se saturan.
- Se descarta sigma = 0 (conductor perfecto): no es realista, quita la variabilidad y produjo una colisión (c05).
- **Paso 8:** validación de c03 y c04 con 5 semillas en los 4 escenarios del aforo. `barrido_calibracion.py` admite
  ahora `semillas: [...]` y al final imprime un resumen por brazo (medio, mínimo, máximo, GEH y semillas que cumplen).
  **Debe medirse.**

### 2026-10-21 — Resultado del paso 8: CALIBRACIÓN VALIDADA

Validación con 5 semillas × 4 escenarios del aforo (`results/calibracion/validacion_conductor/`):

| Escenario | Brazo | Aforo | Simulado medio (mín–máx), sigma 0.25 / minGap 2.5 | GEH máx. |
|---|---|---|---|---|
| bajo | norte / sur / este / oeste | 716 / 696 / 280 / 152 | 711 / 704 / 286 / 146 | 2.6 |
| valle mañana | norte / sur / este / oeste | 996 / 916 / 472 / 368 | 994 / 899 / 475 / 374 | 1.4 |
| medio | norte / sur / este / oeste | 1336 / 1020 / 696 / 404 | 1342 / 998 / 721 / 409 | 2.5 |
| alto | norte / sur / este / oeste | 1436 / 1512 / 460 / 680 | 1429 / 1378 (1364–1397) / 469 / 681 | 3.9 |

- **Las 80 comparaciones cumplen GEH < 5, en las dos candidatas.** aforo_medio y aforo_valle_manana no se usaron
  para ajustar nada: cumplir en ellos es evidencia de que el modelo generaliza.
- **Elegida: sigma 0.25 y minGap 2.5.** Cambia un solo parámetro del conductor respecto a SUMO. La otra candidata
  (minGap 1.5) acerca más el sur en el aforo alto (1439), pero no hay medición que la justifique; queda como sensibilidad.
- **Sesgo conocido:** en el aforo alto el sur queda ~9 % por debajo en todas las semillas (1364–1397 de 1512).
  El modelo es algo conservador en la capacidad del puente en hora pico.
- **Limitación:** en 2 de 40 corridas hubo una colisión con teletransporte en la unión hacia el puente (con camiones),
  más frenadas de emergencia aisladas en esa unión. Es un artefacto del modelo de subcarriles con vehículos pesados
  en un estrechamiento. Su efecto sobre los flujos es despreciable (1 vehículo por corrida).
- **No modelado:** el semáforo de la Calle 18 (~260 m al norte) y el bloqueo del puente que causa a veces.
  Se declara como limitación y trabajo futuro (requiere medir sus tiempos).
- `generar_escenarios_aforo.py` aplica ahora una sección `todos` de `calibracion.yaml` a los 4 tipos de vehículo.

### 2026-10-21 — Cierre de la calibración y zona de medición de varios tramos

**Prueba de cierre** con los escenarios oficiales regenerados (sigma 0.25 en los 4 tipos), aforo_alto, semilla 1:
norte 1438, sur 1377, este 488, oeste 655 → 4/4. Coincide exactamente con c01 de `validacion_conductor`,
o sea que el pipeline oficial reproduce la validación. 0 vehículos sin terminar.

**Zona de medición por brazo (antes del reentrenamiento):** `config/interseccion.yaml` cambia `edge` por `edges`
(lista de tramos desde la línea de pare hacia atrás). El norte se mide en `-642480900` (2 carriles, ~54 m) más
`puente_desde_villavicencio` (1 carril, ~56 m), unos 110 m como antes del paso 5. Los accesos de 500 m no se miden:
la zona equivale a lo que vería una cámara en el cruce. `SumoSource` suma vehículos, detenidos y capacidad de los
tramos. `generar_accesos.py` usa el primer tramo de la lista. Prueba nueva: `tests/test_sumo_source.py`, con un traci
falso, sin abrir SUMO.

### 2026-10-21 — Zona de varios tramos validada y análisis del estado del agente

32/32 pruebas OK. Semáforo real, semilla 1, zona de medición nueva (cola promedio / máxima en vehículos detenidos):
bajo N 2.1/15, S 2.1/14, E 2.3/11, O 1.2/8 · valle N 3.3/20, S 2.9/23, E 3.7/16, O 3.0/13 ·
medio N 4.1/23, S 3.1/19, E 6.5/23, O 3.4/17 · alto N 4.9/28, S 25.4/86, E 4.6/19, O 6.1/23.

**Problema encontrado en el estado actual (cola relativa = detenidos / capacidad del tramo):** la capacidad depende del
largo del tramo que trae OSM, no del tráfico. Norte 18.8 veh (110 m), sur 50.0, este 87.8 (331 m × 2 carriles), oeste 60.4.
Con los cortes [0.1, 0.3, 0.6], en los 4 escenarios juntos el eje Dg 15 está 73 % del tiempo en "vacía", 26 % en "baja"
y **0 % en "media" y "alta"**, aunque el este llegue a 23 detenidos y en campo deje cola sobrante. El agente no puede ver
la congestión de la Dg 15. Cra 23: 52/16/16/15 %.
Propuesta: medir el estado en vehículos detenidos dentro de una zona de igual largo para todos los brazos (la que vería
una cámara) y fijar los cortes con los cuantiles observados. La recompensa y las métricas siguen usando la cola completa.
Pendiente de aprobación de los autores.
**Decisión de los autores:** se aprueba la zona de cámara. En campo las colas llegan a ~150 m como máximo; con
**100 m** una cola más larga se ve igual como "alta". Implementado: `zona_camara_m: 100` en `interseccion.yaml`;
`EstadoBrazo` tiene ahora `vehiculos_zona` y `detenidos_zona`. SumoSource cuenta los vehículos a ≤ 100 m de la línea
de pare (posición de cada vehículo; detenido = velocidad < 0.1 m/s, el mismo umbral de SUMO). El codificador usa
`cortes_detenidos_zona` (vehículos), por ahora provisionales [2, 6, 12]. `series.csv` guarda `detenidos_zona_<brazo>`.
Los cortes definitivos se calculan con `scripts/calcular_cortes_estado.py`: "vacía" = 0 y luego los percentiles 33 y
67 de los segundos con cola, juntando ambos ejes y los 4 escenarios. La recompensa y las métricas siguen usando el brazo completo.
Pruebas nuevas: zona de cámara en `test_sumo_source.py`.

### 2026-10-21 — ¿Los carriles del modelo cumplen la norma colombiana? (consulta)

- Decreto 1077 de 2015, art. 2.2.3.5.2.4 (estándares que los municipios pueden adoptar): carril urbano mínimo de 3.00 m
  sin transporte público colectivo y de 3.20 m con transporte público colectivo o de uso mixto.
  Modelo: Cra 23 = 3.5 m (medido; pasan buses intermunicipales) → por encima del mínimo. Dg 15 = 3.2 m, el valor por defecto
  de SUMO, **no medido** → igual al mínimo. Pendiente: medir la Dg 15 en la foto satelital (la vía no tiene líneas de carril).
- Ley 2251 de 2022: velocidad máxima urbana 50 km/h → modelo 13.89 m/s = 50 km/h en todas las vías.
- Criterio del modelo: representa la vía **como existe** (medida u observada), no como debería ser. Si algo no cumpliera
  la norma, se modelaría igual y se señalaría en la tesis.

### 2026-10-21 — Objetivo de los autores: simulación lo más realista posible

Pendientes de realismo, ordenados por impacto (visita de campo única propuesta para 1–3):
1. Semáforo de la Calle 18 (~260 m al norte): medir verde/amarillo/rojo y modelarlo como semáforo fijo aguas abajo
   (bloqueo del puente). Requiere recalibrar y reentrenar; el proceso ya está automatizado.
2. Conteo de vehículos por verde en norte y sur (pregunta 27): valida directamente la capacidad del modelo.
3. Fotos propias de cada llegada: demarcación, señales de prohibido girar, filas en rojo.
4. Ancho de las calzadas de la Dg 15 (foto satelital), para que ningún ancho sea el valor por defecto de SUMO.
5. Proporción aproximada de tractomulas dentro de "camión" (SUMO usa un camión de 7.1 m).
Limitaciones que se declaran (no se pueden corregir sin datos nuevos): conteos de 15 min por brazo, no simultáneos;
demanda constante dentro de la hora; peatones no modelados (cruzan en el todo-rojo).

### 2026-10-21 — Cortes del estado con colas reales y preparación del reentrenamiento

33/33 pruebas OK. Las métricas de las 4 corridas salen idénticas a las anteriores: la zona de cámara no cambia la
simulación, solo agrega columnas. Detenidos en la zona de cámara (100 m) del brazo más cargado de cada eje:

| Escenario | Cra 23: cero / p50 / p90 / máx | Dg 15: cero / p50 / p90 / máx |
|---|---|---|
| bajo | 52 % / 0 / 8 / 15 | 30 % / 2 / 6 / 11 |
| valle mañana | 45 % / 1 / 11 / 23 | 22 % / 4 / 9 / 16 |
| medio | 41 % / 2 / 13 / 23 | 18 % / 6 / 15 / 23 |
| alto | 32 % / 7 / 43 / 53 | 19 % / 6 / 13 / 23 |

**Cortes adoptados: [1, 4, 9]** → vacía 0 · baja 1–3 · media 4–8 · alta 9 o más. Frecuencia de cada nivel con el semáforo
real: Cra 23 42/16/16/25 %; Dg 15 22/25/31/22 %. Antes la Dg 15 tenía 0 % en media y alta; ahora el agente la ve.
**Entrenamiento con varios escenarios:** `entrenar.py` recibe `--escenarios` (uno o varios) y los rota (episodio k →
escenarios[k % n]). `curva_aprendizaje.csv` tiene ahora la columna `escenario`.

### 2026-10-21 — Corrección: qué conteos fueron simultáneos

Aclaración de los autores: solo los conteos del **viernes 16 (aforo_alto)** y del **lunes 19 (aforo_bajo)** se hicieron
brazo por brazo, a horas distintas. Los del **martes 20 (aforo_medio y aforo_valle_manana)** fueron **simultáneos**:
se grabó el cruce en video y se contó después. `config/escenarios_aforo.yaml` ya lo decía; la limitación anotada antes
("conteos no simultáneos") aplica solo a alto y bajo.
Consecuencia para la tesis: la calibración se ajustó con alto y bajo (no simultáneos) y se validó con medio y valle
(simultáneos, en video, no usados para ajustar), que cumplen GEH < 5 en todos los brazos y semillas. Es un respaldo fuerte.
Próximo conteo (jueves, 6:15 pm, en video): hora pico simultánea, para complementar o reemplazar aforo_alto.
Los videos existentes del martes 20 pueden servir para probar YOLO (fase 7). No se publican (privacidad, Ley 1581).

### 2026-10-21 — Lista de componentes de la parte física

Hardware disponible: ESP32, Arduino UNO (de respaldo, no necesario) e iPhone 14 como cámara de prueba (DroidCam por USB;
requiere iTunes en Windows). La lista completa está en `hardware/lista_componentes.md`. Comprar ya la electrónica barata;
los carritos a control remoto y la webcam se compran después de probar YOLO con carritos que ya tengan (riesgo R3).

### 2026-10-22 — Prueba corta de entrenamiento con los escenarios reales

33/33 OK. Cuatro episodios (uno por escenario, ε ≈ 1, es decir, decisiones casi al azar):
bajo 74 s (detenidos prom. 19.9) · valle 159 s (49.0) · medio 224 s (65.2) · alto 345 s (78.0). Tabla guardada; 33 de 96
estados visitados. Con decisiones al azar las colas son mucho mayores que con el semáforo real (medio: 65 contra 17),
por eso los primeros episodios tardan más. Estimación sin optimizar: ~200 s por episodio, unas 11 h para 200 episodios.
**Optimización:** la zona de cámara (la parte costosa, porque consulta la posición de cada vehículo) se mide solo en los
instantes de decisión, no cada segundo. La recompensa sigue usando los detenidos del brazo completo cada segundo.
`leer_estado(incluir_zona=False)` deja la zona en None; si algo la usara sin medirla, fallaría de forma visible.
`ejecutar_escenario` la sigue midiendo cada segundo (series.csv). Prueba nueva en `test_sumo_source.py`.
**Resultado de la optimización** (mismas semillas): las recompensas salen **idénticas** (−71531, −175942, −233942,
−280082), así que el comportamiento no cambió. Tiempos: 24.5 / 48.4 / 90.3 / 203.8 s (antes 74.4 / 158.7 / 224.0 /
344.7 s): 367 s en total contra 802 s, unas 2.2 veces más rápido. Estimación para 200 episodios: ~5 h o menos (los
episodios se acortan a medida que el agente explora menos y genera menos congestión). 34/34 pruebas OK.

### 2026-10-22 — Entrenamiento por paquetes (para no perder progreso)

`entrenar.py`: `--episodios` es ahora el **total**; `--paquete N` corre N episodios en esta ejecución; `--continuar`
carga la tabla guardada y sigue desde el último episodio completo. Garantías:
- Todo lo del episodio k (semilla de SUMO, escenario, ε y el azar de la exploración, con `TablaQ.reiniciar_azar(semilla)`)
  depende solo de k: entrenar de seguido o por paquetes debe dar exactamente la misma tabla. Se verifica comparando ambos modos.
- La tabla se guarda de forma segura (archivo temporal + reemplazo): un corte durante la escritura no la corrompe.
- `--continuar` exige la misma configuración (escenarios, total, agente, controlador, experimento) y que la curva tenga
  tantas filas como episodios la tabla. Sin `--continuar`, no se sobrescribe un entrenamiento existente.
- Si el programa se corta, solo se pierde el episodio en curso.
Nota: con el azar reiniciado por episodio, las recompensas no son comparables con las pruebas anteriores (prueba_aforo*).
Prueba nueva: `test_reiniciar_azar_repite_las_mismas_decisiones`.

### 2026-10-22 — Aforo del jueves 22-oct (hora pico, simultáneo, en video)

Datos ingresados por los autores en `docs/aforo/planilla_aforo.xlsx`: jueves, 18:15–18:30, los 4 brazos. Totales verificados
(suma de columnas = total de la fila). En veh/h:

| Brazo | Jueves 22 (simultáneo) | Viernes 16 (brazo por brazo) |
|---|---|---|
| Norte | 1320 | 1436 |
| Sur | 1364 | 1512 |
| Este | **948** | 460 |
| Oeste | 552 | 680 |
| Total | 4184 | 4088 |

El total es parecido, pero **el este casi duplica** el del viernes. Coincide con la observación de campo: en hora pico el este
queda con cola sobrante. Diferencias así son esperables entre días y entre conteos no simultáneos.
Nuevo escenario `aforo_pico_jueves` en `config/escenarios_aforo.yaml`.
**Paso 9:** validación externa del modelo calibrado con este conteo, que no se usó para ajustar (5 semillas).
`config/barrido_calibracion.yaml` → `validacion_jueves`. **Debe medirse.**

**Semáforo de la Calle 18** (medido el jueves 22 en hora pico, varias veces, siempre igual): verde 58 s, amarillo 3 s,
rojo 41 s, ciclo de 102 s. Queda en `config/semaforo_calle18.yaml`. Todavía no está en la red. Faltan: el desfase
respecto a nuestro semáforo (no medido), los carriles entre el puente y la Calle 18, y si la luz controla ambos sentidos.

**Respuestas de los autores sobre la Calle 18:** después del puente, la Cra 23 tiene 1 carril por sentido hasta la Calle 18;
el semáforo medido es el de los vehículos que van hacia Villavicencio; hay un semáforo por sentido, con los mismos tiempos.

**Paso 10 (preparado, se activa con `activo: true` en `config/semaforo_calle18.yaml`):**
- `generar_accesos.py` divide el acceso norte. A 260 m de nuestra línea de pare (150 m antes del brazo norte) queda el nodo
  semaforizado `calle18`. Tramos nuevos: `desde_calle18` (hacia el sur), `hacia_calle18` y `despues_calle18` (hacia el
  norte, 100 m para salir de la red); 1 carril de 3.5 m por sentido. Escribe `calle18.tll.xml` con el programa medido
  (verde 58, amarillo 3, rojo 41; los 2 sentidos con la misma luz).
- `generar_escenarios_aforo.py`: los que van hacia Villavicencio (sur recto, este derecha) terminan en `despues_calle18`;
  el `.sumocfg` carga `calle18.tll.xml`.
- `src/simulation/semaforo_calle18.py`: activa el programa medido y aplica el **desfase**. Como no está medido, se elige al
  azar con la semilla de la corrida (reproducible), así que el conjunto de semillas cubre desfases distintos.
  Se llama en `ejecutar_escenario` (que guarda el desfase en `resumen.json`) y en el entorno de entrenamiento.
  Prueba: `tests/test_semaforo_calle18.py`.
- Con `activo: false` la red y los escenarios quedan exactamente como antes (verificado).
- `barrido_calibracion.py --config <archivo>` permite elegir la definición del barrido;
  nueva `config/barrido_validacion_calle18.yaml` (5 escenarios × 5 semillas).

### 2026-10-22 — Resultado del paso 9: VALIDACIÓN EXTERNA con el jueves 22 (sin Calle 18)

Modelo calibrado sin cambios, 5 semillas, `aforo_pico_jueves` (`results/calibracion/validacion_jueves/`):

| Brazo | Aforo | Simulado medio (mín–máx) | GEH medio | GEH máx | Semillas OK |
|---|---|---|---|---|---|
| norte | 1320 | 1319 (1296–1337) | 0.4 | 0.7 | 5/5 |
| sur | 1364 | 1371 (1320–1426) | 1.0 | 1.7 | 5/5 |
| este | 948 | 938 (913–986) | 0.8 | 1.2 | 5/5 |
| oeste | 552 | 564 (539–593) | 0.8 | 1.7 | 5/5 |

**20/20 cumplen GEH < 5 (máx. 1.7)** con un conteo de otro día, simultáneo, que no se usó para ajustar y cuya demanda del
este duplica la del viernes. Es la evidencia más fuerte de que el modelo generaliza. Total acumulado: 100/100 comparaciones
con GEH < 5 en 5 escenarios. Hubo una colisión con teletransporte (s4, bus en la unión del puente): la limitación conocida.
Pendiente: paso B (activar la Calle 18 y validar los 5 escenarios).

### 2026-10-23 — Resultado del paso 10: modelo con el semáforo de la Calle 18

Paso B (`results/calibracion/validacion_calle18/`, 5 escenarios × 5 semillas): **100/100 con GEH < 5** (máx. 3.1).
Comparado con el modelo sin la Calle 18:
- aforo_alto, sur: 1397 (1392–1402), GEH medio 3.0, contra 1378 y 3.5 sin la Calle 18. Mejora un poco.
- Los demás brazos y escenarios cambian poco (±10 veh/h en promedio), como se esperaba: el GEH mide flujo atendido, y la
  Calle 18 afecta sobre todo **cómo** se forman las colas (bloqueo del puente), no cuánto pasa en una hora.
- Red verificada: el nodo `calle18` tiene 2 movimientos, sin conflictos (`GG/yy/rr`); el nodo del puente, también sin conflictos.
- Teletransportes por atasco (>300 s quieto) en `:6048329437_1_0`, la entrada al tramo hacia la Calle 18: 3 en 25
  corridas (valle s3, jueves s5 con 3 vehículos). Es la cola de la Calle 18 subiendo hasta el puente. Raros; se reportan
  como limitación. Desde ahora `ejecutar_escenario` guarda el número de teletransportes en `resumen.json`.
**Decisión: la Calle 18 queda en el modelo definitivo** (`activo: true`). Es más realista, sigue validado 100/100 y el
agente enfrentará el bloqueo del puente que se observa en campo.
Nota: la prueba de paquetes del 23-oct no es válida, porque la red cambió a mitad de la prueba. Se repite.

**Prueba de paquetes repetida (con la Calle 18 y sin cambios durante la prueba):** `prueba_seguido2` (4 episodios de
seguido) y `prueba_paquetes2` (2 + 2 con `--continuar`) dan recompensas idénticas en los 4 episodios (−62773, −179625,
−226450, −273645). Las tablas Q y los conteos de visitas guardados también son idénticos. **Entrenar por paquetes es equivalente a entrenar de seguido.**

### 2026-10-23 — Diseño del entrenamiento definitivo: escenarios de entrenamiento y de prueba

Propuesta de los autores: entrenar solo con bajo, medio y alto. Se adopta, con este diseño:
- **Entrenamiento:** aforo_bajo (1844 veh/h), aforo_medio (3456) y aforo_alto (4088): cubren todo el rango de demanda.
- **Prueba de generalización (el agente nunca los ve al entrenar):** aforo_valle_manana (2752, demanda intermedia)
  y aforo_pico_jueves (4184, hora pico de otro día, con el este casi al doble). Permite responder si el agente sirve en
  situaciones que no practicó, lo que es más exigente y más defendible que evaluar solo en escenarios conocidos.
- **150 episodios** (50 por escenario, semillas 1000–1149). ε baja de 1.0 a 0.05 en los primeros **100** episodios
  (antes 150) y los últimos 50 son casi sin exploración. Si la curva sigue mejorando al final, se evalúa ampliar.
- Por qué 150 y no menos: la tabla tiene 96 estados × 2 acciones; cada par necesita muchas visitas para que su valor Q se
  estabilice (con α = 0.1 cada actualización mueve el valor solo un 10 %). Con 4 episodios se visitaron 36 de 96 estados.
`graficar_curva.py`: ahora dibuja una línea por escenario (detenidos promedio, con media móvil de 5 episodios del mismo
escenario) y la exploración ε. Imprime por escenario los detenidos de los primeros y de los últimos 5 episodios.
Mezclar escenarios en una sola línea escondería el aprendizaje, porque cada escenario tiene su propio nivel de tráfico.

### 2026-10-23 — Capa de seguridad frente a la norma colombiana (consulta)

- Ley 769/2002, art. 118: rojo = detenerse; amarillo = desalojar el cruce y no entrar; verde = vía libre. Parágrafo 1:
  intermitencia amarilla para la vía con prelación y roja para las demás (se usará como modo seguro del ESP32).
  La secuencia de la capa de seguridad (verde → amarillo → todo-rojo → verde del otro eje) es coherente con eso.
- Amarillo (3 s) y todo-rojo (0 s tras la Cra 23, 20 s tras la Dg 15) **copian el semáforo real** que opera la autoridad;
  el agente no puede cambiarlos, solo la duración del verde (10–60 s).
- Referencia técnica internacional (ITE, fórmula cinemática, no es norma colombiana): amarillo ≈ 1 + v/(2a) =
  1 + 13.89/(2 × 3.05) ≈ 3.3 s a 50 km/h. El amarillo real (3 s) está ligeramente por debajo. Observación, no conclusión.
- **Pendiente:** verificar valores (amarillo, despeje, verde mínimo, ciclo) en el Manual de Señalización Vial
  (capítulo 4, Semáforos; Res. 20223040045295 de 2022, modificada por la Res. 20243040045005 de 2024). El PDF del
  MinTransporte no se pudo descargar desde la sesión de Claude: lo descargan los autores a `docs/normativa/`.

### 2026-10-23 — Lectura del Manual de Señalización Vial, capítulo 7 (Semáforos)

Documentos en `docs/normativa/` (aportados por los autores). El capítulo 7 es de la **edición de mayo de 2004**. Hay
ediciones posteriores (2015 y la vigente, adoptada con la Res. 20223040045295 de 2022 y modificada por la Res.
20243040045005 de 2024); hay que confirmar si estos puntos cambiaron. Hallazgos relevantes para la capa de seguridad:
- 7.2.1.3 b: "En ningún caso se cambiará de luz verde a luz roja ... sin que antes aparezca el amarillo" → se cumple
  (secuencia obligatoria del SafetyGuard).
- 7.2.1.3 c: "Es recomendable que ... siempre se incluya un período de todo rojo" → el semáforo real tiene 0 s de
  todo-rojo después de la Cra 23 (y 20 s después de la Dg 15). Es una recomendación, no una obligación.
- 7.2.1.3 c: nunca combinaciones simultáneas de colores (salvo flechas o rojo+amarillo) → se cumple (2 fases sin conflicto).
- 7.2.2.3: el verde no debe ser menor que el tiempo de cruce de peatones, "excepto cuando se dispone de un intervalo
  especial para peatones"; con alta demanda se logra buena eficacia "con lapsos de luz verde tan breves como de 15 s".
  Ejemplo del Manual: verde mínimo = 5 + tiempo de cruce − amarillo. El verde mínimo actual del agente (10 s) está por
  debajo de esos 15 s.
- 7.2.2.4: los semáforos de tiempo fijo a menos de 1000 m que controlan el mismo tránsito deben operar coordinados y con
  ciclos iguales. La Calle 18 (ciclo de 102 s) y nuestro cruce (~101 s) parecen coordinados. Un control adaptativo
  aislado rompería esa coordinación: es una limitación que hay que declarar.
- 7.2.3: el Manual contempla los semáforos accionados por el tránsito y el "control adaptable al tránsito" donde los
  volúmenes fluctúan y donde varían mucho entre las calles → respaldo normativo del enfoque de la tesis.
- 7.4.1.3: en operación intermitente, amarillo intermitente en la vía preferencial y rojo intermitente en las demás; el
  paso a intermitencia se hace durante el verde de la calle principal → modo seguro del ESP32.

### 2026-10-23 — Manual de Señalización Vial 2024 (vigente), capítulo 4 (Semaforización)

Archivo: `docs/normativa/Manual-Sen-alizacio-n-Vial-2024.pdf` (1425 páginas). Hallazgos:
- **4.4 (figura 4-9): amarillo de 3 s para 50 km/h.** El semáforo real y la capa de seguridad cumplen.
- **4.4.3:** nunca de verde a rojo sin amarillo; sin combinaciones verde-amarillo ni verde-rojo; intermitencia amarilla en
  la vía principal y roja en la secundaria → se cumple (y define el modo seguro del ESP32).
- **4.4.4 Tiempo de seguridad (tiempo intermedio):** Ti = (Dd + Lv)/Vd − De/Ve + Tp, con Vd = 10 m/s (vehículo recto),
  Ve = 7 m/s y Tp = 2 o 3 s. Tiempos intermedios típicos entre 4 y 9 s.
  Estimación propia con la geometría de la red (recorrido recto de la Cra 23 por el cruce: 24–27 m; carro Lv = 5 m;
  De entre 0 y 5 m; Tp = 2 s): **Ti ≈ 4.4–5.2 s** (con bus de 12 m, ≈ 5.9 s). Hoy, después del verde de la Cra 23,
  el tiempo intermedio es solo el amarillo (3 s + 0 s de todo-rojo): **queda por debajo**. Después de la Dg 15
  (3 + 20 = 23 s) cumple con holgura.
  Es una estimación con supuestos conservadores; el valor oficial lo debe calcular un profesional idóneo.
- **4.8.2 Tráfico actuado:** la duración de los intervalos se modifica con un algoritmo y sensores, "enmarcada dentro de
  valores máximos, mínimos". **Es la categoría del Manual que corresponde a este sistema** (control local con detección
  en los accesos). En el Manual, "adaptativo" (4.8.4) se refiere a control centralizado de corredor o red, con detectores
  en los tramos. Hay que cuidar la terminología en la tesis.
- **4.8 (monitoreo):** el controlador debe detectar conflictos verde-verde o módulos apagados y pasar a intermitencia
  general → en simulación, `SumoActuator.verificar()` detiene la corrida; en la maqueta, el ESP32 pasará a intermitencia.
- **4.8.6:** ciclos recomendados entre 60 y 120 s; por encima de 120 s, solo en circunstancias particulares; no se
  recomiendan ciclos de más de 150 s. Con la capa actual, el ciclo máximo posible del agente es 60+3+0+60+3+20 = 146 s.
  Se reportará la distribución de ciclos del agente en la evaluación.
- **4.8.6:** los planes deben definirlos un profesional idóneo y ponerlos en marcha la autoridad → el prototipo es académico.
- El Manual 2024 no fija un verde mínimo numérico en los apartados revisados (el de 2004 menciona 15 s como lapso eficaz).
**Decisiones pendientes de los autores** (el entrenamiento aforo_v1 está en curso con la capa anterior):
(1) verde mínimo de 15 s; (2) todo-rojo después de la Cra 23 para el agente, para cumplir el tiempo de seguridad.
**Decisión de los autores (2026-10-23): verde mínimo de 15 s y opción B.** Implementado:
- `config/controlador.yaml`: `seguridad.verde_min_s` = 15 (antes 10). Nuevo perfil `seguridad_norma` con todo-rojo
  después de la Cra 23 = 2 s (tiempo intermedio de 5 s, Manual 2024, 4.4.4).
- `SafetyGuard.desde_config(config, perfil)`: "real" (semáforo medido) o "norma". El agente usa siempre "norma", tanto
  al entrenar como al evaluar. El baseline `tiempos_fijos` usa "real". Nueva referencia `tiempos_fijos_norma`: el semáforo
  real con el todo-rojo de la norma (opción C, para mostrar el efecto de esos 2 s).
- Pruebas nuevas de los perfiles en `tests/test_safety_guard.py`.
- El entrenamiento `aforo_v1`, iniciado con la capa anterior, se descarta y se reinicia.
- La calibración no cambia: con el semáforo real, el verde mínimo de 15 s no interviene (verdes de 55 y 20 s).
**Entrenamiento definitivo iniciado:** `aforo_v2` (bajo, medio, alto; 150 episodios en paquetes de 50; verde mínimo de 15 s;
el agente con el perfil de seguridad "norma"). `aforo_v1` se descarta (capa de seguridad anterior).

### 2026-10-23 — Revisión del aforo original (`planilla_aforo_original_2026-10-20.xlsx`)

- **Conteos:** las 16 filas originales (vie 16, lun 19, mar 20 ×2) son **idénticas** a las de la planilla en uso, y en las
  20 filas actuales el total coincide con la suma de las columnas. La migración no alteró ningún dato.
- **Ya corregido en la planilla en uso:** el brazo "Norte (Cra 23" estaba truncado (por eso el Resumen original no mostraba
  el norte); la columna Día tenía números (16, 19) o estaba vacía (martes).
- **Hoja Semaforo, inconsistencias:**
  1. Un mismo semáforo debe tener un solo ciclo, pero con los rojos medidos sale Cra 23: 55+3+45 = 103 s y Dg 15:
     20+3+77 = 100 s. La diferencia de 3 s es error de cronómetro. Implica un todo-rojo total de 19–22 s por ciclo; el modelo
     usa 20 s (ciclo de 101 s), dentro de ese rango.
  2. Los ciclos 5–8 de la Dg 15 están fechados el 20-oct a las 20:15, 21:15, 22:15 y 23:15. El conteo de la noche fue el
     lunes 19 de 20:15 a 21:15, y la separación de una hora entre ciclos es rara. Probablemente la fecha o las horas están mal
     digitadas. **Por confirmar con los autores.**
  3. La columna Todo-rojo está vacía (se observó después: ~22 s después de la Dg 15). La Calle 18 (jueves 22) no está
     en la hoja (está en `config/semaforo_calle18.yaml`).
- **No es inconsistencia, pero conviene explicarlo:** en el aforo del viernes cada brazo se contó en un cuarto de hora distinto
  (sur 18:00, norte 18:15, este 18:30, oeste 18:45). Puede explicar en parte por qué el este del viernes (460 veh/h, de 18:30
  a 18:45) es mucho menor que el del jueves (948 veh/h, de 18:15 a 18:30).
**aforo_v2, paquete 1 (episodios 0–49, ε de 1.00 a 0.53, 34 min):** detenidos promedio (primeros 5 → últimos 5 episodios
del escenario): bajo 11.2 → 9.8; medio 63.0 → 37.9; alto 75.4 → 69.2. 52 de 96 estados visitados. El aprendizaje es
claro en medio, moderado en alto y pequeño en bajo. Todavía no es comparable con el semáforo real (exploración alta,
otra ventana de medición).
**Análisis de la curva de aforo_v2 tras el paquete 1** (`models/aforo_v2/curva_aprendizaje.png`): medio baja con claridad
desde el episodio ~20 (media móvil de ~62 a ~38), aunque con mucha dispersión entre episodios (28–55) por la exploración.
Alto baja poco y tiende a estabilizarse cerca de 69–70. Bajo se mantiene en ~10, con menos dispersión.
Comportamiento aprendido (primeros 5 → últimos 5 episodios de cada escenario): pide "cambiar" en menos decisiones
(bajo 51 → 36 %, medio 47 → 38 %, alto 45 → 32 %) y arma ciclos más largos (unos 71–72 s → 77–82 s, estimado como
3600 / verdes de la Cra 23). Interpretación (hipótesis): cada cambio cuesta amarillo + todo-rojo (5 s o 23 s), así que
cambiar muy seguido desperdicia tiempo; el agente aprende a sostener los verdes. Sus ciclos siguen siendo más cortos
que los 101 s del semáforo real.
**aforo_v2, paquete 2 (episodios 50–99, ε de 0.53 a 0.06, 25 min):** detenidos promedio (últimos 5 episodios del paquete 1
→ últimos 5 del paquete 2): bajo 9.8 → 9.3; **medio 37.9 → 22.7**; **alto 67.7 → 61.2** (un episodio atípico de 82).
61 de 96 estados visitados. Comportamiento en los últimos 5 episodios: pide "cambiar" en 14–20 % de las decisiones y
arma ciclos de ~96–107 s (estimado), del orden del ciclo real (101 s). Hay que medir si el reparto del verde es distinto
al del plan fijo; eso lo dirá la evaluación.
**aforo_v2, paquete 3 (episodios 100–149, ε = 0.05, 19 min).** Detenidos promedio, media del paquete (desviación estándar):
bajo 8.2 (0.7), **estable**; medio 20.7 (6.3) con dos atípicos al inicio, segunda mitad 18.9, **estable**; alto 48.6 (8.0),
primera mitad 50.8 y segunda mitad 46.7, **todavía bajando y con mucha variación** (38–62).
63 de 96 estados visitados; 47 con 20 visitas o más. Ciclos aproximados: bajo 102 s, medio 107 s, alto 111 s
(menos de 120 s, el límite recomendado por el Manual 2024); pide "cambiar" en 11–14 % de las decisiones.
**Decisión:** bajo y medio convergieron; alto no del todo. Se amplía el entrenamiento a 240 episodios (80 por escenario).
`entrenar.py --continuar --ampliar` permite subir el total; es equivalente a haber pedido 240 desde el inicio, porque la
semilla, el escenario, ε y el azar del episodio k no dependen del total. Respaldo de aforo_v2 con 150 episodios
(fuera del repositorio) por si hace falta comparar.
Copia del modelo con 150 episodios: `models/aforo_v2_150/` (sin cambios después de esta fecha).

### 2026-10-23 — Scripts de la comparación final

- `scripts/comparar_controladores.py --modelo <m>`: corre `tiempos_fijos` (semáforo real), `tiempos_fijos_norma` (real con
  todo-rojo de 2 s) y `qlearning`, con las 30 semillas de evaluación, en los 5 escenarios. Las corridas quedan pareadas por
  semilla (mismos vehículos). Guarda una fila por corrida en `results/comparacion/<m>/corridas.csv`, con métricas de viaje,
  cola, verdes, ciclos (promedio, máximo, % de ciclos de más de 120 s), teletransportes, desfase de la Calle 18 y
  decisiones de respaldo. Se puede retomar: no repite lo ya guardado. El tripinfo se borra al terminar cada corrida.
- `simular(..., zona="al_decidir")`: mide la zona de cámara solo cuando el agente va a decidir
  (`ControladorQLearning.va_a_decidir`). Debe dar el mismo resultado que medirla cada segundo; se verifica.
- `scripts/analizar_comparacion.py --modelo <m>`: medianas, diferencia %, Wilcoxon pareado bilateral (α = 0.05),
  correlación biserial de rangos como tamaño del efecto. Métrica principal: tiempo de espera promedio. Secundarias:
  cola, tiempo de viaje, tiempo perdido, velocidad y throughput, con corrección de Holm. Salidas: `resultados.csv`,
  `resultados.md` y diagramas de cajas `espera_<escenario>.png`. Se verificaron Holm y la biserial con ejemplos a mano.
- `requirements.txt`: se agrega scipy.

### 2026-10-24 — Ampliación de aforo_v2 a 240 episodios (142 min)

Detenidos promedio por bloque (media, desviación estándar):
- bajo: 100–149 → 8.2 (0.7); 150–194 → 8.3 (0.6); 195–239 → 8.8 (0.9)
- medio: 100–149 → 20.7 (6.3); 150–194 → 18.0 (1.6); 195–239 → 20.0 (2.7)
- alto: 100–149 → 48.6 (8.0); 150–194 → 47.7 (8.2); 195–239 → 52.7 (6.9)
66 de 96 estados visitados (51 con 20 visitas o más). Ciclos aproximados: 100 / 105 / 111 s.
**Lectura:** la ampliación no siguió mejorando. Las diferencias entre bloques son del tamaño de la variación entre episodios.
En alto, la variación (de ~7 a 8) refleja la demanda aleatoria y el desfase de la Calle 18, que cambia con cada semilla.
**Se da el entrenamiento por convergido.**
**Modelo para la evaluación (decidido ANTES de ver resultados de evaluación):** `aforo_v2` con 240 episodios, el último
del procedimiento. `aforo_v2_150` queda solo como análisis de sensibilidad opcional. No se elige el modelo según los
resultados de las semillas de evaluación, para no sesgar la comparación.

### 2026-10-24 — Prueba de los scripts de comparación (6 semillas, aforo_bajo; solo prueba de funcionamiento)

- **Verificación de exactitud:** `ejecutar_escenario` (zona medida cada segundo) y `comparar_controladores` (zona solo al
  decidir) dan la misma espera para qlearning con la semilla 1: 23.241796200345423 s en ambos. La versión rápida es exacta.
- 18 corridas en ~8 min. Análisis, tablas y gráfica generados sin errores. Con 6 semillas nada es significativo; **no son
  resultados de la tesis**. Se movieron a `results/comparacion/prueba_6semillas_aforo_v2/`.
- Observación: con la Calle 18 activa, la espera total del semáforo real en aforo_bajo es ~25 s (antes ~15 s), porque
  incluye el rojo de la Calle 18. Ese tiempo es igual para todos los controladores y diluye las diferencias. Se agrega,
  **antes de la corrida completa**, la métrica secundaria `espera_cruce_promedio_s`: vehículo-segundos detenidos en los
  4 brazos dentro de la ventana, dividido por los vehículos medidos. La métrica principal NO cambia (espera total
  promedio): es la que experimenta el usuario y la más conservadora.
- Comportamiento del agente en bajo, semilla 1: verde de la Cra 23 casi siempre hasta el máximo (60 s, 35 cambios forzados),
  verde de la Dg 15 de ~16 s; ciclo de ~104 s. Se analizará en la corrida completa si cambia según el escenario.

### 2026-10-24 — RESULTADOS de la comparación final, iteración 1 (aforo_v2, 240 episodios; 450 corridas; 30 semillas)

Métrica principal: espera total promedio, mediana de 30 semillas, Wilcoxon pareado (α = 0.05), r = biserial de rangos.

| Escenario | Real | Real + norma | Agente | Agente vs real | Agente vs real + norma |
|---|---|---|---|---|---|
| bajo | 24.09 | 24.87 | 24.14 | +0.2 %, p = 0.61 (ns) | **−2.9 %, p = 0.026** |
| valle (no visto) | 25.91 | 27.12 | 26.65 | +2.9 %, p = 0.061 (ns) | **−1.7 %, p = 0.006** |
| medio | 27.62 | 29.47 | 29.03 | **+5.1 %, p < 0.001 (peor)** | −1.5 %, p = 0.82 (ns) |
| alto | 59.40 | 73.03 | 55.85 | **−6.0 %, p = 0.013 (mejor)** | **−23.5 %, p < 0.001** |
| jueves (no visto) | 31.96 | 34.79 | 35.43 | **+10.8 %, p = 0.002 (peor)** | +1.8 %, p = 0.11 (ns) |

- Con las mismas reglas de seguridad (frente a real + norma), el agente es mejor en 3 escenarios y no es peor en ninguno.
  Frente al semáforo real (con 2 s menos de todo-rojo), solo mejora en alto; empata en bajo y valle; es peor en medio y jueves.
- Los 2 s de todo-rojo de la norma cuestan entre +3 % (bajo) y +23 % (alto) de espera con el plan fijo.
- 0 teletransportes y 0 vehículos sin terminar en las 450 corridas; ningún ciclo de más de 120 s.
- **Hipótesis (diferencia significativa frente al semáforo real): se cumple solo en el escenario alto.**

**Diagnóstico con la tabla Q (interpretabilidad):** la política aprendida es casi un plan fijo: Cra 23 en verde hasta el
máximo (60 s en todos los escenarios) y Dg 15 con ~17–20 s. Con verde en la Cra 23 el agente elige "mantener" incluso con
la Cra 23 "vacía" y la Dg 15 "alta" (por ejemplo, 8696 visitas en el estado vacía/alta con 40 s o más).
**Causa probable:** el estado mide vehículos DETENIDOS. Durante su verde, el eje que tiene el paso casi no tiene detenidos
(los vehículos se mueven), así que se ve "vacío" tanto si la vía está desocupada como si pasa un flujo grande. El agente no
puede saber si el verde se está aprovechando. Además, volver a la Cra 23 cuesta 23 s de transición, lo que favorece ciclos
largos. Esto explica el jueves: el este se carga (cola de 13.7 frente a 9.8 del real) y el agente no le alarga el verde
porque nunca lo "ve" ocupado.
**Propuesta de iteración 2 (pendiente de aprobación):** que el eje en verde se describa con los vehículos PRESENTES en su
zona de cámara (en movimiento o detenidos), como la detección de brechas de un control actuado (Manual 2024, 4.8.2). Un
solo cambio de diseño; la cámara puede medirlo.
**Iteración 2 aprobada por los autores. Implementación:**
- `CodificadorEstado`: `estado.modo` = "detenidos" (iteración 1) o "presentes_en_verde" (iteración 2). En el modo nuevo, el
  eje en verde se mide por los vehículos presentes en su zona de cámara y el eje en rojo por sus detenidos. Las 96
  situaciones y los cortes de tiempo no cambian. Los cortes de detenidos [1, 4, 9] se mantienen.
- `cortes_presentes_zona_verde`: provisional [1, 5, 10]. Se calculan con
  `calcular_cortes_estado.py --modo presentes`, usando solo los escenarios de entrenamiento (bajo, medio, alto)
  para no usar información de los escenarios no vistos.
- **Reproducibilidad:** al evaluar, el controlador Q-Learning usa la configuración del agente guardada en el modelo,
  no la de `config/agente.yaml`. aforo_v2 se sigue evaluando con su estado original.
- `series.csv` guarda ahora `vehiculos_zona_<brazo>`. Pruebas nuevas: `TestCodificadorPresentesEnVerde`.
**Cortes de presentes** (`calcular_cortes_estado.py --modo presentes`, semáforo real, bajo/medio/alto, semilla 1):
**[1, 3, 14]**, es decir, vacía 0 · baja 1–2 · media 3–13 · alta 14 o más vehículos presentes del eje en verde.
Frecuencia: Cra 23 4/19/36/40 %; Dg 15 12/39/41/7 %. Vehículos presentes durante el verde (p50 / p90): Cra 23 bajo 2/9,
medio 7/17, alto 29/40; Dg 15 bajo 1/3, medio 4/14, alto 4/13.
**Entrenamiento de la iteración 2:** `aforo_v3`, todo igual que aforo_v2 (bajo, medio, alto; 240 episodios; ε baja en 100;
semillas 1000–1239; perfil de seguridad "norma") salvo el estado. Un solo cambio respecto de la iteración 1.

### 2026-10-25 — RESULTADOS de la iteración 2 (aforo_v3, estado con "presentes en verde"; 450 corridas)

Espera total promedio (mediana de 30 semillas) frente al semáforo real (24.09 / 25.91 / 27.62 / 59.40 / 31.96 s):
| Escenario | Agente v3 | vs real | vs real + norma | v3 frente a v2 (mismas semillas) |
|---|---|---|---|---|
| bajo | 22.72 | −5.7 %, p = 0.19 (ns) | −8.6 %, p = 0.007 | mejor en 24/30 semillas (−1.3 s) |
| valle | 25.97 | +0.3 % (ns) | −4.2 %, p < 0.001 | mejor en 21/30 (−0.5 s) |
| medio | 28.65 | +3.7 %, p < 0.001 (peor) | −2.8 % (ns) | mejor en 17/30 (−0.3 s) |
| **alto** | **149.81** | **+152 % (mucho peor)** | +105 % | peor en 30/30 (+95 s) |
| **jueves** | **75.75** | **+137 % (mucho peor)** | +118 % | peor en 29/30 (+40 s) |

En alto y jueves, el agente v3 da a la Dg 15 verdes de ~42–44 s (el semáforo real, 20 s) y ciclos de ~130 s (100 % de
los ciclos de más de 120 s). La cola del sur se dispara (alto: 37.1 frente a 26.1; jueves: 35.4 frente a 6.7) y hay muchos
teletransportes por atasco (alto 217, jueves 108, en total en las 90 corridas de cada escenario). Los semáforos de referencia
son idénticos en las dos comparaciones (verificado).

**Diagnóstico: la recompensa "no ve" parte del costo.** La recompensa suma los detenidos en los brazos (zona de medición, 110–330 m),
pero en hora pico la cola del sur sale del brazo y sigue por el tramo de acceso de 500 m, que no se mide. Una vez lleno el brazo,
su castigo deja de crecer: el agente puede alargar el verde de la Dg 15 (que sí reduce detenidos medidos) mientras la cola del sur
crece sin castigo fuera de la zona. Además, los vehículos teletransportados por atasco desaparecen y "alivian" la recompensa.
Con la iteración 1 el problema existía, pero su política (Cra 23 siempre al máximo) lo ocultaba. En el entrenamiento, alto de v3
parecía bien (52.8 detenidos) justamente porque el costo estaba fuera de lo medido.
**Lección para la tesis:** la recompensa debe medir TODO el costo que el agente puede causar (*reward hacking*).
**Propuesta de iteración 3 (pendiente de aprobación):** el estado de v3 sin cambios (lo que ve una cámara) y la recompensa con
los detenidos de los brazos + sus tramos aguas arriba (accesos y el tramo de la Calle 18). Un solo cambio.
Protocolo: las decisiones de diseño se validan primero con semillas de VALIDACIÓN aparte (no las 1–30); las 30 semillas de
evaluación se usan una vez con el modelo final. Todas las iteraciones se reportan.

### 2026-10-25 — Corrección de la forma del puente (detectada por los autores en sumo-gui)

En la vista de sumo-gui, los dos sentidos del puente aparecían separados por un "hueco". En la red, `puente_desde_villavicencio`
y `puente_hacia_villavicencio` tenían formas desplazadas a cada lado de la línea central (hueco de ~6 m entre carriles) y medían
~74 m en vez de ~64 m (distancia real entre sus nodos). Probable origen: la geometría de dos vías distintas de OSM más el
desplazamiento automático de netconvert. Corrección: `sumo/network/puente_forma.edg.xml`, cargado en el paso 3
(`acacias_conexiones.netccfg`): los dos sentidos sobre la misma línea central, de nodo a nodo, con `spreadType="right"`.
Efecto esperado: el recorrido por el puente se acorta unos 10 m en cada sentido; la dinámica (carriles, conexiones,
semáforos) no cambia. **Hay que revalidar la calibración** (`config/barrido_validacion_puente.yaml`, 5 escenarios × 5 semillas).
Las iteraciones 1 y 2 se evaluaron con la red anterior; queda registrado. La iteración 3 se entrena y evalúa con la red corregida.
**Verificación de la red corregida (2026-10-25):** los carriles del puente quedaron pegados (separación entre sus ejes de
~3.3 m, con carriles de 3.5 m) y cada sentido mide 59.6 m de carril (antes 73.7 m). Sin hueco en sumo-gui (captura de los
autores). El semáforo sigue con 12 movimientos en el mismo orden; conexiones del puente, de la Calle 18 y de la unión
alternada sin cambios. El tramo suelto al suroccidente es la salida hacia Acacías (calzada separada, correcta) que termina
en el borde de la red.

### 2026-10-25 — Revalidación con el puente corregido e implementación de la iteración 3

**Revalidación** (`results/calibracion/validacion_puente/`, 5 escenarios × 5 semillas): **100/100 con GEH < 5**
(máx. 3.56, sur del aforo alto con 1399 de 1512). Antes de la corrección: 100/100, máx. 3.15. La calibración se mantiene.

**Iteración 3 (`aforo_v4`), un solo cambio respecto de la iteración 2:** la recompensa incluye los detenidos aguas arriba de
cada brazo (`edges_aguas_arriba` en `interseccion.yaml`: accesos de 500 m; en el norte, también el tramo de la Calle 18).
El estado no cambia (presentes en verde). `EstadoBrazo.detenidos_aguas_arriba` es un campo solo de simulación.
`config/agente.yaml`: `recompensa.incluir_aguas_arriba: true`. Prueba nueva en `test_sumo_source.py`.
Nota: los "detenidos promedio" de la curva de aprendizaje incluyen ahora la cola aguas arriba, así que no se comparan
directamente con las curvas de v2 y v3.
**Protocolo de validación:** semillas de validación 101–110 (`semillas.validacion`). `comparar_controladores.py --carpeta <nombre>`
guarda la validación aparte. Primero se valida en bajo, alto y jueves; las 30 semillas de evaluación se usan una sola vez.

### 2026-10-25 — Revisión de la vía y la señalización (pedida por los autores antes de la iteración 3)

`docs/campo/revision_via_senalizacion.md`: tabla de todos los elementos del modelo con su fuente y su estado
(✔ medido/observado, ≈ supuesto declarado, ❓ por confirmar) y 8 preguntas para los autores. Pendiente: sus respuestas.
El entrenamiento de aforo_v4 espera a que se resuelvan los ❓ que cambien el modelo.
**Respuestas de los autores (2026-10-25):** (1) los carriles de la Dg 15 miden lo mismo que los de la Cra 23 → **3.5 m**
(antes 3.2 m por defecto), aplicado en `ajustes.edg.xml` a las llegadas, salidas y accesos de la Dg 15; (2) hay subida
notoria pero no drástica de Villavicencio hacia Acacías → no se modela (SUMO plano), limitación declarada; (3) giro a la
izquierda prohibido por señal ✔; (4) giro a la derecha en rojo prohibido ✔; (5) sin señales de velocidad ni resaltos → 50 km/h ✔;
(6) sin restricciones aguas abajo en la Dg 15 ✔; (7) poco tráfico cruzando en la Calle 18 → sin tráfico transversal ✔;
(8) en la llegada norte, los que giran a la derecha van por la derecha ✔.
Único cambio: el ancho de la Dg 15. Hay que reconstruir la red y revalidar (`config/barrido_validacion_dg15.yaml`)
antes de entrenar aforo_v4. Con 3.5 m, la resolución lateral de 0.7 m divide exacto todos los carriles de la red.
**Forma de la Cra 23 sur (2026-10-25, observada por los autores en netedit):** en OSM, las dos calzadas separadas al sur del
cruce terminan en el mismo punto, así que se doblaban una hacia la otra y el separador terminaba en punta antes del semáforo.
`sumo/network/cra23_sur_forma.edg.xml` (paso 3) quita ese último tramo doblado: cada calzada llega recta al cruce.
Ancho, carriles y conexiones no cambian. Se revalida junto con el cambio de ancho de la Dg 15.

### 2026-10-25 — Bloqueo en el puente (revalidación validacion_dg15)
- Revalidación tras el ancho de la Dg 15 (3.5 m) y la forma de la Cra 23 sur: **99/100** con GEH < 5 (GEH medio 1.20; antes 0.83).
  Las otras 24 corridas iguales a la validación anterior. Falla: `aforo_valle_manana`, semilla 4: sur 98 veh/h (aforo 916),
  GEH 36.3, 756 vehículos sin terminar. Desde t ≈ 400 s casi no salen vehículos por la Calle 18.
- Diagnóstico en sumo-gui (`scripts/ver_corrida.py`, misma semilla y desfase): fila detenida en el puente **sin nada adelante**;
  teleports "waited too long (jam)" en `:6048329437_1_0` (extremo norte del puente). `sur_recto_camion.19`: lateral offset −1.45 m,
  0.90 m **fuera de la vía**, lcState `left|strategic|urgent|overlapping|blocked`. `sur_recto_carro.28` detenido en el zipper
  (`1414166243_1`, `overlapping|sublane|blocked`).
- Causa (geometría verificada en la red): en el zipper `inicio_puente` el carril derecho se corría **3.49 m en 8.0 m**
  (el carril izquierdo ya estaba alineado con el puente). Con el modelo de subcarriles el camión quedó desplazado y no pudo volver.
  En ~160 corridas de calibración anteriores solo ocurrió esta vez, pero en cientos de episodios de entrenamiento sí afectaría.
- Corrección (un solo cambio): `sumo/network/puente_transicion.edg.xml` con `endOffset = 31.2 m` en `1414166243`: la unión ocupa
  el tramo medido 22.6–53.8 m (se va angostando), en vez de 8 m. **Efecto: debe medirse** (semilla 4 en sumo-gui + revalidación).
- Primer intento (solo `endOffset`): en sumo-gui la vía quedó con huecos blancos y, al revisar la red, los carriles internos
  seguían rectos y conservaban el **mismo escalón de 3.5 m en 8 m** al final → no corregía nada. Se complementa con
  `puente_transicion.con.xml` (forma recta de cada carril interno: el derecho se cierra 3.4 m en ~39 m) y
  `puente_transicion.nod.xml` (contorno del nodo para dibujar una sola calzada que se angosta). Efecto: debe medirse.
- Segundo intento (endOffset + forma + contorno): el recorte se aplicó dos veces (el contorno del nodo ya recorta el tramo de
  2 carriles en los 22.6 m) y `1414166243` quedó de 0.10 m: la unión empezaba a la salida del cruce. Se retira `endOffset`
  (archivo movido a `sumo/network/_descartado/`); quedan el contorno del nodo y la forma de los carriles internos.
- **Corrección de lo dicho arriba ("solo ocurrió una vez"):** eso vale para las corridas de calibración (solo semáforo real).
  En las comparaciones de las iteraciones 1 y 2 (`results/comparacion/aforo_v2` y `aforo_v3`, red anterior con el escalón)
  hubo corridas con atasco (> 50 vehículos sin terminar):
  - semáforo real: 0 de 150 en cada comparación;
  - tiempos de norma: 5 de 150 (valle s13 y s14, medio s10, alto s1 y s16);
  - Q-Learning v2: 1 (alto s8); Q-Learning v3: 2 (alto s16, jueves s5).
  No está verificado que todos se deban a la unión del puente (debe revisarse si reaparecen con la red corregida).
  Consecuencia: las ventajas de v2 frente a la norma (sobre todo −23.5 % en alto) están **infladas** por atascos de la
  simulación en la norma. Esos resultados son de redes ya reemplazadas; la evaluación final se hará con la red corregida.
- **Resultado de `validacion_transicion`** (red con transición gradual, 5 escenarios × semillas 1–5): **98/100 con GEH < 5**,
  GEH medio 0.93, máximo 6.52; **0 corridas con vehículos sin terminar** (el atasco de valle s4 desapareció).
  Todos los brazos quedan igual que en `validacion_puente`, salvo **alto–sur: 1325 veh/h simulados vs 1512 aforados**
  (antes 1399; GEH medio 5.0, 2 de 5 semillas > 5). La transición larga reduce algo la capacidad de la unión en pico.
  Lectura: cumple el criterio usual de GEH < 5 en ≥ 85 % de los conteos (aquí 98 %). El aforo alto no fue simultáneo
  entre brazos; el pico simultáneo del jueves sí ajusta en el sur (1390 vs 1364, GEH 0.9). Se registra como limitación:
  en aforo_alto el sur atiende ~12 % menos de lo contado. Avisos nuevos: frenadas de emergencia en `:inicio_puente_0_*`
  (cremallera); observación de campo de los autores: algunos carros sí frenan antes de entrar al puente.

### 2026-10-26 — Iteración 3 (aforo_v4): entrenamiento y validación (semillas 101–110)
- Entrenamiento: 240 episodios (3 paquetes de 80) con la red corregida. Detenidos (últimos episodios): bajo 14.3→~10,
  medio 108→~28, alto 185→~100 pero inestable (rebotes en ep. ~160 y al final). Curva: `models/aforo_v4/curva_aprendizaje.png`.
- Validación, espera total promedio (s), 10 semillas pareadas, Wilcoxon:
  | Escenario | Real | Norma | QL v4 | QL vs real |
  |---|---|---|---|---|
  | bajo | 23.99 | 25.11 | 22.07 | −8.0 % (p = 0.014; 8/10 semillas mejor) |
  | valle | 25.88 | 38.33 | 27.64 | +6.8 % (p = 0.70) |
  | medio | 28.79 | 29.16 | 30.05 | +4.4 % (p = 1.0) |
  | alto | 62.95 | 85.78 | 140.93 | **+123.9 %** (p = 0.002; 0/10) |
  | jueves | 32.28 | 40.91 | 50.43 | **+56.2 %** (p = 0.002; 0/10) |
  Sin atascos (0 corridas con > 50 sin terminar en QL); teleports QL 0–4 por escenario. En alto: verde Dg 15 36 s (real 20),
  ciclo 121 s (61 % de ciclos > 120 s), retraso de entrada 20.6 s (real 0.3). Jueves: verde Dg 15 30 s, ciclo 116 s.
- **Mejor que la iteración 2 en pico (+152 % / +137 %), pero sigue fallando en alto y jueves.**
- Diagnóstico (tabla Q): los estados más visitados en pico son "Cra 23 = cola alta, Dg 15 en verde con 1–2 presentes";
  la política aprendida es **mantener** el verde de la Dg 15 (miles de visitas), hasta que el verde máximo obliga a cambiar.
  Hipótesis: cambiar desde la Dg 15 cuesta de inmediato 3 s de amarillo + 20 s de todo-rojo medido (todos detenidos), y con
  γ = 0.9 por decisión de 5 s (horizonte ≈ 10 decisiones ≈ 50 s, menos de un ciclo) ese costo inevitable pesa más ahora que
  después: el agente "aplaza" el cambio. Debe verificarse.
- **Iteración 4 (aforo_v5):** único cambio `aprendizaje.gamma` 0.9 → 0.95 en `config/agente.yaml`
  (horizonte efectivo 1/(1−γ) = 20 decisiones de 5 s ≈ 100 s ≈ un ciclo). Red, estado, recompensa, α, ε y semillas sin cambios.
  Predicción a verificar: en alto/jueves el verde de la Dg 15 baja de ~36/30 s hacia ~20 s y la espera se acerca a la del real.
- **aforo_v5 con γ = 0.95 por decisión: DETENIDO** en el paquete 1 (carpeta movida a `models/_descartado/aforo_v5_gamma095_norma`).
  Motivo: al revisar la bitácora se encontró el diagnóstico del 2026-10-07 nunca aplicado (sesgo por pasos de distinta
  duración): cambiar desde la Dg 15 dura 38 s (3 + 20 + 15) y desde la Cra 23 18 s, frente a 5 s de mantener. Con γ por
  decisión, ese costo se cobra completo en un paso → el agente sobrevalora "mantener", sobre todo con la Dg 15 en verde
  (justo lo observado en la validación de v4). Subir γ solo lo suavizaba.

### 2026-10-26 — Iteración 4b: descuento por segundo + intervalos del semáforo real
- **Descuento por segundo (semi-Markov; Bradtke y Duff, 1995):** recompensa del paso = −Σ γ^t·detenidos_t y valor
  futuro × γ^(duración del paso). `config/agente.yaml`: `descuento: por_segundo`, `gamma: 0.99` (horizonte 100 s ≈ un
  ciclo; 0.99^5 = 0.951 por decisión de 5 s). Código: `qlearning.py` (`factor_futuro`, `suma_descontada`, guarda
  `descuento`), `entorno_sumo.py`, `entrenar.py` (la curva sigue registrando la recompensa SIN descuento, comparable).
  Modelos anteriores se cargan como "por_decision".
- **Decisión de los autores: el agente usa los intervalos de cambio del semáforo real** (perfil "real": amarillo 3 s,
  todo-rojo 0 s tras la Cra 23 y 20 s tras la Dg 15), no los +2 s del perfil "norma". Justificación: comparación en
  igualdad de condiciones con el semáforo en operación; observación de campo de los autores: las líneas de pare de la
  Dg 15 están retiradas del borde de la Cra 23 (aumenta De en la fórmula del Manual 4.4.4 y reduce el tiempo intermedio
  necesario). La verificación formal del tiempo intermedio queda como limitación. `config/agente.yaml`:
  `perfil_seguridad: real`. En la evaluación, el perfil del agente se lee del modelo (`ejecutar_escenario.perfil_seguridad`);
  v2–v4 siguen evaluándose con "norma". Recomendación: quitar "tiempos_fijos_norma" de la evaluación final (300 corridas).
- Son 2 cambios a la vez: el perfil es una condición del experimento (no una hipótesis); la hipótesis evaluada es el
  descuento por segundo. Pruebas: 31/31 OK (test_agente + test_safety_guard, entorno de Claude).

### 2026-10-26 — Auditoría antes de entrenar aforo_v5: 5 correcciones (iteración 4b completa)
Auditoría de código + validación de aforo_v4. Además del descuento por segundo y del perfil "real" (arriba):
1. **Cola de entrada invisible:** en alto, con QL v4 los vehículos esperaron 20.6 s para poder entrar a la red (real 0.3 s);
   SUMO los deja fuera de la red y no contaban en la recompensa. → `recompensa.incluir_entrada_pendiente: true`
   (suma `len(traci.simulation.getPendingVehicles())` cada segundo). Solo afecta el entrenamiento.
2. **Fin del episodio como estado final:** el episodio termina por tiempo (3600 s) pero el tráfico sigue. →
   `aprendizaje.bootstrap_al_cortar: true` (el corte por tiempo sigue valorando el estado siguiente).
3. **Niveles de tiempo que no representaban el plan real** ([20, 40] para ambos ejes: 41 s y 55 s eran el mismo estado).
   → cortes por eje alineados con el plan: Cra 23 [45, 55], Dg 15 [20, 30]. Siguen siendo 96 estados.
4. **Partir del semáforo real (pedido de los autores):** 20 episodios siguiendo el plan 55/20 (aprende su valor), luego
   `TablaQ.iniciar_desde_plan`: Q(otra acción) = Q(plan) × 1.01 → la política inicial es exactamente el plan real; el agente
   solo se aparta si la experiencia muestra algo mejor. Exploración ε 0.3 → 0.05 en 100 episodios (antes 1.0: azar total).
   La curva marca `politica` = plan_real / agente. Control de coherencia: los episodios plan_real deben rendir como el real.
5. **Verde máximo por eje** (decisión de los autores, opción "recomendada"): Cra 23 70 s, Dg 15 25 s (antes 60/60);
   ciclo máximo 70+3+0+25+3+20 = 121 s. Manual 2024 cap. 4: 60–120 s recomendado; > 120 s solo en circunstancias particulares
   y periodos cortos; no > 150 s; **con paso peatonal exclusivo no se recomiendan > 100 s** (los peatones cruzan en el
   todo-rojo de 20 s; el real ya opera con 101 s) → se discute como limitación. Opción descartada: ciclo ≤ 100 s (sin margen).
- Revisado y correcto: calibración, separación de semillas, SafetyGuard, métricas (la espera total incluye el retraso de
  entrada), Wilcoxon/Holm.
- Pendiente (posible iteración posterior): el nivel "alta" de la Cra 23 (≥ 9 detenidos) se satura en pico.
- Se rompe a propósito la regla de un cambio a la vez: son correcciones de errores de una auditoría, no hipótesis separadas,
  y hacerlas una por una costaría ~4 días de entrenamiento; lo evaluado es el sistema completo contra el semáforo real.
- Las tablas Q de v2–v4 no se reutilizan (estados y condiciones distintas); se conservan como historia del desarrollo.
- Ojo: `ejecutar_escenario` usa la config ACTUAL de controlador.yaml; re-evaluar v2–v4 ahora usaría los verdes máximos nuevos.
- Pruebas (entorno de Claude, sin SUMO): test_agente + test_safety_guard 39/39 OK.
- **Segunda revisión (falla encontrada en la corrección 4):** en la fase "plan", Q-Learning valora el futuro con
  max_a' Q(s', a'); la acción que el plan no toma nunca se prueba y vale 0, así que el máximo la elegía y el futuro
  parecía gratis → los valores del plan quedaban sesgados. Corrección: en esa fase el futuro se valora con
  Q(s', acción del plan) (evaluación de la política del plan, tipo SARSA). `TablaQ.actualizar(..., accion_siguiente)`.
  Prueba nueva; 40/40 OK (sin SUMO).

### 2026-10-27 — Iteración 4b (aforo_v5): entrenamiento y validación (semillas 101–110)
- Entrenamiento 240 episodios (20 siguiendo el plan real + 220 agente). Detenidos, paquete 3 vs plan real: bajo 8.9 vs 10.1,
  medio 21.5 vs 23.2, alto 53.7 vs 61.6 (alto muy variable, sd 13).
- Validación, espera total promedio (s), 10 semillas pareadas, Wilcoxon (sin "norma": el agente usa el perfil real):
  | Escenario | Real | QL v5 | Diferencia | p | QL mejor en |
  |---|---|---|---|---|---|
  | bajo | 23.99 | 20.85 | −13.1 % | 0.002 | 10/10 |
  | valle (no entrenado) | 25.88 | 23.38 | −9.7 % | 0.002 | 10/10 |
  | medio | 28.79 | 26.11 | −9.3 % | 0.002 | 10/10 |
  | alto | 62.95 | 55.40 | −12.0 % | 0.084 | 9/10 |
  | jueves (no entrenado) | 32.28 | 38.71 | +19.9 % | 0.002 | 0/10 |
  Tiempo de viaje: −4 % en bajo/valle/medio, −11.4 % en alto (p = 0.010), +4.3 % en jueves. Throughput igual (±1 %).
- **Primera iteración que mejora al semáforo real en pico (alto) y en tráfico normal.** En alto, 9 de 10 semillas mejoran
  entre 1 % y 28 %; la semilla 101 se atascó (723 sin terminar, 72 teleports) y por eso p = 0.084.
- Problemas: (1) **atascos con QL**: alto s101 y jueves s103 (con el real, ninguno). Causa por investigar en sumo-gui.
  (2) **jueves peor en todas las semillas**: la cola del este crece (QL 14–29 vs real 9–17). El agente aprendió verdes cortos
  para la Dg 15 (15–16 s en bajo/medio; ninguno de los escenarios de entrenamiento tiene una Dg 15 tan cargada como el
  jueves: este 948 veh/h vs 460–696) → no generaliza a ese patrón; además la cola "alta" (≥ 9) se satura.
  Decisiones de respaldo (estados no visitados): alto 27, jueves 16 por corrida (de ~410–620).
- Ciclo: alto 116.8 s promedio (51 % de ciclos > 120 s: usa el máximo de 121 s), verde Cra 23 68.9 s.

### 2026-10-27 — Atasco de aforo_v5 (alto, semilla 101): mismo empalme del fin del puente
- sumo-gui (t ≈ 2180 s): `sur_recto_carro.202` en `:6048329437_1_0` (cruce interno de 0.1 m al final norte del puente),
  lateral offset +1.25 m, 0.4 m FUERA del carril por la izquierda, lcState `overlapping|sublane|blocked`, 260 s quieto.
  Causa: con la cola detenida sobre el puente (1 carril), las motos avanzan por la derecha y SUMO corre a los carros a la
  izquierda; en un tramo normal se reacomodan, pero en un cruce interno de 0.1 m no hay espacio y el vehículo queda trabado.
  El agente lo dispara más (verdes de hasta 70 s para la Cra 23 → más cola sobre el puente), pero es una falla de la red:
  también le pasó al semáforo real (validacion_dg15, valle s4). Probablemente es también el atasco de jueves s103.
- Corrección: el nodo 6048329437 (solo era el corte de OSM entre el puente y el tramo a la Calle 18) se TRASLADA a la
  Calle 18 y es el nodo del semáforo (`scripts/generar_accesos.py`); se eliminan `desde_calle18` y `hacia_calle18`; los dos
  sentidos del puente llegan de forma continua hasta la Calle 18 (`puente_forma.edg.xml`, misma recta).
  `config/interseccion.yaml`: aguas arriba del norte = solo `acceso_norte` (el tramo de 150 m ahora es parte de
  `puente_desde_villavicencio`, que pasa de ~60 a ~210 m; la zona de cámara sigue siendo de 100 m).
  Requiere reconstruir (generar_accesos + pasos 2 y 3), revalidar la calibración y reentrenar.

### 2026-10-27 — Registro del tiempo de cómputo (metodología)
- `comparar_controladores.py` y `barrido_calibracion.py` guardan ahora `segundos_reloj` por corrida (el entrenamiento ya lo
  hacía). Nuevo `scripts/resumen_computo.py` → `docs/resumen_computo.md` (solo datos guardados; no estima lo no medido).
- Al 2026-10-27: **2553 horas de tráfico simuladas** (≈ 106 días continuos; sin contar la copia `aforo_v2_150`);
  cómputo medido 14.1 h (solo entrenamiento); 1353 corridas anteriores sin registro de duración.
- Nota: se editó `barrido_calibracion.py` mientras corría `validacion_calle18_continua`; Python ya había cargado el script,
  así que esa corrida no cambia (y no tendrá la columna de tiempo).

### 2026-10-27 — Causa de fondo de los atascos: vehículos empujados fuera del carril estando detenidos
- Revalidación `validacion_calle18_continua` (en curso): valle s5 se atascó (espera máx. 2387 s; 35 de 43 vehículos con
  > 300 s son sur→Villavicencio). sumo-gui: `sur_recto_bus.13` en `:6048329437_1_0`, que ahora es el cruce interno del
  semáforo de la Calle 18 (0.1 m): lateral offset 0.90 m, left side 3.90 m > 3.5 m, `left|overlapping|sublane|blocked`.
  → Quitar el empalme del puente movió el lugar del atasco, pero no la causa.
- Causa de fondo: con la cola detenida en el carril único, SUMO desplaza de lado a carros/buses/camiones para dejar pasar
  motos hasta sacarlos del carril; en un cruce interno de 0.1 m no pueden volver.
- Corrección: `config/calibracion.yaml` → `lcMaxSpeedLatStanding: 0` para carro, bus y camión (un vehículo detenido no se
  mueve de lado). Requiere regenerar los escenarios y revalidar (la validación en curso queda descartada).
- **Resultado `validacion_sin_empuje`:** 99/100 GEH < 5 (media 0.87, máx. 6.46 en alto–sur: 1368 vs 1512 veh/h), 0 corridas
  con vehículos sin terminar. Bloqueo temporal en medio s1 (~100 vehículos con > 200 s de espera hacia t ≈ 2100–2240 s;
  todos terminan): vigilar teleports en la validación del agente. **Red cerrada.**

### 2026-10-27 — Iteración 5 (aforo_v6): entrenamiento con 4 escenarios
- Igual que aforo_v5 (5 correcciones de la auditoría) + red corregida (puente continuo hasta la Calle 18, vehículos
  detenidos sin desplazamiento lateral) + **el pico del jueves en el entrenamiento** (v5 falló ahí: Dg 15 cargada, patrón
  que no vio). 320 episodios (4 escenarios × 80; los 20 primeros siguen el plan real). Valle queda como escenario nunca visto
  (prueba de generalización). Las semillas de entrenamiento (1000–1319) no se cruzan con validación ni evaluación.

### 2026-10-27 — Iteración 5 (aforo_v6): entrenamiento y validación (semillas 101–110)
- Entrenamiento: 320 episodios (4 escenarios), 3.4 h de cómputo. Paquete 2, mediana de detenidos vs plan real: bajo 8.7 vs
  9.4, medio 21.5 vs 23.1, alto 56.0 vs 61.8, jueves 37.8 vs 41.0. Episodios extremos en alto (ep. 274: 583 detenidos).
- Validación, espera total promedio (s), 10 semillas pareadas, Wilcoxon:
  | Escenario | Real | QL v6 | Diferencia | p | QL mejor en |
  |---|---|---|---|---|---|
  | bajo | 24.16 | 20.88 | −13.5 % | 0.002 | 10/10 |
  | valle (nunca visto) | 27.92 | 23.73 | −15.0 % | 0.002 | 10/10 |
  | medio | 29.45 | 27.35 | −7.1 % | 0.002 | 10/10 |
  | **alto** | 64.77 | 50.29 | **−22.4 %** | **0.037** | 8/10 |
  | jueves | 40.41 | 57.41 | +42.1 % | 0.049 | 1/10 |
  Alto: tiempo de viaje −17.1 % (p = 0.037), throughput +1.8 % (p = 0.004), cola sur 15.5 vs 26.6. **Primera mejora
  significativa en pico.** Ningún atasco del agente (0 corridas con vehículos sin terminar; teleports 1–16 por escenario).
- Jueves: peor en 9/10. Verde Dg 15 17.7 s (real 20), cola del este 35.5 vs 17.1. Hipótesis: el estado no distingue alto de
  jueves (en ambos la Cra 23 está en "alta" y la Dg 15 "alta" = 9 o más, sea 10 o 35): el agente aplica la política de alto
  (poco verde a la Dg 15) en jueves. Corrección candidata: más niveles de cola (saturación, pendiente desde la auditoría).
- El semáforo REAL se atascó en jueves s110 (855 sin terminar, 81 teleports): revisar en sumo-gui (posible otra falla de red).
- Política de v6 (`models/aforo_v6/politica.md`): con la Dg 15 en verde y menos de 20 s, si la Cra 23 está "alta" (≥ 9
  detenidos) el agente CAMBIA aunque la Dg 15 tenga 3–13 vehículos presentes (miles de visitas). En jueves la Cra 23 siempre
  está "alta" → la Dg 15 recibe ~15 s. Refuerza la hipótesis de saturación del estado.

### 2026-10-27 — Iteración 6 (aforo_v7, decisión de los autores: una sola iteración más antes de la evaluación final)
- Único cambio: 5 niveles de cola en vez de 4 (nivel "muy alta"), recalculados con datos: semáforo real, red actual,
  semilla 1, 4 escenarios de entrenamiento; cortes = [1, p33, p67, p90] de los segundos con cola
  (`calcular_cortes_estado.py --percentiles 33 67 90`). Estados: 5 × 5 × 2 × 3 = 150.
- Riesgo declarado: es la 6.ª iteración evaluada con las mismas semillas de validación (101–110); se reportará el número de
  iteraciones. La evaluación final (semillas 1–30) no se ha usado y se corre una sola vez.
- `ver_tabla_q.py` generalizado (cortes de tiempo por eje y 4 o 5 niveles).
- Cortes calculados (red actual, real, semilla 1, 4 escenarios): detenidos [1, 4, 11, 23] (Cra 23 37/17/19/14/13 %,
  Dg 15 20/22/34/23/2 %); presentes [1, 5, 16, 30] (Cra 23 3/24/32/28/13 %, Dg 15 9/48/32/11/0 %). Con ellos la Cra 23 en
  rojo distingue alto (p50 11, p75 36) de jueves (p50 3, p90 18). El nivel "muy alta" casi no ocurre en la Dg 15 (cortes
  comunes a ambos ejes; esos estados usan el plan real de respaldo). 150 estados.
- Dato de referencia (semilla 1, real): alto espera 77.6 s; jueves 30.9 s.

### 2026-10-27 — Segunda auditoría antes de entrenar aforo_v7
- Queda al menos un mecanismo de atasco: en la validación de v6 el **semáforo real** se atascó en jueves s110 (855 sin
  terminar, 77 teleports, cola máxima del ESTE 173 vehículos); el entrenamiento de v6 tuvo episodios extremos en alto
  (ep. 274). No es el empuje lateral (ya corregido): hay que ubicarlo.
- Herramientas nuevas para ubicar atascos sin revisar corrida por corrida: `simular(..., ruta_log)` guarda los avisos de
  SUMO (`--error-log`) con carril y tiempo; `comparar_controladores.py` guarda uno por corrida en `<carpeta>/avisos_sumo/`;
  `ejecutar_escenario.py` en `avisos_sumo.log`; `scripts/resumen_avisos.py` resume teleports y frenadas por carril.
  El entrenamiento registra `teletransportes` por episodio en la curva.
- **Resultado (real, jueves s110, con lcMaxSpeedLatStanding = 0):** 77 teleports; el PRIMERO a t = 1907 s en
  `:6048329437_1_0` (cruce interno del semáforo de la Calle 18): el mismo mecanismo. El resto (este 816899410#0, puente,
  sur, 1414166243) son consecuencia de la cola que se forma detrás. → Impedir que un vehículo DETENIDO se corra no basta:
  también se desplaza al avanzar lento en la fila. Es una limitación conocida del modelo de subcarriles de SUMO (propenso a
  bloqueos; lista sumo-user). Se renuncia a eliminarlo por completo y se **limita su efecto**: `time-to-teleport` 300 → 120 s
  (`config/calibracion.yaml: subcarriles.tiempo_teleport_s`, escrito en los .sumocfg por `generar_escenarios_aforo.py`).
  Riesgo: teleportar vehículos detenidos de verdad en pico; se controla con los avisos por corrida (la calibración ahora
  también los guarda) y se reportan los teleports de cada controlador.
- Revalidación: `config/barrido_validacion_teleport120.yaml`.
- **Cambio de decisión (autores, mismo día):** se descarta el teleport global a 120 s (alteraría colas reales de la
  intersección principal); se vuelve al valor de SUMO (300 s). En su lugar, **desatasco dirigido en la Calle 18**
  (`src/simulation/desatascador.py`, `config/calibracion.yaml: desatasco_calle18`): vehículo en la línea de pare o dentro
  del cruce interno del semáforo, con su luz en VERDE, sin nadie adelante a menos de 15 m y quieto 20 s seguidos → se
  traslada al inicio del tramo de salida (`traci.vehicle.moveTo`). Justificación: dato de campo (con el verde de la
  Calle 18 pasan todos) + un vehículo real arranca en 2–3 s. Se aplica igual a todos los controladores y en el
  entrenamiento; se cuenta por corrida (`desatascos_calle18`) y se registra cada evento.
- Pruebas (traci falso): actúa en el artefacto; NO actúa en rojo, con alguien adelante, lejos de la línea de pare, antes
  de 20 s, ni si el vehículo se movió; umbral < 5 s rechazado. 7/7 OK.
- Verificación pendiente antes de seguir: (1) reproducir real jueves s110 (debe desatascarse cerca de t ≈ 1620 s, sin la
  cola del este); (2) corridas normales sin desatascos (falsos positivos); (3) revalidación de la red.
- **Prueba A (real, jueves s110):** desatasco en t = 1628 s (`sur_recto_carro.180`, como se predijo ~1620 s); 0 vehículos
  sin terminar (antes 855), espera total 35.0 s (antes 106.9), cola máx. del este 36 (antes 173). Pero 1 teleport por
  "junction collision": el carro se ubicó en la posición 0.1 del tramo de salida, con su parte trasera aún en el cruce, y
  chocó con un camión que estaba trabado A SU LADO (latGap −0.65: dos vehículos lado a lado en un carril, como señalaron
  los autores). Corrección: se ubica con todo su largo dentro del tramo (largo + 3 m). Repetir la prueba A.
- **Verificación del desatasco (2026-10-28):**
  | Corrida (semáforo real) | Antes | Con desatasco |
  |---|---|---|
  | jueves s110 (atasco conocido) | 855 sin terminar, 77 teleports, espera 106.9 s | 0 sin terminar, **0 teleports**, 1 desatasco (t = 1628 s), espera 35.7 s |
  | alto s1 | espera 77.6 s | 1 desatasco (t = 3294 s, dentro del cruce), 0 teleports, espera **58.8 s** |
  | jueves s1 (sin atasco) | espera 30.90 s | **0 desatascos, espera 30.90 s (idéntica)** |
  → Corrige el artefacto, no actúa cuando no hay artefacto (resultado idéntico) y no deja colisiones. **Hallazgo:** alto s1
  tenía un atasco artificial OCULTO (sin vehículos sin terminar) que subía la espera del semáforo real de 58.8 a 77.6 s:
  las validaciones anteriores pudieron favorecer al agente en alto por estos artefactos. La evaluación final se hará con
  el desatasco activo para todos los controladores.
- `config/barrido_validacion_teleport120.yaml` movido a `config/_descartado/`. Nueva: `barrido_validacion_desatasco.yaml`.

### 2026-10-28 — Revisión de cumplimiento normativo tras los cambios
- Cumple: amarillo 3 s siempre completo; nunca dos ejes en verde (SafetyGuard, pruebas); verde mínimo 15 s; verde máximo
  por eje 70/25 s; ciclo máximo 121 s (< 150 s); ciclos > 120 s solo en pico (v6: 0–2.8 % de los ciclos, jueves 22 %);
  el desatasco solo mueve vehículos con su luz en VERDE (nunca hace pasar en rojo) y solo en la Calle 18; giros a la
  izquierda y derecha en rojo siguen prohibidos (conexiones de la red); el agente no controla la Calle 18.
- Limitaciones ya declaradas: todo-rojo 0 s tras la Cra 23 (igual al real, por debajo de la estimación del tiempo
  intermedio del Manual 4.4.4); ciclos > 100 s con peatones en el todo-rojo (el real ya usa 101 s); filtrado de motos
  (interpretación del art. 94, Ley 769).
- Hallazgo: el ciclo MÍNIMO posible del agente es 15 + 3 + 0 + 15 + 3 + 20 = 56 s, debajo de los 60 s recomendados.
  No se registraba: `comparar_controladores.py` guarda ahora `ciclo_minimo_s` y `ciclos_menores_60_pct`.
  Propuesta: verde mínimo de la Cra 23 = 20 s (ciclo mínimo 61 s; mantiene las decisiones alineadas con el plan: 20, 25 … 55 s).
- **Aplicado (decisión de los autores):** verde mínimo por eje, Cra 23 = 20 s y Dg 15 = 15 s (`config/controlador.yaml`;
  `SafetyGuard.verde_min(eje)`; usado por el entorno, el controlador Q-Learning y la validación de tiempos fijos).
  Ciclo posible del agente: 61–121 s. No cambia la calibración (el real 55/20 cumple) ni los aforos; v7 aún no se había
  entrenado. Prueba nueva (ciclo mínimo 20+3+15+3+20); 41/41 OK sin SUMO.
- **Resultado `validacion_desatasco` (red final):** **100/100 con GEH < 5** (media 0.85, máx. 3.6 en alto–sur: 1390 vs
  1512 veh/h), 0 vehículos sin terminar, **0 teleports** en las 25 corridas. Frenadas de emergencia: 77 en total
  (~3 por corrida), casi todas en la cremallera antes del puente (observación de campo: los conductores frenan ahí);
  se reporta como limitación menor. **Red y reglas cerradas** para el entrenamiento de v7 y la evaluación final.
- Error al lanzar aforo_v7 (2026-10-28): `EntornoSumo` sumaba `teletransportes_episodio` antes de crearlo (se iniciaba
  después del primer avance en `reset`). Corregido: se inicia antes. No se había completado ningún episodio
  (la carpeta solo tenía el encabezado de la curva); se relanza el mismo comando.

### 2026-10-28 — Iteración 6 (aforo_v7): entrenamiento y validación (semillas 101–110)
- Entrenamiento 320 episodios, 2.1 h. 2.ª mitad, mediana de detenidos vs plan real: bajo 8.9 vs 9.4, medio 21.9 vs 22.1,
  alto 51.9 vs 55.9, jueves 32.9 vs 34.5. Teleports 108 y desatascos 69 en todo el entrenamiento (sobre todo alto).
- Validación, espera total promedio (s) [mediana], Wilcoxon:
  | Escenario | Real | QL v7 | Dif. (media) | p | QL mejor en |
  |---|---|---|---|---|---|
  | bajo | 24.16 [23.9] | 22.13 [22.0] | −8.4 % | 0.014 | 8/10 |
  | valle | 26.60 [27.1] | 25.32 [25.3] | −4.8 % | 0.131 | 6/10 |
  | medio | 28.68 [28.8] | 28.20 [28.3] | −1.6 % | 0.625 | 5/10 |
  | alto | 64.77 [64.4] | 61.54 [44.4] | −5.0 % | 0.084 | 9/10 |
  | jueves | 33.28 [33.3] | 61.88 [31.9] | +85.9 % | 0.492 | 7/10 |
  Con el verde mínimo de 20 s el ciclo mínimo fue 61 s y el máximo 121 s (cumple). Jueves mejoró frente a v6
  (7/10 semillas iguales o mejores; Dg 15 18.8 s). En alto, 9 de 10 semillas mejoran 10–45 %.
- **Dos corridas del agente con bloqueo grave** (el real: ninguno): alto s110 (espera 210.7 s, 51 sin terminar, 88 teleports:
  colisión en la cremallera a t = 2858 s y luego bloqueo DENTRO del cruce principal, carriles internos del cluster) y
  jueves s108 (322.5 s, 1280 sin terminar, 97 teleports, 40 desatascos: desde t ≈ 630 s la Calle 18 se traba una y otra vez;
  el desatasco mueve un vehículo cada 20 s pero no basta). Sin esas dos corridas, el agente gana o empata en todas.
- Hipótesis (por verificar en sumo-gui): (1) en la Calle 18, un vehículo trabado del OTRO sentido (hacia el sur, con cola
  del brazo norte adelante, por eso el desatasco no lo toca) invade el carril hacia el norte; (2) en alto, vehículos del sur
  entran al cruce sin espacio a la salida (el tramo de 2 carriles después del cruce mide 9.9 m) y bloquean el cruce.
- sumo-gui (v7, jueves s108): `este_derecha_carro.6` quieto 200 s en la línea de pare de la Calle 18 (pos 210.00 de
  `puente_hacia_villavicencio_0`), BIEN ubicado en su carril (offset −0.85, lados 0.00/1.80), lcState `stay|sublane`
  (no bloqueado de lado), luz en verde. → No es él: algo adelante lo detiene, y por eso el desatasco no actúa (exige
  "nadie adelante"). Hipótesis: un vehículo quieto en el tramo de salida (despues_calle18).
- Ampliación del desatasco: en las SALIDAS LIBRES (carriles de salida del semáforo que terminan la red: el tramo hacia
  Villavicencio) nada puede detener a un vehículo; el de más adelante que lleve 20 s quieto se adelanta (largo + 3 m).
  No aplica a salidas que siguen a otra vía (p. ej. hacia el brazo norte, donde una cola es real). 9/9 pruebas OK.
  Verificación: repetir v7 jueves s108 y alto s110 y ver los eventos (el carril indica si fue en la salida).
- Verificación (v7 jueves s108, desatasco ampliado): resultado IDÉNTICO (322.5 s, 40 desatascos, 97 teleports); ningún
  evento en la salida → hipótesis "vehículo quieto en la salida" DESCARTADA. Clave: desatasco a t = 628 s y luego nada
  hasta t = 1559 s, aunque el carro y la moto estuvieron lado a lado en la línea de pare de t ≈ 631 a 931 s (teleport).
  Nueva hipótesis: cada uno ve al otro como "líder" con distancia negativa (está al lado) → el criterio "nadie adelante"
  fallaba. Cambio: líder con distancia negativa = al lado, no adelante. Prueba de bloqueo mutuo; 10/10 OK.
  Además, diagnóstico: todo vehículo quieto 60 s en la línea de pare sin desatasco queda registrado con la luz y el
  líder que veía (se imprime en ejecutar_escenario), para confirmar o descartar la hipótesis con datos.
- Alto s110: no hubo desatascos; el bloqueo es en el CRUCE PRINCIPAL (colisión en la cremallera a t = 2858 s y luego
  vehículos atrapados en carriles internos del cluster desde t ≈ 3626 s). Problema distinto, pendiente.
- Repetición con el criterio de "al lado" + diagnóstico (v7 jueves s108): 91 desatascos y AÚN 1290 sin terminar (353 s).
  El diagnóstico muestra el patrón real: **en casi cada ciclo de la Calle 18 (~100 s), el primer vehículo de la fila queda
  quieto en la línea de pare con la luz en VERDE ('G') y SIN NADIE ADELANTE** (líder None); solo 3 de 48 casos tenían un
  vehículo al lado. El desatasco lo saca a los 20 s, pero al siguiente ciclo pasa lo mismo → la Calle 18 deja pasar casi nada.
  La red no tiene conflictos en ese nodo (request foes 00, carriles internos separados 3.5 m, alineados con el puente).
  Causa interna de SUMO no identificada (posible lógica de entrada al cruce con el modelo de subcarriles). Tras 5 intentos de
  corrección en la zona de la Calle 18 se plantea eliminar ese semáforo (opción B).

### 2026-10-28 — Se quita el semáforo de la Calle 18 (decisión de los autores, opción B)
- Motivo: bloqueos artificiales recurrentes del simulador en ese cruce (diagnóstico arriba) tras 5 intentos de corrección.
  Justificación: observación de campo (con su verde pasan todos) y la calibración casi no cambió al agregarlo
  (afectaba la forma de las colas, no el volumen por hora). Riesgo/limitación: se pierde el efecto de la cola de la
  Calle 18 sobre el puente en pico; el modelo se recalibra contra los aforos (GEH).
- Cambios: `config/semaforo_calle18.yaml` activo: false (tiempos medidos conservados); `puente_forma.edg.xml`: el nodo
  6048329437 vuelve a su posición de OSM (fin del puente); hacia Villavicencio el puente termina en salida libre (destino
  `puente_hacia_villavicencio`); acceso norte de 500 m hasta el fin del puente (`generar_accesos.py`, rama general).
  El desatasco queda en el código pero inactivo (no existe el semáforo `calle18`). Brazo norte: -642480900 (41 m) +
  puente_desde_villavicencio (~60 m) = ~101 m ≥ zona de cámara de 100 m.
- Revalidación: `config/barrido_validacion_sin_calle18.yaml`.
- Red reconstruida sin Calle 18 (verificada en el archivo): semáforo principal con 12 movimientos, sin TLS `calle18`,
  puente hacia Villavicencio de 58 m con salida libre, acceso norte 498.5 m. Brazo norte = 41 + 58 = 99 m (1 m menos que
  la zona de cámara; sin efecto práctico).
- **Resultado `validacion_sin_calle18`:** 100/100 con GEH < 5 (media 0.89, máx. 4.77 en alto–sur: 1361 vs 1512 veh/h),
  0 vehículos sin terminar, **0 teleports**, 52 frenadas (cremallera). El sur de alto no subió al quitar la Calle 18 →
  el cuello de botella es la unión de 2 a 1 carril antes del puente, no la Calle 18. **Red final.**

### 2026-10-28 — Iteración 7 (aforo_v8): misma configuración que v7, red final sin Calle 18
- Agente idéntico a v7 (5 niveles de cola, verde mínimo 20/15 s, verde máximo 70/25 s, perfil real, descuento por
  segundo, arranque desde el plan real, 4 escenarios, 320 episodios). Única diferencia: la red.

### 2026-10-29 — Iteración 7 (aforo_v8): entrenamiento y validación (semillas 101–110), red final sin Calle 18
- Entrenamiento: 320 episodios, 1.9 h, 47 teleports en total (antes cientos), 0 desatascos (no hay Calle 18).
  2.ª mitad, mediana de detenidos vs plan real: bajo 7.2 vs 7.9, medio 17.0 vs 17.6, alto 31.8 vs 53.5, jueves 26.0 vs 28.0.
- Validación, espera total promedio (s), 10 semillas pareadas, Wilcoxon:
  | Escenario | Real | QL v8 | Diferencia | p | QL mejor en |
  |---|---|---|---|---|---|
  | bajo | 15.50 | 13.63 | −12.1 % | 0.002 | 10/10 |
  | valle (nunca visto) | 17.63 | 15.85 | −10.1 % | 0.002 | 10/10 |
  | medio | 19.65 | 17.29 | −12.0 % | 0.002 | 10/10 |
  | **alto** | 52.91 | 31.35 | **−40.8 %** | 0.002 | 10/10 |
  | **jueves** | 22.83 | 21.38 | **−6.3 %** | 0.014 | 9/10 |
  Alto: tiempo de viaje −26.0 %, throughput +2.3 %, cola sur 16.8 vs 26.1 (todo p = 0.002). **Primera validación en la que
  el agente gana en los 5 escenarios, incluidos los dos picos.** Sin bloqueos: 0 vehículos sin terminar; teleports 0–3.
  Ciclos del agente 61–121 s (cumple el Manual); verde Dg 15 ~15 s en tráfico normal, ciclos 70–99 s.
- Nota: las esperas son menores que en v2–v7 porque ya no está el rojo de la Calle 18 (no comparables entre redes).
- Cautela: es la 7.ª iteración evaluada con las mismas semillas de validación (101–110). El resultado de la tesis es la
  EVALUACIÓN FINAL (semillas 1–30, nunca usadas), que se corre UNA vez con aforo_v8 sin más cambios.

## 2026-10-29 — EVALUACIÓN FINAL (resultado de la tesis, parte simulada)
- Modelo `aforo_v8` sin cambios después de su validación; semillas de evaluación 1–30 (nunca usadas antes); 5 escenarios
  × 30 semillas × 2 controladores = 300 corridas; red final (sin Calle 18), desatasco inactivo; teleport normal (300 s).
  Cómputo medido: 3.22 h. Archivos: `results/comparacion/evaluacion_final/` (corridas.csv, resultados.csv/.md, gráficos,
  avisos de SUMO por corrida).
- Métrica principal: tiempo de espera promedio por vehículo (s). Wilcoxon de rangos con signo, pareado por semilla
  (n = 30); r biserial de rangos; Holm para las métricas secundarias.
  | Escenario | Real (mediana) | QL v8 (mediana) | Diferencia | p | r | QL mejor en |
  |---|---|---|---|---|---|---|
  | bajo | 15.59 | 13.49 | −13.4 % | 1.9e−9 | −1.00 | 30/30 |
  | valle (nunca visto en entrenamiento) | 17.76 | 16.01 | −9.8 % | 1.9e−9 | −1.00 | 30/30 |
  | medio | 19.30 | 17.18 | −11.0 % | 1.9e−9 | −1.00 | 30/30 |
  | **alto (pico)** | 55.85 | 31.76 | **−43.1 %** | 1.9e−9 | −1.00 | 30/30 |
  | **jueves (pico simultáneo)** | 23.58 | 22.32 | **−5.3 %** | 1.1e−4 | −0.76 | 26/30 |
  Alto, secundarias (Holm, todas significativas): tiempo de viaje −28.4 %, tiempo perdido −44.8 %, velocidad +12.8 %,
  throughput +2.0 %, detenidos −20.7 %. Throughput igual o mayor en todos los escenarios (no se gana espera dejando
  vehículos fuera).
- Calidad de las corridas: 0 vehículos sin terminar en las 300; teleports 1–7 por escenario (30 corridas) en ambos
  controladores. Ciclos del agente 61–121 s (Manual: 60–120 s; > 120 s en 0–6 % de los ciclos, solo en pico).
  Estrategia aprendida: en tráfico normal ciclos más cortos (70–77 s; verde Cra 23 ~29–36 s, Dg 15 ~15 s); en alto,
  verde Cra 23 ~57 s y Dg 15 ~15 s (ciclo 98 s); en jueves, Dg 15 ~17 s.
- Cifras de media: bajo −12.4 %, valle −9.6 %, medio −10.9 %, alto −37.8 %, jueves −5.4 %.
- Contexto obligatorio al reportarlo: 7 iteraciones de diseño validadas con las semillas 101–110 (documentadas arriba);
  esta evaluación se corrió una sola vez. Limitaciones: simulación (no campo); sin Calle 18; aforo alto no simultáneo
  (alto–sur simulado 1361 vs 1512 veh/h); todo-rojo de 0 s tras la Cra 23 igual al real; filtrado de motos como supuesto;
  frenadas de emergencia ocasionales en la cremallera.

### 2026-10-29 — Figuras y estadística de la tesis
- Nuevo `scripts/graficas_tesis.py` (solo lee resultados guardados; reproducible) → `docs/figuras/`: fig01 calibración
  (simulado vs aforo, GEH), fig02 espera pareada por semilla, fig03 cambio % por semilla con IC 95 % bootstrap, fig04 mapa
  de todas las métricas (Holm), fig05 verdes y ciclo, fig06 colas por brazo, fig07 evolución por iteración (historia del
  desarrollo, redes distintas), fig08 política aprendida (Q-table), y `estadistica_evaluacion_final.md` (descriptiva,
  Wilcoxon, r, IC bootstrap, Shapiro-Wilk, t pareada, dz, prueba de signos, calidad de corridas).
- Sensibilidad: las conclusiones no cambian con la t pareada ni con la prueba de signos (todas p ≤ 0.0012). Diferencias no
  normales en alto y jueves (Shapiro p = 0.029 y 0.001) → se mantiene Wilcoxon como prueba principal.
- Dos formas de reportar el cambio: entre medianas (bajo −13.4, valle −9.8, medio −11.0, alto −43.1, jueves −5.3 %) y
  mediana del cambio por semilla con IC 95 % (−12.3 [−14.0, −10.5]; −9.5 [−10.6, −8.9]; −11.3 [−12.6, −10.0];
  −37.0 [−38.5, −34.9]; −3.5 [−5.1, −1.9] %).
- Figuras 10–11 (dinámica en el tiempo) requieren correr la semilla 1 de bajo y alto con ambos controladores (ver el script).
