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
Advanced Ollama AI Agent for Trading Decisions
Provides comprehensive market analysis and intelligent trading recommendations
"""

import logging
import time
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class OllamaAgent:
    """
    Advanced Ollama AI Agent with comprehensive market analysis capabilities.

    This agent integrates multiple technical indicators and market analysis
    to provide intelligent trading decisions with confidence scoring.
    """

    def __init__(
        self,
        model: str = "phi3:latest",
        host: str = "localhost",
        port: int = 11434,
        timeout: int = 30,
        max_retries: int = 3,
        confidence_threshold: float = 0.6
    ):
        """
        Initialize the Ollama AI agent.

        Parameters
        ----------
        model : str
            The Ollama model to use for analysis
        host : str
            Ollama server host
        port : int
            Ollama server port
        timeout : int
            Request timeout in seconds
        max_retries : int
            Maximum number of retry attempts
        confidence_threshold : float
            Minimum confidence threshold for decisions
        """
        self.model = model
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        self.confidence_threshold = confidence_threshold
        self.url = f"http://{host}:{port}/api/generate"

        # Decision tracking
        self.last_decision = "HOLD"
        self.last_confidence = 0.0
        self.decision_history = []
        self.confidence_history = []

        # Market context memory
        self.market_memory = []
        self.max_memory_size = 50

        # Performance tracking
        self.total_decisions = 0
        self.correct_decisions = 0
        self.accuracy_rate = 0.0

        logger.info(f"OllamaAgent initialized with model: {model}")

    def get_decision(self, analysis: Dict[str, Any]) -> str:
        """
        Get trading decision based on comprehensive market analysis.

        Parameters
        ----------
        analysis : Dict[str, Any]
            Comprehensive market analysis from MarketAnalyzer

        Returns
        -------
        str
            Trading decision: 'OPEN_BUY', 'OPEN_SELL', 'CLOSE_POSITION', or 'HOLD'
        """
        try:
            # Update market memory
            self._update_market_memory(analysis)

            # Generate comprehensive prompt
            prompt = self._generate_advanced_prompt(analysis)

            # Get AI response with retry logic
            response = self._get_ai_response(prompt)

            if not response:
                logger.warning("No response from AI agent, defaulting to HOLD")
                return "HOLD"

            # Parse and validate decision
            decision = self._parse_ai_decision(response)

            # Calculate confidence score
            confidence = self._calculate_confidence_score(response, analysis)

            # Store decision data
            self.last_decision = decision
            self.last_confidence = confidence
            self.decision_history.append(decision)
            self.confidence_history.append(confidence)

            # Maintain history size
            if len(self.decision_history) > 100:
                self.decision_history.pop(0)
                self.confidence_history.pop(0)

            logger.info(f"AI Decision: {decision} (confidence: {confidence:.2f})")

            return decision

        except Exception as e:
            logger.error(f"Error getting AI decision: {e}")
            return "HOLD"

    def _update_market_memory(self, analysis: Dict[str, Any]) -> None:
        """Update market memory for context awareness."""
        memory_entry = {
            'timestamp': analysis.get('timestamp', datetime.now()),
            'price': analysis.get('current_price', 0),
            'trend': analysis.get('trend_direction', 'neutral'),
            'volatility': analysis.get('volatility', 0),
            'signal_strength': analysis.get('signal_strength', 0)
        }

        self.market_memory.append(memory_entry)

        # Maintain memory size
        if len(self.market_memory) > self.max_memory_size:
            self.market_memory.pop(0)

    def _generate_advanced_prompt(self, analysis: Dict[str, Any]) -> str:
        """
        Generate comprehensive prompt for AI analysis.

        Parameters
        ----------
        analysis : Dict[str, Any]
            Market analysis data

        Returns
        -------
        str
            Formatted prompt for AI model
        """
        # Extract key metrics
        current_price = analysis.get('current_price', 0)
        alligator_data = analysis.get('alligator', {})
        technical_indicators = analysis.get('technical_indicators', {})
        market_conditions = analysis.get('market_conditions', {})

        # Format Alligator analysis
        jaw = alligator_data.get('jaw', 0)
        teeth = alligator_data.get('teeth', 0)
        lips = alligator_data.get('lips', 0)
        alignment = alligator_data.get('alignment', 'neutral')

        # Format technical indicators
        rsi = technical_indicators.get('rsi', 50)
        macd_data = technical_indicators.get('macd', {})
        bb_data = technical_indicators.get('bollinger_bands', {})
        stoch_data = technical_indicators.get('stochastic', {})

        # Format market conditions
        volatility = market_conditions.get('volatility', 0)
        trend_strength = market_conditions.get('trend_strength', 0)
        price_change_24h = market_conditions.get('price_change_24h', 0)

        # Get recent market context
        recent_trend = self._get_recent_trend_context()

        prompt = f"""You are an expert algorithmic trading AI specializing in forex markets. Analyze the following comprehensive market data and make an intelligent trading decision.

