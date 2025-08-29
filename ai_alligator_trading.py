#!/usr/bin/env python3
"""
AI-Powered Alligator Strategy using Ollama local agent
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
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class OllamaAgent:
    """
    Ollama AI Agent for trading decisions
    """
    
    def __init__(self, model: str = "llama3", host: str = "localhost", port: int = 11434):
        self.model = model
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}/api/generate"
        
    def generate_prompt(self, market_data: Dict[str, Any], positions: list, account_info: Dict[str, Any]) -> str:
        """
        Generate prompt for the AI agent
        """
        prompt = f"""
        You are an expert forex trader specializing in the Alligator strategy. 
        Analyze the following market data and make a trading decision.
        
        Current Market Data:
        - Symbol: {market_data.get('symbol', 'EURUSD')}
        - Current Price: {market_data.get('current_price', 0)}
        - Alligator Jaw: {market_data.get('jaw', 0)}
        - Alligator Teeth: {market_data.get('teeth', 0)}
        - Alligator Lips: {market_data.get('lips', 0)}
        - Price Position: {market_data.get('price_position', 'neutral')}
        - Trend Strength: {market_data.get('trend_strength', 'weak')}
        
        Account Information:
        - Balance: {account_info.get('balance', 0)}
        - Equity: {account_info.get('equity', 0)}
        - Free Margin: {account_info.get('free_margin', 0)}
        - Margin Level: {account_info.get('margin_level', 0)}%
        
        Open Positions:
        - Number of positions: {len(positions)}
        {f"- Position 1: {positions[0].type_str} {positions[0].volume} lots" if positions else "- No open positions"}
        
        Based on this information, should we:
        1. OPEN_BUY - Open a new buy position
        2. OPEN_SELL - Open a new sell position
        3. CLOSE_POSITION - Close existing position
        4. HOLD - Do nothing
        
        Consider:
        - Risk management
        - Current market conditions
        - Account equity preservation
        - Position sizing relative to account size
        
        Respond ONLY with one of these exact words: OPEN_BUY, OPEN_SELL, CLOSE_POSITION, HOLD
        """
        
        return prompt
    
    def get_decision(self, market_data: Dict[str, Any], positions: list, account_info: Dict[str, Any]) -> str:
        """
        Get trading decision from Ollama agent
        """
        try:
            prompt = self.generate_prompt(market_data, positions, account_info)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 100
            }
            
            response = requests.post(self.url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                decision = result.get('response', '').strip().upper()
                
                # Validate decision
                valid_decisions = ['OPEN_BUY', 'OPEN_SELL', 'CLOSE_POSITION', 'HOLD']
                if decision in valid_decisions:
                    logger.info(f"AI Decision: {decision}")
                    return decision
                else:
                    logger.warning(f"Invalid AI decision: {decision}, defaulting to HOLD")
                    return "HOLD"
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "HOLD"
                
        except Exception as e:
            logger.error(f"Error getting AI decision: {e}")
            return "HOLD"


class EnhancedAlligatorStrategy:
    """
    Enhanced Alligator strategy with AI decision making
    """
    
    def __init__(self, symbol="EURUSD", timeframe=mt5.TIMEFRAME_M1, model="llama3"):
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
        self.max_risk_percent = 2.0  # Maximum 2% of equity per trade
        
        # Initialize Ollama agent
        self.ai_agent = OllamaAgent(model=model)
        
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
    
    def analyze_market_context(self, df):
        """
        Analyze market context for AI agent
        """
        # Calculate the Alligator indicator
        jaw, teeth, lips = self.calculate_alligator(df['close'])
        
        # Add to DataFrame
        df['jaw'] = jaw
        df['teeth'] = teeth
        df['lips'] = lips
        
        # Get last values
        last_close = df['close'].iloc[-1]
        last_jaw = df['jaw'].iloc[-1]
        last_teeth = df['teeth'].iloc[-1]
        last_lips = df['lips'].iloc[-1]
        
        # Determine price position
        if pd.isna(last_jaw) or pd.isna(last_teeth) or pd.isna(last_lips):
            price_position = "insufficient_data"
        elif last_close > last_lips > last_teeth > last_jaw:
            price_position = "above_alligator_bullish"
        elif last_close < last_lips < last_teeth < last_jaw:
            price_position = "below_alligator_bearish"
        else:
            price_position = "within_alligator_neutral"
        
        # Calculate trend strength
        # Simple measure: distance between lines
        if not (pd.isna(last_jaw) or pd.isna(last_teeth) or pd.isna(last_lips)):
            alignment = abs((last_lips - last_teeth) + (last_teeth - last_jaw))
            if alignment > (last_close * 0.001):  # 0.1% of price
                trend_strength = "strong"
            elif alignment > (last_close * 0.0005):  # 0.05% of price
                trend_strength = "moderate"
            else:
                trend_strength = "weak"
        else:
            trend_strength = "insufficient_data"
        
        return {
            "symbol": self.symbol,
            "current_price": float(last_close),
            "jaw": float(last_jaw) if not pd.isna(last_jaw) else 0,
            "teeth": float(last_teeth) if not pd.isna(last_teeth) else 0,
            "lips": float(last_lips) if not pd.isna(last_lips) else 0,
            "price_position": price_position,
            "trend_strength": trend_strength
        }
    
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
    
    def get_open_positions(self):
        """
        Get open positions from MT5
        """
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            logger.error(f"Failed to get positions: {mt5.last_error()}")
            return []
        return positions
    
    def calculate_position_size(self, account_equity: float, stop_loss_pips: float) -> float:
        """
        Calculate position size based on risk management
        """
        # Risk 2% of equity
        risk_amount = account_equity * (self.max_risk_percent / 100)
        
        # Get symbol info for pip value
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            return self.lot_size  # Default to fixed size if error
            
        # Approximate pip value (this is simplified)
        pip_value = symbol_info.point * 100000  # For most currency pairs
        if "JPY" in self.symbol:
            pip_value = symbol_info.point * 1000  # For JPY pairs
            
        # Calculate lot size
        if stop_loss_pips > 0:
            lot_size = risk_amount / (stop_loss_pips * pip_value)
            # Limit to reasonable lot sizes
            lot_size = min(lot_size, 1.0)  # Max 1 lot
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
            "comment": "AI Alligator Strategy Close",
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
        
        # Get account info for position sizing
        account_info = self.get_account_info()
        if account_info is None:
            return False
            
        # Calculate dynamic position size
        lot_size = self.calculate_position_size(account_info["equity"], self.sl_points)
        logger.info(f"Calculated lot size: {lot_size} (account equity: {account_info['equity']})")
        
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
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": f"AI Alligator Strategy {signal}",
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
        return True
    
    def execute_strategy(self):
        """
        Execute the enhanced Alligator strategy with AI
        """
        # Get market data
        df = self.get_market_data()
        if df is None or len(df) < 20:  # Need enough data for indicators
            return
            
        # Analyze market context
        market_context = self.analyze_market_context(df)
        
        # Get account info
        account_info = self.get_account_info()
        if account_info is None:
            return
            
        # Get open positions
        positions = self.get_open_positions()
        
        # Get AI decision
        decision = self.ai_agent.get_decision(market_context, positions, account_info)
        
        # Execute decision
        if decision == "OPEN_BUY" and len(positions) == 0:
            logger.info("AI decided to OPEN_BUY")
            self.open_position("BUY")
        elif decision == "OPEN_SELL" and len(positions) == 0:
            logger.info("AI decided to OPEN_SELL")
            self.open_position("SELL")
        elif decision == "CLOSE_POSITION" and len(positions) > 0:
            logger.info("AI decided to CLOSE_POSITION")
            for position in positions:
                self.close_position(position)
        elif decision == "HOLD":
            logger.info("AI decided to HOLD - no action taken")


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
    logger.info("Starting AI-Powered Alligator strategy live trading")
    
    # Initialize MT5
    if not initialize_mt5():
        return
    
    # Test Ollama connection
    try:
        ai_agent = OllamaAgent()
        test_prompt = "Hello, are you working?"
        payload = {
            "model": "llama3",
            "prompt": test_prompt,
            "stream": False
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
    
    # Create strategy instance
    strategy = EnhancedAlligatorStrategy(symbol="EURUSD", timeframe=mt5.TIMEFRAME_M1, model="llama3")
    
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