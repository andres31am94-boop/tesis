# FASE 0 — Planificación y arquitectura (v2)

**Proyecto:** Sistema de semaforización inteligente basado en Machine Learning
**Autores:** Sebastián Stiven Chaves Montenegro · Joseph Andrés Mendoza Barbosa
**Directora:** Mónica Adriana Rubio Carrillo
**Fecha:** 2026-10-03 · **Versión:** 2
**Estado del documento:** PROPUESTA — pendiente de confirmación

> Estados usados en el proyecto: PLANIFICADO → EN DESARROLLO → IMPLEMENTADO → PROBADO → VALIDADO.
> Hoy **todo** el sistema está **PLANIFICADO**. Ningún número de este documento es un resultado: son parámetros de diseño a validar o se marcan "debe medirse".

### Cambios respecto a la v1
| Tema | v1 | v2 | Motivo |
|---|---|---|---|
| Tipo de ML | Supervisado (Random Forest) que predice congestión; una regla decide el verde | **Aprendizaje por Refuerzo (Q-Learning)**: el agente decide la acción; una capa de seguridad la filtra | Decisión de los autores: seguir el anteproyecto aprobado y que el sistema decida por sí mismo |
| Alcance | Simulación + maqueta | Igual | Se agrega la maqueta como **demostración física** al anteproyecto |
| Fases 4–5 | Dataset + entrenamiento supervisado | Entorno de entrenamiento + entrenamiento del agente | Consecuencia del cambio de ML |

---

## 1. Visión general

| Bloque | Función | Naturaleza |
|---|---|---|
| SUMO + TraCI | Entorno donde el agente **aprende** y donde se hacen los experimentos de comparación | Simulación |
| Agente Q-Learning + capa de seguridad | **Decide** en cada momento qué hacer con el semáforo, dentro de límites seguros | Común a ambos |
| Cámara + YOLO + tracking | Medir el estado del tráfico real en la maqueta | Físico |
| ESP32 + LEDs | Ejecutar físicamente la decisión | Físico |

**Idea central:** el agente no sabe de dónde vienen los datos. Recibe siempre el mismo `TrafficState` y devuelve siempre una `Decision`. Cambian la **fuente** (SUMO o cámara) y el **actuador** (TraCI o ESP32). El mismo agente entrenado en SUMO se ejecuta en la maqueta.

---

## 2. Diseño del Machine Learning: Aprendizaje por Refuerzo

### ¿Qué es?
Un **agente** (el controlador del semáforo) aprende por prueba y error. En cada momento observa la situación (**estado**), elige una **acción** y recibe una **recompensa**: positiva si el tráfico mejoró y negativa si empeoró. Tras muchas simulaciones aprende qué acción conviene en cada situación. Nadie le escribe las reglas.

### Q-Learning con tabla (versión inicial)
El agente guarda una tabla **Q(estado, acción)**: "qué tan buena es esta acción en este estado a largo plazo". Después de cada paso la actualiza:

```
Q(s,a) ← Q(s,a) + α · [ r + γ · max Q(s',·) − Q(s,a) ]
```
- `α` (tasa de aprendizaje): cuánto corrige con cada experiencia.
- `γ` (factor de descuento): cuánto le importa el futuro frente al presente.
- `ε` (exploración ε-greedy): probabilidad de probar una acción al azar para descubrir cosas nuevas. Disminuye con el entrenamiento.

Fuente del algoritmo: Watkins & Dayan (1992); Sutton & Barto (2018), ya citado en el anteproyecto.

**¿Por qué tabla y no DQN primero?** Con un estado pequeño la tabla basta. Además es **interpretable**: se puede mostrar al jurado qué decide el agente en cada situación. DQN (red neuronal en lugar de tabla) queda como extensión **solo si** la tabla no alcanza. El anteproyecto dice "Q-Learning o DQN", así que ambas opciones están dentro de lo aprobado.

### Formulación inicial (parámetros a ajustar con experimentos)

