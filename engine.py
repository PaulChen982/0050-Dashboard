import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import pytz
import math

def run_analysis():
    tw_tz = pytz.timezone('Asia/Taipei')
    now_tw = datetime.now(tw_tz)
    update_time_str = now_tw.strftime('%Y-%m-%d %H:%M:%S')
    
    WEIGHTS = {"US_Yield_Inversion": 15, "TW_Foreign_Short": 20, "TW_Margin_Overheat": 20,
               "US_Speculative_Crash": 15, "US_Valuation_Bubble": 10, "TW_Tech_Divergence": 20}
               
    current_price, ma20, high_water_mark, drawdown_pct = 0.0, 0.0, 0.0, 0.0
    fetch_success = False

    try:
        ticker = yf.Ticker("0050.TW")
        df = ticker.history(period="6mo")
        df = df.dropna(subset=['Close'])
        
        if not df.empty:
            df['20MA'] = df['Close'].rolling(window=20).mean()
            valid_ma_df = df.dropna(subset=['20MA'])
            
            current_price = float(df['Close'].iloc[-1])
            ma20 = float(valid_ma_df['20MA'].iloc[-1]) if not valid_ma_df.empty else current_price
            high_water_mark = float(df['Close'].max())
            drawdown_pct = float(((high_water_mark - current_price) / high_water_mark) * 100) if high_water_mark > 0 else 0.0
            
            if not math.isnan(current_price) and not math.isnan(ma20):
                fetch_success = True
    except Exception as e:
        print(f"數據抓取異常: {e}")

    signals = {"US_Yield_Inversion": True, "TW_Foreign_Short": True, "TW_Margin_Overheat": False,
               "US_Speculative_Crash": True, "US_Valuation_Bubble": True, "TW_Tech_Divergence": True}
    
    risk_score = int(sum(WEIGHTS[k] for k, v in signals.items() if v))
    
    env_risk = bool(risk_score >= 85)
    trend_broken = bool(current_price < ma20) if fetch_success else False
    damage_taken = bool(drawdown_pct >= 7.0) if fetch_success else False

    # 【全面白話文修改：決策指令】
    if not fetch_success:
        decision, bg_color, shadow_color = "⚠️ 抓不到資料，可能網路卡卡的，晚點再試試看", "#374151", "rgba(55, 65, 81, 0.5)"
    elif env_risk and trend_broken and damage_taken:
        decision, bg_color, shadow_color = "🚨 危險！強烈建議先跑：市場全面轉弱，先賣出保留現金，等穩定了再說！", "#991B1B", "rgba(153, 27, 27, 0.5)"
    elif env_risk:
        decision, bg_color, shadow_color = "⚠️ 大環境不太妙：先別急著買，盯緊月線，如果跌破就準備閃人！", "#B45309", "rgba(180, 83, 9, 0.5)"
    elif trend_broken or damage_taken:
        decision, bg_color, shadow_color = "👀 稍微轉弱囉：跌破重要支撐了，先停看聽，不要急著加碼。", "#4B5563", "rgba(75, 85, 99, 0.5)"
    else:
        decision, bg_color, shadow_color = "✅ 盤勢很健康：目前沒什麼大風險，安心抱著就好！", "#166534", "rgba(22, 101, 52, 0.5)"

    snapshot = {
        "update_time": update_time_str,
        "price_data": {"current_price": round(current_price, 2), "ma20": round(ma20, 2), 
                       "high_water_mark": round(high_water_mark, 2), "drawdown_pct": round(drawdown_pct, 2)},
        "risk_score": risk_score,
        "locks": {"env_risk": env_risk, "trend_broken": trend_broken, "damage_taken": damage_taken},
        "decision": decision, "bg_color": bg_color, "shadow_color": shadow_color
    }

    with open("latest_status.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=4)
        
if __name__ == "__main__":
    run_analysis()
