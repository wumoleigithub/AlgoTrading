# spy_vix_hedging.py
import sys
import os
import argparse
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.volatility_data import get_realtime_vix_and_vx, calculate_hv
from utils.contracts import create_stock_contract,create_option_contract,fetch_contract_details
from IBKR_Data import fetch_stock_data, fetch_index_data
from IBKR_Connection import connect_ibkr, get_ibkr_price
from utils.date_utils import get_monthly_vix_expiry_date, find_valid_spy_expiry

def parse_args():
    parser = argparse.ArgumentParser(description="SPY-VIX Hedging Strategy Runner")
    parser.add_argument("--mode", type=str, choices=["paper", "live"], default="paper", help="Trading mode (paper/live)")
    # parser.add_argument("--mode", type=str, choices=["paper", "live"], default="live", help="Trading mode (paper/live)")
    # parser.add_argument("--date", type=str, default=datetime.today().strftime("%Y-%m-%d"), help="Trading date (YYYY-MM-DD)")
    parser.add_argument("--delta", type=float, default=0.7, help="Target delta for option selection")
    return parser.parse_args()

def calculate_hedge_ratio(spy_price, spy_hv, vix_price, vix_hv):
    if spy_price == 0 or spy_hv == 0:
        return None
    return (vix_price * vix_hv) / (spy_price * spy_hv)

if __name__ == "__main__":
    # ✅ 解析命令行参数
    args = parse_args()

    # ✅ 自动读取参数
    mode = args.mode
    # trade_date = args.date
    target_delta = args.delta
    #🗓️ 本月 VIX 标准到期日
    vix_expiry = get_monthly_vix_expiry_date()
    print(f"🗓️ VIX expiry date: {vix_expiry}")

      # ✅ 连接 IBKR
    connect_ibkr(mode=mode)
    if not connect_ibkr(mode=mode):
        print("❌ 无法连接到 IBKR，退出。")
        exit()

    # 🗓️ SPY 最近可用的到期日
    spy_expiry = find_valid_spy_expiry(vix_expiry)
    print(f"🗓️ SPY expiry date: {spy_expiry}")
    
    print(f"🚀 Mode: {mode}")
    print(f"🎯 Target Delta: {target_delta}")

    # ✅ 获取实时价格
    vix_price, vx_price = get_realtime_vix_and_vx()

    # ✅ 检查触发条件
    premium = vix_price - vx_price
    print(f"VIX - VX Premium: {premium:.2f}")

    if premium <= 3:
        print("❌ No trade setup: VIX premium over VX is not enough (> 3 required).")
        # exit() # Uncomment this line to exit if the condition is not met

    spy_contract = create_stock_contract("SPY")
    spy_price = get_ibkr_price(spy_contract)

    if spy_price == -1 or vix_price == -1:
        print("❌ 无法获取实时价格，退出。")
        exit()

    print(f"📈 当前价格 - SPY: {spy_price:.2f}, VIX: {vix_price:.2f}")

    # ✅ 获取历史波动率
    spy_df = fetch_stock_data("SPY", duration="30 D", bar_size="1 day")
    vix_df = fetch_index_data("VIX", duration="30 D", bar_size="1 day")

    spy_hv = calculate_hv(spy_df, period=20)
    vix_hv = calculate_hv(vix_df, period=20)

    print(f"📊 SPY 20日 HV: {spy_hv:.2f}%")
    print(f"📊 VIX 20日 HV: {vix_hv:.2f}%")

    # ✅ 计算对冲比例
    ratio = calculate_hedge_ratio(spy_price, spy_hv, vix_price, vix_hv)
    if ratio is not None:
        print(f"⚖️ Hedge Ratio (VIX/SPY) = {ratio:.2f} : 1")
    else:
        print("❌ 无法计算对冲比例")


   


    # ✅ 查找期权
    # spy_option = find_option_by_delta("SPY", spy_expiry, right="C", target_delta=target_delta)
    # if not spy_option:
    #     print(f"🟢 找到 SPY Option:\n{spy_option}")
    # else:
    #     print("❌ 没有找到符合条件的 SPY Option")

    # vix_option = find_option_by_delta("VIX", vix_expiry, right="C", target_delta=target_delta)
    # if not vix_option:
    #     print(f"🟢 找到 VIX Option:\n{vix_option}")
    # else:
    #     print("❌ 没有找到符合条件的 VIX Option")


    # # ✅ ：推荐建仓头寸
    # if not spy_option.empty and not vix_option.empty:
    #     spy_strike = spy_option.iloc[0]['strike']
    #     spy_expiry = spy_option.iloc[0]['expiry']
    #     vix_strike = vix_option.iloc[0]['strike']
    #     vix_expiry = vix_option.iloc[0]['expiry']

    #     # 默认假设 1 手 SPY，对应 Ratio 手 VIX
    #     base_spy_qty = 1
    #     base_vix_qty = max(1, round(ratio))  # 保证至少1张

    #     print("\n🛡️ Hedging Plan Recommendation:")
    #     print(f"- Buy {base_spy_qty}x SPY {spy_expiry} {spy_strike} Call")
    #     print(f"- Buy {base_vix_qty}x VIX {vix_expiry} {vix_strike} Call")
    #     print(f"(Hedge Ratio approximately {ratio:.2f} : 1)")
    # else:
    #     print("\n⚠️ Unable to generate hedging recommendation (missing options)")

