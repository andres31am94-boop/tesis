# Guía de montaje de la maqueta (tabla 110 × 80 cm)

> **Versión vigente (como quedó armada, 2026-11):** `hardware/maqueta/montaje_madera.pdf` (base + brazo de la cámara,
> listón 4,5 × 4,5 cm, puente ARRIBA), `hardware/maqueta/puntos_semaforos.pdf` (huecos de los semáforos) y el modelo
> interactivo `hardware/maqueta/maqueta_3d.html` (abrir en el navegador; etapas 1–5 del montaje).
> `base_maqueta.pdf`, `soporte_camara.pdf`, `esquema_completo_maqueta.pdf` y `planos_maqueta_completos.pdf` quedan
> como versiones anteriores del diseño (con prensas / poste en dos piezas) y no se deben usar para construir.


Para trazar: **`hardware/maqueta/esquema_trazado_maqueta.pdf`** (todas las coordenadas). Plano general: **`hardware/maqueta/plano_tabla_maqueta_puente.pdf`** (versión vigente, con el puente; la versión sin puente `plano_tabla_maqueta.pdf` queda solo como referencia) (escala 1:10, medidas en mm). Origen de las medidas:
**esquina superior izquierda de la tabla**, con el lado de 110 cm horizontal (x hacia la derecha, y hacia abajo).

## 0. Antes de empezar: ¿qué cámara se usará EN VIVO?
El lazo en vivo (`src/maqueta/lazo_camara.py`) lee la cámara con OpenCV en el PC. Las medidas de la tabla salieron del
**iPhone grabando video** (a 1 m ve 102 × 68 cm). Hay dos caminos:
- **iPhone como cámara web** (aplicación tipo cámara virtual en Windows): se conserva el campo de visión medido, pero
  hay que comprobar que la aplicación entregue la imagen completa (sin recorte) y en horizontal.
- **Cámara web USB**: su campo de visión es distinto → **volver a medir** lo que ve a la altura del soporte y ajustar la
  altura para que cubra ~102 × 68 cm.
En ambos casos, el paso 8 (verificación con la cámara fija) lo confirma.

## 1. Materiales
- Pintura **mate** (vinilo o acrílica; RAL = referencia de color, sirve un equivalente):
  - calzada: **gris medio tipo asfalto, RAL 7042** (gris tráfico A). **No gris muy oscuro**: los Hot Wheels negros y
    azul oscuro perderían contraste y el modelo los detectaría peor;
  - aceras y resto de la tabla: **hueso/beige claro, RAL 1013** (parecido a las baldosas con que se entrenó el modelo);
  - líneas de carril y de pare: **blanco, RAL 9016**; línea central: **amarillo, RAL 1023**;
  - postes de los semáforos: **negro mate, RAL 9005**.
  Nada de barniz brillante (reflejos del bombillo). Las líneas también pueden ser cinta adhesiva mate de 5–8 mm.
- Cinta de enmascarar (para bordes rectos), metro, escuadra, regla larga, lápiz.
- Taladro y broca de **8 mm** (huecos para los cables de los semáforos).
- Silicona caliente o tornillos pequeños (fijar los semáforos).
- Cables Dupont macho-hembra **largos** o extensiones (~50 cm) para llegar del semáforo al ESP32 bajo la tabla.
- Base (bastidor): ver `hardware/maqueta/base_maqueta.pdf` (listón 45×70 mm de canto, 2 × 940 mm + 4 × 550 mm, 8 escuadras).
- Soporte de cámara: listón 4×4 cm (poste 70 + 70 cm, brazo 60 cm), escuadra metálica o abrazaderas,
  y un soporte/pinza para el celular o la cámara.
- Cinta doble faz o abrazaderas plásticas para fijar el ESP32 y la protoboard debajo de la tabla.

## 2. Trazar (con lápiz)
1. Revisar que la tabla esté a escuadra (110 × 80 cm).
2. **Cra 23 (horizontal):** dos líneas a lo largo de toda la tabla en **y = 280** y **y = 520** mm (calle de 240 mm).
3. **Dg 15 (vertical):** dos líneas en **x = 430** y **x = 670** mm, de borde a borde.
4. Comprobar: el cruce es un cuadrado de 240 × 240 mm centrado en (550, 400).

5. **Puente (brazo norte de la Cra 23, a la derecha):** desde la línea de pare (x = 690) la calle conserva sus 4 carriles
   hasta **x = 842**; entre x = 842 y x = 882 se estrecha en diagonal y desde **x = 882 hasta el borde (1100)** queda
   **1 carril por sentido**: calzada solo entre **y = 340 y y = 460**. Las franjas y = 280–340 y y = 460–520 de ese tramo
   son ACERA (no se pintan de gris). Representa la red SUMO: 41 m de 2 carriles + puente de 1 carril (58 m) a 3,7 mm/m.

