import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import pytz
import math

def calculate_rsi(data, periods=14):
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
    
    WEIGHTS = {
        "US_Yield_Inversion": 15, "TW_Foreign_Short": 20, "TW_Margin_Overheat": 20,
        "US_Speculative_Crash": 15, "US_Valuation_Bubble": 10, "TW_Tech_Divergence": 20
    }
               
    current_price, ma20, high_water_mark, drawdown_pct = 0.0, 0.0, 0.0, 0.0
    last_trading_date = "未知"
    fetch_success = False
    
    signals = {k: False for k in WEIGHTS.keys()}
    
    # 【新增】用來記錄原始數據以供前端網頁顯示
    raw_data = {
        "us10y": 0.0, "us3m": 0.0, "sp500_bias": 0.0, "ndx_rsi": 0.0,
        "twii_close": 0.0, "twii_20ma": 0.0, "twii_volatility": 0.0, 
        "twii_vol_ratio": 0.0, "twii_is_down": False
    }

    try:
        # --- 0050 股價數據 ---
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

        # --- 總經指標數據 (並儲存原始數值) ---
        us10y = yf.download("^TNX", period="1mo", progress=False, multi_level_index=False)
        us3m = yf.download("^IRX", period="1mo", progress=False, multi_level_index=False)
        if not us10y.empty and not us3m.empty:
            raw_data["us10y"] = round(float(us10y['Close'].iloc[-1]), 3)
            raw_data["us3m"] = round(float(us3m['Close'].iloc[-1]), 3)
            signals["US_Yield_Inversion"] = bool(raw_data["us10y"] < raw_data["us3m"])

        sp500 = yf.download("^GSPC", period="1y", progress=False, multi_level_index=False)
        if not sp500.empty:
            sp500['200MA'] = sp500['Close'].rolling(window=200).mean()
            if not pd.isna(sp500['200MA'].iloc[-1]):
                bias_ratio = (float(sp500['Close'].iloc[-1]) / float(sp500['200MA'].iloc[-1])) - 1
                raw_data["sp500_bias"] = round(bias_ratio * 100, 2)
                signals["US_Valuation_Bubble"] = bool(bias_ratio > 0.15)

        ndx = yf.download("^IXIC", period="3mo", progress=False, multi_level_index=False)
        if not ndx.empty:
            ndx['RSI'] = calculate_rsi(ndx)
            if not pd.isna(ndx['RSI'].iloc[-1]):
                raw_data["ndx_rsi"] = round(float(ndx['RSI'].iloc[-1]), 2)
                signals["US_Speculative_Crash"] = bool(raw_data["ndx_rsi"] > 75.0)

        twii = yf.download("^TWII", period="3mo", progress=False, multi_level_index=False)
        if not twii.empty:
            twii['20MA_Vol'] = twii['Volume'].rolling(window=20).mean()
            twii['Daily_Return'] = twii['Close'].pct_change()
            twii['Volatility'] = twii['Daily_Return'].rolling(window=10).std() * np.sqrt(252)
            
            twii_close = float(twii['Close'].iloc[-1])
            twii_20ma = float(twii['Close'].rolling(window=20).mean().iloc[-1])
            volatility = float(twii['Volatility'].iloc[-1])
            vol_ratio = float(twii['Volume'].iloc[-1]) / float(twii['20MA_Vol'].iloc[-1]) if float(twii['20MA_Vol'].iloc[-1]) > 0 else 0
            is_down = float(twii['Daily_Return'].iloc[-1]) < 0
            
            raw_data["twii_close"] = round(twii_close, 2)
            raw_data["twii_20ma"] = round(twii_20ma, 2)
            raw_data["twii_volatility"] = round(volatility * 100, 2)
            raw_data["twii_vol_ratio"] = round(vol_ratio, 2)
            raw_data["twii_is_down"] = bool(is_down)
            
            signals["TW_Tech_Divergence"] = bool(twii_close < twii_20ma)
            signals["TW_Foreign_Short"] = bool(volatility > 0.20) if not pd.isna(volatility) else False
            signals["TW_Margin_Overheat"] = bool(vol_ratio > 1.5 and is_down)

    except Exception as e:
        print(f"指標自動計算發生異常: {e}")

    risk_score = int(sum(WEIGHTS[k] for k, v in signals.items() if v))
    env_risk = bool(risk_score >= 85)
    trend_broken = bool(current_price < ma20) if fetch_success else False
    damage_taken = bool(drawdown_pct >= 7.0) if fetch_success else False

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
            "current_price": round(current_price, 2), "ma20": round(ma20, 2), 
            "high_water_mark": round(high_water_mark, 2), "drawdown_pct": round(drawdown_pct, 2)
        },
        "risk_score": risk_score,
        "locks": {"env_risk": env_risk, "trend_broken": trend_broken, "damage_taken": damage_taken},
        "decision": decision, "bg_color": bg_color, "shadow_color": shadow_color,
        "indicator_status": signals,
        "raw_indicators": raw_data # 將原始數據傳給前端
    }

    with open("latest_status.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_analysis()
