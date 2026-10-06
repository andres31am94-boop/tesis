# Propuesta de ajustes al anteproyecto

**Para:** reunión con la directora, Mónica Adriana Rubio Carrillo
**Autores:** Sebastián Stiven Chaves Montenegro · Joseph Andrés Mendoza Barbosa
**Fecha:** 2026-10-03
**Estado:** REVISADO — respuestas de la directora registradas (2026-10-04)

## Resumen del cambio

Se mantiene **todo lo esencial** del anteproyecto aprobado:
- simulación en SUMO + TraCI + Python;
- Aprendizaje por Refuerzo (Q-Learning o DQN);
- comparación contra tiempos fijos;
- enfoque cuantitativo, aplicado y experimental;
- hipótesis y variables.

Se **agrega** un componente: un **prototipo físico a escala** (maqueta de una intersección) que demuestra el sistema con datos reales. Una cámara observa vehículos a escala, YOLO los detecta, el agente entrenado en simulación decide y un ESP32 enciende semáforos de LEDs.

**Lo que no cambia:** la evaluación cuantitativa del desempeño sigue haciéndose en la simulación. La maqueta es una **demostración de funcionamiento**, no la fuente de las estadísticas de tráfico.

**Justificación para agregarla:** el propio anteproyecto cita a García-de-la-Cruz y Chancay-García (2024), que destacan a YOLO para detectar vehículos en tiempo real. También señala como vacío la falta de propuestas viables en un proyecto académico. El prototipo muestra que el agente entrenado en simulación puede operar con datos captados por una cámara, lo que acerca el trabajo a una implementación real sin intervenir vías públicas.

---

## Cambios sección por sección

### 1. Título
**Actual:** Simulador de semaforización inteligente basado en estrategias de Machine Learning para la optimización del flujo vehicular urbano

**Propuesto (opciones):**
- a) *Sistema de semaforización inteligente basado en estrategias de Machine Learning para la optimización del flujo vehicular urbano, evaluado en simulación y demostrado en un prototipo físico a escala*
- b) *Simulador y prototipo a escala de semaforización inteligente basado en aprendizaje por refuerzo para la optimización del flujo vehicular urbano*

### 2. Resumen
**Agregar después de** "…un algoritmo de control programado en Python.":

> Adicionalmente, se construye un prototipo físico a escala de una intersección en el que una cámara captura el movimiento de vehículos en miniatura. Los vehículos se detectan mediante el algoritmo de visión por computador YOLO y, a partir de esas detecciones, se calculan variables de tráfico que el agente entrenado en simulación utiliza para decidir el estado de semáforos físicos controlados por un microcontrolador ESP32. Este prototipo permite demostrar el funcionamiento del sistema con datos captados del mundo físico.

### 3. Abstract
**Agregar en el mismo lugar:**

> In addition, a small-scale physical prototype of an intersection is built, in which a camera captures miniature vehicles in motion. Vehicles are detected with the YOLO computer vision algorithm, and the resulting traffic variables are used by the agent trained in simulation to decide the state of physical traffic lights driven by an ESP32 microcontroller. This prototype demonstrates the system's operation with data captured from the physical world.

**Palabras clave — agregar:** visión por computador, YOLO, prototipo a escala.

### 4. Introducción
**Agregar al final del tercer párrafo:**

> Además del entorno simulado, el proyecto incluye una maqueta a escala que permite observar el sistema funcionando con información captada por una cámara, como paso intermedio entre la simulación y una eventual aplicación real.

### 5. Justificación
**Agregar antes de la última oración:**

> La inclusión de un prototipo físico a escala, que integra visión por computador y un microcontrolador, permite verificar que el modelo de decisión entrenado en simulación puede alimentarse con datos reales de un sensor de bajo costo, fortaleciendo la viabilidad técnica de la propuesta.

### 6. Objetivo general
**Propuesto:**

> Desarrollar un sistema de semaforización inteligente basado en estrategias de Machine Learning que permita optimizar los tiempos de los ciclos semafóricos, evaluado mediante simulación y demostrado en un prototipo físico a escala, con el fin de reducir la congestión vehicular en intersecciones urbanas de alto flujo.

### 7. Objetivos específicos
Se mantienen los cuatro actuales y se **agrega uno (quinto)**:

> 5. Implementar un prototipo físico a escala de una intersección que, mediante visión por computador (YOLO) y un microcontrolador ESP32, permita demostrar la toma de decisiones del sistema inteligente a partir de datos captados por una cámara.

### 8. Marco teórico — subsecciones nuevas (texto base)

