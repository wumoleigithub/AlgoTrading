from IBKR_Connection import connect_ibkr
from definitions import load_definitions
import pandas as pd
import numpy as np

# ✅ Load Configuration
config = load_definitions()
BEAR_CONFIG = config["BearTrendBar"]
BODY_RATIO_THRESHOLD = BEAR_CONFIG["conditions"]["body_ratio"]["value"]
LOOKBACK_BARS = BEAR_CONFIG["conditions"]["total_range_comparison"]["lookback_period"]

def is_bear_trend_bar(idx, row, df):
    if idx < LOOKBACK_BARS:
        return False  

    body = row["open"] - row["close"]  # Bearish body
    total_range = row["high"] - row["low"]

    if total_range == 0:
        return False  

    body_ratio = abs(body) / total_range

    avg_total_range = (df.loc[idx-LOOKBACK_BARS:idx-1, "high"] - df.loc[idx-LOOKBACK_BARS:idx-1, "low"]).mean()

    return (
        row["close"] < row["open"] and
        body_ratio >= BODY_RATIO_THRESHOLD and 
        total_range > avg_total_range
    )

def apply_bear_trend_bar(df):
    df = df.reset_index(drop=False)
    df["BearTrendBar"] = [is_bear_trend_bar(i, row, df) for i, row in df.iterrows()]
    df.set_index("date", inplace=True)
    return df
