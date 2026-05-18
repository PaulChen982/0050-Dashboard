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

        st.markdown("<br><h4 style='color: #FFFFFF; font-weight: 600; margin-bottom: 15px;'>🛡️ 核心三大危險訊號 (系統決策鎖)</h4>", unsafe_allow_html=True)
        
        st.markdown(check_status(
            data['locks']['env_risk'], 
            "第一鎖：環境風險過高", 
            "由下方的 6 大總經與籌碼指標總分判定。達 85 分代表發生系統性崩跌的機率極高。",
            "總分 ≥ 85 分", f"{data['risk_score']} 分"
        ), unsafe_allow_html=True)
        
        st.markdown(check_status(
            data['locks']['trend_broken'], 
            "第二鎖：短期趨勢轉弱", 
            "0050 跌破 20 日均線，代表近一個月買盤套牢，多頭趨勢轉弱。",
            f"低於 {data['price_data']['ma20']}", f"{data['price_data']['current_price']}"
        ), unsafe_allow_html=True)
        
        st.markdown(check_status(
            data['locks']['damage_taken'], 
            "第三鎖：波段回檔過深", 
            "0050 自近期最高點回檔一旦超過 7%，通常代表市場引發實質恐慌與多殺多。",
            "跌幅 ≥ 7.00 %", f"{data['price_data']['drawdown_pct']} %"
        ), unsafe_allow_html=True)

        st.markdown("<br><hr style='border-color: #374151;'><br>", unsafe_allow_html=True)

        # ==========================================
        # 新增區塊：六大指標明細
        # ==========================================
        st.markdown("<h4 style='color: #FFFFFF; font-weight: 600; margin-bottom: 15px;'>🌐 六大總經與籌碼指標 (總分計算來源)</h4>", unsafe_allow_html=True)
        
        if "raw_indicators" in data:
            st.markdown(check_status(
                data['indicator_status']['US_Yield_Inversion'],
                "美債殖利率倒掛 (+15 分)", "10 年期公債殖利率低於 3 個月期，預示國際經濟衰退風險。",
                "10年期 < 3個月期", f"10年: {data['raw_indicators']['us10y']}% | 3月: {data['raw_indicators']['us3m']}%"
            ), unsafe_allow_html=True)
            
            st.markdown(check_status(
                data['indicator_status']['US_Valuation_Bubble'],
                "美股估值過高 (+10 分)", "S&P 500 指數偏離 200 日均線過大，有過熱回檔風險。",
                "正乖離 > 15%", f"目前乖離: {data['raw_indicators']['sp500_bias']} %"
            ), unsafe_allow_html=True)
            
            st.markdown(check_status(
                data['indicator_status']['US_Speculative_Crash'],
                "投機市場過熱 (+15 分)", "Nasdaq 指數 RSI 進入極度超買區，隨時可能反轉。",
                "RSI > 75", f"RSI 數值: {data['raw_indicators']['ndx_rsi']}"
            ), unsafe_allow_html=True)
            
            st.markdown(check_status(
                data['indicator_status']['TW_Tech_Divergence'],
                "台股技術背離 (+20 分)", "台股大盤跌破月線，代表整體市場趨勢轉弱。",
                f"大盤低於 {data['raw_indicators']['twii_20ma']}", f"目前大盤: {data['raw_indicators']['twii_close']}"
            ), unsafe_allow_html=True)
            
            st.markdown(check_status(
                data['indicator_status']['TW_Foreign_Short'],
                "大戶恐慌拋售 (+20 分)", "台股短期年化波動率飆升，顯示大戶籌碼鬆動或恐慌拋售。",
                "波動率 > 20%", f"波動率: {data['raw_indicators']['twii_volatility']} %"
            ), unsafe_allow_html=True)
            
            twii_down_text = "收跌" if data['raw_indicators']['twii_is_down'] else "未收跌"
            st.markdown(check_status(
                data['indicator_status']['TW_Margin_Overheat'],
                "散戶爆量殺盤 (+20 分)", "台股成交量爆出 20 日均量的 1.5 倍以上，且當日收黑。",
                "量增 > 1.5倍 且 收跌", f"量增 {data['raw_indicators']['twii_vol_ratio']}倍 | 今日{twii_down_text}"
            ), unsafe_allow_html=True)

    with col2:
        # 在側邊釘選顯示大大的當前風險總分
        st.markdown("<h4 style='text-align: center; color: #FFFFFF; font-weight: 600;'>🎯 今天的風險分數</h4>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='score-card'>
                <p class='score-value' style='color: {data['bg_color']};'>{data['risk_score']}</p>
                <p style='color: #9CA3AF; font-size: 1.1rem; margin-top: 10px; letter-spacing: 1px;'>(由下方六大指標動態加總，滿分 100 分)</p>
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
