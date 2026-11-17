// PRUEBA DE TALLER (no es control de tráfico): enciende el MISMO color en los 4 semáforos a la vez.
//   Todos ROJO 5 s -> todos AMARILLO 5 s -> todos VERDE 5 s -> todo apagado 2 s -> repite.
// Sirve para ver de un vistazo si algún LED no prende (ej.: 2026-11-17, amarillo del S3 apagado).
// Este programa ignora a propósito la regla de "nunca dos verdes": solo se usa en la mesa, sin carros.
// Al terminar, VOLVER A CARGAR hardware/esp32/semaforo_obediente (el que usa Python).
// Placa: "ESP32 Dev Module". Monitor Serie a 115200 baudios (opcional).

struct Semaforo {
  const char* nombre;
  int pinRojo;
  int pinAmarillo;
  int pinVerde;
};

// Mismo mapa de pines que semaforo_obediente.ino (ver hardware/esp32/conexiones.md)
Semaforo semaforos[] = {
  {"S1", 32, 33, 25},
  {"S2", 26, 27, 13},
  {"S3", 23, 22, 21},
  {"S4", 19, 18, 17},
};
const int NUM_SEMAFOROS = 4;
const unsigned long TIEMPO_COLOR_MS = 5000;
const unsigned long TIEMPO_APAGADO_MS = 2000;

enum Color { ROJO, AMARILLO, VERDE, APAGADO };

void ponerTodos(Color color) {
  for (int i = 0; i < NUM_SEMAFOROS; i++) {
    digitalWrite(semaforos[i].pinRojo,     color == ROJO     ? HIGH : LOW);
    digitalWrite(semaforos[i].pinAmarillo, color == AMARILLO ? HIGH : LOW);
    digitalWrite(semaforos[i].pinVerde,    color == VERDE    ? HIGH : LOW);
  }
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_SEMAFOROS; i++) {
    pinMode(semaforos[i].pinRojo, OUTPUT);
    pinMode(semaforos[i].pinAmarillo, OUTPUT);
    pinMode(semaforos[i].pinVerde, OUTPUT);
  }
  ponerTodos(APAGADO);
  delay(500);
  Serial.println();
  Serial.println("=== Prueba de taller: todos del mismo color ===");
}

void loop() {
  Serial.println("Todos ROJO");
  ponerTodos(ROJO);
  delay(TIEMPO_COLOR_MS);
  Serial.println("Todos AMARILLO");
  ponerTodos(AMARILLO);
  delay(TIEMPO_COLOR_MS);
  Serial.println("Todos VERDE");
  ponerTodos(VERDE);
  delay(TIEMPO_COLOR_MS);
  Serial.println("Todo apagado");
  ponerTodos(APAGADO);
  delay(TIEMPO_APAGADO_MS);
}
