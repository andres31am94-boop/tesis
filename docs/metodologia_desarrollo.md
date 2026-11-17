# Metodología de desarrollo

**Proyecto:** Simulador de semaforización inteligente basado en estrategias de Machine Learning para la optimización del flujo vehicular urbano (Cra 23 × Dg 15, Acacías).
**Autores:** Sebastián Chaves y Joseph Andrés Mendoza · **Directora:** Mónica Rubio

---

## 1. Definición

El sistema se desarrolla con un **modelo incremental con prototipado evolutivo** (Pressman y Maxim, 2020; Sommerville, 2016). El componente de datos y aprendizaje automático sigue además el ciclo **CRISP-DM** (Chapman et al., 2000; Wirth y Hipp, 2000).

- **Incremental:** el sistema se construye por fases. Cada fase entrega una parte que funciona y se integra con las anteriores.
- **Prototipado evolutivo:** el prototipo no se desecha. Se mejora en cada iteración a partir de lo que muestran las pruebas.
- **CRISP-DM:** organiza el trabajo con datos en seis etapas: comprensión del problema, comprensión de los datos, preparación, modelado, evaluación y despliegue.

Esta metodología de **desarrollo** es distinta de la metodología de **investigación** del anteproyecto (enfoque cuantitativo, tipo aplicada-experimental). La primera dice cómo se construye el sistema; la segunda, cómo se evalúa la hipótesis.

## 2. Por qué esta metodología

| Necesidad del proyecto | Cómo la atiende el modelo incremental-evolutivo |
|---|---|
| Tecnologías nuevas para los autores (SUMO, TraCI, aprendizaje por refuerzo, YOLO, ESP32) | Se aprende y se valida una tecnología por fase, sin integrar todo de golpe |
| Requisitos que cambian con lo que se encuentra en campo y en las pruebas | Cada iteración puede ajustar el diseño sin rehacer lo anterior |
| Hay que demostrar que cada parte funciona | Ninguna fase avanza sin una prueba concreta y su evidencia |
| Equipo de dos personas, sin roles fijos | No exige ceremonias ni roles formales |

**Alternativas consideradas**

- **Cascada:** supone requisitos estables desde el inicio. Aquí no lo eran: la calibración, la maqueta y el agente cambiaron con los resultados.
- **Scrum:** pide sprints, backlog y roles (dueño de producto, Scrum Master) que no existen en un equipo de dos autores. Del enfoque ágil se toman las iteraciones cortas y la retroalimentación continua, pero no se declara Scrum.
- **Espiral:** su análisis formal de riesgos por ciclo es más pesado de lo que pide un prototipo académico. Los riesgos se manejan dentro de cada fase.

**Limitaciones:** el modelo incremental depende de que las primeras fases (la red de SUMO y la calibración) estén bien hechas, porque todo lo demás se apoya en ellas. Por eso la calibración se validó con un criterio objetivo (GEH < 5) antes de entrenar al agente.

## 3. Ciclo de cada incremento

Cada fase repite el mismo ciclo:

1. **Planificar:** objetivo de la fase, qué se va a entregar y cómo se comprobará.
2. **Implementar:** código, configuración o construcción física.
3. **Probar:** una prueba concreta, ejecutada por los autores (script `.bat`, simulación, foto o video).
4. **Validar:** si la prueba cumple el criterio, la fase se da por terminada. Si no, se diagnostica y se corrige antes de seguir.
5. **Registrar:** entrada en `docs/bitacora.md`, commit en GitHub y, cuando hay cómputo, registro en `results/registro_computo.csv`.

**Criterio de "terminado":**
- la prueba se ejecutó y su resultado quedó guardado;
- el resultado es reproducible (configuración y semillas registradas);
- la bitácora explica qué se hizo y qué se decidió.

## 4. Incrementos del proyecto

