import streamlit as st
import json
import os

st.set_page_config(page_title="0050 每日風險快篩", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E5E7EB; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    div[data-testid="stHeader"] { display: none; }
    
    .dashboard-title { font-size: 2.2rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.5px; margin-bottom: -5px; }
    .update-time { font-size: 0.85rem; color: #9CA3AF; margin-bottom: 30px; }
    
    .metric-card {
        background-color: #1F2937;
        border-radius: 12px;
        padding: 22px;
        border: 1px solid #374151;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        text-align: center;
    }
    .metric-title { font-size: 0.85rem; color: #9CA3AF; font-weight: 500; letter-spacing: 0.5px; margin-bottom: 8px; }
    .metric-value { font-size: 2.4rem; font-weight: 700; color: #FFFFFF; }
    
    .score-card { text-align: center; padding: 25px 0; }
    .score-value { font-size: 6.5rem; font-weight: 800; line-height: 1; margin: 0; }
    
    .checklist-item { font-size: 1.15rem; margin: 15px 0; display: flex; align-items: center; font-weight: 500; }
    .checklist-icon { font-size: 1.4rem; margin-right: 12px; }
</style>
""", unsafe_allow_html=True)

JSON_FILE = "latest_status.json"

if not os.path.exists(JSON_FILE):
    st.warning("⚠️ 系統正在編譯初始指標，請稍後重整網頁。")
else:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 【全面白話文修改：看板標題與小標】
    st.markdown("<div class='dashboard-title'>📊 0050 每日風險快篩</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='update-time'>📡 最新資料時間：{data['update_time']} (週末假日不更新喔！)</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.2, 1], gap="large")
    
    with col1:
        st.markdown("<h4 style='color: #FFFFFF; font-weight: 600; margin-bottom: 15px;'>📈 目前股價狀況</h4>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><div class='metric-title'>今天收盤價</div><div class='metric-value'>{data['price_data']['current_price']}</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><div class='metric-title'>月線 (20MA)</div><div class='metric-value'>{data['price_data']['ma20']}</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><div class='metric-title'>最近的高點</div><div class='metric-value'>{data['price_data']['high_water_mark']}</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br><h4 style='color: #FFFFFF; font-weight: 600; margin-bottom: 15px;'>🛡️ 三大危險訊號檢查</h4>", unsafe_allow_html=True)
        
        def check_status(is_triggered, text):
            icon = "🔴" if is_triggered else "🟢"
            color = "#F87171" if is_triggered else "#34D399"
            return f"<div class='checklist-item'><span class='checklist-icon'>{icon}</span><span style='color: {color};'>{text}</span></div>"
            
        st.markdown(check_status(data['locks']['env_risk'], "大環境亮紅燈 (總經與籌碼分數 ≥ 85)"), unsafe_allow_html=True)
        st.markdown(check_status(data['locks']['trend_broken'], "跌破月線了 (今天收盤價 < 月線)"), unsafe_allow_html=True)
        st.markdown(check_status(data['locks']['damage_taken'], f"跌得有點多 (從高點跌下來超過 7%，現在跌了 {data['price_data']['drawdown_pct']}%)"), unsafe_allow_html=True)

    with col2:
        st.markdown("<h4 style='text-align: center; color: #FFFFFF; font-weight: 600;'>🎯 今天的風險分數</h4>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='score-card'>
                <p class='score-value' style='color: {data['bg_color']};'>{data['risk_score']}</p>
                <p style='color: #9CA3AF; font-size: 1.1rem; margin-top: 10px; letter-spacing: 1px;'>(滿分 100 分，越高越危險)</p>
            </div>
        """, unsafe_allow_html=True)
        st.progress(data['risk_score'] / 100)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(
        f"""
        <div style="background-color: {data['bg_color']}; padding: 25px; border-radius: 16px; text-align: center; 
                    box-shadow: 0 10px 30px {data['shadow_color']}; border: 1px solid rgba(255,255,255,0.08);">
            <h2 style="margin: 0; color: #FFFFFF; font-weight: 700; letter-spacing: 1px;">{data['decision']}</h2>
        </div>
        """, unsafe_allow_html=True
    )
