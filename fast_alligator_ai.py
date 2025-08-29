import MetaTrader5 as mt5
import pandas as pd
import json
import time
import logging
from datetime import datetime
import ollama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fast_alligator_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FastAlligatorAIStrategy:
    """
    Fast Alligator trading strategy with Ollama AI integration
    Optimized for speed and real-time decision making
    """
    
    def __init__(self, config_file: str = "alligator_trading_config.json"):
        """Initialize the fast strategy with configuration"""
        self.config = self.load_config(config_file)
        self.symbol = self.config["trading"]["symbol"]
        self.timeframe = getattr(mt5, f"TIMEFRAME_{self.config['trading']['timeframe']}")
        self.lot_size = self.config["trading"]["lot_size"]
        
        # Initialize Ollama configuration
        self.ollama_model = self.config["ollama"]["model"]
        self.ollama_timeout = self.config["ollama"]["timeout"]
        self.ollama_temperature = self.config["ollama"]["temperature"]
        
        logger.info("FastAlligatorAIStrategy initialized")
    
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
                
            logger.info(f"MT5 initialized. Account: {account_info.login}, Balance: {account_info.balance}")
            return True
        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False
    
    def get_latest_prices(self) -> tuple:
        """Get the latest bid and ask prices"""
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                logger.error("Failed to get tick data")
                return None, None
            return tick.bid, tick.ask
        except Exception as e:
            logger.error(f"Error getting latest prices: {e}")
            return None, None
    
    def get_recent_bars(self, count: int = 20) -> pd.DataFrame:
        """Get recent OHLC bars"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, count)
            if rates is None:
                logger.error("Failed to get market data")
                return None
            
            df = pd.DataFrame(rates)
            return df
        except Exception as e:
            logger.error(f"Error getting recent bars: {e}")
            return None
    
    def calculate_simple_alligator(self, df: pd.DataFrame) -> dict:
        """Calculate simplified Alligator indicators"""
        try:
            # Use shorter periods for faster calculation
            jaw = df['close'].rolling(5).mean().iloc[-1]  # Shortened from 13
            teeth = df['close'].rolling(3).mean().iloc[-1]  # Shortened from 8
            lips = df['close'].rolling(2).mean().iloc[-1]  # Shortened from 5
            
            return {
                'jaw': float(jaw),
                'teeth': float(teeth),
                'lips': float(lips)
            }
        except Exception as e:
            logger.error(f"Error calculating simple alligator: {e}")
            return {'jaw': 0, 'teeth': 0, 'lips': 0}
    
    def get_fast_ai_decision(self, price: float, alligator: dict) -> str:
        """Get fast trading decision from Ollama AI"""
        try:
            # Create a very concise prompt for speed
            def format_value(value, precision=5):
                """Format numeric value or return 'N/A' if None"""
                if value is None:
                    return 'N/A'
                return f"{value:.{precision}f}"
            
            prompt = f"""
            EURUSD={format_value(price, 5)} JAW={format_value(alligator['jaw'], 5)} TEETH={format_value(alligator['teeth'], 5)} LIPS={format_value(alligator['lips'], 5)}
            RULES: LIPS>TEETH>JAW=BUY, LIPS<TEETH<JAW=SELL, ELSE=HOLD
            RESPOND: BUY/SELL/HOLD ONLY
            """
            
            # Get decision from Ollama with minimal parameters for speed
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
            if decision not in ['BUY', 'SELL', 'HOLD']:
                logger.warning(f"Invalid decision from AI: {decision}. Using HOLD.")
                return 'HOLD'
            
            logger.info(f"AI Decision: {decision}")
            return decision
            
        except Exception as e:
            logger.error(f"Error getting AI decision: {e}")
            return 'HOLD'  # Default to HOLD on error
    
    def get_open_positions(self) -> list:
        """Get currently open positions"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            return list(positions) if positions else []
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []
    
    def open_position(self, order_type: str) -> bool:
        """Open a new position quickly"""
        try:
            # Get current price
            bid, ask = self.get_latest_prices()
            if bid is None or ask is None:
                logger.error("Failed to get current prices")
                return False
            
            # Prepare order request
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                logger.error(f"Failed to get symbol info for {self.symbol}")
                return False
            
            # Determine order type and price
            if order_type == "BUY":
                price = ask
                order_type_mt5 = mt5.ORDER_TYPE_BUY
            else:  # SELL
                price = bid
                order_type_mt5 = mt5.ORDER_TYPE_SELL
            
            # Create order request with minimal parameters for speed
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": self.lot_size,
                "type": order_type_mt5,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": f"FastAI {order_type}",
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
        """Close all open positions quickly"""
        try:
            positions = self.get_open_positions()
            if not positions:
                return True
            
            success = True
            for position in positions:
                # Get current price for closing
                bid, ask = self.get_latest_prices()
                if bid is None or ask is None:
                    logger.error("Failed to get current prices for closing")
                    success = False
                    continue
                
                # Determine close order type
                if position.type == mt5.POSITION_TYPE_BUY:
                    order_type = mt5.ORDER_TYPE_SELL
                    price = bid
                else:  # POSITION_TYPE_SELL
                    order_type = mt5.ORDER_TYPE_BUY
                    price = ask
                
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
                    "comment": "FastAI Close",
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
    
    def execute_fast_strategy(self):
        """Execute the fast trading strategy"""
        try:
            # Get latest price
            bid, ask = self.get_latest_prices()
            if bid is None or ask is None:
                logger.error("Failed to get latest prices")
                return
            
            current_price = (bid + ask) / 2
            
            # Get recent bars for Alligator calculation
            df = self.get_recent_bars(20)
            if df is None or len(df) < 5:
                logger.error("Insufficient data for Alligator calculation")
                return
            
            # Calculate simplified Alligator
            alligator = self.calculate_simple_alligator(df)
            
            # Get AI decision
            decision = self.get_fast_ai_decision(current_price, alligator)
            
            # Get current positions
            positions = self.get_open_positions()
            has_positions = len(positions) > 0
            
            # Execute based on decision
            if decision == 'BUY' and not has_positions:
                logger.info("Opening BUY position")
                self.open_position("BUY")
            elif decision == 'SELL' and not has_positions:
                logger.info("Opening SELL position")
                self.open_position("SELL")
            elif decision == 'HOLD' and has_positions:
                logger.info("Closing positions")
                self.close_positions()
            else:
                logger.info(f"Holding. Decision: {decision}, Has positions: {has_positions}")
            
            # Log account info periodically
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"Balance: {account_info.balance}, Equity: {account_info.equity}")
            
        except Exception as e:
            logger.error(f"Error executing fast strategy: {e}")
    
    def run(self):
        """Main fast trading loop"""
        logger.info("Starting Fast Alligator AI trading strategy")
        
        # Initialize MT5
        if not self.initialize_mt5():
            logger.error("Failed to initialize MT5")
            return
        
        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"Iteration {iteration}")
                
                # Execute strategy
                self.execute_fast_strategy()
                
                # Log account info every 10 iterations
                if iteration % 10 == 0:
                    account_info = mt5.account_info()
                    if account_info:
                        logger.info(f"Account Update - Balance: {account_info.balance}, Equity: {account_info.equity}")
                
                # Wait before next iteration (15 seconds for fast trading)
                time.sleep(15)
                
        except KeyboardInterrupt:
            logger.info("Stopping fast strategy...")
        except Exception as e:
            logger.error(f"Error in fast strategy loop: {e}")
        finally:
            mt5.shutdown()
            logger.info("MT5 shutdown completed")

if __name__ == "__main__":
    strategy = FastAlligatorAIStrategy()
    strategy.run()