#!/usr/bin/env python3
"""
AI Alligator Strategy with Integrated Performance Optimizer
Combines the optimized trading strategy with automatic LLM-based performance optimization
"""

import sys
import time
import json
import logging
from datetime import datetime
from ai_alligator_btcusd_optimized import OptimizedAlligatorStrategy, BTCUSDConfig, initialize_mt5
from ai_performance_optimizer import LLMPerformanceOptimizer, integrate_with_strategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('ai_alligator_with_optimizer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EnhancedAlligatorStrategy(OptimizedAlligatorStrategy):
    """Enhanced strategy with integrated performance optimizer"""

    def __init__(self, config: BTCUSDConfig):
        super().__init__(config)

        # Initialize performance optimizer
        self.optimizer = LLMPerformanceOptimizer(
            model=config.model,
            host=config.host,
            port=config.port
        )

        # Optimization settings
        self.enable_auto_optimization = True
        self.last_performance_check = time.time()
        self.performance_check_interval = 300  # 5 minutes

        # Enhanced logging
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.session_start = datetime.now()

        logger.info("Enhanced Alligator Strategy with Performance Optimizer initialized")

    def open_position_optimized(self, signal: str, volatility: float):
        """Enhanced position opening with performance tracking"""

        # Use optimizer parameters if available
        if self.optimizer.metrics.total_trades > 0:
            # Update strategy with optimizer parameters
            self.config.sl_points = self.optimizer.parameters.sl_points
            self.config.tp_points = self.optimizer.parameters.tp_points
            self.config.max_risk_percent = self.optimizer.parameters.max_risk_percent
            self.config.max_lot_size = self.optimizer.parameters.max_lot_size
            self.config.min_volatility_threshold = self.optimizer.parameters.min_volatility_threshold
            self.config.max_spread_percentage = self.optimizer.parameters.max_spread_percentage

        # Execute original position opening
        result = super().open_position_optimized(signal, volatility)

        return result

    def close_position(self, position):
        """Enhanced position closing with performance tracking"""

        # Get position details before closing
        position_info = {
            'ticket': position.ticket,
            'type': 'SELL' if position.type == 1 else 'BUY',  # SELL=1, BUY=0
            'volume': position.volume,
            'open_price': position.price_open,
            'close_price': position.price_current,
            'open_time': datetime.fromtimestamp(position.time_open),
            'close_time': datetime.now(),
            'sl': position.sl,
            'tp': position.tp,
            'profit': position.profit,
            'commission': position.swap,
            'swap': position.swap
        }

        # Execute original close
        result = super().close_position(position)

        # Record trade with optimizer if successful
        if result:
            self.optimizer.record_trade(position_info)

            # Update P&L tracking
            self.total_pnl += position_info['profit']
            self.daily_pnl += position_info['profit']

            logger.info(f"Trade recorded: {position_info['profit']:.2f} profit (Total: {self.total_pnl:.2f})")

        return result

    def execute_strategy_optimized(self):
        """Enhanced strategy execution with performance optimization"""

        # Execute original strategy
        super().execute_strategy_optimized()

        # Check for performance optimization
        self._check_performance_optimization()

    def _check_performance_optimization(self):
        """Check and run performance optimization"""
        current_time = time.time()

        if (self.enable_auto_optimization and
            current_time - self.last_performance_check > self.performance_check_interval):

            self.last_performance_check = current_time

            # Run optimization
            result = self.optimizer.optimize()

            if result:
                logger.info(f"🚀 Performance Optimization Applied!")
                logger.info(f"Expected improvement: {result.expected_improvement:.1%}")
                logger.info(f"Confidence: {result.confidence:.1%}")

                # Log key parameter changes
                old_params = result.old_parameters
                new_params = result.new_parameters

                changes = []
                if old_params.sl_points != new_params.sl_points:
                    changes.append(f"SL: {old_params.sl_points} → {new_params.sl_points}")
                if old_params.tp_points != new_params.tp_points:
                    changes.append(f"TP: {old_params.tp_points} → {new_params.tp_points}")
                if old_params.max_risk_percent != new_params.max_risk_percent:
                    changes.append(f"Risk: {old_params.max_risk_percent}% → {new_params.max_risk_percent}%")
                if old_params.position_sizing_method != new_params.position_sizing_method:
                    changes.append(f"Sizing: {old_params.position_sizing_method} → {new_params.position_sizing_method}")

                if changes:
                    logger.info(f"Key changes: {', '.join(changes)}")

    def get_enhanced_performance_summary(self) -> dict:
        """Get comprehensive performance summary"""
        base_summary = self.performance.get_performance_summary()
        optimizer_summary = self.optimizer.get_optimization_report()

        return {
            'strategy_performance': base_summary,
            'optimizer_metrics': optimizer_summary['current_metrics'],
            'optimizer_parameters': optimizer_summary['current_parameters'],
            'pnl_tracking': {
                'total_pnl': self.total_pnl,
                'daily_pnl': self.daily_pnl,
                'session_duration': str(datetime.now() - self.session_start),
                'session_start': self.session_start.isoformat()
            },
            'optimization_history': optimizer_summary['optimization_history']
        }

    def log_enhanced_performance_summary(self):
        """Log enhanced performance summary"""
        summary = self.get_enhanced_performance_summary()

        logger.info(f"""
🎯 ENHANCED PERFORMANCE SUMMARY:
====================================
Strategy Performance:
- Executions: {summary['strategy_performance']['total_executions']}
- Cache Hit Rate: {summary['strategy_performance']['cache_hit_rate_percent']:.1f}%
- Avg AI Response: {summary['strategy_performance']['avg_ai_response_time']:.2f}s
- Error Rate: {summary['strategy_performance']['error_rate']:.1f}%

Trading Performance:
- Total Trades: {summary['optimizer_metrics']['total_trades']}
- Win Rate: {summary['optimizer_metrics']['win_rate']:.1%}
- Profit Factor: {summary['optimizer_metrics']['profit_factor']:.2f}
- Total P&L: ${summary['optimizer_metrics']['total_profit'] + summary['optimizer_metrics']['total_loss']:.2f}
- Max Drawdown: {summary['optimizer_metrics']['max_drawdown']:.1%}
- Sharpe Ratio: {summary['optimizer_metrics']['sharpe_ratio']:.2f}

Current Parameters:
- SL/TP: {summary['optimizer_parameters']['sl_points']}/{summary['optimizer_parameters']['tp_points']} points
- Risk: {summary['optimizer_parameters']['max_risk_percent']}%
- Position Sizing: {summary['optimizer_parameters']['position_sizing_method']}
- Min Volatility: {summary['optimizer_parameters']['min_volatility_threshold']:.3f}

Session Tracking:
- Total P&L: ${summary['pnl_tracking']['total_pnl']:.2f}
- Daily P&L: ${summary['pnl_tracking']['daily_pnl']:.2f}
- Session Duration: {summary['pnl_tracking']['session_duration']}
====================================
        """)

    def export_session_data(self):
        """Export complete session data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export trade history
        trade_file = f"trades_{timestamp}.csv"
        self.optimizer.export_trade_history(trade_file)

        # Export performance summary
        summary_file = f"performance_summary_{timestamp}.json"
        summary = self.get_enhanced_performance_summary()

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Session data exported:")
        logger.info(f"  Trades: {trade_file}")
        logger.info(f"  Performance: {summary_file}")

        return trade_file, summary_file


def main():
    """Main function with enhanced strategy and optimizer"""
    logger.info("🚀 Starting Enhanced AI Alligator Strategy with Performance Optimizer")

    # Load configuration
    config = BTCUSDConfig()
    logger.info(f"Configuration: {config.model}, SL/TP: {config.sl_points}/{config.tp_points}, Risk: {config.max_risk_percent}%")

    # Initialize MT5
    if not initialize_mt5():
        logger.error("Failed to initialize MT5")
        return

    # Test Ollama connection
    try:
        import requests
        test_payload = {
            "model": config.model,
            "prompt": "Respond with 'OK' if you can read this.",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
        response = requests.post(f"http://{config.host}:{config.port}/api/generate",
                                json=test_payload, timeout=30)
        if response.status_code == 200:
            logger.info("✅ Ollama connection successful")
        else:
            logger.error(f"❌ Ollama connection failed: {response.status_code}")
            import MetaTrader5 as mt5
            mt5.shutdown()
            return
    except Exception as e:
        logger.error(f"❌ Failed to connect to Ollama: {e}")
        import MetaTrader5 as mt5
        mt5.shutdown()
        return

    # Get account info
    import MetaTrader5 as mt5
    account_info = mt5.account_info()
    if account_info is None:
        mt5.shutdown()
        return

    logger.info(f"💰 Connected to MT5 account {account_info.login}")
    logger.info(f"   Balance: {account_info.balance:.2f} {account_info.currency}")
    logger.info(f"   Equity: {account_info.equity:.2f} {account_info.currency}")

    # Create enhanced strategy instance
    strategy = EnhancedAlligatorStrategy(config)

    try:
        # Run the enhanced strategy loop
        iteration = 0
        next_performance_log = time.time() + 300  # Log performance every 5 minutes
        next_export = time.time() + 3600  # Export data every hour

        logger.info("🔄 Starting trading loop...")

        while True:
            iteration += 1
            logger.info(f"📊 Strategy iteration {iteration}")

            # Execute enhanced strategy
            strategy.execute_strategy_optimized()

            # Log performance summary periodically
            if time.time() >= next_performance_log:
                strategy.log_enhanced_performance_summary()
                next_performance_log = time.time() + 300  # Next log in 5 minutes

            # Export data periodically
            if time.time() >= next_export:
                strategy.export_session_data()
                next_export = time.time() + 3600  # Next export in 1 hour

            # Extended account info logging every 50 iterations
            if iteration % 50 == 0:
                account_info = mt5.account_info()
                if account_info:
                    logger.info(f"📈 Account Status - Balance: {account_info.balance:.2f}, "
                               f"Equity: {account_info.equity:.2f}, Free Margin: {account_info.margin_free:.2f}")

            # Sleep for next iteration (60 seconds for M1 timeframe)
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("⏹️ Stopping enhanced strategy...")
    except Exception as e:
        logger.error(f"💥 Critical error in strategy execution: {e}")
    finally:
        # Final export and cleanup
        try:
            logger.info("📦 Exporting final session data...")
            strategy.export_session_data()
            strategy.log_enhanced_performance_summary()

            # Export optimizer data
            optimizer_report = strategy.optimizer.get_optimization_report()
            with open(f"optimizer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                json.dump(optimizer_report, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error during final export: {e}")

        # Shutdown MT5
        mt5.shutdown()
        logger.info("🏁 Enhanced AI Alligator Strategy with Performance Optimizer stopped")


if __name__ == "__main__":
    main()