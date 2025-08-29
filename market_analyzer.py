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
Market Analyzer - Technical Indicator Integration and Signal Analysis
Provides comprehensive market analysis combining multiple technical indicators
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """
    Comprehensive market analysis combining multiple technical indicators.

    This analyzer integrates Alligator, RSI, MACD, Bollinger Bands, and Stochastic
    indicators to provide unified market analysis and signal strength assessment.
    """

    def __init__(self):
        """Initialize the market analyzer."""
        # Signal weights for different indicators
        self.signal_weights = {
            'alligator': 0.25,
            'rsi': 0.20,
            'macd': 0.20,
            'bollinger_bands': 0.15,
            'stochastic': 0.20
        }

        logger.info("MarketAnalyzer initialized")

    def analyze_market_conditions(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive market analysis.

        Parameters
        ----------
        market_data : Dict[str, Any]
            Raw market data including prices and indicator values

        Returns
        -------
        Dict[str, Any]
            Comprehensive market analysis
        """
        try:
            # Extract current values
            current_price = market_data.get('current_price', 0)
            jaw = market_data.get('jaw', 0)
            teeth = market_data.get('teeth', 0)
            lips = market_data.get('lips', 0)
            rsi = market_data.get('rsi', 50)
            macd_line = market_data.get('macd_line', 0)
            macd_signal = market_data.get('macd_signal', 0)
            macd_histogram = market_data.get('macd_histogram', 0)
            bb_upper = market_data.get('bb_upper', current_price * 1.01)
            bb_middle = market_data.get('bb_middle', current_price)
            bb_lower = market_data.get('bb_lower', current_price * 0.99)
            stoch_k = market_data.get('stoch_k', 50)
            stoch_d = market_data.get('stoch_d', 50)
            price_history = market_data.get('price_history', [])
            timestamp = market_data.get('timestamp', datetime.now())

            # Perform individual indicator analyses
            alligator_analysis = self._analyze_alligator(current_price, jaw, teeth, lips)
            rsi_analysis = self._analyze_rsi(rsi)
            macd_analysis = self._analyze_macd(macd_line, macd_signal, macd_histogram)
            bb_analysis = self._analyze_bollinger_bands(current_price, bb_upper, bb_middle, bb_lower)
            stoch_analysis = self._analyze_stochastic(stoch_k, stoch_d)

            # Calculate signal strength
            signal_strength = self._calculate_signal_strength({
                'alligator': alligator_analysis,
                'rsi': rsi_analysis,
                'macd': macd_analysis,
                'bollinger_bands': bb_analysis,
                'stochastic': stoch_analysis
            })

            # Calculate volatility
            volatility = self._calculate_volatility(price_history)

            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(price_history)

            # Compile comprehensive analysis
            analysis = {
                'timestamp': timestamp,
                'current_price': current_price,
                'alligator': alligator_analysis,
                'technical_indicators': {
                    'rsi': rsi,
                    'macd': {
                        'line': macd_line,
                        'signal': macd_signal,
                        'histogram': macd_histogram
                    },
                    'bollinger_bands': {
                        'upper': bb_upper,
                        'middle': bb_middle,
                        'lower': bb_lower,
                        'position': bb_analysis['position']
                    },
                    'stochastic': {
                        'k': stoch_k,
                        'd': stoch_d,
                        'overbought': stoch_k > 80,
                        'oversold': stoch_k < 20
                    }
                },
                'market_conditions': {
                    'volatility': volatility,
                    'trend_strength': trend_strength,
                    'regime': self._determine_market_regime(price_history)
                },
                'signal_analysis': {
                    'overall_strength': signal_strength['overall_strength'],
                    'bullish_signals': signal_strength['bullish_signals'],
                    'bearish_signals': signal_strength['bearish_signals'],
                    'confidence_level': signal_strength['confidence_level'],
                    'signal_strength': signal_strength['overall_strength']  # Alias for compatibility
                },
                'individual_signals': {
                    'alligator': alligator_analysis,
                    'rsi': rsi_analysis,
                    'macd': macd_analysis,
                    'bollinger_bands': bb_analysis,
                    'stochastic': stoch_analysis
                }
            }

            logger.debug(f"Market analysis completed - Signal strength: {signal_strength['overall_strength']:.2f}")
            return analysis

        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return {
                'timestamp': datetime.now(),
                'current_price': market_data.get('current_price', 0),
                'error': str(e),
                'signal_strength': 0.0
            }

    def _analyze_alligator(self, current_price: float, jaw: float, teeth: float, lips: float) -> Dict[str, Any]:
        """Analyze Alligator indicator."""
        if jaw == 0 or teeth == 0 or lips == 0:
            return {
                'alignment': 'insufficient_data',
                'signal': 'neutral',
                'strength': 0.0
            }

        if current_price > lips > teeth > jaw:
            return {
                'alignment': 'bullish_ascending',
                'signal': 'buy',
                'strength': 1.0
            }
        elif current_price < lips < teeth < jaw:
            return {
                'alignment': 'bearish_descending',
                'signal': 'sell',
                'strength': 1.0
            }
        else:
            return {
                'alignment': 'mixed',
                'signal': 'neutral',
                'strength': 0.1
            }

    def _analyze_rsi(self, rsi: float) -> Dict[str, Any]:
        """Analyze RSI indicator."""
        if rsi >= 70:
            return {
                'signal': 'sell',
                'strength': min((rsi - 70) / 30, 1.0),
                'overbought': True,
                'oversold': False
            }
        elif rsi <= 30:
            return {
                'signal': 'buy',
                'strength': min((30 - rsi) / 30, 1.0),
                'overbought': False,
                'oversold': True
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0.5,
                'overbought': False,
                'oversold': False
            }

    def _analyze_macd(self, macd_line: float, macd_signal: float, macd_histogram: float) -> Dict[str, Any]:
        """Analyze MACD indicator."""
        if macd_histogram > 0.0005 and macd_line > macd_signal:
            return {
                'signal': 'buy',
                'strength': min(abs(macd_histogram) * 1000, 1.0),
                'momentum': 'bullish'
            }
        elif macd_histogram < -0.0005 and macd_line < macd_signal:
            return {
                'signal': 'sell',
                'strength': min(abs(macd_histogram) * 1000, 1.0),
                'momentum': 'bearish'
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0.1,
                'momentum': 'neutral'
            }

    def _analyze_bollinger_bands(self, current_price: float, upper: float, middle: float, lower: float) -> Dict[str, Any]:
        """Analyze Bollinger Bands."""
        band_range = upper - lower
        if band_range == 0:
            position_pct = 0.5
        else:
            position_pct = (current_price - lower) / band_range

        if position_pct > 0.9:
            return {
                'position': 'upper_extreme',
                'signal': 'sell',
                'strength': min((position_pct - 0.9) * 10, 1.0)
            }
        elif position_pct < 0.1:
            return {
                'position': 'lower_extreme',
                'signal': 'buy',
                'strength': min((0.1 - position_pct) * 10, 1.0)
            }
        else:
            return {
                'position': 'middle',
                'signal': 'neutral',
                'strength': 0.5
            }

    def _analyze_stochastic(self, k: float, d: float) -> Dict[str, Any]:
        """Analyze Stochastic Oscillator."""
        if k >= 80 and d >= 80:
            return {
                'signal': 'sell',
                'strength': min((k - 80) / 20, 1.0),
                'overbought': True,
                'oversold': False
            }
        elif k <= 20 and d <= 20:
            return {
                'signal': 'buy',
                'strength': min((20 - k) / 20, 1.0),
                'overbought': False,
                'oversold': True
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0.4,
                'overbought': False,
                'oversold': False
            }

    def _calculate_signal_strength(self, signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall signal strength from all indicators."""
        bullish_signals = 0
        bearish_signals = 0
        total_strength = 0.0
        total_signals = len(signals)

        for indicator_name, signal_data in signals.items():
            signal = signal_data.get('signal', 'neutral')
            strength = signal_data.get('strength', 0.0)
            weight = self.signal_weights.get(indicator_name, 0.2)

            if signal == 'buy':
                bullish_signals += 1
                total_strength += strength * weight
            elif signal == 'sell':
                bearish_signals += 1
                total_strength += strength * weight

        # Determine confidence level
        if total_strength >= 0.8:
            confidence_level = 'very_high'
        elif total_strength >= 0.6:
            confidence_level = 'high'
        elif total_strength >= 0.4:
            confidence_level = 'moderate'
        elif total_strength >= 0.2:
            confidence_level = 'low'
        else:
            confidence_level = 'very_low'

        return {
            'overall_strength': min(total_strength, 1.0),
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'confidence_level': confidence_level
        }

    def _calculate_volatility(self, price_history: List[float]) -> float:
        """Calculate price volatility."""
        if len(price_history) < 10:
            return 0.001

        returns = []
        for i in range(1, len(price_history)):
            ret = abs(price_history[i] - price_history[i-1]) / price_history[i-1]
            returns.append(ret)

        recent_returns = returns[-20:] if len(returns) > 20 else returns
        volatility = np.std(recent_returns) if recent_returns else 0.001

        return max(volatility, 0.0001)

    def _calculate_trend_strength(self, price_history: List[float]) -> float:
        """Calculate trend strength."""
        if len(price_history) < 10:
            return 0.0

        recent_prices = price_history[-20:] if len(price_history) > 20 else price_history
        x = np.arange(len(recent_prices))
        slope, _ = np.polyfit(x, recent_prices, 1)

        avg_price = np.mean(recent_prices)
        trend_strength = abs(slope) / (avg_price * 0.01)

        return min(trend_strength, 10.0)

    def _determine_market_regime(self, price_history: List[float]) -> str:
        """Determine market regime."""
        if len(price_history) < 20:
            return 'insufficient_data'

        returns = np.diff(price_history) / price_history[:-1]
        volatility = np.std(returns)

        if volatility > 0.02:
            return 'volatile'
        elif volatility < 0.005:
            return 'calm'
        else:
            return 'normal'