**Visión por computador y detección de objetos con YOLO.**
> La visión por computador permite a un sistema extraer información de imágenes. YOLO (*You Only Look Once*) es una familia de detectores de objetos que, en una sola pasada de la red sobre la imagen, predice la ubicación y la clase de los objetos presentes, lo que la hace adecuada para aplicaciones en tiempo real (Redmon et al., 2016). Los modelos preentrenados en el conjunto de datos COCO incluyen clases de vehículos como automóvil, motocicleta, bus y camión (Lin et al., 2014). En este proyecto, YOLO se utiliza exclusivamente como mecanismo de percepción del prototipo físico.

**Seguimiento de múltiples objetos (tracking).**
> Los algoritmos de seguimiento asignan un identificador estable a cada objeto detectado a lo largo de los fotogramas, evitando contar varias veces el mismo vehículo y permitiendo estimar si está detenido o en movimiento. ByteTrack (Zhang et al., 2022) es uno de los métodos disponibles para este fin.

**Sistemas embebidos para actuación: ESP32.**
> El ESP32 es un microcontrolador de bajo costo con conectividad Wi-Fi y Bluetooth (Espressif Systems, s.f.). En el prototipo actúa únicamente como controlador de los semáforos físicos: recibe la decisión desde el computador y gestiona las transiciones de luces, con un modo seguro ante pérdida de comunicación.

### 9. Referencias nuevas
- Redmon, J., Divvala, S., Girshick, R. y Farhadi, A. (2016). You Only Look Once: Unified, real-time object detection. *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 779–788. https://doi.org/10.1109/CVPR.2016.91
- Lin, T.-Y., Maire, M., Belongie, S., Hays, J., Perona, P., Ramanan, D., Dollár, P. y Zitnick, C. L. (2014). Microsoft COCO: Common objects in context. *European Conference on Computer Vision (ECCV)*. https://arxiv.org/abs/1405.0312
- Zhang, Y., Sun, P., Jiang, Y., Yu, D., Weng, F., Yuan, Z., Luo, P., Liu, W. y Wang, X. (2022). ByteTrack: Multi-object tracking by associating every detection box. *European Conference on Computer Vision (ECCV)*. https://arxiv.org/abs/2110.06864
- Watkins, C. J. C. H. y Dayan, P. (1992). Q-learning. *Machine Learning*, 8, 279–292. https://doi.org/10.1007/BF00992698
- Jocher, G., Qiu, J. y Chaurasia, A. (2023). *Ultralytics YOLO* [Software]. https://github.com/ultralytics/ultralytics
- Espressif Systems. (s.f.). *ESP32 Series Datasheet*. https://www.espressif.com/en/support/documents/technical-documents

> Antes de entregar, verificar en la fuente original cada referencia (autores, año, páginas) y adaptarla al formato APA exigido por la universidad.

### 10. Marco legal
**Agregar al párrafo de la Ley 1581 de 2012:**

> En el prototipo físico la cámara captura únicamente una maqueta con vehículos a escala, por lo que no se recolectan datos personales. La Ley 1581 se mantiene como referente para cualquier aplicación futura con cámaras en vías reales.

### 11. Aspectos metodológicos

**Fuentes primarias — agregar:**
> Datos obtenidos por la cámara del prototipo a escala, procesados mediante YOLO y algoritmos de seguimiento, utilizados para verificar el funcionamiento del sistema con información del mundo físico.

**Muestra — agregar:**
> Adicionalmente, se emplea un prototipo físico a escala de una intersección de cuatro vías como entorno de demostración. Las mediciones de desempeño del tráfico (tiempo de espera y longitud de cola) se obtienen del entorno simulado. En el prototipo se evalúan indicadores de funcionamiento: precisión de detección, error de conteo y latencia entre la captura de imagen y el cambio del semáforo.

**Hipótesis y variables:** sin cambios. Se aclara que se contrastan con los datos de la simulación.

### 12. Glosario — términos nuevos
- **Visión por computador:** área de la inteligencia artificial que permite extraer información de imágenes o video.
- **YOLO (You Only Look Once):** familia de algoritmos de detección de objetos en tiempo real.
- **Tracking (seguimiento):** técnica que asigna un identificador estable a cada objeto detectado a lo largo del video.
- **ESP32:** microcontrolador de bajo costo usado para controlar los semáforos físicos del prototipo.
- **Prototipo a escala (maqueta):** representación física reducida de una intersección, usada para demostrar el funcionamiento del sistema.
- **Capa de seguridad:** conjunto de reglas fijas (verde mínimo y máximo, amarillo, todo-rojo) que limitan las decisiones del agente.

---

## Preguntas para la directora
1. ¿Se aprueba agregar el prototipo físico como quinto objetivo específico?
si y poner otro objetivo que falta son minimo 6
2. ¿Cuál de los títulos propuestos prefiere, o se mantiene el actual?
mantener el actual
3. ¿Se requiere un trámite formal de modificación del anteproyecto ante la universidad?
no requiere tramite, se puede modificar teniendo encuenta lo aprobado por la universidad
4. ¿Se mantiene la hipótesis de "al menos 20 %" o se prefiere formularla como diferencia estadísticamente significativa?
se puede modificar

