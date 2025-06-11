from ib_insync import *

def request_option_chain(symbol: str, delta_range: tuple = (0, 1), strike_buffer: float = 10):
    """
    请求指定标的的期权链和希腊值，并筛选出 Delta 在指定范围内的合约。

    参数:
        symbol (str): 标的资产，例如 'SPY'
        delta_range (tuple): 希望筛选的 delta 范围，例如 (0.6, 0.8)
        strike_buffer (float): 附近多少点以内的 strike 价格窗口

    返回:
        List[dict]: 每个期权合约及其希腊值
    """
    # util.startLoop()
    ib = IB()
    # ib.connect('127.0.0.1', 7496, clientId=1)
    ib.connect('127.0.0.1', 7497, clientId=1) #paper

    underlying = Stock(symbol, 'SMART', 'USD')
    ib.qualifyContracts(underlying)

    chains = ib.reqSecDefOptParams(underlying.symbol, '', underlying.secType, underlying.conId)
    chain = next(c for c in chains if c.exchange == 'SMART' and c.tradingClass == symbol)

    [ticker] = ib.reqTickers(underlying)
    price = ticker.marketPrice()
    expirations = sorted(chain.expirations)[:2]
    strikes = [s for s in chain.strikes if price - strike_buffer < s < price + strike_buffer]

    contracts = [
        Option(symbol, expiry, strike, right, 'SMART', tradingClass=symbol)
        for expiry in expirations
        for strike in strikes
        for right in ['C', 'P']
    ]

    ib.qualifyContracts(*contracts)
    tickers = ib.reqTickers(*contracts)

    results = []
    for ticker in tickers:
        g = ticker.modelGreeks
        if g and g.delta is not None:
            if delta_range[0] <= abs(g.delta) <= delta_range[1]:
                results.append({
                    "symbol": ticker.contract.localSymbol,
                    "expiry": ticker.contract.lastTradeDateOrContractMonth,
                    "strike": ticker.contract.strike,
                    "right": ticker.contract.right,
                    "delta": g.delta,
                    "gamma": g.gamma,
                    "vega": g.vega,
                    "theta": g.theta,
                    "iv": g.impliedVol,
                    "price": ticker.marketPrice()
                })

    ib.disconnect()
    return results