**Estado** (discretizado, solo variables que **también puede medir la cámara**):
| Variable | Valores |
|---|---|
| Cola relativa N-S (detenidos / capacidad de la aproximación) | p. ej. 4 niveles |
| Cola relativa E-O | p. ej. 4 niveles |
| Fase actual | N-S verde / E-O verde |
| Tiempo en la fase actual | p. ej. 3 niveles |

Ejemplo: 4 × 4 × 2 × 3 = 96 estados, un tamaño pequeño para una tabla. El número de niveles y sus cortes **se decidirán con datos** y se documentarán.

**Acciones** (cada intervalo de decisión, p. ej. 5 s — parámetro):
- `0` = mantener la fase actual
- `1` = cambiar a la otra fase

**Recompensa** (propuesta inicial): reducción del tiempo de espera acumulado entre dos decisiones (`r = espera_antes − espera_después`). Se evaluarán alternativas (p. ej. negativo de la cola total) y se justificará la elegida. La literatura usa varias formulaciones (Wei et al., 2019).

**Capa de seguridad (SafetyGuard)** — tiene prioridad sobre el agente:
- antes del **verde mínimo** → se ignora "cambiar";
- al llegar al **verde máximo** → se fuerza el cambio;
- todo cambio pasa por **amarillo + todo-rojo** fijos;
- nunca hay dos verdes en conflicto (solo 2 fases, en secuencia fija);
- si el agente falla o el estado es inválido → se pasa al plan de **tiempos fijos** (degradación segura).

Los valores de verde mínimo/máximo, amarillo y todo-rojo se fijarán en la Fase 3 consultando el Manual de Señalización Vial (Resolución 1885 de 2015). **Debe verificarse en la norma.**

### Entrenamiento y evaluación (reglas para que sea defendible)
- Se entrena con escenarios **bajo, medio y alto mezclados**, para que el agente no se especialice en uno solo.
- **Semillas de entrenamiento y de evaluación separadas.** El agente nunca se evalúa con las mismas simulaciones con que aprendió (equivale a no evaluar con el examen que ya estudió).
- En la evaluación, `ε = 0`: el agente solo usa lo aprendido, sin acciones al azar.
- Se registran curvas de aprendizaje (recompensa por episodio) para mostrar si convergió.
- Hiperparámetros (`α`, `γ`, `ε`, intervalo de decisión, niveles del estado) en archivos de configuración, con semilla fija.

### Implementación propia vs. librería
Existe la librería abierta `sumo-rl`, que conecta SUMO con algoritmos de RL. **Recomendación:** escribir nuestro propio entorno pequeño (una clase con `reset()` y `step()`). Es poco código, lo entiendes por completo (no es caja negra) y lo controlamos para la maqueta. `sumo-rl` puede servir como referencia de lectura.

---

## 3. Problemas técnicos detectados

### P1 — El anteproyecto debe ajustarse por la parte física
El anteproyecto aprobado es "solo simulador". La maqueta, YOLO y el ESP32 deben agregarse formalmente (título, objetivos, marco teórico, metodología). **El tipo de ML no cambia.** Ver `docs/anteproyecto/ajustes_anteproyecto.md`.

### P2 — El agente puede no aprender bien (convergencia)
Q-Learning puede tardar o quedarse en estrategias pobres si el estado o la recompensa están mal diseñados.
**Mitigación:** empezar con estado pequeño, revisar las curvas de aprendizaje, ajustar con experimentos documentados. El paso a DQN se considera solo con evidencia de que la tabla no alcanza.

### P3 — Transferencia simulación → maqueta
En SUMO una calle tiene decenas de vehículos; en la maqueta, unos pocos. Por eso el estado usa **cola relativa** (proporción de la capacidad), no conteos absolutos. Los intervalos de tiempo se escalan en la maqueta y se documenta.
**Declaración honesta para la tesis:** el desempeño de tráfico se evalúa en SUMO; en la maqueta se evalúa el **funcionamiento del sistema** (detección, tracking, latencia, que la decisión cambie cuando cambia el tráfico).