## CURRENT MARKET ANALYSIS

### Price & Alligator Indicator
- Current Price: {current_price:.5f}
- Alligator Jaw (13-period, 8-bar shift): {jaw:.5f}
- Alligator Teeth (8-period, 5-bar shift): {teeth:.5f}
- Alligator Lips (5-period, 3-bar shift): {lips:.5f}
- Alligator Alignment: {alignment}

### Technical Indicators
- RSI (14): {rsi:.2f}
- MACD Line: {macd_data.get('line', 0):.5f}
- MACD Signal: {macd_data.get('signal', 0):.5f}
- MACD Histogram: {macd_data.get('histogram', 0):.5f}
- Bollinger Bands:
  - Upper: {bb_data.get('upper', 0):.5f}
  - Middle: {bb_data.get('middle', 0):.5f}
  - Lower: {bb_data.get('lower', 0):.5f}
  - Position: {bb_data.get('position', 'within')}
- Stochastic Oscillator:
  - K: {stoch_data.get('k', 50):.2f}
  - D: {stoch_data.get('d', 50):.2f}
  - Overbought: {stoch_data.get('overbought', False)}
  - Oversold: {stoch_data.get('oversold', False)}

### Market Conditions
- Volatility (ATR): {volatility:.5f}
- Trend Strength: {trend_strength:.2f}%
- 24h Price Change: {price_change_24h:.2f}%
{recent_trend}

## DECISION FRAMEWORK

Consider these factors in your analysis:
1. **Alligator Signal Strength**: Bullish when price > lips > teeth > jaw, Bearish when price < lips < teeth < jaw
2. **Confluence**: Look for agreement between Alligator, RSI, MACD, and Bollinger Bands
3. **Momentum**: RSI overbought (>70) or oversold (<30) conditions
4. **Trend vs Range**: High volatility suggests trending market, low suggests ranging
5. **Risk Management**: Consider position sizing and stop loss placement

## RECENT MARKET CONTEXT
{recent_trend}

## TRADING DECISIONS

Choose ONE of these actions based on your analysis:

- **OPEN_BUY**: Strong bullish confluence with proper risk management
- **OPEN_SELL**: Strong bearish confluence with proper risk management
- **CLOSE_POSITION**: Exit current position due to changing conditions
- **HOLD**: No clear opportunity or wait for better setup

## RESPONSE FORMAT

Provide your decision in this exact format:
DECISION: [OPEN_BUY|OPEN_SELL|CLOSE_POSITION|HOLD]
CONFIDENCE: [0.0-1.0]
REASONING: [2-3 sentence explanation of your analysis]

