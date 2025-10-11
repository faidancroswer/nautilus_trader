#!/usr/bin/env python3
"""
AI-Powered Alligator Strategy optimized for BTCUSD using Ollama local agent
High-performance version with caching, vectorized operations, and BTC-specific parameters
"""

import logging
import time
import sys
import json
import requests
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor
import gc
import psutil
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('ai_btcusd_trading_optimized.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class BTCUSDConfig:
    """Configuration optimized for BTCUSD trading"""
    symbol: str = "BTCUSD"
    timeframe: int = mt5.TIMEFRAME_M1
    model: str = "llama3.2:3b"
    host: str = "localhost"
    port: int = 11434

    # Alligator parameters optimized for BTC volatility
    jaw_period: int = 21  # Increased for longer trends
    jaw_shift: int = 8
    teeth_period: int = 13  # Intermediate period for crypto
    teeth_shift: int = 5
    lips_period: int = 8   # Shorter period for quick signals
    lips_shift: int = 3

    # Risk management for BTC - FBS specific adjustments
    sl_points: float = 500  # Reduced SL for FBS (500 points)
    tp_points: float = 1000  # 2:1 risk-reward ratio
    max_risk_percent: float = 1.0  # More conservative 1% per trade for FBS
    max_lot_size: float = 0.01  # Use minimum lot size for FBS

    # Performance settings
    cache_ttl: int = 30  # Cache TTL in seconds
    max_cache_size: int = 100
    cleanup_interval: int = 100  # Memory cleanup every N iterations
    request_timeout: int = 15  # API timeout in seconds

    # BTC-specific settings - FBS adjusted
    min_volatility_threshold: float = 0.002  # Higher threshold for FBS
    max_spread_percentage: float = 0.5  # Much higher spread tolerance for FBS (0.5%)


class PerformanceMonitor:
    """Monitor performance metrics"""

    def __init__(self):
        self.metrics = {
            'executions': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'ai_response_times': [],
            'calculation_times': [],
            'memory_usage': [],
            'errors': 0
        }
        self.start_time = time.time()

    def record_execution(self, cache_hit: bool, ai_time: float, calc_time: float):
        self.metrics['executions'] += 1
        if cache_hit:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1

        self.metrics['ai_response_times'].append(ai_time)
        self.metrics['calculation_times'].append(calc_time)

        # Record memory usage every 10 executions
        if self.metrics['executions'] % 10 == 0:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.metrics['memory_usage'].append(memory_mb)

    def record_error(self):
        self.metrics['errors'] += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        runtime = time.time() - self.start_time
        cache_hit_rate = (self.metrics['cache_hits'] / max(self.metrics['executions'], 1)) * 100

        return {
            'runtime_seconds': runtime,
            'total_executions': self.metrics['executions'],
            'cache_hit_rate_percent': cache_hit_rate,
            'avg_ai_response_time': np.mean(self.metrics['ai_response_times']) if self.metrics['ai_response_times'] else 0,
            'avg_calculation_time': np.mean(self.metrics['calculation_times']) if self.metrics['calculation_times'] else 0,
            'current_memory_mb': self.metrics['memory_usage'][-1] if self.metrics['memory_usage'] else 0,
            'error_rate': (self.metrics['errors'] / max(self.metrics['executions'], 1)) * 100
        }


class OptimizedOllamaAgent:
    """Optimized Ollama AI Agent with caching and connection pooling"""

    def __init__(self, config: BTCUSDConfig):
        self.config = config
        self.url = f"http://{config.host}:{config.port}/api/generate"
        self.session = requests.Session()
        self.session.timeout = config.request_timeout

        # Decision caching
        self.decision_cache = {}
        self.cache_timestamps = {}

        # Performance monitoring
        self.performance = PerformanceMonitor()

        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=2)

    def _generate_cache_key(self, market_data: Dict[str, Any]) -> str:
        """Generate optimized cache key"""
        # Bucket values to reduce cache variations
        price = market_data.get('current_price', 0)
        alignment = market_data.get('trend_strength', 'weak')

        # Price bucket (rounded to nearest 10)
        price_bucket = round(price / 10) * 10

        # Volatility bucket
        rsi = market_data.get('rsi', 50)
        rsi_bucket = round(rsi / 5) * 5

        return f"{price_bucket}_{alignment}_{rsi_bucket}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.cache_timestamps:
            return False

        age = time.time() - self.cache_timestamps[cache_key]
        return age < self.config.cache_ttl

    def _generate_fast_prompt(self, market_data: Dict[str, Any]) -> str:
        """Generate short prompt for quick decisions"""
        return f"""
        BTCUSD Analysis: Price {market_data.get('current_price', 0)},
        Alligator: {market_data.get('price_position', 'neutral')},
        Volatility: {market_data.get('trend_strength', 'weak')}

        Decision: OPEN_BUY, OPEN_SELL, CLOSE_POSITION, or HOLD?
        Respond with only the decision.
        """

    def _generate_detailed_prompt(self, market_data: Dict[str, Any],
                               positions: list, account_info: Dict[str, Any]) -> str:
        """Generate comprehensive prompt for detailed analysis"""
        return f"""
        You are an expert Bitcoin trader specializing in the Alligator strategy.

        MARKET DATA:
        - Symbol: BTCUSD
        - Price: ${market_data.get('current_price', 0):.2f}
        - Alligator Jaw: ${market_data.get('jaw', 0):.2f}
        - Alligator Teeth: ${market_data.get('teeth', 0):.2f}
        - Alligator Lips: ${market_data.get('lips', 0):.2f}
        - Position: {market_data.get('price_position', 'neutral')}
        - Trend Strength: {market_data.get('trend_strength', 'weak')}
        - RSI: {market_data.get('rsi', 50):.1f}
        - Volatility: {market_data.get('volatility', 0):.4f}

        ACCOUNT:
        - Balance: ${account_info.get('balance', 0):.2f}
        - Equity: ${account_info.get('equity', 0):.2f}
        - Free Margin: ${account_info.get('free_margin', 0):.2f}
        - Positions: {len(positions)}

        Bitcoin is highly volatile. Consider:
        - Risk management (max 1.5% per trade)
        - Current trend strength
        - Volatility levels
        - Position sizing

        Decision: OPEN_BUY, OPEN_SELL, CLOSE_POSITION, or HOLD?
        """

    def get_decision(self, market_data: Dict[str, Any], positions: list,
                    account_info: Dict[str, Any]) -> str:
        """Get optimized trading decision from Ollama agent"""
        start_time = time.time()

        # Check cache first
        cache_key = self._generate_cache_key(market_data)
        if self._is_cache_valid(cache_key):
            decision = self.decision_cache[cache_key]
            ai_time = time.time() - start_time
            self.performance.record_execution(True, ai_time, 0)
            logger.debug(f"Cache hit: {decision}")
            return decision

        try:
            # Choose prompt based on volatility
            volatility = market_data.get('volatility', 0)
            if volatility < self.config.min_volatility_threshold:
                prompt = self._generate_fast_prompt(market_data)
            else:
                prompt = self._generate_detailed_prompt(market_data, positions, account_info)

            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3 if volatility < self.config.min_volatility_threshold else 0.7,
                "top_p": 0.9,
                "max_tokens": 50 if volatility < self.config.min_volatility_threshold else 100
            }

            response = self.session.post(self.url, json=payload, timeout=self.config.request_timeout)

            if response.status_code == 200:
                result = response.json()
                decision = result.get('response', '').strip().upper()

                # Validate decision
                valid_decisions = ['OPEN_BUY', 'OPEN_SELL', 'CLOSE_POSITION', 'HOLD']
                if decision in valid_decisions:
                    # Cache the decision
                    self.decision_cache[cache_key] = decision
                    self.cache_timestamps[cache_key] = time.time()

                    # Cleanup old cache entries
                    self._cleanup_cache()

                    ai_time = time.time() - start_time
                    self.performance.record_execution(False, ai_time, 0)

                    logger.info(f"AI Decision: {decision} (response time: {ai_time:.2f}s)")
                    return decision
                else:
                    logger.warning(f"Invalid AI decision: {decision}, defaulting to HOLD")
                    self.performance.record_error()
                    return "HOLD"
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                self.performance.record_error()
                return "HOLD"

        except Exception as e:
            logger.error(f"Error getting AI decision: {e}")
            self.performance.record_error()
            return "HOLD"

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.cache_timestamps.items()
            if current_time - timestamp > self.config.cache_ttl
        ]

        for key in expired_keys:
            self.decision_cache.pop(key, None)
            self.cache_timestamps.pop(key, None)

        # Also limit cache size
        if len(self.decision_cache) > self.config.max_cache_size:
            # Remove oldest entries
            sorted_items = sorted(self.cache_timestamps.items(), key=lambda x: x[1])
            for key, _ in sorted_items[:-self.config.max_cache_size]:
                self.decision_cache.pop(key, None)
                self.cache_timestamps.pop(key, None)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return self.performance.get_performance_summary()