### P4 — YOLO preentrenado con carros de juguete
Los modelos preentrenados de Ultralytics usan COCO, que **sí** incluye `car`, `motorcycle`, `bus` y `truck` (hecho documentado; Lin et al., 2014). Pero aprendieron con vehículos reales: con carros a escala vistos desde arriba, el desempeño **debe medirse**. Si no basta, haremos *fine-tuning* con imágenes de nuestra maqueta.

### P5 — Movimiento de los vehículos
La mano tapa los carros. Recomendación: moverlos con una varilla delgada desde el borde. No agregar robots.

### P6 — Tiempo simulado vs. tiempo real
El controlador recibe el tiempo actual como dato (`now`) y nunca lee el reloj del sistema por su cuenta. Así funciona igual en SUMO (tiempo por pasos) y en la maqueta (tiempo real).

### P7 — Baseline débil
Comparar solo contra tiempos fijos deja abierta la pregunta: *"¿una regla simple no lograría lo mismo?"*. Se compararán:
1. **Tiempos fijos** (baseline, variable independiente del anteproyecto).
2. **Adaptativo por reglas** (sin ML).
3. **Agente Q-Learning.**
4. (Referencia opcional) Controlador `actuated` incorporado en SUMO.

### P8 — Hipótesis del 20 % (RESUELTO 2026-10-04: se reformula como diferencia estadísticamente significativa)
El anteproyecto aprobado plantea "al menos 20 %" con hipótesis nula. Se mantiene, pero el resultado se reportará **tal como salga**, con prueba estadística pareada. Si no se alcanza el 20 %, eso también es un resultado válido y se discutirá.

---

## 4. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | La directora no aprueba agregar la parte física | Baja | Alto | Presentar `ajustes_anteproyecto.md` en la semana 1 |
| R2 | El agente no converge o no supera a la regla simple | Media | Alto | Diseño incremental de estado/recompensa; reportar con honestidad |
| R3 | YOLO no detecta bien los carros de juguete | Media | Alto | Probar pronto (semana 12); fine-tuning |
| R4 | Alcance excesivo para el tiempo disponible | Alta | Alto | La simulación es el núcleo; la maqueta nunca bloquea la tesis |
| R5 | Problemas de instalación (SUMO_HOME, CUDA) | Media | Medio | Verificar el entorno antes de programar |
| R6 | Cambios de iluminación en la maqueta | Media | Medio | Lámpara fija, base mate |
| R7 | Pérdida de conexión PC ↔ ESP32 | Baja | Alto | Fail-safe en el ESP32 |
| R8 | Resultados no reproducibles (RL tiene azar) | Media | Alto | Semillas, configs YAML, varias corridas de entrenamiento |
| R9 | Sin GPU NVIDIA (confirmado: Intel UHD) → YOLO solo en CPU | Alta | Medio | Modelo YOLO más pequeño, resolución reducida; FPS **debe medirse**; evaluar exportación a OpenVINO o entrenamiento en Colab si hace falta |
| R10 | Poco espacio en disco (≈29,5 GB libres) y 8 GB de RAM | Media | Medio | PyTorch versión CPU (más liviana), datos pesados fuera de Git, cerrar programas durante pruebas |

---

## 5. Arquitectura

```
   SUMO ──TraCI──► SumoSource          Webcam ──► YOLO ──► Tracker ──► CameraSource
                       │                                                    │
                       └──────────────► TrafficState ◄──────────────────────┘
                                (cola relativa N-S/E-O, ocupación,
                                 fase actual, tiempo en fase, t)
                                              │
                                     StateEncoder (discretiza)
                                              │
                                     Agente Q-Learning ── tabla Q entrenada
                                     acción: mantener / cambiar
                                              │
                                     SafetyGuard (verde mín/máx, amarillo,
                                     todo-rojo, sin conflictos, respaldo fijo)
                                              │
                                          Decision
                        ┌─────────────────────┴─────────────────────┐
                  SumoActuator (TraCI)                     Esp32Actuator (USB Serial)
                        │                                           │
                 Semáforo virtual                        ESP32 → LEDs (+ fail-safe propio)

   En entrenamiento (solo SUMO): la recompensa vuelve al agente y actualiza la tabla Q.
   Logger: registra estados, acciones, recompensas y decisiones en ambos entornos.
```

