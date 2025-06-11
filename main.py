# test_option_chain.py

# from IBKR_Connection import connect_ibkr, fetch_contract_details
# from ibapi.contract import Contract

# ib = connect_ibkr()

# contract = Contract()
# contract.symbol = "SPY"
# contract.secType = "STK"
# contract.exchange = "SMART"
# contract.currency = "USD"

# details = fetch_contract_details(contract)
# con_id = details[0].contract.conId

# req_id = ib.dispatcher.next_id()
# ib.dispatcher.register(req_id)

# ib.reqSecDefOptParams(
#     reqId=req_id,
#     underlyingSymbol="SPY",
#     futFopExchange="SMART",
#     underlyingSecType="STK",
#     underlyingConId=con_id
# )

# result = ib.dispatcher.wait(req_id, timeout=10)
# ib.dispatcher.clear(req_id)

# print(result or "❌ 没有接收到任何 Option Chain 数据")






from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
from typing import Set, List
from core.ibkr_dispatcher import IBKRDispatcher

class TestApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.req_id = 1
        self.dispatcher = IBKRDispatcher()
        self.data_received = threading.Event()
        self.connection_established = threading.Event()
        self.error_message = None
        self.contract_details_received = False
        self.option_params_received = False

    def nextValidId(self, orderId: int):
        self.req_id = orderId
        self.connection_established.set()

        # Step 1: Define contract
        contract = Contract()
        contract.symbol = "SPY"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        # Register for contract details request
        self.dispatcher.register(self.req_id)
        
        # Step 2: Request contract details
        self.reqContractDetails(self.req_id, contract)

    def error(self, reqId: int, errorCode: int, errorString: str, *args):
        # Print all errors for debugging
        print(f"Error {errorCode}: {errorString} for request {reqId}")
        
        # Handle specific error codes
        if errorCode == 2104:
            # Check if this is any of the market data farm connection messages
            if any(farm in errorString for farm in ["usfarm", "usfuture", "cafarm", "cashfarm"]):
                print(f"✅ Market data connection is OK: {errorString}")
                return  # Ignore these messages as they're not errors
            
            print("\n⚠️ Market Data Error (2104) detected!")
            print("This usually means one of the following:")
            print("1. Market data subscription is required")
            print("2. Market data permissions are not enabled")
            print("3. Market data is not available for this symbol")
            self.error_message = f"Market Data Error: {errorString}"
            if reqId > self.req_id:  # This is our option chain request
                self.dispatcher.signal_done(reqId)
                self.data_received.set()
        elif errorCode == 2106:  # HMDS data farm connection
            print(f"✅ HMDS data connection is OK: {errorString}")
            return
        elif errorCode == 2158:  # Sec-def data farm connection
            print(f"✅ Sec-def data connection is OK: {errorString}")
            return
        elif errorCode not in [2106, 2158]:  # Ignore other normal connection status messages
            self.error_message = f"Error {errorCode}: {errorString}"
            if errorCode in [502, 504]:  # Connection errors
                self.connection_established.set()  # Unblock the wait
            # If this is an error for our option chain request, mark it as done
            if reqId > self.req_id:  # This is our option chain request
                print(f"❌ Error occurred during option chain request {reqId}")
                self.dispatcher.signal_done(reqId)
                self.data_received.set()

    def contractDetails(self, reqId, contractDetails):
        print(f"✅ ContractDetails received: {contractDetails.contract.symbol}, conId = {contractDetails.contract.conId}")
        self.contract_details_received = True
        
        # Register for option chain request using dispatcher's next_id
        next_req_id = self.dispatcher.next_id()
        self.dispatcher.register(next_req_id)
        
        # Step 3: Trigger request for Option Chain parameters
        try:
            print(f"Requesting option chain for SPY (conId: {contractDetails.contract.conId})")
            # Match ib_insync's parameter order and add contract qualification
            self.reqSecDefOptParams(
                reqId=next_req_id,
                underlyingSymbol=contractDetails.contract.symbol,
                futFopExchange="SMART",  # Try SMART exchange first
                underlyingSecType=contractDetails.contract.secType,
                underlyingConId=contractDetails.contract.conId
            )
            print(f"✅ Option chain parameters request sent with ID {next_req_id}")
        except Exception as e:
            print(f"❌ Error requesting option chain parameters: {str(e)}")
            self.error_message = f"Error requesting option chain parameters: {str(e)}"
            self.dispatcher.signal_done(next_req_id)

    def contractDetailsEnd(self, reqId):
        print("✅ Contract details request completed.")
        self.dispatcher.signal_done(reqId)

    def securityDefinitionOptionalParameter(
        self,
        reqId: int,
        exchange: str,
        underlyingConId: int,
        tradingClass: str,
        multiplier: str,
        expirations: Set[str],
        strikes: List[float]
    ):
        print(f"\n📊 Received option parameters for request {reqId}")
        print(f"Exchange: {exchange}")
        print(f"Underlying ConId: {underlyingConId}")
        print(f"Trading Class: {tradingClass}")
        print(f"Multiplier: {multiplier}")
        print(f"Number of expirations: {len(expirations)}")
        print(f"Number of strikes: {len(strikes)}")
        
        # Filter for SMART exchange and matching trading class
        if exchange == "SMART" and tradingClass == "SPY":
            self.option_params_received = True
            
            # Store the result
            self.dispatcher.set_result(reqId, {
                "exchange": exchange,
                "underlyingConId": underlyingConId,
                "tradingClass": tradingClass,
                "multiplier": multiplier,
                "expirations": list(expirations),
                "strikes": list(strikes)
            })
            
            # Since we received data, we can consider this request complete
            print(f"✅ Marking request {reqId} as complete")
            self.dispatcher.signal_done(reqId)
            self.data_received.set()
        else:
            print(f"⚠️ Skipping non-matching exchange/trading class: {exchange}/{tradingClass}")

    def securityDefinitionOptionalParameterEnd(self, reqId):
        print(f"✅ Option Chain retrieval completed for request {reqId}")
        self.dispatcher.signal_done(reqId)
        self.data_received.set()

