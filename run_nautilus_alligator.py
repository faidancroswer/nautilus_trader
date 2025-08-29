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

import os
from decimal import Decimal

from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.examples.strategies.ema_cross import EMACrossConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Currency
from nautilus_trader.persistence.catalog import ParquetDataCatalog

# Import our custom Alligator strategy
from nautilus_alligator_strategy import AlligatorConfig
from nautilus_alligator_strategy import AlligatorStrategy


# *** THIS INTEGRATION IS DESIGNED TO BE USED WITH THE NAUTILUS TRADER LIVE NODE ***
# *** IT IS A BASIC EXAMPLE AND NEEDS TO BE PROPERLY CONFIGURED FOR YOUR SPECIFIC BROKER ***

# *** THIS IS A TEMPLATE AND NEEDS TO BE CONFIGURED WITH YOUR BROKER CREDENTIALS ***

# Configure the trading node
config_node = TradingNodeConfig(
    trader_id="TESTER-001",
    logging=LoggingConfig(log_level="INFO"),
    data_clients={
        # Add your data client configuration here
        # Example for Binance:
        # "BINANCE": BinanceDataClientConfig(
        #     api_key=os.getenv("BINANCE_API_KEY"),
        #     api_secret=os.getenv("BINANCE_API_SECRET"),
        #     use_gtd=False,
        # ),
    },
    exec_clients={
        # Add your execution client configuration here
        # Example for Binance:
        # "BINANCE": BinanceExecClientConfig(
        #     api_key=os.getenv("BINANCE_API_KEY"),
        #     api_secret=os.getenv("BINANCE_API_SECRET"),
        #     use_gtd=False,
        #     use_reduce_only=False,
        #     use_position_ids=False,
        # ),
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

# Add your strategies and modules
node.trader.add_strategy(strategy)

# Register your client factories with the node (if any)
# node.add_data_client_factory("IB", InteractiveBrokersLiveDataClientFactory)
# node.add_exec_client_factory("IB", InteractiveBrokersLiveExecutionClientFactory)

# Stop and dispose of the node when done
try:
    node.start()
except KeyboardInterrupt:
    print("Stopping node...")
    node.stop()
    node.dispose()