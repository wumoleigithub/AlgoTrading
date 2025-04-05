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