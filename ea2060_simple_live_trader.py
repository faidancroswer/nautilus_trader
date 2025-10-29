#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EA2060 Simple Live Trader
Real Account Trading - Simplified Version
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ea2060_simple_live.log'),
        logging.StreamHandler()
    ]
)

class SimpleLiveConfig:
    """Simple live trading configuration"""
    SYMBOL = "XAUUSD"
    RISK_PER_TRADE = 0.5  # 0.5% risk per trade
    MAX_POSITIONS = 3     # Conservative for live
    STOP_LOSS_PIPS = 500  # Fixed stop loss
    TAKE_PROFIT_PIPS = 800  # Fixed take profit
    TRADING_HOURS_START = 8
    TRADING_HOURS_END = 18
    MAX_SPREAD_POINTS = 50
    EMA_FAST = 5
    EMA_SLOW = 20

class EA2060SimpleLiveTrader:
    """Simple live trading system"""

    def __init__(self):
        self.config = SimpleLiveConfig()
        self.positions = {}
        self.magic_number = 30001
        self.running = True

        logging.info("EA2060 Simple Live Trader Initialized")

    def connect_mt5(self):
        """Connect to MetaTrader 5"""
        try:
            if not mt5.initialize():
                logging.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False

            account_info = mt5.account_info()
            if account_info is None:
                logging.error("Failed to get account info")
                return False

            logging.info(f"[+] Connected to MT5 - Account: {account_info.login} (${account_info.balance:.2f})")
            return True

        except Exception as e:
            logging.error(f"Connection error: {e}")
            return False

    def calculate_position_size(self):
        """Calculate simple position size based on risk"""
        try:
            account_info = mt5.account_info()
            balance = account_info.balance
            risk_amount = balance * (self.config.RISK_PER_TRADE / 100)

            # Simple calculation: risk amount / stop loss in dollars
            position_size = risk_amount / (self.config.STOP_LOSS_PIPS * 0.1)  # Approximate $0.1 per pip for gold
            position_size = round(position_size, 2)
            position_size = max(0.01, min(position_size, 1.0))

            logging.info(f"Position size: {position_size} lots (Risk: ${risk_amount:.2f})")
            return position_size

        except Exception as e:
            logging.error(f"Error calculating position size: {e}")
            return 0.01

    def place_buy_order(self):
        """Place a simple buy order"""
        try:
            symbol_info = mt5.symbol_info(self.config.SYMBOL)
            if symbol_info is None:
                return None

            position_size = self.calculate_position_size()
            entry_price = symbol_info.ask
            stop_loss = entry_price - (self.config.STOP_LOSS_PIPS * symbol_info.point)
            take_profit = entry_price + (self.config.TAKE_PROFIT_PIPS * symbol_info.point)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.config.SYMBOL,
                "volume": position_size,
                "type": mt5.ORDER_TYPE_BUY,
                "price": entry_price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": self.magic_number,
                "comment": "EA2060_SIMPLE_BUY",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logging.error(f"Buy order failed: {result.retcode} - {result.comment}")
                return None

            logging.info(f"[+] BUY ORDER PLACED: {position_size} lots @ {entry_price:.5f}")
            logging.info(f"   SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
            logging.info(f"   Order ticket: {result.order}")

            return result.order

        except Exception as e:
            logging.error(f"Error placing buy order: {e}")
            return None

    def place_sell_order(self):
        """Place a simple sell order"""
        try:
            symbol_info = mt5.symbol_info(self.config.SYMBOL)
            if symbol_info is None:
                return None

            position_size = self.calculate_position_size()
            entry_price = symbol_info.bid
            stop_loss = entry_price + (self.config.STOP_LOSS_PIPS * symbol_info.point)
            take_profit = entry_price - (self.config.TAKE_PROFIT_PIPS * symbol_info.point)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.config.SYMBOL,
                "volume": position_size,
                "type": mt5.ORDER_TYPE_SELL,
                "price": entry_price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": self.magic_number,
                "comment": "EA2060_SIMPLE_SELL",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logging.error(f"Sell order failed: {result.retcode} - {result.comment}")
                return None

            logging.info(f"[+] SELL ORDER PLACED: {position_size} lots @ {entry_price:.5f}")
            logging.info(f"   SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
            logging.info(f"   Order ticket: {result.order}")

            return result.order

        except Exception as e:
            logging.error(f"Error placing sell order: {e}")
            return None

    def check_positions(self):
        """Check current positions"""
        try:
            positions = mt5.positions_get(symbol=self.config.SYMBOL)
            if positions is None:
                return []

            active_positions = []
            for pos in positions:
                if pos.magic == self.magic_number:
                    active_positions.append(pos)

            return active_positions

        except Exception as e:
            logging.error(f"Error checking positions: {e}")
            return []

    def get_market_data(self, timeframe="M5", bars=100):
        """Get market data"""
        try:
            mt5_timeframe = getattr(mt5, f'TIMEFRAME_{timeframe}')
            rates = mt5.copy_rates_from_pos(self.config.SYMBOL, mt5_timeframe, 0, bars)

            if rates is None or len(rates) == 0:
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            # Calculate simple EMAs
            df['ema_fast'] = df['close'].ewm(span=self.config.EMA_FAST).mean()
            df['ema_slow'] = df['close'].ewm(span=self.config.EMA_SLOW).mean()

            return df

        except Exception as e:
            logging.error(f"Error getting market data: {e}")
            return None

    def generate_simple_signal(self, df):
        """Generate simple trading signal"""
        try:
            if df is None or len(df) < 2:
                return "HOLD", 0

            # Check if EMA columns exist
            if 'ema_fast' not in df.columns or 'ema_slow' not in df.columns:
                logging.error("EMA columns not found in dataframe")
                return "HOLD", 0

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # Simple EMA crossover strategy
            if (latest['ema_fast'] > latest['ema_slow'] and
                prev['ema_fast'] <= prev['ema_slow']):
                return "BUY", 8
            elif (latest['ema_fast'] < latest['ema_slow'] and
                  prev['ema_fast'] >= prev['ema_slow']):
                return "SELL", 8

            return "HOLD", 0

        except Exception as e:
            logging.error(f"Error generating signal: {e}")
            return "HOLD", 0

    def check_market_conditions(self):
        """Check if market conditions are suitable"""
        try:
            symbol_info = mt5.symbol_info(self.config.SYMBOL)
            if symbol_info is None:
                return False, "Symbol info not available"

            # Check spread
            spread = symbol_info.spread
            if spread > self.config.MAX_SPREAD_POINTS:
                return False, f"Spread too high: {spread} points"

            # Check trading hours
            current_time = datetime.now()
            hour = current_time.hour
            if not (self.config.TRADING_HOURS_START <= hour < self.config.TRADING_HOURS_END):
                return False, f"Outside trading hours: {hour}:00"

            return True, "Market conditions OK"

        except Exception as e:
            logging.error(f"Error checking market conditions: {e}")
            return False, f"Error: {e}"

    def run_live_trading(self):
        """Main live trading loop"""
        logging.info("[+] Starting EA2060 Simple Live Trading")

        while self.running:
            try:
                # Check market conditions
                can_trade, reason = self.check_market_conditions()
                if not can_trade:
                    logging.info(f"[PAUSED] Trading paused: {reason}")
                    time.sleep(60)
                    continue

                # Get market data
                df = self.get_market_data()
                if df is None:
                    logging.error("Failed to get market data")
                    time.sleep(10)
                    continue

                # Generate signal
                signal, strength = self.generate_simple_signal(df)
                if signal == "HOLD" or strength < 6:
                    time.sleep(30)
                    continue

                # Check current positions
                current_positions = self.check_positions()

                # Only trade if we have less than max positions
                if len(current_positions) < self.config.MAX_POSITIONS:
                    logging.info(f"[SIGNAL] {signal} detected with strength {strength}")

                    if signal == "BUY":
                        self.place_buy_order()
                    elif signal == "SELL":
                        self.place_sell_order()

                    # Wait after placing order
                    time.sleep(30)

                # Log current status
                if len(current_positions) > 0:
                    total_profit = sum(pos.profit for pos in current_positions)
                    logging.info(f"[INFO] Active Positions: {len(current_positions)} | P&L: ${total_profit:.2f}")

                # Wait before next iteration
                time.sleep(10)  # Check every 10 seconds

            except KeyboardInterrupt:
                logging.info("Trading stopped by user")
                self.running = False
                break
            except Exception as e:
                logging.error(f"Error in trading loop: {e}")
                time.sleep(10)

    def stop_trading(self):
        """Stop live trading"""
        self.running = False
        logging.info("Trading stopped")

def main():
    """Main function"""
    trader = EA2060SimpleLiveTrader()

    if not trader.connect_mt5():
        logging.error("Failed to connect to MT5")
        return

    try:
        print("\n" + "="*80)
        print("[+] EA2060 SIMPLE LIVE TRADER")
        print("[!]  REAL ACCOUNT TRADING - USE WITH CAUTION")
        print("="*80)
        print(f"[INFO] Account: {mt5.account_info().login} (${mt5.account_info().balance:.2f})")
        print(f"[TARGET] Symbol: {trader.config.SYMBOL}")
        print(f"[MONEY] Risk per trade: {trader.config.RISK_PER_TRADE}%")
        print(f"[CHART] Max positions: {trader.config.MAX_POSITIONS}")
        print(f"[TIME] Trading hours: {trader.config.TRADING_HOURS_START}:00 - {trader.config.TRADING_HOURS_END}:00")
        print(f"[SPREAD] Max spread: {trader.config.MAX_SPREAD_POINTS} points")
        print("="*80)
        print("\n[!]  WARNING: This is real money trading!")
        print("   Make sure you understand the risks before proceeding.")
        print("\nPress Ctrl+C to stop trading at any time")
        print("\nStarting in 3 seconds...")

        time.sleep(3)

        trader.run_live_trading()

    except KeyboardInterrupt:
        print("\nTrading stopped by user")
        trader.stop_trading()
    except Exception as e:
        print(f"\nError: {e}")
        trader.stop_trading()
    finally:
        mt5.shutdown()
        print("MT5 connection closed")

if __name__ == "__main__":
    main()