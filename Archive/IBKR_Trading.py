from IBKR_Connection import connect_ibkr, disconnect_ibkr
from ib_insync import *

# ✅ Connect to IBKR API
ib = connect_ibkr()

def place_stock_order(symbol, action, quantity, order_type="MKT", limit_price=None):
    """
    Places a stock order (buy/sell) on IBKR.
    
    Args:
        symbol (str): Stock ticker (e.g., "AAPL").
        action (str): "BUY" or "SELL".
        quantity (int): Number of shares.
        order_type (str): "MKT" (Market) or "LMT" (Limit).
        limit_price (float, optional): Required if order_type is "LMT".
    
    Returns:
        Order status from IBKR.
    """
    contract = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(contract)

    # ✅ Create Order
    if order_type == "LMT" and limit_price is None:
        raise ValueError("❌ Limit order requires a limit price!")

    order = MarketOrder(action, quantity) if order_type == "MKT" else LimitOrder(action, quantity, limit_price)

    # ✅ Place Order
    trade = ib.placeOrder(contract, order)
    ib.sleep(2)  # Allow IBKR to process
    print(f"📈 {action} Order for {quantity} shares of {symbol} sent!")
    
    return trade

def check_positions():
    """
    Fetches current stock positions from IBKR.
    
    Returns:
        List of active positions.
    """
    positions = ib.positions()
    if positions:
        print("\n🔍 Current Positions:")
        for pos in positions:
            print(f"{pos.contract.symbol}: {pos.position} shares @ {pos.avgCost:.2f}")
    else:
        print("🛑 No active positions.")
    return positions

def close_position(symbol):
    """
    Closes a position in a specific stock.
    
    Args:
        symbol (str): Stock ticker to close.
    """
    positions = ib.positions()
    for pos in positions:
        if pos.contract.symbol == symbol:
            action = "SELL" if pos.position > 0 else "BUY"
            place_stock_order(symbol, action, abs(pos.position))
            print(f"🛑 Closed position in {symbol}")
            return
    print(f"❌ No position found in {symbol}")

# ✅ Disconnect API when done
disconnect_ibkr(ib)
