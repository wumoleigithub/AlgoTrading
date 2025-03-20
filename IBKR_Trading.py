# IBKR_Trading.py
from IBKR_Connection import connect_ibkr
from ibapi.contract import Contract
from ibapi.order import Order
import time

def place_stock_order(symbol, action, quantity, order_type="MKT", limit_price=None):
    app = connect_ibkr()
    if app is None:
        print("❌ 无法连接到IBKR，取消下单")
        return None

    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'

    order = Order()
    order.action = action
    order.totalQuantity = quantity
    order.orderType = order_type
    if order_type == "LMT":
        order.lmtPrice = limit_price

    try:
        app.placeOrder(app.nextOrderId, contract, order)
        print(f"✅ 已下单: {action} {quantity}股 {symbol}")
    except Exception as e:
        print(f"❌ 下单失败: {e}")
