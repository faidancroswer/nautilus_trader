import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import ollama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alligator_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlligatorStrategy:
    """
    Alligator trading strategy with Ollama AI integration
    """
    
    def __init__(self, config_file: str = "alligator_trading_config.json"):
        """Initialize the strategy with configuration"""
        self.config = self.load_config(config_file)
        self.symbol = self.config["trading"]["symbol"]
        self.timeframe = getattr(mt5, f"TIMEFRAME_{self.config['trading']['timeframe']}")
        self.lot_size = self.config["trading"]["lot_size"]
        self.risk_percent = self.config["trading"]["risk_percent"]
        
        # Initialize indicators parameters
        self.alligator_params = self.config["indicators"]["alligator"]
        self.rsi_params = self.config["indicators"]["rsi"]
        self.macd_params = self.config["indicators"]["macd"]
        
        # Initialize Ollama configuration
        self.ollama_model = self.config["ollama"]["model"]
        self.ollama_timeout = self.config["ollama"]["timeout"]
        self.ollama_temperature = self.config["ollama"]["temperature"]
        
        # Trading state
        self.position_opened = False
        self.last_signal = None
        
        logger.info("AlligatorStrategy initialized")
    
    def load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Check if we're connected to the correct server
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return False
                
            if self.config["mt5"]["server"] not in account_info.server:
                logger.warning(f"Connected to {account_info.server}, expected {self.config['mt5']['server']}")
            
            logger.info(f"MT5 initialized. Account: {account_info.login}, Balance: {account_info.balance}")
            return True
        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False
    
    def get_market_data(self, symbol: str, timeframe: int, count: int = 100) -> Optional[pd.DataFrame]:
        """Get market data from MT5"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                logger.error("Failed to get market data")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None
    
    def calculate_alligator(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Alligator indicators"""
        # Calculate Alligator lines
        df['alligator_jaw'] = df['close'].rolling(self.alligator_params['jaw_period']).mean().shift(self.alligator_params['jaw_shift'])
        df['alligator_teeth'] = df['close'].rolling(self.alligator_params['teeth_period']).mean().shift(self.alligator_params['teeth_shift'])
        df['alligator_lips'] = df['close'].rolling(self.alligator_params['lips_period']).mean().shift(self.alligator_params['lips_shift'])
        return df
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate RSI indicator"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df
    
    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD indicator"""
        fast_period = self.macd_params['fast_period']
        slow_period = self.macd_params['slow_period']
        signal_period = self.macd_params['signal_period']
        
        df['ema_fast'] = df['close'].ewm(span=fast_period).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period).mean()
        df['macd_line'] = df['ema_fast'] - df['ema_slow']
        df['macd_signal'] = df['macd_line'].ewm(span=signal_period).mean()
        df['macd_histogram'] = df['macd_line'] - df['macd_signal']
        return df
    
    def get_current_indicators(self) -> Optional[Dict]:
        """Get current indicator values"""
        try:
            # Get market data
            df = self.get_market_data(self.symbol, self.timeframe, 100)
            if df is None or len(df) < 30:
                return None
            
            # Calculate indicators
            df = self.calculate_alligator(df)
            df = self.calculate_rsi(df, self.rsi_params['period'])
            df = self.calculate_macd(df)
            
            # Get latest values
            latest = df.iloc[-1]
            
            indicators = {
                'price': float(latest['close']),
                'alligator_jaw': float(latest['alligator_jaw']) if not pd.isna(latest['alligator_jaw']) else None,
                'alligator_teeth': float(latest['alligator_teeth']) if not pd.isna(latest['alligator_teeth']) else None,
                'alligator_lips': float(latest['alligator_lips']) if not pd.isna(latest['alligator_lips']) else None,
                'rsi': float(latest['rsi']) if not pd.isna(latest['rsi']) else None,
                'macd_line': float(latest['macd_line']) if not pd.isna(latest['macd_line']) else None,
                'macd_signal': float(latest['macd_signal']) if not pd.isna(latest['macd_signal']) else None,
                'macd_histogram': float(latest['macd_histogram']) if not pd.isna(latest['macd_histogram']) else None
            }
            
            return indicators
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return None
    
    def get_ai_decision(self, indicators: Dict) -> str:
        """Get trading decision from Ollama AI"""
        try:
            # Create prompt for Ollama
            def format_value(value, precision=5):
                """Format numeric value or return 'N/A' if None"""
                if value is None:
                    return 'N/A'
                return f"{value:.{precision}f}"
            
            prompt = f"""
            You are a professional forex trader specializing in the Alligator strategy.
            Analyze the following market conditions for {self.symbol} and provide a trading decision.
            
            Current Market Data:
            Price: {format_value(indicators['price'], 5)}
            Alligator Jaw: {format_value(indicators['alligator_jaw'], 5)}
            Alligator Teeth: {format_value(indicators['alligator_teeth'], 5)}
            Alligator Lips: {format_value(indicators['alligator_lips'], 5)}
            RSI ({self.rsi_params['period']}): {format_value(indicators['rsi'], 2)}
            MACD Line: {format_value(indicators['macd_line'], 5)}
            MACD Signal: {format_value(indicators['macd_signal'], 5)}
            MACD Histogram: {format_value(indicators['macd_histogram'], 5)}
            
            Trading Rules:
            1. OPEN_BUY when Alligator lines align in upward direction (Lips > Teeth > Jaw) and RSI < 70
            2. OPEN_SELL when Alligator lines align in downward direction (Lips < Teeth < Jaw) and RSI > 30
            3. CLOSE_POSITION when opposite alignment occurs or RSI indicates overbought/oversold
            4. HOLD when conditions are unclear
            
            Risk Management:
            - Risk per trade: {self.risk_percent}%
            - Lot size: {self.lot_size}
            
            Respond with ONLY ONE of these decisions:
            - OPEN_BUY
            - OPEN_SELL
            - CLOSE_POSITION
            - HOLD
            """
            
            # Get decision from Ollama
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': self.ollama_temperature,
                    'timeout': self.ollama_timeout
                }
            )
            
            decision = response['message']['content'].strip().upper()
            
            # Validate decision
            valid_decisions = ['OPEN_BUY', 'OPEN_SELL', 'CLOSE_POSITION', 'HOLD']
            if decision not in valid_decisions:
                logger.warning(f"Invalid decision from AI: {decision}. Using HOLD.")
                return 'HOLD'
            
            logger.info(f"AI Decision: {decision}")
            return decision
            
        except Exception as e:
            logger.error(f"Error getting AI decision: {e}")
            return 'HOLD'  # Default to HOLD on error
    
    def get_open_positions(self) -> List:
        """Get currently open positions"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            return list(positions) if positions else []
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []
    
    def open_position(self, order_type: str) -> bool:
        """Open a new position"""
        try:
            # Prepare order request
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                logger.error(f"Failed to get symbol info for {self.symbol}")
                return False
            
            if not symbol_info.visible:
                if not mt5.symbol_select(self.symbol, True):
                    logger.error(f"Failed to select symbol {self.symbol}")
                    return False
            
            # Determine order type and price
            if order_type == "BUY":
                price = mt5.symbol_info_tick(self.symbol).ask
                order_type_mt5 = mt5.ORDER_TYPE_BUY
            else:  # SELL
                price = mt5.symbol_info_tick(self.symbol).bid
                order_type_mt5 = mt5.ORDER_TYPE_SELL
            
            # Calculate SL and TP (simple fixed points, adjust as needed)
            point = symbol_info.point
            sl_points = 100  # 100 points SL
            tp_points = 200  # 200 points TP (2:1 risk-reward)
            
            if order_type == "BUY":
                sl = price - sl_points * point
                tp = price + tp_points * point
            else:  # SELL
                sl = price + sl_points * point
                tp = price - tp_points * point
            
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": self.lot_size,
                "type": order_type_mt5,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Alligator {order_type}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            if result is None:
                logger.error("Order send failed, no result")
                return False
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order send failed, retcode: {result.retcode}")
                return False
            
            logger.info(f"{order_type} position opened successfully. Ticket: {result.order}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return False
    
    def close_positions(self) -> bool:
        """Close all open positions"""
        try:
            positions = self.get_open_positions()
            if not positions:
                logger.info("No open positions to close")
                return True
            
            success = True
            for position in positions:
                # Determine close order type
                if position.type == mt5.POSITION_TYPE_BUY:
                    order_type = mt5.ORDER_TYPE_SELL
                    price = mt5.symbol_info_tick(self.symbol).bid
                else:  # POSITION_TYPE_SELL
                    order_type = mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(self.symbol).ask
                
                # Create close request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": self.symbol,
                    "volume": position.volume,
                    "type": order_type,
                    "position": position.ticket,
                    "price": price,
                    "deviation": 20,
                    "magic": 234000,
                    "comment": "Alligator Close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                # Send close order
                result = mt5.order_send(request)
                if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                    logger.error(f"Failed to close position {position.ticket}")
                    success = False
                else:
                    logger.info(f"Position {position.ticket} closed successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
            return False
    
    def execute_strategy(self):
        """Execute the trading strategy"""
        try:
            # Get current indicators
            indicators = self.get_current_indicators()
            if indicators is None:
                logger.error("Failed to get indicators")
                return
            
            # Get AI decision
            decision = self.get_ai_decision(indicators)
            
            # Get current positions
            positions = self.get_open_positions()
            has_positions = len(positions) > 0
            
            # Execute based on decision
            if decision == 'OPEN_BUY' and not has_positions:
                logger.info("Opening BUY position")
                self.open_position("BUY")
            elif decision == 'OPEN_SELL' and not has_positions:
                logger.info("Opening SELL position")
                self.open_position("SELL")
            elif decision == 'CLOSE_POSITION' and has_positions:
                logger.info("Closing positions")
                self.close_positions()
            elif decision == 'HOLD':
                logger.info("Holding current position")
            else:
                logger.info(f"No action taken. Decision: {decision}, Has positions: {has_positions}")
            
            # Log current state
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"Account Balance: {account_info.balance}, Equity: {account_info.equity}")
            
        except Exception as e:
            logger.error(f"Error executing strategy: {e}")
    
    def run(self):
        """Main trading loop"""
        logger.info("Starting Alligator trading strategy")
        
        # Initialize MT5
        if not self.initialize_mt5():
            logger.error("Failed to initialize MT5")
            return
        
        try:
            while True:
                # Execute strategy
                self.execute_strategy()
                
                # Wait before next iteration (30 seconds)
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("Stopping strategy...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            mt5.shutdown()
            logger.info("MT5 shutdown completed")

if __name__ == "__main__":
    strategy = AlligatorStrategy()
    strategy.run()