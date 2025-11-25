import streamlit as st
import MetaTrader5 as mt5
import pandas as pd
import time
import plotly.express as px
import os

# Page Config
st.set_page_config(page_title="BLW Strategy Dashboard", layout="wide")

# Constants
MAGIC = 1147485642
SYMBOL = "XAUUSD"

# Initialize MT5
if not mt5.initialize():
    st.error("MT5 Initialization Failed")
else:
    st.success(f"Connected to MT5: {mt5.version()}")

# Sidebar Controls
st.sidebar.title("Controls")
refresh_rate = st.sidebar.slider("Refresh Rate (s)", 1, 60, 5)

if st.sidebar.button("CLOSE ALL POSITIONS"):
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
        st.sidebar.success("Sent Close Commands")
    else:
        st.sidebar.warning("No open positions")

# Main Layout
st.title("BLW Strategy Manager")

# Account Info
account = mt5.account_info()
if account:
    col1, col2, col3 = st.columns(3)
    col1.metric("Balance", f"${account.balance:.2f}")
    col2.metric("Equity", f"${account.equity:.2f}")
    col3.metric("Profit", f"${account.profit:.2f}")

# Open Positions
st.subheader("Open Positions")
positions = mt5.positions_get(symbol=SYMBOL, magic=MAGIC)
if positions:
    df_pos = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
    df_pos['type'] = df_pos['type'].apply(lambda x: 'BUY' if x == 0 else 'SELL')
    df_pos['time'] = pd.to_datetime(df_pos['time'], unit='s')
    st.dataframe(df_pos[['ticket', 'time', 'type', 'volume', 'price_open', 'price_current', 'sl', 'tp', 'profit']])
else:
    st.info("No open positions")

# Performance Chart
st.subheader("Performance History")
history_file = "trade_history.csv"
if os.path.isfile(history_file):
    try:
        df_hist = pd.read_csv(history_file)
        if not df_hist.empty:
            # Clean up
            df_hist['Time'] = pd.to_datetime(df_hist['Time'])
            df_hist['Cumulative Profit'] = df_hist['Profit'].cumsum()
            
            fig = px.line(df_hist, x='Time', y='Cumulative Profit', title="Equity Curve (Closed Trades)")
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df_hist.sort_values('Time', ascending=False).head(10))
    except Exception as e:
        st.error(f"Error reading history: {e}")
else:
    st.warning("No trade history found yet.")

# Auto Refresh
time.sleep(refresh_rate)
st.rerun()
