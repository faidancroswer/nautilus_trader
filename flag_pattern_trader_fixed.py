#!/usr/bin/env python3
"""
Flag Pattern Trader for XAUUSD on FBS Real Account - FIXED VERSION
Based on the backtest strategy from Flag_Pattern_5min.ipynb
"""

import MetaTrader5 as mt5
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

# Fix encoding issues on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flag_pattern_trader.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Strategy parameters from backtest
LOOKBACK = 40
PIVOT_WINDOW = 3
MAX_HIGH_SLOPE = 0.0002
MIN_LOW_SLOPE = 0.0005
MIN_R2 = 0.7
SIGNAL_LEN = 4  # breakout bar + 3 more bars

# Trading parameters
SYMBOL = "XAUUSD"
VOLUME = 0.01  # 0.01 lot (conservative position sizing)
SL_BUFFER = 0.01  # 1% buffer for stop loss
RR_RATIO = 3.0  # Risk/Reward ratio
TIMEFRAME = mt5.TIMEFRAME_M5  # 5 minutes
MAX_POSITIONS = 1  # Maximum concurrent positions

class FlagPatternTrader:
    def __init__(self):
        self.is_running = False
        self.current_positions = []
        self.last_signal_time = None

    def initialize_mt5(self):
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize():
                logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
                return False

            # Verify account
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"Connected to account {account_info.login} ({account_info.server})")
                logger.info(f"Balance: ${account_info.balance:.2f}")
                return True
            else:
                logger.error("Failed to get account info")
                return False
        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False

    def get_historical_data(self, symbol, timeframe, bars):
        """Get historical price data"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
            if rates is None:
                logger.error(f"Failed to get rates for {symbol}: {mt5.last_error()}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    def add_pivots(self, df, window=3):
        """Add pivot points to dataframe"""
        try:
            df = df.copy()
            df["pivoth"] = (
                df["high"]
                .rolling(window * 2 + 1, center=True)
                .apply(lambda x: x[window] == x.max(), raw=True)
                .fillna(0)
                .astype(bool)
            )
            df["pivotl"] = (
                df["low"]
                .rolling(window * 2 + 1, center=True)
                .apply(lambda x: x[window] == x.min(), raw=True)
                .fillna(0)
                .astype(bool)
            )
            return df
        except Exception as e:
            logger.error(f"Error adding pivots: {e}")
            return df

    def calculate_slope(self, xs, ys):
        """Calculate slope and R-squared"""
        try:
            if len(xs) < 2:
                return np.nan, np.nan

            # Linear regression
            coeffs = np.polyfit(xs, ys, 1)
            slope = coeffs[0]

            # R-squared
            y_pred = np.polyval(coeffs, xs)
            ss_res = np.sum((ys - y_pred) ** 2)
            ss_tot = np.sum((ys - np.mean(ys)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            return slope, r2
        except Exception as e:
            logger.error(f"Error calculating slope: {e}")
            return np.nan, np.nan

    def detect_flag(self, df, idx):
        """Detect flag pattern at given index"""
        try:
            if idx < LOOKBACK or idx < PIVOT_WINDOW * 2 + 1:
                return None

            # Convert idx to integer position
            if isinstance(idx, pd.Timestamp):
                idx_pos = df.index.get_loc(idx)
            else:
                idx_pos = idx

            flag_start_pos = idx_pos - LOOKBACK
            flag_end_pos = idx_pos - 1
            last_confirmable_pos = idx_pos - PIVOT_WINDOW

            # Get pivot points within lookback period using integer positions
            mask_slice = (np.arange(len(df)) >= flag_start_pos) & (np.arange(len(df)) <= last_confirmable_pos)
            abs_hi_pos = np.where(mask_slice & df["pivoth"].values)[0][-4:]
            abs_lo_pos = np.where(mask_slice & df["pivotl"].values)[0][-4:]

            # Convert positions back to indices
            abs_hi_idx = df.index[abs_hi_pos].tolist()
            abs_lo_idx = df.index[abs_lo_pos].tolist()

            if (
                len(abs_hi_idx) < 2
                or len(abs_lo_idx) < 2
                or (len(abs_hi_idx) + len(abs_lo_idx)) < 5
            ):
                return None

            # Calculate slopes for highs and lows
            xh = np.arange(len(abs_hi_idx))
            yh = df.loc[abs_hi_idx, "high"].values
            xl = np.arange(len(abs_lo_idx))
            yl = df.loc[abs_lo_idx, "low"].values

            slope_h_raw, r2_h = self.calculate_slope(xh, yh)
            slope_l_raw, r2_l = self.calculate_slope(xl, yl)

            # Normalize slopes by average price
            slope_h = slope_h_raw / yh.mean()
            slope_l = slope_l_raw / yl.mean()

            # Check flag conditions
            if not (
                abs(slope_h) <= MAX_HIGH_SLOPE
                and slope_l >= MIN_LOW_SLOPE
                and r2_h >= MIN_R2
                and r2_l >= MIN_R2
            ):
                return None

            return {
                "highs": [(int(df.index.get_loc(i)), float(df.loc[i, "high"])) for i in abs_hi_idx],
                "lows": [(int(df.index.get_loc(i)), float(df.loc[i, "low"])) for i in abs_lo_idx],
                "slope_high": slope_h,
                "slope_low": slope_l
            }
        except Exception as e:
            logger.error(f"Error detecting flag at index {idx}: {e}")
            return None

    def check_latest_signal(self, df):
        """Check for flag signal in the latest completed bar"""
        try:
            # Check the most recent completed bar (second to last)
            if len(df) < LOOKBACK + 10:
                return None

            latest_idx = len(df) - 2  # Second to last bar (most recent completed)
            flag = self.detect_flag(df, latest_idx)

            if flag:
                signal_time = df.index[latest_idx]
                signal_price = df.loc[signal_time, 'close']
                signal_high = df.loc[signal_time, 'high']

                # Check if we already processed this signal recently
                if self.last_signal_time and (signal_time - self.last_signal_time) < timedelta(minutes=30):
                    return None

                self.last_signal_time = signal_time

                return {
                    'time': signal_time,
                    'price': signal_price,
                    'high': signal_high,
                    'flag': flag
                }

            return None
        except Exception as e:
            logger.error(f"Error checking latest signal: {e}")
            return None

    def place_sell_order(self, price, high):
        """Place a sell order with stop loss and take profit"""
        try:
            logger.info(f"Attempting to place SELL order at {price:.5f}")

            # Get symbol info
            symbol_info = mt5.symbol_info(SYMBOL)
            if not symbol_info:
                logger.error(f"Failed to get symbol info for {SYMBOL}")
                return False

            # Calculate stop loss and take profit
            stop_loss = high * (1 + SL_BUFFER)
            take_profit = price - RR_RATIO * (stop_loss - price)

            # Ensure price is within valid range (round to tick size)
            tick_size = symbol_info.trade_tick_size
            price = round(price / tick_size) * tick_size
            stop_loss = round(stop_loss / tick_size) * tick_size
            take_profit = round(take_profit / tick_size) * tick_size

            # Get current ask price for sell order
            tick = mt5.symbol_info_tick(SYMBOL)
            if tick is None:
                logger.error(f"Failed to get tick info for {SYMBOL}")
                return False

            current_price = tick.bid  # Use bid for sell orders

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": VOLUME,
                "type": mt5.ORDER_TYPE_SELL,
                "price": current_price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": 234000,
                "comment": "Flag Pattern Sell Signal",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,  # IOC for better execution
            }

            # Send order
            result = mt5.order_send(request)

            if result is None:
                logger.error(f"Failed to send order: {mt5.last_error()}")
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed with retcode {result.retcode}: {result.comment}")
                return False

            logger.info("="*50)
            logger.info("SELL ORDER PLACED SUCCESSFULLY!")
            logger.info(f"Symbol: {SYMBOL}")
            logger.info(f"Volume: {VOLUME} lots")
            logger.info(f"Entry Price: {current_price:.5f}")
            logger.info(f"Stop Loss: {stop_loss:.5f}")
            logger.info(f"Take Profit: {take_profit:.5f}")
            logger.info(f"Order Ticket: {result.order}")
            logger.info(f"Deal Ticket: {result.deal}")
            logger.info("="*50)

            return True

        except Exception as e:
            logger.error(f"Error placing sell order: {e}")
            return False

    def get_open_positions(self):
        """Get current open positions"""
        try:
            positions = mt5.positions_get(symbol=SYMBOL)
            if positions is None:
                return []
            return positions
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []

    def count_open_positions(self):
        """Count open positions"""
        return len(self.get_open_positions())

    def run(self):
        """Main trading loop"""
        logger.info("="*60)
        logger.info("FLAG PATTERN TRADER STARTED")
        logger.info("="*60)
        logger.info(f"Symbol: {SYMBOL}")
        logger.info(f"Timeframe: M5")
        logger.info(f"Volume: {VOLUME} lots")
        logger.info(f"Risk/Reward: 1:{RR_RATIO}")
        logger.info(f"Max Positions: {MAX_POSITIONS}")
        logger.info("="*60)

        self.is_running = True
        cycle_count = 0

        try:
            while self.is_running:
                cycle_count += 1
                logger.info(f"--- Check cycle #{cycle_count} ---")

                # Check if we already have max positions
                open_positions = self.count_open_positions()
                if open_positions >= MAX_POSITIONS:
                    logger.info(f"Maximum positions ({MAX_POSITIONS}) reached. Waiting...")
                    time.sleep(300)  # Wait 5 minutes
                    continue

                # Get historical data
                df = self.get_historical_data(SYMBOL, TIMEFRAME, 200)
                if df is None:
                    logger.error("Failed to get historical data, retrying...")
                    time.sleep(60)
                    continue

                logger.info(f"Got {len(df)} bars of data")

                # Add pivots
                df = self.add_pivots(df, PIVOT_WINDOW)

                # Check for flag signals
                signal = self.check_latest_signal(df)

                if signal:
                    logger.info("FLAG PATTERN DETECTED!")
                    logger.info(f"Signal Time: {signal['time']}")
                    logger.info(f"Signal Price: {signal['price']:.5f}")
                    logger.info(f"Signal High: {signal['high']:.5f}")
                    logger.info(f"High Slope: {signal['flag']['slope_high']:.6f}")
                    logger.info(f"Low Slope: {signal['flag']['slope_low']:.6f}")

                    # Place sell order
                    success = self.place_sell_order(
                        signal['price'],
                        signal['high']
                    )

                    if success:
                        logger.info("Order placed successfully, waiting 10 minutes...")
                        time.sleep(600)  # Wait 10 minutes after successful trade
                    else:
                        logger.error("Failed to place order, waiting 1 minute...")
                        time.sleep(60)
                else:
                    logger.info("No flag signals detected")
                    time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("Trading stopped by user")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
        finally:
            self.is_running = False
            logger.info("Trading session ended")

    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping trading bot...")
        self.is_running = False

def main():
    """Main function"""
    logger.info("Starting Flag Pattern Trader...")

    trader = FlagPatternTrader()

    # Initialize MT5
    if not trader.initialize_mt5():
        logger.error("Failed to initialize MT5")
        return

    try:
        # Run the trading bot
        trader.run()
    finally:
        # Shutdown MT5
        mt5.shutdown()
        logger.info("MT5 connection closed")

if __name__ == "__main__":
    main()