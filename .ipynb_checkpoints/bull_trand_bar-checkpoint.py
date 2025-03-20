# 'Bull Trend Bar（多头趋势柱）' is a bar that closes higher than the open price. It is a bullish bar that indicates the price has increased during the period.
# JSON：
# {  

# "bull_bar": {  

# "description": "Bull Bar（阳线）是指收盘价高于开盘价的 K 线，表示该周期价格上涨。",  

# "conditions": {  

# "close": { "operator": ">", "target": "open" },  

# "body": { "formula": "close - open", "operator": ">", "value": 0 }, 

# "upper_shadow": { "formula": "high - max(open, close)", "optional": true }, "lower_shadow": { "formula": "min(open, close) - low", "optional": true }  

# } 

# } 

# }  
#根据定义和JSON，实现以下功能：1. SPY日线最近30天数据，找出所有bull trend bar；2.划出K线图，在每条多头趋势线下用向上绿箭头标出#

import yfinance as yf
import pandas as pd
import mplfinance as mpf
import numpy as np

# 获取 SPY 最近 30 天日线数据
ticker = "SPY"
spy = yf.Ticker(ticker)
data = spy.history(period="1mo")  # 获取最近 1 个月数据

# 计算 Bull Trend Bar 逻辑
def is_bull_trend_bar(row):
    """ 判断当前 K 线是否符合 Bull Trend Bar 的定义 """
    body = row["Close"] - row["Open"]
    upper_shadow = row["High"] - max(row["Open"], row["Close"])
    lower_shadow = min(row["Open"], row["Close"]) - row["Low"]
    
    # Bull Trend Bar 逻辑：主体大于 80%（即最小占比）
    percent = 0.7
    body_size = abs(body)
    total_range = row["High"] - row["Low"]
    
    return (row["Close"] > row["Open"]) and (body_size / total_range >= 0.8)

# 筛选 Bull Trend Bar
data["BullTrendBar"] = data.apply(is_bull_trend_bar, axis=1)

# 找出 Bull Trend Bar 位置
bull_bars = data[data["BullTrendBar"]]

# 绘制 K 线图
fig, ax = mpf.plot(
    data, 
    type="candle", 
    style="charles",
    volume=False, 
    figsize=(10,6),
    returnfig=True
)

# 添加绿色向上箭头标注
for idx in bull_bars.index:
    ax[0].annotate("↑", 
                   (idx, bull_bars.loc[idx, "Low"] - 0.5), 
                   color="green", 
                   fontsize=12, 
                   ha="center")

# 显示图表
mpf.show()