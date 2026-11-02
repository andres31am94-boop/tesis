// Paso 10.2 - Semáforo de tiempos fijos (plan real medido en campo) en la maqueta.
// Tiempos copiados de config/controlador.yaml (perfil "seguridad" + tiempos_fijos):
//   Dg 15 verde 20 s -> amarillo 3 s -> todo rojo 20 s (peatones)
//   Cra 23 verde 55 s -> amarillo 3 s -> todo rojo 0 s
//   Ciclo = 101 s. El ciclo arranca con la Dg 15 en verde (eje_inicial).
// Placa: "ESP32 Dev Module". Monitor Serie a 115200 baudios.

// ---------- Pines (ver hardware/esp32/conexiones.md) ----------
struct Semaforo {
  const char* nombre;
  int pinRojo;
  int pinAmarillo;
  int pinVerde;
};

Semaforo s1 = {"S1 Cra23 sur",   32, 33, 25};
Semaforo s2 = {"S2 Cra23 norte", 26, 27, 13};
Semaforo s3 = {"S3 Dg15 oeste",  23, 22, 21};
Semaforo s4 = {"S4 Dg15 este",   19, 18, 17};

// ---------- Tiempos (segundos) ----------
const unsigned long VERDE_CRA23_S    = 55;
const unsigned long VERDE_DG15_S     = 20;
const unsigned long AMARILLO_S       = 3;
const unsigned long TODO_ROJO_CRA23_S = 0;
const unsigned long TODO_ROJO_DG15_S  = 20;

// 1 = tiempo real. Para demostraciones rápidas se puede poner 5 (todo 5 veces más rápido).
// Los resultados de la tesis se reportan con 1.
const unsigned long FACTOR_VELOCIDAD = 1;

// ---------- Colores y fases ----------
enum Color { ROJO, AMARILLO, VERDE };

struct Fase {
  const char* nombre;
  Color colorCra23;   // S1 y S2
  Color colorDg15;    // S3 y S4
  unsigned long duracionS;
};

// Orden del ciclo. Ninguna fase tiene verde o amarillo en los dos ejes a la vez.
Fase fases[] = {
  {"Dg15 VERDE",          ROJO,     VERDE,    VERDE_DG15_S},
  {"Dg15 AMARILLO",       ROJO,     AMARILLO, AMARILLO_S},
  {"TODO ROJO (peatones)",ROJO,     ROJO,     TODO_ROJO_DG15_S},
  {"Cra23 VERDE",         VERDE,    ROJO,     VERDE_CRA23_S},
  {"Cra23 AMARILLO",      AMARILLO, ROJO,     AMARILLO_S},
  {"TODO ROJO",           ROJO,     ROJO,     TODO_ROJO_CRA23_S},
};
const int NUM_FASES = sizeof(fases) / sizeof(fases[0]);

int faseActual = 0;
unsigned long inicioFaseMs = 0;
unsigned long numeroCiclo = 1;

void ponerColor(const Semaforo& s, Color color) {
  digitalWrite(s.pinRojo,     color == ROJO     ? HIGH : LOW);
  digitalWrite(s.pinAmarillo, color == AMARILLO ? HIGH : LOW);
  digitalWrite(s.pinVerde,    color == VERDE    ? HIGH : LOW);
}

void todoRojo() {
  ponerColor(s1, ROJO);
  ponerColor(s2, ROJO);
  ponerColor(s3, ROJO);
  ponerColor(s4, ROJO);
}

// Regla de seguridad: los dos ejes nunca pueden tener paso (verde o amarillo) al mismo tiempo.
bool faseEsSegura(const Fase& fase) {
  return fase.colorCra23 == ROJO || fase.colorDg15 == ROJO;
}

void aplicarFase(int indice) {
  const Fase& fase = fases[indice];
  if (!faseEsSegura(fase)) {
    // No debería ocurrir con la tabla de arriba; si alguien la edita mal, se queda en rojo.
    todoRojo();
    Serial.print("ERROR: fase insegura bloqueada: ");
    Serial.println(fase.nombre);
    while (true) { delay(1000); }
  }
  // Primero se pone en rojo el eje que pierde el paso y luego se da paso al otro.
  todoRojo();
  ponerColor(s1, fase.colorCra23);
  ponerColor(s2, fase.colorCra23);
  ponerColor(s3, fase.colorDg15);
  ponerColor(s4, fase.colorDg15);

  Serial.print("[t=");
  Serial.print(millis() / 1000);
  Serial.print(" s] ciclo ");
  Serial.print(numeroCiclo);
  Serial.print(" | ");
  Serial.print(fase.nombre);
  Serial.print(" (");
  Serial.print(fase.duracionS);
  Serial.println(" s)");
}

void configurarPines(const Semaforo& s) {
  pinMode(s.pinRojo, OUTPUT);
  pinMode(s.pinAmarillo, OUTPUT);
  pinMode(s.pinVerde, OUTPUT);
}

// Salta las fases de 0 s (el todo-rojo de la Cra 23 dura 0 s en el semáforo real).
void avanzarFase() {
  do {
    faseActual = (faseActual + 1) % NUM_FASES;
    if (faseActual == 0) {
      numeroCiclo++;
    }
  } while (fases[faseActual].duracionS == 0);
  aplicarFase(faseActual);
  inicioFaseMs = millis();
}

void setup() {
  Serial.begin(115200);
  configurarPines(s1);
  configurarPines(s2);
  configurarPines(s3);
  configurarPines(s4);
  todoRojo();
  delay(1000);
  Serial.println();
  Serial.println("=== Semaforo tiempos fijos (plan real, ciclo 101 s) ===");
  Serial.print("Factor de velocidad: ");
  Serial.println(FACTOR_VELOCIDAD);
  faseActual = 0;
  aplicarFase(faseActual);
  inicioFaseMs = millis();
}

void loop() {
  unsigned long duracionMs = fases[faseActual].duracionS * 1000UL / FACTOR_VELOCIDAD;
  if (millis() - inicioFaseMs >= duracionMs) {
    avanzarFase();
  }
}
