from ib_insync import *

# 连接到 IBKR Paper Trading 账户（端口 7497）
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# 检查连接状态
if ib.isConnected():
    print("✅ 成功连接到 IBKR Paper Trade API")
else:
    print("❌ 连接失败，请检查 TWS / IB Gateway 设置")