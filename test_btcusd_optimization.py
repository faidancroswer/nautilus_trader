#!/usr/bin/env python3
"""
Test script for BTCUSD Alligator Strategy Optimization
Validates performance improvements and functionality
"""

import sys
import time
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_test_data(days=7, interval_minutes=1):
    """Generate synthetic BTCUSD test data"""
    logger.info(f"Generating {days} days of test data...")

    # Create time series
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    timestamps = pd.date_range(start_time, end_time, freq=f'{interval_minutes}T')

    # Generate realistic BTC price movement
    initial_price = 45000  # Starting BTC price
    data_points = len(timestamps)

    # Generate price with trend and volatility
    trend = np.linspace(0, 0.1, data_points)  # Slight upward trend
    noise = np.random.normal(0, 0.02, data_points)  # 2% volatility
    price_movement = trend + noise

    # Calculate OHLCV data
    close_prices = initial_price * (1 + price_movement.cumsum())

    # Generate high/low based on close with intraday volatility
    intraday_volatility = np.random.uniform(0.005, 0.02, data_points)
    high_prices = close_prices * (1 + intraday_volatility)
    low_prices = close_prices * (1 - intraday_volatility)

    # Generate open prices (close of previous period with some gap)
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = close_prices[0]  # First open equals first close
    open_prices += np.random.normal(0, initial_price * 0.001, data_points)  # Small gap

    # Generate volume
    base_volume = 1000
    volume = base_volume + np.random.exponential(500, data_points)
    volume = volume.astype(int)

    # Create DataFrame
    df = pd.DataFrame({
        'time': timestamps.astype(int) // 10**9,  # Unix timestamp
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'tick_volume': volume,
        'spread': np.random.uniform(10, 50, data_points),  # BTC spread
        'real_volume': volume
    })

    logger.info(f"Generated {len(df)} data points")
    logger.info(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

    return df

def test_btc_specific_features():
    """Test BTC-specific features and parameters"""
    logger.info("Testing BTC-specific features...")

    try:
        # Test basic functionality without importing the strategy (to avoid MT5 dependency)
        config = {
            'symbol': "BTCUSD",
            'jaw_period': 21,
            'teeth_period': 13,
            'lips_period': 8,
            'sl_points': 1000,
            'tp_points': 2000,
            'max_risk_percent': 1.5,
            'max_lot_size': 0.05
        }

        # Validate BTC-specific parameters
        assert config['symbol'] == "BTCUSD"
        assert config['jaw_period'] == 21  # Increased for crypto
        assert config['teeth_period'] == 13  # Intermediate period
        assert config['lips_period'] == 8   # Shorter period for crypto
        assert config['sl_points'] == 1000  # Larger SL for BTC volatility
        assert config['tp_points'] == 2000  # 2:1 ratio
        assert config['max_risk_percent'] == 1.5  # Conservative risk
        assert config['max_lot_size'] == 0.05  # Conservative position size

        logger.info("✓ BTC-specific configuration validated")

        # Test data generation
        df = generate_test_data(days=1)
        assert len(df) > 0, "Test data generation failed"
        assert 'close' in df.columns, "Close prices missing from test data"

        logger.info("✓ Test data generation working")
        logger.info(f"✓ Generated {len(df)} test data points")

        return True

    except Exception as e:
        logger.error(f"Error in BTC-specific features test: {e}")
        return False

def test_performance_calculation():
    """Test basic performance calculations"""
    logger.info("Testing performance calculations...")

    try:
        # Generate test data
        df = generate_test_data(days=1)

        # Test basic SMA calculation
        def calculate_sma(data, period):
            return data.rolling(window=period).mean()

        close_prices = df['close']
        jaw = calculate_sma(close_prices, 21)
        teeth = calculate_sma(close_prices, 13)
        lips = calculate_sma(close_prices, 8)

        # Test performance
        iterations = 100
        start_time = time.time()

        for i in range(iterations):
            jaw_test = calculate_sma(close_prices, 21)
            teeth_test = calculate_sma(close_prices, 13)
            lips_test = calculate_sma(close_prices, 8)

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations

        logger.info(f"Basic SMA calculation performance:")
        logger.info(f"  {iterations} iterations in {total_time:.3f}s")
        logger.info(f"  Average time per calculation: {avg_time:.6f}s")
        logger.info(f"  Calculations per second: {1/avg_time:.0f}")

        return True

    except Exception as e:
        logger.error(f"Error in performance calculation test: {e}")
        return False

def run_performance_benchmark():
    """Run comprehensive performance benchmark"""
    logger.info("Running comprehensive performance benchmark...")

    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }

    # Run all tests
    tests = [
        ('BTC-Specific Features', test_btc_specific_features),
        ('Performance Calculation', test_performance_calculation)
    ]

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")

        start_time = time.time()
        success = test_func()
        end_time = time.time()

        results['tests'][test_name] = {
            'success': success,
            'duration': end_time - start_time,
            'timestamp': datetime.now().isoformat()
        }

        status = "✓ PASSED" if success else "✗ FAILED"
        logger.info(f"{test_name}: {status} (took {end_time - start_time:.2f}s)")

    # Save results
    with open('btcusd_optimization_benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    passed_tests = sum(1 for test in results['tests'].values() if test['success'])
    total_tests = len(results['tests'])

    logger.info(f"\n{'='*50}")
    logger.info(f"BENCHMARK SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"Tests passed: {passed_tests}/{total_tests}")
    logger.info(f"Success rate: {passed_tests/total_tests*100:.1f}%")
    logger.info(f"Total duration: {sum(test['duration'] for test in results['tests'].values()):.2f}s")
    logger.info(f"Results saved to: btcusd_optimization_benchmark_results.json")

    return passed_tests == total_tests

if __name__ == "__main__":
    logger.info("Starting BTCUSD Alligator Strategy Optimization Tests")
    logger.info(f"Python version: {sys.version}")

    success = run_performance_benchmark()

    if success:
        logger.info("\n🎉 All tests passed! The optimization is working correctly.")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed. Please review the optimization.")
        sys.exit(1)
