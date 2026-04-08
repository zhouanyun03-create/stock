import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests # 確保這行有加在最上面

# ==========================================
# 建立一個「偽裝版」的網路連線通道給 yfinance 使用
# ==========================================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
})

# ==========================================
# 核心 2：抓取單一股票財報並計算 (加入面具版)
# ==========================================
@st.cache_data(ttl=3600) 
def fetch_and_calculate(stock_id):
    ticker_symbol = f"{stock_id}.TW"
    try:
        # 【關鍵修改】在這裡加上 session=session，用偽裝通道去抓資料
        ticker = yf.Ticker(ticker_symbol, session=session)
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
