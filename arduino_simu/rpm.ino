

/*
void setup_rpm() {
    pinMode(PULSE_PIN, OUTPUT);
    pinMode(DENTE_PIN, OUTPUT);
    digitalWrite(PULSE_PIN, LOW);
    digitalWrite(DENTE_PIN, LOW);
 
}

void loop_rpm() {
    int NUM_DENTES = TOTAL_DENTES - FALHAS;
    float tempo_revolucao = (60.0 / RPM_DESEJADO) * 1000.0;
    float tempo_por_dente = tempo_revolucao / NUM_DENTES;
    float TEMPO_PULSO = tempo_por_dente / 2.0;
    for (int i = 0; i < NUM_DENTES; i++) {
        if (i == DENTE_DENTE && fase_on == 1) {  
            digitalWrite(DENTE_PIN, HIGH);
        } else {
            digitalWrite(DENTE_PIN, LOW);
        }

        // Gera pulso na porta 7
        digitalWrite(PULSE_PIN, HIGH);
        delayMicroseconds(TEMPO_PULSO * 1000);
        digitalWrite(PULSE_PIN, LOW);
        delayMicroseconds(TEMPO_PULSO * 1000);
    }
    float TEMPO_PAUSA = tempo_por_dente * FALHAS;
    delayMicroseconds(TEMPO_PAUSA * 1000);
}
*/
void setup_rpm() {
  pinMode(PULSE_PIN, OUTPUT);
  pinMode(DENTE_PIN, OUTPUT);
  digitalWrite(PULSE_PIN, LOW);
  digitalWrite(DENTE_PIN, LOW);
}

// Estado do pulso
int dente_atual = 0;
bool pulso_alto = false;
unsigned long tempo_anterior = 0;
unsigned long pausa_apos_dentes = 0;
bool em_pausa = false;

void loop_rpm() {
  static unsigned long ultima_acao = 0;
  static bool pulso_em_andamento = false;

  int NUM_DENTES = TOTAL_DENTES - FALHAS;
  unsigned long tempo_revolucao_us = (60000000UL / RPM_DESEJADO); // em microssegundos
  unsigned long tempo_por_dente_us = tempo_revolucao_us / NUM_DENTES;
  unsigned long TEMPO_PULSO = tempo_por_dente_us / 2;

  unsigned long agora = micros();

  if (em_pausa) {
    if (agora - tempo_anterior >= pausa_apos_dentes) {
      dente_atual = 0;
      em_pausa = false;
    }
    return;
  }

  if (!pulso_em_andamento) {
    if (agora - ultima_acao >= tempo_por_dente_us) {
      // Começa pulso novo
      if (dente_atual == DENTE_DENTE && fase_on) {
        digitalWrite(DENTE_PIN, HIGH);
      } else {
        digitalWrite(DENTE_PIN, LOW);
      }

      digitalWrite(PULSE_PIN, HIGH);
      ultima_acao = agora;
      pulso_em_andamento = true;
    }
  } else {
    if (agora - ultima_acao >= TEMPO_PULSO) {
      digitalWrite(PULSE_PIN, LOW);
      pulso_em_andamento = false;
      dente_atual++;

      if (dente_atual >= NUM_DENTES) {
        // Entra em pausa para simular dentes faltantes
        pausa_apos_dentes = tempo_por_dente_us * FALHAS;
        tempo_anterior = micros();
        em_pausa = true;
      }
    }
  }
}