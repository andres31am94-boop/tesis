// Paso 10.3 - Semáforo controlado desde Python por el puerto serie (USB).
//
// Idea: el ESP32 mantiene la estructura del ciclo (verde -> amarillo -> todo rojo -> otro eje) y la SEGURIDAD.
// Python solo decide CUÁNTO dura el próximo verde de cada eje (la misma acción que elige el agente en SUMO).
//
// Protocolo (una línea de texto por mensaje, terminada en '\n'):
//   ESP32 -> PC  "LISTO"                              al arrancar
//   ESP32 -> PC  "FASE <t_s> <ciclo> <nombre> <s>"    cada cambio de fase
//   ESP32 -> PC  "SOLICITUD <EJE>"                    pide el verde del próximo eje (al empezar el amarillo del otro)
//   PC -> ESP32  "VERDE <EJE> <s>"                    EJE = CRA23 o DG15
//   ESP32 -> PC  "OK VERDE <EJE> <s>"                 aceptado tal cual
//   ESP32 -> PC  "AJUSTADO VERDE <EJE> <pedido> <aplicado>"   recortado a los límites de seguridad
//   ESP32 -> PC  "SIN_RESPUESTA <EJE> <s>"           no llegó orden a tiempo: usa el plan real
//   ESP32 -> PC  "ERROR <texto>"                      comando no reconocido
//
// Límites (copiados de config/controlador.yaml, perfil "seguridad"). Están en el ESP32 a propósito:
// aunque Python falle o mande algo absurdo, el semáforo físico no los puede violar.
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

enum Eje { CRA23 = 0, DG15 = 1 };
const char* NOMBRE_EJE[] = {"CRA23", "DG15"};

// ---------- Límites de seguridad (s) ----------
const int VERDE_MIN_S[] = {20, 15};
const int VERDE_MAX_S[] = {70, 25};
const int AMARILLO_S = 3;
const int TODO_ROJO_S[] = {0, 20};      // todo rojo DESPUÉS del verde de cada eje
const int VERDE_PLAN_S[] = {55, 20};    // plan real: se usa si Python no responde

enum Color { ROJO, AMARILLO, VERDE };

enum TipoFase { F_VERDE, F_AMARILLO, F_TODO_ROJO };

struct Fase {
  const char* nombre;
  Eje eje;          // eje al que pertenece la fase
  TipoFase tipo;
};

// Ciclo: arranca con la Dg 15 (eje_inicial).
Fase fases[] = {
  {"DG15_VERDE",         DG15,  F_VERDE},
  {"DG15_AMARILLO",      DG15,  F_AMARILLO},
  {"TODO_ROJO_PEATONES", DG15,  F_TODO_ROJO},
  {"CRA23_VERDE",        CRA23, F_VERDE},
  {"CRA23_AMARILLO",     CRA23, F_AMARILLO},
  {"TODO_ROJO",          CRA23, F_TODO_ROJO},
};
const int NUM_FASES = sizeof(fases) / sizeof(fases[0]);

int faseActual = 0;
int duracionFaseActualS = 0;
unsigned long inicioFaseMs = 0;
unsigned long numeroCiclo = 1;
int verdePendienteS[] = {-1, -1};   // -1 = Python todavía no decidió el próximo verde de ese eje

String bufferEntrada = "";

// ---------- LEDs ----------
void ponerColor(const Semaforo& s, Color color) {
  digitalWrite(s.pinRojo,     color == ROJO     ? HIGH : LOW);
  digitalWrite(s.pinAmarillo, color == AMARILLO ? HIGH : LOW);
  digitalWrite(s.pinVerde,    color == VERDE    ? HIGH : LOW);
}

void mostrar(Color colorCra23, Color colorDg15) {
  // Regla de seguridad: nunca paso (verde o amarillo) en los dos ejes a la vez.
  if (colorCra23 != ROJO && colorDg15 != ROJO) {
    colorCra23 = ROJO;
    colorDg15 = ROJO;
    Serial.println("ERROR combinacion insegura bloqueada, todo rojo");
  }
  // Primero se pone en rojo lo que pierde el paso, luego se da el paso.
  if (colorCra23 == ROJO) { ponerColor(s1, ROJO); ponerColor(s2, ROJO); }
  if (colorDg15 == ROJO)  { ponerColor(s3, ROJO); ponerColor(s4, ROJO); }
  ponerColor(s1, colorCra23);
  ponerColor(s2, colorCra23);
  ponerColor(s3, colorDg15);
  ponerColor(s4, colorDg15);
}