| Módulo | Entra | Sale | Entorno |
|---|---|---|---|
| `SumoSource` | Simulación vía TraCI | `TrafficState` | Sim |
| `CameraSource` | Frames + tracks | `TrafficState` | Físico |
| `StateEncoder` | `TrafficState` | Estado discreto | Ambos |
| `QLearningAgent` | Estado discreto | Acción | Ambos |
| `RewardCalculator` | Métricas de SUMO | Recompensa | Solo entrenamiento |
| `SafetyGuard` | Acción + estado actual | Decisión segura | Ambos |
| `SumoActuator` / `Esp32Actuator` | Decisión | TraCI / serial | Sim / Físico |
| `Logger` | Todo | CSV | Ambos |

---

## 6. MVP

### MVP-1 — Simulación (núcleo de la tesis)
1. Intersección de 4 brazos en SUMO, 2 fases.
2. Escenarios bajo / medio / alto con semillas.
3. Baseline de tiempos fijos + métricas automáticas.
4. Entorno de RL propio (`reset`, `step`) sobre TraCI.
5. Agente Q-Learning entrenado con capa de seguridad.
6. Comparación: fijos vs. reglas vs. Q-Learning, con semillas de evaluación separadas.

### MVP-2 — Demostración física
1. Webcam cenital sobre la maqueta.
2. YOLO + tracking.
3. Zonas por aproximación → `TrafficState` (cola relativa).
4. **La misma tabla Q** entrenada en SUMO + SafetyGuard.
5. Python → USB Serial → ESP32 → LEDs.
6. Demo: se acumulan carros en N-S → el agente mantiene el verde de N-S.

---

## 7. Hardware

| Componente | Cant. | Para qué |
|---|---|---|
| ESP32 DevKit | 1 | Actuador de LEDs (no ejecuta YOLO ni el agente) |
| LEDs rojo/amarillo/verde 5 mm | 12 (4 semáforos) | Semáforos de la maqueta |
| Resistencias 220–330 Ω | 12 | Limitar corriente |
| Protoboard + cables dupont | 1 + kit | Montaje sin soldar |
| Cable USB **de datos** | 1 | Alimentación + comunicación |
| Webcam USB 720p/1080p | 1 | Observar la maqueta |
| Soporte cenital | 1 | Vista fija desde arriba |
| Lámpara LED fija | 1 | Iluminación constante (R6) |
| Carros a escala ~1:64 | 10–15 | Tráfico de la maqueta |
| Base MDF/cartón mate | 1 | Calles e intersección |

**Fuente externa:** no es necesaria en el MVP; el USB del PC alimenta el ESP32 y los LEDs.
**Comunicación:** USB Serial (más simple y confiable que Wi-Fi para el MVP).
**Fail-safe:** el ESP32 recibe solicitudes de fase y ejecuta él mismo amarillo y todo-rojo. Sin mensajes del PC durante X s → modo seguro (amarillo intermitente o ciclo fijo local).

---

## 8. Software

| Software | Para qué |
|---|---|
| Python (versión compatible con SUMO, Ultralytics y PyTorch, por verificar) + `venv` | Todo el sistema |
| SUMO (`netedit`, `sumo-gui`, `netconvert`) + `traci`/`sumolib` | Simulación |
| numpy, pandas, matplotlib, scipy | Agente con tabla, datos, gráficos, pruebas estadísticas |
| PyYAML | Configuración |
| ultralytics + PyTorch (+ CUDA si hay GPU NVIDIA) + opencv-python | YOLO, tracking, cámara |
| pyserial | Comunicación con el ESP32 |
| Arduino IDE 2 | Firmware del ESP32 |
| Git + GitHub | Versionado y documentación |
| (Solo si hace falta) CVAT o Label Studio | Etiquetar imágenes para fine-tuning |

