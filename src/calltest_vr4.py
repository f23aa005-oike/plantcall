import os
import serial as pyserial_lib
import requests
import time
from dotenv import load_dotenv  # ★ .envを読み込むためのライブラリ

# --- 【設定】 ---
# 同一フォルダ内にある .env ファイルから環境変数を読み込む
load_dotenv()

TARGET_PORT = '/dev/ttyACM0'  # 認識されているポート名に合わせてください(ACM0かACM1)
TARGET_BAUD = 9600            

# ★ os.environ.get で .env 内の URL を安全に取得
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
# --------------

def send_to_discord(message):
    # URLが正しく読み込めていない場合のガード
    if not WEBHOOK_URL:
        print("❌ エラー: .env ファイルから Webhook URL を読み込めませんでした。")
        return
        
    try:
        data = {"content": message}
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("Discord送信成功")
        else:
            print(f"Discord送信失敗: {response.status_code}")
    except Exception as e:
        print(f"ネットワークエラー: {e}")

def start_basil_monitor():
    print(f"--- スマート自動給水システム起動: {TARGET_PORT} ---")
    try:
        arduino_con = pyserial_lib.Serial(port=TARGET_PORT, baudrate=TARGET_BAUD, timeout=1)
        time.sleep(2)
        
        while True:
            if arduino_con.in_waiting > 0:
                msg = arduino_con.readline().decode('utf-8').strip()
                print(f"受信データ: {msg}")
                
                if msg == "PUMP_ON_TRIGGER":
                    send_to_discord("🚨 **【自動給水発動】** 土が乾いていたため、ポンプを3秒間作動させてバジルにお水をあげました！💧")
                    continue
                
                try:
                    data_list = msg.split(',')
                    if len(data_list) == 5:
                        temp = float(data_list[0])
                        hum  = float(data_list[1])
                        pres = float(data_list[2])
                        lux  = float(data_list[3])
                        soil_val = int(data_list[4])
                        
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
                        
                        send_to_discord(discord_msg)
                        time.sleep(60) 
                        
                except ValueError:
                    pass
                
    except Exception as e:
        print(f"❌ エラー発生: {e}")

if __name__ == "__main__":
    start_basil_monitor()