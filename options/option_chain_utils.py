# options/option_chain_utils.py

from ibapi.contract import Contract
from IBKR_Connection import connect_ibkr, fetch_contract_details
import time


def request_option_chain_params(symbol: str):
    """
    使用 IBKR 官方 API 获取 option chain 元数据（如 strikes、expiry、tradingClass 等）。
    """

    ib = connect_ibkr()
    if ib is None:
        raise RuntimeError("❌ 无法连接 IBKR")

    # ✅ 获取 conId 和 exchange
    stock = Contract()
    stock.symbol = symbol
    stock.secType = "STK"
    stock.currency = "USD"
    stock.exchange = "SMART"

    details = fetch_contract_details(stock)
    if not details:
        raise RuntimeError(f"❌ 获取 {symbol} 合约详情失败")

    conId = details[0].contract.conId
    exchange = details[0].contract.exchange or "SMART"
    secType = details[0].contract.secType

    # ✅ 申请参数
    req_id = ib.dispatcher.next_id()
    ib.dispatcher.register(req_id)

    ib.reqSecDefOptParams(
        reqId=req_id,
        underlyingSymbol=symbol,
        # futFopExchange=exchange,
        futFopExchange='',
        underlyingSecType=secType,
        underlyingConId=conId
    )

    result = ib.dispatcher.wait(req_id, timeout=5)
    ib.dispatcher.clear(req_id)

    if not result:
        print("⚠️ 未收到 option chain 响应")
        return None

    # ✅ 返回第一个 OptionChain（一般就是唯一的）
    return result[0] if isinstance(result, list) else result