Nota: scikit-learn ya no es indispensable. Q-Learning con tabla se implementa con numpy en pocas líneas. PyTorch ya se instala para YOLO y serviría para DQN si se llegara a necesitar.

---

## 9. Dónde entra cada tecnología

- **SUMO/TraCI:** el "mundo" donde el agente aprende y se evalúa. Entrega el estado, recibe las acciones y produce métricas (`tripinfo`, detectores).
- **Q-Learning (ML):** el que **decide** mantener o cambiar según el estado. Es la parte inteligente del sistema.
- **SafetyGuard:** convierte la decisión del agente en una acción segura. Tiene la última palabra.
- **YOLO:** solo percepción. Frame → cajas con clase. **No decide nada.**
- **Tracking (ByteTrack/BoT-SORT):** ID estable por vehículo → conteo sin duplicados, detenidos, velocidad aproximada.
- **ESP32:** solo actuación y seguridad local.

---

## 10. Métricas

### Tráfico (SUMO) — comparación de controladores
| Métrica | Fuente |
|---|---|
| Tiempo promedio de espera | `tripinfo` → `waitingTime` |
| Pérdida de tiempo | `tripinfo` → `timeLoss` |
| Tiempo promedio de viaje | `tripinfo` → `duration` |
| Cola promedio y máxima | Detectores E2 / TraCI |
| Vehículos detenidos | TraCI |
| Velocidad promedio | TraCI / tripinfo |
| Throughput | `tripinfo` |
| Duración de fases | Log del controlador |

Diseño: mismas semillas de evaluación para todos los controladores (pareado), calentamiento descartado, número de repeticiones según la varianza medida, prueba de Wilcoxon o t pareada.

### Agente
Curva de recompensa por episodio, estabilidad entre entrenamientos con distintas semillas, número de veces que la SafetyGuard tuvo que intervenir, política aprendida (tabla visualizada).

### Visión (maqueta)
Precisión/recall de detección, error de conteo frente a conteo manual, cambios de ID, FPS, latencia cámara→LED. **Todo debe medirse.**

---

## 11. Estructura del repositorio

```
tesis/
├── README.md · requirements.txt
├── config/            controller.yaml · agent.yaml · scenarios.yaml · vision.yaml
├── sumo/              network/ routes/ scenarios/ configs/
├── src/
│   ├── common/        TrafficState, Decision (contrato común)
│   ├── simulation/    SumoSource, SumoActuator, entorno RL
│   ├── vision/        cámara, YOLO, tracking, CameraSource
│   ├── traffic/       cálculo de variables
│   ├── agent/         StateEncoder, QLearningAgent, RewardCalculator, entrenamiento
│   ├── controller/    FixedTime, RuleBased, SafetyGuard
│   └── communication/ Esp32Actuator
├── firmware/esp32/
├── hardware/          diagramas, lista de materiales, fotos
├── data/ · models/ (tablas Q entrenadas + metadatos) · experiments/ · results/
├── notebooks/ · tests/
└── docs/
    ├── bitacora.md
    ├── decisiones/    una decisión técnica por archivo
    ├── fases/
    └── anteproyecto/
```
Cambio frente a la estructura sugerida: `src/ml/` pasa a llamarse `src/agent/`, porque con RL lo que hay es un agente, no un modelo de clasificación.

---

## 12. Hoja de ruta (actualizada 2026-10-04)

**Fecha de sustentación:** principios de febrero de 2027 → aprox. **17 semanas** desde el 5 de octubre de 2026.
**Supuesto (por confirmar):** el documento escrito debe estar listo hacia mediados de enero para revisión de la directora/jurados.
**Estrategia:** sistema completo (MVP-1 + MVP-2) **antes de las vacaciones de diciembre**; enero para experimentos finales, redacción y ensayo de la sustentación. Al ser dos autores, desde la semana 3 se trabaja en paralelo (simulación/agente y hardware/visión).

