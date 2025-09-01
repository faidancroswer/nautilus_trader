#!/usr/bin/env python3
"""
Advanced AI Trading Agent with Technical Analysis
"""

import logging
import time
import sys
import json
import requests
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_ai_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """

    Advanced technical analysis tools
    """

    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average
        """
        return prices.rolling(window=period).mean()

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple:
        """
        Calculate MACD
        """
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> tuple:
        """
        Calculate Bollinger Bands
        """
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band

    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> tuple:
        """
        Calculate Stochastic Oscillator
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent


















    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """

        Calculate Relative Strength Index
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple:
        """
        Calculate MACD
        """
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> tuple:
        """
        Calculate Bollinger Bands
        """
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> tuple:
        """
        Calculate Stochastic Oscillator
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent


class AdvancedOllamaAgent:
    """
    Advanced Ollama AI Agent with comprehensive market analysis
    Optimized for fast trading decisions
    """

    def __init__(self, model: str = "phi3:latest", host: str = "localhost", port: int = 11434):
        self.model = model
        self.port = port
        self.url = f"http://{host}:{port}/api/generate"
        self.technical_analyzer = TechnicalAnalyzer()

        # Performance optimization settings
        self.timeout = 30  # Increased timeout for reliable connections

        self.max_retries = 3  # More retries for reliability
        self.temperature = 0.3  # Lower temperature for consistent decisions
        self.max_tokens = 100  # Reduced tokens for faster processing

        # Cache for recent decisions to avoid redundant calls
        self.decision_cache = {}
        self.cache_duration = 30  # seconds
        # Initialize connection test
        self._test_connection()


    def _test_connection(self):
        """Test Ollama connection and warm up the model"""
        try:
            payload = {
                "model": self.model,
                "prompt": "Ready for trading analysis",
                "stream": False,
                "temperature": self.temperature,
                "max_tokens": 10
            }
            response = requests.post(self.url, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                logger.info(f"Ollama connection successful with model {self.model}")
            else:
                logger.warning(f"Ollama connection test failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Ollama connection test error: {e}")
    def _get_cache_key(self, current_price: float, alignment: str) -> str:
        """Generate cache key for decision caching"""
        return f"{current_price:.4f}_{alignment}_{int(time.time() / self.cache_duration)}"



    def create_comprehensive_analysis(self, df: pd.DataFrame, positions: list, account_info: Dict[str, Any], symbol: str = "EURUSD") -> Dict[str, Any]:

        """
        Create comprehensive market analysis
        """
        # Basic Alligator analysis
        jaw, teeth, lips = self.technical_analyzer.calculate_sma(df['close'], 13).shift(8), \
                          self.technical_analyzer.calculate_sma(df['close'], 8).shift(5), \
                          self.technical_analyzer.calculate_sma(df['close'], 5).shift(3)
        
        current_price = df['close'].iloc[-1]
        last_jaw, last_teeth, last_lips = jaw.iloc[-1], teeth.iloc[-1], lips.iloc[-1]
        
        # Technical indicators
        rsi = self.technical_analyzer.calculate_rsi(df['close']).iloc[-1]
        macd_line, signal_line, histogram = self.technical_analyzer.calculate_macd(df['close'])
        macd_val, signal_val, hist_val = macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
        
        upper_band, middle_band, lower_band = self.technical_analyzer.calculate_bollinger_bands(df['close'])
        bb_upper, bb_middle, bb_lower = upper_band.iloc[-1], middle_band.iloc[-1], lower_band.iloc[-1]
        
        k_percent, d_percent = self.technical_analyzer.calculate_stochastic(df['high'], df['low'], df['close'])
        stoch_k, stoch_d = k_percent.iloc[-1], d_percent.iloc[-1]
        
        # Market volatility (ATR approximation)
        tr = np.maximum(df['high'] - df['low'], 
                       np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean().iloc[-1]
        
        # Price action patterns
        price_change_24h = ((current_price - df['close'].iloc[-24]) / df['close'].iloc[-24]) * 100
        
        return {
            "symbol": symbol,
            "current_price": float(current_price),
            "alligator": {
                "jaw": float(last_jaw) if not pd.isna(last_jaw) else 0,
                "teeth": float(last_teeth) if not pd.isna(last_teeth) else 0,
                "lips": float(last_lips) if not pd.isna(last_lips) else 0,
                "alignment": "bullish" if current_price > last_lips > last_teeth > last_jaw else
                           "bearish" if current_price < last_lips < last_teeth < last_jaw else "neutral"
            },
            "technical_indicators": {
                "rsi": float(rsi),
                "macd": {
                    "line": float(macd_val),
                    "signal": float(signal_val),
                    "histogram": float(hist_val)
                },
                "bollinger_bands": {
                    "upper": float(bb_upper),
                    "middle": float(bb_middle),
                    "lower": float(bb_lower),
                    "position": "above_upper" if current_price > bb_upper else
                               "below_lower" if current_price < bb_lower else "within"
                },
                "stochastic": {
                    "k": float(stoch_k),
                    "d": float(stoch_d),
                    "overbought": stoch_k > 80,
                    "oversold": stoch_k < 20
                }
            },
            "market_conditions": {
                "volatility": float(atr),
                "price_change_24h": float(price_change_24h),
                "trend_strength": abs(current_price - bb_middle) / bb_middle * 100
            },
            "account_info": account_info,
            "positions": len(positions)
        }
    

    def generate_optimized_prompt(self, analysis: Dict[str, Any]) -> str:
        """

        Generate optimized prompt for fast AI decisions

        """
        # Simplified prompt for faster processing
        alligator = analysis['alligator']
        tech = analysis['technical_indicators']
        market = analysis['market_conditions']

        prompt = f"""FOREX TRADING DECISION - EURUSD

Price: {analysis['current_price']:.5f}
Alligator: {alligator['alignment']} (J:{alligator['jaw']:.5f} T:{alligator['teeth']:.5f} L:{alligator['lips']:.5f})
RSI: {tech['rsi']:.1f} MACD: {tech['macd']['histogram']:.5f}
BB: {tech['bollinger_bands']['position']} Stoch: {tech['stochastic']['k']:.1f}
Volatility: {market['volatility']:.5f} Change24h: {market['price_change_24h']:.1f}%
Positions: {analysis['positions']}

RULES:
- Bullish: price>lips>teeth>jaw + RSI<70 + MACD>0 → OPEN_BUY
- Bearish: price<lips<teeth<jaw + RSI>30 + MACD<0 → OPEN_SELL
- Exit: opposite signals or RSI extreme → CLOSE_POSITION
- Uncertain: mixed signals → HOLD

RESPOND ONLY: OPEN_BUY, OPEN_SELL, CLOSE_POSITION, or HOLD"""


        return prompt
    
    def get_decision(self, analysis: Dict[str, Any]) -> str:
        """


        Get trading decision from optimized Ollama agent with caching
        """

        try:

            # Check cache first for faster responses
            cache_key = self._get_cache_key(
                analysis['current_price'],
                analysis['alligator']['alignment']



            )






            if cache_key in self.decision_cache:

                cached_decision = self.decision_cache[cache_key]

                logger.info(f"Using cached AI decision: {cached_decision}")

                return cached_decision



            # Generate optimized prompt

            prompt = self.generate_optimized_prompt(analysis)



            # Optimized payload for speed



            payload = {





                "model": self.model,



                "prompt": prompt,

                "stream": False,
                "temperature": self.temperature,






                "top_p": 0.8,

                "max_tokens": self.max_tokens

            }




            # Make request with retry logic

            decision = self._make_ai_request(payload)



            # Cache the decision

            if decision != "HOLD":

                self.decision_cache[cache_key] = decision

                # Clean old cache entries

                if len(self.decision_cache) > 10:


                    oldest_key = next(iter(self.decision_cache))
                    del self.decision_cache[oldest_key]

            return decision

        except Exception as e:
            logger.error(f"Error getting AI decision: {e}")
            return "HOLD"

    def _make_ai_request(self, payload: dict) -> str:
        """Make AI request with optimized retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.url, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    result = response.json()
                    decision = result.get('response', '').strip().upper()

                    # Fast validation
                    valid_decisions = ['OPEN_BUY', 'OPEN_SELL', 'CLOSE_POSITION', 'HOLD']
                    for valid_decision in valid_decisions:
                        if valid_decision in decision:
                            logger.info(f"AI Decision: {valid_decision} (attempt {attempt + 1})")
                            return valid_decision

                    logger.warning(f"Invalid AI response: {decision[:50]}...")
                    return "HOLD"
                else:
                    logger.warning(f"Ollama API error {response.status_code} (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)  # Brief pause before retry

            except requests.exceptions.Timeout:
                logger.warning(f"AI request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"AI request error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(0.5)

        logger.error("All AI request attempts failed, defaulting to HOLD")
        return "HOLD"


class AdvancedAlligatorStrategy:
    """
    Advanced Alligator strategy with comprehensive AI integration
    Now supports XAUUSD and BTCUSD
    """

    def __init__(self, symbols=["XAUUSD", "BTCUSD"], timeframe=mt5.TIMEFRAME_M1, model="phi3:latest"):
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
        self.timeframe = timeframe

        # Configurações específicas por símbolo
        self.symbol_configs = {
            "XAUUSD": {
                "lot_size": 0.01,
                "sl_points": 200,
                "tp_points": 400,
                "max_risk_percent": 1.0,
                "volatility_multiplier": 2.0
            },
            "BTCUSD": {
                "lot_size": 0.01,
                "sl_points": 500,
                "tp_points": 1000,
                "max_risk_percent": 0.5,
                "volatility_multiplier": 5.0
            }
        }

        # Initialize advanced AI agent
        self.ai_agent = AdvancedOllamaAgent(model=model)

        # Tracking por símbolo
        self.last_execution = {symbol: 0 for symbol in self.symbols}
        
    def get_market_data(self, symbol: str, count=100):
        """
        Get market data from MT5 for specific symbol
        """
        rates = mt5.copy_rates_from_pos(symbol, self.timeframe, 0, count)
        if rates is None:
            logger.error(f"Failed to get market data for {symbol}: {mt5.last_error()}")
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def get_account_info(self):
        """
        Get account information
        """
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
    
    def get_open_positions(self, symbol: str):
        """
        Get open positions from MT5 for specific symbol
        """
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            logger.error(f"Failed to get positions for {symbol}: {mt5.last_error()}")
            return []
        return positions
    
    def calculate_position_size(self, account_equity: float, volatility: float) -> float:
        """
        Calculate dynamic position size based on volatility and risk management
        """
        # Risk 1.5% of equity
        risk_amount = account_equity * (self.max_risk_percent / 100)
        
        # Get symbol info for pip value
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            return self.lot_size
            
        # Adjust position size based on volatility
        # Higher volatility = smaller positions
        volatility_multiplier = max(0.5, min(2.0, 1.0 / (volatility * 1000)))  # Normalize volatility
        adjusted_risk = risk_amount * volatility_multiplier
        
        # Approximate pip value
        pip_value = symbol_info.point * 100000
        if "JPY" in self.symbol:
            pip_value = symbol_info.point * 1000
            
        # Calculate lot size
        if self.sl_points > 0:
            lot_size = adjusted_risk / (self.sl_points * pip_value)
            # Limit to reasonable lot sizes
            lot_size = min(lot_size, 0.5)  # Max 0.5 lot for safety
            lot_size = max(lot_size, 0.01)  # Min 0.01 lot
            return round(lot_size, 2)
        else:
            return self.lot_size
    
    def close_position(self, position):


        """
        Close an open position
        """
        # Prepare close request
        if position.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(self.symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(self.symbol).ask
            
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Advanced AI Alligator Strategy Close",
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
    

    def open_position_for_symbol(self, symbol: str, signal: str, volatility: float, config: Dict[str, Any]):
        """
        Open a new position for specific symbol with adapted parameters
        """
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Failed to get symbol info for {symbol}: {mt5.last_error()}")
                return False

            # Check if symbol is available for trading
            if not symbol_info.visible:
                logger.info(f"Symbol {symbol} is not visible, trying to select it")
                if not mt5.symbol_select(symbol, True):
                    logger.error(f"Failed to select symbol {symbol}: {mt5.last_error()}")
                    return False

            # Get account info for position sizing
            account_info = self.get_account_info()
            if account_info is None:
                return False

            # Use symbol-specific lot size
            lot_size = config['lot_size']

            # Adjust lot size based on volatility
            volatility_adj = min(2.0, max(0.5, volatility * config['volatility_multiplier']))
            lot_size = lot_size / volatility_adj
            lot_size = max(symbol_info.volume_min, min(lot_size, config.get('max_lot', 0.1)))

            logger.info(f"{symbol}: Calculated lot size: {lot_size} (volatility: {volatility:.5f})")

            # Get current price
            if signal == "BUY":
                price = mt5.symbol_info_tick(symbol).ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                price = mt5.symbol_info_tick(symbol).bid
                order_type = mt5.ORDER_TYPE_SELL

            # Symbol-specific SL and TP
            sl_points = config['sl_points']
            tp_points = config['tp_points']

            # Adjust for current volatility
            volatility_factor = min(2.0, max(0.5, volatility * 10000))
            sl_points = int(sl_points * volatility_factor)
            tp_points = int(tp_points * volatility_factor)

            # Calculate SL and TP
            point = symbol_info.point
            if signal == "BUY":
                sl = price - sl_points * point
                tp = price + tp_points * point
            else:
                sl = price + sl_points * point
                tp = price - tp_points * point

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 50,  # Higher deviation for volatile symbols
                "magic": 234000 + hash(symbol) % 1000,  # Unique magic per symbol
                "comment": f"AI {symbol} {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order
            result = mt5.order_send(request)
            if result is None:
                logger.error(f"Failed to send order for {symbol}: {mt5.last_error()}")
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed for {symbol} with retcode {result.retcode}")
                return False

            logger.info(f"{symbol} {signal} order placed: {lot_size} lots at {price}")
            logger.info(f"{symbol} SL: {sl:.5f}, TP: {tp:.5f}")
            return True

        except Exception as e:
            logger.error(f"Error opening position for {symbol}: {e}")
            return False

    def open_position(self, signal, volatility: float = 0.001):
        """
        Open a new position with dynamic sizing
        """
        # Get symbol info
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            logger.error(f"Failed to get symbol info: {mt5.last_error()}")
            return False
            
        # Check if symbol is available for trading
        if not symbol_info.visible:
            logger.info(f"Symbol {self.symbol} is not visible, trying to select it")
            if not mt5.symbol_select(self.symbol, True):
                logger.error(f"Failed to select symbol {self.symbol}: {mt5.last_error()}")
                return False
        
        # Get account info for position sizing
        account_info = self.get_account_info()
        if account_info is None:
            return False
            
        # Calculate dynamic position size
        lot_size = self.calculate_position_size(account_info["equity"], volatility)
        logger.info(f"Calculated lot size: {lot_size} (account equity: {account_info['equity']}, volatility: {volatility})")
        
        # Get current price
        if signal == "BUY":
            price = mt5.symbol_info_tick(self.symbol).ask
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = mt5.symbol_info_tick(self.symbol).bid
            order_type = mt5.ORDER_TYPE_SELL
            
        # Dynamic SL and TP based on volatility
        dynamic_sl_points = max(50, min(200, int(self.sl_points * (1 + volatility * 10000))))
        dynamic_tp_points = max(50, min(400, int(self.tp_points * (1 + volatility * 10000))))
        
        # Calculate SL and TP
        point = symbol_info.point
        if signal == "BUY":
            sl = price - dynamic_sl_points * point
            tp = price + dynamic_tp_points * point
        else:
            sl = price + dynamic_sl_points * point
            tp = price - dynamic_tp_points * point
            
        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Advanced AI Alligator Strategy {signal}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        # Send order
        result = mt5.order_send(request)
        if result is None:
            logger.error(f"Failed to send order: {mt5.last_error()}")
            return False
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed with retcode {result.retcode}")
            logger.error(f"Request: {request}")
            return False
            
        logger.info(f"{signal} order placed successfully: {lot_size} {self.symbol} at {price}")
        logger.info(f"SL: {sl:.5f}, TP: {tp:.5f}")
        return True
    
    def execute_strategy_for_symbol(self, symbol: str):
        """
        Execute the advanced Alligator strategy with AI for specific symbol
        """
        try:
            current_time = time.time()

            # Controle de frequência por símbolo
            if current_time - self.last_execution[symbol] < 30:  # 30 segundos entre execuções
                return

            # Get market data for symbol
            df = self.get_market_data(symbol)
            if df is None or len(df) < 50:
                return

            # Get account info
            account_info = self.get_account_info()
            if account_info is None:
                return

            # Get open positions for symbol
            positions = self.get_open_positions(symbol)

            # Create comprehensive analysis with symbol-specific config
            analysis = self.ai_agent.create_comprehensive_analysis(df, positions, account_info, symbol)

            # Get AI decision
            decision = self.ai_agent.get_decision(analysis)

            # Get symbol config
            config = self.symbol_configs.get(symbol, self.symbol_configs["XAUUSD"])

            # Execute decision
            if decision == "OPEN_BUY" and len(positions) == 0:
                logger.info(f"{symbol}: AI decided to OPEN_BUY")
                volatility = analysis['market_conditions']['volatility']
                self.open_position_for_symbol(symbol, "BUY", volatility, config)
            elif decision == "OPEN_SELL" and len(positions) == 0:
                logger.info(f"{symbol}: AI decided to OPEN_SELL")
                volatility = analysis['market_conditions']['volatility']
                self.open_position_for_symbol(symbol, "SELL", volatility, config)
            elif decision == "CLOSE_POSITION" and len(positions) > 0:
                logger.info(f"{symbol}: AI decided to CLOSE_POSITION")
                for position in positions:
                    self.close_position(position)
            elif decision == "HOLD":
                logger.info(f"{symbol}: AI decided to HOLD")

            self.last_execution[symbol] = current_time

        except Exception as e:
            logger.error(f"Error executing strategy for {symbol}: {e}")

    def execute_strategy(self):
        """
        Execute strategy for all symbols
        """
        for symbol in self.symbols:
            self.execute_strategy_for_symbol(symbol)


def initialize_mt5():
    """
    Initialize MT5 connection
    """
    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    logger.info("MT5 initialized successfully")
    return True


def main():
    """
    Main function
    """
    logger.info("Starting Advanced AI-Powered Alligator strategy live trading")
    
    # Initialize MT5
    if not initialize_mt5():
        return
    
    # Test Ollama connection
    try:
        ai_agent = AdvancedOllamaAgent()
        test_prompt = "Test connection to advanced trading AI"
        payload = {
            "model": ai_agent.model,
            "prompt": test_prompt,
            "stream": False,
            "max_tokens": 50
        }
        response = requests.post(ai_agent.url, json=payload, timeout=10)
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
    
    # Create strategy instance for multiple symbols
    strategy = AdvancedAlligatorStrategy(symbols=["XAUUSD", "BTCUSD"], timeframe=mt5.TIMEFRAME_M1, model="phi3:latest")
    
    try:
        # Run the strategy loop
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"Strategy iteration {iteration}")
            
            # Execute strategy
            strategy.execute_strategy()
            
            # Log account info every 10 iterations (10 minutes)
            if iteration % 10 == 0:
                account_info = mt5.account_info()
                if account_info:
                    logger.info(f"Account Balance: {account_info.balance} {account_info.currency}")
                    logger.info(f"Account Equity: {account_info.equity} {account_info.currency}")
                    logger.info(f"Margin: {account_info.margin} {account_info.currency}")
                    logger.info(f"Free Margin: {account_info.margin_free} {account_info.currency}")
                    logger.info(f"Margin Level: {account_info.margin_level}%")
            
            # Wait for next iteration (1 minute)
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Stopping strategy...")
    except Exception as e:
        logger.error(f"Error in strategy execution: {e}")
        logger.exception(e)
    finally:
        # Shutdown MT5
        mt5.shutdown()
        logger.info("MT5 connection closed")


if __name__ == "__main__":
    main()
