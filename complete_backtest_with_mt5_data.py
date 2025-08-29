#!/usr/bin/env python3
"""
Script to run a complete backtest with the Alligator strategy using Nautilus Trader and MT5 data.
"""

import logging
import os
import sys
from decimal import Decimal

import pandas as pd

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
    from nautilus_trader.model.data import Bar
    from nautilus_trader.model.data import BarType
    from nautilus_trader.model.enums import AccountType
    from nautilus_trader.model.enums import OmsType
    from nautilus_trader.model.identifiers import InstrumentId
    from nautilus_trader.model.identifiers import Venue
    from nautilus_trader.model.identifiers import Symbol
    from nautilus_trader.model.instruments import CurrencyPair
    from nautilus_trader.model.objects import Money
    from nautilus_trader.model.objects import Price
    from nautilus_trader.model.objects import Quantity
    
    # Import our custom strategy
    from nautilus_alligator_strategy import AlligatorConfig
    from nautilus_alligator_strategy import AlligatorStrategy
    
    logger.info("All modules imported successfully")
    
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.error("Please make sure Nautilus Trader is properly installed")
    sys.exit(1)


def load_mt5_data(filename):
    """
    Load MT5 data from CSV file
    
    Parameters:
    filename (str): Path to CSV file
    
    Returns:
    pandas.DataFrame: Loaded data
    """
    try:
        data = pd.read_csv(filename)
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        logger.info(f"Loaded {len(data)} rows from {filename}")
        return data
    except Exception as e:
        logger.error(f"Failed to load data from {filename}: {e}")
        return None


def create_instrument():
    """
    Create a currency pair instrument for backtesting
    
    Returns:
    CurrencyPair: Currency pair instrument
    """
    # Create EUR/USD instrument
    instrument = CurrencyPair(
        instrument_id=InstrumentId.from_str("EUR/USD.SIM"),
        raw_symbol=Symbol("EURUSD"),
        base_currency=USD,
        quote_currency=USD,
        price_precision=5,
        size_precision=2,
        price_increment=Price(0.00001, 5),
        size_increment=Quantity(0.01, 2),
        lot_size=Quantity(1000, 0),
        max_quantity=Quantity(1000000, 0),
        min_quantity=Quantity(0.01, 2),
        max_notional=None,
        min_notional=Money(0.01, USD),
        margin_init=Decimal("0.02"),
        margin_maint=Decimal("0.005"),
        maker_fee=Decimal("0.00002"),
        taker_fee=Decimal("0.00002"),
        ts_event=0,
        ts_init=0,
    )
    return instrument


def run_backtest():
    """
    Run a complete backtest with MT5 data
    """
    logger.info("Starting backtest with MT5 data")
    
    # Load data
    filename = "EURUSD_historical_data.csv"
    data = load_mt5_data(filename)
    if data is None:
        return
    
    # Configure the backtest engine
    config = BacktestEngineConfig(
        trader_id="BACKTESTER-001",
        logging=LoggingConfig(log_level="INFO"),
    )
    
    # Create the backtest engine
    engine = BacktestEngine(config=config)
    
    # Add instrument
    instrument = create_instrument()
    
    # Add a venue (for simulation)
    VENUE = Venue("SIM")
    engine.add_venue(
        venue=VENUE,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(100000, USD)],  # $100,000
        default_leverage=50.0,
        leverages={},
    )
    
    # Add instrument to the engine
    engine.add_instrument(instrument)
    
    # Configure your strategy
    strategy_config = AlligatorConfig(
        instrument_id=InstrumentId.from_str("EUR/USD.SIM"),
        bar_type=BarType.from_str("EUR/USD.SIM-1-MINUTE-BID-EXTERNAL"),
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
    
    # Add data to the engine
    logger.info("Adding data to engine...")
    bar_type = BarType.from_str("EUR/USD.SIM-1-MINUTE-BID-EXTERNAL")
    
    # Convert data to Nautilus Trader bars
    for _, row in data.iterrows():
        bar = Bar(
            bar_type=bar_type,
            open=Price(row['open'], 5),
            high=Price(row['high'], 5),
            low=Price(row['low'], 5),
            close=Price(row['close'], 5),
            volume=Quantity(row['volume'], 0),
            ts_event=int(row['timestamp'].timestamp() * 1e9),  # Convert to nanoseconds
            ts_init=int(row['timestamp'].timestamp() * 1e9),
        )
        engine.add_data([bar])
    
    # Run the backtest
    logger.info("Running backtest...")
    engine.run()
    
    # Generate reports
    logger.info("Generating reports...")
    reports = engine.reports()
    print(reports)
    
    # Shutdown engine
    engine.dispose()
    logger.info("Backtest completed")


def main():
    logger.info("Starting complete backtest with Alligator strategy and MT5 data")
    run_backtest()


if __name__ == "__main__":
    main()