| Sem. | Fechas | Fase | Entregable verificable |
|---|---|---|---|
| 1 | 5–11 oct | 0 / 1 | Entorno instalado (SUMO, venv), repo GitHub `tesis`, **compra de hardware** |
| 2 | 12–18 oct | 1 | Intersección en `netedit` + 3 escenarios con semillas en `sumo-gui` |
| 3 | 19–25 oct | 2 / 3 | Python ↔ SUMO por TraCI; baseline de tiempos fijos con métricas automáticas |
| 4 | 26 oct–1 nov | 3 / 10 | Controlador por reglas + SafetyGuard · (paralelo) ESP32 enciende LEDs por serial |
| 5 | 2–8 nov | 4 / 5 | Entorno RL (`reset`, `step`) + primer entrenamiento Q-Learning |
| 6 | 9–15 nov | 5 / 10 | Ajuste de estado/recompensa, curvas de aprendizaje · (paralelo) fail-safe del ESP32 |
| 7 | 16–22 nov | 6 | Agente controlando SUMO; comparación preliminar fijos vs. reglas vs. Q-Learning |
| 8 | 23–29 nov | 7 | YOLO + tracking sobre carros a escala con la webcam; FPS medidos en esta PC |
| 9 | 30 nov–6 dic | 7 / 8 | Decisión sobre fine-tuning; zonas → CameraSource → TrafficState |
| 10 | 7–13 dic | 11 / 9 | Maqueta construida; cámara → agente → decisión en pantalla |
| 11 | 14–20 dic | 12 | **Sistema completo** cámara → agente → ESP32 → LEDs |
| 12 | 21–27 dic | — | Holgura (imprevistos / descanso) |
| 13 | 28 dic–3 ene | 13 | Experimentos finales en SUMO (todas las semillas y escenarios) |
| 14 | 4–10 ene | 13 | Análisis estadístico + pruebas funcionales de la maqueta |
| 15 | 11–17 ene | 14 | Redacción de metodología, resultados y conclusiones |
| 16 | 18–24 ene | 14 | Revisión con la directora y correcciones |
| 17 | 25–31 ene | — | Presentación, ensayo de la demo, **video de respaldo de la demo** |

**Regla de protección del cronograma:** si al final de la semana 11 la maqueta no funciona completa, se congela su alcance (por ejemplo, solo detección + decisión en pantalla + LEDs) y la prioridad pasa a los experimentos en SUMO, que sostienen la hipótesis.

La documentación (bitácora, GitHub, carpeta `tesis`) se actualiza **cada semana**.

---

## 13. Decisiones

| Decisión | Estado |
|---|---|
| ML = Aprendizaje por Refuerzo (Q-Learning con tabla; DQN solo si hace falta), según el anteproyecto | **Tomada** por los autores |
| Agregar la maqueta física como demostración | **Aprobada** por la directora (2026-10-04) |
| Título del anteproyecto | Se mantiene el actual |
| Objetivos específicos | Mínimo 6; se agregan capa de seguridad y prototipo físico |
| Hipótesis | Diferencia estadísticamente significativa (α = 0,05) en lugar de "al menos 20 %" |
| Fecha de sustentación | Principios de febrero de 2027 |
| Repositorio GitHub | `tesis`, **público** |

---

## 14. Referencias

- Chaves, S. y Mendoza, J. (2026). Anteproyecto (documento del proyecto).
- Watkins, C. J. C. H. y Dayan, P. (1992). Q-learning. *Machine Learning*, 8, 279–292. https://doi.org/10.1007/BF00992698
- Sutton, R. S. y Barto, A. G. (2018). *Reinforcement learning: An introduction* (2.ª ed.). MIT Press.
- Wei, H., Zheng, G., Gayah, V. y Li, Z. (2019). A survey on traffic signal control methods. https://arxiv.org/abs/1904.08117
- Lin, T.-Y. et al. (2014). Microsoft COCO: Common Objects in Context. ECCV. https://arxiv.org/abs/1405.0312
- Eclipse SUMO — Documentación oficial: https://sumo.dlr.de/docs/
- Ultralytics — Documentación oficial: https://docs.ultralytics.com/
- Ministerio de Transporte (2015). Resolución 1885 de 2015 (por consultar para tiempos de amarillo/todo-rojo).
