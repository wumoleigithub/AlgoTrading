
import json, threading, time
from pathlib import Path
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
from core.ibkr_dispatcher import IBKRDispatcher 

# ✅ 配置文件路径
CONFIG_FILE = Path(__file__).parent / "config/config.json"
_ib_connection = None
_dispatcher = IBKRDispatcher()  # ✅ 全局 dispatcher 单例，供所有 IBApi 实例复用

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.data = []
        self.data_event = threading.Event()
        self.contract_details = []
        self.contract_event = threading.Event()
        self.dispatcher = _dispatcher  # ✅ 注入全局 dispatcher，而不是每次新建
    
    def nextValidId(self, orderId):
        print(f"✅ IBKR连接成功 (Order ID: {orderId})")
        self.connected_event.set()

    def historicalData(self, reqId, bar):
        print(f"收到数据：{bar.date}, Close:{bar.close}")
        self.data.append({
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

    def historicalDataEnd(self, reqId, start, end):
        self.dispatcher.signal_done(reqId)

    def contractDetails(self, reqId, contractDetails):
        self.dispatcher.set_result(reqId, contractDetails)

    def contractDetailsEnd(self, reqId, _):
        self.dispatcher.signal_done(reqId)

def _test_set_dispatcher_result(self, reqId, value):
        """✅ 测试钩子：手动设置 dispatcher 的结果并触发完成信号"""
        self.dispatcher.set_result(reqId, value)
        self.dispatcher.signal_done(reqId)
        self.dispatcher.signal_done(reqId)


def load_ibkr_config():
    with open(CONFIG_FILE, "r") as f:
        cfg = json.load(f)["IBKR_CONNECTION"]
    return cfg["TWS_HOST"], cfg["TWS_PORT"], cfg["CLIENT_ID"]


def connect_ibkr(timeout=10):
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
    else:
        print("❌ 没有接收到实时价格")
        return -1


def fetch_historical_data(contract: Contract, end_datetime: str, duration: str, bar_size: str, what_to_show="TRADES"):
    ib = connect_ibkr()
    if ib is None:
        return pd.DataFrame()

    req_id = ib.dispatcher.next_id()  # ✅ Replacing the static reqId with a dynamic one
    ib.dispatcher.register(req_id)

    ib.reqHistoricalData(
        reqId=req_id,  # ✅ Dynamic reqId ensures thread safety
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


def fetch_contract_details(contract: Contract, timeout=5):
    ib = connect_ibkr()
    req_id = ib.dispatcher.next_id()
    ib.dispatcher.register(req_id)

    ib.reqContractDetails(req_id, contract)
    details = ib.dispatcher.wait(req_id, timeout)
    ib.dispatcher.clear(req_id)

    return details