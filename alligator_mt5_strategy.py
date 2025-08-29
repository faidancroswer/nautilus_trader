import pandas as pd
import MetaTrader5 as mt5
import numpy as np
import time
from datetime import datetime

def calculate_sma(data, period):
    '''
    Calculate Simple Moving Average
    '''
    return data.rolling(window=period).mean()

def calculate_alligator(close_prices, jaw_period=13, jaw_shift=8, teeth_period=8, teeth_shift=5, lips_period=5, lips_shift=3):
    '''
    Calculate Alligator Indicator with customizable parameters
    '''
    # Jaw (Blue)
    jaw = calculate_sma(close_prices, jaw_period)
    jaw = jaw.shift(jaw_shift)
    
    # Teeth (Red)
    teeth = calculate_sma(close_prices, teeth_period)
    teeth = teeth.shift(teeth_shift)
    
    # Lips (Green)
    lips = calculate_sma(close_prices, lips_period)
    lips = lips.shift(lips_shift)
    
    return jaw, teeth, lips

def generate_signals(df):
    '''
    Generate trading signals based on Alligator indicator
    '''
    # Buy signal: Price above all lines and ascending order (lips > teeth > jaw)
    buy_signal = (
        (df['close'] > df['lips']) & 
        (df['lips'] > df['teeth']) & 
        (df['teeth'] > df['jaw'])
    )
    
    # Sell signal: Price below all lines and descending order (lips < teeth < jaw)
    sell_signal = (
        (df['close'] < df['lips']) & 
        (df['lips'] < df['teeth']) & 
        (df['teeth'] < df['jaw'])
    )
    
    return buy_signal, sell_signal

def initialize_mt5():
    '''
    Initialize MT5 connection
    '''
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return False
    return True

def get_account_info():
    '''
    Get account information
    '''
    account_info = mt5.account_info()
    if account_info is None:
        print("account_info() failed, error code =", mt5.last_error())
        return None
    return account_info

def get_symbol_info(symbol):
    '''
    Get symbol information
    '''
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"symbol_info({symbol}) failed, error code =", mt5.last_error())
        return None
    return symbol_info

def place_order(symbol, order_type, volume, price=None, sl_points=100, tp_points=100):
    '''
    Place an order
    
    Parameters:
    symbol (str): Symbol to trade
    order_type (int): mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL
    volume (float): Volume to trade
    price (float): Price for pending orders (None for market orders)
    sl_points (int): Stop loss in points
    tp_points (int): Take profit in points
    '''
    # Get symbol information
    symbol_info = get_symbol_info(symbol)
    if symbol_info is None:
        return False
    
    # Prepare request
    if order_type == mt5.ORDER_TYPE_BUY:
        order_type_str = "BUY"
        if price is None:
            price = mt5.symbol_info_tick(symbol).ask
        # Verificar se o SL/TP está dentro dos limites permitidos
        sl = price - sl_points * symbol_info.point
        tp = price + tp_points * symbol_info.point
        # Garantir que SL não seja maior que o preço atual (para ordens de compra)
        if sl >= price:
            sl = price - symbol_info.point  # Ajustar para 1 ponto abaixo
        # Garantir que TP não seja menor que o preço atual (para ordens de compra)
        if tp <= price:
            tp = price + symbol_info.point  # Ajustar para 1 ponto acima
    else:
        order_type_str = "SELL"
        if price is None:
            price = mt5.symbol_info_tick(symbol).bid
        # Verificar se o SL/TP está dentro dos limites permitidos
        sl = price + sl_points * symbol_info.point
        tp = price - tp_points * symbol_info.point
        # Garantir que SL não seja menor que o preço atual (para ordens de venda)
        if sl <= price:
            sl = price + symbol_info.point  # Ajustar para 1 ponto acima
        # Garantir que TP não seja maior que o preço atual (para ordens de venda)
        if tp >= price:
            tp = price - symbol_info.point  # Ajustar para 1 ponto abaixo
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": f"Nautilus {order_type_str} Order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,  # Fill or Kill
    }
    
    # Send order
    result = mt5.order_send(request)
    if result is None:
        print("order_send() failed, error code =", mt5.last_error())
        return False
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed with retcode {result.retcode}")
        # Print additional information for debugging
        print(f"Request: {request}")
        print(f"Symbol info: {symbol_info}")
        return False
    
    print(f"Order placed successfully: {order_type_str} {volume} {symbol} at {price}")
    return True

