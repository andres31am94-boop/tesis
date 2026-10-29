# Politica aprendida — modelo aforo_v6

- Episodios de entrenamiento: 320
- Modo de estado: presentes_en_verde. Cortes de detenidos: [1, 4, 9]; cortes de presentes (eje en verde): [1, 3, 14]
- Celda: accion preferida (M mantener / C cambiar) y veces que el agente vivio esa situacion; '.' = nunca la vivio (usa el plan fijo).

## Verde en cra23, lleva menos de 45 s

Filas: cra23 (en verde, presentes). Columnas: dg15 (en rojo, detenidos).

| cra23 \ dg15 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | M (37) | C (487) | C (327) | M (29) |
| baja | M (221) | M (2963) | C (2416) | C (529) |
| media | M (307) | M (5255) | M (9312) | M (14795) |
| alta | . | M (190) | M (7044) | M (17425) |

## Verde en cra23, lleva 45-55 s

Filas: cra23 (en verde, presentes). Columnas: dg15 (en rojo, detenidos).

| cra23 \ dg15 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | . | C (47) | C (96) | C (56) |
| baja | . | M (333) | C (669) | C (598) |
| media | C (2) | M (331) | M (961) | M (5635) |
| alta | . | . | M (138) | M (4603) |

## Verde en cra23, lleva 55 s o mas

Filas: cra23 (en verde, presentes). Columnas: dg15 (en rojo, detenidos).

| cra23 \ dg15 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | . | M (36) | C (67) | C (78) |
| baja | . | M (168) | C (395) | C (831) |
| media | . | C (126) | M (510) | M (5225) |
| alta | . | . | C (29) | M (4383) |

## Verde en dg15, lleva menos de 20 s

Filas: dg15 (en verde, presentes). Columnas: cra23 (en rojo, detenidos).

| dg15 \ cra23 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | C (348) | C (699) | C (696) | C (374) |
| baja | M (53) | C (1453) | C (1879) | C (2518) |
| media | M (7) | M (336) | C (890) | C (2459) |
| alta | . | C (80) | C (354) | M (712) |

## Verde en dg15, lleva 20-30 s

Filas: dg15 (en verde, presentes). Columnas: cra23 (en rojo, detenidos).

| dg15 \ cra23 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | M (154) | C (157) | C (181) | M (218) |
| baja | M (13) | M (326) | M (542) | M (1623) |
| media | . | M (84) | M (198) | M (1050) |
| alta | . | C (10) | M (76) | M (182) |

## Verde en dg15, lleva 30 s o mas

Filas: dg15 (en verde, presentes). Columnas: cra23 (en rojo, detenidos).

| dg15 \ cra23 | vacia | baja | media | alta |
|---|---|---|---|---|
| vacia | . | . | . | . |
| baja | . | . | . | . |
| media | . | . | . | . |
| alta | . | . | . | . |