---

## Resoluciones (2026-10-04)

| # | Pregunta | Respuesta | Acción |
|---|---|---|---|
| 1 | ¿Agregar el prototipo como objetivo? | Sí, y se requieren **mínimo 6 objetivos específicos** | Ver objetivos propuestos abajo |
| 2 | Título | **Se mantiene el título actual** | Se descartan las opciones a) y b) de la sección 1 |
| 3 | ¿Trámite formal? | No; se modifica respetando lo aprobado | Ajustar directamente el documento |
| 4 | Hipótesis del 20 % | Se puede modificar | Ver hipótesis propuestas abajo |

### Objetivos específicos propuestos (6)

1. Analizar las limitaciones técnicas y operativas de los sistemas de semaforización convencionales en Colombia, identificando los factores que generan congestión vehicular en intersecciones urbanas. *(sin cambios)*
2. Seleccionar las técnicas de Machine Learning más adecuadas para el control dinámico de semáforos, evaluando su viabilidad de aplicación dentro de un entorno de simulación de tráfico. *(sin cambios)*
3. Diseñar y construir un simulador de tráfico urbano que represente el comportamiento vehicular en intersecciones, integrando un módulo de toma de decisiones basado en el algoritmo de Machine Learning seleccionado. *(sin cambios)*
4. **(Nuevo)** Diseñar e implementar un mecanismo de control con restricciones de seguridad operativa (tiempos mínimos y máximos de verde, amarillo y todo-rojo) que limite las decisiones del agente inteligente y garantice transiciones seguras entre fases.
5. **(Nuevo)** Implementar un prototipo físico a escala de una intersección que, mediante visión por computador (YOLO) y un microcontrolador ESP32, permita demostrar la toma de decisiones del sistema inteligente a partir de datos captados por una cámara.
6. Evaluar el desempeño del simulador comparando los resultados obtenidos con el sistema inteligente frente a un esquema de semaforización de tiempos fijos, midiendo su impacto en la reducción de tiempos de espera y congestión vehicular. *(sin cambios; pasa al final porque evalúa lo construido en 3–5)*

**Justificación del objetivo 4:** la capa de seguridad es un componente propio que el proyecto debe diseñar, implementar y probar. Responde a la pregunta que un jurado hará con seguridad: *"¿qué impide que el algoritmo tome una decisión peligrosa?"*.

**Alternativa al objetivo 4**, si la directora prefiere otro enfoque: *"Desarrollar un módulo de adquisición de variables de tráfico (conteo, vehículos detenidos, ocupación y cola relativa) a partir de las detecciones de visión por computador, equivalentes a las obtenidas en el entorno simulado."*

### Hipótesis propuestas

**Hipótesis alternativa (H1):**
> La implementación de un sistema de semaforización inteligente basado en aprendizaje por refuerzo reduce de forma estadísticamente significativa (nivel de significancia α = 0,05) el tiempo promedio de espera vehicular en una intersección urbana simulada, en comparación con un sistema de semaforización de tiempos fijos bajo las mismas condiciones de tráfico.

**Hipótesis nula (H0):**
> La implementación de un sistema de semaforización inteligente basado en aprendizaje por refuerzo no genera diferencias estadísticamente significativas en el tiempo promedio de espera vehicular en una intersección urbana simulada, en comparación con un sistema de semaforización de tiempos fijos bajo las mismas condiciones de tráfico.

**Cambio de redacción en el Resumen y el Abstract:** reemplazar "Se espera que el sistema logre reducir en al menos un 20 %…" por "Se espera que el sistema reduzca de forma estadísticamente significativa los tiempos de espera vehicular frente al esquema tradicional…" (y su equivalente en inglés: "The intelligent system is expected to significantly reduce vehicle waiting times compared to the traditional scheme…").

**Por qué es mejor:** el 20 % era una cifra fijada antes de medir. Con la nueva redacción, la hipótesis se contrasta con una prueba estadística, y el porcentaje real de mejora se reporta como resultado, sea cual sea.


---

## Corrección del marco geográfico (2026-10-04)

**Motivo:** la intersección de referencia elegida por los autores está en **Acacías (Meta)**, no en Villavicencio. El anteproyecto actual sitúa todo el marco geográfico en Villavicencio.

**Intersección de referencia:** Carrera 23 con Diagonal 15, Acacías, Meta (coordenadas aproximadas 3.990091, -73.765749). Mapa en `docs/fases/img/interseccion_mapa.png`.

### Opción 1 (recomendada): contexto regional + caso de estudio en Acacías
Se mantiene el párrafo sobre Villavicencio como contexto regional (capital del Meta) y se agrega:

