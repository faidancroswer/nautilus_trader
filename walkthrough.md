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

### 2. Dashboard (Painel de Controle)
Para monitorar e controlar tudo em um só lugar:
```bash
streamlit run d:\nautilus_trader\blw_dashboard.py
```
Isso abrirá uma interface web com 3 abas:
1.  **Negociação ao Vivo**:
    - Botão **INICIAR ROBÔ**: Começa a operar.
    - Botão **PARAR ROBÔ**: Para a operação.
    - Botão **FECHAR TUDO**: Zera todas as posições imediatamente.
    - Monitor de Saldo e Logs ao vivo.
2.  **Backtest**:
    - Botão **Executar Backtest**: Roda a simulação e mostra o gráfico de lucro.
3.  **Otimização**:
    - Botão **Iniciar Otimização**: Busca os melhores parâmetros automaticamente.

### 3. Agente de Risco (Integrado)
O robô (`blw_strategy.py`) já inclui o Agente de IA que:
- **Protege Lucros**: Move StopLoss para BreakEven e faz Trailing Stop.
- **Evita Reversões**: Fecha se o lucro cair 40% do topo.
- **Aprende**: Analisa o histórico a cada hora.

### 4. Execução Manual (Opcional)
Se não quiser usar o Dashboard, você pode rodar os scripts individualmente:
- **Otimizar**: `python d:\nautilus_trader\blw_optimizer.py`
- **Backtest**: `python d:\nautilus_trader\blw_backtest.py`
- **Negociar**: `python d:\nautilus_trader\blw_strategy.py`

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
