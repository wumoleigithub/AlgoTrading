from IBKR_Connection import connect_ibkr, disconnect_ibkr
from logic.bear_trend_bar_static import fetch_historical_data, apply_bear_trend_bar
from logic.bull_trend_bar_static import fetch_historical_data, apply_bull_trend_bar
from ib_insync import *
import pandas as pd
import numpy as np
import mplfinance as mpf

# ✅ CONFIGURATION
REALTIME_MODE = False  # Static analysis mode
DATA_PERIOD = "180 D"  
BAR_SIZE = "1 day"  # Change to "1 week" for weekly, "5 mins" for intraday

# ✅ STEP 1: Define Contract (SPY Stock)
contract = Stock('SPY', 'SMART', 'USD')

# ✅ STEP 2: Fetch Historical Data (Daily, Weekly, or Intraday)
df = fetch_historical_data(contract, bar_size=BAR_SIZE, duration=DATA_PERIOD)

# ✅ STEP 3: Apply Bear Trend Bar Detection
df = apply_bear_trend_bar(df)

# ✅ STEP 4: Highlight Bear Trend Bars
highlight_bear = df["close"].where(df["BearTrendBar"], np.nan)  

highlight_plot = mpf.make_addplot(
    highlight_bear, 
    type='scatter', 
    color='#0000FF', 
    marker='o', 
    markersize=50, 
    alpha=0.5
)

# ✅ STEP 5: Plot Candlestick Chart
# mpf.plot(
#     df, 
#     type="candle", 
#     style="charles", 
#     volume=False, 
#     figsize=(12,6),
#     show_nontrading=False,
#     addplot=[highlight_plot]  
# )

print("✅ Static Bear Trend Bar Analysis Completed!")

##BUll Trend Bar Static Test##
# ✅ STEP 3: Apply Bull Trend Bar Detection
df = apply_bull_trend_bar(df)

# ✅ STEP 4: Highlight Bull Trend Bars
highlight_bull = df["close"].where(df["BullTrendBar"], np.nan)  

highlight_plot = mpf.make_addplot(
    highlight_bull, 
    type='scatter', 
    color='#FF4500',  # Orange-Red for Bull Trend Bars
    marker='o', 
    markersize=50, 
    alpha=0.5
)

# ✅ STEP 5: Plot Candlestick Chart
mpf.plot(
    df, 
    type="candle", 
    style="charles", 
    volume=False, 
    figsize=(12,6),
    show_nontrading=False,
    addplot=[highlight_plot]  
)

print("✅ Static Bull Trend Bar Analysis Completed!")