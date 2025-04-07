#include <SPI.h>
#include <mcp2515.h>

// Configurações ajustáveis
#define PULSE_PIN 0
#define DENTE_PIN 12
const uint8_t pwm_pins[2] = {9, 5}; // Timer1 no pino 9, Timer3 no pino 5
byte pino_can = 13;

float RPM_DESEJADO = 500;  // Insira aqui o RPM desejado
int TOTAL_DENTES = 10;
int FALHAS = 1;
int DENTE_DENTE = 0;
int fase_on = 0;

struct can_frame canMessage;
MCP2515 mcp2515(pino_can);


int pwm_freq[2] = {1000, 1000};
int pwm_duty[2] = {50, 50};
int pwm_on[2] = {1,1};




void setup() {
  Serial.begin(115200);
    mcp2515.reset();
  mcp2515.setBitrate(CAN_125KBPS);
  mcp2515.setNormalMode();
  setup_pwm();
  setup_rpm();
}

void loop() {
  loop_pwm() ;
  loop_rpm();
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("can:")) {
      // Exemplo: can:100;255
      int sep = cmd.indexOf(';');
      if (sep > 4) {
        String id_str = cmd.substring(4, sep);
        String data_str = cmd.substring(sep + 1);

        uint16_t can_id = (uint16_t)strtol(id_str.c_str(), NULL, 0); // Suporta decimal e hexadecimal (0x...)
        uint8_t value = (uint8_t)data_str.toInt();

        canMessage.can_id  = can_id;
        canMessage.can_dlc = 1;
        canMessage.data[0] = value;

        mcp2515.sendMessage(&canMessage);
        Serial.println("can OK");
      }
      } else if (cmd.startsWith("DENTES:")) {
        TOTAL_DENTES = cmd.substring(7).toInt();
      } else if (cmd.startsWith("RPM:")) {
        RPM_DESEJADO = cmd.substring(4).toInt();  // 4 porque "RPM:" tem 4 caracteres
      } else if (cmd.startsWith("FALHAS:")) {
        FALHAS = cmd.substring(7).toInt();
      } else if (cmd.startsWith("FASE:")) {
        DENTE_DENTE = cmd.substring(5).toInt();
      } else if (cmd.startsWith("FASE_ON:")) {
        fase_on = cmd.substring(8).toInt();  // corrigido de 5 para 8
      } else if (cmd.startsWith("PWM1_FREQ:")) {
        pwm_freq[0] = cmd.substring(10).toInt();
      } else if (cmd.startsWith("PWM1_DUTY:")) {
        pwm_duty[0] = cmd.substring(10).toInt();
      } else if (cmd.startsWith("PWM1_ON:")) {
        pwm_on[0] = cmd.substring(8).toInt();  // "PWM1_ON:" tem 8 caracteres
      } else if (cmd.startsWith("PWM2_FREQ:")) {
        pwm_freq[1] = cmd.substring(10).toInt();
      } else if (cmd.startsWith("PWM2_ON:")) {
        pwm_on[1] = cmd.substring(8).toInt();  // corrigido de 10 para 9
        Serial.println("TOTAL_DENTES:" + String(TOTAL_DENTES));
    Serial.println("RPM:" + String(RPM_DESEJADO));
    Serial.println("FALHAS:" + String(FALHAS));
    Serial.println("FASE:" + String(DENTE_DENTE));
    Serial.println("FASE_ON:" + String(fase_on));
    Serial.println("PWM1_FREQ:" + String(pwm_freq[0]));
    Serial.println("PWM1_DUTY:" + String(pwm_duty[0]));
    Serial.println("PWM1_ON:" + String(pwm_on[0]));
    Serial.println("PWM2_FREQ:" + String(pwm_freq[1]));
    Serial.println("PWM2_DUTY:" + String(pwm_duty[1]));
    Serial.println("PWM2_ON:" + String(pwm_on[1]));
      } else if (cmd.startsWith("PWM2_DUTY:")) {
        pwm_duty[1] = cmd.substring(10).toInt();
      }

  }

  // Envia os dados analógicos das portas A0-A5
  String data = "A=";
  for (int i = 0; i < 6; i++) {
    data += String(analogRead(i));
    if (i < 5) data += ",";
  }
  Serial.println(data);

   if (mcp2515.readMessage(&canMessage) == MCP2515::ERROR_OK) {
    Serial.println(String("can: ") + "CAN_ID >" + String(canMessage.can_id) + "< =" + String(canMessage.data[0]) + ";");
  }
}
