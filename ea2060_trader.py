#!/usr/bin/env python3
"""
EA2060 819830 - Python Trading Bot
Versão migrada do EA chinês para Python usando MT5 nativo
"""

import MetaTrader5 as mt5
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
from ea2060_indicators import EA2060Indicators
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
        logging.FileHandler('ea2060_trader.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EA2060Trader:
    """
    EA2060 819830 Python Implementation
    """

    def __init__(self):
        self.is_running = False
        self.indicators = EA2060Indicators()
        self.open_positions = []
        self.magic_numbers = list(range(11111, 11136))  # 25 magic numbers
        self.current_magic_index = 0

        # Trading parameters
        self.symbol = "XAUUSD"
        self.timeframe = mt5.TIMEFRAME_H1  # Timeframe H1 conforme o EA original
        self.base_lot_size = 0.01  # Conforme configuração
        self.max_positions = 25  # 25 posições simultâneas

        # Indicator parameters
        self.atr_period = 24
        self.atr_multiplier = 3.0
        self.supertrend_period = 24
        self.adx_period = 14
        self.alligator_jaw = 13
        self.alligator_teeth = 8
        self.alligator_lips = 5

        # Risk management
        self.stop_loss_atr_multiplier = 2.0
        self.take_profit_atr_multiplier = 3.0
        self.max_risk_per_trade = 0.02  # 2% do capital

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
                logger.info(f"Leverage: {account_info.leverage}")
                return True
            else:
                logger.error("Failed to get account info")
                return False
        except Exception as e:
            logger.error(f"Error initializing MT5: {e}")
            return False

    def get_historical_data(self, symbol: str, timeframe, bars: int = 500) -> Optional[pd.DataFrame]:
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

    def calculate_position_size(self, account_balance: float, atr_value: float) -> float:
        """
        Calculate position size based on ATR and risk management
        """
        risk_amount = account_balance * self.max_risk_per_trade
        atr_in_pips = atr_value * 100  # Assuming XAUUSD pip value

        if atr_in_pips > 0:
            position_size = risk_amount / (atr_in_pips * self.stop_loss_atr_multiplier)
            # Round to standard lot sizes
            position_size = round(position_size / 0.01) * 0.01
            position_size = max(position_size, 0.01)  # Minimum lot size
            return position_size
        return self.base_lot_size

    def check_buy_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Check for buy signals based on EA logic
        """
        signals = []

        if len(df) < 50:  # Need enough data for indicators
            return signals

        latest_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]

        # Signal conditions based on indicators
        conditions = []

        # 1. Alligator alignment (bullish)
        if (latest_candle['lips'] > latest_candle['teeth'] > latest_candle['jaw'] and
            prev_candle['lips'] <= prev_candle['teeth'] <= prev_candle['jaw']):
            conditions.append("alligator_bullish")

        # 2. SuperTrend bullish breakout
        if (latest_candle['close'] > latest_candle['supertrend'] and
            prev_candle['close'] <= prev_candle['supertrend']):
            conditions.append("supertrend_bullish")

        # 3. ADX showing strength (above 25)
        if latest_candle['adx'] > 25:
            conditions.append("adx_strong")

        # 4. Volume confirmation (above average)
        if (latest_candle['volume_ratio'] > 1.2 and
            latest_candle['volume_trend'] > 0):
            conditions.append("volume_confirmation")

        # 5. Heiken Ashi bullish
        if (latest_candle['ha_close'] > latest_candle['ha_open']):
            conditions.append("heiken_ashi_bullish")

        # Generate signal if enough conditions are met
        if len(conditions) >= 3:  # Require at least 3 conditions
            signal = {
                'type': 'BUY',
                'price': latest_candle['close'],
                'time': latest_candle.name,
                'stop_loss': latest_candle['close'] - (latest_candle['atr'] * self.stop_loss_atr_multiplier),
                'take_profit': latest_candle['close'] + (latest_candle['atr'] * self.take_profit_atr_multiplier),
                'conditions': conditions,
                'confidence': len(conditions) / 5.0
            }
            signals.append(signal)

        return signals

    def check_sell_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Check for sell signals based on EA logic
        """
        signals = []

        if len(df) < 50:
            return signals

        latest_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]

        # Signal conditions
        conditions = []

        # 1. Alligator alignment (bearish)
        if (latest_candle['lips'] < latest_candle['teeth'] < latest_candle['jaw'] and
            prev_candle['lips'] >= prev_candle['teeth'] >= prev_candle['jaw']):
            conditions.append("alligator_bearish")

        # 2. SuperTrend bearish breakout
        if (latest_candle['close'] < latest_candle['supertrend'] and
            prev_candle['close'] >= prev_candle['supertrend']):
            conditions.append("supertrend_bearish")

        # 3. ADX showing strength (above 25)
        if latest_candle['adx'] > 25:
            conditions.append("adx_strong")

        # 4. Volume confirmation
        if (latest_candle['volume_ratio'] > 1.2 and
            latest_candle['volume_trend'] < 0):
            conditions.append("volume_confirmation")

        # 5. Heiken Ashi bearish
        if (latest_candle['ha_close'] < latest_candle['ha_open']):
            conditions.append("heiken_ashi_bearish")

        # Generate signal if enough conditions are met
        if len(conditions) >= 3:
            signal = {
                'type': 'SELL',
                'price': latest_candle['close'],
                'time': latest_candle.name,
                'stop_loss': latest_candle['close'] + (latest_candle['atr'] * self.stop_loss_atr_multiplier),
                'take_profit': latest_candle['close'] - (latest_candle['atr'] * self.take_profit_atr_multiplier),
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

            # Get current market price
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
                "comment": f"EA2060_{signal['type']}_{magic}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order
            result = mt5.order_send(request)

            if result is None:
                logger.error(f"Failed to send order: {mt5.last_error()}")
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed with retcode {result.retcode}: {result.comment}")
                return False

            logger.info("="*60)
            logger.info(f"ORDER PLACED SUCCESSFULLY!")
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

            open_positions = []
            for pos in positions:
                open_positions.append({
                    'ticket': pos.ticket,
                    'type': pos.type,
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'magic': pos.magic,
                    'comment': pos.comment,
                    'time': pos.time
                })
            return open_positions
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []

    def count_open_positions(self) -> int:
        """Count open positions"""
        return len(self.get_open_positions())

    def run(self):
        """Main trading loop"""
        logger.info("="*80)
        logger.info("EA2060 819830 - PYTHON VERSION")
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
                    time.sleep(300)  # Wait 5 minutes
                    continue

                # Get historical data
                df = self.get_historical_data(self.symbol, self.timeframe, 200)
                if df is None:
                    logger.error("Failed to get historical data, retrying...")
                    time.sleep(60)
                    continue

                # Calculate indicators
                df_with_indicators = self.indicators.calculate_all_indicators(df)
                logger.info(f"Indicators calculated for {len(df_with_indicators)} bars")

                # Check for signals
                buy_signals = self.check_buy_signals(df_with_indicators)
                sell_signals = self.check_sell_signals(df_with_indicators)

                all_signals = buy_signals + sell_signals

                if all_signals:
                    # Get highest confidence signal
                    best_signal = max(all_signals, key=lambda x: x['confidence'])

                    logger.info(f"SIGNAL DETECTED!")
                    logger.info(f"Type: {best_signal['type']}")
                    logger.info(f"Time: {best_signal['time']}")
                    logger.info(f"Price: {best_signal['price']:.5f}")
                    logger.info(f"Conditions: {', '.join(best_signal['conditions'])}")
                    logger.info(f"Confidence: {best_signal['confidence']:.2f}")

                    # Calculate position size
                    account_info = mt5.account_info()
                    position_size = self.calculate_position_size(
                        account_info.balance,
                        best_signal.get('atr', 50.0)
                    )

                    # Place order
                    success = self.place_order(best_signal, position_size)

                    if success:
                        logger.info("Trade executed successfully, waiting 5 minutes...")
                        time.sleep(300)  # Wait 5 minutes after successful trade
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
            logger.info("EA2060 trading session ended")

    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping EA2060 trading bot...")
        self.is_running = False

def main():
    """Main function"""
    logger.info("Starting EA2060 819830 Python Trader...")

    trader = EA2060Trader()

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