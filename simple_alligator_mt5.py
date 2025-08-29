#!/usr/bin/env python3
"""
Simple live trading script using Alligator strategy with MT5
"""

import logging
import time
import sys
from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mt5_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SimpleAlligatorStrategy:
    """
    A simple Alligator strategy implementation
    """
    
    def __init__(self, symbol="EURUSD", timeframe=mt5.TIMEFRAME_M1):
        self.symbol = symbol
        self.timeframe = timeframe
        self.jaw_period = 13
        self.jaw_shift = 8
        self.teeth_period = 8
        self.teeth_shift = 5
        self.lips_period = 5
        self.lips_shift = 3
        self.lot_size = 0.1
        self.sl_points = 100
        self.tp_points = 100
        self.position = None  # None, "BUY", "SELL"
        self.last_signal = None
        
    def calculate_sma(self, data, period):
        """
        Calculate Simple Moving Average
        """
        return data.rolling(window=period).mean()
    
    def calculate_alligator(self, close_prices):
        """
        Calculate Alligator Indicator
        """
        # Jaw (Blue) - 13 periods, shifted 8 bars into the future
        jaw = self.calculate_sma(close_prices, self.jaw_period)
        jaw = jaw.shift(self.jaw_shift)
        
        # Teeth (Red) - 8 periods, shifted 5 bars into the future
        teeth = self.calculate_sma(close_prices, self.teeth_period)
        teeth = teeth.shift(self.teeth_shift)
        
        # Lips (Green) - 5 periods, shifted 3 bars into the future
        lips = self.calculate_sma(close_prices, self.lips_period)
        lips = lips.shift(self.lips_shift)
        
        return jaw, teeth, lips
    
    def get_market_data(self, count=100):
        """
        Get market data from MT5
        """
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, count)
        if rates is None:
            logger.error(f"Failed to get market data: {mt5.last_error()}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def generate_signals(self, df):
        """
        Generate trading signals based on Alligator indicator
        """
        # Calculate the Alligator indicator
        jaw, teeth, lips = self.calculate_alligator(df['close'])
        
        # Add to DataFrame
        df['jaw'] = jaw
        df['teeth'] = teeth
        df['lips'] = lips
        
        # Check if we have enough data
        if len(df) < max(self.jaw_shift, self.teeth_shift, self.lips_shift):
            return None
            
        # Get last values
        last_close = df['close'].iloc[-1]
        last_jaw = df['jaw'].iloc[-1]
        last_teeth = df['teeth'].iloc[-1]
        last_lips = df['lips'].iloc[-1]
        
        # Check if all indicators have values
        if pd.isna(last_jaw) or pd.isna(last_teeth) or pd.isna(last_lips):
            return None
            
        # Buy signal: Price above all lines and ascending order (lips > teeth > jaw)
        if (last_close > last_lips > last_teeth > last_jaw):
            return "BUY"
            
        # Sell signal: Price below all lines and descending order (lips < teeth < jaw)
        elif (last_close < last_lips < last_teeth < last_jaw):
            return "SELL"
            
        return "HOLD"
    
    def get_open_positions(self):
        """
        Get open positions from MT5
        """
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            logger.error(f"Failed to get positions: {mt5.last_error()}")
            return []
        return positions
    
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
            "comment": "Alligator Strategy Close",
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
    
    def open_position(self, signal):
        """
        Open a new position
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
        
        # Get current price
        if signal == "BUY":
            price = mt5.symbol_info_tick(self.symbol).ask
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = mt5.symbol_info_tick(self.symbol).bid
            order_type = mt5.ORDER_TYPE_SELL
            
        # Calculate SL and TP
        point = symbol_info.point
        if signal == "BUY":
            sl = price - self.sl_points * point
            tp = price + self.tp_points * point
        else:
            sl = price + self.sl_points * point
            tp = price - self.tp_points * point
            
        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Alligator Strategy {signal}",
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
            
        logger.info(f"{signal} order placed successfully: {self.lot_size} {self.symbol} at {price}")
        return True
    
    def execute_strategy(self):
        """
        Execute the Alligator strategy
        """
        # Get market data
        df = self.get_market_data()
        if df is None or len(df) < 20:  # Need enough data for indicators
            return
            
        # Generate signal
        signal = self.generate_signals(df)
        if signal is None or signal == "HOLD":
            return
            
        # Check if we already have a position
        positions = self.get_open_positions()
        
        # If we have a position
        if len(positions) > 0:
            position = positions[0]
            
            # Close position if signal is opposite
            if (position.type == mt5.POSITION_TYPE_BUY and signal == "SELL") or \
               (position.type == mt5.POSITION_TYPE_SELL and signal == "BUY"):
                logger.info(f"Closing {position.type} position due to opposite signal")
                self.close_position(position)
                # Open new position after a short delay
                time.sleep(1)
                self.open_position(signal)
                
        # If we don't have a position
        elif len(positions) == 0:
            # Open new position
            logger.info(f"Opening new {signal} position")
            self.open_position(signal)


def initialize_mt5():
    """
    Initialize MT5 connection
    """
    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    logger.info("MT5 initialized successfully")
    return True


def get_account_info():
    """
    Get MT5 account information
    """
    account_info = mt5.account_info()
    if account_info is None:
        logger.error(f"Failed to get account info: {mt5.last_error()}")
        return None
    return account_info


def main():
    """
    Main function
    """
    logger.info("Starting Alligator strategy live trading")
    
    # Initialize MT5
    if not initialize_mt5():
        return
    
    # Get account info
    account_info = get_account_info()
    if account_info is None:
        mt5.shutdown()
        return
    
    logger.info(f"Connected to MT5 account {account_info.login}")
    logger.info(f"Balance: {account_info.balance} {account_info.currency}")
    logger.info(f"Equity: {account_info.equity} {account_info.currency}")
    
    # Create strategy instance
    strategy = SimpleAlligatorStrategy(symbol="EURUSD", timeframe=mt5.TIMEFRAME_M1)
    
    try:
        # Run the strategy loop
        while True:
            # Execute strategy
            strategy.execute_strategy()
            
            # Log account info every 10 iterations
            if int(time.time()) % 600 == 0:  # Every 10 minutes
                account_info = get_account_info()
                if account_info:
                    logger.info(f"Account Balance: {account_info.balance} {account_info.currency}")
                    logger.info(f"Account Equity: {account_info.equity} {account_info.currency}")
                    logger.info(f"Margin: {account_info.margin} {account_info.currency}")
                    logger.info(f"Free Margin: {account_info.margin_free} {account_info.currency}")
            
            # Wait for next iteration (1 minute)
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Stopping strategy...")
    except Exception as e:
        logger.error(f"Error in strategy execution: {e}")
    finally:
        # Shutdown MT5
        mt5.shutdown()
        logger.info("MT5 connection closed")


if __name__ == "__main__":
    main()