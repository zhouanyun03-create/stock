import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# ==========================================
# 核心 1：內建 150 檔台股精選名單 (防雲端 IP 封鎖)
# ==========================================
def get_safe_stock_list():
    # 這裡包含了台灣前 150 大市值的優質公司，直接內建，不用去證交所抓！
    return [
        "2330", "2317", "2454", "2382", "2308", "2881", "2891", "2412", "2886", "2882",
        "1216", "3231", "2002", "2603", "3045", "2884", "2356", "2892", "2345", "1301",
        "3034", "1303", "2303", "2885", "3711", "2890", "5871", "2207", "2395", "5880",
        "1101", "2379", "2880", "2912", "2887", "4938", "3008", "2615", "1590", "2301",
        "1326", "2883", "6669", "3037", "2609", "1102", "1402", "3293", "2353", "2324",
        "1229", "2313", "1605", "2105", "2357", "2362", "2376", "2383", "2385", "2392",
        "2404", "2408", "2409", "2449", "2451", "2542", "2606", "2610", "2618", "2809",
        "2812", "2834", "2845", "2888", "2889", "2903", "2915", "3019", "3044", "3443",
        "3481", "3532", "3653", "3661", "3702", "4904", "4915", "4958", "5522", "6176",
        "6239", "6269", "6415", "6770", "8046", "8299", "8454", "8464", "9904", "9910",
        "9914", "9921", "9941", "1504", "1707", "1717", "1722", "1802", "1907", "2006",
        "2015", "2027", "2049", "2106", "2201", "2204", "2206", "2314", "2337", "2344",
        "2347", "2352", "2354", "2360", "2371", "2373", "2377", "2439", "2448", "2474",
        "2489", "2492", "2504", "2511", "2548", "2601", "2607", "2614", "2633", "2707",
        "2723", "2727", "2855", "2887", "3005", "3010", "3014", "3023", "3051", "3209"
    ]

# ==========================================
# 核心 2：抓取單一股票財報並計算
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
# 網頁介面設計
# ==========================================
st.set_page_config(page_title="績優股雷達 (精選150檔)", page_icon="🎯", layout="wide")

st.title("🎯 績優股雷達 (防護加強版)")
st.write("內建台股前 150 大優質公司名單，穩定快速過濾出現金流好公司。")

all_stocks = get_safe_stock_list()
total_stocks_count = len(all_stocks)

st.info(f"📊 內建精選觀察名單總計： **{total_stocks_count}** 檔 (免連線證交所，速度更快！)")

scan_limit = st.slider("請選擇本次要掃描的股票數量：", min_value=10, max_value=total_stocks_count, value=50, step=10)

if st.button("🚀 開始自動掃描"):
    
    target_stocks = all_stocks[:scan_limit]
    st.warning(f"☕ 正在為您掃描前 {scan_limit} 檔股票，請稍候...")
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, stock in enumerate(target_stocks):
        status_text.text(f"🔍 正在抓取財報，第 {i+1} / {scan_limit} 檔： {stock}")
        
        data = fetch_and_calculate(stock)
        if data:
            results.append(data)
            
        progress_bar.progress((i + 1) / scan_limit)
        time.sleep(0.5) # 稍微加長一點休息時間，避免被 Yahoo 踢掉

    status_text.empty()

    if results:
        df = pd.DataFrame(results)
        
        df = df[df['本益比(PE)'] > 0]
        df_step1 = df[df['今年FCF報酬率(%)'] >= df['去年FCF報酬率(%)']]
        df_step2 = df_step1[df_step1['3年平均FCF報酬率(%)'] > 0]
        
        if df_step2.empty:
            st.error("掃描完成。但在這批名單中，今天沒有股票通過現金流標準喔！")
        else:
            df_step2['PB排名'] = df_step2['股價淨值比(PB)'].rank(ascending=True)
            df_step2['PE排名'] = df_step2['本益比(PE)'].rank(ascending=True)
            df_step2['殖利率排名'] = df_step2['殖利率(%)'].rank(ascending=False)
            df_step2['綜合總分'] = df_step2['PB排名'] + df_step2['PE排名'] + df_step2['殖利率排名']
            
            final_list = df_step2.sort_values(by='綜合總分')
            
            st.success(f"🎉 掃描完成！從 {scan_limit} 檔股票中，淬鍊出以下績優股：")
            display_cols = ['代號', '股價', '綜合總分', '本益比(PE)', '股價淨值比(PB)', '殖利率(%)']
            st.dataframe(final_list[display_cols].style.format("{:.2f}", subset=['股價', '綜合總分', '本益比(PE)', '股價淨值比(PB)', '殖利率(%)']), height=400)
            
    else:
        st.error("抓取資料失敗。Yahoo 財經可能暫時限制了雲端主機的連線，請過幾分鐘後再試。")
