import pandas as pd
import matplotlib.pyplot as plt
import MetaTrader5 as mt5
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import Price
from nautilus_trader.model.data import Quantity
from nautilus_trader.model.enums import PriceType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Price as PriceObject
from nautilus_trader.model.objects import Quantity as QuantityObject

# Import our custom Alligator indicator
from alligator_indicator import AlligatorIndicator

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
    
    # Criar instância do indicador Alligator
    alligator = AlligatorIndicator(
        jaw_period=13,
        jaw_shift=8,
        teeth_period=8,
        teeth_shift=5,
        lips_period=5,
        lips_shift=3
    )
    
    # Processar os dados
    jaw_values = []
    teeth_values = []
    lips_values = []
    close_prices = []
    timestamps = []
    
    for i, rate in enumerate(rates):
        # Criar um objeto Bar para o indicador
        # Nota: Este é um exemplo simplificado. Em prática, você precisaria criar
        # objetos Bar completos com todos os campos necessários.
        bar = Bar(
            bar_type=BarType.from_str("EUR/USD.FBS-1-MINUTE-BID-INTERNAL"),
            open=PriceObject(rate['open'], 5),
            high=PriceObject(rate['high'], 5),
            low=PriceObject(rate['low'], 5),
            close=PriceObject(rate['close'], 5),
            volume=QuantityObject(rate['tick_volume'], 0),
            ts_event=rate['time'] * 1_000_000_000,  # Converter para nanossegundos
            ts_init=rate['time'] * 1_000_000_000,
        )
        
        # Atualizar o indicador com a barra
        alligator.handle_bar(bar)
        
        # Armazenar valores para plotagem
        close_prices.append(rate['close'])
        timestamps.append(rate['time'])
        jaw_values.append(alligator.jaw if alligator.initialized else None)
        teeth_values.append(alligator.teeth if alligator.initialized else None)
        lips_values.append(alligator.lips if alligator.initialized else None)
        
        # Imprimir valores para verificação
        if i % 10 == 0:  # Imprimir a cada 10 iterações
            print(f"Bar {i}: Close={rate['close']:.5f}, Jaw={alligator.jaw:.5f}, Teeth={alligator.teeth:.5f}, Lips={alligator.lips:.5f}")
    
    # Plotar os resultados
    plt.figure(figsize=(12, 8))
    plt.plot(timestamps, close_prices, label='Close', linewidth=1)
    plt.plot(timestamps, jaw_values, label='Jaw (Blue)', linewidth=1)
    plt.plot(timestamps, teeth_values, label='Teeth (Red)', linewidth=1)
    plt.plot(timestamps, lips_values, label='Lips (Green)', linewidth=1)
    plt.legend()
    plt.title('Alligator Indicator')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.grid(True)
    plt.show()
    
    # Finalizar conexão com MT5
    mt5.shutdown()

if __name__ == "__main__":
    main()