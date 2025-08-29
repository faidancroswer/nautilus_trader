import pandas as pd
import MetaTrader5 as mt5
import numpy as np

def calculate_sma(data, period):
    """
    Calculate Simple Moving Average
    """
    return data.rolling(window=period).mean()

def calculate_alligator(close_prices):
    """
    Calculate Alligator Indicator
    """
    # Jaw (Blue) - 13 periods, shifted 8 bars into the future
    jaw = calculate_sma(close_prices, 13)
    jaw = jaw.shift(8)
    
    # Teeth (Red) - 8 periods, shifted 5 bars into the future
    teeth = calculate_sma(close_prices, 8)
    teeth = teeth.shift(5)
    
    # Lips (Green) - 5 periods, shifted 3 bars into the future
    lips = calculate_sma(close_prices, 5)
    lips = lips.shift(3)
    
    return jaw, teeth, lips

def generate_signals(df):
    """
    Generate trading signals based on Alligator indicator
    """
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

def main():
    # Inicializar MT5
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    
    # Definir o símbolo
    symbol = "EURUSD"
    
    # Obter dados históricos
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1000)
    if rates is None:
        print("copy_rates_from_pos() failed, error code =", mt5.last_error())
        mt5.shutdown()
        quit()
    
    # Converter para DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calcular o indicador Alligator
    jaw, teeth, lips = calculate_alligator(df['close'])
    
    # Adicionar ao DataFrame
    df['jaw'] = jaw
    df['teeth'] = teeth
    df['lips'] = lips
    
    # Gerar sinais de trading
    buy_signal, sell_signal = generate_signals(df)
    df['buy_signal'] = buy_signal
    df['sell_signal'] = sell_signal
    
    # Exibir sinais de compra
    print("Buy Signals:")
    buy_signals = df[df['buy_signal'] == True]
    print(buy_signals[['time', 'close', 'jaw', 'teeth', 'lips']].tail(5))
    
    # Exibir sinais de venda
    print("\nSell Signals:")
    sell_signals = df[df['sell_signal'] == True]
    print(sell_signals[['time', 'close', 'jaw', 'teeth', 'lips']].tail(5))
    
    # Calcular estatísticas básicas
    print(f"\nTotal Buy Signals: {buy_signals.shape[0]}")
    print(f"Total Sell Signals: {sell_signals.shape[0]}")
    
    # Finalizar conexão com MT5
    mt5.shutdown()

if __name__ == "__main__":
    main()