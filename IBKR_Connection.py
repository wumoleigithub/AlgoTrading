
import json, threading, time
from pathlib import Path
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd

CONFIG_FILE = Path(__file__).parent / "config/config.json"
_ib_connection = None

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.data = []
        self.data_event = threading.Event()
        self.contract_details = []
        self.contract_event = threading.Event()

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

    def historicalDataEnd(self, reqId, start, end):
        print("✅ 数据接收完毕")
        self.data_event.set()

    def contractDetails(self, reqId, contractDetails):
        self.contract_details.append(contractDetails)

    def contractDetailsEnd(self, reqId, *_):
        self.contract_event.set()


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


def fetch_historical_data(contract: Contract, end_datetime: str, duration: str, bar_size: str, what_to_show="TRADES"):
    """
    获取指定合约的历史数据，返回 pandas DataFrame。
    """
    ib = connect_ibkr()
    if ib is None:
        return pd.DataFrame()

    ib.data.clear()
    ib.data_event.clear()

    ib.reqHistoricalData(
        reqId=1,
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

    waited = 0
    while not ib.data_event.is_set() and waited < 15:
        time.sleep(1)
        waited += 1

    if not ib.data:
        print("❌ 没有接收到历史数据")
        return pd.DataFrame()

    df = pd.DataFrame(ib.data)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df

def fetch_contract_details(contract: Contract, timeout=5):
    """
    使用 reqContractDetails 异步获取合约详情列表。
    """
    ib = connect_ibkr()
    ib.contract_details.clear()
    ib.contract_event.clear()

    ib.reqContractDetails(999, contract)

    waited = 0
    while not ib.contract_event.is_set() and waited < timeout:
        time.sleep(1)
        waited += 1

    return ib.contract_details