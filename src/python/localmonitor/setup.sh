#!/bin/bash
# localmonitor - 自動セットアップスクリプト
# このスクリプトは、monitor.py や dashboard.py があるディレクトリで実行してください。

set -e

# 色の設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== localmonitor 自動セットアップスクリプト ===${NC}"

# 実行ユーザーとカレントディレクトリの取得
USER_NAME=$(whoami)
CURRENT_DIR=$(pwd)

echo -e "実行ユーザー: ${GREEN}${USER_NAME}${NC}"
echo -e "セットアップ対象ディレクトリ: ${GREEN}${CURRENT_DIR}${NC}"

# 必要ファイルの存在チェック
REQUIRED_FILES=("monitor.py" "dashboard.py" ".env")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}エラー: $file が現在のディレクトリに見つかりません。${NC}"
        echo "このスクリプトは、monitor.py や dashboard.py が配置されているディレクトリで実行してください。"
        exit 1
    fi
done

# 1. Python仮想環境 (venv) の構築
echo -e "\n${BLUE}[1/4] Python仮想環境 (venv) を構築しています...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "仮想環境 'venv' を新規作成しました。"
else
    echo "仮想環境 'venv' は既に存在します。"
fi

# 仮想環境のアクティベートとパッケージインストール
source venv/bin/activate
echo "依存パッケージをインストール中..."
# 完全オフライン環境等で pip が失敗した場合でもセットアップ自体を中断しないようにする
if pip install --upgrade pip; then
    if pip install streamlit pandas pyserial python-dotenv requests; then
        echo -e "${GREEN}ライブラリのインストールが完了しました。${NC}"
    else
        echo -e "${YELLOW}警告: ライブラリのインストールに失敗しました。オフライン環境の場合は手動でパッケージをインストールしてください。${NC}"
    fi
else
    echo -e "${YELLOW}警告: pipのアップグレードに失敗しました。オフライン環境の場合は手動でパッケージをインストールしてください。${NC}"
fi
deactivate

# 2. udevルールの設定
echo -e "\n${BLUE}[2/4] USBシリアル (udevルール) の設定を行っています...${NC}"
UDEV_RULE_PATH="/etc/udev/rules.d/99-arduino.rules"
UDEV_RULE='KERNEL=="ttyACM*", MODE="0666"'

echo "udevルールファイルを作成します: $UDEV_RULE_PATH"
# sudoを使って書き込む
echo "$UDEV_RULE" | sudo tee "$UDEV_RULE_PATH" > /dev/null

echo "udevルールをシステムに反映しています..."
sudo udevadm control --reload-rules
sudo udevadm trigger
echo -e "${GREEN}udevルールの設定が完了しました。${NC}"

# 3. systemdサービスファイルの生成と登録
echo -e "\n${BLUE}[3/4] systemd サービスファイルを生成しています...${NC}"

COLLECTOR_SERVICE_PATH="/etc/systemd/system/localmonitor-collector.service"
DASHBOARD_SERVICE_PATH="/etc/systemd/system/localmonitor-dashboard.service"

# Collectorサービスの作成
echo "作成中: $COLLECTOR_SERVICE_PATH"
cat <<EOF | sudo tee "$COLLECTOR_SERVICE_PATH" > /dev/null
[Unit]
Description=Localmonitor Serial Data Collector
After=network.target

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${CURRENT_DIR}
ExecStart=${CURRENT_DIR}/venv/bin/python ${CURRENT_DIR}/monitor.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Dashboardサービスの作成
echo "作成中: $DASHBOARD_SERVICE_PATH"
cat <<EOF | sudo tee "$DASHBOARD_SERVICE_PATH" > /dev/null
[Unit]
Description=Localmonitor Streamlit Dashboard
After=localmonitor-collector.service

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${CURRENT_DIR}
ExecStart=${CURRENT_DIR}/venv/bin/streamlit run ${CURRENT_DIR}/dashboard.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# systemdの再読み込み
sudo systemctl daemon-reload
echo -e "${GREEN}systemdサービス定義の作成が完了しました。${NC}"

# 4. サービスの有効化と起動
echo -e "\n${BLUE}[4/4] サービスを有効化し、起動しています...${NC}"

# Collector
sudo systemctl enable localmonitor-collector.service
sudo systemctl start localmonitor-collector.service
echo "Collectorサービスを自動起動有効化および起動しました。"

# Dashboard
sudo systemctl enable localmonitor-dashboard.service
sudo systemctl start localmonitor-dashboard.service
echo "Dashboardサービスを自動起動有効化および起動しました。"

echo -e "\n${GREEN}=== セットアップが正常に完了しました！ ===${NC}"
echo -e "・Streamlit UI: http://localhost:8501 (または http://<ラズパイのIPアドレス>:8501)"
echo -e "・データ収集ログ確認: sudo journalctl -u localmonitor-collector.service -f"
echo -e "・UIログ確認: sudo journalctl -u localmonitor-dashboard.service -f"
