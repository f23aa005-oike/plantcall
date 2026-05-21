import serial as pyserial_lib
import requests
import time

# --- 【設定】 ---
TARGET_PORT = '/dev/ttyACM1'  # ポートがACM0の場合は戻してください
TARGET_BAUD = 9600            
WEBHOOK_URL = "https://discord.com/api/webhooks/1503584418554577109/8DLrXh09eSEdmCt0B1eeMxthnxWsAi10lU65Dr5Y9fL52Uy-bhYwAZ4pKqWSZ7az5uQl"
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
    print(f"--- 5大環境センサーモニタリング開始: {TARGET_PORT} ---")
    try:
        arduino_con = pyserial_lib.Serial(port=TARGET_PORT, baudrate=TARGET_BAUD, timeout=1)
        time.sleep(2)
        
        while True:
            if arduino_con.in_waiting > 0:
                msg = arduino_con.readline().decode('utf-8').strip()
                print(f"受信生データ: {msg}")
                
                try:
                    data_list = msg.split(',')
                    # データが5つ届いているかチェック
                    if len(data_list) == 5:
                        temp = float(data_list[0])
                        hum  = float(data_list[1])
                        pres = float(data_list[2])
                        lux  = float(data_list[3])
                        soil_val = int(data_list[4]) # ★土壌水分の生データ
                        
                        # 【水分量のパーセンテージ計算】
                        # 乾燥(576) 〜 湿潤(271) の範囲を 0% 〜 100% に変換する
                        # 計算式: (乾燥時の値 - 現在の値) / (乾燥時の値 - 湿潤時の値) * 100
                        dry_val = 576
                        wet_val = 271
                        
                        # 範囲外の数値が来ても 0%〜100% に収まるようにガードをかける
                        if soil_val > dry_val:
                            soil_per = 0
                        elif soil_val < wet_val:
                            soil_per = 100
                        else:
                            soil_per = int((dry_val - soil_val) / (dry_val - wet_val) * 100)
                        
                        # バジルの機嫌（コメント）を添える
                        if soil_per < 20:
                            status_comment = "❌ カラカラ！お水ちょうだい！"
                        elif soil_per < 40:
                            status_comment = "⚠️ ちょっと喉が渇いてきたかも"
                        else:
                            status_comment = "🟢 潤ってていい感じ！"

                        # Discord用のメッセージ作成
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
                        
                        # テスト用に1分（60秒）待機。安定したら1800（30分）や3600（1時間）に延ばしてください
                        time.sleep(1800)
                        
                except ValueError:
                    pass
                
    except Exception as e:
        print(f"❌ エラー発生: {e}")

if __name__ == "__main__":
    start_basil_monitor()