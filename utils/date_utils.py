# utils/date_utils.py

from datetime import datetime, timedelta
from utils.contracts import Contract, fetch_contract_details

def get_monthly_vix_expiry_date(reference_date=None) -> str:
    """
    返回当前月份 VIX 月度合约的标准到期日，格式为 yyyy-mm-dd。
    VIX 标准月度期权的到期日通常是 每月第三个星期三的早上。
    """
    if reference_date is None:
        reference_date = datetime.today()

    first_day = datetime(reference_date.year, reference_date.month, 1)

    wednesdays = [
        first_day + timedelta(days=i)
        for i in range(31)
        if (first_day + timedelta(days=i)).month == reference_date.month and
           (first_day + timedelta(days=i)).weekday() == 2
    ]

    if len(wednesdays) >= 3:
        third_wednesday = wednesdays[2]
        return third_wednesday.strftime("%Y-%m-%d")
    else:
        raise ValueError("无法找到当月第三个星期三")

def find_valid_spy_expiry(target_expiry: str, max_days_forward=30) -> str:
    """
    给定一个目标 expiry (YYYY-MM-DD)，智能寻找最近的 SPY 有效到期日。
    如果找不到，抛出异常。
    """

    base_date = datetime.strptime(target_expiry, "%Y-%m-%d")

    for i in range(max_days_forward + 1):
        check_date = base_date + timedelta(days=i)
        expiry_str = check_date.strftime("%Y%m%d")

        # 构建 contract
        contract = Contract()
        contract.symbol = "SPY"
        contract.secType = "OPT"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = expiry_str

        details = fetch_contract_details(contract)

        if details:
            print(f"✅ 找到有效 SPY expiry: {expiry_str}")
            return expiry_str

    raise ValueError(f"找不到合适的 SPY expiry，起始日期: {target_expiry}")