class OptimizedAlligatorStrategy:
    """Optimized Alligator strategy with BTC-specific enhancements"""

    def __init__(self, config: BTCUSDConfig):
        self.config = config

        # Initialize optimized AI agent
        self.ai_agent = OptimizedOllamaAgent(config)

        # Data cache for calculations
        self.data_cache = {}
        self.execution_count = 0

        # Performance monitoring
        self.performance = PerformanceMonitor()

        logger.info(f"Initialized optimized BTCUSD strategy with config: {asdict(config)}")

    @lru_cache(maxsize=50)
    def calculate_sma(self, data_tuple: Tuple, period: int) -> np.ndarray:
        """Cached SMA calculation using NumPy"""
        data = np.array(data_tuple)
        return np.convolve(data, np.ones(period)/period, mode='valid')

    def calculate_alligator_optimized(self, close_prices: pd.Series) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Optimized Alligator calculation with caching"""
        # Convert to tuple for caching
        prices_tuple = tuple(close_prices.values)

        # Calculate SMAs using cached function
        jaw_values = self.calculate_sma(prices_tuple, self.config.jaw_period)
        teeth_values = self.calculate_sma(prices_tuple, self.config.teeth_period)
        lips_values = self.calculate_sma(prices_tuple, self.config.lips_period)

        # Pad arrays to match original length
        jaw_padded = np.pad(jaw_values, (len(prices_tuple) - len(jaw_values), 0), 'constant')
        teeth_padded = np.pad(teeth_values, (len(prices_tuple) - len(teeth_values), 0), 'constant')
        lips_padded = np.pad(lips_values, (len(prices_tuple) - len(lips_values), 0), 'constant')

        # Apply shifts
        jaw = np.roll(jaw_padded, self.config.jaw_shift)
        teeth = np.roll(teeth_padded, self.config.teeth_shift)
        lips = np.roll(lips_padded, self.config.lips_shift)

        return jaw, teeth, lips

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calculate Average True Range for volatility measurement"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI using optimized method"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

    def analyze_market_context_optimized(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Optimized market context analysis"""
        start_time = time.time()

        try:
            # Calculate Alligator
            jaw, teeth, lips = self.calculate_alligator_optimized(df['close'])

            # Get last values
            last_close = df['close'].iloc[-1]
            last_jaw = jaw[-1]
            last_teeth = teeth[-1]
            last_lips = lips[-1]

            # Calculate additional indicators
            atr = self.calculate_atr(df['high'], df['low'], df['close'])
            rsi = self.calculate_rsi(df['close'])
            volatility = atr / last_close if last_close > 0 else 0

            # Enhanced price position logic
            if pd.isna(last_jaw) or pd.isna(last_teeth) or pd.isna(last_lips):
                price_position = "insufficient_data"
            elif last_close > last_lips > last_teeth > last_jaw:
                price_position = "above_alligator_bullish"
            elif last_close < last_lips < last_teeth < last_jaw:
                price_position = "below_alligator_bearish"
            else:
                # Check for convergence/divergence
                convergence = abs(last_lips - last_teeth) + abs(last_teeth - last_jaw)
                if convergence < (last_close * 0.0005):  # Very tight convergence
                    price_position = "alligator_sleeping"
                else:
                    price_position = "within_alligator_neutral"

            # Enhanced trend strength calculation
            if not (pd.isna(last_jaw) or pd.isna(last_teeth) or pd.isna(last_lips)):
                # Calculate alignment strength
                alignment_strength = 0
                if last_lips > last_teeth > last_jaw:
                    alignment_strength = (last_lips - last_jaw) / last_jaw
                elif last_lips < last_teeth < last_jaw:
                    alignment_strength = (last_jaw - last_lips) / last_jaw

                # Classify trend strength based on alignment and volatility
                if alignment_strength > 0.002 and volatility > 0.01:
                    trend_strength = "very_strong"
                elif alignment_strength > 0.001:
                    trend_strength = "strong"
                elif alignment_strength > 0.0005:
                    trend_strength = "moderate"
                else:
                    trend_strength = "weak"
            else:
                trend_strength = "insufficient_data"

            context = {
                "symbol": self.config.symbol,
                "current_price": float(last_close),
                "jaw": float(last_jaw) if not pd.isna(last_jaw) else 0,
                "teeth": float(last_teeth) if not pd.isna(last_teeth) else 0,
                "lips": float(last_lips) if not pd.isna(last_lips) else 0,
                "price_position": price_position,
                "trend_strength": trend_strength,
                "rsi": float(rsi),
                "volatility": float(volatility),
                "atr": float(atr)
            }

            calc_time = time.time() - start_time
            self.performance.record_execution(False, 0, calc_time)

            return context

        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            self.performance.record_error()
            return {}

    def get_market_data_optimized(self, count: int = 200) -> Optional[pd.DataFrame]:
        """Optimized market data retrieval"""
        try:
            rates = mt5.copy_rates_from_pos(self.config.symbol, self.config.timeframe, 0, count)
            if rates is None:
                logger.error(f"Failed to get market data: {mt5.last_error()}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')

            # Additional validation
            if len(df) < max(self.config.jaw_period + self.config.jaw_shift, 50):
                logger.warning(f"Insufficient data: {len(df)} bars")
                return None

            return df

        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None

    def calculate_position_size_optimized(self, account_equity: float,
                                       volatility: float) -> float:
        """Optimized position sizing based on volatility"""
        # Dynamic risk based on volatility - FBS adjusted
        if volatility > 0.03:  # High volatility - reduce risk for FBS
            risk_percent = self.config.max_risk_percent * 0.5
        elif volatility > 0.01:  # Medium volatility
            risk_percent = self.config.max_risk_percent * 0.75
        else:  # Normal volatility
            risk_percent = self.config.max_risk_percent

        risk_amount = account_equity * (risk_percent / 100)

        # Get symbol info
        symbol_info = mt5.symbol_info(self.config.symbol)
        if symbol_info is None:
            return 0.01  # Minimum safe size

        # Calculate pip value for BTCUSD
        pip_value = symbol_info.trade_tick_value

        # Dynamic stop loss based on volatility
        volatility_sl = max(self.config.sl_points, int(volatility * 10000))

        # Calculate position size - FBS specific
        if volatility_sl > 0:
            lot_size = risk_amount / (volatility_sl * pip_value)
            # FBS requires specific lot size handling
            lot_size = min(lot_size, self.config.max_lot_size)
            lot_size = max(lot_size, symbol_info.volume_min)
            # Round to valid lot step
            lot_size = round(lot_size / symbol_info.volume_step) * symbol_info.volume_step
            return round(lot_size, 2)
        else:
            return symbol_info.volume_min

    def execute_strategy_optimized(self):
        """Execute optimized strategy with performance monitoring"""
        self.execution_count += 1
        start_time = time.time()

        try:
            # Get market data
            df = self.get_market_data_optimized()
            if df is None:
                logger.error("Failed to get market data")
                return

            # Analyze market context
            market_context = self.analyze_market_context_optimized(df)
            if not market_context:
                logger.error("Failed to analyze market context")
                return

            # Get account info
            account_info = self.get_account_info()
            if not account_info:
                logger.error("Failed to get account info")
                return

            # Get open positions
            positions = self.get_open_positions()

            # Check spread
            if not self._check_spread_acceptable():
                logger.info("Spread too wide, skipping execution")
                return

            # Get AI decision
            decision = self.ai_agent.get_decision(market_context, positions, account_info)

            # Execute decision with optimized position sizing
            if decision == "OPEN_BUY" and len(positions) == 0:
                logger.info("AI decided to OPEN_BUY")
                self.open_position_optimized("BUY", market_context.get('volatility', 0))
            elif decision == "OPEN_SELL" and len(positions) == 0:
                logger.info("AI decided to OPEN_SELL")
                self.open_position_optimized("SELL", market_context.get('volatility', 0))
            elif decision == "CLOSE_POSITION" and len(positions) > 0:
                logger.info("AI decided to CLOSE_POSITION")
                for position in positions:
                    self.close_position(position)
            elif decision == "HOLD":
                logger.debug("AI decided to HOLD - no action taken")

            # Memory cleanup periodically
            if self.execution_count % self.config.cleanup_interval == 0:
                self._cleanup_memory()

            # Log performance summary
            if self.execution_count % 10 == 0:
                self._log_performance_summary()

        except Exception as e:
            logger.error(f"Error in strategy execution: {e}")
            self.performance.record_error()

        finally:
            execution_time = time.time() - start_time
            logger.debug(f"Strategy execution completed in {execution_time:.2f}s")

    def _check_spread_acceptable(self) -> bool:
        """Check if current spread is acceptable for trading"""
        try:
            tick = mt5.symbol_info_tick(self.config.symbol)
            if tick is None:
                return False

            spread = tick.ask - tick.bid
            spread_percentage = (spread / tick.bid) * 100

            return spread_percentage <= self.config.max_spread_percentage

        except Exception as e:
            logger.error(f"Error checking spread: {e}")
            return False

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            account_info = mt5.account_info()
            if account_info is None:
                logger.error(f"Failed to get account info: {mt5.last_error()}")
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

    def get_open_positions(self) -> list:
        """Get open positions from MT5"""
        try:
            positions = mt5.positions_get(symbol=self.config.symbol)
            if positions is None:
                logger.error(f"Failed to get positions: {mt5.last_error()}")
                return []
            return positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def open_position_optimized(self, signal: str, volatility: float):
        """Open optimized position with dynamic sizing"""
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(self.config.symbol)
            if symbol_info is None:
                logger.error(f"Failed to get symbol info: {mt5.last_error()}")
                return False

            # Select symbol if needed
            if not symbol_info.visible:
                if not mt5.symbol_select(self.config.symbol, True):
                    logger.error(f"Failed to select symbol: {mt5.last_error()}")
                    return False

            # Get account info
            account_info = self.get_account_info()
            if not account_info:
                return False

            # Calculate optimized position size
            lot_size = self.calculate_position_size_optimized(
                account_info["equity"],
                volatility
            )

            logger.info(f"Calculated lot size: {lot_size} (equity: {account_info['equity']}, volatility: {volatility:.4f})")

            # Get current price
            tick = mt5.symbol_info_tick(self.config.symbol)
            if tick is None:
                logger.error("Failed to get current tick")
                return False

            if signal == "BUY":
                price = tick.ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                price = tick.bid
                order_type = mt5.ORDER_TYPE_SELL

            # Dynamic SL/TP based on volatility - FBS specific
            # FBS uses points differently - adjust calculation
            current_spread = tick.ask - tick.bid
            spread_points = current_spread / symbol_info.point

            # Use conservative SL/TP for FBS
            sl_points = max(self.config.sl_points, spread_points * 3)  # 3x spread minimum
            tp_points = sl_points * 2  # 2:1 ratio

            if signal == "BUY":
                sl = price - (sl_points * symbol_info.point)
                tp = price + (tp_points * symbol_info.point)
            else:
                sl = price + (sl_points * symbol_info.point)
                tp = price - (tp_points * symbol_info.point)

            # Prepare optimized order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.config.symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234001,
                "comment": f"AI-BTC-{signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,  # Fill or Kill for FBS
            }

            # Log detailed order info for debugging
            logger.info(f"Sending {signal} order:")
            logger.info(f"  Volume: {lot_size}")
            logger.info(f"  Price: {price}")
            logger.info(f"  SL: {sl}")
            logger.info(f"  TP: {tp}")
            logger.info(f"  Deviation: 20")
            logger.info(f"  Magic: 234001")
            logger.info(f"  Comment: AI-BTC-{signal}")
            logger.info(f"  Type_filling: FOK")

            # Send order
            result = mt5.order_send(request)
            if result is None:
                error = mt5.last_error()
                logger.error(f"Failed to send order: {error}")
                logger.error(f"Full request: {request}")
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed with retcode {result.retcode}")
                logger.error(f"Error code: {result.comment}")
                logger.error(f"Request: {request}")
                logger.error(f"Result: {result}")
                return False

            logger.info(f"SUCCESS: {signal} order placed successfully!")
            logger.info(f"  Ticket: {result.order}")
            logger.info(f"  Volume: {result.volume} {self.config.symbol}")
            logger.info(f"  Price: {result.price}")
            logger.info(f"  Requested SL: {sl}")
            logger.info(f"  Requested TP: {tp}")
            return True

        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return False

    def close_position(self, position):
        """Close position with error handling"""
        try:
            # Get current tick
            tick = mt5.symbol_info_tick(self.config.symbol)
            if tick is None:
                logger.error("Failed to get current tick for closing")
                return False

            # Prepare close request
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.config.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": position.ticket,
                "price": price,
                "deviation": 20,
                "magic": 234001,
                "comment": "AI-BTC-CLOSE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            # Send close order
            result = mt5.order_send(request)
            if result is None:
                logger.error(f"Failed to close position: {mt5.last_error()}")
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Close order failed with retcode {result.retcode}")
                return False

            logger.info(f"Position {position.ticket} closed successfully")
            return True

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    def _cleanup_memory(self):
        """Cleanup memory and cache"""
        try:
            # Clear data cache
            self.data_cache.clear()

            # Force garbage collection
            gc.collect()

            logger.debug("Memory cleanup completed")

        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")

    def _log_performance_summary(self):
        """Log performance summary"""
        try:
            strategy_perf = self.performance.get_performance_summary()
            ai_perf = self.ai_agent.get_performance_summary()

            logger.info(f"""
Performance Summary (Executions: {self.execution_count}):
- Strategy: Avg calc time: {strategy_perf['avg_calculation_time']:.3f}s, Memory: {strategy_perf['current_memory_mb']:.1f}MB
- AI Agent: Cache hit rate: {ai_perf['cache_hit_rate_percent']:.1f}%, Avg response: {ai_perf['avg_ai_response_time']:.2f}s
- Errors: {strategy_perf['error_rate']:.1f}%
            """)

        except Exception as e:
            logger.error(f"Error logging performance summary: {e}")


