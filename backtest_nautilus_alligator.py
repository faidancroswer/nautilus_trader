#!/usr/bin/env python3
"""
Script to run a backtest with the Alligator strategy using Nautilus Trader.
"""

import logging
import sys
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Import Nautilus Trader modules
    from nautilus_trader.backtest.engine import BacktestEngine
    from nautilus_trader.backtest.modules import FXRolloverInterestConfig
    from nautilus_trader.backtest.modules import FXRolloverInterestModule
    from nautilus_trader.config import BacktestEngineConfig
    from nautilus_trader.config import LoggingConfig
    from nautilus_trader.model.currencies import USD
    from nautilus_trader.model.data import BarType
    from nautilus_trader.model.enums import AccountType
    from nautilus_trader.model.enums import OmsType
    from nautilus_trader.model.identifiers import InstrumentId
    from nautilus_trader.model.identifiers import Venue
    from nautilus_trader.model.objects import Money
    
    # Import our custom strategy
    from nautilus_alligator_strategy import AlligatorConfig
    from nautilus_alligator_strategy import AlligatorStrategy
    
    logger.info("All modules imported successfully")
    
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.error("Please make sure Nautilus Trader is properly installed")
    sys.exit(1)


def main():
    logger.info("Starting Alligator strategy backtest with Nautilus Trader")
    
    # Configure the backtest engine
    config = BacktestEngineConfig(
        trader_id="BACKTESTER-001",
        logging=LoggingConfig(log_level="INFO"),
    )
    
    # Create the backtest engine
    engine = BacktestEngine(config=config)
    
    # Add a venue (for simulation)
    VENUE = Venue("SIM")
    engine.add_venue(
        venue=VENUE,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(1_000_000, USD)],
        default_leverage=50.0,
        leverages={},
    )
    
    # Configure your strategy
    strategy_config = AlligatorConfig(
        instrument_id=InstrumentId.from_str("EUR/USD.SIM"),  # Example instrument
        bar_type=BarType.from_str("EUR/USD.SIM-1-MINUTE-BID-EXTERNAL"),  # Example bar type
        trade_size=Decimal("1000"),  # 1,000 units
        jaw_period=13,
        jaw_shift=8,
        teeth_period=8,
        teeth_shift=5,
        lips_period=5,
        lips_shift=3,
    )

    # Instantiate your strategy
    strategy = AlligatorStrategy(config=strategy_config)
    
    # Add the strategy to the engine
    engine.add_strategy(strategy)
    
    # Run the backtest (this would normally include data, but we're just testing the setup)
    logger.info("Backtest engine configured successfully")
    logger.info(f"Strategy config: {strategy_config}")
    
    # In a real implementation, we would:
    # 1. Add data to the engine
    # 2. Run the backtest
    # 3. Generate reports
    
    logger.info("Backtest setup completed successfully")


if __name__ == "__main__":
    main()