from ib_insync import IB

# ✅ 统一定义连接参数，方便调整
TWS_HOST = '127.0.0.1'
TWS_PORT = 7497  # Paper trading账户端口
CLIENT_ID = 1    # 唯一的客户端ID（每个连接需不同）

_ib_connection = None  # 全局变量保存连接实例

def connect_ibkr():
    global _ib_connection
    if not _ib_connection or not _ib_connection.isConnected():
        _ib_connection = IB()
        try:
            # 使用统一定义的参数进行连接
            _ib_connection.connect(TWS_HOST, TWS_PORT, clientId=CLIENT_ID)
            print(f"✅ IBKR 已连接 ({TWS_HOST}:{TWS_PORT}, ClientID={CLIENT_ID})")
        except Exception as e:
            print(f"❌ IBKR连接失败: {e}")
            return None
    return _ib_connection

def disconnect_ibkr():
    global _ib_connection
    if _ib_connection and _ib_connection.isConnected():
        _ib_connection.disconnect()
        print("🔌 已从IBKR断开连接")
