#!/usr/bin/env python3
"""
Simplified MT5 adapter for Nautilus Trader
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import MetaTrader5 as mt5

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.enums import LogColor
from nautilus_trader.execution.messages import SubmitOrder
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import AccountBalance
from nautilus_trader.model.objects import Currency
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity


class MT5ExecutionClient(LiveExecutionClient):
    """
    Simplified MT5 execution client for Nautilus Trader
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client_id: ClientId,
        venue: Venue,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        log: logging.Logger,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.MARGIN,
            base_currency=None,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            log=log,
        )
        
        self.config = config or {}
        self._account_id = AccountId(f"{self.venue.value}-001")
        
        # Initialize MT5 connection
        self.log.info("Initializing MT5 connection...", LogColor.BLUE)
        if not mt5.initialize():
            self.log.error(f"Failed to initialize MT5: {mt5.last_error()}")
            raise RuntimeError("Failed to initialize MT5")
        
        self.log.info("MT5 initialized successfully", LogColor.GREEN)

    def connect(self):
        """
        Connect the client.
        """
        self.log.info("Connecting to MT5...", LogColor.BLUE)
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            self.log.error(f"Failed to get account info: {mt5.last_error()}")
            return
            
        self.log.info(f"Connected to MT5 account {account_info.login}", LogColor.GREEN)
        self._set_connected(True)
        self._send_account_state()

    def disconnect(self):
        """
        Disconnect the client.
        """
        self.log.info("Disconnecting from MT5...", LogColor.BLUE)
        mt5.shutdown()
        self._set_connected(False)
        self.log.info("Disconnected from MT5", LogColor.BLUE)

    def submit_order(self, command: SubmitOrder) -> None:
        """
        Submit an order.
        """
        order = command.order
        self.log.info(f"Submitting order {order.client_order_id}", LogColor.BLUE)
        
        # Convert Nautilus order to MT5 order
        symbol = order.instrument_id.symbol.value.replace("/", "")
        order_type = {
            OrderType.MARKET: mt5.ORDER_TYPE_BUY if order.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL,
        }.get(order.order_type, None)
        
        if order_type is None:
            self.log.error(f"Unsupported order type: {order.order_type}")
            return
            
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.log.error(f"Failed to get symbol info for {symbol}")
            return
            
        # Check if symbol is available for trading
        if not symbol_info.visible:
            self.log.info(f"Symbol {symbol} is not visible, trying to select it")
            if not mt5.symbol_select(symbol, True):
                self.log.error(f"Failed to select symbol {symbol}")
                return
        
        # Get current price
        if order.side == OrderSide.BUY:
            price = mt5.symbol_info_tick(symbol).ask
        else:
            price = mt5.symbol_info_tick(symbol).bid
            
        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(order.quantity),
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Nautilus {order.side.value} Order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        # Send order to MT5
        result = mt5.order_send(request)
        if result is None:
            self.log.error(f"Failed to send order: {mt5.last_error()}")
            return
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log.error(f"Order failed with retcode {result.retcode}")
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
            trade_id=str(result.deal),
            order_side=order.side,
            order_type=order.order_type,
            last_qty=order.quantity,
            last_px=Price(result.price, 5),
            quote_currency=Currency.USD,
            commission=Money(0, Currency.USD),
            liquidity_side=None,
        )

    def _send_account_state(self):
        """
        Send account state.
        """
        account_info = mt5.account_info()
        if account_info is None:
            return
            
        balances = [
            AccountBalance(
                total=Money(account_info.balance, Currency.USD),
                locked=Money(account_info.margin, Currency.USD),
                free=Money(account_info.balance - account_info.margin, Currency.USD),
            )
        ]
        
        self.generate_account_state(
            balances=balances,
            margins=[],
            reported=True,
            ts_event=self._clock.timestamp_ns(),
        )


class MT5DataClient(LiveDataClient):
    """
    Simplified MT5 data client for Nautilus Trader
    """
    
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client_id: ClientId,
        venue: Venue,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        log: logging.Logger,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=venue,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            log=log,
        )
        
        self.config = config or {}
        
        # Initialize MT5 connection
        self.log.info("Initializing MT5 data connection...", LogColor.BLUE)
        if not mt5.initialize():
            self.log.error(f"Failed to initialize MT5 data: {mt5.last_error()}")
            raise RuntimeError("Failed to initialize MT5 data")
        
        self.log.info("MT5 data initialized successfully", LogColor.GREEN)

    def connect(self):
        """
        Connect the client.
        """
        self.log.info("Connecting to MT5 for data...", LogColor.BLUE)
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            self.log.error(f"Failed to get account info: {mt5.last_error()}")
            return
            
        self.log.info(f"Connected to MT5 account {account_info.login} for data", LogColor.GREEN)
        self._set_connected(True)

    def disconnect(self):
        """
        Disconnect the client.
        """
        self.log.info("Disconnecting from MT5 data feed...", LogColor.BLUE)
        mt5.shutdown()
        self._set_connected(False)
        self.log.info("Disconnected from MT5 data feed", LogColor.BLUE)