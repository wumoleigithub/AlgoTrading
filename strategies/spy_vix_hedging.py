
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.volatility_data import get_realtime_vix_and_vx, calculate_hv
from IBKR_Data import fetch_stock_data, fetch_index_data

vix, vx = get_realtime_vix_and_vx()
print(f"VIX: {vix:.2f}, VX: {vx:.2f}")

# 获取历史价格数据（过去30个交易日）
spy_df = fetch_stock_data("SPY", duration="30 D", bar_size="1 day")
vix_df = fetch_index_data("VIX", duration="30 D", bar_size="1 day")

# print(spy_df["close"])
# print(vix_df["close"])

# 计算 20 日 Historical Volatility
# spy_hv = calculate_hv(spy_df["close"], window=20)
# vix_hv = calculate_hv(vix_df["close"], window=20)

vix_hv = calculate_hv(vix_df, period=20)
spy_hv = calculate_hv(spy_df, period=20)

print(f"📊 SPY 20日 HV: {spy_hv}%")
print(f"📊 VIX 20日 HV: {vix_hv}%")