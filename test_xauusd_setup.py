import MetaTrader5 as mt5
import json

def test_xauusd_setup():
    """Test XAUUSD setup and analysis"""
    print("Testing XAUUSD setup...")
    
    # Initialize MT5
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return False
    
    # Check if XAUUSD is available
    symbol = "XAUUSD"
    symbol_info = mt5.symbol_info(symbol)
    
    if symbol_info is None:
        print(f"Failed to get symbol info for {symbol}")
        mt5.shutdown()
        return False
    
    print(f"Symbol: {symbol_info.name}")
    print(f"Point value: {symbol_info.point}")
    print(f"Digits: {symbol_info.digits}")
    print(f"Spread: {symbol_info.spread}")
    
    # Select symbol
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to select symbol {symbol}")
            mt5.shutdown()
            return False
    
    # Get current price
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"Current ask: {tick.ask}")
        print(f"Current bid: {tick.bid}")
    else:
        print("Failed to get current price")
    
    # Get recent market data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 10)
    if rates is not None:
        print(f"Retrieved {len(rates)} recent candles")
        print("Latest candle:")
        print(f"  Open: {rates[-1]['open']}")
        print(f"  High: {rates[-1]['high']}")
        print(f"  Low: {rates[-1]['low']}")
        print(f"  Close: {rates[-1]['close']}")
    else:
        print("Failed to get market data")
    
    mt5.shutdown()
    return True

if __name__ == "__main__":
    test_xauusd_setup()