def close_position(ticket):
    '''
    Close a position by ticket
    
    Parameters:
    ticket (int): Position ticket to close
    '''
    # Get position information
    position = mt5.positions_get(ticket=ticket)
    if position is None or len(position) == 0:
        print(f"Position {ticket} not found")
        return False
    
    position = position[0]
    
    # Prepare close request
    if position.type == mt5.POSITION_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(position.symbol).bid
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(position.symbol).ask
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": order_type,
        "position": ticket,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "Nautilus Close Order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    
    # Send close order
    result = mt5.order_send(request)
    if result is None:
        print("order_send() failed, error code =", mt5.last_error())
        return False
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Close order failed with retcode {result.retcode}")
        return False
    
    print(f"Position {ticket} closed successfully")
    return True

def get_positions():
    '''
    Get all open positions
    '''
    positions = mt5.positions_get()
    if positions is None:
        print("positions_get() failed, error code =", mt5.last_error())
        return []
    return positions

def shutdown_mt5():
    '''
    Shutdown MT5 connection
    '''
    mt5.shutdown()

def run_alligator_strategy():
    '''
    Run the Alligator trading strategy
    '''
    # Initialize MT5
    if not initialize_mt5():
        return
    
    # Get account info
    account_info = get_account_info()
    if account_info is not None:
        print(f"Connected to account {account_info.login}")
        print(f"Balance: {account_info.balance} {account_info.currency}")
    
    # Configuration
    symbol = "EURUSD"
    volume = 0.1  # 0.1 lot
    sl_points = 100  # 100 points stop loss
    tp_points = 100  # 100 points take profit
    
    # Get initial data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
    if rates is None:
        print("copy_rates_from_pos() failed, error code =", mt5.last_error())
        shutdown_mt5()
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate the Alligator indicator
    jaw, teeth, lips = calculate_alligator(df['close'])
    
    # Add to DataFrame
    df['jaw'] = jaw
    df['teeth'] = teeth
    df['lips'] = lips
    
    # Generate initial signals
    buy_signal, sell_signal = generate_signals(df)
    df['buy_signal'] = buy_signal
    df['sell_signal'] = sell_signal
    
    # Check last signal
    last_buy = df['buy_signal'].iloc[-1]
    last_sell = df['sell_signal'].iloc[-1]
    
    print(f"Last BUY signal: {last_buy}")
    print(f"Last SELL signal: {last_sell}")
    
    # Get open positions
    positions = get_positions()
    print(f"Open positions: {len(positions)}")
    
    # Simple trading logic
    if last_buy and len(positions) == 0:
        print("\nPlacing BUY order...")
        place_order(symbol, mt5.ORDER_TYPE_BUY, volume, sl_points=sl_points, tp_points=tp_points)
    elif last_sell and len(positions) == 0:
        print("\nPlacing SELL order...")
        place_order(symbol, mt5.ORDER_TYPE_SELL, volume, sl_points=sl_points, tp_points=tp_points)
    elif len(positions) > 0:
        # Close positions if signal is opposite
        position = positions[0]
        if (position.type == mt5.POSITION_TYPE_BUY and last_sell) or \
           (position.type == mt5.POSITION_TYPE_SELL and last_buy):
            print(f"\nClosing position {position.ticket}...")
            close_position(position.ticket)
    
    # Shutdown MT5
    shutdown_mt5()

def main():
    print(f"Starting Alligator Strategy at {datetime.now()}")
    run_alligator_strategy()
    print(f"Strategy execution completed at {datetime.now()}")

if __name__ == "__main__":
    main()