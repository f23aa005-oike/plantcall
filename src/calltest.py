import serial as pyserial_lib # 名前を被らないようにインポート
import requests
import time

# ポート名を直接指定
target_port = '/dev/ttyACM0' 
target_baud = 9600

def start_process():
    print(f"--- 接続テスト開始: {target_port} ---")
    try:
        # 変数名を 'ser' ではなく 'arduino_con' に変更
        arduino_con = pyserial_lib.Serial(port=target_port, baudrate=target_baud, timeout=1)
        
        if arduino_con.is_open:
            print("無事にポートが開きました！")
            
        while True:
            if arduino_con.in_waiting > 0:
                msg = arduino_con.readline().decode('utf-8').strip()
                print(f"受信したバジルの声: {msg}")
                
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        # ここでエラーの型を表示させる
        print(f"エラーの種類: {type(e)}")

if __name__ == "__main__":
    start_process()