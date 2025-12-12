# Implementation Plan - Agent Monitoring

The user wants to monitor the AI Agent's activity and state in the dashboard.

## Proposed Changes

### Agent (`blw_agent.py`)
- Add `save_status()` method to `RiskManager`.
- Export current parameters (`trailing_start`, `breakeven_trigger`, etc.) and state (`max_profits` count) to `agent_status.json`.
- Call `save_status()` periodically (e.g., in `manage_positions` or `learn`).

### Dashboard (`blw_dashboard.py`)
- Add a new section "Monitoramento do Agente" in the "Negociação ao Vivo" tab.
- Read `agent_status.json`.
- Display parameters and last update time.
- Show a "Health Check" (Active/Inactive based on file timestamp).

## Verification Plan

### Manual Verification
1.  **Start Strategy**: Run the strategy via dashboard.
2.  **Check File**: Verify `agent_status.json` is created and updated.
3.  **Check Dashboard**: Verify the "Monitoramento do Agente" section appears and shows correct values.
4.  **Trigger Learning**: Wait for learning interval (or force it) and see if parameters update in the dashboard.
