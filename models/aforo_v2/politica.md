# Politica aprendida — modelo aforo_v2

- Episodios de entrenamiento: 240
- Modo de estado: detenidos. Cortes de detenidos: [1, 4, 9]
- Celda: accion preferida (M mantener / C cambiar) y veces que el agente vivio esa situacion; '.' = nunca la vivio (usa el plan fijo).

## Verde en cra23, lleva menos de 20 s

Filas: cra23 (en verde, detenidos). Columnas: dg15 (en rojo, detenidos).

| cra23 \ dg15 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | M (136) | M (1793) | M (2175) | M (511) |
| baja | M (5) | M (381) | M (1620) | M (595) |
| media | . | M (84) | M (981) | M (381) |
| alta | . | M (23) | M (445) | M (173) |

## Verde en cra23, lleva 20-40 s

Filas: cra23 (en verde, detenidos). Columnas: dg15 (en rojo, detenidos).

| cra23 \ dg15 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | M (123) | M (4016) | M (9446) | M (7293) |
| baja | M (5) | M (278) | M (2152) | M (2660) |
| media | . | M (12) | M (322) | M (448) |
| alta | . | C (1) | M (102) | M (173) |

## Verde en cra23, lleva 40 s o mas

Filas: cra23 (en verde, detenidos). Columnas: dg15 (en rojo, detenidos).

| cra23 \ dg15 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | M (5) | M (1137) | M (4828) | M (8696) |
| baja | . | M (34) | M (332) | M (2175) |
| media | . | M (1) | C (16) | M (285) |
| alta | . | . | C (3) | C (114) |

## Verde en dg15, lleva menos de 20 s

Filas: dg15 (en verde, detenidos). Columnas: cra23 (en rojo, detenidos).

| dg15 \ cra23 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | C (273) | M (1058) | C (2533) | M (5312) |
| baja | . | M (8) | C (35) | M (170) |
| media | . | . | M (2) | M (28) |
| alta | . | . | . | M (4) |

## Verde en dg15, lleva 20-40 s

Filas: dg15 (en verde, detenidos). Columnas: cra23 (en rojo, detenidos).

| dg15 \ cra23 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | M (520) | C (549) | C (1107) | C (8075) |
| baja | . | . | C (2) | M (96) |
| media | . | . | . | M (42) |
| alta | . | . | . | C (12) |

## Verde en dg15, lleva 40 s o mas

Filas: dg15 (en verde, detenidos). Columnas: cra23 (en rojo, detenidos).

| dg15 \ cra23 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | M (243) | C (66) | C (35) | M (1855) |
| baja | . | . | M (1) | M (38) |
| media | . | . | . | C (20) |
| alta | . | . | . | M (5) |

