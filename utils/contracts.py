# contracts.py
import time
from datetime import datetime, timedelta
from ibapi.contract import Contract
from IBKR_Connection import fetch_historical_data, connect_ibkr, fetch_contract_details

def create_stock_contract(symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = exchange
    contract.currency = currency
    return contract

def create_option_contract(
    symbol: str,
    expiry: str,
    strike: float,
    right: str,
    exchange: str = "SMART",
    currency: str = "USD",
    multiplier: str = "100"
) -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "OPT"
    contract.exchange = exchange
    contract.currency = currency
    contract.lastTradeDateOrContractMonth = expiry.replace("-", "")  # e.g. "20240315"
    contract.strike = strike
    contract.right = right.upper()  # "C" or "P"
    contract.multiplier = multiplier
    return contract

def get_atm_strike(symbol: str, trade_date: str, bar_size: str = "1 day") -> float:
    """
    根据指定交易日获取标的收盘价作为 ATM 执行价。
    """
    contract = create_stock_contract(symbol)
    df = fetch_historical_data(
        contract=contract,
        end_datetime=trade_date.replace("-", "") + "-21:00:00",
        duration="1 D",
        bar_size=bar_size,
        what_to_show="TRADES"
    )
    if not df.empty:
        atm = round(df["close"].iloc[-1], 1)
        print(f"[INFO] 自动获取 ATM price: {atm}")
        return atm
    print("⚠️ 无法获取标的价格，使用默认 ATM 450.0")
    return 450.0

def verify_contract(contract: Contract, timeout: int = 5) -> bool:
    """
    使用 reqContractDetails 异步方式验证合约是否存在。
    """
    ib = connect_ibkr()
    result = []
    done = ib.contractDetails

    def contractDetails(reqId, contractDetails):
        result.append(contractDetails)
        ib.data_event.set()

    # 替换临时回调处理
    ib.contractDetails = contractDetails
    ib.data_event.clear()
    ib.reqContractDetails(999, contract)

    waited = 0
    while not ib.data_event.is_set() and waited < timeout:
        time.sleep(1)
        waited += 1

    return len(result) > 0

def get_vix_contract():
    contract = Contract()
    contract.symbol = "VIX"
    contract.secType = "IND"
    contract.exchange = "CBOE"
    contract.currency = "USD"
    return contract

def get_vx_contract(front_month: str = None):
    contract = Contract()
    contract.symbol = "VX"
    contract.secType = "FUT"
    contract.exchange = "CFE"
    contract.currency = "USD"
    if front_month is None:
        front_month = get_front_month_vx()
    else:
        front_month = front_month.replace("-", "")
    contract.lastTradeDateOrContractMonth = front_month
    return contract

def create_vx_contract(front_month: str = None) -> Contract:
    """
    构造 VX（VIX Futures）期货合约对象
    """
    contract = Contract()
    contract.symbol = "VXM"#############
    contract.secType = "FUT"
    contract.exchange = "CFE"  # VX 属于芝加哥期货交易所
    contract.currency = "USD"
    if front_month is None:
        front_month = get_front_month_vx()
    else:
        front_month = front_month.replace("-", "")
    contract.lastTradeDateOrContractMonth = front_month
    return contract

def get_front_month_vx():
    today = datetime.today()
    year = today.year
    month = today.month
    third_wednesday = get_third_wednesday(year, month)
    if today <= third_wednesday:
        return f"{year}{month:02d}"
    else:
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        return f"{year}{month:02d}"

# def get_front_month_vx() -> str:
#     """
#     自动获取最近一个可用的 VX（VIX Futures）月份（格式如 '202404'）
#     """
#     today = datetime.now()
#     for i in range(6):  # 向后检查最多 6 个月
#         month = today.month + i
#         year = today.year + (month - 1) // 12
#         month = (month - 1) % 12 + 1
#         expiry = f"{year}{month:02d}"

#         contract = create_vx_contract(expiry)
#         if fetch_contract_details(contract):
#             print(f"[INFO] 找到最近可用的 VX 合约：{expiry}")
#             return expiry

#     raise ValueError("未找到可用的 VX 合约")

def get_third_wednesday(year, month):
    first_day = datetime(year, month, 1)
    weekday = first_day.weekday()
    days_to_wednesday = (2 - weekday + 7) % 7
    first_wednesday = first_day + timedelta(days=days_to_wednesday)
    return first_wednesday + timedelta(weeks=2)

from IBKR_Connection import fetch_contract_details
from ibapi.contract import Contract
import pandas as pd


