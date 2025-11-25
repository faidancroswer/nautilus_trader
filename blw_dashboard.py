import streamlit as st
import MetaTrader5 as mt5
import pandas as pd
import time
import plotly.express as px
import os
import subprocess
import signal

# Page Config
st.set_page_config(page_title="Painel de Controle BLW", layout="wide")

# Constants
MAGIC = 1147485642
SYMBOL = "XAUUSD"

# Dynamic Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STRATEGY_SCRIPT = os.path.join(BASE_DIR, "blw_strategy.py")
BACKTEST_SCRIPT = os.path.join(BASE_DIR, "blw_backtest.py")
OPTIMIZER_SCRIPT = os.path.join(BASE_DIR, "blw_optimizer.py")
PID_FILE = os.path.join(BASE_DIR, "strategy.pid")
LOG_FILE = os.path.join(BASE_DIR, "strategy.log")

# Initialize MT5
if not mt5.initialize():
    st.error("Falha na Inicialização do MT5")
else:
    st.success(f"Conectado ao MT5: {mt5.version()}")

# --- Helper Functions ---
def is_strategy_running():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read())
            # Check if process exists
            # In Windows, we can't easily check without psutil, but we can try sending signal 0
            # Or just assume it's running if PID file exists and let user "Stop" handle errors
            return pid
        except:
            return None
    return None

def start_strategy():
    if is_strategy_running():
        st.warning("A estratégia já está rodando!")
        return
    
    # Open log file
    with open(LOG_FILE, "w") as log:
        # Start process
        process = subprocess.Popen(["python", STRATEGY_SCRIPT], stdout=log, stderr=log, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))
    st.success(f"Estratégia iniciada! PID: {process.pid}")
    time.sleep(1)
    st.rerun()

def stop_strategy():
    pid = is_strategy_running()
    if not pid:
        st.warning("A estratégia não está rodando.")
        return
    
    try:
        # Kill process
        os.kill(pid, signal.SIGTERM) # Might need SIGKILL or taskkill on Windows
        # subprocess.run(["taskkill", "/F", "/PID", str(pid)])
        st.success("Comando de parada enviado.")
    except Exception as e:
        st.error(f"Erro ao parar: {e}")
        # Force remove PID file if it fails
    
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    time.sleep(1)
    st.rerun()

def close_all_positions():
    positions = mt5.positions_get(symbol=SYMBOL, magic=MAGIC)
    if positions:
        for pos in positions:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": pos.ticket,
                "price": mt5.symbol_info_tick(SYMBOL).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(SYMBOL).ask,
                "magic": MAGIC,
                "comment": "Dashboard Close All",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            mt5.order_send(request)
        st.success("Comando de Fechamento Enviado!")
    else:
        st.warning("Sem posições abertas.")

# --- Main Layout ---
st.title("Painel de Controle BLW - XAUUSD")

# Tabs
tab1, tab2, tab3 = st.tabs(["Negociação ao Vivo", "Backtest", "Otimização"])

# --- Tab 1: Live Trading ---
with tab1:
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Controles")
        pid = is_strategy_running()
        if pid:
            st.success(f"Status: RODANDO (PID: {pid})")
            if st.button("PARAR ROBÔ", type="primary"):
                stop_strategy()
        else:
            st.error("Status: PARADO")
            if st.button("INICIAR ROBÔ"):
                start_strategy()
        
        st.divider()
        if st.button("FECHAR TUDO (EMERGÊNCIA)", type="primary"):
            close_all_positions()

    with col2:
        st.subheader("Monitoramento")
        # Account Info
        account = mt5.account_info()
        if account:
            m1, m2, m3 = st.columns(3)
            m1.metric("Saldo", f"${account.balance:.2f}")
            m2.metric("Patrimônio (Equity)", f"${account.equity:.2f}")
            m3.metric("Lucro Aberto", f"${account.profit:.2f}")

        # Open Positions
        st.write("Posições Abertas:")
        positions = mt5.positions_get(symbol=SYMBOL, magic=MAGIC)
        if positions:
            df_pos = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
            df_pos['type'] = df_pos['type'].apply(lambda x: 'COMPRA' if x == 0 else 'VENDA')
            df_pos['time'] = pd.to_datetime(df_pos['time'], unit='s')
            st.dataframe(df_pos[['ticket', 'time', 'type', 'volume', 'price_open', 'price_current', 'sl', 'tp', 'profit']])
        else:
            st.info("Nenhuma posição aberta.")
            
        # Live Logs
        st.subheader("Logs da Estratégia")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                st.code("".join(lines[-20:])) # Show last 20 lines

# --- Tab 2: Backtest ---
with tab2:
    st.header("Backtest (Simulação)")
    if st.button("Executar Backtest"):
        with st.spinner("Rodando Backtest..."):
            result = subprocess.run(["python", BACKTEST_SCRIPT], capture_output=True, text=True, cwd=BASE_DIR)
            st.text(result.stdout)
            if result.stderr:
                st.error(result.stderr)
            
            img_path = os.path.join(BASE_DIR, "backtest_result.png")
            if os.path.exists(img_path):
                st.image(img_path, caption="Curva de Patrimônio")

# --- Tab 3: Optimization ---
with tab3:
    st.header("Otimização de Parâmetros")
    st.write("Isso testará várias combinações de SL, TP e ZigZag para encontrar a melhor.")
    if st.button("Iniciar Otimização"):
        with st.spinner("Otimizando... (Isso pode demorar)"):
            # We use Popen to stream output or just run and wait
            # For simplicity, run and wait
            result = subprocess.run(["python", OPTIMIZER_SCRIPT], capture_output=True, text=True, cwd=BASE_DIR)
            st.code(result.stdout)
            if result.stderr:
                st.error(result.stderr)

# Auto Refresh logic only for Live Tab mostly, but we put it at end
if pid:
    time.sleep(5)
    st.rerun()