// ---------- Fases ----------
int duracionDeFase(int indice) {
  const Fase& fase = fases[indice];
  if (fase.tipo == F_AMARILLO) return AMARILLO_S;
  if (fase.tipo == F_TODO_ROJO) return TODO_ROJO_S[fase.eje];
  // Verde: lo que haya decidido Python, o el plan real si no respondió.
  int verde = verdePendienteS[fase.eje];
  if (verde < 0) {
    verde = VERDE_PLAN_S[fase.eje];
    Serial.print("SIN_RESPUESTA ");
    Serial.print(NOMBRE_EJE[fase.eje]);
    Serial.print(" ");
    Serial.println(verde);
  }
  verdePendienteS[fase.eje] = -1;   // la decisión se consume: el próximo verde necesita una nueva
  return verde;
}

void aplicarFase(int indice) {
  const Fase& fase = fases[indice];
  duracionFaseActualS = duracionDeFase(indice);

  Color colorEje = (fase.tipo == F_VERDE) ? VERDE : (fase.tipo == F_AMARILLO ? AMARILLO : ROJO);
  if (fase.eje == CRA23) mostrar(colorEje, ROJO);
  else                   mostrar(ROJO, colorEje);

  Serial.print("FASE ");
  Serial.print(millis() / 1000);
  Serial.print(" ");
  Serial.print(numeroCiclo);
  Serial.print(" ");
  Serial.print(fase.nombre);
  Serial.print(" ");
  Serial.println(duracionFaseActualS);

  // Al empezar el amarillo de un eje se le pide a Python el verde del otro eje.
  if (fase.tipo == F_AMARILLO) {
    Eje siguiente = (fase.eje == CRA23) ? DG15 : CRA23;
    Serial.print("SOLICITUD ");
    Serial.println(NOMBRE_EJE[siguiente]);
  }
  inicioFaseMs = millis();
}

void avanzarFase() {
  do {
    faseActual = (faseActual + 1) % NUM_FASES;
    if (faseActual == 0) numeroCiclo++;
  } while (fases[faseActual].tipo == F_TODO_ROJO && TODO_ROJO_S[fases[faseActual].eje] == 0);
  aplicarFase(faseActual);
}

// ---------- Comandos desde Python ----------
void procesarComando(String linea) {
  linea.trim();
  if (linea.length() == 0) return;

  // Formato esperado: VERDE <EJE> <s>
  int espacio1 = linea.indexOf(' ');
  int espacio2 = linea.indexOf(' ', espacio1 + 1);
  if (espacio1 < 0 || espacio2 < 0 || linea.substring(0, espacio1) != "VERDE") {
    Serial.print("ERROR comando no reconocido: ");
    Serial.println(linea);
    return;
  }
  String textoEje = linea.substring(espacio1 + 1, espacio2);
  String textoSegundos = linea.substring(espacio2 + 1);

  int eje;
  if (textoEje == "CRA23") eje = CRA23;
  else if (textoEje == "DG15") eje = DG15;
  else {
    Serial.print("ERROR eje desconocido: ");
    Serial.println(textoEje);
    return;
  }

  for (unsigned int i = 0; i < textoSegundos.length(); i++) {
    if (!isDigit(textoSegundos[i])) {
      Serial.print("ERROR segundos no validos: ");
      Serial.println(textoSegundos);
      return;
    }
  }
  int pedido = textoSegundos.toInt();
  int aplicado = constrain(pedido, VERDE_MIN_S[eje], VERDE_MAX_S[eje]);
  verdePendienteS[eje] = aplicado;

  if (aplicado == pedido) {
    Serial.print("OK VERDE ");
    Serial.print(NOMBRE_EJE[eje]);
    Serial.print(" ");
    Serial.println(aplicado);
  } else {
    Serial.print("AJUSTADO VERDE ");
    Serial.print(NOMBRE_EJE[eje]);
    Serial.print(" ");
    Serial.print(pedido);
    Serial.print(" ");
    Serial.println(aplicado);
  }
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
  mostrar(ROJO, ROJO);
  delay(1000);
  Serial.println();
  Serial.println("LISTO");
  // El primer verde (Dg 15) usa el plan real: todavía no hubo solicitud.
  verdePendienteS[DG15] = VERDE_PLAN_S[DG15];
  faseActual = 0;
  aplicarFase(faseActual);
}

void loop() {
  leerSerie();
  if (millis() - inicioFaseMs >= (unsigned long)duracionFaseActualS * 1000UL) {
    avanzarFase();
  }
}
