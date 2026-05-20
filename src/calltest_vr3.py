import serial as pyserial_lib
import requests
import time

# --- 【設定】 ---
TARGET_PORT = '/dev/ttyACM0'  
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
    print(f"--- 4大環境センサーモニタリング開始: {TARGET_PORT} ---")
    try:
        arduino_con = pyserial_lib.Serial(port=TARGET_PORT, baudrate=TARGET_BAUD, timeout=1)
        time.sleep(2)  # 接続安定待ち
        
        while True:
            if arduino_con.in_waiting > 0:
                # Arduinoからの1行（temp,hum,pres,lux）を読み込む
                msg = arduino_con.readline().decode('utf-8').strip()
                print(f"受信生データ: {msg}")
                
                try:
                    # カンマで分割してそれぞれの数値に変換
                    data_list = msg.split(',')
                    if len(data_list) == 4:
                        temp = float(data_list[0])
                        hum  = float(data_list[1])
                        pres = float(data_list[2])
                        lux  = float(data_list[3])
                        
                        # Discord用のメッセージを作成
                        discord_msg = (
                            f"🌱 **【バジル栽培環境レポート】**\n"
                            f"🌡️ **温　度:** {temp:.1f} °C\n"
                            f"💧 **湿　度:** {hum:.1f} %\n"
                            f"🌀 **気　圧:** {pres:.1f} hPa\n"
                            f"☀️ **照　度:** {lux:.1f} Lux\n"
                            f"----------------------------"
                        )
                        
                        # Discordへ送信
                        send_to_discord(discord_msg)
                        
                        # 通知が爆発しないように、次の送信まで1分待機（テストが終わったら3600=1時間等に延ばすと快適です）
                        time.sleep(60)
                        
                except ValueError:
                    # エラーメッセージなどの文字列が混ざった場合はスルー
                    pass
                
    except Exception as e:
        print(f"❌ エラー発生: {e}")

if __name__ == "__main__":
    start_basil_monitor()