import streamlit as st
import MetaTrader5 as mt5
import pandas as pd
import time
import plotly.express as px
import os
import subprocess
import signal
import json
from datetime import datetime

# Page Config
st.set_page_config(page_title="Painel de Controle BLW", layout="wide")

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAGIC = 1147485642
SYMBOL = "XAUUSD"

# Dynamic Paths
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
            return pid
        except:
            return None
    return None

def start_strategy(symbol, volume):
    if is_strategy_running():
        st.warning("A estratégia já está rodando!")
        return
    
    # Open log file
    with open(LOG_FILE, "w") as log:
        # Start process
        cmd = ["python", STRATEGY_SCRIPT, "--symbol", symbol, "--volume", str(volume)]
        process = subprocess.Popen(cmd, stdout=log, stderr=log, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))
    st.success(f"Estratégia iniciada para {symbol} (Lote: {volume})! PID: {process.pid}")
    time.sleep(1)
    st.rerun()

def stop_strategy():
    pid = is_strategy_running()
    if not pid:
        st.warning("A estratégia não está rodando.")
        return
    
    try:
        # Kill process
        os.kill(pid, signal.SIGTERM) 
        st.success("Comando de parada enviado.")
    except Exception as e:
        st.error(f"Erro ao parar: {e}")
    
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    time.sleep(1)
    st.rerun()

def close_all_positions(symbol):
    positions = mt5.positions_get(symbol=symbol, magic=MAGIC)
    if positions:
        for pos in positions:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": pos.ticket,
                "price": mt5.symbol_info_tick(symbol).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask,
                "magic": MAGIC,
                "comment": "Dashboard Close All",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            mt5.order_send(request)
        st.success("Comando de Fechamento Enviado!")
    else:
        st.warning(f"Sem posições abertas para {symbol}.")

# --- Main Layout ---
st.title("Painel de Controle BLW")

# Tabs
tab1, tab2, tab3 = st.tabs(["Negociação ao Vivo", "Backtest", "Otimização"])

