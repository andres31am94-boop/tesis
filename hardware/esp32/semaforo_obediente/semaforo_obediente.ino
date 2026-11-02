// Paso 10.5a - ESP32 OBEDIENTE: Python decide todas las luces; el ESP32 solo las enciende.
// (Reemplaza el protocolo de 10.3/10.4, donde Python mandaba la duración del verde por adelantado:
//  el agente entrenado decide MANTENER/CAMBIAR cada 5 s, así que la duración no se conoce de antemano.)
//
// Quién decide qué:
//   Python (agente + SafetyGuard): cuándo cambiar, verde mínimo/máximo, amarillo, todo rojo.
//   ESP32: obedece, y solo tiene DOS FRENOS DE EMERGENCIA (no son decisiones de tráfico):
//     1. Monitor de conflictos: rechaza
//          - nombres de luz desconocidos (ERROR, no cambia nada)
//          - pasar de VERDE de un eje a cualquier cosa que no sea seguir en verde o su AMARILLO
//            (Manual 2004 cap. 7: nunca de verde a rojo sin amarillo) -> intermitente CONFLICTO (sin recuperación)
//        Dos verdes a la vez no se pueden ni pedir: cada mensaje es UNA luz del cruce completo.
//     2. Vigilancia (watchdog): si no llega ningún mensaje válido en TIEMPO_SIN_PC_MS
//        -> termina el verde con su amarillo (3 s) -> intermitente SIN_PC.
//        Se sale enviando "LUZ TODO_ROJO" (arranque seguro); luego Python sigue normalmente.
//   Intermitente (Manual 2024, 4.2.3): amarillo intermitente Cra 23 (principal), rojo intermitente Dg 15 (secundaria);
//   60 destellos/min con 0,6 s encendido (4.10: 50-60/min, encendido entre 1/2 y 2/3).
//
// Protocolo (una línea por mensaje):
//   PC -> ESP32   LUZ <NOMBRE>   NOMBRE = VERDE_CRA23 | AMARILLO_CRA23 | VERDE_DG15 | AMARILLO_DG15 | TODO_ROJO
//                 Python la envía CADA SEGUNDO aunque no cambie (así el ESP32 sabe que Python está vivo).
//   ESP32 -> PC   LISTO                         al arrancar (luces en TODO_ROJO)
//                 OK <t_ms> <NOMBRE>             cuando la luz cambia por orden de Python
//                 AUTO <t_ms> <NOMBRE>           cuando el ESP32 cambia la luz por un freno (amarillo de emergencia)
//                 MODO INTERMITENTE <motivo>     motivo = SIN_PC | CONFLICTO
//                 MODO NORMAL
//                 ERROR <texto>
// Placa: "ESP32 Dev Module". 115200 baudios.

struct Semaforo {
  int pinRojo;
  int pinAmarillo;
  int pinVerde;
};

Semaforo s1 = {32, 33, 25};  // Cra 23 sur
Semaforo s2 = {26, 27, 13};  // Cra 23 norte
Semaforo s3 = {23, 22, 21};  // Dg 15 oeste
Semaforo s4 = {19, 18, 17};  // Dg 15 este

enum Color { ROJO, AMARILLO, VERDE, APAGADO };

enum Luz { VERDE_CRA23, AMARILLO_CRA23, VERDE_DG15, AMARILLO_DG15, TODO_ROJO, NUM_LUCES };
const char* NOMBRE_LUZ[] = {"VERDE_CRA23", "AMARILLO_CRA23", "VERDE_DG15", "AMARILLO_DG15", "TODO_ROJO"};
const Color COLOR_CRA23[] = {VERDE, AMARILLO, ROJO, ROJO, ROJO};
const Color COLOR_DG15[]  = {ROJO, ROJO, VERDE, AMARILLO, ROJO};

// ---------- Frenos de emergencia ----------
const unsigned long TIEMPO_SIN_PC_MS = 5000;        // Python envía cada 1 s: 5 mensajes perdidos = PC caído
const unsigned long AMARILLO_EMERGENCIA_MS = 3000;  // amarillo antes de pasar a intermitente (= amarillo del cruce)
const unsigned long PERIODO_DESTELLO_MS = 1000;
const unsigned long ENCENDIDO_DESTELLO_MS = 600;

enum Modo { NORMAL, AMARILLO_HACIA_INTERMITENTE, INTERMITENTE };

Luz luzActual = TODO_ROJO;
unsigned long inicioLuzMs = 0;
unsigned long ultimoMensajeMs = 0;
Modo modo = NORMAL;
const char* motivoIntermitente = "";
bool intermitenteRecuperable = true;
unsigned long inicioIntermitenteMs = 0;
String bufferEntrada = "";

// ---------- LEDs ----------
void ponerColor(const Semaforo& s, Color color) {
  digitalWrite(s.pinRojo,     color == ROJO     ? HIGH : LOW);
  digitalWrite(s.pinAmarillo, color == AMARILLO ? HIGH : LOW);
  digitalWrite(s.pinVerde,    color == VERDE    ? HIGH : LOW);
}

void ponerEjes(Color colorCra23, Color colorDg15) {
  ponerColor(s1, colorCra23);
  ponerColor(s2, colorCra23);
  ponerColor(s3, colorDg15);
  ponerColor(s4, colorDg15);
}

