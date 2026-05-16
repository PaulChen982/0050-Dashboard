import streamlit as st
import json
import os

# 隱藏預設選單，設定為全螢幕寬度
st.set_page_config(page_title="0050 戰情中心 | Pro", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# 植入高階財經網頁 CSS (深色卡片、光影質感、無邊框設計)
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E5E7EB; font-family: 'Helvetica Neue', sans-serif; }
    div[data-testid="stHeader"] { display: none; }
    
    .dashboard-title { font-size: 2rem; font-weight: 800; color: #FFFFFF; margin-bottom: -10px; }
    .update-time { font-size: 0.85rem; color: #9CA3AF; margin-bottom: 25px; }
    
    .metric-card {
        background-color: #1F2937;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    .metric-title { font-size: 0.9rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .metric-value { font-size: 2.2rem; font-weight: 700; color: #F3F4F6; }
    
    .score-card { text-align: center; padding: 20px 0; }
    .score-value { font-size: 6rem; font-weight: 900; line-height: 1; margin: 0; text-shadow: 2px 4px 10px rgba(0,0,0,0.5); }
    
    .checklist-item { font-size: 1.1rem; color: #D1D5DB; margin: 12px 0; display: flex; align-items: center; }
    .checklist-icon { font-size: 1.3rem; margin-right: 10px; }
</style>
""", unsafe_allow_html=True)

JSON_FILE = "latest_status.json"

if not os.path.exists(JSON_FILE):
    st.warning("⚠️ 系統正在初始化，請稍後重整網頁。")
else:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    st.markdown("<div class='dashboard-title'>🛡️ 0050 量化防禦戰情中心</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='update-time'>📡 最新數據時間：{data['update_time']} (自動過濾週末無效數據)</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.2, 1], gap="large")
    
    with col1:
        # 使用自訂的 UI 卡片取代原本醜醜的 metrics
        st.markdown("<h4 style='color: #F3F4F6;'>📊 價格防衛線</h4>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><div class='metric-title'>還原收盤價</div><div class='metric-value'>{data['price_data']['current_price']}</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><div class='metric-title'>20MA 月線</div><div class='metric-value'>{data['price_data']['ma20']}</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><div class='metric-title'>歷史高點</div><div class='metric-value'>{data['price_data']['high_water_mark']}</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br><h4 style='color: #F3F4F6;'>🛡️ 三維安全栓</h4>", unsafe_allow_html=True)
        # 優化 Checklist 的顯示邏輯 (亮起紅燈與安全綠燈)
        def check_status(is_triggered, text):
            icon = "🔴" if is_triggered else "🟢"
            color = "#EF4444" if is_triggered else "#10B981"
            return f"<div class='checklist-item'><span class='checklist-icon'>{icon}</span><span style='color: {color};'>{text}</span></div>"
            
        st.markdown(check_status(data['locks']['env_risk'], "環境極度危險 (分數 ≥ 85)"), unsafe_allow_html=True)
        st.markdown(check_status(data['locks']['trend_broken'], "趨勢跌破生命線 (現價 < 月線)"), unsafe_allow_html=True)
        st.markdown(check_status(data['locks']['damage_taken'], f"實質防線貫破 (回撤 ≥ 7%，目前 {data['price_data']['drawdown_pct']}%)"), unsafe_allow_html=True)

    with col2:
        st.markdown("<h4 style='text-align: center; color: #F3F4F6;'>🎯 總體風險評級</h4>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='score-card'>
                <p class='score-value' style='color: {data['bg_color']};'>{data['risk_score']}</p>
                <p style='color: #9CA3AF; font-size: 1.2rem;'>MAX RISK: 100</p>
            </div>
        """, unsafe_allow_html=True)
        st.progress(data['risk_score'] / 100)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 最終決策橫幅 (加入光影特效)
    st.markdown(
        f"""
        <div style="background-color: {data['bg_color']}; padding: 25px; border-radius: 16px; text-align: center; 
                    box-shadow: 0 10px 25px {data['shadow_color']}; border: 1px solid rgba(255,255,255,0.1);">
            <h2 style="margin: 0; color: #FFFFFF; font-weight: 800; letter-spacing: 1.5px;">{data['decision']}</h2>
        </div>
        """, unsafe_allow_html=True
    )
