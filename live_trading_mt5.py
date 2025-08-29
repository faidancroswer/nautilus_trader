#!/usr/bin/env python3
"""
Live trading script using Nautilus Trader with MT5 integration
"""

import asyncio
import logging
import sys
from decimal import Decimal
from datetime import datetime

import MetaTrader5 as mt5

from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType

# Import our custom modules
from nautilus_alligator_strategy import AlligatorConfig
from nautilus_alligator_strategy import AlligatorStrategy
from mt5_live_adapter import MT5ExecutionClient
from mt5_live_adapter import MT5DataClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_mt5():
    """
    Initialize MT5 connection
    """
    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    logger.info("MT5 initialized successfully")
    return True


def get_account_info():
    """
    Get MT5 account information
    """
    account_info = mt5.account_info()
    if account_info is None:
        logger.error(f"Failed to get account info: {mt5.last_error()}")
        return None
    return account_info


async def run_live_trading():
    """
    Run live trading with Nautilus Trader and MT5
    """
    logger.info("Starting live trading with Nautilus Trader and MT5")
    
    # Initialize MT5
    if not initialize_mt5():
        return
    
    # Get account info
    account_info = get_account_info()
    if account_info is None:
        mt5.shutdown()
        return
    
    logger.info(f"Connected to MT5 account {account_info.login}")
    logger.info(f"Balance: {account_info.balance} {account_info.currency}")
    
    # Configure the trading node
    config_node = TradingNodeConfig(
        trader_id="MT5_LIVE_TRADER-001",
        logging=LoggingConfig(log_level="INFO"),
        data_clients={
            "MT5": None,  # Configuration for MT5 data client
        },
        exec_clients={
            "MT5": None,  # Configuration for MT5 execution client
        },
        timeout_connection=30.0,
        timeout_reconciliation=10.0,
        timeout_portfolio=10.0,
        timeout_disconnection=10.0,
        timeout_post_stop=30.0,
    )

    # Instantiate the node with a configuration
    node = TradingNode(config=config_node)
    
    # Configure your strategy
    strategy_config = AlligatorConfig(
        instrument_id=InstrumentId.from_str("EUR/USD.MT5"),  # Instrument for MT5
        bar_type=BarType.from_str("EUR/USD.MT5-1-MINUTE-BID-EXTERNAL"),  # Bar type for MT5
        trade_size=Decimal("0.1"),  # 0.1 lot (adjust as needed)
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
    
    # TODO: Register client factories
    # This would require implementing proper factory classes
    
    try:
        # Start the node
        node.start()
        
        # Keep the node running
        logger.info("Live trading started. Press Ctrl+C to stop.")
        await asyncio.sleep(3600)  # Run for 1 hour, adjust as needed
        
    except KeyboardInterrupt:
        logger.info("Stopping live trading...")
        node.stop()
        node.dispose()
    finally:
        # Shutdown MT5
        mt5.shutdown()


def main():
    """
    Main function
    """
    logger.info("Starting MT5 live trading with Alligator strategy")
    
    try:
        # Run the live trading
        asyncio.run(run_live_trading())
    except Exception as e:
        logger.error(f"Error in live trading: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()