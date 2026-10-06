# Demanda (flujos de vehículos)

| Archivo | Contenido | Estado |
|---|---|---|
| `prueba_flujos.csv` | Vehículos/hora por brazo de llegada y movimiento | **DATOS DE PRUEBA INVENTADOS — NO usar para resultados** |
| `prueba_tipos.csv` | Proporción de cada tipo de vehículo | **DATOS DE PRUEBA INVENTADOS — NO usar para resultados** |

Cuando llegue el aforo se crean `aforo_*.csv` con el mismo formato y se regenera el `.rou.xml` con
`scripts/generar_demanda.py`. El resto del sistema no cambia.

Movimientos permitidos: `recto` y `derecha` (giro a la izquierda prohibido en los 4 brazos).
