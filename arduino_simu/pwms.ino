#include <TimerOne.h>
#include <TimerThree.h>

void setup_pwm() {

  // === PWM 1 - TimerOne ===
 
    pinMode(pwm_pins[0], OUTPUT);
    Timer1.initialize(1000000L / pwm_freq[0]); // período em microssegundos
    Timer1.pwm(pwm_pins[0], map(pwm_duty[0], 0, 100, 0, 1023));


  // === PWM 2 - TimerThree ===

    pinMode(pwm_pins[1], OUTPUT);
    Timer3.initialize(1000000L / pwm_freq[1]);
    Timer3.pwm(pwm_pins[1], map(pwm_duty[1], 0, 100, 0, 1023));

}

void loop_pwm() {
    if (pwm_on[0] == 0) {
      Timer1.setPeriod(1000000L /1);
      Timer1.setPwmDuty(pwm_pins[0], 0);
    }else{
      Timer1.setPeriod(1000000L / pwm_freq[0]);
      Timer1.setPwmDuty(pwm_pins[0], map(pwm_duty[0], 0, 100, 0, 1023));
    }
    if (pwm_on[1] == 0) {
      Timer3.setPeriod(1000000L / 1);
      Timer3.setPwmDuty(pwm_pins[1],0);
    }else{
      Timer3.setPeriod(1000000L / pwm_freq[1]);
      Timer3.setPwmDuty(pwm_pins[1], map(pwm_duty[1], 0, 100, 0, 1023));
    }
}