## 3. Pintar la calzada
1. Pintar toda la tabla de hueso/beige claro (aceras). Luego enmascarar y pintar las dos calles de gris medio mate (2 capas,
   secar entre capas).
2. Retirar la cinta con la pintura aún fresca para bordes limpios.

## 4. Líneas (después de que seque la calzada)
- **Central doble amarilla** (continua, separadas 8 mm): Cra 23 en y = 396 y 404; Dg 15 en x = 546 y 554. **No** se
  pintan dentro del cruce.
- **Carriles** (blanca discontinua: 25 mm de línea, 20 mm de espacio): Cra 23 en y = 340 y 460 (en el brazo norte solo
  hasta x = 842: en el puente no hay línea de carril); Dg 15 en x = 490 y 610. Tampoco dentro del cruce.
- **Borde del puente:** línea continua negra o gris del estrechamiento (842,280)→(882,340)→(1100,340) y
  (842,520)→(882,460)→(1100,460).
- **Líneas de pare** (blancas, 8 mm de ancho, 20 mm antes del cruce, solo en los carriles que LLEGAN):
  | Brazo | Línea de pare |
  |---|---|
  | Cra 23 norte (derecha) | x = 690, de y = 280 a 400 |
  | Cra 23 sur (izquierda) | x = 410, de y = 400 a 520 |
  | Dg 15 este (arriba) | y = 260, de x = 430 a 550 |
  | Dg 15 oeste (abajo) | y = 540, de x = 550 a 670 |
- **Sin texto, flechas pintadas ni dibujos** en la tabla: el modelo confundió texto con carros.

## 5. Semáforos (en postes de ~8 cm, en las aceras, a la derecha de cada acceso, junto a su línea de pare)
Altura ~80 mm: a la escala de un Hot Wheels (1:64) equivale a un semáforo real de 5–6 m. Se ven bien desde el lado
(jurados) y los LED no apuntan a la cámara (evita reflejos).
| Semáforo | Controla | Centro del poste = hueco Ø8 (mm) | Los LED miran hacia |
|---|---|---|---|
| S1 | Cra 23 sur (llegan de la izquierda) | (405, 545) | la izquierda |
| S2 | Cra 23 norte (llegan de la derecha) | (705, 255) | la derecha |
| S3 | Dg 15 oeste (llegan de abajo) | (695, 545) | abajo |
| S4 | Dg 15 este (llegan de arriba) | (405, 255) | arriba |
1. Perforar el hueco de 8 mm **en el centro de cada semáforo**.
2. Poste **hueco** de ~80 mm (tubo PVC delgado, pitillo grueso o listón con canal) **encima del hueco**.
3. Pasar los cables **por dentro del poste** hasta debajo de la tabla; el módulo arriba, con los LED de frente a los
   carros que llegan. Fijar firme con silicona (que no gire al mover carros con la mano).
4. Verificar con la cámara fija (paso 8) que los postes no caen dentro de ninguna zona de conteo ni se detectan como carro.

## 6. Electrónica (debajo de la tabla)
1. Fijar el ESP32 y la protoboard debajo, cerca del borde inferior derecho (junto al poste).
2. Conectar según `hardware/esp32/conexiones.md` (S1: D32/D33/D25, S2: D26/D27/D13, S3: D23/D22/D21, S4: D19/D18/D17;
   **GND común**). Rotular cada cable con cinta (S1-R, S1-Y, ...).
3. Sujetar los cables con cinta o abrazaderas para que no cuelguen.


## 6b. Base de la maqueta (bastidor) y ESP32
Plano: **`hardware/maqueta/base_maqueta.pdf`** (script `scripts/generar_base_maqueta.py`). Todo junto (vista 3D + lista
de cortes + base + soporte): **`hardware/maqueta/planos_maqueta_completos.pdf`**.
- Bastidor de listón 45×70 mm de canto, **80 mm adentro del borde** por los 4 lados (no se ve desde los lados y por ahí
  pasa la pieza que une el poste de la cámara con la base), con 2 travesaños en y = 300 y y = 800 mm.
- Deja **7 cm libres** bajo la tabla. La protoboard con el ESP32 va pegada debajo del **centro del cruce**: los
  4 semáforos quedan a ≈ 20 cm (cables Dupont cortos), por huecos de Ø 8 mm en la base de cada poste.
- El cable USB sale por una muesca de 25×25 mm en el larguero izquierdo, a la altura del cruce.
- La tabla se fija con escuadras y tornillos cortos que **no atraviesan** la superficie pintada.

