#!/usr/bin/env python3
"""
MT5 Live Adapter for Nautilus Trader
This adapter connects to a live MT5 account and executes trades
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.execution.messages import SubmitOrder
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.execution.reports import PositionStatusReport
from nautilus_trader.execution.reports import TradeReport
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.data import TradeTick
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
from nautilus_trader.model.position import Position


class MT5ExecutionClient(LiveExecutionClient):
    """
    An example MT5 execution client adapter for Nautilus Trader.
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
            instrument_provider=instrument_provider,
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
        
        # Get account info
        self.account_info = mt5.account_info()
        if self.account_info is None:
            self.log.error(f"Failed to get account info: {mt5.last_error()}")
            raise RuntimeError("Failed to get account info")
            
        self.log.info(f"Connected to MT5 account {self.account_info.login}", LogColor.GREEN)

    def connect(self):
        """
        Connect the client.
        """
        self.log.info("Connecting to MT5...", LogColor.BLUE)
        
        # Check if we're already connected
        if not mt5.initialize():
            self.log.error(f"Failed to initialize MT5: {mt5.last_error()}")
            return
            
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
            self.log.error(f"Failed to get symbol info for {symbol}: {mt5.last_error()}")
            return
            
        # Check if symbol is available for trading
        if not symbol_info.visible:
            self.log.info(f"Symbol {symbol} is not visible, trying to select it")
            if not mt5.symbol_select(symbol, True):
                self.log.error(f"Failed to select symbol {symbol}: {mt5.last_error()}")
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
            "type_filling": mt5.ORDER_FILLING_FOK,  # Fill or Kill
        }
        
        # Send order to MT5
        result = mt5.order_send(request)
        if result is None:
            self.log.error(f"Failed to send order: {mt5.last_error()}")
            return
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log.error(f"Order failed with retcode {result.retcode}")
            # Log additional information for debugging
            self.log.error(f"Request: {request}")
            self.log.error(f"Result: {result}")
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
        account_info = mt5.account_info()
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


class MT5DataClient:
    """
    An example MT5 data client for Nautilus Trader.
    """
    
    def __init__(self, log: logging.Logger):
        self.log = log
        self.mt5 = mt5
        
        # Initialize MT5 connection
        self.log.info("Initializing MT5 data connection...", LogColor.BLUE)
        if not self.mt5.initialize():
            self.log.error(f"Failed to initialize MT5 data: {self.mt5.last_error()}")
            raise RuntimeError("Failed to initialize MT5 data")
        
        self.log.info("MT5 data initialized successfully", LogColor.GREEN)

    def fetch_bars(self, symbol: str, timeframe: int, count: int = 1000):
        """
        Fetch bars from MT5
        
        Parameters:
        symbol (str): Symbol to fetch data for
        timeframe (int): Timeframe (e.g., mt5.TIMEFRAME_M1)
        count (int): Number of bars to fetch
        
        Returns:
        list: List of bars
        """
        # Fetch data
        rates = self.mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            self.log.error(f"Failed to fetch data for {symbol}: {self.mt5.last_error()}")
            return []
        
        # Convert to list of bars
        bars = []
        for rate in rates:
            bar = {
                'timestamp': rate['time'],
                'open': rate['open'],
                'high': rate['high'],
                'low': rate['low'],
                'close': rate['close'],
                'volume': rate['tick_volume']
            }
            bars.append(bar)
            
        return bars

    def shutdown(self):
        """
        Shutdown MT5 connection
        """
        self.mt5.shutdown()