## 🧩 Project Module Overview

### 🔌 Connection Layer
- `IBKR_Connection.py` → Connects to TWS Gateway, manages IB API requests and asynchronous events

### 📈 Data Access
- `IBKR_Data.py` → Fetches historical price data (stock/option)
- `option_data_fetcher.py` → High-level option chain retriever for a given date + expiry

### ⚙️ Analysis Logic
- `bull_trend_bar_static.py` → Detect Bullish Trend Bars using static rules
- `bear_trend_bar_static.py` → Detect Bearish Trend Bars using static rules

### 💼 Backtesting
- `main_back_testing.py` → Example entry point for testing historical option prices
- `main.py` → Visual trend bar analysis and static plotting tool

### 🧰 Utility Modules
- `utils/contracts.py` → Functions to create IBKR contracts, validate and infer ATM prices
- `config/config.json` → Connection settings (TWS host/port, clientId)
- `definitions.json` → Strategy definitions (e.g., trend bar rules)

### 🗃️ Meta
- `.gitignore` → Ignore cache/pyc and sensitive files
- `requirements.txt` → Package dependencies
