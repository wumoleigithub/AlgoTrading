from ib_insync import *
import pandas as pd
from typing import List, Dict, Optional
import time
from datetime import datetime
import traceback

def format_value(value, format_str='8.2f'):
    """格式化数值，处理None值"""
    if value is None:
        return ' ' * 8
    return f"{value:{format_str}}"

def get_option_chain(symbol: str = "SPY", strike_buffer: float = 10) -> None:
    """
    获取指定标的的最近到期日期权链数据。

    参数:
        symbol (str): 标的资产，例如 'SPY'
        strike_buffer (float): 不再使用此参数，保留是为了兼容性
    """
    try:
        # 1. 连接IBKR
        print(f"\n🔌 正在连接IBKR...")
        ib = IB()
        ib.connect('127.0.0.1', 7496, clientId=1)  # 7497为paper，7496为实盘
        print("✅ 连接成功")

        # 2. 获取标的合约信息
        print(f"\n🔍 正在获取 {symbol} 合约信息...")
        underlying = Stock(symbol, 'SMART', 'USD')
        ib.qualifyContracts(underlying)
        print(f"✅ 合约信息: conId={underlying.conId}")

        # 3. 获取期权链参数
        print(f"\n📊 正在获取期权链参数...")
        chains = ib.reqSecDefOptParams(
            underlying.symbol,
            '',  # futFopExchange
            underlying.secType,
            underlying.conId
        )

        # 4. 选取SMART交易所、tradingClass=symbol的option chain
        chain = next((c for c in chains if c.exchange == 'SMART' and c.tradingClass == symbol), None)
        if not chain:
            print("❌ 未找到SMART交易所的option chain")
            return

        # 5. 获取标的最新价格
        print(f"\n💰 正在获取{symbol}最新价格...")
        [ticker] = ib.reqTickers(underlying)
        # 获取历史数据来获取最新收盘价
        bars = ib.reqHistoricalData(
            underlying,
            endDateTime='',
            durationStr='1 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=False
        )
        if bars:
            price = bars[-1].close
            print(f"✅ 获取到最新收盘价: {price:.2f}")
        else:
            print("❌ 无法获取价格数据")
            return

        # 6. 获取最近到期日 - 修改为获取更近的到期日
        print(f"\n📈 正在获取可用到期日...")
        available_expiries = sorted(chain.expirations)
        # 过滤掉太远的到期日（只保留未来30天内的）
        current_date = datetime.now()
        valid_expiries = [exp for exp in available_expiries 
                         if datetime.strptime(exp, '%Y%m%d') - current_date < pd.Timedelta(days=30)]
        
        if not valid_expiries:
            print("❌ 没有找到合适的到期日")
            return
            
        nearest_expiry = valid_expiries[0]
        print(f"✅ 选择到期日: {nearest_expiry}")

        # 7. 获取所有期权合约定义
        print(f"\n📝 正在获取期权链定义...")
        
        # 使用reqContractDetails直接获取指定到期日的所有期权
        option_contract = Option(symbol, nearest_expiry, 0, '', 'SMART', tradingClass=symbol)
        try:
            # 获取所有可用的期权合约详情
            contract_details = ib.reqContractDetails(option_contract)
            if not contract_details:
                print("❌ 没有找到任何期权合约")
                return

            all_contracts = [cd.contract for cd in contract_details]
            print(f"✅ 获取到 {len(all_contracts)} 个合约定义")

            # 8. 批量获取所有合约的行情和希腊值
            print(f"\n📊 正在获取行情和希腊值 (这可能需要一些时间)...")
            tickers = []
            batch_size = 50  # 每次请求的合约数量
            for i in range(0, len(all_contracts), batch_size):
                batch = all_contracts[i:i + batch_size]
                print(f"正在处理批次 {i//batch_size + 1}/{(len(all_contracts) + batch_size - 1)//batch_size}...")
                
                # 请求市场数据和希腊值
                for contract in batch:
                    ib.reqMktData(contract, genericTickList="106", snapshot=False, regulatorySnapshot=False)
                
                # 等待IB服务器响应
                ib.sleep(2) # 等待时间可以根据网络状况调整

                # 获取已更新的ticker
                for contract in batch:
                    tickers.append(ib.ticker(contract))

            # 取消所有市场数据订阅
            for contract in all_contracts:
                ib.cancelMktData(contract)

            print(f"✅ 完成行情获取，共收到 {len(tickers)} 个ticker")

            # 9. 处理结果并构建期权链数据结构
            option_chain_data = {}
            
            for ticker in tickers:
                # 过滤掉没有有效报价或希腊值的合约
                if not (ticker and ticker.modelGreeks and ticker.modelGreeks.delta is not None and (ticker.bid > 0 or ticker.ask > 0)):
                    continue

                g = ticker.modelGreeks
                strike = ticker.contract.strike
                right = ticker.contract.right
                
                option_data = {
                    "strike": strike,
                    "bid": ticker.bid,
                    "ask": ticker.ask,
                    "delta": g.delta,
                    "gamma": g.gamma,
                    "theta": g.theta,
                    "vega": g.vega,
                    "iv": g.impliedVol
                }

                if strike not in option_chain_data:
                    option_chain_data[strike] = {'C': None, 'P': None}
                
                option_chain_data[strike][right] = option_data
            
            if not option_chain_data:
                print("❌ 没有找到任何有有效市场数据的期权合约。")
                return

            # 10. 打印期权链
            print(f"\n📊 {symbol} 期权链 - {nearest_expiry}")
            print(f"当前价格: {price:.2f}")
            
            header_line = f"{'Calls':^62} | {'Strike':^10} | {'Puts':^62}"
            columns_line = f"{'Bid':>8} {'Ask':>8} {'Delta':>8} {'Gamma':>8} {'Theta':>8} {'Vega':>8} {'IV':>8} | {'':^10} | {'Bid':>8} {'Ask':>8} {'Delta':>8} {'Gamma':>8} {'Theta':>8} {'Vega':>8} {'IV':>8}"
            separator_line = "-"*len(header_line)

            print("\n" + separator_line)
            print(header_line)
            print(columns_line)
            print(separator_line)

            sorted_strikes = sorted(option_chain_data.keys())

            def format_option_str(data):
                if not data:
                    return ' ' * 62
                return (f"{format_value(data['bid']):>8} "
                        f"{format_value(data['ask']):>8} "
                        f"{format_value(data['delta'], '8.3f'):>8} "
                        f"{format_value(data['gamma'], '8.3f'):>8} "
                        f"{format_value(data['theta'], '8.3f'):>8} "
                        f"{format_value(data['vega'], '8.3f'):>8} "
                        f"{format_value(data['iv'], '8.3f'):>8}")

            for strike in sorted_strikes:
                call_str = format_option_str(option_chain_data[strike].get('C'))
                put_str = format_option_str(option_chain_data[strike].get('P'))
                print(f"{call_str} | {strike:^10.2f} | {put_str}")

            print(separator_line)

        except Exception as e:
            print(f"❌ 处理期权数据时发生错误: {str(e)}")
            traceback.print_exc()
            return

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
    finally:
        print("\n🔌 正在断开连接...")
        ib.disconnect()
        print("✅ 已断开连接")

def main():
    print("\n🚀 开始获取SPY期权链数据...")
    get_option_chain(
        symbol="SPY",
        strike_buffer=10
    )

if __name__ == "__main__":
    main()