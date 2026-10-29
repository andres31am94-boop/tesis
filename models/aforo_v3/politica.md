# Politica aprendida — modelo aforo_v3

- Episodios de entrenamiento: 240
- Modo de estado: presentes_en_verde. Cortes de detenidos: [1, 4, 9]; cortes de presentes (eje en verde): [1, 3, 14]
- Celda: accion preferida (M mantener / C cambiar) y veces que el agente vivio esa situacion; '.' = nunca la vivio (usa el plan fijo).

## Verde en cra23, lleva menos de 20 s

Filas: cra23 (en verde, presentes). Columnas: dg15 (en rojo, detenidos).

| cra23 \ dg15 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | C (4) | M (71) | M (34) | . |
| baja | C (53) | M (473) | M (229) | M (6) |
| media | M (79) | M (1556) | M (1586) | M (311) |
| alta | M (2) | M (267) | M (3285) | M (1128) |

## Verde en cra23, lleva 20-40 s

Filas: cra23 (en verde, presentes). Columnas: dg15 (en rojo, detenidos).

| cra23 \ dg15 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | C (11) | M (247) | M (334) | M (12) |
| baja | M (43) | M (1670) | M (1923) | M (196) |
| media | M (69) | M (2336) | M (4829) | M (3519) |
| alta | . | M (107) | M (4580) | M (6110) |

## Verde en cra23, lleva 40 s o mas

Filas: cra23 (en verde, presentes). Columnas: dg15 (en rojo, detenidos).

| cra23 \ dg15 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | . | M (101) | M (337) | C (78) |
| baja | C (1) | C (465) | M (2023) | C (742) |
| media | M (2) | M (483) | M (2192) | M (4264) |
| alta | . | C (1) | M (437) | M (5776) |

## Verde en dg15, lleva menos de 20 s

Filas: dg15 (en verde, presentes). Columnas: cra23 (en rojo, detenidos).

| dg15 \ cra23 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | M (248) | C (437) | C (695) | M (526) |
| baja | C (29) | C (832) | C (1447) | M (3151) |
| media | M (4) | C (116) | C (320) | M (1372) |
| alta | . | . | . | M (16) |

## Verde en dg15, lleva 20-40 s

Filas: dg15 (en verde, presentes). Columnas: cra23 (en rojo, detenidos).

| dg15 \ cra23 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | C (536) | M (201) | C (278) | M (1240) |
| baja | M (6) | M (308) | C (640) | M (6916) |
| media | . | M (43) | C (107) | M (2549) |
| alta | . | . | . | M (23) |

## Verde en dg15, lleva 40 s o mas

Filas: dg15 (en verde, presentes). Columnas: cra23 (en rojo, detenidos).

| dg15 \ cra23 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | M (248) | M (42) | C (6) | C (410) |
| baja | C (32) | M (29) | C (11) | C (2636) |
| media | C (2) | . | M (1) | M (1001) |
| alta | . | . | . | M (8) |

