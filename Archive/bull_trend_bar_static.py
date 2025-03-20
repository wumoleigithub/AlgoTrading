from IBKR_Connection import connect_ibkr, disconnect_ibkr
from ib_insync import *
import pandas as pd
import numpy as np

# ✅ CONFIGURABLE PARAMETERS
BODY_RATIO_THRESHOLD = 0.6  # Minimum body percentage (60%)
LOOKBACK_BARS = 20  # Compare last 20 bars

def fetch_historical_data(contract, bar_size="1 day", duration="180 D"):
    """
    Fetch historical data from IBKR based on the given timeframe.
    
    Args:
        contract (Contract): The IBKR contract (e.g., Stock, Forex).
        bar_size (str): Timeframe (e.g., "1 day", "1 week", "1 hour", "5 mins").
        duration (str): Data period to fetch (e.g., "180 D", "52 W", "30 D").
        
    Returns:
        pd.DataFrame: DataFrame with historical market data.
    """
    ib = connect_ibkr()
    if not ib:
        exit("❌ Unable to connect to IBKR. Exiting...")

    print(f"📊 Fetching {bar_size} historical data for {contract.symbol} ({duration})...")
    
    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow='TRADES',
        useRTH=True,
        formatDate=1
    )

    df = util.df(bars)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index("date", inplace=True)

    disconnect_ibkr(ib)
    return df

def is_bull_trend_bar(idx, row, df):
    """
    Identify Bull Trend Bar based on given criteria.
    
    Args:
        idx (int): Index of the current row.
        row (pd.Series): The row data for the current bar.
        df (pd.DataFrame): The DataFrame containing historical bars.
        
    Returns:
        bool: True if it's a Bull Trend Bar, False otherwise.
    """
    if idx < LOOKBACK_BARS:
        return False  

    body = row.close - row.open  # Bullish body
    total_range = row.high - row.low

    if total_range == 0:
        return False  # Avoid division by zero

    body_ratio = abs(body) / total_range  

    # ✅ Use `.iloc[]` for integer-based indexing
    avg_total_range = (df.iloc[idx-LOOKBACK_BARS:idx, df.columns.get_loc("high")] - 
                       df.iloc[idx-LOOKBACK_BARS:idx, df.columns.get_loc("low")]).mean()

    return row.close > row.open and body_ratio >= BODY_RATIO_THRESHOLD and total_range > avg_total_range

def apply_bull_trend_bar(df):
    """
    Apply the Bull Trend Bar detection function to the entire DataFrame.
    
    Args:
        df (pd.DataFrame): The DataFrame containing historical market data.
        
    Returns:
        pd.DataFrame: DataFrame with an added column 'BullTrendBar' (True/False).
    """
    df["BullTrendBar"] = [is_bull_trend_bar(i, row, df) for i, row in enumerate(df.itertuples())]
    return df
