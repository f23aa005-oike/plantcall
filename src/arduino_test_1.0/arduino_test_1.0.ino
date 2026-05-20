#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <BH1750.h>

Adafruit_BME280 bme; // BME280オブジェクト
BH1750 lightMeter;   // GY-30 (BH1750) オブジェクト

void setup() {
  Serial.begin(9600);
  Wire.begin();

  // BME280の初期化 (I2Cアドレスが0x76の場合が多いですが、ダメなら0x77に変更)
  if (!bme.begin(0x76)) {
    Serial.println("Could not find a valid BME280 sensor, check wiring!");
    while (1);
  }

  // GY-30 (BH1750) の初期化
  if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("Could not find a valid BH1750 sensor, check wiring!");
    while (1);
  }
}

void loop() {
  // 各センサーから値を読み込む
  float temp = bme.readTemperature();    // 温度 (°C)
  float hum  = bme.readHumidity();       // 湿度 (%)
  float pres = bme.readPressure() / 100.0F; // 気圧 (hPa)
  float lux  = lightMeter.readLightLevel(); // 照度 (Lux)

  // ラズパイが読みやすいように カンマ区切り で1行で送信
  // 例: 24.5,55.2,1013.2,450.0
  Serial.print(temp);   Serial.print(",");
  Serial.print(hum);    Serial.print(",");
  Serial.print(pres);   Serial.print(",");
  Serial.println(lux);

  delay(5000); // 5秒ごとに測定
}