#!/usr/bin/env python3
"""
EA2060 Simple Trader - Quick Backtest for Rapid Optimization
Versão simplificada para otimização rápida de parâmetros principais
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import MetaTrader5 as mt5
from typing import List, Dict, Tuple, Optional
import itertools
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickBacktestEngine:
    """Motor de backtest rápido para EA2060"""

    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance

    def calculate_indicators(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Calculate essential indicators"""
        result = df.copy()

        # EMA para crossovers
        result['ema_fast'] = df['close'].ewm(span=params['ema_fast'], adjust=False).mean()
        result['ema_slow'] = df['close'].ewm(span=params['ema_slow'], adjust=False).mean()

        # ATR para volatilidade
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        result['atr'] = true_range.rolling(window=params['atr_period']).mean()

        # RSI para momentum
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=params['rsi_period']).mean()
        rs = gain / loss
        result['rsi'] = 100 - (100 / (1 + rs))

        # SuperTrend simplificado
        hl2 = (df['high'] + df['low']) / 2
        upper_band = hl2 + (params['st_multiplier'] * result['atr'])
        lower_band = hl2 - (params['st_multiplier'] * result['atr'])

        result['supertrend'] = np.where(df['close'] > upper_band, lower_band, upper_band)

        # Volume
        result['volume_ma'] = df['volume'].rolling(window=params['volume_period']).mean()
        result['volume_ratio'] = df['volume'] / result['volume_ma']

        return result

    def check_signals(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.Series, pd.Series]:
        """Check for buy and sell signals"""
        buy_signals = pd.Series(False, index=df.index)
        sell_signals = pd.Series(False, index=df.index)

        for i in range(30, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]

            # Buy conditions
            buy_score = 0

            # EMA crossover bullish
            if prev['ema_fast'] <= prev['ema_slow'] and current['ema_fast'] > current['ema_slow']:
                buy_score += 2

            # Price above EMAs
            if current['close'] > current['ema_fast'] > current['ema_slow']:
                buy_score += 1

            # RSI in buy range
            if params['rsi_oversold'] < current['rsi'] < params['rsi_overbought']:
                buy_score += 1

            # Price above SuperTrend
            if current['close'] > current['supertrend']:
                buy_score += 2

            # Volume confirmation
            if current['volume_ratio'] > params['volume_threshold']:
                buy_score += 1

            # Generate buy signal
            if buy_score >= params['min_score']:
                buy_signals.iloc[i] = True

            # Sell conditions
            sell_score = 0

            # EMA crossover bearish
            if prev['ema_fast'] >= prev['ema_slow'] and current['ema_fast'] < current['ema_slow']:
                sell_score += 2

            # Price below EMAs
            if current['close'] < current['ema_fast'] < current['ema_slow']:
                sell_score += 1

            # RSI in sell range
            if params['rsi_oversold'] < current['rsi'] < params['rsi_overbought']:
                sell_score += 1

            # Price below SuperTrend
            if current['close'] < current['supertrend']:
                sell_score += 2

            # Volume confirmation
            if current['volume_ratio'] > params['volume_threshold']:
                sell_score += 1

            # Generate sell signal
            if sell_score >= params['min_score']:
                sell_signals.iloc[i] = True

        return buy_signals, sell_signals

    def run_backtest(self, df: pd.DataFrame, params: Dict) -> Dict:
        """Execute single backtest"""
        try:
            # Calculate indicators
            df_indicators = self.calculate_indicators(df, params)
            df_clean = df_indicators.dropna()

            if len(df_clean) < 100:
                return {'total_return': -100, 'max_drawdown': 100, 'trades': 0, 'win_rate': 0}

            # Get signals
            buy_signals, sell_signals = self.check_signals(df_clean, params)

            # Track trades
            balance = self.initial_balance
            position = None
            trades = []
            equity_curve = [balance]
            max_balance = balance

            for i in range(len(df_clean)):
                current_time = df_clean.index[i]
                current_price = df_clean.iloc[i]['close']

                # Close position if needed
                if position:
                    close_reason = None

                    if position['type'] == 'LONG':
                        if current_price >= position['tp']:
                            close_reason = 'TP'
                        elif current_price <= position['sl']:
                            close_reason = 'SL'
                    else:  # SHORT
                        if current_price <= position['tp']:
                            close_reason = 'TP'
                        elif current_price >= position['sl']:
                            close_reason = 'SL'

                    if close_reason:
                        # Calculate P&L
                        if position['type'] == 'LONG':
                            profit_pct = (current_price - position['entry']) / position['entry']
                        else:
                            profit_pct = (position['entry'] - current_price) / position['entry']

                        profit_amount = balance * position['risk'] * profit_pct
                        balance += profit_amount

                        trades.append({
                            'type': position['type'],
                            'entry': position['entry'],
                            'exit': current_price,
                            'profit': profit_amount,
                            'profit_pct': profit_pct * 100,
                            'reason': close_reason
                        })

                        position = None

                # Open new position
                if not position:
                    risk_amount = balance * params['risk_per_trade']

                    if buy_signals.iloc[i]:
                        position = {
                            'type': 'LONG',
                            'entry': current_price,
                            'sl': current_price - (params['sl_pips'] * 0.01),
                            'tp': current_price + (params['tp_pips'] * 0.01),
                            'risk': params['risk_per_trade']
                        }

                    elif sell_signals.iloc[i]:
                        position = {
                            'type': 'SHORT',
                            'entry': current_price,
                            'sl': current_price + (params['sl_pips'] * 0.01),
                            'tp': current_price - (params['tp_pips'] * 0.01),
                            'risk': params['risk_per_trade']
                        }

                # Update equity
                current_equity = balance
                if position:
                    if position['type'] == 'LONG':
                        unrealized = (current_price - position['entry']) / position['entry'] * balance * position['risk']
                    else:
                        unrealized = (position['entry'] - current_price) / position['entry'] * balance * position['risk']
                    current_equity += unrealized

                equity_curve.append(current_equity)
                max_balance = max(max_balance, current_equity)

            # Calculate metrics
            total_return = ((balance - self.initial_balance) / self.initial_balance) * 100
            max_drawdown = ((max_balance - min(equity_curve)) / max_balance) * 100

            winning_trades = [t for t in trades if t['profit'] > 0]
            win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0

            return {
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'total_trades': len(trades),
                'win_rate': win_rate,
                'final_balance': balance,
                'params': params,
                'trades': trades
            }

        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return {'total_return': -100, 'max_drawdown': 100, 'trades': 0, 'win_rate': 0}