## 7. Soporte de la cámara
Plano: **`hardware/maqueta/soporte_camara.pdf`** (generado con `scripts/generar_soporte_camara.py`). Está dibujado en la
orientación de la maqueta pintada: tabla vertical 80 × 110 cm, Cra 23 vertical, **puente abajo**, origen arriba-izquierda.
1. Poste de listón 4×4 cm en dos piezas (70 cm + 70 cm; la base sube la tabla 7 cm) solapadas ~25 cm con 2 pernos 1/4" y mariposa; el poste superior
   lleva agujeros cada 25 mm para ajustar la altura.
2. El poste va pegado al **canto derecho**, frente al lote verde de arriba (**y = 250 mm**), apoyado en la mesa, y se
   **atornilla a la base**: una pieza de listón 4×4 cm de 8 cm pasa por debajo de la tabla (en la franja libre entre el
   borde y el larguero derecho) y se fija con 2 escuadras al poste y al larguero. Así la cámara se mueve junto con la
   maqueta y no se pierden las zonas. (Se descartaron las prensas en C.)
3. Brazo de 60 cm encima del poste (1 perno, gira para apuntar). El lente queda a **516 mm** del eje del poste, sobre el
   **centro del cruce (400, 550)**; se centra con una plomada colgada del lente y luego se fija con el refuerzo a 45°.
4. Celular con la **pantalla hacia arriba** y la **cámara trasera mirando a la tabla**, en una pinza con rosca 1/4", lado largo de la imagen a lo largo de la Cra 23, lente a
   **1000 mm** de la superficie de la tabla, nivelado.
5. Cable USB por el brazo y el poste con bridas. Debe quedar **rígido**: si se mueve, hay que redefinir las zonas.
6. Iluminación de los lados (no una lámpara justo encima: el brazo y el celular darían sombra sobre el cruce).

## 8. Verificación (en este orden)
1. **LEDs:** `scripts\windows\probar_esp32_obediente.bat` → los 4 semáforos encienden y cambian como en la prueba 10.5a.
2. **Encuadre:** tomar un cuadro con la cámara fija y la tabla vacía; los bordes de la imagen deben caer ~4 cm dentro del
   borde de la tabla en los lados cortos y ~6 cm en los largos. Si no, ajustar altura/centrado.
3. **Zonas:** con ese cuadro se definen las zonas reales en `config/zonas_camara.yaml` (las dibuja el tutor/código y se
   verifican con `scripts/ver_zonas.py`).
4. **Detección:** foto con 8–12 carros repartidos → contar a mano vs detectados.
5. **Lazo en vivo con ESP32:** `python -m src.maqueta.lazo_camara --fuente <cámara> --zonas config\zonas_camara.yaml --puerto COM4 --mostrar`.
6. Después: grabar los videos para reentrenar YOLO con la maqueta (dos sesiones separadas: entrenamiento y prueba).


## 9. Cómo quedó armada (registro real)
- **Base:** 2 largueros de 930 mm + 2 cabezales de 630 mm + travesaño F de 630 mm **centrado**, listón 4,5 × 4,5 cm,
  sobre 4 tacos de 1 cm. Base **centrada** bajo la tabla (≈ 4 cm libres en cada lado largo, 85 mm en las puntas).
- **Tabla ↔ base:** 4 tornillos de 1½" desde arriba, en zonas verdes, sobre los largueros (a 6,2 y 73,8 cm del borde
  izquierdo; 15 y 95 cm del borde del puente), cabeza hundida y retocada con verde.
- **Taco G (10 cm)** atornillado al larguero del lado donde termina la Dg 15 a la derecha (puente lejos), centrado a
  595 mm del borde del puente; sobresale ≈ 1 mm del borde.
- **Poste C (1300 mm):** apoyado en la mesa, unido a taco + larguero con 2 pernos 1/4" × 6" y tuerca mariposa por dentro
  de la base (desmontable para transportar). 9 agujeros Ø7 cada 25 mm entre 1050 y 1250 mm en la cara que mira al puente.
- **Brazo D (550 mm)** con 2 pernos 1/4" × 5" y mariposa (uno encima del otro, 25 mm) y **refuerzo E** (300 mm, 45°).
  Para transportar se sueltan las 2 mariposas de abajo y sale la L completa.
- **Semáforos:** huecos Ø8 a 2,5 cm de una calle y 3 cm de la otra (los cuatro con el mismo patrón); pitillo ≈ 5,5 cm
  pintado de negro + módulo LED (altura total ≈ 9 cm). Decoración (casas y árboles) en las zonas verdes, pegada.
- **Prueba a 1 m (foto del iPhone, 4:3):** se ve toda la tabla con margen y el cruce cae casi en el centro. Pendiente:
  confirmar el encuadre del **video** con DroidCam.