def main():
    
    app = TestApp()
    
    try:
        app.connect("127.0.0.1", 7497, clientId=1)
        
        # Start the client thread
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()

        # Wait for connection
        connection_timeout = 5
        if not app.connection_established.wait(timeout=connection_timeout):
            print("\n❌ Connection timeout. Trying live trading port...")
            app.disconnect()
            time.sleep(1)  # Wait for disconnect
            
            # Try live trading port
            print("🔌 Attempting to connect to Live Trading (port 7496)...")
            app.connect("127.0.0.1", 7496, clientId=1)
            if not app.connection_established.wait(timeout=connection_timeout):
                raise ConnectionError("Could not connect to either port (7496 or 7497)")
        
        if app.error_message:
            raise ConnectionError(app.error_message)

        # Wait for data with progress updates
        print("\n⏳ Waiting for option chain data...")
        data_timeout = 60  # Increased timeout to 60 seconds
        start_time = time.time()
        while time.time() - start_time < data_timeout:
            if app.data_received.is_set():
                break
            
            # Print progress with more details
            print(f"\rStatus: Contract Details: {'✅' if app.contract_details_received else '⏳'} | "
                  f"Option Params: {'✅' if app.option_params_received else '⏳'} | "
                  f"Time Elapsed: {int(time.time() - start_time)}s", end='')
            time.sleep(1)
        
        print()  # New line after progress

        if not app.data_received.is_set():
            print("\n❌ Timeout: No option chain data received")
            if not app.contract_details_received:
                print("  - Contract details were not received")
            if not app.option_params_received:
                print("  - Option parameters were not received")
                if app.error_message:
                    print(f"  - Error message: {app.error_message}")
                else:
                    print("  - No error message received, possible timeout or connection issue")
        else:
            # Get results with more detailed error handling
            try:
                result = app.dispatcher.wait(app.req_id + 1, timeout=10)
                if result:
                    print("\n✅ Retrieved option chain data successfully!")
                    if isinstance(result, list):
                        print(f"\nReceived {len(result)} results")
                        print("First result:", result[0])
                    else:
                        print("\nResult:", result)
                else:
                    print("\n❌ No option chain data in results")
                    print("  - This might indicate a timeout or empty response")
            except Exception as e:
                print(f"\n❌ Error retrieving results: {str(e)}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        print("\n🔌 Disconnecting from IBKR...")
        app.disconnect()

if __name__ == "__main__":
    main()










# from ibapi.client import EClient
# from ibapi.wrapper import EWrapper
# import threading, time

# class TestApp(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)
#         self.data_received = threading.Event()

#     def nextValidId(self, orderId):
#         print("✅ Connected. Sending reqSecDefOptParams...")
#         self.reqSecDefOptParams(1, "SPY", "SMART", "STK", 756733)

#     def securityDefinitionOptionalParameter(self, reqId, exchange, underlyingConId, tradingClass, multiplier, expirations, strikes):
#         print("✅ Got option chain data!")
#         print("Exchange:", exchange)
#         print("Expirations:", sorted(expirations))
#         print("Strikes:", sorted(strikes))

#     def securityDefinitionOptionalParameterEnd(self, reqId):
#         print("✅ Option chain request complete.")
#         self.data_received.set()
#         self.disconnect()

# app = TestApp()
# app.connect("127.0.0.1", 7497, 0)
# thread = threading.Thread(target=app.run)
# thread.start()

# if not app.data_received.wait(timeout=10):
#     print("❌ Timeout: No option chain data received.")







# from IBKR_Data import fetch_stock_data #fetch_historical_data
# from logic import apply_bull_trend_bar, apply_bear_trend_bar

# from options.option_chain_utils import request_option_chain_params
# from options.option_chain_scanner_ib_insync import request_option_chain

# chain0 = request_option_chain("SPY", delta_range=(0.6, 0.8), strike_buffer=10)

# chain = request_option_chain_params("SPY")
# if chain:
#     print("✅ Option Chain 参数:")
#     print("Exchange:", chain.exchange)
#     print("Trading Class:", chain.tradingClass)
#     print("Expirations:", chain.expirations[:5])
#     print("Strikes:", sorted(chain.strikes)[:10])
# else:
#     print("❌ 无法获取期权链参数")



# from IBKR_Trading import place_stock_order, check_positions, close_position

# from ib_insync import *
# import pandas as pd
# import numpy as np
# import mplfinance as mpf

# from IBKR_Trading import place_stock_order, check_positions, close_position

# # ✅ TEST ORDER: Buy 10 shares of AAPL
# trade = place_stock_order("AAPL", "BUY", 10, order_type="MKT")

# # ✅ CHECK POSITIONS
# check_positions()

# # ✅ CLOSE AAPL POSITION
# close_position("AAPL")

#######################Bear Trend Bar Static Test#######################


# from ib_insync import *
# import pandas as pd
# import numpy as np
# import mplfinance as mpf

# # ✅ CONFIGURATION
# REALTIME_MODE = False  # Static analysis mode
# DATA_PERIOD = "180 D"  
# BAR_SIZE = "1 day"  # Change to "1 week" for weekly, "5 mins" for intraday

# # ✅ STEP 1: Define Contract (SPY Stock)
# # from ibapi.contract import Contract

# # contract = Contract()
# # contract.symbol = "SPY"
# # contract.secType = "STK"
# # contract.exchange = "SMART"
# # contract.currency = "USD"

# # ✅ STEP 2: Fetch Historical Data (Daily, Weekly, or Intraday)
# df = fetch_stock_data("SPY", bar_size=BAR_SIZE, duration=DATA_PERIOD)

# # ✅ STEP 3: Apply Trend Bar Detection
# if df.empty:
#     print("❌ 无法获取数据，无法绘图")
# else:
#     df = apply_bull_trend_bar(df)
#     df = apply_bear_trend_bar(df)
#     df.sort_index(inplace=True)
#     df["BullTrendBar"] = df["BullTrendBar"].fillna(False)
#     df["BearTrendBar"] = df["BearTrendBar"].fillna(False)

# # ✅ STEP 4: Highlight Trend Bars
#  # 关键修复：用np.where生成完全匹配的数据序列
#     highlight_bull_data = pd.Series(
#         np.where(df["BullTrendBar"], df["low"], np.nan),
#         index=df.index
#     )

#     highlight_bull = mpf.make_addplot(
#         highlight_bull_data,
#         type='scatter', markersize=100, marker='^', color='green', alpha=0.7
#     )

#     highlight_bear_data = pd.Series(
#         np.where(df["BearTrendBar"], df["high"], np.nan),
#         index=df.index
#     )

#     highlight_bear = mpf.make_addplot(
#         highlight_bear_data,
#         type='scatter', markersize=100, marker='v', color='red', alpha=0.7
#     )




# ## STEP 5: Plot Candlestick Chart
# # 绘图
#     mpf.plot(
#         df,
#         type="candle",
#         style="charles",
#         addplot=[highlight_bull,highlight_bear]
#     )

# print("✅ Static Bear Trend Bar Analysis Completed!")
