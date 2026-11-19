#include "BluetoothSerial.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled!
#endif

BluetoothSerial ESP_BT;

void setup() {
  Serial.begin(9600); 
  ESP_BT.begin("Quadropod_Robot_BT");
  Serial.println("Bluetooth запуск: пристрій готовий.");
}

void loop() {
  if (ESP_BT.available()) {
    char incoming = ESP_BT.read();
    
    // Фільтруємо і передаємо на Arduino ТІЛЬКИ значущі символи команд
    if (incoming == 'w' || incoming == 's' || incoming == 'a' || 
        incoming == 'd' || incoming == 'x' || incoming == '9' || incoming == '0') {
      
      Serial.print(incoming); // Шлемо чистий символ на Arduino
    }
  }
}