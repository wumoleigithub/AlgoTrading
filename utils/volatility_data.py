import time
from datetime import datetime
from IBKR_Connection import get_ibkr_price, fetch_contract_details
from utils.contracts import get_vix_contract, create_vx_contract

def get_realtime_vix():
    """
    获取 VIX 指数的快照价格。
    """
    return get_ibkr_price(get_vix_contract())

# def get_realtime_vx(front_month: str = None):
#     """
#     获取 VX（VIX 期货）的快照价格。
#     若未指定 front_month，将自动获取下一个月份。
#     格式如 "2024-05"
#     """
#     return get_ibkr_price(get_vx_contract(front_month))

def get_realtime_vx(expiry: str = None) -> float:
    """
    获取某个月份的 VIX 期货（VX）价格
    """
    contract = create_vx_contract(expiry)
    # if not fetch_contract_details(contract):
    #     print(f"❌ 无效的 VX 合约：{expiry}")
    #     print(contract)
    #     return -1

    return get_ibkr_price(contract)

def get_realtime_vix_and_vx(front_month: str = None):
    """
    同时获取 VIX 与 VX 当前快照价格。
    """
    vix_price = get_realtime_vix()
    vx_price = get_realtime_vx(front_month)
    #vx_price = get_realtime_vx("2025-05-21")  # 使用指定的月份获取 VX 价格")
    return vix_price, vx_price
