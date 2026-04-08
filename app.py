import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# ==========================================
# 核心模組：抓取資料 (加入 Streamlit 快取，讓APP變超快)
# ==========================================
@st.cache_data(ttl=3600) 
def fetch_and_calculate(stock_id):
    ticker_symbol = f"{stock_id}.TW"
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        current_price = info.get('currentPrice')
        market_cap = info.get('marketCap')
        if not current_price or not market_cap: return None
            
        pe_ratio = info.get('trailingPE', np.nan)
        pb_ratio = info.get('priceToBook', np.nan)
        div_yield = (info.get('dividendYield', 0) * 100) if info.get('dividendYield') else 0
        
        cf = ticker.cashflow
        if cf.empty or 'Free Cash Flow' not in cf.index: return None
            
        fcf_data = cf.loc['Free Cash Flow'].dropna()
        if len(fcf_data) < 2: return None
            
        fcf_yield_history = (fcf_data / market_cap) * 100
        current_fcf_yield = fcf_yield_history.iloc[0]
        last_year_fcf_yield = fcf_yield_history.iloc[1]
        avg_3y_fcf_yield = fcf_yield_history.head(3).mean() if len(fcf_yield_history) >= 3 else current_fcf_yield

        return {
            '代號': stock_id,
            '股價': current_price,
            '今年FCF報酬率(%)': current_fcf_yield,
            '去年FCF報酬率(%)': last_year_fcf_yield,
            '3年平均FCF報酬率(%)': avg_3y_fcf_yield,
            '股價淨值比(PB)': pb_ratio,
            '本益比(PE)': pe_ratio,
            '殖利率(%)': div_yield
        }
    except Exception:
        return None

# ==========================================
# 網頁介面設計 (APP 前台)
# ==========================================
# 1. 設定網頁標題與圖示
st.set_page_config(page_title="績優股雷達", page_icon="🎯", layout="centered")

# 2. 顯示大標題
st.title("🎯 專屬績優股雷達")
st.write("根據財報狗 6 步驟邏輯，自動過濾並為好公司打分數。")

# 測試名單 (為了讓您馬上看到效果，先用 5 檔知名大型股測試)
test_stocks = ["2330", "2317", "2454", "2881", "2002"]

# 3. 建立一個按鈕，按下去才開始執行
if st.button("🚀 開始掃描今日名單"):
    
    # 顯示轉圈圈的讀取動畫
    with st.spinner('正在從市場抓取最新財報與股價，請稍候...'):
        results = []
        progress_bar = st.progress(0) # 顯示進度條
        
        for i, stock in enumerate(test_stocks):
            data = fetch_and_calculate(stock)
            if data:
                results.append(data)
            progress_bar.progress((i + 1) / len(test_stocks)) # 更新進度條
            time.sleep(0.5)

        if results:
            df = pd.DataFrame(results)
            
            # 執行 6 步驟篩選邏輯
            df = df[df['本益比(PE)'] > 0]
            df_step1 = df[df['今年FCF報酬率(%)'] >= df['去年FCF報酬率(%)']]
            df_step2 = df_step1[df_step1['3年平均FCF報酬率(%)'] > 0]
            
            if df_step2.empty:
                st.warning("今天沒有股票通過嚴格的現金流標準喔！")
            else:
                # 計算排名
                df_step2['PB排名'] = df_step2['股價淨值比(PB)'].rank(ascending=True)
                df_step2['PE排名'] = df_step2['本益比(PE)'].rank(ascending=True)
                df_step2['殖利率排名'] = df_step2['殖利率(%)'].rank(ascending=False)
                df_step2['綜合總分'] = df_step2['PB排名'] + df_step2['PE排名'] + df_step2['殖利率排名']
                
                final_list = df_step2.sort_values(by='綜合總分')
                
                # 顯示成功訊息
                st.success("掃描完成！以下是為您精選的績優股：")
                
                # 將資料顯示成漂亮的網頁互動表格
                display_cols = ['代號', '股價', '綜合總分', '本益比(PE)', '股價淨值比(PB)', '殖利率(%)']
                st.dataframe(final_list[display_cols].style.format("{:.2f}", subset=['股價', '綜合總分', '本益比(PE)', '股價淨值比(PB)', '殖利率(%)']))
                
                st.info("💡 總分越低，代表這家公司越便宜且現金流越健康。")
        else:
            st.error("抓取資料失敗，請稍後再試。")
