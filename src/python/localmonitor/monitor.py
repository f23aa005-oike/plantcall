#!/usr/bin/env python3
import os
import csv
from datetime import datetime
import time
import serial
from dotenv import load_dotenv
import requests

# スクリプトの配置ディレクトリをカレントディレクトリに設定
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)

# .envファイルの読み込み
load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GAS_WEBHOOK_URL = os.getenv("GAS_WEBHOOK_URL")

CSV_FILE = "basil_data.csv"
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600

def convert_soil_moisture(raw_value):
    """
    土壌水分の生データ（乾燥576 〜 湿潤271）を 0% 〜 100% のパーセンテージに変換
    """
    try:
        raw_val = float(raw_value)
        # 乾燥576のときに0%、湿潤271のときに100%とする変換式
        percentage = ((576.0 - raw_val) / (576.0 - 271.0)) * 100.0
        # 0%から100%の範囲に収める
        percentage = max(0.0, min(100.0, percentage))
        return round(percentage, 2)
    except ValueError:
        return 0.0

def save_to_csv(data_dict):
    """
    測定データをCSVファイルに追記保存する。ファイルが存在しない場合はヘッダーを作成。
    """
    file_exists = os.path.isfile(CSV_FILE)
    headers = ["Datetime", "Temperature", "Humidity", "Pressure", "Illuminance", "SoilMoistureRaw", "SoilMoisturePercent"]
    
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data_dict)

def send_to_discord(timestamp, temp, hum, press, lux, raw_soil, pct_soil):
    """
    Discord Webhookへデータを送信する。オフライン時はエラーを握りつぶして沈黙する。
    """
    if not DISCORD_WEBHOOK_URL or not DISCORD_WEBHOOK_URL.strip():
        return
    
    payload = {
        "embeds": [{
            "title": "🌿 バジル栽培モニター 測定データ",
            "color": 3066993,  # 緑色 (Emerald Green)
            "fields": [
                {"name": "測定日時", "value": timestamp, "inline": False},
                {"name": "温度", "value": f"{temp} ℃", "inline": True},
                {"name": "湿度", "value": f"{hum} %", "inline": True},
                {"name": "気圧", "value": f"{press} hPa", "inline": True},
                {"name": "照度", "value": f"{lux} lx", "inline": True},
                {"name": "土壌水分", "value": f"{pct_soil} % (生値: {raw_soil})", "inline": True}
            ]
        }]
    }
    
    try:
        # タイムアウトを短めに設定（オフライン環境で待機が発生するのを防ぐため）
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        # インターネット未接続・接続エラー時は例外をキャッチして無視（沈黙）
        pass

def send_to_gas(timestamp, temp, hum, press, lux, raw_soil, pct_soil):
    """
    Google Apps Script (GAS) Webhookへデータ送信。オフライン時は例外を握りつぶして沈黙する。
    """
    if not GAS_WEBHOOK_URL or not GAS_WEBHOOK_URL.strip():
        return
    
    payload = {
        "datetime": timestamp,
        "temperature": temp,
        "humidity": hum,
        "pressure": press,
        "illuminance": lux,
        "soil_moisture_raw": raw_soil,
        "soil_moisture_percent": pct_soil
    }
    
    try:
        # タイムアウトを短めに設定
        requests.post(GAS_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        # インターネット未接続・接続エラー時は例外をキャッチして無視（沈黙）
        pass

def main():
    print(f"Starting localmonitor collector on {SERIAL_PORT}...")
    
    while True:
        try:
            # シリアル通信の初期化
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=10) as ser:
                print(f"Connected to {SERIAL_PORT} successfully.")
                
                # シリアルバッファのクリア
                ser.reset_input_buffer()
                
                while True:
                    # 1行読み込み
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                    
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Received raw data: {line}")
                    
                    # データの分割 (温度,湿度,気圧,照度,土壌水分生データ)
                    parts = line.split(',')
                    if len(parts) != 5:
                        print(f"Warning: Invalid format (expected 5 items, got {len(parts)}): {line}")
                        continue
                    
                    try:
                        temp = float(parts[0])
                        hum = float(parts[1])
                        press = float(parts[2])
                        lux = float(parts[3])
                        raw_soil = float(parts[4])
                    except ValueError as e:
                        print(f"Warning: Failed to parse float values: {e}")
                        continue
                    
                    # 土壌水分のパーセンテージ変換
                    pct_soil = convert_soil_moisture(raw_soil)
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # CSVデータ構築
                    data_dict = {
                        "Datetime": timestamp,
                        "Temperature": temp,
                        "Humidity": hum,
                        "Pressure": press,
                        "Illuminance": lux,
                        "SoilMoistureRaw": raw_soil,
                        "SoilMoisturePercent": pct_soil
                    }
                    
                    # ローカルCSVへの保存
                    try:
                        save_to_csv(data_dict)
                    except Exception as e:
                        print(f"Error saving to CSV: {e}")
                    
                    # 外部サービスへのデータ転送 (エラー時は自動でスキップされる)
                    send_to_discord(timestamp, temp, hum, press, lux, raw_soil, pct_soil)
                    send_to_gas(timestamp, temp, hum, press, lux, raw_soil, pct_soil)
                    
        except serial.SerialException as e:
            print(f"Serial connection error: {e}. Reconnecting in 10 seconds...")
            time.sleep(10)
        except Exception as e:
            print(f"Unexpected system error: {e}. Restarting loop in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    main()
