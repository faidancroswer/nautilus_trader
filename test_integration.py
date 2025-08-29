#!/usr/bin/env python3
"""
Test script to verify MT5 connection and Nautilus Trader integration
"""

import logging
import sys
import MetaTrader5 as mt5

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mt5_connection():
    """
    Test MT5 connection
    """
    logger.info("Testing MT5 connection...")
    
    # Initialize MT5
    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    
    logger.info("MT5 initialized successfully")
    
    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        logger.error(f"Failed to get account info: {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    logger.info(f"Connected to MT5 account {account_info.login}")
    logger.info(f"Balance: {account_info.balance} {account_info.currency}")
    logger.info(f"Equity: {account_info.equity} {account_info.currency}")
    
    # Get terminal info
    terminal_info = mt5.terminal_info()
    if terminal_info is not None:
        logger.info(f"Terminal connected: {terminal_info.connected}")
        logger.info(f"Trade allowed: {terminal_info.trade_allowed}")
    
    # Get some symbols
    symbols = mt5.symbols_get()
    if symbols is not None:
        logger.info(f"Available symbols: {len(symbols)}")
        # Show first 5 symbols
        for symbol in symbols[:5]:
            logger.info(f"  - {symbol.name}")
    
    # Shutdown MT5
    mt5.shutdown()
    logger.info("MT5 connection test completed")
    return True


def test_nautilus_imports():
    """
    Test Nautilus Trader imports
    """
    logger.info("Testing Nautilus Trader imports...")
    
    try:
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
        from mt5_factories import MT5DataClientFactory
        from mt5_factories import MT5ExecClientFactory
        
        logger.info("All Nautilus Trader imports successful")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import Nautilus Trader modules: {e}")
        return False


def main():
    """
    Main function
    """
    logger.info("Starting MT5 and Nautilus Trader integration test")
    
    # Test MT5 connection
    if not test_mt5_connection():
        logger.error("MT5 connection test failed")
        return
    
    # Test Nautilus Trader imports
    if not test_nautilus_imports():
        logger.error("Nautilus Trader import test failed")
        return
    
    logger.info("All tests passed! Ready for live trading.")


if __name__ == "__main__":
    main()