void encender(Luz luz) {
  // Primero el rojo de quien pierde el paso, luego el paso.
  if (COLOR_CRA23[luz] == ROJO) { ponerColor(s1, ROJO); ponerColor(s2, ROJO); }
  if (COLOR_DG15[luz] == ROJO)  { ponerColor(s3, ROJO); ponerColor(s4, ROJO); }
  ponerEjes(COLOR_CRA23[luz], COLOR_DG15[luz]);
  luzActual = luz;
  inicioLuzMs = millis();
}

void avisar(const char* tipo, Luz luz) {
  Serial.print(tipo);
  Serial.print(" ");
  Serial.print(millis());
  Serial.print(" ");
  Serial.println(NOMBRE_LUZ[luz]);
}

// ---------- Frenos ----------
bool esVerde(Luz luz) { return luz == VERDE_CRA23 || luz == VERDE_DG15; }
Luz amarilloDe(Luz verde) { return verde == VERDE_CRA23 ? AMARILLO_CRA23 : AMARILLO_DG15; }

// Freno 1: desde un verde solo se puede seguir en ese verde o ir a su amarillo.
bool transicionPermitida(Luz desde, Luz hacia) {
  if (esVerde(desde)) return hacia == desde || hacia == amarilloDe(desde);
  return true;
}

// Lleva el cruce a intermitente de forma segura: si hay un verde, primero su amarillo.
void iniciarFailsafe(const char* motivo, bool recuperable) {
  motivoIntermitente = motivo;
  intermitenteRecuperable = recuperable;
  if (esVerde(luzActual)) {
    encender(amarilloDe(luzActual));
    avisar("AUTO", luzActual);
    modo = AMARILLO_HACIA_INTERMITENTE;
  } else if (luzActual == AMARILLO_CRA23 || luzActual == AMARILLO_DG15) {
    modo = AMARILLO_HACIA_INTERMITENTE;   // se deja terminar el amarillo que ya estaba
  } else {
    entrarIntermitente();
  }
}

void entrarIntermitente() {
  modo = INTERMITENTE;
  inicioIntermitenteMs = millis();
  Serial.print("MODO INTERMITENTE ");
  Serial.println(motivoIntermitente);
}

void actualizarDestello() {
  unsigned long transcurridoMs = (millis() - inicioIntermitenteMs) % PERIODO_DESTELLO_MS;
  bool encendido = transcurridoMs < ENCENDIDO_DESTELLO_MS;
  ponerEjes(encendido ? AMARILLO : APAGADO, encendido ? ROJO : APAGADO);
}

// ---------- Comandos ----------
void procesarComando(String linea) {
  linea.trim();
  if (linea.length() == 0) return;
  if (!linea.startsWith("LUZ ")) {
    Serial.print("ERROR comando no reconocido: ");
    Serial.println(linea);
    return;
  }
  String nombre = linea.substring(4);
  int luzPedida = -1;
  for (int i = 0; i < NUM_LUCES; i++) {
    if (nombre == NOMBRE_LUZ[i]) luzPedida = i;
  }
  if (luzPedida < 0) {
    Serial.print("ERROR luz desconocida: ");
    Serial.println(nombre);
    return;
  }
  Luz luz = (Luz)luzPedida;

  if (modo == INTERMITENTE) {
    if (!intermitenteRecuperable) {
      Serial.println("ERROR intermitente por CONFLICTO: reinicie el ESP32");
      return;
    }
    if (luz != TODO_ROJO) {
      Serial.println("ERROR para salir de intermitente envie LUZ TODO_ROJO");
      return;
    }
    modo = NORMAL;
    ultimoMensajeMs = millis();
    Serial.println("MODO NORMAL");
    encender(TODO_ROJO);
    avisar("OK", TODO_ROJO);
    return;
  }
  if (modo == AMARILLO_HACIA_INTERMITENTE) {
    return;   // ya se está saliendo a intermitente; se ignora hasta terminar
  }

  ultimoMensajeMs = millis();   // mensaje válido: Python está vivo
  if (luz == luzActual) return; // latido: misma luz, nada que hacer

  if (!transicionPermitida(luzActual, luz)) {
    Serial.print("ERROR transicion prohibida ");
    Serial.print(NOMBRE_LUZ[luzActual]);
    Serial.print(" -> ");
    Serial.println(NOMBRE_LUZ[luz]);
    iniciarFailsafe("CONFLICTO", false);
    return;
  }
  encender(luz);
  avisar("OK", luz);
}

void leerSerie() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      procesarComando(bufferEntrada);
      bufferEntrada = "";
    } else if (bufferEntrada.length() < 60) {
      bufferEntrada += c;
    }
  }
}

void configurarPines(const Semaforo& s) {
  pinMode(s.pinRojo, OUTPUT);
  pinMode(s.pinAmarillo, OUTPUT);
  pinMode(s.pinVerde, OUTPUT);
}

void setup() {
  Serial.begin(115200);
  configurarPines(s1);
  configurarPines(s2);
  configurarPines(s3);
  configurarPines(s4);
  encender(TODO_ROJO);
  delay(500);
  Serial.println();
  Serial.println("LISTO");
  ultimoMensajeMs = millis();
}

void loop() {
  leerSerie();
  if (modo == NORMAL && millis() - ultimoMensajeMs >= TIEMPO_SIN_PC_MS) {
    iniciarFailsafe("SIN_PC", true);
  }
  if (modo == AMARILLO_HACIA_INTERMITENTE && millis() - inicioLuzMs >= AMARILLO_EMERGENCIA_MS) {
    entrarIntermitente();
  }
  if (modo == INTERMITENTE) {
    actualizarDestello();
  }
}
