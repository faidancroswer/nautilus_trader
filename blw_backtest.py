import pandas as pd
import numpy as np
from blw_strategy import BLWStrategy
import matplotlib.pyplot as plt

class Backtester:
    def __init__(self, strategy, data_path=None):
        self.strategy = strategy
        self.data = None
        if data_path:
            self.load_data(data_path)
            
    def load_data(self, path):
        # Load data from CSV or generate synthetic data
        # For now, we'll assume we can get data from MT5 or use a sample CSV
        pass
        
    def fetch_data_from_mt5(self, bars=5000):
        self.data = self.strategy.get_data(bars)
        if self.data is not None:
            print(f"Loaded {len(self.data)} bars from MT5")
            
    def run_backtest(self, silent=False):
        if self.data is None:
            if not silent: print("No data loaded")
            return 0
            
        if not silent: print("Running backtest...")
        
        balance = 10000
        equity = 10000
        trades = []
        active_orders = [] 
        positions = [] 
        
        equity_curve = []
        
        df = self.data.copy()
        
        # Pre-calculate ZigZag for speed (Approximation)
        # We calculate it once. This means we see the "final" zigzag.
        # This introduces lookahead bias because the last leg changes.
        # However, for optimization of SL/TP/Depth, it might be acceptable if we are careful.
        # A better way is to use a windowed calculation but it's slow.
        # We will proceed with windowed calculation for accuracy as requested by user "optimize profit".
        # False optimization is worse than slow optimization.
        
        # Optimization: We can limit the window size.
        
        for i in range(100, len(df)):
            # Windowed calculation
            window = df.iloc[i-100:i+1].copy().reset_index(drop=True)
            current_bar = df.iloc[i]
            
            # Get Signals
            signals = self.strategy.get_signal(window)
            
            if signals:
                active_orders = [] # Reset pending orders
                active_orders.append({
                    'type': 'BUY_STOP',
                    'price': signals['buy_stop'],
                    'sl': signals['sl_buy'],
                    'tp': signals['tp_buy']
                })
                active_orders.append({
                    'type': 'SELL_STOP',
                    'price': signals['sell_stop'],
                    'sl': signals['sl_sell'],
                    'tp': signals['tp_sell']
                })
                
            # Check Order Execution
            high = current_bar['high']
            low = current_bar['low']
            
            new_positions = []
            for order in active_orders:
                if order['type'] == 'BUY_STOP':
                    if high >= order['price']:
                        positions.append({
                            'type': 'BUY',
                            'open_price': order['price'],
                            'sl': order['sl'],
                            'tp': order['tp'],
                            'open_time': current_bar['time']
                        })
                        if not silent: print(f"BUY Executed at {order['price']} on {current_bar['time']}")
                elif order['type'] == 'SELL_STOP':
                    if low <= order['price']:
                        positions.append({
                            'type': 'SELL',
                            'open_price': order['price'],
                            'sl': order['sl'],
                            'tp': order['tp'],
                            'open_time': current_bar['time']
                        })
                        if not silent: print(f"SELL Executed at {order['price']} on {current_bar['time']}")
            
            # Check Position Exit (SL/TP)
            remaining_positions = []
            for pos in positions:
                closed = False
                pnl = 0
                if pos['type'] == 'BUY':
                    if low <= pos['sl']:
                        pnl = (pos['sl'] - pos['open_price'])
                        closed = True
                    elif high >= pos['tp']:
                        pnl = (pos['tp'] - pos['open_price'])
                        closed = True
                elif pos['type'] == 'SELL':
                    if high >= pos['sl']:
                        pnl = (pos['open_price'] - pos['sl'])
                        closed = True
                    elif low <= pos['tp']:
                        pnl = (pos['open_price'] - pos['tp'])
                        closed = True
                        
                if closed:
                    balance += pnl * 1 # Raw points
                    trades.append(pnl)
                    if not silent: print(f"Closed {pos['type']} PnL: {pnl}")
                else:
                    remaining_positions.append(pos)
            
            positions = remaining_positions
            equity_curve.append(balance)
            
        if not silent:
            print(f"Final Balance: {balance}")
            plt.plot(equity_curve)
            plt.title("Equity Curve")
            plt.savefig("backtest_result.png")
            
        return balance

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='BLW Backtester')
    parser.add_argument('--symbol', type=str, default="XAUUSD", help='Trading Symbol')
    args = parser.parse_args()

    strategy = BLWStrategy(symbol=args.symbol)
    backtester = Backtester(strategy)
    backtester.fetch_data_from_mt5(1000) # Fetch 1000 bars
    backtester.run_backtest()
