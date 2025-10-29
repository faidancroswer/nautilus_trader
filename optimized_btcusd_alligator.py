#!/usr/bin/env python3
"""
Optimized AI Alligator Trading Strategy for BTCUSD
High-performance implementation with advanced optimizations
"""

import logging
import time
import sys
import json
import requests
import asyncio
import aiohttp
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor
import gc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [BTCUSD] - %(message)s',
    handlers=[
        logging.FileHandler('btcusd_alligator_optimized.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class BTCUSDConfig:
    """Optimized configuration for BTCUSD trading"""
    # Alligator parameters optimized for crypto volatility
    jaw_period: int = 21  # Increased for crypto trends
    jaw_shift: int = 13
    teeth_period: int = 13
    teeth_shift: int = 8
    lips_period: int = 8
    lips_shift: int = 5

    # Risk management for BTC
    lot_size: float = 0.01
    max_risk_percent: float = 0.5  # Conservative for crypto
    sl_points: int = 1000  # Higher for BTC volatility
    tp_points: int = 2000
    max_positions: int = 1
    volatility_threshold: float = 0.02  # 2% volatility threshold

    # Performance settings
    cache_duration: int = 30
    ai_timeout: int = 15
    max_retries: int = 2
    concurrent_requests: bool = True
    data_buffer_size: int = 200  # Keep more data for calculations

    # BTC-specific parameters
    btc_volatility_multiplier: float = 3.0
    btc_trend_confirmation_periods: int = 3
    btc_min_profit_pips: int = 500


class PerformanceOptimizer:
    """Performance optimization utilities"""

    @staticmethod
    @lru_cache(maxsize=128)
    def cached_sma(data_tuple: tuple, period: int) -> tuple:
        """Cached SMA calculation for performance"""
        data = np.array(data_tuple)
        if len(data) < period:
            return tuple(np.full(len(data), np.nan))

        sma = np.convolve(data, np.ones(period)/period, mode='valid')
        result = np.full(len(data), np.nan)
        result[period-1:] = sma
        return tuple(result)

    @staticmethod
    def calculate_atr_vectorized(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Vectorized ATR calculation for performance"""
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = np.mean(tr[-period:]) if len(tr) >= period else np.mean(tr)
        return float(atr)

    @staticmethod
    def calculate_rsi_vectorized(prices: np.ndarray, period: int = 14) -> float:
        """Vectorized RSI calculation"""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)

    @staticmethod
    def cleanup_memory():
        """Memory cleanup for performance"""
        gc.collect()


class OptimizedOllamaAgent:
    """High-performance Ollama AI Agent with optimizations"""

    def __init__(self, model: str = "phi3:latest", host: str = "localhost", port: int = 11434):
        self.model = model
        self.url = f"http://{host}:{port}/api/generate"
        self.timeout = BTCUSDConfig.ai_timeout
        self.max_retries = BTCUSDConfig.max_retries

        # Performance optimizations
        self.decision_cache = {}
        self.cache_timestamps = {}
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

        # Connection pooling for faster requests
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=2
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # Pre-computed prompts for speed
        self.prompt_templates = self._load_prompt_templates()

        # Test connection on initialization
        self._warm_up_connection()

    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load optimized prompt templates"""
        return {
            "btc_analysis": """
BTCUSD TRADING ANALYSIS - {signal_type}
Price: ${price:.2f} | Change: {change_24h:.2f}%
Volatility: {volatility:.3f} | ATR: {atr:.2f}

ALLIGATOR:
Jaw: {jaw:.2f} | Teeth: {teeth:.2f} | Lips: {lips:.2f}
Alignment: {alignment}

TECHNICAL:
RSI: {rsi:.1f} | Momentum: {momentum:.3f}
Support: {support:.2f} | Resistance: {resistance:.2f}

BTC-SPECIFIC:
Trend Strength: {trend_strength:.3f}
Volume Confirmation: {volume_confirmed}

RISK: Account Equity: ${equity:.2f} | Risk %: {risk_percent:.1f}

DECISION RULES:
1. STRONG_BULL: price>lips>teeth>jaw + RSI<70 + momentum>0 → OPEN_BUY
2. STRONG_BEAR: price<lips<teeth<jaw + RSI>30 + momentum<0 → OPEN_SELL
3. EXIT: signal reversal + RSI extreme → CLOSE_POSITION
4. UNCERTAIN: weak signals or high volatility → HOLD

RESPOND ONLY: OPEN_BUY, OPEN_SELL, CLOSE_POSITION, or HOLD
""",
            "fast_decision": """
BTC: ${price:.2f} | {alignment} | RSI:{rsi:.0f} | Vol:{volatility:.3f}
Signal: {signal_summary}
Decision: """
        }

    def _warm_up_connection(self):
        """Warm up Ollama connection for faster responses"""
        try:
            payload = {
                "model": self.model,
                "prompt": "Ready",
                "stream": False,
                "temperature": 0.1,
                "max_tokens": 5
            }
            self.session.post(self.url, json=payload, timeout=5)
            logger.info("Ollama connection warmed up")
        except Exception as e:
            logger.warning(f"Failed to warm up Ollama: {e}")

    def _get_cache_key(self, price: float, alignment: str, rsi: float) -> str:
        """Generate optimized cache key"""
        price_bucket = round(price, 2)
        rsi_bucket = round(rsi, 0)
        return f"{price_bucket}_{alignment}_{rsi_bucket}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.cache_timestamps:
            return False
        age = time.time() - self.cache_timestamps[cache_key]
        return age < BTCUSDConfig.cache_duration

    def get_btc_decision(self, market_data: Dict[str, Any]) -> str:
        """Get optimized trading decision for BTCUSD"""
        try:
            # Generate cache key
            cache_key = self._get_cache_key(
                market_data['current_price'],
                market_data['alligator']['alignment'],
                market_data['technical_indicators']['rsi']
            )

            # Check cache first
            if cache_key in self.decision_cache and self._is_cache_valid(cache_key):
                cached_decision = self.decision_cache[cache_key]
                logger.debug(f"Using cached decision: {cached_decision}")
                return cached_decision

            # Generate optimized prompt
            prompt = self._generate_btc_prompt(market_data)

            # Optimized payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2,  # Lower for consistency
                "top_p": 0.9,
                "max_tokens": 50,  # Reduced for speed
                "repeat_penalty": 1.1
            }

            # Make request with retry logic
            decision = self._make_request_with_retry(payload)

            # Cache valid decisions
            if decision != "HOLD":
                self.decision_cache[cache_key] = decision
                self.cache_timestamps[cache_key] = time.time()

                # Clean old cache entries
                if len(self.decision_cache) > 20:
                    oldest_key = min(self.cache_timestamps.keys(),
                                   key=lambda k: self.cache_timestamps[k])
                    del self.decision_cache[oldest_key]
                    del self.cache_timestamps[oldest_key]

            return decision

        except Exception as e:
            logger.error(f"Error getting BTC decision: {e}")
            return "HOLD"

    def _generate_btc_prompt(self, data: Dict[str, Any]) -> str:
        """Generate optimized BTC-specific prompt"""
        # Extract relevant data
        current_price = data['current_price']
        alligator = data['alligator']
        tech = data['technical_indicators']
        market = data['market_conditions']

        # Determine signal summary
        signal_summary = "BULLISH" if alligator['alignment'] == 'bullish' else \
                        "BEARISH" if alligator['alignment'] == 'bearish' else "NEUTRAL"

        # Use fast template for quick decisions
        if market['volatility'] < BTCUSDConfig.volatility_threshold:
            return self.prompt_templates["fast_decision"].format(
                price=current_price,
                alignment=alligator['alignment'].upper(),
                rsi=tech['rsi'],
                volatility=market['volatility'],
                signal_summary=signal_summary
            )
        else:
            # Use detailed template for high volatility
            return self.prompt_templates["btc_analysis"].format(
                signal_type=signal_summary,
                price=current_price,
                change_24h=market.get('price_change_24h', 0),
                volatility=market['volatility'],
                atr=market.get('atr', 0),
                jaw=alligator['jaw'],
                teeth=alligator['teeth'],
                lips=alligator['lips'],
                alignment=alligator['alignment'],
                rsi=tech['rsi'],
                momentum=tech.get('momentum', 0),
                support=market.get('support', 0),
                resistance=market.get('resistance', 0),
                trend_strength=market.get('trend_strength', 0),
                volume_confirmed=market.get('volume_confirmed', False),
                equity=data.get('account_info', {}).get('equity', 0),
                risk_percent=BTCUSDConfig.max_risk_percent
            )

    def _make_request_with_retry(self, payload: Dict[str, Any]) -> str:
        """Make AI request with optimized retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    self.url,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    decision = result.get('response', '').strip().upper()

                    # Fast validation
                    valid_decisions = ['OPEN_BUY', 'OPEN_SELL', 'CLOSE_POSITION', 'HOLD']
                    for valid in valid_decisions:
                        if valid in decision:
                            logger.debug(f"AI Decision: {valid} (attempt {attempt + 1})")
                            return valid

                    logger.warning(f"Invalid AI response: {decision[:30]}...")
                    return "HOLD"
                else:
                    logger.warning(f"Ollama error {response.status_code} (attempt {attempt + 1})")

            except requests.exceptions.Timeout:
                logger.warning(f"AI timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"AI request error (attempt {attempt + 1}): {e}")

            # Brief pause before retry
            if attempt < self.max_retries - 1:
                time.sleep(0.1)

        logger.error("All AI requests failed, defaulting to HOLD")
        return "HOLD"


class OptimizedBTCAlligatorStrategy:
    """High-performance Alligator strategy optimized for BTCUSD"""

    def __init__(self, config: Optional[BTCUSDConfig] = None):
        self.config = config or BTCUSDConfig()
        self.symbol = "BTCUSD"
        self.timeframe = mt5.TIMEFRAME_M1

        # Performance optimization components
        self.performance_optimizer = PerformanceOptimizer()
        self.ai_agent = OptimizedOllamaAgent()

        # Data buffers for performance
        self.price_buffer = []
        self.max_buffer_size = self.config.data_buffer_size

        # Threading for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=3)

        # Performance tracking
        self.last_execution_time = 0
        self.execution_interval = 15  # Minimum seconds between executions
        self.performance_metrics = {
            'total_decisions': 0,
            'cache_hits': 0,
            'avg_response_time': 0,
            'errors': 0
        }

        # Pre-calculate common values
        self._precalculate_values()

    def _precalculate_values(self):
        """Pre-calculate commonly used values for performance"""
        self.point_value_cache = {}
        self.lot_size_cache = {}

    @lru_cache(maxsize=32)
    def _get_symbol_info_cached(self) -> Optional[Any]:
        """Cached symbol info retrieval"""
        return mt5.symbol_info(self.symbol)

    def update_price_buffer(self, new_price: float):
        """Update price buffer with new data"""
        self.price_buffer.append(new_price)
        if len(self.price_buffer) > self.max_buffer_size:
            self.price_buffer.pop(0)

    def calculate_alligator_optimized(self, prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Optimized Alligator calculation using cached operations"""
        prices_tuple = tuple(prices)

        # Use cached SMA calculations
        jaw = np.array(self.performance_optimizer.cached_sma(prices_tuple, self.config.jaw_period))
        teeth = np.array(self.performance_optimizer.cached_sma(prices_tuple, self.config.teeth_period))
        lips = np.array(self.performance_optimizer.cached_sma(prices_tuple, self.config.lips_period))

        # Apply shifts
        jaw = np.roll(jaw, self.config.jaw_shift)
        teeth = np.roll(teeth, self.config.teeth_shift)
        lips = np.roll(lips, self.config.lips_shift)

        return jaw, teeth, lips

    def analyze_btc_market_optimized(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Optimized market analysis for BTCUSD"""
        try:
            if len(df) < 50:
                return self._get_default_market_data()

            # Convert to numpy for performance
            close_prices = df['close'].values
            high_prices = df['high'].values
            low_prices = df['low'].values

            # Calculate Alligator with optimizations
            jaw, teeth, lips = self.calculate_alligator_optimized(close_prices)

            current_price = close_prices[-1]
            last_jaw = jaw[-1]
            last_teeth = teeth[-1]
            last_lips = lips[-1]

            # Update price buffer
            self.update_price_buffer(current_price)

            # Determine alignment with NaN handling
            if any(pd.isna([last_jaw, last_teeth, last_lips])):
                alignment = "insufficient_data"
            elif current_price > last_lips > last_teeth > last_jaw:
                alignment = "bullish"
            elif current_price < last_lips < last_teeth < last_jaw:
                alignment = "bearish"
            else:
                alignment = "neutral"

            # Vectorized technical indicators
            rsi = self.performance_optimizer.calculate_rsi_vectorized(close_prices)
            atr = self.performance_optimizer.calculate_atr_vectorized(high_prices, low_prices, close_prices)

            # Calculate momentum (rate of change)
            momentum = (close_prices[-1] - close_prices[-5]) / close_prices[-5] if len(close_prices) >= 5 else 0

            # Calculate volatility
            volatility = atr / current_price if current_price > 0 else 0

            # Support and resistance levels (simplified)
            recent_high = np.max(high_prices[-20:])
            recent_low = np.min(low_prices[-20:])

            # Trend strength
            trend_strength = abs(current_price - close_prices[-20]) / close_prices[-20] if len(close_prices) >= 20 else 0

            # Price change 24h (assuming M1 timeframe, 1440 minutes = 24h)
            price_change_24h = ((current_price - close_prices[-1440]) / close_prices[-1440] * 100) if len(close_prices) >= 1440 else 0

            return {
                "symbol": self.symbol,
                "current_price": float(current_price),
                "alligator": {
                    "jaw": float(last_jaw) if not pd.isna(last_jaw) else 0,
                    "teeth": float(last_teeth) if not pd.isna(last_teeth) else 0,
                    "lips": float(last_lips) if not pd.isna(last_lips) else 0,
                    "alignment": alignment
                },
                "technical_indicators": {
                    "rsi": float(rsi),
                    "atr": float(atr),
                    "momentum": float(momentum),
                    "volatility": float(volatility)
                },
                "market_conditions": {
                    "support": float(recent_low),
                    "resistance": float(recent_high),
                    "trend_strength": float(trend_strength),
                    "price_change_24h": float(price_change_24h),
                    "volatility": float(volatility),
                    "volume_confirmed": True  # Simplified
                }
            }

        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return self._get_default_market_data()

    def _get_default_market_data(self) -> Dict[str, Any]:
        """Return default market data for error cases"""
        return {
            "symbol": self.symbol,
            "current_price": 0,
            "alligator": {"jaw": 0, "teeth": 0, "lips": 0, "alignment": "neutral"},
            "technical_indicators": {"rsi": 50, "atr": 0, "momentum": 0, "volatility": 0},
            "market_conditions": {
                "support": 0, "resistance": 0, "trend_strength": 0,
                "price_change_24h": 0, "volatility": 0, "volume_confirmed": False
            }
        }

    def get_market_data_optimized(self) -> Optional[pd.DataFrame]:
        """Optimized market data retrieval"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, self.config.data_buffer_size)
            if rates is None:
                logger.error(f"Failed to get market data: {mt5.last_error()}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df

        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None

    def get_account_info_cached(self) -> Optional[Dict[str, Any]]:
        """Cached account info retrieval"""
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None

            return {
                "balance": account_info.balance,
                "equity": account_info.equity,
                "free_margin": account_info.margin_free,
                "margin_level": account_info.margin_level
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def calculate_btc_position_size(self, account_equity: float, volatility: float) -> float:
        """Optimized position sizing for BTCUSD"""
        try:
            # Dynamic risk based on volatility
            risk_multiplier = min(1.0, max(0.3, 1.0 - (volatility * 10)))
            adjusted_risk_percent = self.config.max_risk_percent * risk_multiplier

            # Calculate risk amount
            risk_amount = account_equity * (adjusted_risk_percent / 100)

            # Get symbol info from cache
            symbol_info = self._get_symbol_info_cached()
            if symbol_info is None:
                return self.config.lot_size

            # Calculate position size based on BTC volatility
            lot_size = risk_amount / (self.config.sl_points * symbol_info.point * 100)

            # Apply BTC-specific limits
            lot_size = min(lot_size, 0.05)  # Max 0.05 for BTC
            lot_size = max(lot_size, symbol_info.volume_min)

            return round(lot_size, 3)

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return self.config.lot_size

    def open_btc_position_optimized(self, signal: str, volatility: float) -> bool:
        """Optimized position opening for BTCUSD"""
        try:
            # Get symbol info
            symbol_info = self._get_symbol_info_cached()
            if symbol_info is None:
                logger.error("Failed to get symbol info")
                return False

            # Ensure symbol is selected
            if not symbol_info.visible:
                if not mt5.symbol_select(self.symbol, True):
                    logger.error(f"Failed to select {self.symbol}")
                    return False

            # Get account info
            account_info = self.get_account_info_cached()
            if account_info is None:
                return False

            # Calculate optimized position size
            lot_size = self.calculate_btc_position_size(account_info['equity'], volatility)

            # Get current price
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                logger.error("Failed to get tick info")
                return False

            if signal == "BUY":
                price = tick.ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                price = tick.bid
                order_type = mt5.ORDER_TYPE_SELL

            # Dynamic SL/TP based on volatility
            volatility_factor = min(2.0, max(0.5, volatility * self.config.btc_volatility_multiplier))
            dynamic_sl = int(self.config.sl_points * volatility_factor)
            dynamic_tp = int(self.config.tp_points * volatility_factor)

            # Calculate SL and TP
            point = symbol_info.point
            if signal == "BUY":
                sl = price - dynamic_sl * point
                tp = price + dynamic_tp * point
            else:
                sl = price + dynamic_sl * point
                tp = price - dynamic_tp * point

            # Optimized request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 100,  # Higher for crypto
                "magic": 666000,
                "comment": f"Optimized BTC Alligator {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order
            result = mt5.order_send(request)

            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.retcode if result else 'None'}")
                return False

            logger.info(f"BTC {signal} position opened: {lot_size} lots at {price}")
            logger.info(f"SL: {sl:.2f}, TP: {tp:.2f}, Volatility: {volatility:.4f}")
            return True

        except Exception as e:
            logger.error(f"Error opening BTC position: {e}")
            return False

    def close_positions_optimized(self) -> bool:
        """Optimized position closing"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            if not positions:
                return True

            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return False

            for position in positions:
                # Prepare close request
                if position.type == mt5.POSITION_TYPE_BUY:
                    order_type = mt5.ORDER_TYPE_SELL
                    price = tick.bid
                else:
                    order_type = mt5.ORDER_TYPE_BUY
                    price = tick.ask

                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": self.symbol,
                    "volume": position.volume,
                    "type": order_type,
                    "position": position.ticket,
                    "price": price,
                    "deviation": 100,
                    "magic": 666000,
                    "comment": "Optimized BTC Alligator Close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"BTC position {position.ticket} closed at {price}")
                else:
                    logger.error(f"Failed to close position {position.ticket}")

            return True

        except Exception as e:
            logger.error(f"Error closing positions: {e}")
            return False

    def should_execute_strategy(self) -> bool:
        """Check if strategy should execute based on timing"""
        current_time = time.time()
        if current_time - self.last_execution_time < self.execution_interval:
            return False

        # Additional checks
        positions = mt5.positions_get(symbol=self.symbol)
        if positions and len(positions) >= self.config.max_positions:
            return False

        self.last_execution_time = current_time
        return True

    def execute_strategy_optimized(self) -> Dict[str, Any]:
        """Execute optimized strategy with performance tracking"""
        performance_start = time.time()

        try:
            # Check execution timing
            if not self.should_execute_strategy():
                return {"status": "skipped", "reason": "execution_interval"}

            # Get market data
            df = self.get_market_data_optimized()
            if df is None:
                return {"status": "error", "reason": "no_market_data"}

            # Analyze market
            market_analysis = self.analyze_btc_market_optimized(df)

            # Get account info
            account_info = self.get_account_info_cached()
            if account_info is None:
                return {"status": "error", "reason": "no_account_info"}

            # Add account info to market analysis
            market_analysis['account_info'] = account_info

            # Check volatility
            volatility = market_analysis['technical_indicators']['volatility']
            if volatility > self.config.volatility_threshold * 2:
                logger.warning(f"High volatility detected: {volatility:.4f}")
                return {"status": "skipped", "reason": "high_volatility"}

            # Get positions
            positions = mt5.positions_get(symbol=self.symbol)
            position_count = len(positions) if positions else 0

            # Get AI decision
            decision = self.ai_agent.get_btc_decision(market_analysis)

            # Execute decision
            result = {"status": "executed", "decision": decision}

            if decision == "OPEN_BUY" and position_count == 0:
                logger.info("AI signal: OPEN_BUY")
                success = self.open_btc_position_optimized("BUY", volatility)
                result['action'] = "buy_opened" if success else "buy_failed"

            elif decision == "OPEN_SELL" and position_count == 0:
                logger.info("AI signal: OPEN_SELL")
                success = self.open_btc_position_optimized("SELL", volatility)
                result['action'] = "sell_opened" if success else "sell_failed"

            elif decision == "CLOSE_POSITION" and position_count > 0:
                logger.info("AI signal: CLOSE_POSITION")
                success = self.close_positions_optimized()
                result['action'] = "positions_closed" if success else "close_failed"

            elif decision == "HOLD":
                logger.debug("AI signal: HOLD")
                result['action'] = "hold"

            # Update performance metrics
            execution_time = time.time() - performance_start
            self.performance_metrics['total_decisions'] += 1
            self.performance_metrics['avg_response_time'] = (
                (self.performance_metrics['avg_response_time'] * (self.performance_metrics['total_decisions'] - 1) + execution_time) /
                self.performance_metrics['total_decisions']
            )

            result['execution_time'] = execution_time
            result['market_data'] = {
                'price': market_analysis['current_price'],
                'volatility': volatility,
                'alignment': market_analysis['alligator']['alignment']
            }

            # Memory cleanup
            if self.performance_metrics['total_decisions'] % 100 == 0:
                self.performance_optimizer.cleanup_memory()

            return result

        except Exception as e:
            logger.error(f"Error in strategy execution: {e}")
            self.performance_metrics['errors'] += 1
            return {"status": "error", "reason": str(e)}


def initialize_mt5_optimized() -> bool:
    """Optimized MT5 initialization"""
    try:
        if not mt5.initialize():
            logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
            return False

        # Pre-select BTCUSD for performance
        if not mt5.symbol_select("BTCUSD", True):
            logger.error("Failed to select BTCUSD")
            return False

        logger.info("MT5 initialized successfully for BTCUSD")
        return True

    except Exception as e:
        logger.error(f"MT5 initialization error: {e}")
        return False


def main():
    """Main optimized execution function"""
    logger.info("Starting Optimized BTCUSD Alligator Trading Strategy")

    # Initialize MT5
    if not initialize_mt5_optimized():
        return

    # Test Ollama connection
    try:
        ai_agent = OptimizedOllamaAgent()
        logger.info("AI agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI agent: {e}")
        mt5.shutdown()
        return

    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        logger.error("Failed to get account info")
        mt5.shutdown()
        return

    logger.info(f"Connected to account {account_info.login}")
    logger.info(f"Balance: ${account_info.balance:.2f}")
    logger.info(f"Equity: ${account_info.equity:.2f}")

    # Create optimized strategy
    config = BTCUSDConfig()
    strategy = OptimizedBTCAlligatorStrategy(config)

    logger.info(f"Strategy configuration:")
    logger.info(f"  - Max Risk: {config.max_risk_percent}%")
    logger.info(f"  - SL/TP: {config.sl_points}/{config.tp_points} points")
    logger.info(f"  - Lot size: {config.lot_size}")
    logger.info(f"  - Volatility threshold: {config.volatility_threshold}")

    try:
        # Strategy execution loop
        iteration = 0
        last_performance_log = time.time()

        while True:
            iteration += 1

            # Execute strategy
            result = strategy.execute_strategy_optimized()

            # Log performance metrics every 5 minutes
            current_time = time.time()
            if current_time - last_performance_log > 300:
                metrics = strategy.performance_metrics
                logger.info(f"Performance Metrics:")
                logger.info(f"  - Total decisions: {metrics['total_decisions']}")
                logger.info(f"  - Avg response time: {metrics['avg_response_time']:.3f}s")
                logger.info(f"  - Errors: {metrics['errors']}")
                logger.info(f"  - Cache size: {len(strategy.ai_agent.decision_cache)}")

                # Log account status
                account = mt5.account_info()
                if account:
                    logger.info(f"Account: Balance=${account.balance:.2f}, Equity=${account.equity:.2f}")

                last_performance_log = current_time

            # Brief pause between iterations
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping strategy...")
    except Exception as e:
        logger.error(f"Critical error in strategy: {e}")
        logger.exception(e)
    finally:
        # Cleanup
        strategy.executor.shutdown(wait=True)
        mt5.shutdown()
        logger.info("Strategy stopped and resources cleaned up")


if __name__ == "__main__":
    main()