#include <Adafruit_NeoPixel.h>

#define LED_PIN       6  // WS2812BのDIN（データ線）を繋ぐピン
#define NUMPIXELS   144  // ★LEDの個数を144個に設定しました

// NeoPixelオブジェクトの宣言
Adafruit_NeoPixel pixels(NUMPIXELS, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(9600);
  pixels.begin(); // NeoPixelの初期化
  pixels.clear();
  
  // 起動時に赤と青を交互に点灯
  setAlternatingColor();
}

void loop() {
  // A0に繋いだ土壌湿度センサーの値を読み取る
  int sensorValue = analogRead(A0);
  
  // ラズパイ（Python）へデータを送信
  Serial.println(sensorValue);

  // 2秒ごとにLEDの状態をリフレッシュ（常時交互点灯をキープ）
  setAlternatingColor();

  delay(2000); 
}

// 144個のLEDを赤と青、互い違いに光らせる関数
void setAlternatingColor() {
  for(int i = 0; i < NUMPIXELS; i++) {
    if (i % 2 == 0) {
      // 偶数番目：赤色 (R=150, G=0, B=0)
      pixels.setPixelColor(i, pixels.Color(150, 0, 0));
    } else {
      // 奇数番目：青色 (R=0, G=0, B=150)
      pixels.setPixelColor(i, pixels.Color(0, 0, 150));
    }
  }
  pixels.show(); // 144個すべてのLEDに色を反映
}