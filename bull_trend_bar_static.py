import pandas as pd
import numpy as np
from definitions import load_definitions

# ✅ Load Configuration
config = load_definitions()
BULL_CONFIG = config["BullTrendBar"]
BODY_RATIO_THRESHOLD = BULL_CONFIG["conditions"]["body_ratio"]["value"]
LOOKBACK_BARS = BULL_CONFIG["conditions"]["total_range_comparison"]["lookback_period"]

def is_bull_trend_bar(idx, row, df):
    """
    根据定义识别单根Bull Trend Bar (多头趋势柱)
    """
    if idx < LOOKBACK_BARS:
        return False  # 前面数据不足时不处理

    body = row["close"] - row["open"]
    total_range = row["high"] - row["low"]

    if total_range == 0:
        return False

    body_ratio = abs(body) / total_range

    avg_total_range = (
        df.loc[idx - LOOKBACK_BARS:idx - 1, "high"] - 
        df.loc[idx - LOOKBACK_BARS:idx - 1, "low"]
    ).mean()

    return (
        row["close"] > row["open"]
        and body_ratio >= BODY_RATIO_THRESHOLD
        and total_range > avg_total_range
    )

def apply_bull_trend_bar(df):
    """
    在DataFrame上应用Bull Trend Bar标识
    """
    # 为避免索引问题，首先重置索引为整数，日期变成列
    df = df.reset_index(drop=False)

    df["BullTrendBar"] = [
        is_bull_trend_bar(idx, row, df)
        for idx, row in df.iterrows()
    ]

    # 重新设置日期为索引
    df.set_index("date", inplace=True)
    
    return df

#直接运行 测试#
if __name__ == "__main__":
    from IBKR_Data import fetch_historical_data
    from ibapi.contract import Contract

    # 测试合约定义 (SPY为例)
    contract = Contract()
    contract.symbol = "SPY"
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    # 获取历史数据进行测试
    df = fetch_historical_data(contract, duration="180 D", bar_size="1 day")

    if df.empty:
        print("❌ 未获取到数据")
    else:
        df = apply_bull_trend_bar(df)
        print(df.head())
