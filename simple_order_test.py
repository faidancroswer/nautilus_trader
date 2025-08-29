import MetaTrader5 as mt5

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

def simple_buy_order():
    '''
    Place a simple buy order
    '''
    symbol = "EURUSD"
    lot = 0.1
    
    # Get symbol info
    symbol_info = get_symbol_info(symbol)
    if symbol_info is None:
        return False
    
    # Check if symbol is available for trading
    if not symbol_info.visible:
        print(f"Symbol {symbol} is not visible, trying to select it")
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to select symbol {symbol}")
            return False
    
    # Get current price
    price = mt5.symbol_info_tick(symbol).ask
    print(f"Current ask price: {price}")
    
    # Prepare request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "Python script open",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,  # Change to FOK (Fill or Kill)
    }
    
    # Send order
    result = mt5.order_send(request)
    if result is None:
        print("order_send() failed, error code =", mt5.last_error())
        return False
    
    print(f"Order send result: {result}")
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed with retcode {result.retcode}")
        # Print error description
        error_descriptions = {
            10004: "Requote",
            10006: "Request rejected",
            10007: "Too frequent requests",
            10011: "No changes in request",
            10013: "Market closed",
            10014: "Not enough money",
            10018: "Position closed",
            10019: "Invalid price",
            10020: "Invalid stops",
            10021: "Invalid lot",
            10022: "Invalid order type",
            10023: "Invalid trade parameters",
            10024: "Invalid trade context",
            10025: "Invalid trade state",
            10026: "Invalid trade expert",
            10027: "Trade timeout",
            10028: "Invalid trade volume",
            10029: "Invalid trade price",
            10030: "Invalid stops",
            10031: "Invalid trade expiration",
            10032: "Trade context locked",
            10033: "Invalid trade parameters",
            10034: "Invalid trade parameters",
            10035: "Invalid trade parameters",
            10036: "Invalid trade parameters"
        }
        
        error_desc = error_descriptions.get(result.retcode, "Unknown error")
        print(f"Error description: {error_desc}")
        
        return False
    
    print(f"Order placed successfully: BUY {lot} {symbol} at {price}")
    return True

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
    
    # Place a simple buy order
    print("\nPlacing simple BUY order...")
    simple_buy_order()
    
    # Shutdown MT5
    shutdown_mt5()

if __name__ == "__main__":
    main()