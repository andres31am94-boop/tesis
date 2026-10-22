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
