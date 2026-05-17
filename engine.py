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
    last_trading_date = "未知"
    fetch_success = False

    try:
        # 下載歷史資料庫
        df = yf.download("0050.TW", period="6mo")
        
        if not df.empty:
            # 【終極核心修復】：如果欄位是新版的多層結構，強制降維扁平化，徹底根絕 KeyError
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 確保精確採用還原收盤價
            if 'Adj Close' in df.columns:
                df['Close'] = df['Adj Close']
            
            df = df.dropna(subset=['Close'])
            
            if not df.empty:
                df['20MA'] = df['Close'].rolling(window=20).mean()
                valid_ma_df = df.dropna(subset=['20MA'])
                
                # 紀錄資料庫中最後一筆有效的交易日期
                last_trading_date = df.index[-1].strftime('%Y-%m-%d')
                
                current_price = float(df['Close'].iloc[-1])
                ma20 = float(valid_ma_df['20MA'].iloc[-1]) if not valid_ma_df.empty else current_price
                high_water_mark = float(df['Close'].max())
                drawdown_pct = float(((high_water_mark - current_price) / high_water_mark) * 100) if high_water_mark > 0 else 0.0
                
                if not math.isnan(current_price) and not math.isnan(ma20):
                    fetch_success = True
    except Exception as e:
        print(f"數據抓取異常: {e}")

    # 模擬大環境指標
    signals = {"US_Yield_Inversion": True, "TW_Foreign_Short": True, "TW_Margin_Overheat": False,
               "US_Speculative_Crash": True, "US_Valuation_Bubble": True, "TW_Tech_Divergence": True}
    
    risk_score = int(sum(WEIGHTS[k] for k, v in signals.items() if v))
    
    env_risk = bool(risk_score >= 85)
    trend_broken = bool(current_price < ma20) if fetch_success else False
    damage_taken = bool(drawdown_pct >= 7.0) if fetch_success else False

    # 決策橫幅文字與燈號
    if not fetch_success:
        decision, bg_color, shadow_color = "⚠️ 數據格式同步異常，等待雲端修正中", "#374151", "rgba(55, 65, 81, 0.5)"
    elif env_risk and trend_broken and damage_taken:
        decision, bg_color, shadow_color = "🚨 危險！強烈建議先跑：市場全面轉弱，先賣出保留現金，等穩定了再說！", "#991B1B", "rgba(153, 27, 27, 0.5)"
    elif env_risk:
        decision, bg_color, shadow_color = "⚠️ 大環境非常惡劣：市場隨時有雪崩風險！絕對不要再加碼，盯緊月線準備閃人！", "#B45309", "rgba(180, 83, 9, 0.5)"
    elif trend_broken or damage_taken:
        decision, bg_color, shadow_color = "👀 價格走勢轉弱：已經跌破重要支撐，先停看聽，不要急著伸手接刀。", "#4B5
