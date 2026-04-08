import yfinance as yf
import pandas as pd
import numpy as np
import time

# ==========================================
# 核心模組：抓取單一股票資料並計算指標 (包含強力防呆)
# ==========================================
def fetch_and_calculate(stock_id):
    ticker_symbol = f"{stock_id}.TW"
    
    try:
        # 1. 連線抓取資料
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 【防呆 1】檢查是否有基本報價，若無代表此代碼無效或下市
        current_price = info.get('currentPrice')
        market_cap = info.get('marketCap')
        if not current_price or not market_cap:
            return None
            
        # 2. 抓取 Yahoo 算好的基本面指標 (比自己除更穩定)
        # 【防呆 2】如果沒有數字，給予 NaN (空值) 交給後面 Pandas 處理
        pe_ratio = info.get('trailingPE', np.nan)
        pb_ratio = info.get('priceToBook', np.nan)
        div_yield = (info.get('dividendYield', 0) * 100) if info.get('dividendYield') else 0
        
        # 3. 處理自由現金流 (FCF)
        cf = ticker.cashflow
        # 【防呆 3】檢查現金流量表是否存在，且是否有 FCF 欄位
        if cf.empty or 'Free Cash Flow' not in cf.index:
            return None
            
        fcf_data = cf.loc['Free Cash Flow'].dropna()
        # 【防呆 4】至少需要兩年的財報才能比較「今年 vs 去年」
        if len(fcf_data) < 2:
            return None
            
        # 計算 FCF 報酬率 (自由現金流 / 當前市值)
        fcf_yield_history = (fcf_data / market_cap) * 100
        
        current_fcf_yield = fcf_yield_history.iloc[0]
        last_year_fcf_yield = fcf_yield_history.iloc[1]
        avg_3y_fcf_yield = fcf_yield_history.head(3).mean() if len(fcf_yield_history) >= 3 else current_fcf_yield

        # 將成功算出的資料打包成字典
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
        
    except Exception as e:
        # 【終極防呆】發生任何預期外的網路或運算錯誤，直接回傳 None，保護程式不中斷
        return None

# ==========================================
# 主程式：執行 6 步驟漏斗篩選
# ==========================================
if __name__ == "__main__":
    print("啟動績優股掃描器...\n")
    
    # 測試名單 (你未來可以換成全台股清單，這裡用大型股測試速度)
    test_stocks = ["2330", "2317", "2454", "2881", "1301", "2002", "1216", "2308", "2891", "2603", "2382", "3231"]
    
    results = []
    
    # 批次抓取資料
    for stock in test_stocks:
        print(f"正在分析 {stock}...")
        data = fetch_and_calculate(stock)
        if data:
            results.append(data)
        time.sleep(0.5) # 暫停 0.5 秒，避免狂發請求被 Yahoo 封鎖
        
    # 將結果轉為強大的 Pandas 表格
    df = pd.DataFrame(results)
    
    print("\n--- 開始執行 6 步驟篩選 ---\n")
    
    # 【資料清理】剔除本益比為空值或負數的公司 (賠錢公司不看本益比)
    df = df[df['本益比(PE)'] > 0].copy()
    
    # 步驟 1：排除自由現金流報酬率下滑的公司
    # 邏輯：保留 今年 >= 去年 的公司
    df_step1 = df[df['今年FCF報酬率(%)'] >= df['去年FCF報酬率(%)']].copy()
    
    # 步驟 2：挑出 3 年平均自由現金流報酬率高的公司
    # 邏輯：保留報酬率大於 0 的公司 (由於測試樣本少，這裡不硬性切前 20%)
    df_step2 = df_step1[df_step1['3年平均FCF報酬率(%)'] > 0].copy()
    
    if df_step2.empty:
        print("目前沒有股票符合步驟 1 和步驟 2 的嚴格現金流條件。")
    else:
        # 步驟 3：根據股價淨值比排名 (越小越好 -> ascending=True)
        df_step2['PB排名'] = df_step2['股價淨值比(PB)'].rank(ascending=True)
        
        # 步驟 4：根據本益比排名 (越小越好 -> ascending=True)
        df_step2['PE排名'] = df_step2['本益比(PE)'].rank(ascending=True)
        
        # 步驟 5：根據股息殖利率排名 (越大越好 -> ascending=False)
        df_step2['殖利率排名'] = df_step2['殖利率(%)'].rank(ascending=False)
        
        # 步驟 6：綜合排名 (分數越小越前面)
        df_step2['綜合總分'] = df_step2['PB排名'] + df_step2['PE排名'] + df_step2['殖利率排名']
        
        # 依照總分由小到大排序
        final_list = df_step2.sort_values(by='綜合總分')
        
        # 整理輸出格式，讓數字更好看
        pd.options.display.float_format = '{:.2f}'.format
        output_columns = ['代號', '股價', '綜合總分', '本益比(PE)', '股價淨值比(PB)', '殖利率(%)', '今年FCF報酬率(%)']
        
        print("🎯 今日績優股最終排名 (分數越低越好)：")
        print(final_list[output_columns].to_string(index=False))
