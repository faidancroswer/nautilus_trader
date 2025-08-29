#!/usr/bin/env python3
"""
Continuous Learning AI Trading System
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
from typing import Dict, Any, List, Optional
import pickle
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('learning_ai_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TradeMemory:
    """
    Memory system for storing and retrieving trade experiences
    """
    
    def __init__(self, memory_file: str = "trade_memory.pkl"):
        self.memory_file = memory_file
        self.trades = []
        self.load_memory()
        
    def load_memory(self):
        """Load memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'rb') as f:
                    self.trades = pickle.load(f)
                logger.info(f"Loaded {len(self.trades)} trades from memory")
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
            self.trades = []
    
    def save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'wb') as f:
                pickle.dump(self.trades, f)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def add_trade(self, trade_data: Dict[str, Any]):
        """Add a trade to memory"""
        trade_data['timestamp'] = datetime.now()
        self.trades.append(trade_data)
        # Keep only last 1000 trades
        if len(self.trades) > 1000:
            self.trades = self.trades[-1000:]
        self.save_memory()
    
    def get_recent_trades(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent trades"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [trade for trade in self.trades if trade['timestamp'] > cutoff_time]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.trades:
            return {}
        
        profits = [trade.get('profit', 0) for trade in self.trades if 'profit' in trade]
        if not profits:
            return {}
        
        return {
            'total_trades': len(profits),
            'winning_trades': len([p for p in profits if p > 0]),
            'losing_trades': len([p for p in profits if p < 0]),
            'win_rate': len([p for p in profits if p > 0]) / len(profits) * 100,
            'average_profit': np.mean(profits),
            'total_profit': np.sum(profits),
            'max_profit': np.max(profits),
            'max_loss': np.min(profits)
        }


class ContinuousLearningAgent:
    """
    AI Agent with continuous learning capabilities
    """
    
    def __init__(self, model: str = "llama3", host: str = "localhost", port: int = 11434):
        self.model = model
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}/api/generate"
        self.memory = TradeMemory()
        self.performance_stats = self.memory.get_performance_stats()
        
    def update_performance_stats(self):
        """Update performance statistics"""
        self.performance_stats = self.memory.get_performance_stats()
        
    def create_learning_prompt(self, market_analysis: Dict[str, Any], recent_performance: Dict[str, Any]) -> str:
        """
        Create prompt that includes learning from past trades
        """
        prompt = f"""
        You are an advanced forex trading AI with continuous learning capabilities.
        You have access to your recent trading performance and market analysis.
        
        Recent Trading Performance (last 24 hours):
        - Total Trades: {recent_performance.get('total_trades', 0)}
        - Win Rate: {recent_performance.get('win_rate', 0):.1f}%
        - Average Profit: ${recent_performance.get('average_profit', 0):.2f}
        - Total Profit: ${recent_performance.get('total_profit', 0):.2f}
        
        Current Market Analysis:
        Symbol: {market_analysis.get('symbol', 'EURUSD')}
        Current Price: {market_analysis.get('current_price', 0):.5f}
        Alligator Alignment: {market_analysis.get('alligator_alignment', 'neutral')}
        RSI (14): {market_analysis.get('rsi', 50):.2f}
        Market Volatility: {market_analysis.get('volatility', 0):.5f}
        
        Based on your recent performance and current market conditions, 
        adjust your trading approach to improve results.
        
        Consider:
        1. What strategies worked well recently?
        2. What strategies underperformed?
        3. How should you adapt to current market conditions?
        4. Risk management based on recent performance
        
        Make a trading decision considering:
        - OPEN_BUY: Open a long position
        - OPEN_SELL: Open a short position  
        - CLOSE_POSITION: Close existing position(s)
        - HOLD: Do nothing
        - ADJUST_STRATEGY: Modify approach based on learning
        
        Respond ONLY with one of these exact actions: OPEN_BUY, OPEN_SELL, CLOSE_POSITION, HOLD, ADJUST_STRATEGY
        """
        
        return prompt
    
    def get_decision(self, market_analysis: Dict[str, Any]) -> str:
        """
        Get trading decision with continuous learning
        """
        try:
            # Update performance stats
            self.update_performance_stats()
            
            # Create learning prompt
            prompt = self.create_learning_prompt(market_analysis, self.performance_stats)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,  # Higher temperature for creative learning
                "top_p": 0.9,
                "max_tokens": 200
            }
            
            response = requests.post(self.url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                decision = result.get('response', '').strip().upper()
                
                # Validate decision
                valid_decisions = ['OPEN_BUY', 'OPEN_SELL', 'CLOSE_POSITION', 'HOLD', 'ADJUST_STRATEGY']
                if decision in valid_decisions:
                    logger.info(f"AI Learning Decision: {decision}")
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
    
    def record_trade_result(self, trade_data: Dict[str, Any]):
        """
        Record trade result for learning
        """
        self.memory.add_trade(trade_data)
        logger.info(f"Recorded trade result: {trade_data}")


class LearningAlligatorStrategy:
    """
    Alligator strategy with continuous learning
    """
    
    def __init__(self, symbol="EURUSD", timeframe=mt5.TIMEFRAME_M1, model="llama3"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.lot_size = 0.1
        self.sl_points = 100
        self.tp_points = 100
        self.max_risk_percent = 1.0
        
        # Initialize learning agent
        self.ai_agent = ContinuousLearningAgent(model=model)
        
        # Track open trades
        self.open_trades = {}
        
    def calculate_sma(self, data, period):
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    def analyze_market(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive market analysis
        """
        # Alligator calculation
        jaw = self.calculate_sma(df['close'], 13).shift(8)
        teeth = self.calculate_sma(df['close'], 8).shift(5)
        lips = self.calculate_sma(df['close'], 5).shift(3)
        
        current_price = df['close'].iloc[-1]
        last_jaw, last_teeth, last_lips = jaw.iloc[-1], teeth.iloc[-1], lips.iloc[-1]
        
        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Volatility (ATR)
        tr = np.maximum(df['high'] - df['low'], 
                       np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean().iloc[-1]
        
        return {
            "symbol": self.symbol,
            "current_price": float(current_price),
            "alligator_jaw": float(last_jaw) if not pd.isna(last_jaw) else 0,
            "alligator_teeth": float(last_teeth) if not pd.isna(last_teeth) else 0,
            "alligator_lips": float(last_lips) if not pd.isna(last_lips) else 0,
            "alligator_alignment": "bullish" if current_price > last_lips > last_teeth > last_jaw else 
                                 "bearish" if current_price < last_lips < last_teeth < last_jaw else "neutral",
            "rsi": float(current_rsi),
            "volatility": float(atr),
            "timestamp": datetime.now()
        }
    
    def get_market_data(self, count=100):
        """Get market data from MT5"""
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, count)
        if rates is None:
            logger.error(f"Failed to get market data: {mt5.last_error()}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def get_account_info(self):
        """Get account information"""
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
        """Get open positions from MT5"""
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            logger.error(f"Failed to get positions: {mt5.last_error()}")
            return []
        return positions
    
    def calculate_position_size(self, account_equity: float, volatility: float) -> float:
        """Calculate dynamic position size"""
        risk_amount = account_equity * (self.max_risk_percent / 100)
        
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            return self.lot_size
            
        volatility_multiplier = max(0.5, min(2.0, 1.0 / (volatility * 1000)))
        adjusted_risk = risk_amount * volatility_multiplier
        
        pip_value = symbol_info.point * 100000
        if "JPY" in self.symbol:
            pip_value = symbol_info.point * 1000
            
        if self.sl_points > 0:
            lot_size = adjusted_risk / (self.sl_points * pip_value)
            lot_size = min(lot_size, 0.3)  # Max 0.3 lot
            lot_size = max(lot_size, 0.01)  # Min 0.01 lot
            return round(lot_size, 2)
        else:
            return self.lot_size
    
    def close_position(self, position):
        """Close an open position"""
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
            "comment": "Learning AI Alligator Strategy Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        result = mt5.order_send(request)
        if result is None:
            logger.error(f"Failed to close position: {mt5.last_error()}")
            return False
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Close order failed with retcode {result.retcode}")
            return False
            
        # Record trade result
        if position.ticket in self.open_trades:
            trade_data = self.open_trades[position.ticket]
            trade_data['close_time'] = datetime.now()
            trade_data['close_price'] = price
            trade_data['profit'] = (price - trade_data['open_price']) * trade_data['volume'] * 100000 if position.type == mt5.POSITION_TYPE_BUY else \
                                  (trade_data['open_price'] - price) * trade_data['volume'] * 100000
            self.ai_agent.record_trade_result(trade_data)
            del self.open_trades[position.ticket]
            
        logger.info(f"Position {position.ticket} closed successfully")
        return True
    
    def open_position(self, signal, market_analysis: Dict[str, Any]):
        """Open a new position"""
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            logger.error(f"Failed to get symbol info: {mt5.last_error()}")
            return False
            
        if not symbol_info.visible:
            if not mt5.symbol_select(self.symbol, True):
                logger.error(f"Failed to select symbol {self.symbol}: {mt5.last_error()}")
                return False
        
        account_info = self.get_account_info()
        if account_info is None:
            return False
            
        lot_size = self.calculate_position_size(account_info["equity"], market_analysis["volatility"])
        logger.info(f"Calculated lot size: {lot_size}")
        
        if signal == "BUY":
            price = mt5.symbol_info_tick(self.symbol).ask
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = mt5.symbol_info_tick(self.symbol).bid
            order_type = mt5.ORDER_TYPE_SELL
            
        point = symbol_info.point
        if signal == "BUY":
            sl = price - self.sl_points * point
            tp = price + self.tp_points * point
        else:
            sl = price + self.sl_points * point
            tp = price - self.tp_points * point
            
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
            "comment": f"Learning AI Alligator Strategy {signal}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        result = mt5.order_send(request)
        if result is None:
            logger.error(f"Failed to send order: {mt5.last_error()}")
            return False
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed with retcode {result.retcode}")
            return False
            
        # Track open trade
        trade_data = {
            "ticket": result.order,
            "symbol": self.symbol,
            "type": signal,
            "volume": lot_size,
            "open_price": price,
            "open_time": datetime.now(),
            "sl": sl,
            "tp": tp,
            "market_conditions": market_analysis
        }
        self.open_trades[result.order] = trade_data
            
        logger.info(f"{signal} order placed successfully: {lot_size} {self.symbol} at {price}")
        return True
    
    def execute_strategy(self):
        """Execute the learning strategy"""
        df = self.get_market_data()
        if df is None or len(df) < 50:
            return
            
        account_info = self.get_account_info()
        if account_info is None:
            return
            
        positions = self.get_open_positions()
        
        # Analyze market
        market_analysis = self.analyze_market(df)
        
        # Get AI decision
        decision = self.ai_agent.get_decision(market_analysis)
        
        # Execute decision
        if decision == "OPEN_BUY" and len(positions) == 0:
            logger.info("AI decided to OPEN_BUY")
            self.open_position("BUY", market_analysis)
        elif decision == "OPEN_SELL" and len(positions) == 0:
            logger.info("AI decided to OPEN_SELL")
            self.open_position("SELL", market_analysis)
        elif decision == "CLOSE_POSITION" and len(positions) > 0:
            logger.info("AI decided to CLOSE_POSITION")
            for position in positions:
                self.close_position(position)
        elif decision == "ADJUST_STRATEGY":
            logger.info("AI decided to ADJUST_STRATEGY - adapting approach based on learning")
        elif decision == "HOLD":
            logger.info("AI decided to HOLD - no action taken")


def initialize_mt5():
    """Initialize MT5 connection"""
    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    logger.info("MT5 initialized successfully")
    return True


def main():
    """Main function"""
    logger.info("Starting Continuous Learning AI-Powered Alligator strategy")
    
    # Initialize MT5
    if not initialize_mt5():
        return
    
    # Test Ollama connection
    try:
        agent = ContinuousLearningAgent()
        test_payload = {
            "model": "llama3",
            "prompt": "Test connection to learning AI",
            "stream": False,
            "max_tokens": 50
        }
        response = requests.post(agent.url, json=test_payload, timeout=10)
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
    strategy = LearningAlligatorStrategy(symbol="EURUSD", timeframe=mt5.TIMEFRAME_M1, model="llama3")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"Strategy iteration {iteration}")
            
            # Execute strategy
            strategy.execute_strategy()
            
            # Log performance every 10 iterations
            if iteration % 10 == 0:
                stats = strategy.ai_agent.memory.get_performance_stats()
                if stats:
                    logger.info(f"Performance Stats: {stats}")
                else:
                    logger.info("No performance data yet")
            
            # Wait for next iteration (1 minute)
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Stopping strategy...")
    except Exception as e:
        logger.error(f"Error in strategy execution: {e}")
        logger.exception(e)
    finally:
        mt5.shutdown()
        logger.info("MT5 connection closed")


if __name__ == "__main__":
    main()