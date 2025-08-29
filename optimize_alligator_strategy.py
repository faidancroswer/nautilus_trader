import pandas as pd
import MetaTrader5 as mt5
import numpy as np

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

def backtest_strategy(df, buy_signals, sell_signals, initial_capital=10000.0):
    '''
    Simple backtest of the strategy
    '''
    # Inicializar variáveis
    capital = initial_capital
    position = 0  # 0 = fora do mercado, 1 = long, -1 = short
    entry_price = 0
    trades = []
    
    # Iterar pelos sinais
    for i in range(len(df)):
        # Entrar em posição long
        if buy_signals.iloc[i] and position == 0:
            position = 1
            entry_price = df['close'].iloc[i]
            trades.append({
                'type': 'BUY',
                'entry_time': df['time'].iloc[i],
                'entry_price': entry_price,
                'exit_time': None,
                'exit_price': None,
                'pnl': 0
            })
        
        # Entrar em posição short
        elif sell_signals.iloc[i] and position == 0:
            position = -1
            entry_price = df['close'].iloc[i]
            trades.append({
                'type': 'SELL',
                'entry_time': df['time'].iloc[i],
                'entry_price': entry_price,
                'exit_time': None,
                'exit_price': None,
                'pnl': 0
            })
        
        # Sair de posição long
        elif sell_signals.iloc[i] and position == 1:
            position = 0
            exit_price = df['close'].iloc[i]
            # Atualizar última operação
            if trades:
                trades[-1]['exit_time'] = df['time'].iloc[i]
                trades[-1]['exit_price'] = exit_price
                trades[-1]['pnl'] = (exit_price - entry_price) * 100000  # Assumindo 1 lote = 100.000 unidades
                capital += trades[-1]['pnl']
        
        # Sair de posição short
        elif buy_signals.iloc[i] and position == -1:
            position = 0
            exit_price = df['close'].iloc[i]
            # Atualizar última operação
            if trades:
                trades[-1]['exit_time'] = df['time'].iloc[i]
                trades[-1]['exit_price'] = exit_price
                trades[-1]['pnl'] = (entry_price - exit_price) * 100000  # Assumindo 1 lote = 100.000 unidades
                capital += trades[-1]['pnl']
    
    return capital, trades

def optimize_parameters(df):
    '''
    Simple parameter optimization
    '''
    best_pnl = -np.inf
    best_params = None
    
    # Definir ranges de parâmetros para otimização
    jaw_periods = [10, 13, 15]
    teeth_periods = [7, 8, 10]
    lips_periods = [3, 5, 7]
    
    jaw_shifts = [5, 8, 10]
    teeth_shifts = [3, 5, 7]
    lips_shifts = [1, 3, 5]
    
    total_combinations = len(jaw_periods) * len(teeth_periods) * len(lips_periods) * \
                         len(jaw_shifts) * len(teeth_shifts) * len(lips_shifts)
    
    print(f"Testing {total_combinations} parameter combinations...")
    
    count = 0
    for jp in jaw_periods:
        for jsh in jaw_shifts:
            for tp in teeth_periods:
                for tsh in teeth_shifts:
                    for lp in lips_periods:
                        for lsh in lips_shifts:
                            count += 1
                            if count % 100 == 0:
                                print(f"Tested {count}/{total_combinations} combinations...")
                            
                            # Calcular o indicador com os parâmetros atuais
                            jaw, teeth, lips = calculate_alligator(
                                df['close'], jp, jsh, tp, tsh, lp, lsh
                            )
                            
                            # Adicionar ao DataFrame
                            df_test = df.copy()
                            df_test['jaw'] = jaw
                            df_test['teeth'] = teeth
                            df_test['lips'] = lips
                            
                            # Gerar sinais
                            buy_signal, sell_signal = generate_signals(df_test)
                            
                            # Backtest
                            final_capital, trades = backtest_strategy(df_test, buy_signal, sell_signal)
                            total_pnl = final_capital - 10000.0
                            
                            # Verificar se é o melhor resultado
                            if total_pnl > best_pnl:
                                best_pnl = total_pnl
                                best_params = {
                                    'jaw_period': jp,
                                    'jaw_shift': jsh,
                                    'teeth_period': tp,
                                    'teeth_shift': tsh,
                                    'lips_period': lp,
                                    'lips_shift': lsh
                                }
    
    return best_params, best_pnl

def main():
    # Inicializar MT5
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    
    # Definir o símbolo
    symbol = "EURUSD"
    
    # Obter dados históricos (mais dados para otimização)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 5000)
    if rates is None:
        print("copy_rates_from_pos() failed, error code =", mt5.last_error())
        mt5.shutdown()
        quit()
    
    # Converter para DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calcular o indicador Alligator com parâmetros padrão
    jaw, teeth, lips = calculate_alligator(df['close'])
    
    # Adicionar ao DataFrame
    df['jaw'] = jaw
    df['teeth'] = teeth
    df['lips'] = lips
    
    # Gerar sinais de trading
    buy_signal, sell_signal = generate_signals(df)
    df['buy_signal'] = buy_signal
    df['sell_signal'] = sell_signal
    
    # Executar backtest
    final_capital, trades = backtest_strategy(df, buy_signal, sell_signal)
    
    # Exibir resultados
    print(f"Initial Capital: $10,000.00")
    print(f"Final Capital: ${final_capital:.2f}")
    print(f"Total PnL: ${final_capital - 10000.0:.2f}")
    print(f"Total Trades: {len(trades)}")
    
    # Exibir últimas operações
    print("\nLast 5 Trades:")
    for trade in trades[-5:]:
        exit_time = trade['exit_time'] if trade['exit_time'] else "Open"
        exit_price = f"{trade['exit_price']:.5f}" if trade['exit_price'] else "N/A"
        print(f"{trade['type']} at {trade['entry_time']} price {trade['entry_price']:.5f}, "
              f"Exit at {exit_time} price {exit_price}, PnL: ${trade['pnl']:.2f}")
    
    # Otimizar parâmetros (comentado para evitar tempo excessivo de execução)
    # print("\nOptimizing parameters...")
    # best_params, best_pnl = optimize_parameters(df)
    # print(f"Best Parameters: {best_params}")
    # print(f"Best PnL: ${best_pnl:.2f}")
    
    # Finalizar conexão com MT5
    mt5.shutdown()

if __name__ == "__main__":
    main()