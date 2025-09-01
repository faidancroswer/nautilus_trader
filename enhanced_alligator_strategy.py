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

"""
Enhanced Alligator Strategy - Unified Implementation
Combines Nautilus Trader, advanced technical analysis, AI integration, and risk management
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import PositiveInt, PositiveFloat
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.indicators.average.sma import SimpleMovingAverage
from nautilus_trader.indicators.momentum.rsi import RelativeStrengthIndex
from nautilus_trader.indicators.momentum.macd import MovingAverageConvergenceDivergence
from nautilus_trader.indicators.momentum.bb import BollingerBands
from nautilus_trader.indicators.momentum.stochastics import StochasticOscillator
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy

from ollama_agent import OllamaAgent
from risk_manager import RiskManager
from market_analyzer import MarketAnalyzer
from performance_analyzer import PerformanceAnalyzer


class EnhancedAlligatorConfig(StrategyConfig, frozen=True):
    """
    Configuration for EnhancedAlligatorStrategy instances with comprehensive settings.

    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument ID for the strategy.
    bar_type : BarType
        The bar type for the strategy.
    trade_size : Decimal
        The base position size per trade.
    max_risk_per_trade : PositiveFloat, default 0.01
        Maximum risk per trade as fraction of account equity (1% = 0.01).
    max_daily_risk : PositiveFloat, default 0.05
        Maximum daily risk as fraction of account equity (5% = 0.05).
    max_drawdown_limit : PositiveFloat, default 0.15
        Maximum drawdown limit before strategy suspension (15% = 0.15).

    # Alligator Indicator Parameters
    jaw_period : PositiveInt, default 13
        The period for the Jaw moving average.
    jaw_shift : PositiveInt, default 8
        The shift for the Jaw moving average.
    teeth_period : PositiveInt, default 8
        The period for the Teeth moving average.
    teeth_shift : PositiveInt, default 5
        The shift for the Teeth moving average.
    lips_period : PositiveInt, default 5
        The period for the Lips moving average.
    lips_shift : PositiveInt, default 3
        The shift for the Lips moving average.

    # Additional Technical Indicators
    rsi_period : PositiveInt, default 14
        The period for RSI indicator.
    macd_fast_period : PositiveInt, default 12
        The fast period for MACD.
    macd_slow_period : PositiveInt, default 26
        The slow period for MACD.
    macd_signal_period : PositiveInt, default 9
        The signal period for MACD.
    bb_period : PositiveInt, default 20
        The period for Bollinger Bands.
    bb_std_dev : PositiveFloat, default 2.0
        The standard deviation for Bollinger Bands.
    stoch_k_period : PositiveInt, default 14
        The K period for Stochastic Oscillator.
    stoch_d_period : PositiveInt, default 3
        The D period for Stochastic Oscillator.

    # AI Configuration
    ollama_model : str, default "phi3:latest"
        The Ollama model to use for AI decisions.
    ollama_host : str, default "localhost"
        The Ollama server host.
    ollama_port : PositiveInt, default 11434
        The Ollama server port.
    ai_decision_threshold : PositiveFloat, default 0.7
        Minimum confidence threshold for AI decisions (0.0 to 1.0).

    # Risk Management
    enable_adaptive_position_sizing : bool, default True
        Whether to enable adaptive position sizing based on volatility.
    enable_correlation_filter : bool, default False
        Whether to enable correlation-based trade filtering.
    max_concurrent_positions : PositiveInt, default 3
        Maximum number of concurrent positions allowed.
    min_signal_strength : PositiveFloat, default 0.6
        Minimum signal strength required for trade execution.
    """

    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    max_risk_per_trade: PositiveFloat = 0.01  # 1%
    max_daily_risk: PositiveFloat = 0.05      # 5%
    max_drawdown_limit: PositiveFloat = 0.15  # 15%

    # Alligator parameters
    jaw_period: PositiveInt = 13
    jaw_shift: PositiveInt = 8
    teeth_period: PositiveInt = 8
    teeth_shift: PositiveInt = 5
    lips_period: PositiveInt = 5
    lips_shift: PositiveInt = 3

    # Additional indicators
    rsi_period: PositiveInt = 14
    macd_fast_period: PositiveInt = 12
    macd_slow_period: PositiveInt = 26
    macd_signal_period: PositiveInt = 9
    bb_period: PositiveInt = 20
    bb_std_dev: PositiveFloat = 2.0
    stoch_k_period: PositiveInt = 14
    stoch_d_period: PositiveInt = 3

    # AI configuration
    ollama_model: str = "phi3:latest"
    ollama_host: str = "localhost"
    ollama_port: PositiveInt = 11434
    ai_decision_threshold: PositiveFloat = 0.7

    # Risk management
    enable_adaptive_position_sizing: bool = True
    enable_correlation_filter: bool = False
    max_concurrent_positions: PositiveInt = 3
    min_signal_strength: PositiveFloat = 0.6


class EnhancedAlligatorStrategy(Strategy):
    """
    Enhanced Alligator Strategy combining multiple technical indicators,
    AI analysis, and comprehensive risk management.

    This strategy integrates:
    - Alligator indicator with advanced signal generation
    - Multiple technical indicators (RSI, MACD, Bollinger Bands, Stochastic)
    - AI-powered decision making via Ollama
    - Advanced risk management with portfolio-level controls
    - Performance tracking and continuous learning
    """

    def __init__(self, config: EnhancedAlligatorConfig) -> None:
        PyCondition.type(config, EnhancedAlligatorConfig, "config")
        super().__init__(config)

        # Configuration
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.base_trade_size = config.trade_size
        self.max_risk_per_trade = config.max_risk_per_trade
        self.max_daily_risk = config.max_daily_risk
        self.max_drawdown_limit = config.max_drawdown_limit

        # Initialize components
        self._initialize_indicators(config)
        self._initialize_ai_agent(config)
        self._initialize_risk_manager(config)
        self._initialize_analyzers(config)

        # State tracking
        self.current_signal_strength = 0.0
        self.last_ai_decision = "HOLD"
        self.consecutive_losses = 0
        self.daily_pnl = 0.0
        self.peak_equity = 0.0

        # Data storage for analysis
        self.price_history = []
        self.signal_history = []
        self.decision_history = []

        # Instrument reference
        self.instrument = None

        self.log.info("Enhanced Alligator Strategy initialized", color=LogColor.GREEN)

    def _initialize_indicators(self, config: EnhancedAlligatorConfig) -> None:
        """Initialize all technical indicators."""
        # Alligator components
        self.jaw_sma = SimpleMovingAverage(config.jaw_period)
        self.teeth_sma = SimpleMovingAverage(config.teeth_period)
        self.lips_sma = SimpleMovingAverage(config.lips_period)

        # Additional indicators
        self.rsi = RelativeStrengthIndex(config.rsi_period)
        self.macd = MovingAverageConvergenceDivergence(
            config.macd_fast_period,
            config.macd_slow_period,
            config.macd_signal_period
        )
        self.bollinger_bands = BollingerBands(config.bb_period, config.bb_std_dev)
        self.stochastic = StochasticOscillator(config.stoch_k_period, config.stoch_d_period)

        # Store shift parameters
        self.jaw_shift = config.jaw_shift
        self.teeth_shift = config.teeth_shift
        self.lips_shift = config.lips_shift

        # Shifted value storage
        self.jaw_values = []
        self.teeth_values = []
        self.lips_values = []

    def _initialize_ai_agent(self, config: EnhancedAlligatorConfig) -> None:
        """Initialize the Ollama AI agent."""
        self.ai_agent = OllamaAgent(
            model=config.ollama_model,
            host=config.ollama_host,
            port=config.ollama_port
        )
        self.ai_decision_threshold = config.ai_decision_threshold

    def _initialize_risk_manager(self, config: EnhancedAlligatorConfig) -> None:
        """Initialize the risk management system."""
        self.risk_manager = RiskManager(
            max_risk_per_trade=config.max_risk_per_trade,
            max_daily_risk=config.max_daily_risk,
            max_drawdown_limit=config.max_drawdown_limit,
            enable_adaptive_sizing=config.enable_adaptive_position_sizing,
            max_concurrent_positions=config.max_concurrent_positions
        )

    def _initialize_analyzers(self, config: EnhancedAlligatorConfig) -> None:
        """Initialize analysis components."""
        self.market_analyzer = MarketAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()

    def on_start(self) -> None:
        """Actions to be performed on strategy start."""
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument for {self.instrument_id}")
            self.stop()
            return

        # Register all indicators for bar updates
        indicators = [
            self.jaw_sma, self.teeth_sma, self.lips_sma,
            self.rsi, self.macd, self.bollinger_bands, self.stochastic
        ]

        for indicator in indicators:
            self.register_indicator_for_bars(self.bar_type, indicator)

        # Request historical data for indicator warm-up
        self.request_bars(self.bar_type, start=pd.Timestamp.utcnow() - pd.Timedelta(days=2))

        # Subscribe to real-time data
        self.subscribe_bars(self.bar_type)

        # Initialize peak equity tracking
        if hasattr(self.portfolio, 'account') and self.portfolio.account:
            self.peak_equity = float(self.portfolio.account.balance)

        self.log.info("Enhanced Alligator Strategy started successfully", color=LogColor.GREEN)

    def on_bar(self, bar: Bar) -> None:
        """Actions to be performed when the strategy receives a bar."""
        self.log.info(f"Processing bar: {bar}", LogColor.CYAN)

        # Update price history
        self.price_history.append(float(bar.close.as_double()))

        # Check if indicators are warmed up
        if not self._indicators_ready():
            self.log.info("Waiting for indicators to warm up...", color=LogColor.BLUE)
            return

        # Update all indicators
        self._update_indicators(bar)

        # Perform comprehensive analysis
        analysis = self._perform_market_analysis(bar)

        # Get AI decision
        ai_decision = self._get_ai_decision(analysis)

        # Apply risk management
        risk_adjusted_decision = self.risk_manager.evaluate_trade_decision(
            ai_decision, analysis, self.portfolio, self.instrument_id
        )

        # Execute trade if conditions are met
        if risk_adjusted_decision != "HOLD":
            self._execute_trade(risk_adjusted_decision, bar, analysis)

        # Update performance tracking
        self._update_performance_tracking()

    def _indicators_ready(self) -> bool:
        """Check if all indicators are ready for analysis."""
        return (
            self.jaw_sma.initialized and
            self.teeth_sma.initialized and
            self.lips_sma.initialized and
            self.rsi.initialized and
            self.macd.initialized and
            self.bollinger_bands.initialized and
            self.stochastic.initialized and
            len(self.price_history) >= max(
                self.config.jaw_period + self.config.jaw_shift,
                self.config.teeth_period + self.config.teeth_shift,
                self.config.lips_period + self.config.lips_shift,
                50  # Minimum history for reliable analysis
            )
        )

    def _update_indicators(self, bar: Bar) -> None:
        """Update all technical indicators with the latest bar data."""
        close_price = bar.close.as_double()

        # Update basic indicators
        self.jaw_sma.update_raw(close_price)
        self.teeth_sma.update_raw(close_price)
        self.lips_sma.update_raw(close_price)
        self.rsi.update_raw(close_price)
        self.macd.update_raw(close_price)
        self.bollinger_bands.update_raw(close_price)
        self.stochastic.update_raw(close_price, bar.high.as_double(), bar.low.as_double())

        # Maintain shifted values for Alligator
        self.jaw_values.append(self.jaw_sma.value)
        self.teeth_values.append(self.teeth_sma.value)
        self.lips_values.append(self.lips_sma.value)

        # Trim to maintain only necessary shift history
        max_shift = max(self.jaw_shift, self.teeth_shift, self.lips_shift)
        if len(self.jaw_values) > max_shift:
            self.jaw_values.pop(0)
        if len(self.teeth_values) > max_shift:
            self.teeth_values.pop(0)
        if len(self.lips_values) > max_shift:
            self.lips_values.pop(0)

    def _perform_market_analysis(self, bar: Bar) -> Dict[str, Any]:
        """Perform comprehensive market analysis using all indicators."""
        # Get current values
        current_price = bar.close.as_double()

        # Get shifted Alligator values
        jaw = self.jaw_values[-self.jaw_shift] if len(self.jaw_values) >= self.jaw_shift else 0.0
        teeth = self.teeth_values[-self.teeth_shift] if len(self.teeth_values) >= self.teeth_shift else 0.0
        lips = self.lips_values[-self.lips_shift] if len(self.lips_values) >= self.lips_shift else 0.0

        # Compile comprehensive analysis
        analysis = self.market_analyzer.analyze_market_conditions({
            'current_price': current_price,
            'jaw': jaw,
            'teeth': teeth,
            'lips': lips,
            'rsi': float(self.rsi.value),
            'macd_line': float(self.macd.value),
            'macd_signal': float(self.macd.signal),
            'macd_histogram': float(self.macd.histogram),
            'bb_upper': float(self.bollinger_bands.upper),
            'bb_middle': float(self.bollinger_bands.middle),
            'bb_lower': float(self.bollinger_bands.lower),
            'stoch_k': float(self.stochastic.k),
            'stoch_d': float(self.stochastic.d),
            'price_history': self.price_history[-50:],  # Last 50 prices for context
            'timestamp': bar.timestamp
        })

        return analysis

    def _get_ai_decision(self, analysis: Dict[str, Any]) -> str:
        """Get AI-powered trading decision."""
        try:
            # Get AI decision with comprehensive context
            decision = self.ai_agent.get_decision(analysis)

            # Validate decision confidence
            if hasattr(self.ai_agent, 'last_confidence'):
                confidence = self.ai_agent.last_confidence
                if confidence < self.ai_decision_threshold:
                    self.log.warning(f"AI confidence {confidence:.2f} below threshold {self.ai_decision_threshold}")
                    return "HOLD"

            self.last_ai_decision = decision
            return decision

        except Exception as e:
            self.log.error(f"AI decision error: {e}")
            return "HOLD"  # Default to safe action on error

    def _execute_trade(self, decision: str, bar: Bar, analysis: Dict[str, Any]) -> None:
        """Execute a trade with comprehensive risk management."""
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            analysis, self.portfolio, self.instrument_id, self.base_trade_size
        )

        if position_size <= 0:
            self.log.warning("Risk management prevented trade execution")
            return

        # Create order
        if decision == "OPEN_BUY" and self.portfolio.is_flat(self.instrument_id):
            self._open_buy_position(position_size, bar, analysis)
        elif decision == "OPEN_SELL" and self.portfolio.is_flat(self.instrument_id):
            self._open_sell_position(position_size, bar, analysis)
        elif decision == "CLOSE_POSITION":
            self._close_positions()

    def _open_buy_position(self, size: Decimal, bar: Bar, analysis: Dict[str, Any]) -> None:
        """Open a buy position with proper risk management."""
        try:
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.instrument.make_qty(size),
                time_in_force=TimeInForce.GTC,
            )

            self.submit_order(order)
            self.log.info(f"BUY order submitted: {size} units at {bar.close}", color=LogColor.GREEN)

        except Exception as e:
            self.log.error(f"Error opening buy position: {e}")

    def _open_sell_position(self, size: Decimal, bar: Bar, analysis: Dict[str, Any]) -> None:
        """Open a sell position with proper risk management."""
        try:
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=self.instrument.make_qty(size),
                time_in_force=TimeInForce.GTC,
            )

            self.submit_order(order)
            self.log.info(f"SELL order submitted: {size} units at {bar.close}", color=LogColor.RED)

        except Exception as e:
            self.log.error(f"Error opening sell position: {e}")

    def _close_positions(self) -> None:
        """Close all positions for this instrument."""
        try:
            self.close_all_positions(self.instrument_id)
            self.log.info("All positions closed", color=LogColor.YELLOW)
        except Exception as e:
            self.log.error(f"Error closing positions: {e}")

    def _update_performance_tracking(self) -> None:
        """Update performance tracking metrics."""
        # Update daily P&L
        if hasattr(self.portfolio, 'account') and self.portfolio.account:
            current_equity = float(self.portfolio.account.equity)
            if self.peak_equity == 0:
                self.peak_equity = current_equity
            else:
                # Check for drawdown
                drawdown = (self.peak_equity - current_equity) / self.peak_equity
                if drawdown > self.max_drawdown_limit:
                    self.log.error(f"Maximum drawdown limit reached: {drawdown:.2%}")
                    self.stop()

                # Update peak equity
                if current_equity > self.peak_equity:
                    self.peak_equity = current_equity

    def on_stop(self) -> None:
        """Actions to be performed when the strategy is stopped."""
        self.log.info("Enhanced Alligator Strategy stopping...")

        # Cancel all orders
        self.cancel_all_orders(self.instrument_id)

        # Close all positions
        self.close_all_positions(self.instrument_id)

        # Save final performance report
        if hasattr(self, 'performance_analyzer'):
            self.performance_analyzer.generate_final_report()

    def on_save(self) -> dict[str, bytes]:
        """Save strategy state."""
        state = {
            'price_history': self.price_history[-1000:],  # Keep last 1000 prices
            'signal_history': self.signal_history[-100:],  # Keep last 100 signals
            'decision_history': self.decision_history[-100:],  # Keep last 100 decisions
            'peak_equity': self.peak_equity,
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl': self.daily_pnl
        }
        return state

    def on_load(self, state: dict[str, bytes]) -> None:
        """Load strategy state."""
        if 'price_history' in state:
            self.price_history = state['price_history']
        if 'signal_history' in state:
            self.signal_history = state['signal_history']
        if 'decision_history' in state:
            self.decision_history = state['decision_history']
        if 'peak_equity' in state:
            self.peak_equity = state['peak_equity']
        if 'consecutive_losses' in state:
            self.consecutive_losses = state['consecutive_losses']
        if 'daily_pnl' in state:
            self.daily_pnl = state['daily_pnl']

    def on_dispose(self) -> None:
        """Cleanup resources."""
        self.log.info("Enhanced Alligator Strategy disposed")
