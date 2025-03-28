# IBKR_Data.py
# from IBKR_Connection import connect_ibkr
# from ibapi.contract import Contract
# import pandas as pd
# import time

# def fetch_historical_data(contract, duration, bar_size, timeout=30):
#     app = connect_ibkr()
#     if app is None:
#         print("❌ 无法连接到IBKR")
#         return pd.DataFrame()

#     # 清空数据容器
#     app.data.clear()
    
#     app.reqHistoricalData(
#         reqId=1,
#         contract=contract,
#         endDateTime='',
#         durationStr=duration,
#         barSizeSetting=bar_size,
#         whatToShow='TRADES',
#         useRTH=1,
#         formatDate=1,
#         keepUpToDate=False,
#         chartOptions=[]
#     )

#     waited = 0
#     while not app.data and waited < timeout:
#         time.sleep(1)
#         waited += 1

#     if not app.data:
#         print("❌ 历史数据请求超时")
#         return pd.DataFrame()

#     df = pd.DataFrame(app.data)
#     df['date'] = pd.to_datetime(df['date'])
#     df.set_index("date", inplace=True)
#     return df

from IBKR_Connection import fetch_historical_data
from ibapi.contract import Contract

def fetch_stock_data(symbol, duration="30 D", bar_size="1 day"):
    """
    快速获取某个股票的历史数据，返回 DataFrame。
    """
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK" # 股票,将来可以拓展成其他类型
    contract.exchange = "SMART"
    contract.currency = "USD"

    return fetch_historical_data(
        contract=contract,
        end_datetime="",  # 默认当前时间
        duration=duration,
        bar_size=bar_size,
        what_to_show="TRADES"
    )