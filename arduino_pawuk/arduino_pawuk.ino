#include <Multiservo.h>

Multiservo servo_pp1, servo_pp2, servo_pp3; // Передня права
Multiservo servo_pl1, servo_pl2, servo_pl3; // Передня ліва
Multiservo servo_zp1, servo_zp2, servo_zp3; // Задня права
Multiservo servo_zl1, servo_zl2, servo_zl3; // Задня ліва

int SWING = 30;
int LIFT = 35;
int HEIGHT = 90;
int SPEED_DELAY = 15;

bool is_walking = false;
String current_direction = "stop"; 

void setAllTo90() {
  is_walking = false;
  current_direction = "stop";
  
  servo_pl1.write(90); servo_pl2.write(90); servo_pl3.write(90);
  servo_zl1.write(90); servo_zl2.write(90); servo_zl3.write(90);
  servo_zp1.write(90); servo_zp2.write(90); servo_zp3.write(90);
  servo_pp1.write(90); servo_pp2.write(90); servo_pp3.write(90);
}

void setup() {
  Serial.begin(9600);
  servo_pl1.attach(14); servo_pl2.attach(13); servo_pl3.attach(12);
  servo_zl1.attach(15); servo_zl2.attach(16); servo_zl3.attach(17);
  servo_zp1.attach(5);  servo_zp2.attach(4);  servo_zp3.attach(3);
  servo_pp1.attach(9);  servo_pp2.attach(10); servo_pp3.attach(11);

  setAllTo90();
  delay(1000);
}

void moveSingleLegInAir(int leg_id, int target_coxa, int target_femur, int target_tibia) {
  for (int f = 0; f <= 20; f++) {
    if (Serial.available() > 0) return;
    float t = (float)f / 20.0;
    int cur_femur = HEIGHT - (LIFT * t);
    int cur_tibia = 90 + (10 * t);
    
         if (leg_id == 0) { servo_pl2.write(cur_femur); servo_pl3.write(cur_tibia); }
    else if (leg_id == 1) { servo_zl2.write(cur_femur); servo_zl3.write(cur_tibia); }
    else if (leg_id == 2) { servo_zp2.write(180 - cur_femur); servo_zp3.write(180 - cur_tibia); }
    else if (leg_id == 3) { servo_pp2.write(180 - cur_femur); servo_pp3.write(180 - cur_tibia); }
    delay(SPEED_DELAY);
  }

  for (int f = 0; f <= 20; f++) {
    if (Serial.available() > 0) return;
    float t = (float)f / 20.0;
    
    if (leg_id == 0) { int start = servo_pl1.read(); servo_pl1.write(start + (target_coxa - start) * t); }
    else if (leg_id == 1) { int start = servo_zl1.read(); servo_zl1.write(start + (target_coxa - start) * t); }
    else if (leg_id == 2) { int start = 180 - servo_zp1.read(); int val = start + (target_coxa - start) * t; servo_zp1.write(180 - val); }
    else if (leg_id == 3) { int start = 180 - servo_pp1.read(); int val = start + (target_coxa - start) * t; servo_pp1.write(180 - val); }
    delay(SPEED_DELAY);
  }

  for (int f = 0; f <= 20; f++) {
    if (Serial.available() > 0) return;
    float t = (float)f / 20.0;
    int cur_femur = (HEIGHT - LIFT) + (LIFT * t);
    int cur_tibia = 100 - (10 * t);
    
         if (leg_id == 0) { servo_pl2.write(cur_femur); servo_pl3.write(cur_tibia); }
    else if (leg_id == 1) { servo_zl2.write(cur_femur); servo_zl3.write(cur_tibia); }
    else if (leg_id == 2) { servo_zp2.write(180 - cur_femur); servo_zp3.write(180 - cur_tibia); }
    else if (leg_id == 3) { servo_pp2.write(180 - cur_femur); servo_pp3.write(180 - cur_tibia); }
    delay(SPEED_DELAY);
  }
}


void swingLeg(int leg_id, int start_coxa, int end_coxa) {
  for (int f = 0; f <= 30; f++) {
    if (Serial.available() > 0) return;
    float t = (float)f / 30.0;
    
    int coxa = start_coxa + (end_coxa - start_coxa) * t;
    float parabola = 4.0 * t * (1.0 - t);
    int femur = HEIGHT - (LIFT * parabola);
    int tibia = 90 + (10 * parabola);

    if (leg_id == 0) { servo_pl1.write(coxa); servo_pl2.write(femur); servo_pl3.write(tibia); }
    else if (leg_id == 1) { servo_zl1.write(coxa); servo_zl2.write(femur); servo_zl3.write(tibia); }
    else if (leg_id == 2) { servo_zp1.write(180 - coxa); servo_zp2.write(180 - femur); servo_zp3.write(180 - tibia); }
    else if (leg_id == 3) { servo_pp1.write(180 - coxa); servo_pp2.write(180 - femur); servo_pp3.write(180 - tibia); }
    delay(SPEED_DELAY);
  }
}

