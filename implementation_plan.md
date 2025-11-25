# Implementation Plan - Convert blw-fixed.mq4 to Python MT5

# Goal Description
Convert the `blw-fixed.mq4` Expert Advisor to a Python script that runs on MetaTrader 5 (FBS broker) for XAUUSD H1. The project includes backtesting and optimization capabilities.

## User Review Required
> [!IMPORTANT]
> - **Broker**: FBS (Real Account). Ensure MT5 is logged in.
> - **Symbol**: XAUUSD.
> - **Timeframe**: H1.
> - **Risk**: Optimization will determine best risk parameters.

## Proposed Changes

### Strategy Conversion
#### [NEW] [blw_strategy.py](file:///d:/nautilus_trader/blw_strategy.py)
- **Logic**: ZigZag Breakout with Pending Orders.
- **Indicators**: ZigZag (Depth=18, Deviation=5, Backstep=3).
- **Entry**:
    - **Buy Stop**: ZigZag High + Indent.
    - **Sell Stop**: ZigZag Low - Indent.
- **Exit**: StopLoss, TakeProfit, TrailingStop, BreakEven, SmartTakeProfit.
- **Risk Management**:
    - Fixed Lot or Risk %.
    - Max Drawdown protection.
    - Time filter (StartHour, EndHour).

### Backtesting & Optimization
#### [NEW] [blw_backtest.py](file:///d:/nautilus_trader/blw_backtest.py)
- **Engine**: Custom event-driven backtester or vector-based if possible (given ZigZag repainting nature, event-driven is safer).
- **Optimization**:
    - Parameters: `Risk`, `StopLoss`, `TakeProfit`, `TrailingStop`, `Indent`, `ZigZag` params.
    - Metric: Net Profit, Sharpe Ratio, Max Drawdown.

### Live Trading
- Ensure `MetaTrader5` library is installed and configured.
- Implement `OnTick` logic equivalent in Python loop.


## Verification Plan

### Automated Tests
- **Backtest Validation**: Run `blw_backtest.py` and compare logic with expected MQ4 behavior.
- **Dry Run**: Run `blw_strategy.py` in dry-run mode (no trade execution) to verify signal generation.

### Manual Verification
- **Visual Check**: Compare Python signals with MT4 visual backtest (if possible) or manual chart inspection.
