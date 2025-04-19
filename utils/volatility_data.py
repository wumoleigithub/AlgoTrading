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

def calculate_hv(prices: pd.Series, window: int = 20) -> float:
    """
    模拟 TradingView 风格的历史波动率计算方式：
    - 对数收益率
    - 滚动窗口 std
    - 年化 √252
    """
    log_returns = np.log(prices / prices.shift(1)).dropna()
    rolling_std = log_returns.rolling(window=window).std()
    latest_std = rolling_std.iloc[-1]
    hv = latest_std * np.sqrt(260) * 100
    return round(hv, 2)

def calculate_hv_exact(prices: pd.Series, window: int = 20) -> float:
    """
    更接近 AlphaQuery/TV 的 HV：不使用 rolling，只取最近 window 的 std
    """
    log_returns = np.log(prices / prices.shift(1)).dropna()
    if len(log_returns) < window:
        return np.nan  # 数据不足
    std_dev = log_returns[-window:].std()
    return round(std_dev * np.sqrt(252) * 100, 2)


def compute_hv_tv_style(df, period=20):
    """
    计算历史波动率（TradingView 风格）

    参数：
    df: 包含 'close' 列的 DataFrame
    period: 时间窗口，默认为 20

    返回：
    年化历史波动率（百分比）
    """
    # 计算对数收益率
    log_returns = np.log(df['close'] / df['close'].shift(1))
    
    # 计算滚动标准差
    rolling_std = log_returns.rolling(window=period).std()
    
    # 取最后一个有效值并年化
    hv = rolling_std.iloc[-1] * np.sqrt(252) * 100
    
    return round(hv, 2)

