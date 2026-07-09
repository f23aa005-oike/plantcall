# Pull Request

## タイトル
`feat: スマート農業用ローカル監視システム「localmonitor」の追加と構築手順の整備`

---

## 概要
ラズパイ3（Raspberry Pi 3）上で完全オフラインで動作するバジル栽培用のローカル遠隔監視システム「localmonitor」を構築するためのスクリプト、設定ファイル一式、および構築・自動起動手順書を追加しました。

---

## 変更内容

### 1. 新規プログラム・設定ファイルの追加
- **[monitor.py](file:///home/plantcall/Desktop/plantcall/src/python/localmonitor/monitor.py)** (データ収集・CSV保存・外部連携スクリプト)
  - `/dev/ttyACM0` から USB シリアルデータ（温度,湿度,気圧,照度,土壌水分生データ）を毎分受信。
  - 土壌水分の生データ（乾燥576〜湿潤271）を 0% 〜 100% の値にスケーリング変換して保存。
  - `basil_data.csv` に日時（`YYYY-MM-DD HH:MM:SS`）付きで追記保存。
  - `.env` から Webhook URL を読み込み、存在する場合のみ送信。ネットワーク未接続やタイムアウトなどのエラー発生時は例外をすべてキャッチし、送信をスキップ（完全沈黙）してローカル保存を継続します。
  - USBの抜き差し等による一時的な切断に対処するための自動再接続ループを実装。
- **[dashboard.py](file:///home/plantcall/Desktop/plantcall/src/python/localmonitor/dashboard.py)** (StreamlitによるグラフUI画面)
  - 5秒ごとに `basil_data.csv` を自動ロードし、画面をリアルタイム更新。
  - `st.metric` を使用し、最上部に最新の「温度」「湿度」「気圧」「照度」「土壌水分%」を大きく表示。
  - 左右2カラムに分け、左に「温度・湿度・土水分（折れ線グラフ）」、右に「気圧（折れ線グラフ）」を配置。
  - 下部に「照度推移（面グラフ）」を表示。
  - 最下部に「直近20件のデータ履歴テーブル」を表示（最新データが一番上になるようリバース表示）。
  - ラズパイ3のハードウェア負荷を抑えるため、描画するグラフデータを直近100件に限定。
- **[.env](file:///home/plantcall/Desktop/plantcall/src/python/localmonitor/.env)** (環境変数のダミーテンプレート)
  - Discord Webhook URL と GAS Webhook URL を記述するためのテンプレート。
- **[setup.sh](file:///home/plantcall/Desktop/plantcall/src/python/localmonitor/setup.sh)** (自動セットアップスクリプト)
  - 仮想環境の構築、udevルールの作成、systemdサービスの設定を自動で行うBashスクリプトを追加。

### 2. ドキュメントの整備
- **[localmonitor_setup.md](file:///home/plantcall/Desktop/plantcall/docs/localmonitor_setup.md)** (環境構築・自動起動手順)
  - PEP 668対策を踏まえた Python 仮想環境（venv）でのライブラリインストール手順。
  - USBの抜き差し時にパーミッションエラーを防止するための `udevルール`（`/etc/udev/rules.d/99-arduino.rules`）の設定手順。
  - データ収集スクリプトとStreamlitダッシュボードをバックグラウンドで同時起動・常時稼働させるための `systemd` によるサービス化と自動起動の手順。

### 3. その他
- **[.gitignore](file:///home/plantcall/Desktop/plantcall/.gitignore)**
  - リポジトリに不要な Python キャッシュ（`__pycache__/`、`*.pyc`）が含まれないよう除外設定を追加。

---

## 理由
- **完全オフライン動作の堅牢性確保**: インターネット未接続環境では、Webhookの送信処理でエラーが発生しプログラムがクラッシュする恐れがあるため、例外を完全にハンドリングして沈黙（自動スキップ）させる設計にしました。
- **ラズパイ3のパフォーマンス維持**: ラズパイ3の限られた処理能力でもカクつかずにリアルタイム監視Web UIを表示できるよう、Streamlitで描画するデータ量を制限する最適化を施しました。
- **運用の効率化**: udevルールによるデバイスファイルの権限永続化や、systemdによるサービス化を行うことで、運用の手間と起動ミスのリスクを最小限に抑えるためです。

---

## 確認したこと
- `python3 -m py_compile` を使用して、新規作成した python スクリプト（`monitor.py`, `dashboard.py`）に構文エラーがないことを確認。
- `__pycache__` などのコンパイル済みファイルが git コミット対象外になっていることを確認。

---

## 注意点
- **ファイルの配置場所**:
  - セキュリティ規則上、リポジトリ外への直接ファイル配置を行わずに `src/python/localmonitor/` 内に一式を配置しています。
  - 実機にデプロイする際は、このフォルダ一式を `~/Desktop/localmonitor` にコピーした上で、手順書に沿ってセットアップを行ってください。
