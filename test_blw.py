import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import sys

# Mock mt5 before importing blw_strategy
sys.modules['MetaTrader5'] = MagicMock()
import MetaTrader5 as mt5

from blw_strategy import BLWStrategy

class TestBLWStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = BLWStrategy()
        
    def test_zigzag_calculation(self):
        # Create synthetic data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
        # Create a zigzag pattern: Up, Down, Up
        prices = [100 + i for i in range(20)] + \
                 [120 - i for i in range(20)] + \
                 [100 + i for i in range(20)] + \
                 [120 - i for i in range(20)] + \
                 [100 + i for i in range(20)]
                 
        df = pd.DataFrame({
            'time': dates,
            'high': prices,
            'low': prices, # Simplified
            'close': prices,
            'tick_volume': 100,
            'spread': 10,
            'real_volume': 100
        })
        
        df = self.strategy.calculate_zigzag(df, depth=12, deviation=5, backstep=3)
        
        # Check if we have zigzag points
        zz_points = df[df['zigzag'].notna()]
        print("\nZigZag Points found:")
        print(zz_points[['time', 'zigzag']])
        
        self.assertTrue(len(zz_points) > 0)
        
    def test_signal_generation(self):
        # Create data that should trigger a signal
        dates = pd.date_range(start='2024-01-01', periods=50, freq='H')
        prices = [100 + i for i in range(20)] + [120 - i for i in range(20)] + [100 + i for i in range(10)]
        df = pd.DataFrame({
            'time': dates,
            'high': prices,
            'low': prices,
            'close': prices
        })
        
        signal = self.strategy.get_signal(df)
        print(f"\nSignal: {signal}")
        
        self.assertIsNotNone(signal)
        self.assertIn('buy_stop', signal)
        self.assertIn('sell_stop', signal)

if __name__ == '__main__':
    unittest.main()
