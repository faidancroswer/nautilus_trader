# Task: Convert blw-fixed.mq4 to Python for MT5 (XAUUSD H1)

- [x] Analyze `blw-fixed.mq4` source code <!-- id: 0 -->
    - [x] Locate and read the file <!-- id: 1 -->
    - [x] Understand entry/exit logic and indicators <!-- id: 2 -->
- [x] Create Python Strategy Implementation <!-- id: 3 -->
    - [x] Setup MT5 connection and data retrieval for XAUUSD H1 <!-- id: 4 -->
    - [x] Implement indicators in Python (pandas/ta-lib) <!-- id: 5 -->
    - [x] Implement trading logic (Signal generation) <!-- id: 6 -->
- [x] Develop Backtesting System <!-- id: 7 -->
    - [x] Create backtest engine or use library <!-- id: 8 -->
    - [x] Simulate trades based on historical data <!-- id: 9 -->
- [x] Implement Optimization <!-- id: 10 -->
    - [x] Define parameter ranges <!-- id: 11 -->
    - [x] Run optimization for profit and risk <!-- id: 12 -->
- [x] Finalize Live Trading Script <!-- id: 13 -->
# Task: Convert blw-fixed.mq4 to Python for MT5 (XAUUSD H1)

- [x] Analyze `blw-fixed.mq4` source code <!-- id: 0 -->
    - [x] Locate and read the file <!-- id: 1 -->
    - [x] Understand entry/exit logic and indicators <!-- id: 2 -->
- [x] Create Python Strategy Implementation <!-- id: 3 -->
    - [x] Setup MT5 connection and data retrieval for XAUUSD H1 <!-- id: 4 -->
    - [x] Implement indicators in Python (pandas/ta-lib) <!-- id: 5 -->
    - [x] Implement trading logic (Signal generation) <!-- id: 6 -->
- [x] Develop Backtesting System <!-- id: 7 -->
    - [x] Create backtest engine or use library <!-- id: 8 -->
    - [x] Simulate trades based on historical data <!-- id: 9 -->
- [x] Implement Optimization <!-- id: 10 -->
    - [x] Define parameter ranges <!-- id: 11 -->
    - [x] Run optimization for profit and risk <!-- id: 12 -->
- [x] Finalize Live Trading Script <!-- id: 13 -->
    - [x] Integrate risk management <!-- id: 14 -->
    - [x] Ensure robust error handling for live execution <!-- id: 15 -->

# Task: Dashboard & AI Risk Agent <!-- id: 16 -->
- [ ] Design and Plan <!-- id: 17 -->
    - [ ] Create implementation plan for Dashboard and Agent <!-- id: 18 -->
- [x] Develop AI Risk Agent <!-- id: 23 -->
    - [x] Create `RiskManager` class in `blw_agent.py` <!-- id: 24 -->
    - [x] Implement "Profit Protection" (Dynamic Trailing/BreakEven) <!-- id: 25 -->
    - [x] Implement "Learning Module" (Log analysis & Parameter adjustment) <!-- id: 26 -->
    - [x] Integrate Agent into `blw_strategy.py` <!-- id: 27 -->
- [x] Integrate All into Dashboard <!-- id: 28 -->
    - [x] Add "Trading" tab (Start/Stop Strategy Process) <!-- id: 29 -->
    - [x] Add "Backtest" tab (Run Backtest & View Results) <!-- id: 30 -->
    - [x] Integrate All into Dashboard <!-- id: 28 -->
    - [x] Add "Trading" tab (Start/Stop Strategy Process) <!-- id: 29 -->
    - [x] Add "Backtest" tab (Run Backtest & View Results) <!-- id: 30 -->
    - [x] Add "Optimization" tab (Run Optimizer & View Output) <!-- id: 31 -->
    - [x] Fix hardcoded paths for portability <!-- id: 32 -->
- [x] Develop Dashboard (Streamlit) <!-- id: 19 -->
    - [x] Create `blw_dashboard.py` layout <!-- id: 20 -->
    - [x] Connect dashboard to MT5 account data <!-- id: 21 -->
    - [x] Implement controls (Start/Stop, Close All) <!-- id: 22 -->

# Task: Debugging & Maintenance <!-- id: 32 -->
- [x] Fix `blw_dashboard.py` startup errors <!-- id: 33 -->
- [x] Fix Dashboard Monitoring (Balance/Positions) <!-- id: 57 -->
# Task: Optimization & Agent Tuning <!-- id: 34 -->
- [x] Optimize for XAUUSD (0.05 Lot) <!-- id: 35 -->
    - [x] Expand `blw_optimizer.py` ranges <!-- id: 36 -->
    - [x] Run optimization to find best SL/TP/ZigZag <!-- id: 37 -->
    - [x] Update `blw_strategy.py` with new defaults <!-- id: 38 -->
- [x] Enhance AI Agent <!-- id: 39 -->
    - [x] Verify if Agent adjusts SL/TP <!-- id: 40 -->
    - [x] Implement SL/TP adjustment in Agent if missing <!-- id: 41 -->

# Task: Volatility Filter & Profit Optimization <!-- id: 42 -->
- [x] Implement Volatility Filter <!-- id: 43 -->
    - [x] Add ATR indicator to `blw_strategy.py` <!-- id: 44 -->
    - [x] Add logic to skip trades if ATR is low <!-- id: 45 -->
    - [x] Add Time Filter (Start/End Hour) <!-- id: 46 -->
- [x] Optimize with Filters <!-- id: 47 -->
    - [x] Run backtest to verify filter effectiveness <!-- id: 48 -->
    - [x] Optimize ATR threshold and Time Window <!-- id: 49 -->

# Task: Advanced Agent Upgrade (Dynamic Risk) <!-- id: 50 -->
- [x] Implement ATR-based Risk Management <!-- id: 51 -->
    - [x] Replace fixed SL/TP with Multipliers in `blw_agent.py` <!-- id: 52 -->
    - [x] Implement Regime-Based Learning (Low/Normal/High Volatility) <!-- id: 53 -->
    - [x] Update `blw_strategy.py` to use dynamic parameters <!-- id: 54 -->
- [x] Update Dashboard <!-- id: 55 -->
    - [x] Display Regime and Multipliers in Agent Monitor <!-- id: 56 -->
