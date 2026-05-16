import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import pytz

def run_analysis():
    tw_tz = pytz.timezone('Asia/Taipei')
    now_tw = datetime.now(tw_tz)
    print(f"啟動量化分析，目前台灣時間: {now_tw.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 權重設定
    WEIGHTS = {"US_Yield_Inversion": 15, "TW_Foreign_Short": 20, "TW_Margin_Overheat": 20,
               "US_Speculative_Crash": 15, "US_Valuation_Bubble": 10, "TW_Tech_Divergence": 20}
               
    # 1. 抓取 0050 股價
    try:
        ticker = yf.Ticker("0050.TW")
        df = ticker.history(period="6mo")
        current_price = df['Close'].iloc[-1]
        df['20MA'] = df['Close'].rolling(window=20).mean()
        ma20 = df['20MA'].iloc[-1]
        high_water_mark = df['Close'].max()
    except Exception as e:
        print(f"抓取數據失敗: {e}")
        return

    # 2. 總經環境設定 (這部分目前設為預設值，未來你可自行在此修改 True/False)
    signals = {"US_Yield_Inversion": True, "TW_Foreign_Short": True, "TW_Margin_Overheat": False,
               "US_Speculative_Crash": True, "US_Valuation_Bubble": True, "TW_Tech_Divergence": True}
    
    # 3. 計算分數與決策
    risk_score = sum(WEIGHTS[k] for k, v in signals.items() if v)
    drawdown_pct = ((high_water_mark - current_price) / high_water_mark) * 100 if high_water_mark > 0 else 0
    
    env_risk = risk_score >= 85
    trend_broken = current_price < ma20
    damage_taken = drawdown_pct >= 7.0

    if env_risk and trend_broken and damage_taken:
        decision, bg_color = "🚨 終極指令：全數出清，滿手現金避險！", "#8B0000" # 深紅
    elif env_risk:
        decision, bg_color = "⚠️ 戰術減碼：停止買進，嚴守支撐！", "#D2691E" # 深橘
    elif trend_broken or damage_taken:
        decision, bg_color = "👀 技術洗盤：暫不動作，持續觀察。", "#555555" # 鐵灰
    else:
        decision, bg_color = "✅ 安全巡航：維持紀律，順勢而為。", "#006400" # 深綠

    # 4. 存成 JSON 檔案
    snapshot = {
        "update_time": now_tw.strftime('%Y-%m-%d %H:%M:%S'),
        "price_data": {"current_price": round(current_price, 2), "ma20": round(ma20, 2), 
                       "high_water_mark": round(high_water_mark, 2), "drawdown_pct": round(drawdown_pct, 2)},
        "risk_score": risk_score,
        "locks": {"env_risk": env_risk, "trend_broken": trend_broken, "damage_taken": damage_taken},
        "decision": decision, "bg_color": bg_color
    }

    with open("latest_status.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=4)
    print("分析完成並存檔！")

if __name__ == "__main__":
    run_analysis()