| Fase | Incremento | Entregable | Criterio de validación |
|---|---|---|---|
| 0 | Planificación | Arquitectura, alcance, riesgos | Aprobación de los autores |
| 1 | Red en SUMO | Intersección modelada desde OpenStreetMap y verificada en campo | Geometría y movimientos iguales a los del sitio |
| 2 | Python ↔ TraCI | Lectura del estado y control del semáforo | El semáforo cambia por orden de Python |
| 3 | Sistema convencional | Plan de tiempos fijos medido (55 s / 20 s) | Reproduce el plan real |
| 4 | Demanda y datos | Escenarios desde aforos de campo | GEH < 5 en las 100 comparaciones |
| 5 | Agente de aprendizaje | Q-Learning tabular (aforo_v8, versión final) | Validación con semillas separadas |
| 6 | Control seguro | Capa de seguridad (verde mín./máx., amarillo, todo-rojo) | Ninguna decisión del agente la viola |
| 7 | Visión | YOLO ajustado con Hot Wheels + ByteTrack | Precisión de detección medida |
| 8 | Datos desde la cámara | Conteo por zonas y escalado maqueta → SUMO | Conteo contra conteo manual |
| 9 | Cámara → agente | Decisión desde video (aforo_v9, adaptación a la maqueta) | Decisiones coherentes con la cola observada |
| 10 | ESP32 | Semáforos LED obedientes a Python, con frenos de emergencia | Prueba de LEDs y del corte de comunicación |
| 11 | Maqueta | Tabla, base, semáforos y brazo de la cámara | Encuadre y zonas verificadas |
| 12 | Integración | Lazo en vivo: cámara → YOLO → agente → ESP32 | Funcionamiento continuo y latencia medida |
| 13 | Evaluación | Tiempos fijos vs. agente (simulación y maqueta) | Pruebas estadísticas del protocolo |
| 14 | Documentación | Documento de tesis | Revisión de la directora |

## 5. CRISP-DM en el componente de aprendizaje automático

| Etapa | Agente de semaforización (Q-Learning) | Detección de vehículos (YOLO) |
|---|---|---|
| Comprensión del problema | Esperas causadas por el plan fijo | Contar carros por brazo desde una cámara |
| Comprensión de los datos | Aforos de campo por acceso, tipo y movimiento | Videos de Hot Wheels sobre la maqueta |
| Preparación | Escenarios de demanda calibrados en SUMO | Etiquetado en Label Studio, división de entrenamiento y validación por video |
| Modelado | Diseño de estados, acciones y recompensa; entrenamiento | Ajuste fino de YOLO |
| Evaluación | Semillas de validación (101–110) y de evaluación final (1–30); Wilcoxon | Precisión y error de conteo |
| Despliegue | Controlador con capa de seguridad, en SUMO y en la maqueta | Lazo en vivo con el ESP32 |

## 6. Gestión de cambios

Los cambios se aceptan cuando una prueba muestra que hacen falta, y quedan registrados en la bitácora. Ejemplos reales del proyecto:

- **Agente:** el agente final de simulación es aforo_v8. Para la maqueta se entrenó aforo_v9 porque, con brazos vacíos, v8 recurría al control de respaldo.
- **Red de SUMO:** se excluyó el semáforo de la Calle 18 porque generaba bloqueos artificiales.
- **Soporte de la cámara:** pasó de prensas en C a un poste atornillado y luego a uno desmontable con pernos, para poder transportar la maqueta sin perder la posición de la cámara.
- **Base de la maqueta:** se adaptó a cómo quedó armada (travesaño centrado, base centrada y taco separador para el poste).

## 7. Herramientas que sostienen la metodología

- **Git y GitHub:** historial de cada incremento (un commit por avance).
- **Bitácora (`docs/bitacora.md`):** qué se hizo, qué falló y qué se decidió.
- **Registro de cómputo (`results/registro_computo.csv`):** tiempo de cada ejecución.
- **Configuraciones en archivos y semillas fijas:** cualquier resultado se puede repetir.
- **Pruebas automáticas (`tests/`):** verifican las piezas críticas, como el escalado maqueta → SUMO.
- **Lanzadores `.bat`:** cada prueba se ejecuta igual cada vez.

## 8. Roles

- **Autores:** deciden el alcance, toman los datos de campo, construyen la maqueta, ejecutan y validan las pruebas.
- **Directora:** valida académicamente cada entrega.
- **Asistente de IA (Claude, Anthropic):** apoyo técnico en diseño, código y documentación. Las decisiones y la validación de cada fase son de los autores, y los commits con su participación quedan identificados en el historial de GitHub.

## Referencias

Chapman, P., Clinton, J., Kerber, R., Khabaza, T., Reinartz, T., Shearer, C., & Wirth, R. (2000). *CRISP-DM 1.0: Step-by-step data mining guide*. SPSS Inc.

Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9th ed.). McGraw-Hill Education.

Sommerville, I. (2016). *Software engineering* (10th ed.). Pearson.

Wirth, R., & Hipp, J. (2000). CRISP-DM: Towards a standard process model for data mining. In *Proceedings of the 4th International Conference on the Practical Applications of Knowledge Discovery and Data Mining* (pp. 29–39).