void pushSidePair(bool active_is_right, int right_start, int right_end, int left_start, int left_end) {
  for (int f = 0; f <= 30; f++) {
    if (Serial.available() > 0) return;
    float t = (float)f / 30.0;
    int femur = HEIGHT;
    int tibia = 90;

    if (active_is_right) {
      int right_coxa = right_start + (right_end - right_start) * t;
      int left_coxa = left_start; 
      servo_zp1.write(180 - right_coxa); servo_zp2.write(180 - femur); servo_zp3.write(180 - tibia);
      servo_pp1.write(180 - right_coxa); servo_pp2.write(180 - femur); servo_pp3.write(180 - tibia);
      servo_zl1.write(left_coxa); servo_zl2.write(femur); servo_zl3.write(tibia);
      servo_pl1.write(left_coxa); servo_pl2.write(femur); servo_pl3.write(tibia);
    } else {
      int left_coxa = left_start + (left_end - left_start) * t;
      int right_coxa = right_start; 
      servo_zl1.write(left_coxa); servo_zl2.write(femur); servo_zl3.write(tibia);
      servo_pl1.write(left_coxa); servo_pl2.write(femur); servo_pl3.write(tibia);
      servo_zp1.write(180 - right_coxa); servo_zp2.write(180 - femur); servo_zp3.write(180 - tibia);
      servo_pp1.write(180 - right_coxa); servo_pp2.write(180 - femur); servo_pp3.write(180 - tibia);
    }
    delay(SPEED_DELAY);
  }
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == '9') {
      setAllTo90();
    }
    else if (cmd == 'x') {
      is_walking = false;
      current_direction = "stop";
      setAllTo90();
    } 
    else if (cmd == 'w') { is_walking = true; current_direction = "forward"; }
    else if (cmd == 's') { is_walking = true; current_direction = "backward"; }
    else if (cmd == 'a') { is_walking = true; current_direction = "left"; }
    else if (cmd == 'd') { is_walking = true; current_direction = "right"; }
  }

  if (is_walking) {
    if (current_direction == "forward") {
      swingLeg(2, 90 - SWING, 90 + SWING); if (!is_walking) return; // ZP
      swingLeg(3, 90 - SWING, 90 + SWING); if (!is_walking) return; // PP
      pushSidePair(true, 90 + SWING, 90 - SWING, 90 - SWING, 90 - SWING); if (!is_walking) return;

      swingLeg(1, 90 - SWING, 90 + SWING); if (!is_walking) return; // ZL
      swingLeg(0, 90 - SWING, 90 + SWING); if (!is_walking) return; // PL
      pushSidePair(false, 90 - SWING, 90 - SWING, 90 + SWING, 90 - SWING); if (!is_walking) return;
    } 
    else if (current_direction == "backward") {
      swingLeg(3, 90 + SWING, 90 - SWING); if (!is_walking) return; // PP
      swingLeg(2, 90 + SWING, 90 - SWING); if (!is_walking) return; // ZP
      pushSidePair(true, 90 - SWING, 90 + SWING, 90 + SWING, 90 + SWING); if (!is_walking) return;

      swingLeg(0, 90 + SWING, 90 - SWING); if (!is_walking) return; // PL
      swingLeg(1, 90 + SWING, 90 - SWINGP; if (!is_walking) return;
    else if (current_direction == "left") {
      swingLeg(2, 90 - SWING, 90 + SWING); if (!is_walking) return; // ZP
      swingLeg(3, 90 - SWING, 90 + SWING); if (!is_walking) return; // PP 
      pushSidePair(true,  90 + SWING, 90 - SWING, 90 - SWING, 90 - SWING); if (!is_walking) return; 
      swingLeg(1, 90 - SWING, 90 + SWING); if (!is_walking) return; // ZL (Задня ліва)
      swingLeg(0, 90 - SWING, 90 + SWING); if (!is_walking) return; // PL (Передня ліва)
      pushSidePair(false, 90 - SWING, 90 - SWING, 90 + SWING, 90 - SWING); if (!is_walking) return;
    }
    else if (current_direction == "right") {
      swingLeg(2, 90 + SWING, 90 - SWING); if (!is_walking) return; // ZP
      swingLeg(3, 90 + SWING, 90 - SWING); if (!is_walking) return; // PP
      pushSidePair(true,  90 - SWING, 90 + SWING, 90 + SWING, 90 + SWING); if (!is_walking) return;.

      swingLeg(1, 90 + SWING, 90 - SWING); if (!is_walking) return; // ZL
      swingLeg(0, 90 + SWING, 90 - SWING); if (!is_walking) return; // PL
      pushSidePair(false, 90 + SWING, 90 + SWING, 90 - SWING, 90 + SWING); if (!is_walking) return;
    }
    

  else {
    delay(50);
  }
  }
}