def initialize_mt5() -> bool:
    """Initialize MT5 connection with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if mt5.initialize():
                logger.info("MT5 initialized successfully")
                return True
            else:
                logger.warning(f"MT5 initialization attempt {attempt + 1} failed: {mt5.last_error()}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        except Exception as e:
            logger.error(f"Error initializing MT5 (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)

    logger.error("Failed to initialize MT5 after all attempts")
    return False


def main():
    """Main function with enhanced error handling"""
    logger.info("Starting Optimized AI-Powered Alligator BTCUSD strategy")

    # Load configuration
    config = BTCUSDConfig()

    # Initialize MT5
    if not initialize_mt5():
        return

    # Test Ollama connection
    try:
        ai_agent = OptimizedOllamaAgent(config)
        test_payload = {
            "model": config.model,
            "prompt": "Respond with 'OK' if you can read this.",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
        response = requests.post(ai_agent.url, json=test_payload, timeout=30)
        if response.status_code == 200:
            logger.info("Ollama connection successful")
        else:
            logger.error(f"Ollama connection failed: {response.status_code}")
            mt5.shutdown()
            return
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        mt5.shutdown()
        return

    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        mt5.shutdown()
        return

    logger.info(f"Connected to MT5 account {account_info.login}")
    logger.info(f"Balance: {account_info.balance} {account_info.currency}")
    logger.info(f"Equity: {account_info.equity} {account_info.currency}")

    # Create optimized strategy instance
    strategy = OptimizedAlligatorStrategy(config)

    try:
        # Run the optimized strategy loop
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"Strategy iteration {iteration}")

            # Execute optimized strategy
            strategy.execute_strategy_optimized()

            # Extended account info logging every 50 iterations
            if iteration % 50 == 0:
                account_info = mt5.account_info()
                if account_info:
                    logger.info(f"Account Status - Balance: {account_info.balance}, Equity: {account_info.equity}, Free Margin: {account_info.margin_free}")

            # Optimized sleep interval (60 seconds for M1 timeframe)
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Stopping optimized strategy...")
    except Exception as e:
        logger.error(f"Critical error in strategy execution: {e}")
    finally:
        # Cleanup and shutdown
        try:
            strategy._cleanup_memory()
            ai_agent.session.close()
        except:
            pass

        mt5.shutdown()
        logger.info("Optimized AI Alligator BTCUSD strategy stopped")


if __name__ == "__main__":
    main()