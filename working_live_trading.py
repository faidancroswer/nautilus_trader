#!/usr/bin/env python3
"""
Working live trading script using Nautilus Trader with MT5 integration
"""

import asyncio
import logging
import sys
from decimal import Decimal

from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId

# Import our custom modules
from nautilus_alligator_strategy import AlligatorConfig
from nautilus_alligator_strategy import AlligatorStrategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to run live trading
    """
    logger.info("Starting MT5 live trading with Alligator strategy using Nautilus Trader")
    
    # Configure the trading node
    config_node = TradingNodeConfig(
        trader_id="MT5_LIVE_TRADER-001",
        logging=LoggingConfig(log_level="INFO"),
    )

    # Instantiate the node with a configuration
    node = TradingNode(config=config_node)
    
    # Configure your strategy
    strategy_config = AlligatorConfig(
        instrument_id=InstrumentId.from_str("EUR/USD.IDEALPRO"),  # Using a standard instrument
        bar_type=BarType.from_str("EUR/USD.IDEALPRO-1-MINUTE-BID-EXTERNAL"),  # Standard bar type
        trade_size=Decimal("100000"),  # 100,000 units
        jaw_period=13,
        jaw_shift=8,
        teeth_period=8,
        teeth_shift=5,
        lips_period=5,
        lips_shift=3,
    )

    # Instantiate your strategy
    strategy = AlligatorStrategy(config=strategy_config)

    # Add your strategies and modules
    node.trader.add_strategy(strategy)

    try:
        # Start the node
        node.start()
        
        # Keep the node running
        logger.info("Live trading started. Press Ctrl+C to stop.")
        node.wait()
        
    except KeyboardInterrupt:
        logger.info("Stopping live trading...")
        node.stop()
        node.dispose()
    except Exception as e:
        logger.error(f"Error in live trading: {e}")
        node.stop()
        node.dispose()


if __name__ == "__main__":
    main()