#!/usr/bin/env python3
"""
Simplified factory classes for MT5 adapters
"""

import asyncio
from typing import Optional, Dict, Any

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import Venue

from simplified_mt5_adapter import MT5ExecutionClient
from simplified_mt5_adapter import MT5DataClient


class MT5DataClientFactory:
    """
    Simplified factory for creating MT5 data clients.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def __call__(
        self,
        loop: asyncio.AbstractEventLoop,
        name: str,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        log: Logger,
    ):
        client = MT5DataClient(
            loop=loop,
            client_id=ClientId(name),
            venue=Venue(name),
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            log=log,
            config=self.config,
        )
        return client


class MT5ExecClientFactory:
    """
    Simplified factory for creating MT5 execution clients.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def __call__(
        self,
        loop: asyncio.AbstractEventLoop,
        name: str,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        log: Logger,
    ):
        client = MT5ExecutionClient(
            loop=loop,
            client_id=ClientId(name),
            venue=Venue(name),
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            log=log,
            config=self.config,
        )
        return client