import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from IBKR_Connection import IBApi

# 检查 contractDetailsEnd 的签名
param_names = IBApi.contractDetailsEnd.__code__.co_varnames
arg_count = IBApi.contractDetailsEnd.__code__.co_argcount

print("\U0001F50E 正在检查 contractDetailsEnd 的参数签名...")
print(f"函数参数数量：{arg_count}")
print(f"参数名：{param_names}")

expected = ('self', 'reqId', '_')
if param_names[:3] == expected:
    print("✅ 你使用的是自定义的 IBApi.contractDetailsEnd 方法，签名正确")
else:
    print("❌ 警告：你使用的可能是基类 EWrapper 中的旧签名（缺少 _），请确认是否正确继承并重写")
