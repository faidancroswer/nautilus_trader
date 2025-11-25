import pandas as pd
import itertools
from blw_strategy import BLWStrategy
from blw_backtest import Backtester
import MetaTrader5 as mt5

class Optimizer:
    def __init__(self):
        self.strategy = BLWStrategy()
        self.data = None
        
    def load_data(self, bars=5000):
        print("Fetching data for optimization...")
        self.data = self.strategy.get_data(bars)
        if self.data is None:
            print("Failed to fetch data")
            
    def run_optimization(self):
        if self.data is None:
            self.load_data()
            if self.data is None:
                return

        # Parameter Ranges
        sl_range = [1000, 2000, 3000]
        tp_range = [2000, 5000, 10000]
        depth_range = [12, 18, 24]
        
        combinations = list(itertools.product(sl_range, tp_range, depth_range))
        print(f"Testing {len(combinations)} combinations...")
        
        results = []
        
        for sl, tp, depth in combinations:
            # Update Strategy Parameters
            # Note: We need to modify the global variables or strategy instance variables
            # Since the strategy uses global variables in the current implementation, 
            # we might need to refactor or monkeypatch.
            # Ideally, strategy should accept params in __init__ or have setters.
            # For now, we will monkeypatch the module level variables if possible, 
            # or better, refactor BLWStrategy to use instance variables.
            
            # Let's assume we refactored or we just set them here if they were instance vars.
            # But they are globals in blw_strategy.py.
            # We can modify them via the module.
            
            import blw_strategy
            blw_strategy.STOP_LOSS = sl
            blw_strategy.TAKE_PROFIT = tp
            blw_strategy.EXT_DEPTH = depth
            
            # Run Backtest
            # We need a headless backtester that returns metrics
            backtester = Backtester(self.strategy)
            backtester.data = self.data # Share data to avoid re-fetching
            
            # We need to capture the result. 
            # Currently backtester prints result. We should modify it to return it.
            # Or we can just calculate it here if we move logic.
            
            # Let's modify Backtester to return balance.
            final_balance = self.run_backtest_headless(backtester)
            
            print(f"Params: SL={sl}, TP={tp}, Depth={depth} -> Balance: {final_balance}")
            results.append({
                'sl': sl,
                'tp': tp,
                'depth': depth,
                'balance': final_balance
            })
            
        # Find Best
        best_result = max(results, key=lambda x: x['balance'])
        print("\nOptimization Complete!")
        print(f"Best Params: SL={best_result['sl']}, TP={best_result['tp']}, Depth={best_result['depth']}")
        print(f"Best Balance: {best_result['balance']}")
        
    def run_backtest_headless(self, backtester):
        # Use the refactored backtester
        return backtester.run_backtest(silent=True)

if __name__ == "__main__":
    import blw_strategy # Import to modify globals
    opt = Optimizer()
    opt.run_optimization()
