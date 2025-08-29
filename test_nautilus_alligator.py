#!/usr/bin/env python3
"""
Simple script to run a basic strategy with Nautilus Trader.
"""

import asyncio
import logging
import os
import sys
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Import Nautilus Trader modules
    from nautilus_trader.config import LoggingConfig
    from nautilus_trader.config import TradingNodeConfig
    from nautilus_trader.live.node import TradingNode
    from nautilus_trader.model.data import BarType
    from nautilus_trader.model.identifiers import InstrumentId
    
    # Import our custom strategy
    from nautilus_alligator_strategy import AlligatorConfig
    from nautilus_alligator_strategy import AlligatorStrategy
    
    logger.info("All modules imported successfully")
    
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.error("Please make sure Nautilus Trader is properly installed")
    sys.exit(1)


def main():
    logger.info("Starting Alligator strategy with Nautilus Trader")
    
    # For now, we'll just test if we can instantiate our strategy
    # without the complex MT5 integration
    
    # Configure your strategy
    strategy_config = AlligatorConfig(
        instrument_id=InstrumentId.from_str("EUR/USD.IDEALPRO"),  # Example instrument
        bar_type=BarType.from_str("EUR/USD.IDEALPRO-1-MINUTE-BID-EXTERNAL"),  # Example bar type
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
    
    logger.info("Alligator strategy instantiated successfully")
    logger.info(f"Strategy config: {strategy_config}")
    
    # In a real implementation, we would:
    # 1. Configure a TradingNode with proper data and execution clients
    # 2. Add the strategy to the node
    # 3. Start the node
    # 
    # But for now, we're just testing that our strategy can be imported and instantiated
    
    logger.info("Script completed successfully")


if __name__ == "__main__":
    main()