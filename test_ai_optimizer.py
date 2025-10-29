#!/usr/bin/env python3
"""
Test script for AI Performance Optimizer
Validates the optimization agent with sample data
"""

import sys
import time
import json
import logging
from datetime import datetime, timedelta
from ai_performance_optimizer import LLMPerformanceOptimizer, StrategyParameters, PerformanceMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_trades(num_trades: int = 15) -> list:
    """Create sample trade data for testing"""
    trades = []
    base_price = 45000
    current_time = datetime.now()

    for i in range(num_trades):
        # Simulate realistic trade outcomes
        trade_type = 'BUY' if i % 2 == 0 else 'SELL'

        # Generate realistic profit/loss
        import random
        if random.random() < 0.6:  # 60% win rate
            profit = random.uniform(20, 100)  # $20-$100 profit
        else:
            profit = -random.uniform(10, 60)  # $10-$60 loss

        trade = {
            'ticket': 100000 + i,
            'type': trade_type,
            'volume': 0.01,
            'open_price': base_price + random.uniform(-100, 100),
            'close_price': base_price + random.uniform(-150, 150),
            'open_time': current_time - timedelta(minutes=num_trades-i),
            'close_time': current_time - timedelta(minutes=num_trades-i-1),
            'sl': base_price - random.uniform(200, 400),
            'tp': base_price + random.uniform(200, 400),
            'profit': profit,
            'commission': 0.5,
            'swap': 0.0
        }
        trades.append(trade)
        base_price += random.uniform(-50, 50)  # Price movement

    return trades


def test_optimizer_basic_functionality():
    """Test basic optimizer functionality"""
    logger.info("Testing basic optimizer functionality...")

    try:
        # Initialize optimizer
        optimizer = LLMPerformanceOptimizer()
        logger.info("✅ Optimizer initialized successfully")

        # Test metrics calculation
        trades = create_sample_trades(10)
        for trade in trades:
            optimizer.record_trade(trade)

        metrics = optimizer.metrics
        logger.info(f"📊 Metrics calculated:")
        logger.info(f"   Total trades: {metrics.total_trades}")
        logger.info(f"   Win rate: {metrics.win_rate:.1%}")
        logger.info(f"   Profit factor: {metrics.profit_factor:.2f}")
        logger.info(f"   Total P&L: {metrics.total_profit + metrics.total_loss:.2f}")

        # Test parameter validation
        test_params = {
            'sl_points': 300,
            'tp_points': 1500,
            'max_risk_percent': 2.5,
            'max_lot_size': 0.02,
            'min_volatility_threshold': 0.003
        }

        validated = optimizer._validate_parameters(test_params)
        logger.info(f"✅ Parameter validation successful")
        logger.info(f"   Validated SL: {validated['sl_points']}")
        logger.info(f"   Validated Risk: {validated['max_risk_percent']}%")

        return True

    except Exception as e:
        logger.error(f"❌ Error in basic functionality test: {e}")
        return False


def test_llm_optimization():
    """Test LLM-based optimization"""
    logger.info("Testing LLM-based optimization...")

    try:
        # Initialize optimizer
        optimizer = LLMPerformanceOptimizer()

        # Add sample trades
        trades = create_sample_trades(12)
        for trade in trades:
            optimizer.record_trade(trade)

        logger.info(f"Added {len(trades)} sample trades")
        logger.info(f"Current metrics: Win rate {optimizer.metrics.win_rate:.1%}, "
                   f"Profit factor {optimizer.metrics.profit_factor:.2f}")

        # Test prompt generation
        prompt = optimizer._generate_optimization_prompt()
        logger.info(f"✅ Prompt generated successfully ({len(prompt)} chars)")

        # Run optimization (this will call LLM)
        logger.info("🤖 Running LLM optimization...")
        result = optimizer.optimize()

        if result:
            logger.info("✅ LLM optimization successful!")
            logger.info(f"   Expected improvement: {result.expected_improvement:.1%}")
            logger.info(f"   Confidence: {result.confidence:.1%}")
            logger.info(f"   Reasoning: {result.reasoning[:200]}...")

            # Show parameter changes
            old = result.old_parameters
            new = result.new_parameters

            changes = []
            if old.sl_points != new.sl_points:
                changes.append(f"SL: {old.sl_points} → {new.sl_points}")
            if old.tp_points != new.tp_points:
                changes.append(f"TP: {old.tp_points} → {new.tp_points}")
            if old.max_risk_percent != new.max_risk_percent:
                changes.append(f"Risk: {old.max_risk_percent}% → {new.max_risk_percent}%")

            if changes:
                logger.info(f"   Changes: {', '.join(changes)}")

            return True
        else:
            logger.error("❌ LLM optimization failed")
            return False

    except Exception as e:
        logger.error(f"❌ Error in LLM optimization test: {e}")
        return False