Example:
DECISION: OPEN_BUY
CONFIDENCE: 0.85
REASONING: Strong bullish alignment in Alligator indicator with RSI oversold conditions and MACD positive momentum suggests excellent buying opportunity.
"""

        return prompt

    def _get_recent_trend_context(self) -> str:
        """Get recent market trend context from memory."""
        if len(self.market_memory) < 5:
            return "Insufficient market history for trend analysis."

        recent_prices = [entry['price'] for entry in self.market_memory[-10:]]
        if len(recent_prices) < 2:
            return "Limited price data available."

        # Calculate trend direction
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100

        # Calculate average volatility
        volatilities = [entry['volatility'] for entry in self.market_memory[-10:] if entry['volatility'] > 0]
        avg_volatility = np.mean(volatilities) if volatilities else 0

        trend_direction = "bullish" if price_change > 0.1 else "bearish" if price_change < -0.1 else "neutral"

        return f"- Recent Trend: {trend_direction} ({price_change:.2f}% over last {len(recent_prices)} periods)\n- Average Volatility: {avg_volatility:.5f}"

    def _get_ai_response(self, prompt: str) -> Optional[str]:
        """
        Get response from Ollama API with retry logic.

        Parameters
        ----------
        prompt : str
            The prompt to send to the AI model

        Returns
        -------
        Optional[str]
            AI response or None if failed
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.3,  # Lower temperature for more consistent decisions
            "top_p": 0.8,
            "max_tokens": 300
        }

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"AI Request attempt {attempt + 1}/{self.max_retries}")

                response = requests.post(
                    self.url,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get('response', '').strip()

                    if ai_response:
                        logger.debug(f"AI Response received ({len(ai_response)} chars)")
                        return ai_response
                    else:
                        logger.warning("Empty response from AI model")
                        continue
                else:
                    logger.warning(f"AI API error {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return None

            except requests.exceptions.Timeout:
                logger.warning(f"AI request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None

            except requests.exceptions.RequestException as e:
                logger.error(f"AI request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None

        logger.error("All AI request attempts failed")
        return None

    def _parse_ai_decision(self, response: str) -> str:
        """
        Parse AI response to extract trading decision.

        Parameters
        ----------
        response : str
            Raw AI response

        Returns
        -------
        str
            Parsed decision or 'HOLD' if parsing fails
        """
        try:
            # Look for decision in response
            lines = response.upper().split('\n')

            for line in lines:
                if 'DECISION:' in line:
                    # Extract decision after colon
                    decision_part = line.split('DECISION:')[1].strip()

                    # Clean up the decision
                    for valid_decision in ['OPEN_BUY', 'OPEN_SELL', 'CLOSE_POSITION', 'HOLD']:
                        if valid_decision in decision_part:
                            return valid_decision

            # Fallback: look for decision keywords anywhere in response
            response_upper = response.upper()
            if 'OPEN_BUY' in response_upper or 'BUY SIGNAL' in response_upper or 'LONG POSITION' in response_upper:
                return 'OPEN_BUY'
            elif 'OPEN_SELL' in response_upper or 'SELL SIGNAL' in response_upper or 'SHORT POSITION' in response_upper:
                return 'OPEN_SELL'
            elif 'CLOSE_POSITION' in response_upper or 'EXIT POSITION' in response_upper or 'CLOSE TRADE' in response_upper:
                return 'CLOSE_POSITION'
            elif 'HOLD' in response_upper or 'WAIT' in response_upper or 'NO ACTION' in response_upper:
                return 'HOLD'

            logger.warning(f"Could not parse decision from response: {response[:200]}...")
            return 'HOLD'

        except Exception as e:
            logger.error(f"Error parsing AI decision: {e}")
            return 'HOLD'

    def _calculate_confidence_score(self, response: str, analysis: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the AI decision.

        Parameters
        ----------
        response : str
            AI response text
        analysis : Dict[str, Any]
            Market analysis data

        Returns
        -------
        float
            Confidence score between 0.0 and 1.0
        """
        try:
            confidence = 0.5  # Base confidence

            # Extract confidence from response if present
            lines = response.split('\n')
            for line in lines:
                if 'CONFIDENCE:' in line.lower():
                    try:
                        conf_value = float(line.split(':')[1].strip())
                        if 0.0 <= conf_value <= 1.0:
                            confidence = conf_value
                            break
                    except (ValueError, IndexError):
                        pass

            # Adjust confidence based on market conditions
            signal_strength = analysis.get('signal_strength', 0.5)
            volatility = analysis.get('market_conditions', {}).get('volatility', 0.001)

            # Higher signal strength increases confidence
            confidence += signal_strength * 0.2

            # Moderate volatility increases confidence
            if 0.0005 <= volatility <= 0.005:
                confidence += 0.1
            elif volatility > 0.01:  # Too volatile
                confidence -= 0.2

            # Ensure confidence is within bounds
            confidence = max(0.0, min(1.0, confidence))

            return confidence

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the AI agent."""
        total_decisions = len(self.decision_history)

        if total_decisions == 0:
            return {
                'total_decisions': 0,
                'average_confidence': 0.0,
                'decision_distribution': {},
                'performance_score': 0.0
            }

        # Calculate decision distribution
        decision_counts = {}
        for decision in self.decision_history:
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

        # Calculate average confidence
        avg_confidence = np.mean(self.confidence_history) if self.confidence_history else 0.0

        # Calculate performance score (based on confidence and decision variety)
        confidence_weight = avg_confidence
        diversity_weight = len(decision_counts) / 4.0  # Max 4 decision types
        performance_score = (confidence_weight * 0.7) + (diversity_weight * 0.3)

        return {
            'total_decisions': total_decisions,
            'average_confidence': avg_confidence,
            'decision_distribution': decision_counts,
            'performance_score': performance_score,
            'recent_decisions': self.decision_history[-10:],  # Last 10 decisions
            'recent_confidence': self.confidence_history[-10:]  # Last 10 confidence scores
        }

    def reset_memory(self) -> None:
        """Reset the agent's memory and history."""
        self.market_memory.clear()
        self.decision_history.clear()
        self.confidence_history.clear()
        self.last_decision = "HOLD"
        self.last_confidence = 0.0
        logger.info("AI agent memory reset")

    def is_ready(self) -> bool:
        """
        Check if the AI agent is ready for operation.

        Returns
        -------
        bool
            True if agent is ready, False otherwise
        """
        try:
            # Test connection to Ollama
            test_payload = {
                "model": self.model,
                "prompt": "test",
                "stream": False,
                "max_tokens": 10
            }

            response = requests.post(self.url, json=test_payload, timeout=5)
            return response.status_code == 200

        except Exception:
            return False
