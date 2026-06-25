#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <BH1750.h>

struct Adafruit_BME280 bme; 
BH1750 lightMeter;

const int SOIL_PIN = A0; // 土壌センサーのピン

void setup() {
  Serial.begin(9600);
  Wire.begin();

  if (!bme.begin(0x77)) {
    Serial.println("Could not find a valid BME280 sensor, check wiring!");
    while (1);
  }

  if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("Could not find a valid BH1750 sensor, check wiring!");
    while (1);
  }
}

void loop() {
  float temp = bme.readTemperature();
  float hum  = bme.readHumidity();
  float pres = bme.readPressure() / 100.0F;
  float lux  = lightMeter.readLightLevel();
  int soil   = analogRead(SOIL_PIN); // ★土壌水分の値を読み取る

  // カンマ区切りで5つのデータを送信
  // 例: 24.5,55.2,1013.2,450.0,350
  Serial.print(temp);   Serial.print(",");
  Serial.print(hum);    Serial.print(",");
  Serial.print(pres);   Serial.print(",");
  Serial.print(lux);    Serial.print(",");
  Serial.println(soil); // ★最後に土壌水分の数値を送信

  delay(5000); 
}