# main_back_testing.py

from options.option_data_fetcher import fetch_option_data

# ✅ 设置参数
symbol = "SPY"                    # 标的
trade_date = "2025-03-26"         # 查询交易日（格式 YYYY-MM-DD）
expiry = "2025-04-01"             # 到期日（格式 YYYY-MM-DD）
right = "both"                    # 可选："call"、"put"、"both"
strike = None                     # 若为 None，则自动查找 ATM 附近期权
strike_count = 10                 # ATM 上下各取几个 strike，总共 20 个

# ✅ 调用函数获取期权价格数据
df = fetch_option_data(
    symbol=symbol,
    trade_date=trade_date,
    expiry=expiry,
    right=right,
    strike=strike,
    strike_count=strike_count,
    bar_size="5 mins"
)

# ✅ 显示结果
if df.empty:
    print("⚠️ 无期权数据返回，请检查连接或参数。")
else:
    print(df)
