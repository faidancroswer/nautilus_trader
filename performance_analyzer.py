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
Performance Analyzer - Comprehensive Trading Performance Analysis
Provides detailed performance metrics and continuous learning insights
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import os
import pandas as pd
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """Data class for individual trade records."""
    timestamp: datetime
    instrument: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    duration: timedelta
    signal_strength: float
    market_condition: str
    ai_confidence: float
    risk_amount: float


@dataclass
class PerformanceMetrics:
    """Data class for comprehensive performance metrics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    total_pnl: float
    total_pnl_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    recovery_factor: float
    profit_factor: float
    expectancy: float
    avg_trade_duration: timedelta
    calmar_ratio: float
    information_ratio: float


class PerformanceAnalyzer:
    """
    Comprehensive performance analysis system for algorithmic trading.

    This analyzer provides:
    - Detailed trade-by-trade performance metrics
    - Risk-adjusted return calculations
    - Market condition analysis
    - AI performance evaluation
    - Continuous learning insights
    - Automated reporting and visualization
    """

    def __init__(self, output_dir: str = "performance_reports"):
        """
        Initialize the performance analyzer.

        Parameters
        ----------
        output_dir : str
            Directory to save performance reports and data
        """
        self.output_dir = output_dir
        self.trade_records: List[TradeRecord] = []
        self.daily_pnl: Dict[str, float] = {}
        self.market_condition_performance: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"PerformanceAnalyzer initialized - reports will be saved to {output_dir}")

    def record_trade(
        self,
        timestamp: datetime,
        instrument: str,
        side: str,
        quantity: float,
        entry_price: float,
        exit_price: float,
        signal_strength: float = 0.0,
        market_condition: str = "unknown",
        ai_confidence: float = 0.0,
        risk_amount: float = 0.0
    ) -> None:
        """
        Record a completed trade for analysis.

        Parameters
        ----------
        timestamp : datetime
            Trade completion timestamp
        instrument : str
            Trading instrument
        side : str
            Trade side ('BUY' or 'SELL')
        quantity : float
            Trade quantity
        entry_price : float
            Entry price
        exit_price : float
            Exit price
        signal_strength : float
            Signal strength at trade entry
        market_condition : str
            Market condition when trade was executed
        ai_confidence : float
            AI confidence level at trade entry
        risk_amount : float
            Risk amount for the trade
        """
        try:
            # Calculate P&L
            if side == 'BUY':
                pnl = (exit_price - entry_price) * quantity
            else:  # SELL
                pnl = (entry_price - exit_price) * quantity

            pnl_pct = (pnl / (entry_price * quantity)) * 100

            # Create trade record
            trade = TradeRecord(
                timestamp=timestamp,
                instrument=instrument,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl=pnl,
                pnl_pct=pnl_pct,
                duration=timedelta(0),  # Would need entry timestamp to calculate
                signal_strength=signal_strength,
                market_condition=market_condition,
                ai_confidence=ai_confidence,
                risk_amount=risk_amount
            )

            self.trade_records.append(trade)

            # Update daily P&L
            date_key = timestamp.strftime('%Y-%m-%d')
            if date_key not in self.daily_pnl:
                self.daily_pnl[date_key] = 0.0
            self.daily_pnl[date_key] += pnl

            # Update market condition performance
            if market_condition not in self.market_condition_performance:
                self.market_condition_performance[market_condition] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'total_pnl': 0.0,
                    'win_rate': 0.0
                }

            perf = self.market_condition_performance[market_condition]
            perf['total_trades'] += 1
            perf['total_pnl'] += pnl
            if pnl > 0:
                perf['winning_trades'] += 1
            perf['win_rate'] = perf['winning_trades'] / perf['total_trades']

            logger.debug(f"Trade recorded: {instrument} {side} {quantity} @ {entry_price:.5f} -> {exit_price:.5f} (P&L: {pnl:.2f})")

        except Exception as e:
            logger.error(f"Error recording trade: {e}")

    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.

        Returns
        -------
        PerformanceMetrics
            Complete set of performance metrics
        """
        try:
            if not self.trade_records:
                return PerformanceMetrics(
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    avg_win=0.0,
                    avg_loss=0.0,
                    largest_win=0.0,
                    largest_loss=0.0,
                    total_pnl=0.0,
                    total_pnl_pct=0.0,
                    sharpe_ratio=0.0,
                    sortino_ratio=0.0,
                    max_drawdown=0.0,
                    max_drawdown_pct=0.0,
                    recovery_factor=0.0,
                    profit_factor=0.0,
                    expectancy=0.0,
                    avg_trade_duration=timedelta(0),
                    calmar_ratio=0.0,
                    information_ratio=0.0
                )

            # Basic trade counts
            total_trades = len(self.trade_records)
            winning_trades = sum(1 for trade in self.trade_records if trade.pnl > 0)
            losing_trades = total_trades - winning_trades
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

            # P&L calculations
            winning_pnl = [trade.pnl for trade in self.trade_records if trade.pnl > 0]
            losing_pnl = [trade.pnl for trade in self.trade_records if trade.pnl < 0]

            avg_win = np.mean(winning_pnl) if winning_pnl else 0.0
            avg_loss = np.mean(losing_pnl) if losing_pnl else 0.0
            largest_win = max(winning_pnl) if winning_pnl else 0.0
            largest_loss = min(losing_pnl) if losing_pnl else 0.0

            total_pnl = sum(trade.pnl for trade in self.trade_records)
            total_pnl_pct = (total_pnl / sum(trade.entry_price * trade.quantity for trade in self.trade_records)) * 100

            # Calculate drawdown
            max_drawdown, max_drawdown_pct, recovery_factor = self._calculate_drawdown_metrics()

            # Calculate Sharpe and Sortino ratios
            sharpe_ratio, sortino_ratio = self._calculate_risk_adjusted_returns()

            # Calculate profit factor
            total_win_pnl = sum(winning_pnl)
            total_loss_pnl = abs(sum(losing_pnl))
            profit_factor = total_win_pnl / total_loss_pnl if total_loss_pnl > 0 else float('inf')

            # Calculate expectancy
            expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))

            # Calculate average trade duration
            durations = [trade.duration for trade in self.trade_records if trade.duration.total_seconds() > 0]
            avg_trade_duration = np.mean(durations) if durations else timedelta(0)

            # Calculate Calmar ratio
            annualized_return = total_pnl_pct * (365 / max(len(self.daily_pnl), 1))
            calmar_ratio = annualized_return / max_drawdown_pct if max_drawdown_pct > 0 else 0.0

            # Calculate Information ratio (simplified)
            daily_returns = list(self.daily_pnl.values())
            if len(daily_returns) > 1:
                avg_daily_return = np.mean(daily_returns)
                tracking_error = np.std(daily_returns)
                information_ratio = avg_daily_return / tracking_error if tracking_error > 0 else 0.0
            else:
                information_ratio = 0.0

            return PerformanceMetrics(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                largest_win=largest_win,
                largest_loss=largest_loss,
                total_pnl=total_pnl,
                total_pnl_pct=total_pnl_pct,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                max_drawdown_pct=max_drawdown_pct,
                recovery_factor=recovery_factor,
                profit_factor=profit_factor,
                expectancy=expectancy,
                avg_trade_duration=avg_trade_duration,
                calmar_ratio=calmar_ratio,
                information_ratio=information_ratio
            )

        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return PerformanceMetrics(
                total_trades=len(self.trade_records),
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                total_pnl=0.0,
                total_pnl_pct=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
                recovery_factor=0.0,
                profit_factor=0.0,
                expectancy=0.0,
                avg_trade_duration=timedelta(0),
                calmar_ratio=0.0,
                information_ratio=0.0
            )

    def _calculate_drawdown_metrics(self) -> Tuple[float, float, float]:
        """Calculate drawdown-related metrics."""
        try:
            if not self.daily_pnl:
                return 0.0, 0.0, 0.0

            # Calculate cumulative P&L
            dates = sorted(self.daily_pnl.keys())
            cumulative_pnl = 0.0
            peak = 0.0
            max_drawdown = 0.0
            max_drawdown_pct = 0.0

            for date in dates:
                cumulative_pnl += self.daily_pnl[date]
                if cumulative_pnl > peak:
                    peak = cumulative_pnl

                drawdown = peak - cumulative_pnl
                drawdown_pct = (drawdown / peak) * 100 if peak > 0 else 0.0

                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_pct = drawdown_pct

            # Calculate recovery factor
            recovery_factor = abs(cumulative_pnl) / max_drawdown if max_drawdown > 0 else float('inf')

            return max_drawdown, max_drawdown_pct, recovery_factor

        except Exception as e:
            logger.error(f"Error calculating drawdown metrics: {e}")
            return 0.0, 0.0, 0.0

    def _calculate_risk_adjusted_returns(self) -> Tuple[float, float]:
        """Calculate Sharpe and Sortino ratios."""
        try:
            if not self.daily_pnl:
                return 0.0, 0.0

            daily_returns = list(self.daily_pnl.values())
            if len(daily_returns) < 2:
                return 0.0, 0.0

            # Calculate Sharpe ratio
            avg_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0

            # Calculate Sortino ratio (downside deviation)
            negative_returns = [r for r in daily_returns if r < 0]
            downside_deviation = np.std(negative_returns) if negative_returns else 0.0
            sortino_ratio = avg_return / downside_deviation if downside_deviation > 0 else 0.0

            return sharpe_ratio, sortino_ratio

        except Exception as e:
            logger.error(f"Error calculating risk-adjusted returns: {e}")
            return 0.0, 0.0

    def generate_performance_report(self, filename: Optional[str] = None) -> str:
        """
        Generate a comprehensive performance report.

        Parameters
        ----------
        filename : Optional[str]
            Custom filename for the report (auto-generated if None)

        Returns
        -------
        str
            Path to the generated report file
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"performance_report_{timestamp}.json"

            filepath = os.path.join(self.output_dir, filename)

            # Calculate metrics
            metrics = self.calculate_performance_metrics()

            # Create report data
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'total_trades': metrics.total_trades,
                    'win_rate': metrics.win_rate,
                    'total_pnl': metrics.total_pnl,
                    'total_pnl_pct': metrics.total_pnl_pct,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'max_drawdown_pct': metrics.max_drawdown_pct,
                    'profit_factor': metrics.profit_factor,
                    'expectancy': metrics.expectancy
                },
                'detailed_metrics': {
                    'winning_trades': metrics.winning_trades,
                    'losing_trades': metrics.losing_trades,
                    'avg_win': metrics.avg_win,
                    'avg_loss': metrics.avg_loss,
                    'largest_win': metrics.largest_win,
                    'largest_loss': metrics.largest_loss,
                    'sortino_ratio': metrics.sortino_ratio,
                    'recovery_factor': metrics.recovery_factor,
                    'calmar_ratio': metrics.calmar_ratio,
                    'information_ratio': metrics.information_ratio,
                    'avg_trade_duration_seconds': metrics.avg_trade_duration.total_seconds()
                },
                'market_condition_performance': dict(self.market_condition_performance),
                'daily_pnl': self.daily_pnl,
                'recent_trades': [
                    {
                        'timestamp': trade.timestamp.isoformat(),
                        'instrument': trade.instrument,
                        'side': trade.side,
                        'pnl': trade.pnl,
                        'pnl_pct': trade.pnl_pct,
                        'signal_strength': trade.signal_strength,
                        'ai_confidence': trade.ai_confidence
                    }
                    for trade in self.trade_records[-10:]  # Last 10 trades
                ]
            }

            # Save report
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)

            logger.info(f"Performance report generated: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return ""

    def generate_final_report(self) -> None:
        """Generate a final performance report when strategy stops."""
        try:
            self.generate_performance_report("final_performance_report.json")

            # Generate summary statistics
            metrics = self.calculate_performance_metrics()

            logger.info("=" * 60)
            logger.info("FINAL PERFORMANCE REPORT")
            logger.info("=" * 60)
            logger.info(f"Total Trades: {metrics.total_trades}")
            logger.info(".1%")
            logger.info(".2f")
            logger.info(".2f")
            logger.info(".2f")
            logger.info(".3f")
            logger.info(".2f")
            logger.info(".4f")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error generating final report: {e}")

    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Generate insights for continuous learning and strategy optimization.

        Returns
        -------
        Dict[str, Any]
            Learning insights and recommendations
        """
        try:
            if not self.trade_records:
                return {'insights': [], 'recommendations': []}

            insights = []
            recommendations = []

            metrics = self.calculate_performance_metrics()

            # Analyze win rate by market condition
            best_market_condition = max(
                self.market_condition_performance.keys(),
                key=lambda x: self.market_condition_performance[x]['win_rate']
            )

            insights.append(f"Best performance in {best_market_condition} market conditions")

            # Analyze signal strength correlation
            strong_signals = [t for t in self.trade_records if t.signal_strength > 0.8]
            weak_signals = [t for t in self.trade_records if t.signal_strength < 0.4]

            if strong_signals and weak_signals:
                strong_win_rate = sum(1 for t in strong_signals if t.pnl > 0) / len(strong_signals)
                weak_win_rate = sum(1 for t in weak_signals if t.pnl > 0) / len(weak_signals)

                if strong_win_rate > weak_win_rate + 0.1:
                    insights.append(".1%")
                    recommendations.append("Consider tightening entry criteria to focus on high-confidence signals")

            # Analyze AI confidence correlation
            high_confidence = [t for t in self.trade_records if t.ai_confidence > 0.8]
            low_confidence = [t for t in self.trade_records if t.ai_confidence < 0.4]

            if high_confidence and low_confidence:
                high_win_rate = sum(1 for t in high_confidence if t.pnl > 0) / len(high_confidence)
                low_win_rate = sum(1 for t in low_confidence if t.pnl > 0) / len(low_confidence)

                if high_win_rate > low_win_rate + 0.1:
                    insights.append(".1%")
                    recommendations.append("AI confidence threshold could be increased for better performance")

            # Analyze trade timing
            if metrics.avg_trade_duration > timedelta(hours=4):
                insights.append("Trades are held longer than optimal")
                recommendations.append("Consider reducing holding time to capture quicker moves")

            # Analyze risk-adjusted performance
            if metrics.sharpe_ratio < 1.0:
                insights.append("Risk-adjusted returns could be improved")
                recommendations.append("Consider reducing position sizes or improving entry timing")

            return {
                'insights': insights,
                'recommendations': recommendations,
                'best_market_condition': best_market_condition,
                'performance_score': self._calculate_performance_score(metrics)
            }

        except Exception as e:
            logger.error(f"Error generating learning insights: {e}")
            return {'insights': [], 'recommendations': []}

    def _calculate_performance_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate an overall performance score (0-100)."""
        try:
            score = 0.0

            # Win rate contribution (40% weight)
            score += metrics.win_rate * 40

            # Profit factor contribution (30% weight)
            profit_factor_score = min(metrics.profit_factor / 2, 1.0) * 30
            score += profit_factor_score

            # Sharpe ratio contribution (20% weight)
            sharpe_score = min(metrics.sharpe_ratio / 2, 1.0) * 20
            score += sharpe_score

            # Drawdown penalty (10% weight)
            drawdown_penalty = max(0, (10 - metrics.max_drawdown_pct) / 10) * 10
            score += drawdown_penalty

            return min(score, 100.0)

        except Exception:
            return 0.0

    def reset(self) -> None:
        """Reset all performance data."""
        self.trade_records.clear()
        self.daily_pnl.clear()
        self.market_condition_performance.clear()
        logger.info("Performance analyzer data reset")