# --- Tab 1: Live Trading ---
with tab1:
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Configuração")
        
        # Inputs
        symbol_input = st.text_input("Símbolo", value="XAUUSD").upper()
        volume_input = st.number_input("Lote", min_value=0.01, value=0.01, step=0.01, format="%.2f")
        
        auto_refresh = st.checkbox("Atualização Automática", value=True)
        
        st.divider()
        st.subheader("Controles")
        pid = is_strategy_running()
        if pid:
            st.success(f"Status: RODANDO (PID: {pid})")
            if st.button("PARAR ROBÔ", type="primary"):
                stop_strategy()
        else:
            st.error("Status: PARADO")
            if st.button("INICIAR ROBÔ"):
                start_strategy(symbol_input, volume_input)
        
        st.divider()
        if st.button("FECHAR TUDO (EMERGÊNCIA)", type="primary"):
            close_all_positions(symbol_input)

    with col2:
        st.subheader("Monitoramento")
        # Account Info
        account = mt5.account_info()
        if account:
            m1, m2, m3 = st.columns(3)
            m1.metric("Saldo", f"${account.balance:.2f}")
            m2.metric("Patrimônio (Equity)", f"${account.equity:.2f}")
            m3.metric("Lucro Aberto", f"${account.profit:.2f}")
        else:
            st.error(f"Erro ao obter dados da conta: {mt5.last_error()}")

        # Open Positions
        st.write(f"Posições Abertas ({symbol_input}):")
        # Show ALL positions for the symbol, not just the robot's, so user sees everything
        positions = mt5.positions_get(symbol=symbol_input) 
        if positions:
            df_pos = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
            df_pos['type'] = df_pos['type'].apply(lambda x: 'COMPRA' if x == 0 else 'VENDA')
            df_pos['time'] = pd.to_datetime(df_pos['time'], unit='s')
            st.dataframe(df_pos[['ticket', 'time', 'type', 'volume', 'price_open', 'price_current', 'sl', 'tp', 'profit', 'magic']])
        else:
            st.info(f"Nenhuma posição aberta para {symbol_input}.")
            
        # Live Logs
        st.subheader("Logs da Estratégia")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                st.code("".join(lines[-20:])) # Show last 20 lines

        st.divider()
        st.subheader("Monitoramento do Agente (IA)")
        
        AGENT_STATUS_FILE = os.path.join(BASE_DIR, "agent_status.json")
        if os.path.exists(AGENT_STATUS_FILE):
            try:
                with open(AGENT_STATUS_FILE, "r") as f:
                    agent_status = json.load(f)
                
                # Check latency
                last_update = datetime.fromisoformat(agent_status['timestamp'])
                latency = (datetime.now() - last_update).total_seconds()
                
                status_color = "green" if latency < 10 else "red"
                st.markdown(f"**Status:** <span style='color:{status_color}'>{'ATIVO' if latency < 10 else 'INATIVO'}</span> (Última atualização: {last_update.strftime('%H:%M:%S')})", unsafe_allow_html=True)
                
                # Parameters
                params = agent_status['parameters']
                market = agent_status.get('market_status', {})
                current_atr = market.get('atr', 0)
                
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                
                regime = params.get('current_regime', 'Normal')
                sl_mult = params.get('sl_multiplier', 2.0)
                tp_mult = params.get('tp_multiplier', 4.0)
                
                # Calculate estimated points for display
                est_sl = current_atr * sl_mult
                est_tp = current_atr * tp_mult
                
                c1.metric("Regime", regime)
                c2.metric("SL (Dinâmico)", f"{est_sl:.0f} pts", f"{sl_mult:.1f}x ATR")
                c3.metric("TP (Dinâmico)", f"{est_tp:.0f} pts", f"{tp_mult:.1f}x ATR")
                c4.metric("Trailing Start", f"{2.0 * current_atr:.0f} pts", "2.0x ATR")
                c5.metric("BreakEven", f"{1.5 * current_atr:.0f} pts", "1.5x ATR")
                c6.metric("Profit Lock", f"{params['profit_lock_percent']*100:.0f}%")
                
                st.caption(f"Monitorando {agent_status['active_tracking']} posições. Histórico de aprendizado: {agent_status['learning_history_size']} bytes.")
                
                st.divider()
                st.subheader("Status dos Filtros (Mercado)")
                
                market = agent_status.get('market_status', {})
                if market:
                    mc1, mc2, mc3 = st.columns(3)
                    
                    # ATR Status
                    atr_val = market.get('atr', 0)
                    atr_thresh = market.get('atr_threshold', 0)
                    is_vol_ok = market.get('is_volatility_ok', False)
                    vol_color = "green" if is_vol_ok else "red"
                    
                    mc1.metric("Volatilidade (ATR)", f"{atr_val:.1f} pts", delta=f"{atr_val - atr_thresh:.1f} pts vs Min {atr_thresh}", delta_color="normal" if is_vol_ok else "inverse")
                    mc1.markdown(f"Status: <span style='color:{vol_color}'>{'OK' if is_vol_ok else 'BAIXA VOLATILIDADE'}</span>", unsafe_allow_html=True)
                    
                    # Time Status
                    curr_hour = market.get('current_hour', 0)
                    is_time_ok = market.get('is_time_ok', False)
                    time_color = "green" if is_time_ok else "red"
                    
                    mc2.metric("Horário Atual", f"{curr_hour}:00", delta="Dentro do Horário" if is_time_ok else "Fora do Horário")
                    mc2.markdown(f"Status: <span style='color:{time_color}'>{'NEGOCIAÇÃO PERMITIDA' if is_time_ok else 'MERCADO FECHADO'}</span>", unsafe_allow_html=True)
                    
                else:
                    st.info("Aguardando dados de mercado...")
                
            except Exception as e:
                st.error(f"Erro ao ler status do agente: {e}")
        else:
            st.info("Aguardando dados do agente...")

# --- Tab 2: Backtest ---
with tab2:
    st.header("Backtest (Simulação)")
    if st.button("Executar Backtest"):
        with st.spinner("Rodando Backtest..."):
            cmd = ["python", BACKTEST_SCRIPT, "--symbol", symbol_input]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_DIR)
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
            cmd = ["python", OPTIMIZER_SCRIPT, "--symbol", symbol_input]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_DIR)
            st.code(result.stdout)
            if result.stderr:
                st.error(result.stderr)

# Auto Refresh logic
if pid or auto_refresh:
    time.sleep(5)
    st.rerun()
