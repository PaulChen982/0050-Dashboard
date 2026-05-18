import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import pytz
import math

def calculate_rsi(data, periods=14):
    """計算 RSI 輔助函數"""
    close_delta = data['Close'].diff()
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    rsi = ma_up / ma_down
    rsi = 100 - (100 / (1 + rsi))
    return rsi

def run_analysis():
    tw_tz = pytz.timezone('Asia/Taipei')
    now_tw = datetime.now(tw_tz)
    update_time_str = now_tw.strftime('%Y-%m-%d %H:%M:%S')
    print(f"啟動全自動量化分析 (100% 雲端數據連動)，目前台灣時間: {update_time_str}")
    
    # 風控指標權重配置
    WEIGHTS = {
        "US_Yield_Inversion": 15, 
        "TW_Foreign_Short": 20, 
        "TW_Margin_Overheat": 20,
        "US_Speculative_Crash": 15, 
        "US_Valuation_Bubble": 10, 
        "TW_Tech_Divergence": 20
    }
               
    current_price, ma20, high_water_mark, drawdown_pct = 0.0, 0.0, 0.0, 0.0
    last_trading_date = "未知"
    fetch_success = False
    
    # 初始化自動判定的信號開關
    signals = {k: False for k in WEIGHTS.keys()}

    try:
        # ==========================================
        # 1. 抓取 0050 主體價格數據
        # ==========================================
        df_0050 = yf.download("0050.TW", period="6mo", multi_level_index=False)
        
        if not df_0050.empty:
            df_0050 = df_0050.copy()
            if 'Adj Close' in df_0050.columns:
                df_0050.loc[:, 'Close'] = df_0050['Adj Close']
            
            df_0050 = df_0050.dropna(subset=['Close'])
            
            if not df_0050.empty:
                df_0050['20MA'] = df_0050['Close'].rolling(window=20).mean()
                valid_ma_df = df_0050.dropna(subset=['20MA'])
                
                last_trading_date = df_0050.index[-1].strftime('%Y-%m-%d')
                
                current_price = float(df_0050['Close'].iloc[-1])
                ma20 = float(valid_ma_df['20MA'].iloc[-1]) if not valid_ma_df.empty else current_price
                high_water_mark = float(df_0050['Close'].max())
                drawdown_pct = float(((high_water_mark - current_price) / high_water_mark) * 100) if high_water_mark > 0 else 0.0
                
                if not math.isnan(current_price) and not math.isnan(ma20):
                    fetch_success = True

        # ==========================================
        # 2. 全自動抓取國際總經與籌碼指標，動態計算信號
        # ==========================================
        # 指標 1: 美債倒掛 (10Y < 3M)
        us10y = yf.download("^TNX", period="1mo", progress=False, multi_level_index=False)
        us3m = yf.download("^IRX", period="1mo", progress=False, multi_level_index=False)
        if not us10y.empty and not us3m.empty:
            # 【修復】加入 bool() 強制轉型
            signals["US_Yield_Inversion"] = bool(float(us10y['Close'].iloc[-1]) < float(us3m['Close'].iloc[-1]))

        # 指標 2: 美股估值過高 (S&P 500 乖離率 > 15%)
        sp500 = yf.download("^GSPC", period="1y", progress=False, multi_level_index=False)
        if not sp500.empty:
            sp500['200MA'] = sp500['Close'].rolling(window=200).mean()
            if not pd.isna(sp500['200MA'].iloc[-1]):
                bias_ratio = (sp500['Close'].iloc[-1] / sp500['200MA'].iloc[-1]) - 1
                signals["US_Valuation_Bubble"] = bool(bias_ratio > 0.15)

        # 指標 3: 投機市場過熱 (Nasdaq RSI > 75)
        ndx = yf.download("^IXIC", period="3mo", progress=False, multi_level_index=False)
        if not ndx.empty:
            ndx['RSI'] = calculate_rsi(ndx)
            signals["US_Speculative_Crash"] = bool(float(ndx['RSI'].iloc[-1]) > 75.0) if not pd.isna(ndx['RSI'].iloc[-1]) else False

        # 指標 4, 5, 6: 台股大盤連動性與籌碼 (Volatility & Volume Proxy)
        twii = yf.download("^TWII", period="3mo", progress=False, multi_level_index=False)
        if not twii.empty:
            twii['20MA_Vol'] = twii['Volume'].rolling(window=20).mean()
            twii['Daily_Return'] = twii['Close'].pct_change()
            twii['Volatility'] = twii['Daily_Return'].rolling(window=10).std() * np.sqrt(252) # 年化波動度
            
            # 台股技術背離：大盤跌破月線
            signals["TW_Tech_Divergence"] = bool(float(twii['Close'].iloc[-1]) < float(twii['Close'].rolling(window=20).mean().iloc[-1]))
            
            # 外資/機構恐慌指標：短期波動率飆升超過 20%
            signals["TW_Foreign_Short"] = bool(float(twii['Volatility'].iloc[-1]) > 0.20) if not pd.isna(twii['Volatility'].iloc[-1]) else False
            
            # 散戶融資/爆量殺盤：成交量 > 20日均量 1.5倍 且 當日下跌
            vol_surge = float(twii['Volume'].iloc[-1]) > (float(twii['20MA_Vol'].iloc[-1]) * 1.5)
            is_down = float(twii['Daily_Return'].iloc[-1]) < 0
            signals["TW_Margin_Overheat"] = bool(vol_surge and is_down)

    except Exception as e:
        print(f"指標自動計算發生異常: {e}")

    # 計算總風險分數
    risk_score = int(sum(WEIGHTS[k] for k, v in signals.items() if v))
    
    env_risk = bool(risk_score >= 85)
    trend_broken = bool(current_price < ma20) if fetch_success else False
    damage_taken = bool(drawdown_pct >= 7.0) if fetch_success else False

    # 決策橫幅文字、顏色與陰影設定
    if not fetch_success:
        decision, bg_color, shadow_color = "⚠️ 數據格式同步異常，等待雲端修正中", "#374151", "rgba(55, 65, 81, 0.5)"
    elif env_risk and trend_broken and damage_taken:
        decision, bg_color, shadow_color = "🚨 危險！強烈建議先跑：市場全面轉弱，先賣出保留現金，等穩定了再說！", "#991B1B", "rgba(153, 27, 27, 0.5)"
    elif env_risk:
        decision, bg_color, shadow_color = "⚠️ 大環境非常惡劣：市場隨時有雪崩風險！絕對不要再加碼，盯緊月線準備閃人！", "#B45309", "rgba(180, 83, 9, 0.5)"
    elif trend_broken or damage_taken:
        decision, bg_color, shadow_color = "👀 價格走勢轉弱：已經跌破重要支撐，先停看聽，不要急著伸手接刀。", "#4B5563", "rgba(75, 85, 99, 0.5)"
    elif risk_score >= 70:
        decision, bg_color, shadow_color = "🟡 警訊浮現、支撐仍在：外圍風向開始變了，好在 0050 股價還踩得很穩。不用嚇自己，繼續抱著觀察！", "#D97706", "rgba(217, 119, 6, 0.5)"
    else:
        decision, bg_color, shadow_color = "✅ 盤勢非常健康：內外指標都很安全，沒有明顯風險，安心抱著就好！", "#166534", "rgba(22, 101, 52, 0.5)"

    snapshot = {
        "update_time": update_time_str,
        "last_trading_date": last_trading_date,
        "price_data": {
            "current_price": round(current_price, 2), 
            "ma20": round(ma20, 2), 
            "high_water_mark": round(high_water_mark, 2), 
            "drawdown_pct": round(drawdown_pct, 2)
        },
        "risk_score": risk_score,
        "locks": {"env_risk": env_risk, "trend_broken": trend_broken, "damage_taken": damage_taken},
        "decision": decision, "bg_color": bg_color, "shadow_color": shadow_color,
        "indicator_status": signals
    }

    with open("latest_status.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=4)
    print("全自動化分析完成並成功寫入 JSON！風險總分：", risk_score)

if __name__ == "__main__":
    run_analysis()
