#!/usr/bin/env python3
"""
Final AI Trading System - Performance Optimized
Runs the enhanced strategy with optimizer without unicode issues
"""

import sys
import time
import json
import logging
from datetime import datetime

# Configure logging without unicode issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_trading_final.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Run the enhanced trading system"""
    logger.info("Starting Enhanced AI Trading System with Performance Optimizer")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Startup time: {datetime.now().isoformat()}")

    try:
        # Import and run the enhanced strategy directly
        from ai_alligator_with_optimizer import EnhancedAlligatorStrategy, BTCUSDConfig, initialize_mt5
        import MetaTrader5 as mt5
        import requests

        # Initialize MT5
        if not initialize_mt5():
            logger.error("Failed to initialize MT5")
            return

        # Test Ollama connection
        try:
            test_payload = {
                "model": "llama3.2:3b",
                "prompt": "Respond with 'OK' if you can read this.",
                "stream": False,
                "options": {"temperature": 0.1, "top_p": 0.9}
            }
            response = requests.post("http://localhost:11434/api/generate",
                                    json=test_payload, timeout=30)
            if response.status_code == 200:
                logger.info("Ollama connection successful")
            else:
                logger.error(f"Ollama connection failed: {response.status_code}")
                mt5.shutdown()
                return
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            mt5.shutdown()
            return

        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            mt5.shutdown()
            return

        logger.info(f"Connected to MT5 account {account_info.login}")
        logger.info(f"Balance: {account_info.balance} {account_info.currency}")
        logger.info(f"Equity: {account_info.equity} {account_info.currency}")

        # Create enhanced strategy instance
        config = BTCUSDConfig()
        strategy = EnhancedAlligatorStrategy(config)

        try:
            # Run the enhanced strategy loop
            iteration = 0
            next_performance_log = time.time() + 300  # Log performance every 5 minutes
            next_export = time.time() + 3600  # Export data every hour

            logger.info("Starting trading loop...")

            while True:
                iteration += 1
                logger.info(f"Strategy iteration {iteration}")

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
                        logger.info(f"Account Status - Balance: {account_info.balance}, "
                                   f"Equity: {account_info.equity}, Free Margin: {account_info.margin_free}")

                # Sleep for next iteration (60 seconds for M1 timeframe)
                time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Stopping enhanced strategy...")
        except Exception as e:
            logger.error(f"Critical error in strategy execution: {e}")
        finally:
            # Final export and cleanup
            try:
                logger.info("Exporting final session data...")
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
            logger.info("Enhanced AI Alligator Strategy with Performance Optimizer stopped")

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure all required modules are available")
        return

    except Exception as e:
        logger.error(f"System error: {e}")
        return

    logger.info("Trading system completed successfully")


if __name__ == "__main__":
    main()