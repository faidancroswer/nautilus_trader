#!/usr/bin/env python3
"""
EA2060 819830 - Simplified Python Trading Bot
Versão simplificada com indicadores robustos para funcionamento imediato
"""

import MetaTrader5 as mt5
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
from typing import List, Dict, Optional, Tuple

# Fix encoding issues on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ea2060_simple_trader.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleIndicators:
    """Simplified indicators that work reliably with limited data"""

    def __init__(self):
        pass

    def sma(self, data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()

    def ema(self, data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()

    def atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()

    def rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def simple_supertrend(self, df: pd.DataFrame, period: int = 10, multiplier: float = 2.0) -> pd.Series:
        """Simplified SuperTrend"""
        hl2 = (df['high'] + df['low']) / 2
        atr_values = self.atr(df, period)

        upper_band = hl2 + (multiplier * atr_values)
        lower_band = hl2 - (multiplier * atr_values)

        # Simple trend detection
        supertrend = pd.Series(index=df.index, dtype=float)

        for i in range(len(df)):
            if i == 0:
                supertrend.iloc[i] = hl2.iloc[i]
            elif df['close'].iloc[i] > upper_band.iloc[i]:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]

        return supertrend

    def volume_sma(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Volume Simple Moving Average"""
        volume_col = 'volume' if 'volume' in df.columns else 'tick_volume'
        return df[volume_col].rolling(window=period).mean()

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all simplified indicators"""
        result = df.copy()

        # Moving averages for trend
        result['ma_short'] = self.sma(result['close'], 10)
        result['ma_medium'] = self.sma(result['close'], 20)
        result['ma_long'] = self.sma(result['close'], 50)

        # EMA for crossover signals
        result['ema_fast'] = self.ema(result['close'], 8)
        result['ema_slow'] = self.ema(result['close'], 21)

        # ATR for volatility
        result['atr'] = self.atr(result)

        # RSI for momentum
        result['rsi'] = self.rsi(result)

        # Simple SuperTrend
        result['supertrend'] = self.simple_supertrend(result)

        # Volume analysis
        result['volume_ma'] = self.volume_sma(result)
        volume_col = 'volume' if 'volume' in df.columns else 'tick_volume'
        result['volume_ratio'] = result[volume_col] / result['volume_ma']

        return result

class EA2060SimpleTrader:
    """
    EA2060 819830 Simplified Python Implementation
    Focused on robust trading with minimal indicators
    """

    def __init__(self):
        self.is_running = False
        self.indicators = SimpleIndicators()
        self.open_positions = []
        self.magic_numbers = list(range(11111, 11136))  # 25 magic numbers
        self.current_magic_index = 0

        # Trading parameters
        self.symbol = "XAUUSD"
        self.timeframe = mt5.TIMEFRAME_H1
        self.base_lot_size = 0.01
        self.max_positions = 5  # Conservative for testing

        # Risk management
        self.stop_loss_pips = 200  # 20 pips for XAUUSD
        self.take_profit_pips = 400  # 40 pips for XAUUSD
        self.max_risk_per_trade = 0.01  # 1% risk

    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize():
                logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
                return False

            account_info = mt5.account_info()
            if account_info:
                logger.info(f"Connected to account {account_info.login} ({account_info.server})")
                logger.info(f"Balance: ${account_info.balance:.2f}")
                logger.info(f"Equity: ${account_info.equity:.2f}")
                return True
            else:
                logger.error("Failed to get account info")
                return False
        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False

    def get_historical_data(self, symbol: str, timeframe, bars: int = 200) -> Optional[pd.DataFrame]:
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

    def calculate_position_size(self, account_balance: float) -> float:
        """Calculate position size based on risk management"""
        risk_amount = account_balance * self.max_risk_per_trade

        # Simple position sizing for XAUUSD
        # 1 pip = $0.01 for 0.01 lots, so 200 pips = $2 risk
        if risk_amount >= 2:
            return 0.01
        else:
            return 0.01  # Minimum lot size

    def check_buy_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Check for buy signals using simplified logic"""
        signals = []

        if len(df) < 20:  # Need enough data for indicators
            return signals

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        conditions = []

        # 1. EMA crossover bullish
        if prev['ema_fast'] <= prev['ema_slow'] and latest['ema_fast'] > latest['ema_slow']:
            conditions.append("ema_crossover_bullish")

        # 2. Price above moving averages
        if latest['close'] > latest['ma_short'] > latest['ma_medium']:
            conditions.append("price_above_mas")

        # 3. RSI not overbought
        if 30 < latest['rsi'] < 70:
            conditions.append("rsi_neutral")

        # 4. Price above SuperTrend
        if latest['close'] > latest['supertrend']:
            conditions.append("price_above_supertrend")

        # 5. Volume confirmation
        if latest['volume_ratio'] > 1.0:
            conditions.append("volume_confirm")

        # Generate signal if enough conditions
        if len(conditions) >= 3:
            signal = {
                'type': 'BUY',
                'price': latest['close'],
                'time': latest.name,
                'stop_loss': latest['close'] - (self.stop_loss_pips * 0.01),  # Convert pips to price
                'take_profit': latest['close'] + (self.take_profit_pips * 0.01),
                'conditions': conditions,
                'confidence': len(conditions) / 5.0
            }
            signals.append(signal)

        return signals

    def check_sell_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Check for sell signals using simplified logic"""
        signals = []

        if len(df) < 20:
            return signals

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        conditions = []

        # 1. EMA crossover bearish
        if prev['ema_fast'] >= prev['ema_slow'] and latest['ema_fast'] < latest['ema_slow']:
            conditions.append("ema_crossover_bearish")

        # 2. Price below moving averages
        if latest['close'] < latest['ma_short'] < latest['ma_medium']:
            conditions.append("price_below_mas")

        # 3. RSI not oversold
        if 30 < latest['rsi'] < 70:
            conditions.append("rsi_neutral")

        # 4. Price below SuperTrend
        if latest['close'] < latest['supertrend']:
            conditions.append("price_below_supertrend")

        # 5. Volume confirmation
        if latest['volume_ratio'] > 1.0:
            conditions.append("volume_confirm")

        # Generate signal if enough conditions
        if len(conditions) >= 3:
            signal = {
                'type': 'SELL',
                'price': latest['close'],
                'time': latest.name,
                'stop_loss': latest['close'] + (self.stop_loss_pips * 0.01),
                'take_profit': latest['close'] - (self.take_profit_pips * 0.01),
                'conditions': conditions,
                'confidence': len(conditions) / 5.0
            }
            signals.append(signal)

        return signals

    def place_order(self, signal: Dict, position_size: float) -> bool:
        """Place trading order"""
        try:
            magic = self.magic_numbers[self.current_magic_index]
            self.current_magic_index = (self.current_magic_index + 1) % len(self.magic_numbers)

            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                logger.error(f"Failed to get symbol info for {self.symbol}")
                return False

            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                logger.error(f"Failed to get tick info for {self.symbol}")
                return False

            if signal['type'] == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                sl = signal['stop_loss']
                tp = signal['take_profit']
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                sl = signal['stop_loss']
                tp = signal['take_profit']

            # Round to tick size
            tick_size = symbol_info.trade_tick_size
            price = round(price / tick_size) * tick_size
            sl = round(sl / tick_size) * tick_size
            tp = round(tp / tick_size) * tick_size

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": position_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": magic,
                "comment": f"EA2060_Simple_{signal['type']}_{magic}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)

            if result is None:
                logger.error(f"Failed to send order: {mt5.last_error()}")
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed with retcode {result.retcode}: {result.comment}")
                return False

            logger.info("="*60)
            logger.info("ORDER PLACED SUCCESSFULLY!")
            logger.info(f"Type: {signal['type']}")
            logger.info(f"Symbol: {self.symbol}")
            logger.info(f"Volume: {position_size} lots")
            logger.info(f"Entry Price: {price:.5f}")
            logger.info(f"Stop Loss: {sl:.5f}")
            logger.info(f"Take Profit: {tp:.5f}")
            logger.info(f"Magic Number: {magic}")
            logger.info(f"Confidence: {signal['confidence']:.2f}")
            logger.info(f"Conditions: {', '.join(signal['conditions'])}")
            logger.info(f"Order Ticket: {result.order}")
            logger.info("="*60)

            return True

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return False

    def get_open_positions(self) -> List[Dict]:
        """Get current open positions"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            if positions is None:
                return []
            return positions
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []

    def count_open_positions(self) -> int:
        """Count open positions"""
        return len(self.get_open_positions())

    def run(self):
        """Main trading loop"""
        logger.info("="*80)
        logger.info("EA2060 819830 - SIMPLIFIED PYTHON VERSION")
        logger.info("="*80)
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Timeframe: H1")
        logger.info(f"Base Lot Size: {self.base_lot_size}")
        logger.info(f"Max Positions: {self.max_positions}")
        logger.info(f"Magic Numbers: {self.magic_numbers[0]}-{self.magic_numbers[-1]}")
        logger.info("="*80)

        self.is_running = True
        cycle_count = 0

        try:
            while self.is_running:
                cycle_count += 1
                logger.info(f"--- Trading Cycle #{cycle_count} ---")

                # Check position limits
                open_positions_count = self.count_open_positions()
                if open_positions_count >= self.max_positions:
                    logger.info(f"Maximum positions ({self.max_positions}) reached. Waiting...")
                    time.sleep(300)
                    continue

                # Get historical data
                df = self.get_historical_data(self.symbol, self.timeframe, 100)
                if df is None:
                    logger.error("Failed to get historical data, retrying...")
                    time.sleep(60)
                    continue

                # Calculate indicators
                df_with_indicators = self.indicators.calculate_all(df)

                # Remove rows with NaN values (warm-up period)
                df_clean = df_with_indicators.dropna()

                if len(df_clean) < 10:
                    logger.warning("Insufficient clean data for analysis")
                    time.sleep(60)
                    continue

                logger.info(f"Analyzing {len(df_clean)} bars of clean data")

                # Check for signals
                buy_signals = self.check_buy_signals(df_clean)
                sell_signals = self.check_sell_signals(df_clean)

                all_signals = buy_signals + sell_signals

                if all_signals:
                    # Get highest confidence signal
                    best_signal = max(all_signals, key=lambda x: x['confidence'])

                    logger.info("SIGNAL DETECTED!")
                    logger.info(f"Type: {best_signal['type']}")
                    logger.info(f"Time: {best_signal['time']}")
                    logger.info(f"Price: {best_signal['price']:.5f}")
                    logger.info(f"Conditions: {', '.join(best_signal['conditions'])}")
                    logger.info(f"Confidence: {best_signal['confidence']:.2f}")

                    # Calculate position size
                    account_info = mt5.account_info()
                    position_size = self.calculate_position_size(account_info.balance)

                    # Place order
                    success = self.place_order(best_signal, position_size)

                    if success:
                        logger.info("Trade executed successfully, waiting 10 minutes...")
                        time.sleep(600)  # Wait 10 minutes after successful trade
                    else:
                        logger.error("Failed to execute trade, waiting 1 minute...")
                        time.sleep(60)
                else:
                    logger.info("No trading signals detected")
                    time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("Trading stopped by user")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
        finally:
            self.is_running = False
            logger.info("EA2060 Simple trading session ended")

    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping EA2060 Simple trading bot...")
        self.is_running = False

def main():
    """Main function"""
    logger.info("Starting EA2060 819830 Simple Python Trader...")

    trader = EA2060SimpleTrader()

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