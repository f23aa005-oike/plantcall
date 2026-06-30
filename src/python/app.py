from flask import Flask, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)

# DBファイルのパス。ルートディレクトリから実行されることを想定
DB_PATH = 'plant_data.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    if not os.path.exists(DB_PATH):
        return jsonify([]) # DBが存在しない場合は空配列を返す

    conn = get_db_connection()
    # 最新の100件のデータを取得 (古い順に並び替えるためにサブクエリを使用)
    data = conn.execute('''
        SELECT * FROM (
            SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 100
        ) ORDER BY timestamp ASC
    ''').fetchall()
    conn.close()
    
    # 辞書のリストに変換
    result = [dict(row) for row in data]
    return jsonify(result)

if __name__ == '__main__':
    # すべてのネットワークインターフェースからアクセス可能にする (ローカルネットワーク用)
    app.run(host='0.0.0.0', port=5000, debug=True)
