#!/usr/bin/env python3
"""
Flag Pattern Trader for XAUUSD on FBS Real Account
Based on the backtest strategy from Flag_Pattern_5min.ipynb
"""

import MetaTrader5 as mt5
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flag_pattern_trader.log'),
        logging.StreamHandler()
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

    def initialize_mt5(self):
        """Initialize MT5 connection"""
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

    def get_historical_data(self, symbol, timeframe, bars):
        """Get historical price data"""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None:
            logger.error(f"Failed to get rates for {symbol}: {mt5.last_error()}")
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def add_pivots(self, df, window=3):
        """Add pivot points to dataframe"""
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

    def calculate_slope(self, xs, ys):
        """Calculate slope and R-squared"""
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

    def detect_flag(self, df, idx):
        """Detect flag pattern at given index"""
        if idx < LOOKBACK or idx < PIVOT_WINDOW * 2 + 1:
            return None

        flag_start = idx - LOOKBACK
        flag_end = idx - 1
        last_confirmable = idx - PIVOT_WINDOW

        # Get pivot points within lookback period
        mask_slice = (df.index >= flag_start) & (df.index <= last_confirmable)
        abs_hi_idx = df.index[mask_slice & df["pivoth"]].tolist()[-4:]
        abs_lo_idx = df.index[mask_slice & df["pivotl"]].tolist()[-4:]

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
            "highs": [(int(i), float(df.loc[i, "high"])) for i in abs_hi_idx],
            "lows": [(int(i), float(df.loc[i, "low"])) for i in abs_lo_idx],
            "slope_high": slope_h,
            "slope_low": slope_l
        }

    def check_flag_signals(self, df):
        """Check for flag signals in the latest bars"""
        signals = []

        # Check last few bars for flag patterns
        for i in range(LOOKBACK, len(df)):
            flag = self.detect_flag(df, i)
            if flag:
                # Signal is valid for SIGNAL_LEN bars
                end_pos = min(i + SIGNAL_LEN, len(df))
                for j in range(i, end_pos):
                    signals.append({
                        'index': j,
                        'timestamp': df.index[j],
                        'price': df.loc[df.index[j], 'close'],
                        'flag': flag
                    })

        return signals

    def place_sell_order(self, price, high):
        """Place a sell order with stop loss and take profit"""
        try:
            # Calculate stop loss and take profit
            stop_loss = high * (1 + SL_BUFFER)
            take_profit = price - RR_RATIO * (stop_loss - price)

            # Get symbol info
            symbol_info = mt5.symbol_info(SYMBOL)
            if not symbol_info:
                logger.error(f"Failed to get symbol info for {SYMBOL}")
                return False

            # Ensure price is within valid range
            tick_size = symbol_info.trade_tick_size
            stop_loss = round(stop_loss / tick_size) * tick_size
            take_profit = round(take_profit / tick_size) * tick_size

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": VOLUME,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": 234000,
                "comment": "Flag Pattern Sell Signal",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }

            # Send order
            result = mt5.order_send(request)

            if result is None:
                logger.error(f"Failed to send order: {mt5.last_error()}")
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed with retcode {result.retcode}")
                return False

            logger.info(f"✅ Sell order placed successfully!")
            logger.info(f"   Symbol: {SYMBOL}")
            logger.info(f"   Volume: {VOLUME}")
            logger.info(f"   Entry Price: {price:.5f}")
            logger.info(f"   Stop Loss: {stop_loss:.5f}")
            logger.info(f"   Take Profit: {take_profit:.5f}")
            logger.info(f"   Order Ticket: {result.order}")

            return True

        except Exception as e:
            logger.error(f"Error placing sell order: {e}")
            return False

    def get_open_positions(self):
        """Get current open positions"""
        positions = mt5.positions_get(symbol=SYMBOL)
        if positions is None:
            return []
        return positions

    def count_open_positions(self):
        """Count open positions"""
        positions = self.get_open_positions()
        return len(positions)

    def run(self):
        """Main trading loop"""
        logger.info("🚀 Starting Flag Pattern Trader...")
        logger.info(f"📊 Symbol: {SYMBOL}")
        logger.info(f"💰 Volume: {VOLUME} lots")
        logger.info(f"⚖️  Risk/Reward: 1:{RR_RATIO}")
        logger.info(f"📈 Timeframe: M5")

        self.is_running = True

        try:
            while self.is_running:
                # Check if we already have max positions
                if self.count_open_positions() >= MAX_POSITIONS:
                    logger.info(f"Maximum positions ({MAX_POSITIONS}) reached. Waiting...")
                    time.sleep(60)  # Wait 1 minute
                    continue

                # Get historical data
                df = self.get_historical_data(SYMBOL, TIMEFRAME, 200)
                if df is None:
                    logger.error("Failed to get historical data")
                    time.sleep(60)
                    continue

                # Add pivots
                df = self.add_pivots(df, PIVOT_WINDOW)

                # Check for flag signals
                signals = self.check_flag_signals(df)

                # Process signals (only look at the most recent one)
                if signals:
                    latest_signal = signals[-1]  # Get the most recent signal

                    # Check if this signal is from the last completed bar
                    now = datetime.now()
                    signal_time = latest_signal['timestamp']

                    # Only consider signals from the last 10 minutes
                    if (now - signal_time) <= timedelta(minutes=10):
                        logger.info(f"🚩 Flag Pattern detected!")
                        logger.info(f"   Time: {signal_time}")
                        logger.info(f"   Price: {latest_signal['price']:.5f}")
                        logger.info(f"   High Slope: {latest_signal['flag']['slope_high']:.6f}")
                        logger.info(f"   Low Slope: {latest_signal['flag']['slope_low']:.6f}")

                        # Place sell order
                        success = self.place_sell_order(
                            latest_signal['price'],
                            df.loc[signal_time, 'high']
                        )

                        if success:
                            # Wait after placing order
                            time.sleep(300)  # Wait 5 minutes
                    else:
                        logger.debug(f"Old signal found, skipping...")
                else:
                    logger.debug("No flag signals detected")

                # Wait before next check
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("🛑 Trading stopped by user")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
        finally:
            self.is_running = False
            logger.info("📊 Trading session ended")

    def stop(self):
        """Stop the trading bot"""
        self.is_running = False

def main():
    """Main function"""
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