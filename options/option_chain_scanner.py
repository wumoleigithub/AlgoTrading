# options/option_chain_scanner.py
from ib_insync import *
from options.option_chain_utils import get_option_chain_params

def scan_option_chain_with_greeks(
        symbol: str,
        expiry: str | None = None,
        delta_range: tuple = (0.6, 0.8),
        strike_buffer: float = 10,
        max_tickers: int = 200
    ):
    """
    1. 先调用 get_option_chain_params 拿到 strikes / expirations / tradingClass
    2. 生成期权 Contract 列表
    3. 用 snapshot 方式批量拉取 Greeks
    4. 按 delta_range 过滤并返回列表
    """
    # ---------- Step-0 连接 ----------
    util.startLoop()           # 若在脚本里可省；在 notebook 需启动事件循环
    ib = IB()
    ib.connect("127.0.0.1", 7497, clientId=123)

    # ---------- Step-1 取 Option Chain 参数 ----------
    chain = get_option_chain_params(symbol)
    if not chain:
        ib.disconnect()
        return []

    trading_class = chain["tradingClass"]
    expirations   = sorted(chain["expirations"])
    strikes_all   = sorted(chain["strikes"])

    # 若未指定 expiry，则取最近到期日
    if expiry is None:
        expiry = expirations[0]
    elif expiry not in expirations:
        print(f"⚠️ 指定 expiry {expiry} 不在合法列表，改用最近 {expirations[0]}")
        expiry = expirations[0]

    # ---------- Step-2 获取标的最新价来确定 strike 窗口 ----------
    underlying = Stock(symbol, "SMART", "USD")
    [u_ticker] = ib.reqTickers(underlying)
    price = u_ticker.last or u_ticker.marketPrice()

    strikes = [s for s in strikes_all if price-strike_buffer < s < price+strike_buffer]

    # ---------- Step-3 构建 Contract 列表 ----------
    contracts = [
        Option(symbol, expiry, strike, right, "SMART", tradingClass=trading_class)
        for strike in strikes
        for right in ("C", "P")
    ][:max_tickers]         # 防止一次请求过多

    ib.qualifyContracts(*contracts)

    # ---------- Step-4 请求 snapshot Greeks ----------
    tickers = ib.reqTickers(*contracts)
    results = []
    for tk in tickers:
        g = tk.modelGreeks
        if g and g.delta is not None:
            if delta_range[0] <= abs(g.delta) <= delta_range[1]:
                results.append({
                    "symbol": tk.contract.localSymbol,
                    "expiry": tk.contract.lastTradeDateOrContractMonth,
                    "strike": tk.contract.strike,
                    "right": tk.contract.right,
                    "price": tk.marketPrice(),
                    "delta": g.delta,
                    "gamma": g.gamma,
                    "vega": g.vega,
                    "theta": g.theta,
                    "iv": g.impliedVol
                })

    ib.disconnect()
    return results


# ---------------- Demo ----------------
# if __name__ == "__main__":
#     chain = scan_option_chain_with_greeks(
#         symbol="SPY",
#         expiry=None,          # 最近到期日
#         delta_range=(0.65, 0.75),
#         strike_buffer=15
#     )
#     for row in chain:
#         print(row)
