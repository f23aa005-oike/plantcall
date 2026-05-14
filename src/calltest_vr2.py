import serial as pyserial_lib
import requests
import time

# --- 【設定：ここを自分の環境に合わせて書き換える】 ---
TARGET_PORT = '/dev/ttyACM0'  # 確認したポート名
TARGET_BAUD = 9600            # Arduino側と合わせる
WEBHOOK_URL = "https://discord.com/api/webhooks/1503584418554577109/8DLrXh09eSEdmCt0B1eeMxthnxWsAi10lU65Dr5Y9fL52Uy-bhYwAZ4pKqWSZ7az5uQl"
# --------------------------------------------------

def send_to_discord(message):
    """Discordにメッセージを送信する関数"""
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
    print(f"--- 接続テスト開始: {TARGET_PORT} ---")
    try:
        # シリアル接続の確立
        arduino_con = pyserial_lib.Serial(port=TARGET_PORT, baudrate=TARGET_BAUD, timeout=1)
        time.sleep(2)  # 接続直後の不安定な時間を待つ
        
        print("モニタリング中...（Ctrl+C で終了）")
        
        while True:
            if arduino_con.in_waiting > 0:
                # Arduinoからのデータを一行読み込む
                msg = arduino_con.readline().decode('utf-8').strip()
                print(f"受信データ: {msg}")
                
                # --- ここでデータの判定と送信 ---
                try:
                    val = int(msg)
                    if val < 300: # 閾値はセンサーに合わせて調整してください
                        send_to_discord(f"🌱【緊急】バジル「お水が足りないよ！(値:{val})」")
                        # 一度送ったら1時間は送らない（通知が鳴り止まなくなるのを防ぐ）
                        time.sleep(3600) 
                except ValueError:
                    # 数値以外（起動メッセージなど）は無視する
                    pass
                
    except Exception as e:
        print(f"❌ エラー発生: {e}")

if __name__ == "__main__":
    start_basil_monitor()