def test_performance_monitoring():
    """Test performance monitoring and reporting"""
    logger.info("Testing performance monitoring...")

    try:
        optimizer = LLMPerformanceOptimizer()

        # Add progressive trades to simulate real trading
        for batch in range(3):
            trades = create_sample_trades(5)
            for trade in trades:
                optimizer.record_trade(trade)

            logger.info(f"Batch {batch + 1} completed - "
                       f"Win rate: {optimizer.metrics.win_rate:.1%}, "
                       f"P&L: {optimizer.metrics.total_profit + optimizer.metrics.total_loss:.2f}")

            time.sleep(1)  # Small delay

        # Generate performance report
        report = optimizer.get_optimization_report()
        logger.info("✅ Performance report generated")

        # Export trade history
        filename = optimizer.export_trade_history()
        logger.info(f"✅ Trade history exported to {filename}")

        return True

    except Exception as e:
        logger.error(f"❌ Error in performance monitoring test: {e}")
        return False


def test_parameter_scenarios():
    """Test different parameter scenarios"""
    logger.info("Testing parameter optimization scenarios...")

    try:
        optimizer = LLMPerformanceOptimizer()

        # Scenario 1: Low win rate, needs adjustment
        optimizer.parameters.sl_points = 200  # Too tight
        optimizer.parameters.tp_points = 400  # Too small

        trades = create_sample_trades(8)
        for trade in trades:
            # Simulate poor performance
            if trade['profit'] > 0:
                trade['profit'] *= 0.5  # Reduce profits
            else:
                trade['profit'] *= 1.5  # Increase losses
        optimizer.record_trade(trade)

        logger.info(f"Scenario 1 - Low win rate: {optimizer.metrics.win_rate:.1%}")

        # Scenario 2: High drawdown, needs risk adjustment
        optimizer.parameters.max_risk_percent = 3.0  # Too high risk

        trades = create_sample_trades(5)
        for trade in trades:
            # Simulate high drawdown
            if trade['profit'] < 0:
                trade['profit'] *= 2.0  # Big losses
        optimizer.record_trade(trade)

        logger.info(f"Scenario 2 - High drawdown: {optimizer.metrics.max_drawdown:.1%}")

        return True

    except Exception as e:
        logger.error(f"❌ Error in parameter scenarios test: {e}")
        return False


def run_comprehensive_test():
    """Run comprehensive test suite"""
    logger.info("🧪 Starting AI Performance Optimizer Test Suite")
    logger.info("=" * 60)

    tests = [
        ("Basic Functionality", test_optimizer_basic_functionality),
        ("LLM Optimization", test_llm_optimization),
        ("Performance Monitoring", test_performance_monitoring),
        ("Parameter Scenarios", test_parameter_scenarios)
    ]

    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'summary': {}
    }

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n🔄 Running: {test_name}")
        logger.info("-" * 40)

        start_time = time.time()
        success = test_func()
        end_time = time.time()

        results['tests'][test_name] = {
            'success': success,
            'duration': end_time - start_time,
            'timestamp': datetime.now().isoformat()
        }

        if success:
            passed += 1
            logger.info(f"✅ {test_name}: PASSED ({end_time - start_time:.2f}s)")
        else:
            logger.error(f"❌ {test_name}: FAILED ({end_time - start_time:.2f}s)")

    # Summary
    results['summary'] = {
        'total_tests': total,
        'passed_tests': passed,
        'failed_tests': total - passed,
        'success_rate': passed / total * 100,
        'total_duration': sum(test['duration'] for test in results['tests'].values())
    }

    # Save results
    with open('optimizer_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info("\n" + "=" * 60)
    logger.info("🏁 TEST SUITE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Tests passed: {passed}/{total}")
    logger.info(f"Success rate: {passed/total*100:.1f}%")
    logger.info(f"Total duration: {results['summary']['total_duration']:.2f}s")
    logger.info(f"Results saved to: optimizer_test_results.json")

    return passed == total


if __name__ == "__main__":
    logger.info("AI Performance Optimizer Test Suite")
    logger.info(f"Python version: {sys.version}")

    success = run_comprehensive_test()

    if success:
        logger.info("\n🎉 All tests passed! The AI optimizer is working correctly.")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed. Please check the optimizer implementation.")
        sys.exit(1)