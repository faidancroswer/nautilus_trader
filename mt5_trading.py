import MetaTrader5 as mt5
import time

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
        sl = price - sl_points * symbol_info.point
        tp = price + tp_points * symbol_info.point
    else:
        order_type_str = "SELL"
        if price is None:
            price = mt5.symbol_info_tick(symbol).bid
        sl = price + sl_points * symbol_info.point
        tp = price - tp_points * symbol_info.point
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 234000,
        "comment": f"Nautilus {order_type_str} Order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    
    # Send order
    result = mt5.order_send(request)
    if result is None:
        print("order_send() failed, error code =", mt5.last_error())
        return False
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed with retcode {result.retcode}")
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

def main():
    # Initialize MT5
    if not initialize_mt5():
        return
    
    # Get account info
    account_info = get_account_info()
    if account_info is not None:
        print(f"Connected to account {account_info.login}")
        print(f"Balance: {account_info.balance} {account_info.currency}")
    
    # Example: Place a buy order
    symbol = "EURUSD"
    volume = 0.1  # 0.1 lot
    sl_points = 100  # 100 points stop loss
    tp_points = 100  # 100 points take profit
    
    # Place a buy order
    print("\nPlacing BUY order...")
    place_order(symbol, mt5.ORDER_TYPE_BUY, volume, sl_points=sl_points, tp_points=tp_points)
    
    # Wait a bit
    time.sleep(5)
    
    # Get open positions
    positions = get_positions()
    print(f"\nOpen positions: {len(positions)}")
    for position in positions:
        print(f"Position {position.ticket}: {position.symbol} {position.volume} "
              f"{position.type_str} at {position.price_open}")
    
    # Wait a bit more
    time.sleep(5)
    
    # Close all positions
    print("\nClosing all positions...")
    for position in positions:
        close_position(position.ticket)
    
    # Shutdown MT5
    shutdown_mt5()

if __name__ == "__main__":
    main()