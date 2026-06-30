import os
import serial as pyserial_lib
import requests
import time
from dotenv import load_dotenv
import sqlite3
import datetime

# --- 【設定】 ---
load_dotenv()

TARGET_PORT = '/dev/ttyACM0'  
TARGET_BAUD = 9600            

# .env からそれぞれのURLを取得
DISCORD_URL = os.environ.get("DISCORD_WEBHOOK_URL")
GAS_URL = os.environ.get("GAS_WEBHOOK_URL")
# --------------

def send_to_discord(message):
    if not DISCORD_URL: return
    try:
        data = {"content": message}
        requests.post(DISCORD_URL, json=data)
        print("Discord送信成功")
    except Exception as e:
        print(f"Discordエラー: {e}")

# ★新機能：スプレッドシート（GAS）にデータを送信する関数
def send_to_spreadsheet(temp, hum, pres, lux, soil_per):
    if not GAS_URL:
        print("⚠️ GAS_URLが設定されていません")
        return
    try:
        # GASが受け取れるようにキー名を合わせてJSONデータを作成
        payload = {
            "temp": temp,
            "hum": hum,
            "pres": pres,
            "lux": lux,
            "soil": soil_per
        }
        # GASへ送信
        response = requests.post(GAS_URL, json=payload)
        if response.status_code == 200:
            print("スプレッドシート記録成功")
        else:
            print(f"スプレッドシート送信失敗: {response.status_code}")
    except Exception as e:
        print(f"スプレッドシートエラー: {e}")

# ★新機能：SQLiteデータベースにデータを保存する関数
def init_db():
    conn = sqlite3.connect('plant_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temperature REAL,
            humidity REAL,
            pressure REAL,
            lux REAL,
            soil_moisture INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def send_to_sqlite(temp, hum, pres, lux, soil_per):
    try:
        conn = sqlite3.connect('plant_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sensor_data (temperature, humidity, pressure, lux, soil_moisture)
            VALUES (?, ?, ?, ?, ?)
        ''', (temp, hum, pres, lux, soil_per))
        conn.commit()
        conn.close()
        print("SQLiteデータベース保存成功")
    except Exception as e:
        print(f"SQLiteエラー: {e}")

def start_basil_monitor():
    init_db()  # データベースの初期化
    print(f"--- 5大環境センサー W通知システム起動: {TARGET_PORT} ---")
    try:
        arduino_con = pyserial_lib.Serial(port=TARGET_PORT, baudrate=TARGET_BAUD, timeout=1)
        time.sleep(2)
        
        while True:
            if arduino_con.in_waiting > 0:
                msg = arduino_con.readline().decode('utf-8').strip()
                print(f"受信データ: {msg}")
                
                try:
                    data_list = msg.split(',')
                    if len(data_list) == 5:
                        # 🔴 シリアルモニタの並び順（0から順番）に完全に一致させます！
                        temp     = float(data_list[0])  # 1番目: 25.42
                        hum      = float(data_list[1])  # 2番目: 49.78
                        pres     = float(data_list[2])  # 3番目: 995.39
                        lux      = float(data_list[3])  # 4番目: 565.00
                        soil_val = int(data_list[4])    # 5番目: 524
                        
                        # 水分量のパーセンテージ計算（乾燥576 〜 湿潤271）
                        dry_val = 576
                        wet_val = 271
                        if soil_val > dry_val: soil_per = 0
                        elif soil_val < wet_val: soil_per = 100
                        else: soil_per = int((dry_val - soil_val) / (dry_val - wet_val) * 100)
                        
                        if soil_per < 20: status_comment = "❌ カラカラ！お水ちょうだい！"
                        elif soil_per < 40: status_comment = "⚠️ ちょっと喉が渇いてきたかも"
                        else: status_comment = "🟢 潤ってていい感じ！"

                        discord_msg = (
                            f"🌱 **【バジル環境・土壌レポート】**\n"
                            f"🌡️ **温 度:** {temp:.1f} °C\n"
                            f"💧 **湿 度:** {hum:.1f} %\n"
                            f"🌀 **気 圧:** {pres:.1f} hPa\n"
                            f"☀️ **照 度:** {lux:.1f} Lux\n"
                            f"🪴 **土水分:** {soil_per} % ({status_comment})\n"
                            f"----------------------------"
                        )
                        
                        # Discordとスプレッドシートの両方に送信！
                        send_to_discord(discord_msg)
                        send_to_spreadsheet(temp, hum, pres, lux, soil_per)
                        send_to_sqlite(temp, hum, pres, lux, soil_per)
                        
                        # 1分待機（テスト用）
                        time.sleep(1800)
                        
                except ValueError:
                    pass
                
    except Exception as e:
        print(f"❌ エラー発生: {e}")

if __name__ == "__main__":
    start_basil_monitor()