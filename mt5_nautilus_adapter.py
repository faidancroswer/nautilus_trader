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
from typing import Optional

import msgspec
import pandas as pd
from nautilus_trader.adapters.base import BaseDataClient, BaseExecutionClient
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.execution.messages import SubmitOrder
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.live.execution_engine import LiveExecutionEngine
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import PositionId
from nautilus_trader.model.identifiers import StrategyId
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import AccountBalance
from nautilus_trader.model.objects import Currency
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import Order


class MT5ExecutionClient(BaseExecutionClient):
    """
    An example MT5 execution client adapter for Nautilus Trader.
    
    This client is not complete and is provided for illustrative purposes only.
    It does not handle all order types, error conditions, or edge cases.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client_id: ClientId,
        venue: Venue,
        instrument_provider,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        log,
        config: Optional[dict] = None,
    ):
        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.MARGIN,
            base_currency=None,
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            log=log,
        )
        
        self.config = config or {}
        self._account_id = AccountId(f"{self.venue.value}-001")
        
        # Initialize MT5 connection
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
            if not self.mt5.initialize():
                self._log.error(f"Failed to initialize MT5: {self.mt5.last_error()}")
                return
            self._log.info("MT5 initialized successfully", LogColor.GREEN)
        except ImportError:
            self._log.error("MetaTrader5 package not installed")
            return

    def connect(self):
        """
        Connect the client.
        """
        self._log.info("Connecting to MT5...", LogColor.BLUE)
        
        # Get account info
        account_info = self.mt5.account_info()
        if account_info is None:
            self._log.error(f"Failed to get account info: {self.mt5.last_error()}")
            return
            
        self._log.info(f"Connected to MT5 account {account_info.login}", LogColor.GREEN)
        self._set_connected(True)
        self._send_account_state()

    def disconnect(self):
        """
        Disconnect the client.
        """
        self._log.info("Disconnecting from MT5...", LogColor.BLUE)
        self.mt5.shutdown()
        self._set_connected(False)
        self._log.info("Disconnected from MT5", LogColor.BLUE)

    def submit_order(self, command: SubmitOrder) -> None:
        """
        Submit an order.
        """
        order = command.order
        self._log.info(f"Submitting order {order.client_order_id}", LogColor.BLUE)
        
        # Convert Nautilus order to MT5 order
        symbol = order.instrument_id.symbol.value.replace("/", "")
        order_type = {
            OrderType.MARKET: self.mt5.ORDER_TYPE_BUY if order.side == OrderSide.BUY else self.mt5.ORDER_TYPE_SELL,
        }.get(order.order_type, None)
        
        if order_type is None:
            self._log.error(f"Unsupported order type: {order.order_type}")
            return
            
        # Get symbol info
        symbol_info = self.mt5.symbol_info(symbol)
        if symbol_info is None:
            self._log.error(f"Failed to get symbol info for {symbol}")
            return
            
        # Check if symbol is available for trading
        if not symbol_info.visible:
            self._log.info(f"Symbol {symbol} is not visible, trying to select it")
            if not self.mt5.symbol_select(symbol, True):
                self._log.error(f"Failed to select symbol {symbol}")
                return
        
        # Get current price
        if order.side == OrderSide.BUY:
            price = self.mt5.symbol_info_tick(symbol).ask
        else:
            price = self.mt5.symbol_info_tick(symbol).bid
            
        # Prepare order request
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(order.quantity),
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Nautilus {order.side.value} Order",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_FOK,  # Fill or Kill
        }
        
        # Send order to MT5
        result = self.mt5.order_send(request)
        if result is None:
            self._log.error(f"Failed to send order: {self.mt5.last_error()}")
            return
            
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            self._log.error(f"Order failed with retcode {result.retcode}")
            return
            
        # Report order status
        self.generate_order_accepted(
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=VenueOrderId(str(result.order)),
        )
        
        # Report trade
        self.generate_order_filled(
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=VenueOrderId(str(result.order)),
            venue_position_id=None,
            trade_id=TradeId(str(result.deal)),
            order_side=order.side,
            order_type=order.order_type,
            last_qty=order.quantity,
            last_px=Price(result.price, 5),  # TODO: Get proper precision
            quote_currency=Currency.USD,  # TODO: Get proper currency
            commission=Money(0, Currency.USD),  # TODO: Get proper commission
            liquidity_side=None,  # TODO: Determine liquidity side
        )

    def _send_account_state(self):
        """
        Send account state.
        """
        account_info = self.mt5.account_info()
        if account_info is None:
            return
            
        balances = [
            AccountBalance(
                total=Money(account_info.balance, Currency.USD),  # TODO: Get proper currency
                locked=Money(account_info.margin, Currency.USD),   # TODO: Get proper currency
                free=Money(account_info.balance - account_info.margin, Currency.USD),  # TODO: Get proper currency
            )
        ]
        
        self.generate_account_state(
            balances=balances,
            margins=[],
            reported=True,
            ts_event=self._clock.timestamp_ns(),
        )


class MT5DataClient(BaseDataClient):
    """
    An example MT5 data client adapter for Nautilus Trader.
    
    This client is not complete and is provided for illustrative purposes only.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client_id: ClientId,
        venue: Venue,
        instrument_provider,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        log,
        config: Optional[dict] = None,
    ):
        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=venue,
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            log=log,
        )
        
        self.config = config or {}
        
        # Initialize MT5 connection
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
            if not self.mt5.initialize():
                self._log.error(f"Failed to initialize MT5: {self.mt5.last_error()}")
                return
            self._log.info("MT5 initialized successfully", LogColor.GREEN)
        except ImportError:
            self._log.error("MetaTrader5 package not installed")
            return

    def connect(self):
        """
        Connect the client.
        """
        self._log.info("Connecting to MT5 for data...", LogColor.BLUE)
        
        # Get account info
        account_info = self.mt5.account_info()
        if account_info is None:
            self._log.error(f"Failed to get account info: {self.mt5.last_error()}")
            return
            
        self._log.info(f"Connected to MT5 account {account_info.login} for data", LogColor.GREEN)
        self._set_connected(True)

    def disconnect(self):
        """
        Disconnect the client.
        """
        self._log.info("Disconnecting from MT5 data feed...", LogColor.BLUE)
        self.mt5.shutdown()
        self._set_connected(False)
        self._log.info("Disconnected from MT5 data feed", LogColor.BLUE)

    # Implement data subscription methods as needed
    # For example:
    # def subscribe_bars(self, bar_type: BarType):
    #     # Subscribe to bar data from MT5
    #     pass
    # 
    # def subscribe_quote_ticks(self, instrument_id: InstrumentId):
    #     # Subscribe to quote tick data from MT5
    #     pass