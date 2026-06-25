import os
import serial as pyserial_lib
import requests
import time
from dotenv import load_dotenv

# --- 【設定】 ---
load_dotenv() # .env ファイルから環境変数を読み込む

TARGET_PORT = '/dev/ttyACM0'  # 現在認識されているポート（ACM0 か ACM1）に合わせてください
TARGET_BAUD = 9600            

# .env からURLを取得（無ければ直書きのURLを予備で使用）
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL") or "https://discord.com/api/webhooks/1503584418554577109/8DLrXh09eSEdmCt0B1eeMxthnxWsAi10lU65Dr5Y9fL52Uy-bhYwAZ4pKqWSZ7az5uQl"
# --------------

def send_to_discord(message):
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
    print(f"--- 5大環境センサー観測システム起動: {TARGET_PORT} ---")
    try:
        arduino_con = pyserial_lib.Serial(port=TARGET_PORT, baudrate=TARGET_BAUD, timeout=1)
        time.sleep(2) # 接続安定待ち
        
        while True:
            if arduino_con.in_waiting > 0:
                msg = arduino_con.readline().decode('utf-8').strip()
                print(f"受信データ: {msg}")
                
                try:
                    data_list = msg.split(',')
                    # 純粋にデータが5つ揃っているときだけ処理する
                    if len(data_list) == 5:
                        temp = float(data_list[0])
                        hum  = float(data_list[1])
                        pres = float(data_list[2])
                        lux  = float(data_list[3])
                        soil_val = int(data_list[4])
                        
                        # 水分量のパーセンテージ計算（乾燥576 〜 湿潤271）
                        dry_val = 576
                        wet_val = 271
                        
                        if soil_val > dry_val:
                            soil_per = 0
                        elif soil_val < wet_val:
                            soil_per = 100
                        else:
                            soil_per = int((dry_val - soil_val) / (dry_val - wet_val) * 100)
                        
                        # 水分量に応じたコメント
                        if soil_per < 20:
                            status_comment = "❌ カラカラ！お水ちょうだい！"
                        elif soil_per < 40:
                            status_comment = "⚠️ ちょっと喉が渇いてきたかも"
                        else:
                            status_comment = "🟢 潤ってていい感じ！"

                        # Discord用メッセージ
                        discord_msg = (
                            f"🌱 **【バジル環境・土壌レポート】**\n"
                            f"🌡️ **温　度:** {temp:.1f} °C\n"
                            f"💧 **湿　度:** {hum:.1f} %\n"
                            f"🌀 **気　圧:** {pres:.1f} hPa\n"
                            f"☀️ **照　度:** {lux:.1f} Lux\n"
                            f"🪴 **土水分:** {soil_per} % ({status_comment})\n"
                            f"----------------------------"
                        )
                        
                        send_to_discord(discord_msg)
                        
                        # 通知の間隔（現在はテスト用に1分=60秒。本番運用は1800=30分や3600=1時間がおすすめ）
                        time.sleep(60)
                        
                except ValueError:
                    pass
                
    except Exception as e:
        print(f"❌ エラー発生: {e}")

if __name__ == "__main__":
    start_basil_monitor()