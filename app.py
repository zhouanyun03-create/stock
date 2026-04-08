import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests

# ==========================================
# 核心 1：自動抓取全台股「股票代碼」清單
# ==========================================
@st.cache_data(ttl=86400) # 每天只抓一次清單，加快速度
def get_all_taiwan_stocks():
    try:
        # 抓取上市股票名單
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        res = requests.get(url)
        dfs = pd.read_html(res.text)
        df = dfs[0]
        df.columns = df.iloc[0]
        df = df.iloc[2:]
        # 清理資料，只拿出代號
        df['代號'] = df['有價證券代號及名稱'].astype(str).apply(lambda x: x.split('\u3000')[0])
        # 只保留普通股 (ESVTFR)
        stock_list = df[df['CFICode'] == 'ESVTFR']['代號'].tolist()
        return [s for s in stock_list if len(s) == 4] # 確保代號是4碼數字
    except Exception as e:
        # 如果證交所網站剛好在維護，提供台灣市值前段班作為備用名單
        return ["2330", "2317", "2454", "2382", "2308", "2881", "2891", "2412", "2886", "2882"] 

# ==========================================
# 核心 2：抓取單一股票財報並計算 (財報狗 6 步驟邏輯)
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
st.set_page_config(page_title="全市場績優股雷達", page_icon="🎯", layout="wide")

st.title("🎯 全市場績優股雷達")
st.write("自動連線證交所抓取名單，過濾出被低估的現金流好公司。")

# 獲取全市場名單
all_stocks = get_all_taiwan_stocks()
total_stocks_count = len(all_stocks)

st.info(f"📊 目前證交所上市普通股總計： **{total_stocks_count}** 檔")

# 互動拉桿：預設幫你設定在 100 檔
scan_limit = st.slider("請選擇本次要掃描的股票數量：", min_value=10, max_value=total_stocks_count, value=100, step=10)

if st.button("🚀 開始自動掃描"):
    
    target_stocks = all_stocks[:scan_limit]
    st.warning(f"☕ 正在為您掃描前 {scan_limit} 檔股票，這大約需要 1 分鐘，請喝杯咖啡稍候...")
    
    results = []
    
    # 建立進度條與狀態文字
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, stock in enumerate(target_stocks):
        status_text.text(f"🔍 正在掃描第 {i+1} / {scan_limit} 檔： {stock}")
        
        data = fetch_and_calculate(stock)
        if data:
            results.append(data)
            
        progress_bar.progress((i + 1) / scan_limit)
        time.sleep(0.3) # 停頓 0.3 秒防止被 Yahoo 封鎖 IP

    status_text.empty()

    if results:
        df = pd.DataFrame(results)
        
        # 執行 6 步驟篩選邏輯
        df = df[df['本益比(PE)'] > 0]
        df_step1 = df[df['今年FCF報酬率(%)'] >= df['去年FCF報酬率(%)']]
        df_step2 = df_step1[df_step1['3年平均FCF報酬率(%)'] > 0]
        
        if df_step2.empty:
            st.error("掃描完成。但在您選擇的範圍內，今天沒有股票通過嚴格的現金流標準喔！")
        else:
            # 計算排名
            df_step2['PB排名'] = df_step2['股價淨值比(PB)'].rank(ascending=True)
            df_step2['PE排名'] = df_step2['本益比(PE)'].rank(ascending=True)
            df_step2['殖利率排名'] = df_step2['殖利率(%)'].rank(ascending=False)
            df_step2['綜合總分'] = df_step2['PB排名'] + df_step2['PE排名'] + df_step2['殖利率排名']
            
            final_list = df_step2.sort_values(by='綜合總分')
            
            st.success(f"🎉 掃描完成！從 {scan_limit} 檔股票中，為您淬鍊出以下績優股：")
            
            # 顯示漂亮的表格
            display_cols = ['代號', '股價', '綜合總分', '本益比(PE)', '股價淨值比(PB)', '殖利率(%)', '今年FCF報酬率(%)']
            st.dataframe(final_list[display_cols].style.format("{:.2f}", subset=['股價', '綜合總分', '本益比(PE)', '股價淨值比(PB)', '殖利率(%)', '今年FCF報酬率(%)']), height=400)
            
    else:
        st.error("抓取資料失敗，可能是網路連線問題，請稍後再試。")
