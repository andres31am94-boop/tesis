# Protocolo de experimentos en la maqueta (Fase 13) — PROPUESTA v1 (2026-11-05)

Estado: propuesta para revisar con los autores; se ajusta después de una prueba piloto. Ningún valor de este documento
es un resultado: los números de demanda son de DISEÑO y todo lo demás **debe medirse**.

## 1. Objetivo y alcance
- **Objetivo:** comprobar en un entorno físico que el sistema completo funciona (cámara → YOLO → zonas → agente
  aforo_v9 → ESP32 → LEDs) y comparar, con la MISMA demanda, el semáforo de **tiempos fijos** (55/20 s, el real) contra
  el **agente**.
- **Alcance honesto:** la evidencia principal de la tesis es la evaluación en SUMO (aforo_v8, 30 semillas). La maqueta
  es una **validación funcional** con indicadores comparativos; sus resultados se presentan con sus limitaciones
  (pocas repeticiones, carros movidos a mano, escala reducida).

## 2. Qué se compara
| Factor | Niveles |
|---|---|
| Controlador | `tiempos_fijos` (55 s Cra 23 / 20 s Dg 15, amarillo 3 s, todo rojo 20 s) vs `qlearning` (aforo_v9) |
| Demanda (guion de llegadas) | G1 baja balanceada · G2 media (proporciones del aforo) · G3 Dg 15 cargada (desbalance) |
Mismo SafetyGuard (verde mín./máx., amarillo, todo rojo) para ambos: la única diferencia es quién decide.

## 3. Demanda reproducible: guion de llegadas
Para que fijos y agente reciban **exactamente** la misma demanda, las llegadas no se improvisan: un programa
(pendiente: `scripts/guion_llegadas.py`) anuncia por pantalla y con sonido "carro en NORTE", "carro en ESTE", etc., en
instantes fijados por una semilla. Mismo guion + misma semilla = misma demanda.

Tasas de DISEÑO (carros por minuto, a ajustar en la piloto según lo que puedan manejar 2 personas):
| Guion | Norte | Sur | Este | Oeste | Total | Base |
|---|---|---|---|---|---|---|
| G1 baja | 1.5 | 1.5 | 0.75 | 0.5 | ~4.3 | proporciones de aforo_bajo |
| G2 media | 3 | 2.5 | 1.5 | 1 | 8 | proporciones de aforo_medio (Cra 23 ≈ 2× Dg 15) |
| G3 Dg 15 cargada | 0.5 | 0.5 | 3 | 2 | 6 | como `desb_dg15_cargada` |
Duración de cada corrida: **10 min** de guion + vaciado (hasta que no queden carros). Con ciclos de ~100 s son ~6 ciclos.

## 4. Reglas de conducción manual (iguales en todas las corridas)
Inspiradas en el flujo de saturación usual (~1 vehículo cada 2 s por carril):
1. **Llegada:** al oír el aviso, el operador pone un carro en el borde de la tabla del brazo indicado y lo lleva al final de
   la cola (o hasta la línea de pare si no hay cola), en el carril de llegada que tenga menos carros.
2. **Verde:** el primer carro de cada carril arranca; cada carro siguiente arranca **2 s después** del anterior
   (metrónomo del programa). Cruza en ~2 s y se retira al llegar al borde de la tabla del brazo de salida.
3. **Amarillo:** solo termina de cruzar el carro que ya pasó la línea de pare; nadie más arranca.
4. **Rojo / todo rojo:** nadie cruza.
5. Un operador por eje (Cra 23 y Dg 15); manos fuera de la imagen cuando no están moviendo un carro.
Los operadores saben qué controlador corre (no se puede ocultar); las reglas fijas y el guion limitan ese sesgo.

## 5. Diseño y orden de las corridas
- 3 guiones × 2 controladores × **3 repeticiones** = **18 corridas** (≈ 10–12 min cada una → ~4 h con montaje y pausas;
  se puede repartir en 2 sesiones).
- Cada repetición usa una **semilla distinta** del guion; la MISMA semilla se usa para fijos y agente (corridas pareadas).
- Orden **aleatorizado y balanceado** (en la mitad de los pares va primero fijos, en la otra mitad el agente) para
  controlar el cansancio y el aprendizaje de los operadores.
- Antes: 1 corrida **piloto** por guion (no se analiza) para ajustar tasas y reglas.

## 6. Qué se mide (todo lo registra `src/maqueta/lazo_camara.py` + el guion)
| Métrica | Cómo | Unidad |
|---|---|---|
| Espera promedio por carro | carro-segundos **detenidos** en las zonas / carros atendidos | s |
| Cola promedio y máxima por brazo | carros detenidos en cada zona, por segundo | carros |
| Carros atendidos (throughput) | carros que salen de la zona hacia el cruce (pendiente: conteo de salidas por id) | carros / 10 min |
| Duración de verdes por eje y ciclo | registro del SafetyGuard (`cambios.csv`) | s |
| Decisiones del agente y respaldos | `resumen.json` | n |
| Latencia de confirmación del ESP32 | `cambios.csv` | ms |
| Cuadros por segundo del sistema | `resumen.json` | cuadros/s |

**Validación de la medición (aparte, una vez):** en el video grabado de 2 corridas se cuentan A MANO los carros en cada
zona en 30 segundos elegidos al azar y se comparan con lo que contó el sistema (error medio por zona). Sin esto, las
métricas de la cámara no son defendibles.

## 7. Análisis
- Por guion: mediana de la espera de las 3 repeticiones para cada controlador y diferencia pareada por semilla.
- Con n = 3 pares por guion **no hay potencia estadística** para una prueba formal por guion: se reporta descriptivo
  (mediana, rango) y, como apoyo, Wilcoxon pareado sobre los 9 pares juntos (los 3 guiones), dejando claro el alcance.
- Gráficas: luz de cada eje en el tiempo + cola por brazo (una corrida de ejemplo por guion), y espera por controlador.

## 8. Control de condiciones
- Cámara fija (no tocar el soporte); revisar el encuadre al inicio de cada sesión con una foto de la tabla vacía.
- Misma iluminación (luz difusa, sin sol directo), mismos carros, mismas casas.
- Registrar en `docs/bitacora.md`: fecha, hora, operadores, guion, semilla, controlador y cualquier incidente.
- Si una corrida se interrumpe (falla de cámara, ESP32 en intermitente, carro caído) se repite completa y se anota.

## 9. Pendientes para poder ejecutarlo
1. `scripts/guion_llegadas.py` (avisos con sonido + metrónomo de 2 s + registro de llegadas).
2. Conteo de salidas por id en `ContadorZonas` (throughput) y cálculo de la espera en el resumen.
3. Zonas reales de la maqueta y validación de la detección (después del montaje).
4. Prueba piloto y ajuste de tasas.
