# utils/volatility_data.py

from IBKR_Connection import connect_ibkr
from ibapi.contract import Contract
import time
import datetime

def get_ibkr_price(contract: Contract, timeout: int = 5) -> float:
    """
    请求 IBKR 实时市场价格（中间价），用于指数或期货。
    """
    ib = connect_ibkr()
    if ib is None:
        return -1

    #to be changed
    ib.reqMktData(1, contract, "", False, False, [])

    price = None
    waited = 0
    while waited < timeout:
        tickers = ib.tickerSnapshot(1, contract, snapshot=True)
        if tickers:
            ticker = tickers[0]
            price = ticker.marketPrice()
            if price > 0:
                break
        time.sleep(1)
        waited += 1

    ib.cancelMktData(1)
    return price

def get_realtime_vix() -> float:
    """获取 VIX 指数的实时价格。"""
    vix = Contract()
    vix.symbol = "VIX"
    vix.secType = "IND"
    vix.exchange = "CBOE"
    vix.currency = "USD"
    return get_ibkr_price(vix)

def get_realtime_vx(month_code: str) -> float:
    """
    获取指定月份 VX 期货的实时价格。
    参数 month_code 示例："202404" 表示 2024 年 4 月合约。
    """
    vx = Contract()
    vx.symbol = "VX"
    vx.secType = "FUT"
    vx.exchange = "CFE"
    vx.currency = "USD"
    vx.lastTradeDateOrContractMonth = month_code
    return get_ibkr_price(vx)

def get_front_month_code() -> str:
    """
    自动生成最近月 VX 合约代码（格式如 "202404"）。
    若今日在月初（如1~3号），则可能使用当月，否则默认下月。
    """
    today = datetime.date.today()
    year = today.year
    month = today.month
    if today.day >= 25:
        month += 1
        if month > 12:
            month = 1
            year += 1
    return f"{year}{month:02d}"

def get_realtime_vix_and_vx(month_code: str = None):
    """
    获取 VIX 指数和指定月份（默认最近月）VX 期货的实时价格。
    """
    if month_code is None:
        month_code = get_front_month_code()

    vix_price = get_realtime_vix()
    vx_price = get_realtime_vx(month_code)
    return vix_price, vx_price

# 示例调用
# if __name__ == "__main__":
#     vix, vx = get_realtime_vix_and_vx()
#     print(f"✅ VIX Index: {vix:.2f}, VX Front Month: {vx:.2f}")
