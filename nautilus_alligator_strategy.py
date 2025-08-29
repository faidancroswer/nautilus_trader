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

from decimal import Decimal

import pandas as pd

from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import PositiveInt
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.indicators.average.sma import SimpleMovingAverage
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy


class AlligatorConfig(StrategyConfig, frozen=True):
    """
    Configuration for ``AlligatorStrategy`` instances.

    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument ID for the strategy.
    bar_type : BarType
        The bar type for the strategy.
    trade_size : Decimal
        The position size per trade.
    jaw_period : int, default 13
        The period for the Jaw moving average.
    jaw_shift : int, default 8
        The shift for the Jaw moving average.
    teeth_period : int, default 8
        The period for the Teeth moving average.
    teeth_shift : int, default 5
        The shift for the Teeth moving average.
    lips_period : int, default 5
        The period for the Lips moving average.
    lips_shift : int, default 3
        The shift for the Lips moving average.
    """

    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    jaw_period: PositiveInt = 13
    jaw_shift: PositiveInt = 8
    teeth_period: PositiveInt = 8
    teeth_shift: PositiveInt = 5
    lips_period: PositiveInt = 5
    lips_shift: PositiveInt = 3


class AlligatorStrategy(Strategy):
    """
    A simple Alligator strategy example.

    When the price is above all three Alligator lines and they are aligned in 
    ascending order (lips > teeth > jaw), it's a buy signal.
    When the price is below all three Alligator lines and they are aligned in 
    descending order (lips < teeth < jaw), it's a sell signal.

    Parameters
    ----------
    config : AlligatorConfig
        The configuration for the instance.

    """

    def __init__(self, config: AlligatorConfig) -> None:
        PyCondition.type(config, AlligatorConfig, "config")
        super().__init__(config)

        # Configuration
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.trade_size = config.trade_size

        # Create the indicators for the strategy
        self.jaw_sma = SimpleMovingAverage(config.jaw_period)
        self.teeth_sma = SimpleMovingAverage(config.teeth_period)
        self.lips_sma = SimpleMovingAverage(config.lips_period)
        
        # Store parameters
        self.jaw_shift = config.jaw_shift
        self.teeth_shift = config.teeth_shift
        self.lips_shift = config.lips_shift
        
        # Store values for each line with shifts
        self.jaw_values = []
        self.teeth_values = []
        self.lips_values = []
        
        # Current values (shifted)
        self.jaw = 0.0
        self.teeth = 0.0
        self.lips = 0.0
        
        # Instrument
        self.instrument = None

    def on_start(self) -> None:
        """
        Actions to be performed on strategy start.
        """
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument for {self.instrument_id}")
            self.stop()
            return

        # Register indicators for bar updates
        self.register_indicator_for_bars(self.bar_type, self.jaw_sma)
        self.register_indicator_for_bars(self.bar_type, self.teeth_sma)
        self.register_indicator_for_bars(self.bar_type, self.lips_sma)

        # Request historical data
        self.request_bars(self.bar_type, start=pd.Timestamp.utcnow() - pd.Timedelta(days=1))

        # Subscribe to real-time data
        self.subscribe_bars(self.bar_type)

    def on_bar(self, bar: Bar) -> None:
        """
        Actions to be performed when the strategy receives a bar.

        Parameters
        ----------
        bar : Bar
            The bar received.

        """
        self.log.info(repr(bar), LogColor.CYAN)

        # Check if indicators are initialized
        if not self.indicators_initialized():
            self.log.info(
                f"Waiting for indicators to warm up [{self.cache.bar_count(self.bar_type)}]",
                color=LogColor.BLUE,
            )
            return

        # Update the SMAs with the bar's close price
        self.jaw_sma.update_raw(bar.close.as_double())
        self.teeth_sma.update_raw(bar.close.as_double())
        self.lips_sma.update_raw(bar.close.as_double())
        
        # Store the current SMA values
        self.jaw_values.append(self.jaw_sma.value)
        self.teeth_values.append(self.teeth_sma.value)
        self.lips_values.append(self.lips_sma.value)
        
        # Maintain only the necessary number of values based on shifts
        if len(self.jaw_values) > self.jaw_shift:
            self.jaw_values.pop(0)
        if len(self.teeth_values) > self.teeth_shift:
            self.teeth_values.pop(0)
        if len(self.lips_values) > self.lips_shift:
            self.lips_values.pop(0)
            
        # Set the shifted values as current values
        self.jaw = self.jaw_values[0] if len(self.jaw_values) == self.jaw_shift else 0.0
        self.teeth = self.teeth_values[0] if len(self.teeth_values) == self.teeth_shift else 0.0
        self.lips = self.lips_values[0] if len(self.lips_values) == self.lips_shift else 0.0
        
        # Check if all indicators are ready with shifted values
        if self.jaw == 0.0 or self.teeth == 0.0 or self.lips == 0.0:
            return

        # Get current price
        current_price = bar.close.as_double()
        
        # BUY LOGIC: Price above all lines and ascending order (lips > teeth > jaw)
        if (current_price > self.lips > self.teeth > self.jaw):
            if self.portfolio.is_flat(self.instrument_id):
                self.buy()
            elif self.portfolio.is_net_short(self.instrument_id):
                self.close_all_positions(self.instrument_id)
                self.buy()
                
        # SELL LOGIC: Price below all lines and descending order (lips < teeth < jaw)
        elif (current_price < self.lips < self.teeth < self.jaw):
            if self.portfolio.is_flat(self.instrument_id):
                self.sell()
            elif self.portfolio.is_net_long(self.instrument_id):
                self.close_all_positions(self.instrument_id)
                self.sell()

    def buy(self) -> None:
        """
        Users simple buy method (example).
        """
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )

        self.submit_order(order)

    def sell(self) -> None:
        """
        Users simple sell method (example).
        """
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )

        self.submit_order(order)

    def on_stop(self) -> None:
        """
        Actions to be performed when the strategy is stopped.
        """
        # Cancel all orders
        self.cancel_all_orders(self.instrument_id)
        
        # Close all positions
        self.close_all_positions(self.instrument_id)

    def on_reset(self) -> None:
        """
        Actions to be performed when the strategy is reset.
        """
        # Reset indicators
        self.jaw_sma.reset()
        self.teeth_sma.reset()
        self.lips_sma.reset()
        
        # Reset stored values
        self.jaw_values.clear()
        self.teeth_values.clear()
        self.lips_values.clear()
        
        # Reset current values
        self.jaw = 0.0
        self.teeth = 0.0
        self.lips = 0.0

    def on_save(self) -> dict[str, bytes]:
        """
        Actions to be performed when the strategy is saved.

        Create and return a state dictionary of values to be saved.

        Returns
        -------
        dict[str, bytes]
            The strategy state dictionary.

        """
        return {}

    def on_load(self, state: dict[str, bytes]) -> None:
        """
        Actions to be performed when the strategy is loaded.

        Saved state values will be contained in the give state dictionary.

        Parameters
        ----------
        state : dict[str, bytes]
            The strategy state dictionary.

        """

    def on_dispose(self) -> None:
        """
        Actions to be performed when the strategy is disposed.

        Cleanup any resources used by the strategy here.

        """