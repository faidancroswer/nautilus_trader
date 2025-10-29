#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EA2060 High Frequency Live Trader - Fixed Version
Real Account Trading System - Standalone Implementation
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
        logging.FileHandler('ea2060_hf_live_fixed.log'),
        logging.StreamHandler()
    ]
)

class HighFrequencyLiveConfig:
    """Live trading configuration for high frequency"""
    SYMBOL = "XAUUSD"
    TIMEFRAMES = ["M1", "M5"]
    RISK_PER_TRADE = 0.5  # 0.5% risk per trade (conservative for live)
    MAX_POSITIONS = 5     # Conservative for live
    STOP_LOSS_ATR = 1.5   # Tighter stops for live
    TAKE_PROFIT_ATR = 2.5 # Conservative profit target
    MIN_SIGNAL_STRENGTH = 6
    TRADING_HOURS_START = 8
    TRADING_HOURS_END = 18
    MAX_SPREAD_POINTS = 50

    # High frequency parameters
    EMA_FAST = 3
    EMA_SLOW = 7
    SUPERTREND_PERIOD = 8
    SUPERTREND_MULTIPLIER = 2.5
    ADX_THRESHOLD = 20
    RSI_PERIOD = 10

class EA2060Indicators:
    """Standalone indicators class"""

    @staticmethod
    def ema(data, period):
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period).mean()

    @staticmethod
    def atr(data, period=14):
        """Calculate Average True Range"""
        high = data['high']
        low = data['low']
        close = data['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period).mean()

        return atr

    @staticmethod
    def supertrend(data, period=10, multiplier=3.0):
        """Calculate SuperTrend indicator"""
        hl2 = (data['high'] + data['low']) / 2
        atr = EA2060Indicators.atr(data, period)

        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)

        supertrend = pd.Series(index=data.index, dtype=float)
        direction = pd.Series(index=data.index, dtype=float)

        for i in range(1, len(data)):
            if data['close'].iloc[i] > upper_band.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            elif data['close'].iloc[i] < lower_band.iloc[i-1]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]

        return direction

    @staticmethod
    def adx(data, period=14):
        """Calculate ADX indicator"""
        high = data['high']
        low = data['low']
        close = data['close']

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        # Calculate ADX
        atr_smooth = tr.ewm(span=period).mean()
        plus_di_smooth = pd.Series(plus_dm).ewm(span=period).mean()
        minus_di_smooth = pd.Series(minus_dm).ewm(span=period).mean()

        plus_di = 100 * (plus_di_smooth / atr_smooth)
        minus_di = 100 * (minus_di_smooth / atr_smooth)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period).mean()

        return adx.fillna(0)

    @staticmethod
    def rsi(data, period=14):
        """Calculate RSI indicator"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(span=period).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(span=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.fillna(50)

class EA2060HighFrequencyLiveFixed:
    """Fixed live high frequency trading system"""

    def __init__(self):
        self.config = HighFrequencyLiveConfig()
        self.positions = {}
        self.magic_numbers = list(range(20001, 20006))  # 5 magic numbers for live
        self.running = True

        logging.info("EA2060 High Frequency Live Trader Fixed Initialized")

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

    def get_live_data(self, timeframe, bars=500):
        """Get live data from MT5"""
        try:
            mt5_timeframe = getattr(mt5, f'TIMEFRAME_{timeframe}')
            rates = mt5.copy_rates_from_pos(self.config.SYMBOL, mt5_timeframe, 0, bars)

            if rates is None or len(rates) == 0:
                logging.error(f"Failed to get {timeframe} data")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            return df

        except Exception as e:
            logging.error(f"Error getting {timeframe} data: {e}")
            return None

    def check_market_conditions(self):
        """Check if market conditions are suitable for trading"""
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

            # Check if market is closed (Friday evening)
            if current_time.weekday() == 4 and hour >= 20:  # Friday after 8pm
                return False, "Market closing soon"

            return True, "Market conditions OK"

        except Exception as e:
            logging.error(f"Error checking market conditions: {e}")
            return False, f"Error: {e}"

    def calculate_position_size(self, stop_loss_points):
        """Calculate position size based on risk management"""
        try:
            account_info = mt5.account_info()
            balance = account_info.balance
            risk_amount = balance * (self.config.RISK_PER_TRADE / 100)

            # Calculate position size
            symbol_info = mt5.symbol_info(self.config.SYMBOL)
            point = symbol_info.point
            tick_value = symbol_info.trade_tick_value

            if point == 0 or tick_value == 0:
                return 0.01  # Minimum position

            position_size = risk_amount / (stop_loss_points * tick_value)
            position_size = round(position_size, 2)

            # Ensure minimum and maximum position size
            position_size = max(0.01, min(position_size, 1.0))

            logging.info(f"Position size calculated: {position_size} lots (Risk: ${risk_amount:.2f})")
            return position_size

        except Exception as e:
            logging.error(f"Error calculating position size: {e}")
            return 0.01

    def place_buy_order(self, signal_strength, entry_price, stop_loss, take_profit):
        """Place a buy order"""
        try:
            symbol_info = mt5.symbol_info(self.config.SYMBOL)
            point = symbol_info.point
            stop_loss_points = (entry_price - stop_loss) / point
            position_size = self.calculate_position_size(stop_loss_points)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.config.SYMBOL,
                "volume": position_size,
                "type": mt5.ORDER_TYPE_BUY,
                "price": entry_price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": self.magic_numbers[0],
                "comment": f"EA2060_HF_BUY_STR{signal_strength}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logging.error(f"Buy order failed: {result.retcode} - {result.comment}")
                return None

            logging.info(f"[+] BUY ORDER PLACED: {position_size} lots @ {entry_price:.5f}")
            logging.info(f"   SL: {stop_loss:.5f} | TP: {take_profit:.5f} | Strength: {signal_strength}")
            logging.info(f"   Order ticket: {result.order}")

            return result.order

        except Exception as e:
            logging.error(f"Error placing buy order: {e}")
            return None

    def place_sell_order(self, signal_strength, entry_price, stop_loss, take_profit):
        """Place a sell order"""
        try:
            symbol_info = mt5.symbol_info(self.config.SYMBOL)
            point = symbol_info.point
            stop_loss_points = (stop_loss - entry_price) / point
            position_size = self.calculate_position_size(stop_loss_points)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.config.SYMBOL,
                "volume": position_size,
                "type": mt5.ORDER_TYPE_SELL,
                "price": entry_price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": self.magic_numbers[1],
                "comment": f"EA2060_HF_SELL_STR{signal_strength}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logging.error(f"Sell order failed: {result.retcode} - {result.comment}")
                return None

            logging.info(f"[+] SELL ORDER PLACED: {position_size} lots @ {entry_price:.5f}")
            logging.info(f"   SL: {stop_loss:.5f} | TP: {take_profit:.5f} | Strength: {signal_strength}")
            logging.info(f"   Order ticket: {result.order}")

            return result.order

        except Exception as e:
            logging.error(f"Error placing sell order: {e}")
            return None

    def check_positions(self):
        """Check and manage open positions"""
        try:
            positions = mt5.positions_get(symbol=self.config.SYMBOL)
            if positions is None:
                return []

            active_positions = []
            for pos in positions:
                if pos.magic in self.magic_numbers:
                    active_positions.append(pos)

            return active_positions

        except Exception as e:
            logging.error(f"Error checking positions: {e}")
            return []

    def generate_live_signals(self, data_dict):
        """Generate live trading signals"""
        try:
            signals = {}

            for tf, df in data_dict.items():
                if df is None or len(df) < 50:
                    continue

                # Calculate indicators
                df['ema_fast'] = EA2060Indicators.ema(df['close'], self.config.EMA_FAST)
                df['ema_slow'] = EA2060Indicators.ema(df['close'], self.config.EMA_SLOW)
                df['supertrend'] = EA2060Indicators.supertrend(df, self.config.SUPERTREND_PERIOD, self.config.SUPERTREND_MULTIPLIER)
                df['adx'] = EA2060Indicators.adx(df, 14)
                df['rsi'] = EA2060Indicators.rsi(df, self.config.RSI_PERIOD)
                df['atr'] = EA2060Indicators.atr(df, 14)

                # Generate signals based on high frequency strategy
                latest = df.iloc[-1]
                prev = df.iloc[-2]

                signal_strength = 0
                signal_type = "HOLD"

                # EMA signals (ultra fast)
                if latest['ema_fast'] > latest['ema_slow']:
                    if prev['ema_fast'] <= prev['ema_slow']:
                        signal_strength += 3
                        signal_type = "BUY"
                else:
                    if prev['ema_fast'] >= prev['ema_slow']:
                        signal_strength += 3
                        signal_type = "SELL"

                # SuperTrend signals
                if latest['supertrend'] == 1 and prev['supertrend'] == -1:
                    signal_strength += 3
                    signal_type = "BUY"
                elif latest['supertrend'] == -1 and prev['supertrend'] == 1:
                    signal_strength += 3
                    signal_type = "SELL"

                # ADX strength
                if latest['adx'] > self.config.ADX_THRESHOLD:
                    signal_strength += 1

                # RSI signals
                if latest['rsi'] < 30:
                    signal_strength += 2
                    if signal_type != "SELL":
                        signal_type = "BUY"
                elif latest['rsi'] > 70:
                    signal_strength += 2
                    if signal_type != "BUY":
                        signal_type = "SELL"

                signals[tf] = {
                    'type': signal_type,
                    'strength': signal_strength,
                    'price': latest['close'],
                    'atr': latest['atr'],
                    'volume': latest['tick_volume']
                }

            return signals

        except Exception as e:
            logging.error(f"Error generating signals: {e}")
            return {}

    def run_live_trading(self):
        """Main live trading loop"""
        logging.info("[+] Starting EA2060 High Frequency Live Trading")

        while self.running:
            try:
                # Check market conditions
                can_trade, reason = self.check_market_conditions()
                if not can_trade:
                    logging.info(f"[PAUSED] Trading paused: {reason}")
                    time.sleep(60)
                    continue

                # Get live data
                data_dict = {}
                for tf in self.config.TIMEFRAMES:
                    data_dict[tf] = self.get_live_data(tf)

                # Check if we have data
                valid_data = True
                for tf, df in data_dict.items():
                    if df is None or len(df) < 50:
                        valid_data = False
                        break

                if not valid_data:
                    logging.error("Failed to get required data")
                    time.sleep(10)
                    continue

                # Generate signals
                signals = self.generate_live_signals(data_dict)

                # Check current positions
                current_positions = self.check_positions()

                # Trading logic
                if len(current_positions) < self.config.MAX_POSITIONS:
                    # Look for trading opportunities
                    for tf, signal in signals.items():
                        if signal['strength'] >= self.config.MIN_SIGNAL_STRENGTH:

                            # Calculate stop loss and take profit
                            atr = signal['atr']
                            entry_price = signal['price']

                            if signal['type'] == "BUY":
                                stop_loss = entry_price - (atr * self.config.STOP_LOSS_ATR)
                                take_profit = entry_price + (atr * self.config.TAKE_PROFIT_ATR)

                                order_ticket = self.place_buy_order(
                                    signal['strength'], entry_price, stop_loss, take_profit
                                )

                                if order_ticket:
                                    self.positions[order_ticket] = {
                                        'type': 'BUY',
                                        'entry': entry_price,
                                        'stop_loss': stop_loss,
                                        'take_profit': take_profit,
                                        'time': datetime.now(),
                                        'strength': signal['strength']
                                    }

                            elif signal['type'] == "SELL":
                                stop_loss = entry_price + (atr * self.config.STOP_LOSS_ATR)
                                take_profit = entry_price - (atr * self.config.TAKE_PROFIT_ATR)

                                order_ticket = self.place_sell_order(
                                    signal['strength'], entry_price, stop_loss, take_profit
                                )

                                if order_ticket:
                                    self.positions[order_ticket] = {
                                        'type': 'SELL',
                                        'entry': entry_price,
                                        'stop_loss': stop_loss,
                                        'take_profit': take_profit,
                                        'time': datetime.now(),
                                        'strength': signal['strength']
                                    }

                # Log current status
                if len(current_positions) > 0:
                    total_profit = sum(pos.profit for pos in current_positions)
                    logging.info(f"[INFO] Active Positions: {len(current_positions)} | P&L: ${total_profit:.2f}")
                    logging.info(f"   Signal strength range: {signals.get('M1', {}).get('strength', 0)}")

                # Wait before next iteration
                time.sleep(5)  # Check every 5 seconds for high frequency

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
    trader = EA2060HighFrequencyLiveFixed()

    if not trader.connect_mt5():
        logging.error("Failed to connect to MT5")
        return

    try:
        print("\n" + "="*80)
        print("[+] EA2060 HIGH FREQUENCY LIVE TRADER - FIXED VERSION")
        print("[!]  REAL ACCOUNT TRADING - USE WITH CAUTION")
        print("="*80)
        print(f"[INFO] Account: {mt5.account_info().login} (${mt5.account_info().balance:.2f})")
        print(f"[TARGET] Symbol: {trader.config.SYMBOL}")
        print(f"[MONEY] Risk per trade: {trader.config.RISK_PER_TRADE}%")
        print(f"[CHART] Max positions: {trader.config.MAX_POSITIONS}")
        print(f"[TIME] Trading hours: {trader.config.TRADING_HOURS_START}:00 - {trader.config.TRADING_HOURS_END}:00")
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