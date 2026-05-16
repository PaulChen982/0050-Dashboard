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
    print(f"啟動量化分析，目前台灣時間: {update_time_str}")
    
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

    # 模擬環境指標（目前觸發5項共80分）
    signals = {"US_Yield_Inversion": True, "TW_Foreign_Short": True, "TW_Margin_Overheat": False,
               "US_Speculative_Crash": True, "US_Valuation_Bubble": True, "TW_Tech_Divergence": True}
    
    risk_score = int(sum(WEIGHTS[k] for k, v in signals.items() if v))
    
    env_risk = bool(risk_score >= 85)
    trend_broken = bool(current_price < ma20) if fetch_success else False
    damage_taken = bool(drawdown_pct >= 7.0) if fetch_success else False

    # 【🛡️ 完美修正：嚴格分層的白話決策邏輯】
    if not fetch_success:
        decision, bg_color, shadow_color = "⚠️ 抓不到資料，可能網路卡卡的，晚點再試試看", "#374151", "rgba(55, 65, 81, 0.5)"
    
    # 狀態 1：大環境爆表 + 股價崩盤 = 全面撤退
    elif env_risk and trend_broken and damage_taken:
        decision, bg_color, shadow_color = "🚨 危險！強烈建議先跑：市場全面轉弱，先賣出保留現金，等穩定了再說！", "#991B1B", "rgba(153, 27, 27, 0.5)"
    
    # 狀態 2：環境極度惡劣 (85分以上) 但股價還在撐 = 停止買進，嚴守防線
    elif env_risk:
        decision, bg_color, shadow_color = "⚠️ 大環境非常惡劣：市場隨時有雪崩風險！絕對不要再加碼，盯緊月線準備閃人！", "#B45309", "rgba(180, 83, 9, 0.5)"
    
    # 狀態 3：不論環境幾分，股價實質破線 = 走勢轉弱，先停看聽
    elif trend_broken or damage_taken:
        decision, bg_color, shadow_color = "👀 價格走勢轉弱：已經跌破重要支撐，先停看聽，不要急著伸手接刀。", "#4B5563", "rgba(75, 85, 99, 0.5)"
    
    # 狀態 4【本次核心修復】：大環境風險高（70~84分，如今天的80分），但股價支撐完好 = 警訊浮現，抱股觀望
    elif risk_score >= 70:
        decision, bg_color, shadow_color = "🟡 警訊浮現、支撐仍在：外圍風向開始變了（風險達80分），好在 0050 股價還踩得很穩。不用嚇自己，繼續抱著觀察！", "#D97706", "rgba(217, 119, 6, 0.5)"
    
    # 狀態 5：真正內外皆安的安全水域
    else:
        decision, bg_color, shadow_color = "✅ 盤勢非常健康：內外指標都很安全，沒有明顯風險，安心抱著就好！", "#166534", "rgba(22, 101, 52, 0.5)"

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
    print("分析完成並成功寫入 JSON！")

if __name__ == "__main__":
    run_analysis()
