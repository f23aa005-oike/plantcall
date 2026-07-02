import os
import sys
import time
import serial as pyserial_lib
import requests
import sqlite3
import threading
from queue import Queue
from datetime import datetime
from dotenv import load_dotenv

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

load_dotenv()
TARGET_PORT = '/dev/ttyACM1'  
TARGET_BAUD = 9600            
DB_NAME = "basil_data.db"

DISCORD_URL = os.environ.get("DISCORD_WEBHOOK_URL")
GAS_URL = os.environ.get("GAS_WEBHOOK_URL")

data_queue = Queue(maxsize=100)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_logs (
            timestamp TEXT PRIMARY KEY,
            temperature REAL,
            humidity REAL,
            pressure REAL,
            lux REAL,
            soil_moisture INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def send_to_discord(message):
    if not DISCORD_URL: return
    try: requests.post(DISCORD_URL, json={"content": message})
    except Exception as e: print(f"Discordエラー: {e}")

def send_to_spreadsheet(temp, hum, pres, lux, soil_per):
    if not GAS_URL: return
    try:
        payload = {"temp": temp, "hum": hum, "pres": pres, "lux": lux, "soil": soil_per}
        requests.post(GAS_URL, json=payload)
    except Exception as e: print(f"スプレッドシートエラー: {e}")

def save_to_db(temp, hum, pres, lux, soil_per):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT OR REPLACE INTO sensor_logs VALUES (?, ?, ?, ?, ?, ?)
        ''', (now_str, temp, hum, pres, lux, soil_per))
        conn.commit()
        conn.close()
    except Exception as e: print(f"DB保存エラー: {e}")

def serial_reader_thread():
    print(f"シリアル読込スレッド開始: {TARGET_PORT}")
    last_network_send = 0
    while True:
        try:
            arduino_con = pyserial_lib.Serial(port=TARGET_PORT, baudrate=TARGET_BAUD, timeout=1)
            time.sleep(2)
            while True:
                if arduino_con.in_waiting > 0:
                    msg = arduino_con.readline().decode('utf-8').strip()
                    data_list = msg.split(',')
                    if len(data_list) == 5:
                        temp = float(data_list[0])
                        hum  = float(data_list[1])
                        pres = float(data_list[2])
                        lux  = float(data_list[3])
                        soil_val = int(data_list[4])
                        
                        dry_val, wet_val = 576, 271
                        if soil_val > dry_val: soil_per = 0
                        elif soil_val < wet_val: soil_per = 100
                        else: soil_per = int((dry_val - soil_val) / (dry_val - wet_val) * 100)
                        
                        if not data_queue.full():
                            data_queue.put((temp, hum, pres, lux, soil_per))
                        
                        current_time = time.time()
                        if current_time - last_network_send >= 60:
                            save_to_db(temp, hum, pres, lux, soil_per)
                            status = "❌ カラカラ！" if soil_per < 20 else "⚠️ 渇き気味" if soil_per < 40 else "🟢 潤い良好"
                            discord_msg = f"🌱 **【バジル環境レポート】**\n🌡️ 温度: {temp:.1f}°C / 💧 湿度: {hum:.1f}% / 🪴 土水分: {soil_per}% ({status})"
                            send_to_discord(discord_msg)
                            send_to_spreadsheet(temp, hum, pres, lux, soil_per)
                            last_network_send = current_time
                time.sleep(0.1)
        except Exception as e:
            print(f"シリアルエラー(再接続を試みます): {e}")
            time.sleep(5)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌱 Basil Smart Monitor")
        self.resize(1000, 600)
        self.max_points = 100
        self.temp_data = []
        self.soil_data = []
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("データ受信待機中...")
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #003057; padding: 10px;")
        main_layout.addWidget(self.status_label)
        
        graph_layout = QHBoxLayout()
        main_layout.addLayout(graph_layout)
        
        self.temp_plot = pg.PlotWidget(title="🌡️ 温度推移 (°C)")
        self.temp_plot.setBackground('w')
        self.temp_curve = self.temp_plot.plot(pen=pg.mkPen('r', width=2))
        graph_layout.addWidget(self.temp_plot)
        
        self.soil_plot = pg.PlotWidget(title="🪴 土壌水分推移 (%)")
        self.soil_plot.setBackground('w')
        self.soil_curve = self.soil_plot.plot(pen=pg.mkPen('b', width=2))
        graph_layout.addWidget(self.soil_plot)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(500)

    def update_plots(self):
        while not data_queue.empty():
            temp, hum, pres, lux, soil_per = data_queue.get()
            self.status_label.setText(
                f"【リアルタイム現在値】 🌡️ 温度: {temp:.1f} °C  |  💧 湿度: {hum:.1f} %  |  ☀️ 照度: {lux:.1f} Lux  |  🪴 土水分: {soil_per} %"
            )
            self.temp_data.append(temp)
            self.soil_data.append(soil_per)
            if len(self.temp_data) > self.max_points:
                self.temp_data.pop(0)
                self.soil_data.pop(0)
        if self.temp_data:
            self.temp_curve.setData(self.temp_data)
            self.soil_curve.setData(self.soil_data)

if __name__ == "__main__":
    init_db()
    reader_t = threading.Thread(target=serial_reader_thread, daemon=True)
    reader_t.start()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