> El escenario de simulación y el prototipo físico toman como referencia una intersección real del municipio de Acacías, Meta: el cruce de la Carrera 23 con la Diagonal 15. Acacías, al igual que Villavicencio, pertenece a la región de los Llanos Orientales y presenta un crecimiento urbano y vehicular que hace pertinente evaluar alternativas de semaforización. La elección de esta intersección responde a criterios de viabilidad técnica: se trata de un cruce de cuatro brazos, accesible para los investigadores y susceptible de ser modelado en el simulador y reproducido en una maqueta a escala.

**Muestra — reemplazar** "una intersección vial simulada dentro del entorno SUMO, diseñada para representar condiciones reales de tráfico urbano" **por:**
> La muestra corresponde a la intersección de la Carrera 23 con la Diagonal 15 del municipio de Acacías, Meta, modelada en el entorno SUMO a partir de datos de OpenStreetMap verificados por los investigadores, e incluye variaciones en el flujo vehicular.

### Opción 2: trasladar todo el marco geográfico a Acacías
Reescribir la sección completa centrada en Acacías. Es más coherente, pero exige buscar y citar fuentes sobre movilidad en Acacías (parque automotor, crecimiento), que pueden ser más escasas que las de Villavicencio.

**Decisión de los autores (2026-10-05): Opción 2** — Acacías como único marco geográfico. Ver el borrador abajo.

> Antes de redactar datos de Acacías (población, parque automotor, distancia a Villavicencio), buscar fuentes oficiales (DANE, Alcaldía de Acacías, Secretaría de Movilidad). No incluir cifras sin fuente.


### Borrador del nuevo Marco Geográfico (Opción 2)

> Los textos entre corchetes **[ ]** son datos que deben completarse con una fuente oficial **antes** de entregar. No se deben llenar con cifras sin fuente.

**Marco Geográfico**

> El presente proyecto se contextualiza en el municipio de Acacías, ubicado en el departamento del Meta, en la región de la Orinoquía colombiana [ubicación respecto a Villavicencio y altitud — fuente: Ficha Municipal de Acacías, Gobernación del Meta]. [Población total y de la cabecera urbana — fuente: DANE, Censo Nacional de Población y Vivienda 2018 o proyecciones de población vigentes].
>
> En los últimos años el municipio ha presentado un crecimiento urbano y vehicular [cifra o indicador que lo respalde — fuente: Plan de Desarrollo Municipal de Acacías, RUNT u organismo de tránsito municipal], que se refleja en la acumulación de vehículos en intersecciones del casco urbano reguladas por semáforos de tiempos fijos, que no se adaptan a las variaciones del flujo a lo largo del día.
>
> Como caso de estudio se seleccionó la intersección de la Carrera 23 con la Diagonal 15, un cruce semaforizado de cuatro brazos con un carril por sentido en cada vía. La elección responde a criterios de viabilidad técnica: es accesible para los investigadores, permite la observación directa de su funcionamiento actual y puede modelarse en el simulador SUMO y reproducirse en una maqueta a escala.
>
> Aunque el proyecto se desarrolla en un entorno de simulación y en un prototipo físico, los escenarios buscan aproximarse a las condiciones de esta intersección. Se tienen en cuenta su geometría, el número de carriles, los tiempos semafóricos observados y la variabilidad de la demanda. Así, los resultados pueden servir como referencia para intersecciones similares en el municipio y en otras ciudades intermedias de la región.

**Otras secciones que mencionan Villavicencio y deben ajustarse:**
| Sección | Texto actual | Cambio |
|---|---|---|
| Resumen | "…ciudades como Villavicencio…" | "…municipios como Acacías (Meta)…" |
| Abstract | "…cities like Villavicencio…" | "…municipalities such as Acacías (Meta)…" |
| Marco institucional | "…convenios con la Secretaría de Movilidad local, tránsito y transporte de Villavicencio y el Meta" | Reemplazar por el organismo de tránsito de Acacías [verificar el nombre oficial en acacias.gov.co] |
| Muestra | "una intersección vial simulada…" | Usar el texto de la Opción 1 (Carrera 23 con Diagonal 15) |
| Datos institucionales de la portada | "Extensión Villavicencio" | **No cambiar**: es la sede de la universidad, no el lugar de estudio |

**Fuentes candidatas para completar los corchetes:**
- Gobernación del Meta. *Ficha Municipal Acacías* (2020). https://devx.meta.gov.co/media/centrodocumentacion/2021/08/10/c._Ficha_Municipal_Acacias_2020.pdf
- DANE. Censo Nacional de Población y Vivienda 2018 / proyecciones de población. https://www.dane.gov.co
- Alcaldía de Acacías. https://acacias.gov.co/ (Plan de Desarrollo Municipal, organismo de tránsito)
