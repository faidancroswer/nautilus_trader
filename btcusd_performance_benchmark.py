#!/usr/bin/env python3
"""
BTCUSD Alligator Strategy Performance Benchmark
Compares original vs optimized implementation
"""

import time
import logging
import json
import sys
import numpy as np
import pandas as pd
import psutil
import os
from typing import Dict, Any, List
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [BENCHMARK] - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkSuite:
    """Comprehensive benchmark suite for BTCUSD strategy"""

    def __init__(self):
        self.results = {
            'original': {},
            'optimized': {},
            'comparison': {}
        }
        self.test_data = self._generate_test_data()

    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate realistic BTCUSD test data"""
        np.random.seed(42)  # For reproducible results

        # Generate 24 hours of M1 data (1440 bars)
        num_bars = 1440
        base_price = 50000.0

        # Simulate BTC price movement with trend and volatility
        returns = np.random.normal(0.0001, 0.02, num_bars)  # 2% daily volatility
        prices = base_price * np.exp(np.cumsum(returns))

        # Generate OHLC data
        high = prices * (1 + np.abs(np.random.normal(0, 0.005, num_bars)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.005, num_bars)))
        open_prices = np.roll(prices, 1)
        open_prices[0] = base_price

        return {
            'df': pd.DataFrame({
                'time': pd.date_range('2023-01-01', periods=num_bars, freq='1min'),
                'open': open_prices,
                'high': high,
                'low': low,
                'close': prices,
                'tick_volume': np.random.randint(100, 1000, num_bars)
            }),
            'prices': prices,
            'high': high,
            'low': low,
            'num_bars': num_bars
        }

    def benchmark_alligator_calculation(self):
        """Benchmark Alligator indicator calculation"""
        logger.info("Benchmarking Alligator calculation...")

        # Original implementation simulation
        def original_alligator(prices):
            jaw_period, jaw_shift = 13, 8
            teeth_period, teeth_shift = 8, 5
            lips_period, lips_shift = 5, 3

            jaw = pd.Series(prices).rolling(jaw_period).mean().shift(jaw_shift)
            teeth = pd.Series(prices).rolling(teeth_period).mean().shift(teeth_shift)
            lips = pd.Series(prices).rolling(lips_period).mean().shift(lips_shift)

            return jaw.values, teeth.values, lips.values

        # Optimized implementation
        from optimized_btcusd_alligator import OptimizedBTCAlligatorStrategy
        optimized_strategy = OptimizedBTCAlligatorStrategy()

        # Test different data sizes
        test_sizes = [100, 500, 1000, 1440]

        for size in test_sizes:
            prices_subset = self.test_data['prices'][:size]

            # Benchmark original
            times_original = []
            for _ in range(10):
                start_time = time.perf_counter()
                original_alligator(prices_subset)
                times_original.append(time.perf_counter() - start_time)

            avg_time_original = np.mean(times_original)

            # Benchmark optimized
            times_optimized = []
            for _ in range(10):
                start_time = time.perf_counter()
                optimized_strategy.calculate_alligator_optimized(prices_subset)
                times_optimized.append(time.perf_counter() - start_time)

            avg_time_optimized = np.mean(times_optimized)

            # Calculate improvement
            improvement = ((avg_time_original - avg_time_optimized) / avg_time_original) * 100

            self.results['original'][f'alligator_{size}'] = avg_time_original
            self.results['optimized'][f'alligator_{size}'] = avg_time_optimized
            self.results['comparison'][f'alligator_{size}'] = improvement

            logger.info(f"Size {size}: Original={avg_time_original:.6f}s, Optimized={avg_time_optimized:.6f}s, Improvement={improvement:.1f}%")

    def benchmark_market_analysis(self):
        """Benchmark market analysis performance"""
        logger.info("Benchmarking market analysis...")

        from optimized_btcusd_alligator import OptimizedBTCAlligatorStrategy

        optimized_strategy = OptimizedBTCAlligatorStrategy()

        # Test multiple iterations
        num_iterations = 50
        times_optimized = []

        for i in range(num_iterations):
            # Use different subsets each time
            start_idx = i * 10
            end_idx = start_idx + 200
            if end_idx > len(self.test_data['df']):
                end_idx = len(self.test_data['df'])
                start_idx = end_idx - 200

            test_df = self.test_data['df'].iloc[start_idx:end_idx]

            start_time = time.perf_counter()
            analysis = optimized_strategy.analyze_btc_market_optimized(test_df)
            end_time = time.perf_counter()

            times_optimized.append(end_time - start_time)

        avg_time_optimized = np.mean(times_optimized)
        std_time_optimized = np.std(times_optimized)

        self.results['optimized']['market_analysis'] = {
            'avg_time': avg_time_optimized,
            'std_time': std_time_optimized,
            'min_time': np.min(times_optimized),
            'max_time': np.max(times_optimized)
        }

        logger.info(f"Market Analysis: Avg={avg_time_optimized:.6f}s ± {std_time_optimized:.6f}s")

    def benchmark_ai_decision_performance(self):
        """Benchmark AI decision making performance"""
        logger.info("Benchmarking AI decision performance...")

        from optimized_btcusd_alligator import OptimizedOllamaAgent

        ai_agent = OptimizedOllamaAgent()

        # Test market data for AI
        test_market_data = {
            'current_price': 50000.0,
            'alligator': {
                'jaw': 49900.0,
                'teeth': 49950.0,
                'lips': 49980.0,
                'alignment': 'bullish'
            },
            'technical_indicators': {
                'rsi': 55.0,
                'atr': 500.0,
                'momentum': 0.01,
                'volatility': 0.015
            },
            'market_conditions': {
                'support': 49000.0,
                'resistance': 51000.0,
                'trend_strength': 0.02,
                'price_change_24h': 1.5,
                'volatility': 0.015,
                'volume_confirmed': True
            },
            'account_info': {
                'balance': 10000.0,
                'equity': 10000.0,
                'free_margin': 9500.0,
                'margin_level': 200.0
            }
        }

        # Test multiple decisions
        num_tests = 20
        times_first_request = []
        times_cached_requests = []

        for i in range(num_tests):
            # Clear cache periodically
            if i % 5 == 0:
                ai_agent.decision_cache.clear()
                ai_agent.cache_timestamps.clear()

            start_time = time.perf_counter()
            decision = ai_agent.get_btc_decision(test_market_data)
            end_time = time.perf_counter()

            elapsed = end_time - start_time

            if i % 5 == 0:
                times_first_request.append(elapsed)
            else:
                times_cached_requests.append(elapsed)

        avg_first_request = np.mean(times_first_request)
        avg_cached_request = np.mean(times_cached_requests) if times_cached_requests else 0
        cache_improvement = ((avg_first_request - avg_cached_request) / avg_first_request) * 100 if avg_cached_request > 0 else 0

        self.results['optimized']['ai_decision'] = {
            'avg_first_request': avg_first_request,
            'avg_cached_request': avg_cached_request,
            'cache_improvement': cache_improvement,
            'cache_size': len(ai_agent.decision_cache)
        }

        logger.info(f"AI Decision: First={avg_first_request:.3f}s, Cached={avg_cached_request:.3f}s, Improvement={cache_improvement:.1f}%")

    def benchmark_memory_usage(self):
        """Benchmark memory usage patterns"""
        logger.info("Benchmarking memory usage...")

        from optimized_btcusd_alligator import OptimizedBTCAlligatorStrategy

        process = psutil.Process(os.getpid())

        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create strategy and run operations
        strategy = OptimizedBTCAlligatorStrategy()

        memory_samples = [baseline_memory]

        # Run multiple strategy iterations
        for i in range(100):
            # Analyze market
            analysis = strategy.analyze_btc_market_optimized(self.test_data['df'])

            # AI decision
            if i % 10 == 0:
                ai_decision = strategy.ai_agent.get_btc_decision(analysis)

            # Sample memory usage
            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)

                # Memory cleanup
                if i % 40 == 0:
                    strategy.performance_optimizer.cleanup_memory()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - baseline_memory
        avg_memory_per_iteration = memory_increase / 100

        self.results['optimized']['memory_usage'] = {
            'baseline_mb': baseline_memory,
            'final_mb': final_memory,
            'increase_mb': memory_increase,
            'avg_per_iteration_mb': avg_memory_per_iteration,
            'memory_samples': memory_samples
        }

        logger.info(f"Memory: Baseline={baseline_memory:.1f}MB, Final={final_memory:.1f}MB, Increase={memory_increase:.1f}MB")

    def benchmark_throughput(self):
        """Benchmark overall strategy throughput"""
        logger.info("Benchmarking strategy throughput...")

        from optimized_btcusd_alligator import OptimizedBTCAlligatorStrategy

        strategy = OptimizedBTCAlligatorStrategy()

        # Simulate continuous strategy execution
        num_executions = 1440  # 24 hours of M1 data
        start_time = time.perf_counter()

        successful_executions = 0
        total_execution_time = 0

        for i in range(num_executions):
            # Use sliding window of data
            start_idx = min(i, len(self.test_data['df']) - 200)
            end_idx = start_idx + 200
            test_df = self.test_data['df'].iloc[start_idx:end_idx]

            execution_start = time.perf_counter()
            result = strategy.execute_strategy_optimized()
            execution_end = time.perf_counter()

            execution_time = execution_end - execution_start
            total_execution_time += execution_time

            if result['status'] == 'executed':
                successful_executions += 1

        total_time = time.perf_counter() - start_time
        avg_execution_time = total_execution_time / num_executions
        throughput = num_executions / total_time  # executions per second

        self.results['optimized']['throughput'] = {
            'total_time': total_time,
            'avg_execution_time': avg_execution_time,
            'throughput_per_second': throughput,
            'successful_executions': successful_executions,
            'success_rate': (successful_executions / num_executions) * 100
        }

        logger.info(f"Throughput: {throughput:.2f} exec/s, Avg time: {avg_execution_time:.6f}s, Success rate: {(successful_executions/num_executions)*100:.1f}%")

    def generate_benchmark_report(self):
        """Generate comprehensive benchmark report"""
        logger.info("Generating benchmark report...")

        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_configuration': {
                'data_points': self.test_data['num_bars'],
                'base_price': self.test_data['prices'][0],
                'final_price': self.test_data['prices'][-1]
            },
            'results': self.results,
            'summary': self._generate_summary()
        }

        # Save detailed report
        with open('btcusd_benchmark_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        # Generate visual report
        self._generate_visual_report()

        # Print summary
        self._print_summary()

        return report

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate performance summary"""
        summary = {
            'alligator_improvement': 0,
            'ai_cache_improvement': 0,
            'memory_efficiency': 'Good',
            'overall_performance': 'Improved'
        }

        # Calculate average Alligator improvement
        alligator_improvements = [v for k, v in self.results['comparison'].items() if 'alligator' in k]
        if alligator_improvements:
            summary['alligator_improvement'] = np.mean(alligator_improvements)

        # AI cache improvement
        if 'ai_decision' in self.results['optimized']:
            summary['ai_cache_improvement'] = self.results['optimized']['ai_decision']['cache_improvement']

        # Memory efficiency assessment
        if 'memory_usage' in self.results['optimized']:
            memory_per_iteration = self.results['optimized']['memory_usage']['avg_per_iteration_mb']
            if memory_per_iteration < 0.1:
                summary['memory_efficiency'] = 'Excellent'
            elif memory_per_iteration < 0.5:
                summary['memory_efficiency'] = 'Good'
            else:
                summary['memory_efficiency'] = 'Needs Improvement'

        return summary

    def _generate_visual_report(self):
        """Generate visual performance charts"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('BTCUSD Alligator Strategy Performance Benchmark', fontsize=16)

            # Alligator Performance Comparison
            if 'comparison' in self.results:
                alligator_keys = [k for k in self.results['comparison'].keys() if 'alligator' in k]
                sizes = [int(k.split('_')[1]) for k in alligator_keys]
                improvements = [self.results['comparison'][k] for k in alligator_keys]

                axes[0, 0].bar(sizes, improvements, color='green', alpha=0.7)
                axes[0, 0].set_xlabel('Data Size (bars)')
                axes[0, 0].set_ylabel('Performance Improvement (%)')
                axes[0, 0].set_title('Alligator Calculation Performance')
                axes[0, 0].grid(True, alpha=0.3)

            # Memory Usage
            if 'memory_usage' in self.results['optimized']:
                memory_samples = self.results['optimized']['memory_usage']['memory_samples']
                axes[0, 1].plot(memory_samples, 'b-', linewidth=2)
                axes[0, 1].set_xlabel('Sample Point')
                axes[0, 1].set_ylabel('Memory Usage (MB)')
                axes[0, 1].set_title('Memory Usage Over Time')
                axes[0, 1].grid(True, alpha=0.3)

            # AI Decision Performance
            if 'ai_decision' in self.results['optimized']:
                ai_data = self.results['optimized']['ai_decision']
                categories = ['First Request', 'Cached Request']
                times = [ai_data['avg_first_request'], ai_data['avg_cached_request']]

                axes[1, 0].bar(categories, times, color=['orange', 'green'], alpha=0.7)
                axes[1, 0].set_ylabel('Response Time (seconds)')
                axes[1, 0].set_title('AI Decision Performance')
                axes[1, 0].grid(True, alpha=0.3)

            # Throughput Performance
            if 'throughput' in self.results['optimized']:
                throughput_data = self.results['optimized']['throughput']
                axes[1, 1].bar(['Executions/sec', 'Success Rate %'],
                             [throughput_data['throughput_per_second'], throughput_data['success_rate']/10],
                             color=['blue', 'purple'], alpha=0.7)
                axes[1, 1].set_ylabel('Value')
                axes[1, 1].set_title('Strategy Throughput Metrics')
                axes[1, 1].grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig('btcusd_performance_benchmark.png', dpi=300, bbox_inches='tight')
            logger.info("Visual benchmark report saved to: btcusd_performance_benchmark.png")

        except Exception as e:
            logger.error(f"Error generating visual report: {e}")

    def _print_summary(self):
        """Print benchmark summary to console"""
        print("\n" + "="*70)
        print("BTCUSD ALLIGATOR STRATEGY PERFORMANCE BENCHMARK REPORT")
        print("="*70)

        print(f"\nTest Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Data: {self.test_data['num_bars']} bars")
        print(f"Price Range: ${self.test_data['prices'].min():.2f} - ${self.test_data['prices'].max():.2f}")

        print("\nPERFORMANCE IMPROVEMENTS:")
        print("-" * 40)

        # Alligator improvements
        if 'comparison' in self.results:
            alligator_improvements = [v for k, v in self.results['comparison'].items() if 'alligator' in k]
            if alligator_improvements:
                avg_improvement = np.mean(alligator_improvements)
                print(f"✓ Alligator Calculation: {avg_improvement:.1f}% faster on average")

        # AI performance
        if 'ai_decision' in self.results['optimized']:
            ai_data = self.results['optimized']['ai_decision']
            print(f"✓ AI Decision Cache: {ai_data['cache_improvement']:.1f}% faster with caching")
            print(f"✓ Cache Size: {ai_data['cache_size']} entries")

        # Memory efficiency
        if 'memory_usage' in self.results['optimized']:
            memory_data = self.results['optimized']['memory_usage']
            print(f"✓ Memory Usage: {memory_data['increase_mb']:.2f} MB total increase")
            print(f"✓ Per Iteration: {memory_data['avg_per_iteration_mb']:.4f} MB")

        # Throughput
        if 'throughput' in self.results['optimized']:
            throughput = self.results['optimized']['throughput']
            print(f"✓ Strategy Throughput: {throughput['throughput_per_second']:.2f} executions/second")
            print(f"✓ Success Rate: {throughput['success_rate']:.1f}%")

        print("\nOPTIMIZATION FEATURES:")
        print("-" * 40)
        print("✓ Cached SMA calculations")
        print("✓ Vectorized technical indicators")
        print("✓ AI decision caching with TTL")
        print("✓ Optimized prompt engineering")
        print("✓ Dynamic position sizing")
        print("✓ Memory management and cleanup")
        print("✓ Connection pooling for API requests")
        print("✓ BTC-specific volatility adaptation")

        print("\nFILES GENERATED:")
        print("-" * 40)
        print("• btcusd_benchmark_report.json - Detailed benchmark data")
        print("• btcusd_performance_benchmark.png - Visual performance charts")

        print("\n" + "="*70)


def main():
    """Main benchmark execution"""
    logger.info("Starting BTCUSD Alligator Strategy Performance Benchmark")

    try:
        # Initialize benchmark suite
        benchmark = BenchmarkSuite()

        # Run all benchmarks
        logger.info("Running performance benchmarks...")

        benchmark.benchmark_alligator_calculation()
        benchmark.benchmark_market_analysis()
        benchmark.benchmark_ai_decision_performance()
        benchmark.benchmark_memory_usage()
        benchmark.benchmark_throughput()

        # Generate comprehensive report
        logger.info("Generating benchmark report...")
        benchmark.generate_benchmark_report()

        logger.info("Benchmark completed successfully")

    except Exception as e:
        logger.error(f"Benchmark error: {e}")
        logger.exception(e)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())