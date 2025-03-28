# contracts.py

from ibapi.contract import Contract
from IBKR_Connection import fetch_historical_data, connect_ibkr
import time

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
