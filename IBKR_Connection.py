# IBKR_Connection.py
import json, threading
from pathlib import Path
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

CONFIG_FILE = Path(__file__).parent / "config/config.json"
_ib_connection = None

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.data = []  # 新增数据容器

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
        self.connected_event.set()

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
