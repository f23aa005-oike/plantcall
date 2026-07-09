# localmonitor 環境構築・自動起動手順

本ドキュメントでは、ラズパイ3（Raspberry Pi 3）上で動作するバジル栽培用ローカル遠隔監視システム「localmonitor」の環境構築および自動起動の設定手順について説明します。

---

## 1. ディレクトリとファイルの配置

本プロジェクトでは、プログラムファイルはすべてプロジェクト内の `src/python/localmonitor` ディレクトリに生成されています。
完全オフライン環境のラズパイ3で動作させる際は、このフォルダ一式をラズパイのデスクトップ `~/Desktop/localmonitor` にコピーするか、あるいは任意の場所に配置して実行してください。

**構成ファイル一式:**
- `monitor.py`: データ収集・CSV保存・外部Webhook送信スクリプト
- `dashboard.py`: Streamlitによるリアルタイム監視Web UI
- `.env`: 環境変数（Discord / GAS のWebhook URL用）テンプレート

---

## 2. 依存ライブラリのインストール

Raspberry Pi OSの新しいバージョン（Debian 12 Bookworm以降など）では、PEP 668（外部管理パッケージ）の影響により、グローバルなPython環境に対して直接 `pip install` を行うとエラーが発生します。
そのため、**仮想環境 (venv)** を使用するか、システムパッケージとしてのインストールフラグを使用することを推奨します。

### 推奨: Python仮想環境 (venv) を使用する手順

`~/Desktop/localmonitor` ディレクトリに移動し、以下のコマンドを実行します。

```bash
# ディレクトリに移動
cd ~/Desktop/localmonitor

# 仮想環境 'venv' の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# 必要なライブラリのインストール
pip install --upgrade pip
pip install streamlit pandas pyserial python-dotenv requests
```

> [!NOTE]
> 完全オフラインの環境に導入する場合、事前にインターネット接続環境下で必要なライブラリをダウンロードしてUSBメモリ等で持ち込むか、一時的にラズパイをインターネットに接続して上記コマンドを実行してください。

---

## 3. udevルールによるUSBシリアルパーミッションの永続化

Arduino UNOをラズパイに接続すると、通常は `/dev/ttyACM0` などのデバイスファイルとして認識されますが、標準では一般ユーザーによる読み書き権限がありません。
ラズパイの起動時やUSBの抜き差し時に毎回 `sudo chmod 666 /dev/ttyACM0` を実行する手間を省くため、udevルールを設定して自動的に権限を付与します。

### 設定手順

1. **udevルールファイルの作成・編集**
   ターミナルで以下のコマンドを実行し、ルールファイルを作成します。
   ```bash
   sudo nano /etc/udev/rules.d/99-arduino.rules
   ```

2. **ルールの記述**
   ファイル内に以下の1行を記述し、保存（Ctrl+O -> Enter）して閉じます（Ctrl+X）。
   ```udev
   KERNEL=="ttyACM*", MODE="0666"
   ```
   *※これにより、Arduinoが `/dev/ttyACM0` や `/dev/ttyACM1` 等のいずれで認識されても、自動的にパーミッション `0666` (全ユーザー読み書き可能) が適用されます。*

3. **ルールの反映**
   記述したルールを即時に適用するために、以下のコマンドを実行します。
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```
   Arduinoを一度抜き差しすることで、自動的に `/dev/ttyACM0` の権限が `crw-rw-rw-` に変更されていることを `ls -l /dev/ttyACM0` で確認できます。

---

## 4. systemdによるサービス化と自動起動設定

データ収集スクリプト (`monitor.py`) とStreamlitダッシュボード (`dashboard.py`) をバックグラウンドで同時に起動し、ラズパイの電源がONになったら自動で開始、かつプロセスが異常終了した場合にも自動で再起動するように `systemd` を使用してサービス化します。

### ① データ収集スクリプトのサービス化

1. **サービスファイルの作成**
   ```bash
   sudo nano /etc/systemd/system/localmonitor-collector.service
   ```

2. **設定内容の記述**
   以下を記述します。（※ユーザー名 `plantcall` や、配置場所 `~/Desktop/localmonitor` または仮想環境のパスは適宜環境に合わせて変更してください）
   ```ini
   [Unit]
   Description=Localmonitor Serial Data Collector
   After=network.target

   [Service]
   Type=simple
   User=plantcall
   WorkingDirectory=/home/plantcall/Desktop/localmonitor
   ExecStart=/home/plantcall/Desktop/localmonitor/venv/bin/python /home/plantcall/Desktop/localmonitor/monitor.py
   Restart=always
   RestartSec=5
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

### ② Streamlitダッシュボードのサービス化

1. **サービスファイルの作成**
   ```bash
   sudo nano /etc/systemd/system/localmonitor-dashboard.service
   ```

2. **設定内容の記述**
   以下を記述します。
   ```ini
   [Unit]
   Description=Localmonitor Streamlit Dashboard
   After=localmonitor-collector.service

   [Service]
   Type=simple
   User=plantcall
   WorkingDirectory=/home/plantcall/Desktop/localmonitor
   ExecStart=/home/plantcall/Desktop/localmonitor/venv/bin/streamlit run /home/plantcall/Desktop/localmonitor/dashboard.py --server.port=8501 --server.address=0.0.0.0
   Restart=always
   RestartSec=5
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

### ③ サービスの有効化と起動

設定したサービスファイルを再読み込みし、自動起動を設定して実行します。

```bash
# systemd設定ファイルの再読み込み
sudo systemctl daemon-reload

# サービスの自動起動（有効化）
sudo systemctl enable localmonitor-collector.service
sudo systemctl enable localmonitor-dashboard.service

# サービスの即時起動
sudo systemctl start localmonitor-collector.service
sudo systemctl start localmonitor-dashboard.service
```

### ④ 動作状況・ログの確認

サービスが正常に稼働しているかを確認するには、以下のコマンドを使用します。

* **ステータス確認:**
  ```bash
  sudo systemctl status localmonitor-collector.service
  sudo systemctl status localmonitor-dashboard.service
  ```
* **ログ確認:**
  ```bash
  # データ収集のログをリアルタイムで追跡
  journalctl -u localmonitor-collector.service -f
  
  # ダッシュボードのログをリアルタイムで追跡
  journalctl -u localmonitor-dashboard.service -f
  ```

Streamlitダッシュボードは、同じローカルネットワーク内のPCやスマホのブラウザから `http://<ラズパイのIPアドレス>:8501` にアクセスすることでも確認できます。完全にオフラインで動作させる場合は、ラズパイ上のブラウザから `http://localhost:8501` でアクセス可能です。
