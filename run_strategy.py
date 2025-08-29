import asyncio
import logging
from decimal import Decimal

from nautilus_trader.adapters.betfair.factories import BetfairLiveDataClientFactory
from nautilus_trader.adapters.betfair.factories import BetfairLiveExecutionClientFactory
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.modules import FXRolloverInterestConfig
from nautilus_trader.backtest.modules import FXRolloverInterestModule
from nautilus_trader.common.component import Logger
from nautilus_trader.common.component import LoggerAdapter
from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import NautilusKernelConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.data.engine import DataEngineConfig
from nautilus_trader.examples.strategies.ema_cross import EMACross
from nautilus_trader.examples.strategies.ema_cross import EMACrossConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.external.core import process_files
from nautilus_trader.persistence.external.readers import CSVReader
from nautilus_trader.portfolio.portfolio import PortfolioConfig
from nautilus_trader.risk.engine import RiskEngineConfig
from nautilus_trader.system.kernel import NautilusKernel

# Import our custom strategy and indicator
from alligator_strategy import AlligatorConfig
from alligator_strategy import AlligatorStrategy
from config import *


def main():
    # Setup logging
    logger = LoggerAdapter(logging.getLogger("main"), Logger(logging.INFO))
    
    # Configuration
    instrument_id = InstrumentId.from_str(INSTRUMENT_ID)
    bar_type = BarType.from_str(BAR_TYPE)
    
    # Strategy configuration
    config = AlligatorConfig(
        instrument_id=instrument_id,
        bar_type=bar_type,
        trade_size=Decimal(str(TRADE_SIZE)),
        jaw_period=JAW_PERIOD,
        jaw_shift=JAW_SHIFT,
        teeth_period=TEETH_PERIOD,
        teeth_shift=TEETH_SHIFT,
        lips_period=LIPS_PERIOD,
        lips_shift=LIPS_SHIFT,
    )
    
    # Create strategy instance
    strategy = AlligatorStrategy(config=config)
    
    # Create trading node
    node = TradingNode(
        config=NautilusKernelConfig(
            environment="live",
            trader_id="TESTER-001",
            logging=LoggingConfig(
                log_level="INFO",
                log_file="nautilus.log",
            ),
            data_engine=DataEngineConfig(
                time_bars_timestamp_on_close=False,
            ),
            risk_engine=RiskEngineConfig(
                bypass=True,  # Example bypass for testing
            ),
            portfolio=PortfolioConfig(
                cash_precision=8,
            ),
            loop_debug=False,
        ),
        strategies=[strategy],
    )
    
    # Register client factories
    # Note: This is a simplified example. In practice, you would need to implement
    # proper MT5 client factories similar to Betfair's.
    # node.trader.add_data_client_factory("MT5", MT5LiveDataClientFactory)
    # node.trader.add_execution_client_factory("MT5", MT5LiveExecutionClientFactory)
    
    # Connect to MT5
    # This is a placeholder - actual implementation would depend on your MT5 setup
    logger.info("Starting trading node...", LogColor.BLUE)
    node.start()
    
    # Keep the node running
    try:
        node.wait()
    except KeyboardInterrupt:
        logger.info("Stopping trading node...", LogColor.BLUE)
        node.stop()
        node.dispose()


if __name__ == "__main__":
    main()