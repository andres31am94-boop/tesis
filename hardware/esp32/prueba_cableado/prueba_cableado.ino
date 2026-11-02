// Paso 10.1 - Prueba de cableado de los 4 semáforos de la maqueta.
// Enciende cada LED uno por uno (1 s) e imprime cuál es por el Monitor Serie.
// Si el LED que se enciende no coincide con el texto, el cable está mal.
// Placa: "ESP32 Dev Module". Monitor Serie a 115200 baudios.

struct Led {
  const char* nombre;
  int pin;
};

// Mapa de pines (ver hardware/esp32/conexiones.md)
Led leds[] = {
  {"S1 Cra23 SUR   - ROJO",     32},
  {"S1 Cra23 SUR   - AMARILLO", 33},
  {"S1 Cra23 SUR   - VERDE",    25},
  {"S2 Cra23 NORTE - ROJO",     26},
  {"S2 Cra23 NORTE - AMARILLO", 27},
  {"S2 Cra23 NORTE - VERDE",    13},
  {"S3 Dg15 OESTE  - ROJO",     23},
  {"S3 Dg15 OESTE  - AMARILLO", 22},
  {"S3 Dg15 OESTE  - VERDE",    21},
  {"S4 Dg15 ESTE   - ROJO",     19},
  {"S4 Dg15 ESTE   - AMARILLO", 18},
  {"S4 Dg15 ESTE   - VERDE",    17},
};
const int NUM_LEDS = sizeof(leds) / sizeof(leds[0]);
const unsigned long TIEMPO_ENCENDIDO_MS = 1000;

void apagarTodos() {
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(leds[i].pin, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(leds[i].pin, OUTPUT);
  }
  apagarTodos();
  delay(500);
  Serial.println();
  Serial.println("=== Prueba de cableado: 12 LEDs ===");
}

void loop() {
  for (int i = 0; i < NUM_LEDS; i++) {
    apagarTodos();
    digitalWrite(leds[i].pin, HIGH);
    Serial.print("Encendido: ");
    Serial.print(leds[i].nombre);
    Serial.print("  (GPIO ");
    Serial.print(leds[i].pin);
    Serial.println(")");
    delay(TIEMPO_ENCENDIDO_MS);
  }
  apagarTodos();
  Serial.println("--- vuelta completa ---");
  delay(1500);
}
