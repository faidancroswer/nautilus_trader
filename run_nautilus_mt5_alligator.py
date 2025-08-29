#!/usr/bin/env python3
# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2025 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

import asyncio
from decimal import Decimal

from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue

# Import our custom Alligator strategy
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
from nautilus_trader.common.enums import LogColor
from nautilus_trader.model.identifiers import ClientId


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

# Start the node
def main():
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