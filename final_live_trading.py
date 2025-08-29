#!/usr/bin/env python3
"""
Final live trading script using Nautilus Trader with MT5 integration
"""

import logging
import sys
from decimal import Decimal

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
from simplified_factories import MT5DataClientFactory
from simplified_factories import MT5ExecClientFactory

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
    
    # Register client factories
    node.add_data_client_factory("MT5", MT5DataClientFactory(None))
    node.add_exec_client_factory("MT5", MT5ExecClientFactory(None))

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