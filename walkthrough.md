# BLW Strategy Conversion Walkthrough

This document explains how to use the Python scripts converted from `blw-fixed.mq4` for trading on MT5.

## Files Created
- **[blw_strategy.py](file:///d:/nautilus_trader/blw_strategy.py)**: Main strategy script. Handles connection to MT5, ZigZag calculation, and trade execution.
- **[blw_backtest.py](file:///d:/nautilus_trader/blw_backtest.py)**: Backtesting engine to simulate trades on historical data.
- **[blw_optimizer.py](file:///d:/nautilus_trader/blw_optimizer.py)**: Optimization script to find the best parameters (SL, TP, ZigZag Depth).
- **[test_blw.py](file:///d:/nautilus_trader/test_blw.py)**: Unit tests to verify logic without MT5 connection.

## How to Use

### 1. Prerequisites
Ensure you have `MetaTrader5`, `pandas`, `numpy`, `matplotlib`, `streamlit`, and `plotly` installed:
```bash
pip install MetaTrader5 pandas numpy matplotlib streamlit plotly
```
Ensure your MT5 terminal is open and logged into your FBS account.

### 2. Dashboard (New!)
To monitor your strategy and control risk:
```bash
streamlit run d:\nautilus_trader\blw_dashboard.py
```
This will open a web interface where you can:
- See live Balance/Equity.
- View open positions.
- **Emergency Close**: Click "CLOSE ALL POSITIONS" to liquidate everything.
- View Equity Curve.

### 3. AI Risk Agent (Integrated)
The `blw_strategy.py` now includes an AI Agent that:
- **Protects Profits**: Automatically moves StopLoss to BreakEven and trails price.
- **Prevents Reversals**: Closes trades if they drop 40% from their max profit.
- **Learns**: Analyzes trade history every hour to adjust trailing parameters.

### 4. Optimization
Run the optimizer to find the best parameters for XAUUSD H1:
```bash
python d:\nautilus_trader\blw_optimizer.py
```

### 5. Live Trading
**WARNING**: This will execute real trades if your MT5 is connected to a real account.
1. Open `blw_strategy.py`.
2. Update the `Configuration` section with your optimized parameters.
3. Run the script:
```bash
python d:\nautilus_trader\blw_strategy.py
```
The script will loop, checking for signals every minute (sleeping 10s between checks) and managing Pending Orders (Buy Stop / Sell Stop).
The AI Agent runs in the background to manage open positions.

## Strategy Logic
- **Indicator**: ZigZag (Standard High/Low logic).
- **Entry**:
    - **Buy Stop**: Placed at `ZigZag High + Indent`.
    - **Sell Stop**: Placed at `ZigZag Low - Indent`.
- **Exit**: StopLoss, TakeProfit.
- **Risk Management**: Fixed Lot size (configurable).

## Notes
- The ZigZag implementation in Python is an approximation of the standard MT4 ZigZag.
- Ensure "AutoTrading" is enabled in your MT5 terminal.
