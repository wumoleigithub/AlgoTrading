import time
import numpy as np
import pandas as pd
from datetime import datetime
from IBKR_Connection import get_ibkr_price
from utils.contracts import get_vix_contract, create_vx_contract
from config.constants import TRADING_DAYS_PER_YEAR

def get_realtime_vix():
    """
    获取 VIX 指数的快照价格。
    """
    return get_ibkr_price(get_vix_contract())

def get_realtime_vx(expiry: str = None) -> float:
    """
    获取某个月份的 VIX 期货（VX）价格
    """
    contract = create_vx_contract(expiry)

    return get_ibkr_price(contract)

def get_realtime_vix_and_vx(front_month: str = None):
    """
    同时获取 VIX 与 VX 当前快照价格。
    """
    vix_price = get_realtime_vix()
    vx_price = get_realtime_vx(front_month)
    return vix_price, vx_price

def calculate_hv(df, period=20):
    """
    计算历史波动率,结果与TradingView不一致，目前不清楚原因
    """
    # 计算对数收益率
    log_returns = np.log(df['close'] / df['close'].shift(1))
    
    # 计算滚动标准差
    rolling_std = log_returns.rolling(window=period).std()
    
    # 取最后一个有效值并年化
    hv = rolling_std.iloc[-1] * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
    
    return round(hv, 2)

