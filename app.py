import streamlit as st
import json
import os

st.set_page_config(page_title="0050 量化戰情中心", page_icon="🛡️", layout="wide")

JSON_FILE = "latest_status.json"

st.title("🛡️ 0050 量化防禦戰情中心")

if not os.path.exists(JSON_FILE):
    st.warning("⚠️ 系統正在初始化或尚未取得今日數據，請稍後再試。")
else:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    st.success(f"📡 最新資料更新時間：{data['update_time']} (每日 17:00 自動結算)")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("📊 0050 價格防衛線")
        metrics = st.columns(3)
        metrics[0].metric("今日還原收盤價", f"{data['price_data']['current_price']}")
        metrics[1].metric("月線 (20MA)", f"{data['price_data']['ma20']}")
        metrics[2].metric("波段最高點", f"{data['price_data']['high_water_mark']}")
        
        st.markdown("---")
        st.subheader("🛡️ 三重安全栓狀態")
        st.checkbox("1. 環境極度危險 (分數 >= 85)", value=data['locks']['env_risk'], disabled=True)
        st.checkbox("2. 趨勢跌破月線 (現價 < 20MA)", value=data['locks']['trend_broken'], disabled=True)
        st.checkbox(f"3. 實質防線貫破 (回撤 >= 7%, 目前為 {data['price_data']['drawdown_pct']}%)", value=data['locks']['damage_taken'], disabled=True)

    with col2:
        st.subheader("🎯 當前風險總分")
        st.markdown(f"<h1 style='text-align: center; color: {data['bg_color']}; font-size: 6rem; margin-bottom: 0px;'>{data['risk_score']} 分</h1>", unsafe_allow_html=True)
        st.progress(data['risk_score'] / 100)
        
    st.markdown("---")
    st.markdown(
        f"""
        <div style="background-color: {data['bg_color']}; padding: 30px; border-radius: 12px; text-align: center; color: white;">
            <h1 style="margin: 0;">{data['decision']}</h1>
        </div>
        """, unsafe_allow_html=True
    )