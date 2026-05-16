import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import pytz

def run_analysis():
    tw_tz = pytz.timezone('Asia/Taipei')
    now_tw = datetime.now(tw_tz)
    update_time_str = now_tw.strftime('%Y-%m-%d %H:%M:%S')
    print(f"啟動量化分析，目前台灣時間: {update_time_str}")
    
    WEIGHTS = {"US_Yield_Inversion": 15, "TW_Foreign_Short": 20, "TW_Margin_Overheat": 20,
               "US_Speculative_Crash": 15, "US_Valuation_Bubble": 10, "TW_Tech_Divergence": 20}
               
    current_price, ma20, high_water_mark, drawdown_pct = 0.0, 0.0, 0.0, 0.0
    fetch_success = False

    try:
        ticker = yf.Ticker("0050.TW")
        df = ticker.history(period="6mo")
        if not df.empty:
            df['20MA'] = df['Close'].rolling(window=20).mean()
            
            # 【關鍵修復】：加上 float()，把 Pandas 特殊格式洗掉，轉成標準 Python 數字
            current_price = float(df['Close'].iloc[-1])
            ma20 = float(df['20MA'].iloc[-1])
            high_water_mark = float(df['Close'].max())
            drawdown_pct = float(((high_water_mark - current_price) / high_water_mark) * 100) if high_water_mark > 0 else 0.0
            
            fetch_success = True
    except Exception as e:
        print(f"抓取數據失敗: {e}")

    signals = {"US_Yield_Inversion": True, "TW_Foreign_Short": True, "TW_Margin_Overheat": False,
               "US_Speculative_Crash": True, "US_Valuation_Bubble": True, "TW_Tech_Divergence": True}
    
    risk_score = int(sum(WEIGHTS[k] for k, v in signals.items() if v))
    
    # 【關鍵修復】：加上 bool()，確保一定是標準的 Python 布林值
    env_risk = bool(risk_score >= 85)
    trend_broken = bool(current_price < ma20) if fetch_success else False
    damage_taken = bool(drawdown_pct >= 7.0) if fetch_success else False

    if not fetch_success:
        decision, bg_color = "⚠️ 股價 API 連線異常，請稍後再試。", "#A9A9A9"
    elif env_risk and trend_broken and damage_taken:
        decision, bg_color = "🚨 終極指令：全數出清，滿手現金避險！", "#8B0000"
    elif env_risk:
        decision, bg_color = "⚠️ 戰術減碼：停止買進，嚴守支撐！", "#D2691E"
    elif trend_broken or damage_taken:
        decision, bg_color = "👀 技術洗盤：暫不動作，持續觀察。", "#555555"
    else:
        decision, bg_color = "✅ 安全巡航：維持紀律，順勢而為。", "#006400"

    snapshot = {
        "update_time": update_time_str,
        "price_data": {"current_price": round(current_price, 2), "ma20": round(ma20, 2), 
                       "high_water_mark": round(high_water_mark, 2), "drawdown_pct": round(drawdown_pct, 2)},
        "risk_score": risk_score,
        "locks": {"env_risk": env_risk, "trend_broken": trend_broken, "damage_taken": damage_taken},
        "decision": decision, "bg_color": bg_color
    }

    # 這裡就不會再報錯了！
    with open("latest_status.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=4)
    print("分析完成並成功寫入 JSON！")

if __name__ == "__main__":
    run_analysis()
