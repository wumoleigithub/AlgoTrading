# Entry point for historical backtesting
from options.option_data_fetcher import fetch_option_data, get_available_option_strikes, get_single_option_data

# ✅ 获取可用的期权执行价,只能获得未来数据
# df_strikes = get_available_option_strikes("SPY", "2025-04-14")
# print(df_strikes.head(20))

################################################################
#获取单一期权的历史数据
df = get_single_option_data(
    symbol="SPY",
    expiry="2024-03-15",
    strike=560,
    right="C",
    duration="60 D",
    bar_size="1 day",
    end_datetime=""  # 默认当前时间
)

print(df.tail())


#next: 根据 strike 和 trade date 获取期权在某日的日内数据数据
# learn copilot
