from IBKR_Connection import connect_ibkr, disconnect_ibkr
from IBKR_Data import fetch_historical_data
from bear_trend_bar_static import  apply_bear_trend_bar
from bull_trend_bar_static import apply_bull_trend_bar



# from IBKR_Trading import place_stock_order, check_positions, close_position

# from ib_insync import *
# import pandas as pd
# import numpy as np
# import mplfinance as mpf

# from IBKR_Trading import place_stock_order, check_positions, close_position

# # ✅ TEST ORDER: Buy 10 shares of AAPL
# trade = place_stock_order("AAPL", "BUY", 10, order_type="MKT")

# # ✅ CHECK POSITIONS
# check_positions()

# # ✅ CLOSE AAPL POSITION
# close_position("AAPL")

#######################Bear Trend Bar Static Test#######################


from ib_insync import *
import pandas as pd
import numpy as np
import mplfinance as mpf

# ✅ CONFIGURATION
REALTIME_MODE = False  # Static analysis mode
DATA_PERIOD = "180 D"  
BAR_SIZE = "1 day"  # Change to "1 week" for weekly, "5 mins" for intraday

# ✅ STEP 1: Define Contract (SPY Stock)
from ibapi.contract import Contract

contract = Contract()
contract.symbol = "SPY"
contract.secType = "STK"
contract.exchange = "SMART"
contract.currency = "USD"

# ✅ STEP 2: Fetch Historical Data (Daily, Weekly, or Intraday)
df = fetch_historical_data(contract, bar_size=BAR_SIZE, duration=DATA_PERIOD)

# ✅ STEP 3: Apply Trend Bar Detection
if df.empty:
    print("❌ 无法获取数据，无法绘图")
else:
    df = apply_bull_trend_bar(df)
    df = apply_bear_trend_bar(df)
    df.sort_index(inplace=True)
    df["BullTrendBar"] = df["BullTrendBar"].fillna(False)
    df["BearTrendBar"] = df["BearTrendBar"].fillna(False)

# ✅ STEP 4: Highlight Trend Bars
 # 关键修复：用np.where生成完全匹配的数据序列
    highlight_bull_data = pd.Series(
        np.where(df["BullTrendBar"], df["low"], np.nan),
        index=df.index
    )

    highlight_bull = mpf.make_addplot(
        highlight_bull_data,
        type='scatter', markersize=100, marker='^', color='green', alpha=0.7
    )

    highlight_bear_data = pd.Series(
        np.where(df["BearTrendBar"], df["high"], np.nan),
        index=df.index
    )

    highlight_bear = mpf.make_addplot(
        highlight_bear_data,
        type='scatter', markersize=100, marker='v', color='red', alpha=0.7
    )




## STEP 5: Plot Candlestick Chart
# 绘图
    mpf.plot(
        df,
        type="candle",
        style="charles",
        addplot=[highlight_bull,highlight_bear]
    )

print("✅ Static Bear Trend Bar Analysis Completed!")


