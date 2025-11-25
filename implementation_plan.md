# Implementation Plan - Dashboard & AI Risk Agent

# Goal Description
Create a control dashboard for the BLW Strategy and implement an "AI Risk Agent" that actively manages open trades to protect profits and learns from historical performance to optimize risk parameters.

## User Review Required
> [!IMPORTANT]
> - **Dashboard Technology**: Streamlit (Python-based, runs in browser).
> - **AI Agent Logic**: The "learning" will initially be heuristic-based (analyzing past trade logs to adjust Trailing Stop/BreakEven levels) rather than a full Neural Network, to ensure stability and explainability.

## Proposed Changes

### Dashboard
#### [NEW] [blw_dashboard.py](file:///d:/nautilus_trader/blw_dashboard.py)
- **Tech**: Streamlit.
- **Features**:
    - Live Account Stats (Balance, Equity, Margin).
    - Open Positions table with PnL.
    - Strategy Control: Start/Stop button (controls the running process).
    - Emergency: "Close All Positions" button.
    - Performance Graph: Equity curve from `trade_history.csv`.

### AI Risk Agent
#### [NEW] [blw_agent.py](file:///d:/nautilus_trader/blw_agent.py)
- **Class**: `RiskManager`
- **Responsibilities**:
    - **Monitor**: Checks open trades every tick (or frequent interval).
    - **Protect**: 
        - **Smart BreakEven**: Moves SL to entry + fees once Profit > X%.
        - **Dynamic Trailing**: Tightens trailing stop as profit increases (e.g., loose at start, tight near peak).
        - **Profit Lock**: Closes trade if it drops Y% from its max peak profit (to prevent winning trades turning losers).
    - **Learn**:
        - Logs every trade's lifecycle (Entry, Max Profit, Exit, Reason).
        - `optimize_parameters()`: Analyzes the log to suggest better X% and Y% values based on "what if" scenarios.

### Dashboard Integration (Unified Control)
#### [MODIFY] [blw_dashboard.py](file:///d:/nautilus_trader/blw_dashboard.py)
- **Structure**: Use `st.tabs` to separate functionality: "Live Trading", "Backtest", "Optimization".
- **Live Trading Tab**:
    - **Process Management**: Use `subprocess.Popen` to start `blw_strategy.py` in the background.
    - **State Tracking**: Save PID to a file (`strategy.pid`) to know if it's running.
    - **Logs**: Read `strategy.log` (redirected stdout) to show live logs in the dashboard.
- **Backtest Tab**:
    - **Input**: Allow selecting Date Range (optional) or just "Run Default".
    - **Action**: Run `blw_backtest.py`.
    - **Output**: Display `backtest_result.png` and the final balance text.
- **Optimization Tab**:
    - **Action**: Run `blw_optimizer.py`.
    - **Output**: Stream the output text to show progress and final best params.

## Verification Plan

### Automated Tests
- **Agent Logic**: Unit tests for `RiskManager` to verify it triggers BreakEven/Trailing correctly on mock data.

### Manual Verification
- **Dashboard**: 
    - Click "Start Trading" -> Verify `python blw_strategy.py` process starts.
    - Click "Stop Trading" -> Verify process ends.
    - Click "Run Backtest" -> Verify image appears.
    - Click "Optimize" -> Verify text output appears.
- **Agent**: Open a demo trade and observe if the Agent modifies the SL/TP as price moves.
