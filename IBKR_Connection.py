# IBKR_Connection.py

import json, threading, time
from pathlib import Path
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
from core.ibkr_dispatcher import IBKRDispatcher

# ✅ 全局配置文件路径
CONFIG_FILE = Path(__file__).parent / "config/config.json"

# ✅ 模块级变量：连接实例和 Dispatcher（类型注解）
_ib_connection: 'IBApi | None' = None
_dispatcher: IBKRDispatcher = IBKRDispatcher()

# ✅ 核心 IB 接口类（继承 EClient + EWrapper）
class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.dispatcher = _dispatcher  # ✅ 注入全局 dispatcher
    
    def nextValidId(self, orderId, *_):
        print(f"✅ IBKR连接成功 (Order ID: {orderId})")
        self.connected_event.set()

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType in (1, 2, 4) and price > 0:
            self.dispatcher.set_result(reqId, price)
            self.dispatcher.signal_done(reqId)

    def historicalData(self, reqId, bar):
        self.dispatcher.set_result(reqId, {
            "date": bar.date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        })


    # def historicalDataEnd(self, reqId, start, end):
    #     print("✅ 数据接收完毕")
    #     self.data_event.set()

    # def contractDetails(self, reqId, contractDetails):
    #     self.contract_details.append(contractDetails)

    # def contractDetailsEnd(self, reqId, *_):
    #     self.contract_event.set()

    def historicalDataEnd(self, reqId, *_):
        self.dispatcher.signal_done(reqId)

    def contractDetails(self, reqId, contractDetails):
        self.dispatcher.set_result(reqId, contractDetails)

    def contractDetailsEnd(self, reqId, *_):
        self.dispatcher.signal_done(reqId)

# ✅ 外部配置文件加载
def load_ibkr_config():
    with open(CONFIG_FILE, "r") as f:
        cfg = json.load(f)["IBKR_CONNECTION"]
    return cfg["TWS_HOST"], cfg["TWS_PORT"], cfg["CLIENT_ID"]

# ✅ 连接 IBKR（全局连接单例）
def connect_ibkr(timeout=10) -> IBApi | None:
    global _ib_connection
    if _ib_connection is None or not _ib_connection.isConnected():
        host, port, client_id = load_ibkr_config()
        _ib_connection = IBApi()
        try:
            _ib_connection.connect(host, port, client_id)
            api_thread = threading.Thread(target=_ib_connection.run, daemon=True)
            api_thread.start()
            if not _ib_connection.connected_event.wait(timeout):
                raise ConnectionError("IBKR连接超时")
            print(f"✅ IBKR 已连接 ({host}:{port}, Client ID={client_id})")
        except Exception as e:
            print(f"❌ IBKR连接失败: {e}")
            _ib_connection.disconnect()
            _ib_connection = None
    return _ib_connection

def disconnect_ibkr():
    global _ib_connection
    if _ib_connection and _ib_connection.isConnected():
        _ib_connection.disconnect()
        _ib_connection = None
        print("🔌 IBKR连接已断开")

# 获取实时价格（支持回调超时 & 合约验证）
# 注意：
# 为避免 IBKR 限制和连接管理问题，这里使用 snapshot=True 获取一次性价格快照。
# 不建议使用 snapshot=False（流式实时数据），除非你明确管理 cancelMktData 调用。
# 如果在非交易时间 snapshot 失败，建议使用 fallback 方法 get_last_close_price 代替。
def get_ibkr_price(contract: Contract, timeout: int = 5) -> float:
    ib = connect_ibkr()
    if ib is None:
        return -1

    req_id = ib.dispatcher.next_id()
    ib.dispatcher.register(req_id)

    ib.reqMktData(req_id, contract, "", False, False, [])
    price_list = ib.dispatcher.wait(req_id, timeout)
    ib.cancelMktData(req_id)
    ib.dispatcher.clear(req_id)

    if price_list:
        return price_list[0]
    elif not verify_contract_internal(contract):
        print("❌ 合约不存在")
        return -1
    else:
        print("⚠️ snapshot 获取失败，尝试 fallback 至历史数据")
        return get_last_close_price(contract)

def get_last_close_price(contract: Contract, timeout: int = 5) -> float:
    """
    用于在非交易时间或 snapshot 获取失败时模拟当前价格。
    获取最近一根 1 分钟 K 线的 close 值作为替代价格。
    """
    ib = connect_ibkr()
    if ib is None:
        return -1

    req_id = ib.dispatcher.next_id()
    ib.dispatcher.register(req_id)

    ib.reqHistoricalData(
        reqId=req_id,
        contract=contract,
        endDateTime='',
        durationStr='1 D', # 必须用1D级别才能返回数据
        barSizeSetting='1 min',
        whatToShow='MIDPOINT',  #也可以改为 "TRADES"
        useRTH=0,
        formatDate=1,
        keepUpToDate=False,
        chartOptions=[]
    )

    bars = ib.dispatcher.wait(req_id, timeout)
    ib.dispatcher.clear(req_id)

    if bars:
        df = pd.DataFrame(bars)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df["close"].iloc[-1]  # ✅ 返回最近一根K线的收盘价
    else:
        print("❌ 无法通过历史数据获取当前价格")
        return -1


# ✅ 获取历史数据（动态 reqId，返回 DataFrame）
def fetch_historical_data(contract: Contract, end_datetime: str, duration: str, bar_size: str, what_to_show="TRADES") -> pd.DataFrame:
    ib = connect_ibkr()
    if ib is None:
        return pd.DataFrame()

    req_id = ib.dispatcher.next_id()
    ib.dispatcher.register(req_id)

    ib.reqHistoricalData(
        reqId=req_id,
        contract=contract,
        endDateTime=end_datetime,
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow=what_to_show,
        useRTH=1,
        formatDate=1,
        keepUpToDate=False,
        chartOptions=[]
    )

    bars = ib.dispatcher.wait(req_id, timeout=15)
    ib.dispatcher.clear(req_id)

    if not bars:
        print("❌ 没有接收到历史数据")
        return pd.DataFrame()

    df = pd.DataFrame(bars)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df

# ✅ 获取合约详情（如验证或补全参数用）
def fetch_contract_details(contract: Contract, timeout=5):
    ib = connect_ibkr()
    req_id = ib.dispatcher.next_id()
    ib.dispatcher.register(req_id)

    ib.reqContractDetails(req_id, contract)
    details = ib.dispatcher.wait(req_id, timeout)
    ib.dispatcher.clear(req_id)

    return details

# ✅ 合约验证工具（避免循环导入）
def verify_contract_internal(contract: Contract, timeout: int = 5) -> bool:
    ib = connect_ibkr()
    if ib is None:
        return False

    req_id = ib.dispatcher.next_id()
    ib.dispatcher.register(req_id)

    ib.reqContractDetails(req_id, contract)
    result = ib.dispatcher.wait(req_id, timeout)
    ib.dispatcher.clear(req_id)

    return bool(result)
