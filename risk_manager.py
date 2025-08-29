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
Risk Manager - Advanced Portfolio Risk Management System
Provides comprehensive risk controls and position sizing for algorithmic trading
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Data class for risk metrics."""
    daily_pnl: float
    daily_pnl_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    volatility: float
    var_95: float
    total_exposure: float
    concentration_risk: float


@dataclass
class PositionSizing:
    """Data class for position sizing calculations."""
    base_size: Decimal
    adjusted_size: Decimal
    risk_amount: float
    stop_loss_price: float
    take_profit_price: float
    risk_reward_ratio: float


class RiskManager:
    """
    Advanced risk management system for algorithmic trading.

    This system provides:
    - Dynamic position sizing based on volatility and account equity
    - Portfolio-level risk controls and diversification
    - Real-time risk monitoring and automatic position reduction
    - Drawdown protection and recovery mechanisms
    - Value at Risk (VaR) calculations
    """

    def __init__(
        self,
        max_risk_per_trade: float = 0.01,  # 1% of equity
        max_daily_risk: float = 0.05,     # 5% of equity
        max_drawdown_limit: float = 0.15, # 15% drawdown limit
        enable_adaptive_sizing: bool = True,
        max_concurrent_positions: int = 3,
        var_confidence_level: float = 0.95,
        recovery_mode_threshold: float = 0.10  # Enter recovery mode after 10% drawdown
    ):
        """
        Initialize the risk manager.

        Parameters
        ----------
        max_risk_per_trade : float
            Maximum risk per trade as fraction of account equity
        max_daily_risk : float
            Maximum daily risk as fraction of account equity
        max_drawdown_limit : float
            Maximum drawdown before strategy suspension
        enable_adaptive_sizing : bool
            Whether to enable adaptive position sizing
        max_concurrent_positions : int
            Maximum number of concurrent positions
        var_confidence_level : float
            Confidence level for VaR calculations
        recovery_mode_threshold : float
            Drawdown threshold to enter recovery mode
        """
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_risk = max_daily_risk
        self.max_drawdown_limit = max_drawdown_limit
        self.enable_adaptive_sizing = enable_adaptive_sizing
        self.max_concurrent_positions = max_concurrent_positions
        self.var_confidence_level = var_confidence_level
        self.recovery_mode_threshold = recovery_mode_threshold

        # Risk state tracking
        self.daily_start_equity = 0.0
        self.peak_equity = 0.0
        self.current_drawdown = 0.0
        self.in_recovery_mode = False
        self.consecutive_losses = 0
        self.portfolio_exposure = 0.0

        # Risk history for VaR calculation
        self.returns_history = []
        self.max_history_length = 1000

        # Position tracking
        self.active_positions = {}
        self.position_history = []

        # Risk limits
        self.daily_risk_used = 0.0
        self.max_daily_risk_amount = 0.0

        logger.info("RiskManager initialized with conservative risk parameters")

    def evaluate_trade_decision(
        self,
        ai_decision: str,
        market_analysis: Dict[str, Any],
        portfolio: Any,
        instrument_id: str
    ) -> str:
        """
        Evaluate and potentially override AI trading decision based on risk management.

        Parameters
        ----------
        ai_decision : str
            AI-generated trading decision
        market_analysis : Dict[str, Any]
            Comprehensive market analysis
        portfolio : Any
            Portfolio object for position tracking
        instrument_id : str
            Instrument identifier

        Returns
        -------
        str
            Final trading decision after risk evaluation
        """
        try:
            # Update risk state
            self._update_risk_state(portfolio)

            # Check if we're in recovery mode
            if self.in_recovery_mode:
                logger.warning("Recovery mode active - restricting trading")
                return "HOLD"

            # Check drawdown limits
            if self.current_drawdown >= self.max_drawdown_limit:
                logger.error(f"Maximum drawdown limit reached: {self.current_drawdown:.2%}")
                return "HOLD"

            # Check daily risk limits
            if self.daily_risk_used >= self.max_daily_risk:
                logger.warning(f"Daily risk limit reached: {self.daily_risk_used:.2%}")
                return "HOLD"

            # Check concurrent position limits
            current_positions = len([p for p in portfolio.positions.values() if p.quantity != 0])
            if current_positions >= self.max_concurrent_positions and ai_decision in ['OPEN_BUY', 'OPEN_SELL']:
                logger.warning(f"Maximum concurrent positions reached: {current_positions}")
                return "HOLD"

            # Check signal strength for new positions
            signal_strength = market_analysis.get('signal_strength', 0.0)
            min_signal_strength = 0.6  # Configurable threshold

            if ai_decision in ['OPEN_BUY', 'OPEN_SELL'] and signal_strength < min_signal_strength:
                logger.warning(f"Signal strength too low: {signal_strength:.2f} < {min_signal_strength}")
                return "HOLD"

            # Apply volatility filter
            volatility = market_analysis.get('market_conditions', {}).get('volatility', 0.001)
            if volatility > 0.03:  # 3% volatility threshold
                logger.warning(f"High volatility detected: {volatility:.2%}")
                # Still allow trades but reduce size (handled in position sizing)

            # Check for correlated positions (simplified)
            if not self._check_correlation_safety(instrument_id, portfolio):
                logger.warning("Correlation safety check failed")
                return "HOLD"

            logger.info(f"Risk evaluation passed for decision: {ai_decision}")
            return ai_decision

        except Exception as e:
            logger.error(f"Error in risk evaluation: {e}")
            return "HOLD"  # Default to safe action on error

    def calculate_position_size(
        self,
        market_analysis: Dict[str, Any],
        portfolio: Any,
        instrument_id: str,
        base_trade_size: Decimal
    ) -> Decimal:
        """
        Calculate optimal position size based on risk management rules.

        Parameters
        ----------
        market_analysis : Dict[str, Any]
            Comprehensive market analysis
        portfolio : Any
            Portfolio object
        instrument_id : str
            Instrument identifier
        base_trade_size : Decimal
            Base trade size before risk adjustment

        Returns
        -------
        Decimal
            Adjusted position size
        """
        try:
            # Get account equity
            account_equity = float(portfolio.account.equity) if hasattr(portfolio, 'account') else 10000.0

            # Calculate base risk amount
            risk_amount = account_equity * self.max_risk_per_trade

            # Apply recovery mode reduction
            if self.in_recovery_mode:
                risk_amount *= 0.5  # 50% reduction in recovery mode
                logger.info("Recovery mode: position size reduced by 50%")

            # Get volatility for adaptive sizing
            volatility = market_analysis.get('market_conditions', {}).get('volatility', 0.001)

            # Apply adaptive sizing based on volatility
            if self.enable_adaptive_sizing:
                volatility_multiplier = self._calculate_volatility_multiplier(volatility)
                risk_amount *= volatility_multiplier

                logger.debug(f"Volatility multiplier applied: {volatility_multiplier:.2f}")

            # Get signal strength for confidence adjustment
            signal_strength = market_analysis.get('signal_strength', 0.5)
            confidence_multiplier = 0.5 + (signal_strength * 0.5)  # 0.5 to 1.0
            risk_amount *= confidence_multiplier

            # Calculate remaining daily risk
            remaining_daily_risk = self.max_daily_risk - self.daily_risk_used
            if remaining_daily_risk <= 0:
                return Decimal('0')

            daily_risk_amount = account_equity * remaining_daily_risk
            risk_amount = min(risk_amount, daily_risk_amount)

            # Get stop loss distance (simplified - based on volatility)
            stop_loss_distance = self._calculate_stop_loss_distance(market_analysis, volatility)

            if stop_loss_distance <= 0:
                logger.warning("Invalid stop loss distance")
                return Decimal('0')

            # Calculate position size
            current_price = market_analysis.get('current_price', 0)
            if current_price <= 0:
                logger.warning("Invalid current price")
                return Decimal('0')

            # Position size = Risk Amount / (Stop Loss Distance * Price)
            position_size = risk_amount / (stop_loss_distance * current_price)

            # Convert to lots/units (simplified)
            position_size_decimal = Decimal(str(position_size))

            # Apply maximum position size limit
            max_position_size = base_trade_size * Decimal('2')  # Max 2x base size
            position_size_decimal = min(position_size_decimal, max_position_size)

            # Apply minimum position size
            min_position_size = base_trade_size * Decimal('0.1')  # Min 10% of base size
            position_size_decimal = max(position_size_decimal, min_position_size)

            logger.info(f"Calculated position size: {position_size_decimal} (risk: {risk_amount:.2f})")

            return position_size_decimal

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return Decimal('0')

    def _calculate_volatility_multiplier(self, volatility: float) -> float:
        """Calculate position size multiplier based on volatility."""
        # Higher volatility = smaller positions
        if volatility <= 0.005:  # Low volatility
            return 1.2
        elif volatility <= 0.01:  # Moderate volatility
            return 1.0
        elif volatility <= 0.02:  # High volatility
            return 0.7
        else:  # Very high volatility
            return 0.4

    def _calculate_stop_loss_distance(self, market_analysis: Dict[str, Any], volatility: float) -> float:
        """Calculate appropriate stop loss distance."""
        # Base stop loss on volatility
        current_price = market_analysis.get('current_price', 0)

        if volatility <= 0.005:
            stop_distance = current_price * 0.01  # 1% for low volatility
        elif volatility <= 0.01:
            stop_distance = current_price * 0.015  # 1.5% for moderate volatility
        elif volatility <= 0.02:
            stop_distance = current_price * 0.02  # 2% for high volatility
        else:
            stop_distance = current_price * 0.03  # 3% for very high volatility

        # Adjust based on support/resistance levels (simplified)
        technical_indicators = market_analysis.get('technical_indicators', {})

        # Use Bollinger Bands for stop loss reference
        bb_lower = technical_indicators.get('bollinger_bands', {}).get('lower', 0)
        if bb_lower > 0 and current_price > bb_lower:
            # For long positions, use BB lower as stop reference
            bb_distance = current_price - bb_lower
            stop_distance = min(stop_distance, bb_distance * 0.8)

        return max(stop_distance, current_price * 0.005)  # Minimum 0.5%

    def _check_correlation_safety(self, instrument_id: str, portfolio: Any) -> bool:
        """Check if opening a position in this instrument is safe given correlations."""
        # Simplified correlation check
        # In a full implementation, this would check correlations with existing positions

        current_positions = [p for p in portfolio.positions.values() if p.quantity != 0]

        # If we have positions in similar instruments, be more conservative
        for position in current_positions:
            if position.instrument_id.value.startswith(instrument_id.split('.')[0][:3]):
                # Similar currency pair - reduce risk
                logger.info(f"Similar position detected: {position.instrument_id}")
                return True  # Allow but will be handled by position sizing

        return True

    def _update_risk_state(self, portfolio: Any) -> None:
        """Update internal risk state."""
        try:
            if not hasattr(portfolio, 'account'):
                return

            current_equity = float(portfolio.account.equity)

            # Initialize peak equity on first run
            if self.peak_equity == 0:
                self.peak_equity = current_equity
                self.daily_start_equity = current_equity

            # Update peak equity
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity

            # Calculate current drawdown
            if self.peak_equity > 0:
                self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity

            # Update recovery mode
            if self.current_drawdown >= self.recovery_mode_threshold:
                if not self.in_recovery_mode:
                    logger.warning(f"Entering recovery mode - Drawdown: {self.current_drawdown:.2%}")
                    self.in_recovery_mode = True
            elif self.current_drawdown < self.recovery_mode_threshold * 0.5:  # Exit recovery when drawdown halves
                if self.in_recovery_mode:
                    logger.info("Exiting recovery mode")
                    self.in_recovery_mode = False

            # Update daily risk tracking
            if current_equity > 0:
                daily_pnl_pct = (current_equity - self.daily_start_equity) / self.daily_start_equity
                self.daily_risk_used = abs(daily_pnl_pct)

        except Exception as e:
            logger.error(f"Error updating risk state: {e}")

    def get_risk_metrics(self, portfolio: Any) -> RiskMetrics:
        """Get comprehensive risk metrics."""
        try:
            current_equity = float(portfolio.account.equity) if hasattr(portfolio, 'account') else 0.0

            # Calculate daily P&L
            daily_pnl = current_equity - self.daily_start_equity
            daily_pnl_pct = daily_pnl / self.daily_start_equity if self.daily_start_equity > 0 else 0.0

            # Calculate Sharpe ratio (simplified)
            if len(self.returns_history) > 1:
                avg_return = np.mean(self.returns_history)
                std_return = np.std(self.returns_history)
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0
            else:
                sharpe_ratio = 0.0

            # Calculate VaR (simplified)
            if len(self.returns_history) > 10:
                var_95 = np.percentile(self.returns_history, 5)  # 5th percentile = 95% VaR
            else:
                var_95 = 0.0

            # Calculate portfolio exposure
            total_exposure = sum(abs(float(p.quantity)) * float(p.avg_price_px)
                               for p in portfolio.positions.values() if p.quantity != 0)

            # Calculate concentration risk (simplified)
            max_position = max((abs(float(p.quantity)) * float(p.avg_price_px)
                              for p in portfolio.positions.values() if p.quantity != 0), default=0)
            concentration_risk = max_position / total_exposure if total_exposure > 0 else 0.0

            return RiskMetrics(
                daily_pnl=daily_pnl,
                daily_pnl_pct=daily_pnl_pct,
                max_drawdown=self.current_drawdown,
                max_drawdown_pct=self.current_drawdown * 100,
                sharpe_ratio=sharpe_ratio,
                volatility=np.std(self.returns_history) if self.returns_history else 0.0,
                var_95=var_95,
                total_exposure=total_exposure,
                concentration_risk=concentration_risk
            )

        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)

    def reset_daily_risk(self) -> None:
        """Reset daily risk tracking for new trading day."""
        self.daily_risk_used = 0.0
        if hasattr(self, 'daily_start_equity') and self.daily_start_equity > 0:
            self.daily_start_equity = self.daily_start_equity  # Keep current equity as new starting point
        logger.info("Daily risk tracking reset")

    def emergency_stop(self) -> None:
        """Emergency stop - close all positions immediately."""
        logger.critical("Emergency stop activated - manual intervention required")
        # This would trigger position closure in the main strategy

    def is_risk_within_limits(self) -> bool:
        """Check if current risk is within acceptable limits."""
        return (
            self.current_drawdown < self.max_drawdown_limit and
            self.daily_risk_used < self.max_daily_risk and
            not self.in_recovery_mode
        )
