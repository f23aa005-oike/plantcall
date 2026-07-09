import streamlit as st
import pandas as pd
import time
import os

# ページ全体のレイアウト設定 (ワイド表示)
st.set_page_config(
    page_title="🌱 バジル栽培 遠隔監視システム",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSSでデザインを少しプレミアムにする
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #10B981; /* 緑系のアクセント */
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1.0rem;
        color: #9CA3AF;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌱 バジル栽培 遠隔監視システム (localmonitor)")
st.caption("ラズパイ3上で動作中 - 完全オフライン対応ローカルダッシュボード")

# CSVファイルの相対パス解決
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "basil_data.csv")

def load_data():
    """
    CSVファイルを読み込む。ファイルが存在しない場合や空の場合はNoneを返す。
    破損行を安全に読み飛ばすための設定も行う。
    """
    if not os.path.exists(CSV_FILE):
        return None
    try:
        df = pd.read_csv(CSV_FILE, on_bad_lines='skip')
        return df
    except Exception:
        return None

# リアルタイム表示を自動更新するためのコンテナ
placeholder = st.empty()

while True:
    df = load_data()
    
    with placeholder.container():
        if df is None or df.empty:
            st.warning(f"データファイル ({CSV_FILE}) が見つからないか、データが空です。センサーのデータ受信をお待ちください...")
        else:
            # 最新の測定データ
            latest = df.iloc[-1]
            
            # 1. 最上部に最新のメトリクスを st.metric で横並びにする
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("温度 (Temperature)", f"{latest['Temperature']} ℃")
            col2.metric("湿度 (Humidity)", f"{latest['Humidity']} %")
            col3.metric("気圧 (Pressure)", f"{latest['Pressure']} hPa")
            col4.metric("照度 (Illuminance)", f"{latest['Illuminance']} lx")
            col5.metric("土壌水分 (Soil Moisture)", f"{latest['SoilMoisturePercent']} %")
            
            st.write("---")
            
            # ラズパイの描画負荷を大幅に軽減するため、グラフ描画用のデータは直近100件に限定する
            chart_df = df.tail(100).copy()
            
            # 2. 左右カラムに分ける
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("📈 温度・湿度・土壌水分 推移（直近100件）")
                # 折れ線グラフ用にインデックスを日時に設定
                chart_data_left = chart_df.set_index("Datetime")[["Temperature", "Humidity", "SoilMoisturePercent"]]
                chart_data_left.columns = ["温度 (℃)", "湿度 (%)", "土壌水分 (%)"]
                st.line_chart(chart_data_left)
                
            with col_right:
                st.subheader("📉 気圧 推移（直近100件）")
                chart_data_right = chart_df.set_index("Datetime")[["Pressure"]]
                chart_data_right.columns = ["気圧 (hPa)"]
                st.line_chart(chart_data_right)
            
            st.write("---")
            
            # 3. 下部に「照度」の推移を面グラフ（st.area_chart）で表示
            st.subheader("☀️ 照度 推移 (直近100件・面グラフ)")
            chart_data_light = chart_df.set_index("Datetime")[["Illuminance"]]
            chart_data_light.columns = ["照度 (lx)"]
            st.area_chart(chart_data_light)
            
            st.write("---")
            
            # 4. 最下部に直近20件のデータ履歴テーブルを表示
            st.subheader("📋 直近20件の測定履歴")
            # 最新のものが上に来るようにリバース
            history_df = df.tail(20).iloc[::-1].copy()
            st.dataframe(history_df, use_container_width=True)
            
    # 5秒待機して再レンダリング
    time.sleep(5)
