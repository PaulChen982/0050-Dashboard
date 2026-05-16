import streamlit as st
import json
import os

st.set_page_config(page_title="0050 每日風險快篩", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E5E7EB; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    div[data-testid="stHeader"] { display: none; }
    
    .dashboard-title { font-size: 2.2rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.5px; margin-bottom: -5px; }
    .update-time { font-size: 0.9rem; color: #9CA3AF; margin-bottom: 30px; }
    .highlight-date { color: #38BDF8; font-weight: 600; }
    
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
</style>
""", unsafe_allow_html=True)

JSON_FILE = "latest_status.json"

if not os.path.exists(JSON_FILE):
    st.warning("⚠️ 系統正在編譯初始指標，請稍後重整網頁。")
else:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    trading_date = data.get('last_trading_date', '更新中...')

    st.markdown("<div class='dashboard-title'>📊 0050 每日風險快篩</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='update-time'>系統結算時間：{data['update_time']} ｜ 📊 股價基準日：<span class='highlight-date'>{trading_date}</span></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.2, 1], gap="large")
    
    with col1:
        st.markdown("<h4 style='color: #FFFFFF; font-weight: 600; margin-bottom: 15px;'>📈 目前股價狀況</h4>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><div class='metric-title'>收盤價</div><div class='metric-value'>{data['price_data']['current_price']}</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><div class='metric-title'>月線 (20MA)</div><div class='metric-value'>{data['price_data']['ma20']}</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><div class='metric-title'>最近的高點</div><div class='metric-value'>{data['price_data']['high_water_mark']}</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br><h4 style='color: #FFFFFF; font-weight: 600; margin-bottom: 15px;'>🛡️ 三大危險訊號檢查</h4>", unsafe_allow_html=True)
        
        # 封裝一體化的數據對比面板函數
        def check_status(is_triggered, title, description, baseline_text, current_text):
            icon = "🔴" if is_triggered else "🟢"
            color = "#EF4444" if is_triggered else "#10B981"
            
            return f"""
            <div style='margin: 18px 0; padding: 16px; background-color: rgba(255,255,255,0.02); border-radius: 10px; border-left: 4px solid {color};'>
                <div style='display: flex; align-items: center; font-size: 1.15rem; font-weight: 600;'>
                    <span style='font-size: 1.3rem; margin-right: 12px;'>{icon}</span>
                    <span style='color: {color};'>{title}</span>
                </div>
                <div style='font-size: 0.85rem; color: #9CA3AF; margin-left: 36px; margin-top: 6px; line-height: 1.4;'>
                    {description}
                </div>
                <div style='margin-left: 36px; margin-top: 12px; font-size: 0.95rem; background-color: rgba(0,0,0,0.4); padding: 8px 15px; border-radius: 6px; display: inline-block; border: 1px solid rgba(255,255,255,0.05);'>
                    <span style='color: #9CA3AF;'>警戒基準：</span><span style='color: #D1D5DB; margin-right: 20px;'>{baseline_text}</span>
                    <span style='color: #9CA3AF;'>目前現況：</span><span style='color: {color}; font-weight: 700;'>{current_text}</span>
                </div>
            </div>
            """
            
        st.markdown(check_status(
            data['locks']['env_risk'], 
            "環境風險過高", 
            "綜合評估外資籌碼與國際總經等6項核心指標。達85分代表發生系統性崩跌的機率極高。",
            "≥ 85 分",
            f"{data['risk_score']} 分"
        ), unsafe_allow_html=True)
        
        st.markdown(check_status(
            data['locks']['trend_broken'], 
            "短期趨勢轉弱", 
            "月線(20MA)為短線生命線。跌破代表近一個月買盤套牢，多頭趨勢轉弱，需提高警覺。",
            f"低於 {data['price_data']['ma20']}",
            f"{data['price_data']['current_price']}"
        ), unsafe_allow_html=True)
        
        st.markdown(check_status(
            data['locks']['damage_taken'], 
            "波段回檔過深", 
            "0050正常洗盤震盪約在3~5%內。回檔一旦超過7%，通常代表市場引發實質恐慌與多殺多。",
            "≥ 7.00 %",
            f"{data['price_data']['drawdown_pct']} %"
        ), unsafe_allow_html=True)

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
