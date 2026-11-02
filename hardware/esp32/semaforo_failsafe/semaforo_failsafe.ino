// Paso 10.4 - Semáforo controlado desde Python + modo a prueba de fallas (fail-safe).
// Parte del paso 10.3 (semaforo_serial.ino, validado) y agrega:
//   1. Si Python deja de responder: primero sigue con el plan real (55/20) durante 2 ciclos.
//   2. Si la falta de respuesta continúa: pasa a INTERMITENTE
//        Cra 23 (vía principal)  -> amarillo intermitente
//        Dg 15  (vía secundaria) -> rojo intermitente
//      Manual de Señalización Vial 2024, 4.2.3 (Controlador): ante fallas o estados conflictivos la señalización
//      "debe tornarse en amarillo intermitente para la vía principal y en rojo intermitente para la vía secundaria".
//      Destellos: 4.10 (características): 50 a 60 por minuto, encendido entre 1/2 y 2/3 del ciclo de destello.
//   3. Si Python vuelve (responde "VERDE CRA23 <s>"): todo rojo 20 s y retoma el ciclo con la Cra 23 en verde.
//   4. Si se detecta una combinación insegura (paso en los dos ejes): intermitente SIN recuperación automática
//      (hay que reiniciar el ESP32), como pide el Manual hasta que se corrija el error.
//
// Protocolo (una línea por mensaje):
//   ESP32 -> PC  LISTO | FASE <t_s> <ciclo> <nombre> <s> | SOLICITUD <EJE>
//                OK VERDE <EJE> <s> | AJUSTADO VERDE <EJE> <pedido> <aplicado> | SIN_RESPUESTA <EJE> <s> <n_seguidas>
//                MODO INTERMITENTE <motivo> | MODO NORMAL | ERROR <texto>
//   PC -> ESP32  VERDE <EJE> <s>      (EJE = CRA23 o DG15)
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

// ---------- Límites de seguridad (s), de config/controlador.yaml ----------
const int VERDE_MIN_S[] = {20, 15};
const int VERDE_MAX_S[] = {70, 25};
const int AMARILLO_S = 3;
const int TODO_ROJO_S[] = {0, 20};      // todo rojo DESPUÉS del verde de cada eje
const int VERDE_PLAN_S[] = {55, 20};    // plan real: respaldo si Python no responde

// ---------- Fail-safe ----------
// Verdes seguidos con el plan real antes de pasar a intermitente: 4 = 2 ciclos completos (~3.5 min).
const int MAX_VERDES_SIN_PC = 4;
// Destello: 60 por minuto (periodo 1000 ms), encendido 600 ms (entre 1/2 y 2/3 del periodo).
const unsigned long PERIODO_DESTELLO_MS = 1000;
const unsigned long ENCENDIDO_DESTELLO_MS = 600;
// En intermitente se le pregunta a Python cada cierto tiempo si ya puede retomar el control.
const unsigned long INTERVALO_SOLICITUD_INTERMITENTE_MS = 5000;

enum Color { ROJO, AMARILLO, VERDE, APAGADO };
enum TipoFase { F_VERDE, F_AMARILLO, F_TODO_ROJO };

struct Fase {
  const char* nombre;
  Eje eje;
  TipoFase tipo;
};

Fase fases[] = {
  {"DG15_VERDE",         DG15,  F_VERDE},
  {"DG15_AMARILLO",      DG15,  F_AMARILLO},
  {"TODO_ROJO_PEATONES", DG15,  F_TODO_ROJO},
  {"CRA23_VERDE",        CRA23, F_VERDE},
  {"CRA23_AMARILLO",     CRA23, F_AMARILLO},
  {"TODO_ROJO",          CRA23, F_TODO_ROJO},
};
const int NUM_FASES = sizeof(fases) / sizeof(fases[0]);
const int INDICE_TODO_ROJO_PEATONES = 2;   // fase previa al verde de la Cra 23 (se usa al salir de intermitente)

int faseActual = 0;
int duracionFaseActualS = 0;
unsigned long inicioFaseMs = 0;
unsigned long numeroCiclo = 1;
int verdePendienteS[] = {-1, -1};   // -1 = Python todavía no decidió el próximo verde de ese eje
int verdesSinPcSeguidos = 0;

bool modoIntermitente = false;
bool intermitenteRecuperable = true;
unsigned long inicioIntermitenteMs = 0;
unsigned long ultimaSolicitudIntermitenteMs = 0;

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

void entrarIntermitente(const char* motivo, bool recuperable) {
  modoIntermitente = true;
  intermitenteRecuperable = recuperable;
  inicioIntermitenteMs = millis();
  ultimaSolicitudIntermitenteMs = millis();
  Serial.print("MODO INTERMITENTE ");
  Serial.println(motivo);
}

void mostrar(Color colorCra23, Color colorDg15) {
  // Regla de seguridad: nunca paso (verde o amarillo) en los dos ejes a la vez.
  if (colorCra23 != ROJO && colorDg15 != ROJO) {
    ponerEjes(ROJO, ROJO);
    entrarIntermitente("CONFLICTO", false);
    return;
  }
  // Primero se pone en rojo lo que pierde el paso, luego se da el paso.
  if (colorCra23 == ROJO) { ponerColor(s1, ROJO); ponerColor(s2, ROJO); }
  if (colorDg15 == ROJO)  { ponerColor(s3, ROJO); ponerColor(s4, ROJO); }
  ponerEjes(colorCra23, colorDg15);
}

