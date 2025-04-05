from IBKR_Connection import fetch_historical_data, connect_ibkr, fetch_contract_details
from utils.contracts import create_option_contract, get_atm_strike, verify_contract
import pandas as pd


def fetch_option_data(
    symbol: str,
    trade_date: str,
    expiry: str,
    right: str = "both",
    strike: float | None = None,
    strike_count: int = 10,
    bar_size: str = "5 mins"  # ✅ 使用分钟级别，避免期权 EOD 数据限制
) -> pd.DataFrame:
    """
    获取指定日期的期权价格。

    如果未指定 strike，则自动寻找 ATM 附近的合约。
    返回包含 close price 的 DataFrame。
    """
    # 如果没有提供 strike，调用 utils 中的获取 ATM 工具函数
    if strike is None:
        strike = get_atm_strike(symbol, trade_date, bar_size)

    all_data = []
    rights = ["C", "P"] if right == "both" else [right.upper()]

    for r in rights:
        for offset in range(-strike_count, strike_count + 1):
            option_strike = int(round(strike + offset))
            contract = create_option_contract(symbol, expiry, option_strike, r)

            # ✅ 合约合法性验证
            if not verify_contract(contract):
                print(f"⛔ 合约无效，跳过: {symbol} {expiry} {option_strike} {r}")
                continue

            df = fetch_historical_data(
                contract=contract,
                end_datetime=trade_date.replace("-", "") + "-21:00:00",
                duration="1 D",
                bar_size=bar_size,
                what_to_show="TRADES"  # ✅ 成交价为主要展示项
            )

            if not df.empty:
                 # ✅ 聚合分钟数据为日线收盘价
                df = df.resample("1D").agg({
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum"
                }).dropna()
                
                close_price = df["close"].iloc[-1]
                all_data.append({
                    "symbol": symbol,
                    "expiry": expiry,
                    "strike": option_strike,
                    "right": r,
                    "close": close_price
                })

    return pd.DataFrame(all_data)

def get_available_option_strikes(symbol: str, expiry: str) -> pd.DataFrame:
    """
    使用 reqContractDetails 获取指定标的和到期日下所有可用的期权合约信息。
    返回一个包含 strike、right 的 DataFrame。
    """
    ib = connect_ibkr()

    from ibapi.contract import Contract
    
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "OPT"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = expiry.replace("-", "")
    #contract.includeExpired = True
    # contract.multiplier = "100"

    details = fetch_contract_details(contract)
    data = []
    for d in details:
        c = d.contract
        data.append({
            "strike": c.strike,
            "right": c.right,
            "expiry": c.lastTradeDateOrContractMonth
        })

    if not data:
        print(f"⚠️ 无可用合约返回: {symbol} {expiry}")
        return pd.DataFrame()
    
    df = pd.DataFrame(data).drop_duplicates().sort_values("strike")
    return df.reset_index(drop=True)