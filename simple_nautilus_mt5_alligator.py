#!/usr/bin/env python3
"""
Simple script to run the Alligator strategy with Nautilus Trader and MT5 integration.
"""

import asyncio
import logging
import os
import sys
from decimal import Decimal

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Try to import Nautilus Trader
    from nautilus_trader.config import LoggingConfig
    from nautilus_trader.config import TradingNodeConfig
    from nautilus_trader.live.node import TradingNode
    from nautilus_trader.model.data import BarType
    from nautilus_trader.model.identifiers import InstrumentId
    from nautilus_trader.model.identifiers import Venue
    
    # Import our custom strategy
    from nautilus_alligator_strategy import AlligatorConfig
    from nautilus_alligator_strategy import AlligatorStrategy
    
    # Import our MT5 adapter
    from mt5_nautilus_adapter import MT5ExecutionClient
    from mt5_nautilus_adapter import MT5DataClient
    from nautilus_trader.adapters.base import BaseDataClientFactory, BaseExecClientFactory
    from nautilus_trader.cache.cache import Cache
    from nautilus_trader.common.component import MessageBus
    from nautilus_trader.common.component import LiveClock
    from nautilus_trader.common.component import Logger
    from nautilus_trader.model.identifiers import ClientId
    
    logger.info("All modules imported successfully")
    
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.error("Please make sure Nautilus Trader is properly installed")
    sys.exit(1)

class MT5DataClientFactory(BaseDataClientFactory):
    """
    Factory for creating MT5 data clients.
    """
    def __init__(self, config):
        self.config = config

    def create(
        self,
        loop: asyncio.AbstractEventLoop,
        name: str,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        log: Logger,
        instrument_provider,
    ):
        client = MT5DataClient(
            loop=loop,
            client_id=ClientId(name),
            venue=Venue(name),
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            log=log,
            config=self.config,
        )
        return client


class MT5ExecClientFactory(BaseExecClientFactory):
    """
    Factory for creating MT5 execution clients.
    """
    def __init__(self, config):
        self.config = config

    def create(
        self,
        loop: asyncio.AbstractEventLoop,
        name: str,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        log: Logger,
        instrument_provider,
    ):
        client = MT5ExecutionClient(
            loop=loop,
            client_id=ClientId(name),
            venue=Venue(name),
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            log=log,
            config=self.config,
        )
        return client


def main():
    logger.info("Starting Alligator strategy with Nautilus Trader and MT5 integration")
    
    # Configure the trading node
    config_node = TradingNodeConfig(
        trader_id="MT5_TRADER-001",
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
        node.start()
        # Keep the node running
        node.wait()
    except KeyboardInterrupt:
        print("Stopping node...")
        node.stop()
        node.dispose()


if __name__ == "__main__":
    main()