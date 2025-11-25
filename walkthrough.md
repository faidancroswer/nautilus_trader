# BLW Strategy Conversion Walkthrough

This document explains how to use the Python scripts converted from `blw-fixed.mq4` for trading on MT5.

## Files Created
- **[blw_strategy.py](file:///d:/nautilus_trader/blw_strategy.py)**: Main strategy script. Handles connection to MT5, ZigZag calculation, and trade execution.
- **[blw_backtest.py](file:///d:/nautilus_trader/blw_backtest.py)**: Backtesting engine to simulate trades on historical data.
- **[blw_optimizer.py](file:///d:/nautilus_trader/blw_optimizer.py)**: Optimization script to find the best parameters (SL, TP, ZigZag Depth).
- **[test_blw.py](file:///d:/nautilus_trader/test_blw.py)**: Unit tests to verify logic without MT5 connection.

## How to Use

### 1. Prerequisites
Ensure you have `MetaTrader5`, `pandas`, `numpy`, and `matplotlib` installed:
```bash
pip install MetaTrader5 pandas numpy matplotlib
```
Ensure your MT5 terminal is open and logged into your FBS account.

### 2. Optimization (Recommended First Step)
Run the optimizer to find the best parameters for XAUUSD H1:
```bash
python d:\nautilus_trader\blw_optimizer.py
```
This will test various combinations of StopLoss, TakeProfit, and ZigZag Depth and print the best configuration.

### 3. Backtesting
To run a detailed backtest with specific parameters (edit `blw_strategy.py` to set them first):
```bash
python d:\nautilus_trader\blw_backtest.py
```
This will generate an equity curve plot `backtest_result.png`.

### 4. Live Trading
**WARNING**: This will execute real trades if your MT5 is connected to a real account.
1. Open `blw_strategy.py`.
2. Update the `Configuration` section with your optimized parameters.
3. Run the script:
```bash
python d:\nautilus_trader\blw_strategy.py
```
The script will loop, checking for signals every minute (sleeping 10s between checks) and managing Pending Orders (Buy Stop / Sell Stop).

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
