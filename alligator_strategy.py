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

from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import PositiveInt
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.indicators.base.indicator import Indicator
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy

# Import our custom Alligator indicator
from alligator_indicator import AlligatorIndicator


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
    subscribe_trade_ticks : bool, default True
        If trades should be subscribed to.
    request_bars : bool, default True
        If historical bars should be requested on strategy start.
    unsubscribe_data_on_stop : bool, default True
        If live data feeds should be unsubscribed on strategy stop.
    order_quantity_precision : int, optional
        The quantity precision for strategy market orders.
    order_time_in_force : TimeInForce, optional
        The time in force for strategy market orders.
    close_positions_on_stop : bool, default True
        If all open positions should be closed on strategy stop.
    reduce_only_on_stop : bool, default True
        If position closing market orders on stop should be reduce-only.

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
    subscribe_trade_ticks: bool = True
    request_bars: bool = True
    unsubscribe_data_on_stop: bool = True
    order_quantity_precision: int | None = None
    order_time_in_force: TimeInForce | None = None
    close_positions_on_stop: bool = True
    reduce_only_on_stop: bool = True


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
        super().__init__(config)

        self.instrument: Instrument = None

        # Create the Alligator indicator for the strategy
        self.alligator = AlligatorIndicator(
            jaw_period=config.jaw_period,
            jaw_shift=config.jaw_shift,
            teeth_period=config.teeth_period,
            teeth_shift=config.teeth_shift,
            lips_period=config.lips_period,
            lips_shift=config.lips_shift
        )

    def on_start(self) -> None:
        """
        Actions to be performed on strategy start.
        """
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument for {self.config.instrument_id}")
            self.stop()
            return

        # Register the indicator for updating
        self.register_indicator_for_bars(self.config.bar_type, self.alligator)

        # Get historical data
        if self.config.request_bars:
            self.request_bars(
                self.config.bar_type,
                start=self._clock.utc_now() - pd.Timedelta(days=1),
            )

        # Subscribe to real-time data
        self.subscribe_bars(self.config.bar_type)

        if self.config.subscribe_trade_ticks:
            self.subscribe_trade_ticks(self.config.instrument_id)

    def on_bar(self, bar: Bar) -> None:
        """
        Actions to be performed when the strategy is running and receives a bar.

        Parameters
        ----------
        bar : Bar
            The bar received.

        """
        self.log.info(repr(bar), LogColor.CYAN)

        # Check if indicators ready
        if not self.indicators_initialized():
            self.log.info(
                f"Waiting for indicators to warm up [{self.cache.bar_count(self.config.bar_type)}]",
                color=LogColor.BLUE,
            )
            return  # Wait for indicators to warm up...

        if bar.is_single_price():
            self._log.warning("Bar OHLC is single price; implies no market information")
            return

        # Get current price
        current_price = bar.close.as_double()
        
        # BUY LOGIC: Price above all lines and ascending order (lips > teeth > jaw)
        if (current_price > self.alligator.lips > self.alligator.teeth > self.alligator.jaw):
            if self.portfolio.is_flat(self.config.instrument_id):
                self.buy()
            elif self.portfolio.is_net_short(self.config.instrument_id):
                self.close_all_positions(self.config.instrument_id)
                self.buy()
                
        # SELL LOGIC: Price below all lines and descending order (lips < teeth < jaw)
        elif (current_price < self.alligator.lips < self.alligator.teeth < self.alligator.jaw):
            if self.portfolio.is_flat(self.config.instrument_id):
                self.sell()
            elif self.portfolio.is_net_long(self.config.instrument_id):
                self.close_all_positions(self.config.instrument_id)
                self.sell()

    def buy(self) -> None:
        """
        Users simple buy method (example).
        """
        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.create_order_qty(),
            time_in_force=self.config.order_time_in_force or TimeInForce.GTC,
        )

        self.submit_order(order)

    def sell(self) -> None:
        """
        Users simple sell method (example).
        """
        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.create_order_qty(),
            time_in_force=self.config.order_time_in_force or TimeInForce.GTC,
        )

        self.submit_order(order)

    def create_order_qty(self) -> Quantity:
        if self.config.order_quantity_precision is not None:
            return Quantity(self.config.trade_size, self.config.order_quantity_precision)
        else:
            return self.instrument.make_qty(self.config.trade_size)

    def on_stop(self) -> None:
        """
        Actions to be performed when the strategy is stopped.
        """
        self.cancel_all_orders(self.config.instrument_id)
        if self.config.close_positions_on_stop:
            self.close_all_positions(
                instrument_id=self.config.instrument_id,
                reduce_only=self.config.reduce_only_on_stop,
            )

        if self.config.unsubscribe_data_on_stop:
            self.unsubscribe_bars(self.config.bar_type)

        if self.config.unsubscribe_data_on_stop and self.config.subscribe_trade_ticks:
            self.unsubscribe_trade_ticks(self.config.instrument_id)

    def on_reset(self) -> None:
        """
        Actions to be performed when the strategy is reset.
        """
        # Reset indicators here
        self.alligator.reset()

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