void actualizarDestello() {
  unsigned long transcurridoMs = (millis() - inicioIntermitenteMs) % PERIODO_DESTELLO_MS;
  bool encendido = transcurridoMs < ENCENDIDO_DESTELLO_MS;
  ponerEjes(encendido ? AMARILLO : APAGADO, encendido ? ROJO : APAGADO);
}

// ---------- Fases ----------
void imprimirFase(const char* nombre, int duracionS) {
  Serial.print("FASE ");
  Serial.print(millis() / 1000);
  Serial.print(" ");
  Serial.print(numeroCiclo);
  Serial.print(" ");
  Serial.print(nombre);
  Serial.print(" ");
  Serial.println(duracionS);
}

void aplicarFase(int indice) {
  const Fase& fase = fases[indice];

  if (fase.tipo == F_VERDE) {
    int verde = verdePendienteS[fase.eje];
    if (verde < 0) {
      verdesSinPcSeguidos++;
      if (verdesSinPcSeguidos > MAX_VERDES_SIN_PC) {
        // Venimos de amarillo o todo rojo: es seguro empezar a destellar.
        entrarIntermitente("SIN_PC", true);
        return;
      }
      verde = VERDE_PLAN_S[fase.eje];
      Serial.print("SIN_RESPUESTA ");
      Serial.print(NOMBRE_EJE[fase.eje]);
      Serial.print(" ");
      Serial.print(verde);
      Serial.print(" ");
      Serial.println(verdesSinPcSeguidos);
    }
    verdePendienteS[fase.eje] = -1;   // la decisión se consume
    duracionFaseActualS = verde;
  } else if (fase.tipo == F_AMARILLO) {
    duracionFaseActualS = AMARILLO_S;
  } else {
    duracionFaseActualS = TODO_ROJO_S[fase.eje];
  }

  Color colorEje = (fase.tipo == F_VERDE) ? VERDE : (fase.tipo == F_AMARILLO ? AMARILLO : ROJO);
  if (fase.eje == CRA23) mostrar(colorEje, ROJO);
  else                   mostrar(ROJO, colorEje);
  if (modoIntermitente) return;   // mostrar() detectó un conflicto

  imprimirFase(fase.nombre, duracionFaseActualS);

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

void salirIntermitente() {
  modoIntermitente = false;
  verdesSinPcSeguidos = 0;
  Serial.println("MODO NORMAL");
  // Todo rojo 20 s y luego verde a la Cra 23 con la duración que mandó Python.
  faseActual = INDICE_TODO_ROJO_PEATONES;
  aplicarFase(faseActual);
}

// ---------- Comandos desde Python ----------
void procesarComando(String linea) {
  linea.trim();
  if (linea.length() == 0) return;

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
  if (textoSegundos.length() == 0) {
    Serial.println("ERROR segundos vacios");
    return;
  }
  for (unsigned int i = 0; i < textoSegundos.length(); i++) {
    if (!isDigit(textoSegundos[i])) {
      Serial.print("ERROR segundos no validos: ");
      Serial.println(textoSegundos);
      return;
    }
  }

  if (modoIntermitente) {
    if (!intermitenteRecuperable) {
      Serial.println("ERROR intermitente por CONFLICTO: reinicie el ESP32");
      return;
    }
    if (eje != CRA23) {
      Serial.println("ERROR en intermitente se espera VERDE CRA23");
      return;
    }
  }

  int pedido = textoSegundos.toInt();
  int aplicado = constrain(pedido, VERDE_MIN_S[eje], VERDE_MAX_S[eje]);
  verdePendienteS[eje] = aplicado;
  verdesSinPcSeguidos = 0;   // Python está vivo

  Serial.print(aplicado == pedido ? "OK VERDE " : "AJUSTADO VERDE ");
  Serial.print(NOMBRE_EJE[eje]);
  Serial.print(" ");
  if (aplicado != pedido) {
    Serial.print(pedido);
    Serial.print(" ");
  }
  Serial.println(aplicado);

  if (modoIntermitente) {
    salirIntermitente();
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
  ponerEjes(ROJO, ROJO);
  delay(1000);
  Serial.println();
  Serial.println("LISTO");
  verdePendienteS[DG15] = VERDE_PLAN_S[DG15];   // el primer verde usa el plan real (aún no hubo solicitud)
  faseActual = 0;
  aplicarFase(faseActual);
}

void loop() {
  leerSerie();
  if (modoIntermitente) {
    actualizarDestello();
    if (intermitenteRecuperable && millis() - ultimaSolicitudIntermitenteMs >= INTERVALO_SOLICITUD_INTERMITENTE_MS) {
      Serial.println("SOLICITUD CRA23");
      ultimaSolicitudIntermitenteMs = millis();
    }
    return;
  }
  if (millis() - inicioFaseMs >= (unsigned long)duracionFaseActualS * 1000UL) {
    avanzarFase();
  }
}