def get_mt5_data(bars: int = 2000) -> pd.DataFrame:
    """Get data from MT5"""
    try:
        if not mt5.initialize():
            logger.error("Failed to initialize MT5")
            return None

        rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H1, 0, bars)
        mt5.shutdown()

        if rates is None:
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        df = df.rename(columns={'tick_volume': 'volume'})

        return df

    except Exception as e:
        logger.error(f"Error getting MT5 data: {e}")
        return None

def quick_optimization():
    """Quick optimization with key parameters"""
    logger.info("Starting quick optimization...")

    # Get data
    df = get_mt5_data(2000)
    if df is None:
        logger.error("No data available")
        return

    logger.info(f"Testing with {len(df)} bars from {df.index[0]} to {df.index[-1]}")

    # Define parameter ranges
    ema_fast_range = [6, 8, 10, 12]
    ema_slow_range = [18, 21, 24, 27]
    sl_pips_range = [150, 200, 250, 300]
    tp_pips_range = [300, 400, 500, 600]
    risk_range = [0.01, 0.015, 0.02]

    # Generate combinations (limit to 50 for speed)
    combinations = []
    for ema_fast, ema_slow, sl, tp, risk in itertools.product(
        ema_fast_range, ema_slow_range, sl_pips_range, tp_pips_range, risk_range
    ):
        if ema_fast < ema_slow and tp > sl:  # Logic check
            combinations.append({
                'ema_fast': ema_fast,
                'ema_slow': ema_slow,
                'sl_pips': sl,
                'tp_pips': tp,
                'risk_per_trade': risk,
                # Fixed parameters
                'atr_period': 14,
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'st_multiplier': 2.0,
                'volume_period': 20,
                'volume_threshold': 1.0,
                'min_score': 4
            })

    # Limit to 50 combinations
    combinations = combinations[:50]

    logger.info(f"Testing {len(combinations)} parameter combinations...")

    engine = QuickBacktestEngine()
    results = []

    for i, params in enumerate(combinations):
        logger.info(f"Testing {i+1}/{len(combinations)}: EMA {params['ema_fast']}/{params['ema_slow']}, "
                   f"SL/TP {params['sl_pips']}/{params['tp_pips']}, Risk {params['risk_per_trade']*100:.1f}%")

        result = engine.run_backtest(df, params)
        results.append(result)

        if (i + 1) % 10 == 0:
            logger.info(f"Completed {i+1} combinations")

    # Sort by total return
    results.sort(key=lambda x: x['total_return'], reverse=True)

    # Display top results
    logger.info("\n" + "="*80)
    logger.info("TOP 10 OPTIMIZATION RESULTS")
    logger.info("="*80)

    for i, result in enumerate(results[:10]):
        params = result['params']
        logger.info(f"\nRank #{i+1}:")
        logger.info(f"  Return: {result['total_return']:.2f}%")
        logger.info(f"  Drawdown: {result['max_drawdown']:.2f}%")
        logger.info(f"  Trades: {result['total_trades']}")
        logger.info(f"  Win Rate: {result['win_rate']:.1f}%")
        logger.info(f"  Final Balance: ${result['final_balance']:.2f}")
        logger.info(f"  EMA: {params['ema_fast']}/{params['ema_slow']}")
        logger.info(f"  SL/TP: {params['sl_pips']}/{params['tp_pips']} pips")
        logger.info(f"  Risk: {params['risk_per_trade']*100:.1f}%")

    # Save best parameters
    best = results[0]
    with open('ea2060_quick_optimized.txt', 'w') as f:
        f.write("EA2060 Quick Optimization Results\n")
        f.write("="*40 + "\n\n")
        f.write(f"Best Performance:\n")
        f.write(f"  Return: {best['total_return']:.2f}%\n")
        f.write(f"  Drawdown: {best['max_drawdown']:.2f}%\n")
        f.write(f"  Trades: {best['total_trades']}\n")
        f.write(f"  Win Rate: {best['win_rate']:.1f}%\n\n")
        f.write("Optimized Parameters:\n")
        for key, value in best['params'].items():
            f.write(f"  {key}: {value}\n")

    logger.info("\nBest parameters saved to 'ea2060_quick_optimized.txt'")
    logger.info("Quick optimization completed!")

if __name__ == "__main__":
    quick_optimization()