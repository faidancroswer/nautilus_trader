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

from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.indicators.base.indicator import Indicator
from nautilus_trader.indicators.average.sma import SimpleMovingAverage
from nautilus_trader.model.data import Bar


class AlligatorIndicator(Indicator):
    """
    An indicator which calculates the Alligator indicator.
    
    The Alligator indicator consists of three smoothed moving averages:
    - Jaw (Blue): 13-period SMA, shifted 8 bars into the future
    - Teeth (Red): 8-period SMA, shifted 5 bars into the future
    - Lips (Green): 5-period SMA, shifted 3 bars into the future

    Parameters
    ----------
    jaw_period : int
        The period for the Jaw moving average (default 13).
    jaw_shift : int
        The shift for the Jaw moving average (default 8).
    teeth_period : int
        The period for the Teeth moving average (default 8).
    teeth_shift : int
        The shift for the Teeth moving average (default 5).
    lips_period : int
        The period for the Lips moving average (default 5).
    lips_shift : int
        The shift for the Lips moving average (default 3).

    Raises
    ------
    ValueError
        If any period or shift is not positive (> 0).

    """

    def __init__(
        self, 
        jaw_period: int = 13, 
        jaw_shift: int = 8, 
        teeth_period: int = 8, 
        teeth_shift: int = 5, 
        lips_period: int = 5, 
        lips_shift: int = 3
    ):
        PyCondition.positive_int(jaw_period, "jaw_period")
        PyCondition.positive_int(jaw_shift, "jaw_shift")
        PyCondition.positive_int(teeth_period, "teeth_period")
        PyCondition.positive_int(teeth_shift, "teeth_shift")
        PyCondition.positive_int(lips_period, "lips_period")
        PyCondition.positive_int(lips_shift, "lips_shift")
        
        super().__init__(params=[
            jaw_period, 
            jaw_shift, 
            teeth_period, 
            teeth_shift, 
            lips_period, 
            lips_shift
        ])

        # Create the SMAs for each line
        self.jaw_sma = SimpleMovingAverage(jaw_period)
        self.teeth_sma = SimpleMovingAverage(teeth_period)
        self.lips_sma = SimpleMovingAverage(lips_period)
        
        # Store parameters
        self.jaw_period = jaw_period
        self.jaw_shift = jaw_shift
        self.teeth_period = teeth_period
        self.teeth_shift = teeth_shift
        self.lips_period = lips_period
        self.lips_shift = lips_shift
        
        # Store values for each line
        self.jaw_values = []
        self.teeth_values = []
        self.lips_values = []
        
        # Current values (shifted)
        self.jaw = 0.0
        self.teeth = 0.0
        self.lips = 0.0

    def handle_bar(self, bar: Bar):
        """
        Update the indicator with the given bar.

        Parameters
        ----------
        bar : Bar
            The update bar to handle.

        """
        PyCondition.not_none(bar, "bar")

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
        
        # Update count and initialization status
        self.count += 1
        if not self.initialized:
            self._set_has_inputs(True)
            # The indicator is initialized when all lines have valid values
            if (len(self.jaw_values) == self.jaw_shift and 
                len(self.teeth_values) == self.teeth_shift and 
                len(self.lips_values) == self.lips_shift):
                self._set_initialized(True)

    def _reset(self):
        # Reset the SMAs
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
        
        # Reset count
        self.count = 0