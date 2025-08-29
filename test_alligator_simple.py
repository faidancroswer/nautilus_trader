import pandas as pd
import matplotlib.pyplot as plt
import MetaTrader5 as mt5
import numpy as np

def calculate_sma(data, period):
    """Calculate Simple Moving Average"""
    return data.rolling(window=period).mean()

def calculate_alligator(close_prices):
    """Calculate Alligator Indicator"""
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

def main():
    # Inicializar MT5
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    
    # Definir o símbolo
    symbol = "EURUSD"
    
    # Obter dados históricos
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
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
    
    # Plotar os resultados
    plt.figure(figsize=(12, 8))
    plt.plot(df['time'], df['close'], label='Close', linewidth=1)
    plt.plot(df['time'], df['jaw'], label='Jaw (Blue)', linewidth=1)
    plt.plot(df['time'], df['teeth'], label='Teeth (Red)', linewidth=1)
    plt.plot(df['time'], df['lips'], label='Lips (Green)', linewidth=1)
    plt.legend()
    plt.title('Alligator Indicator')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.grid(True)
    plt.show()
    
    # Imprimir valores para verificação
    print(df[['time', 'close', 'jaw', 'teeth', 'lips']].tail(10))
    
    # Finalizar conexão com MT5
    mt5.shutdown()

if __name__ == "__main__":
    main()