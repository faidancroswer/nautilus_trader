#!/usr/bin/env python3
"""
EA2060 Simple Trader - Backtesting and Optimization Engine
Utiliza dados históricos para otimizar parâmetros de trading
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import yfinance as yf
from typing import List, Dict, Tuple, Optional
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BacktestIndicators:
    """Indicadores otimizados para backtest"""

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

    def supertrend(self, df: pd.DataFrame, period: int = 10, multiplier: float = 2.0) -> pd.Series:
        """SuperTrend Indicator"""
        hl2 = (df['high'] + df['low']) / 2
        atr_values = self.atr(df, period)

        upper_band = hl2 + (multiplier * atr_values)
        lower_band = hl2 - (multiplier * atr_values)

        supertrend = pd.Series(index=df.index, dtype=float)

        for i in range(len(df)):
            if i == 0:
                supertrend.iloc[i] = hl2.iloc[i]
            elif df['close'].iloc[i] > upper_band.iloc[i]:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]

        return supertrend

    def calculate_all(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Calculate all indicators with given parameters"""
        result = df.copy()

        # Moving averages
        result['ma_short'] = self.sma(result['close'], params['ma_short_period'])
        result['ma_medium'] = self.sma(result['close'], params['ma_medium_period'])
        result['ma_long'] = self.sma(result['close'], params['ma_long_period'])

        # EMA for crossovers
        result['ema_fast'] = self.ema(result['close'], params['ema_fast_period'])
        result['ema_slow'] = self.ema(result['close'], params['ema_slow_period'])

        # ATR
        result['atr'] = self.atr(result, params['atr_period'])

        # RSI
        result['rsi'] = self.rsi(result, params['rsi_period'])

        # SuperTrend
        result['supertrend'] = self.supertrend(result, params['supertrend_period'], params['supertrend_multiplier'])

        # Volume analysis
        result['volume_ma'] = result['volume'].rolling(window=params['volume_period']).mean()
        result['volume_ratio'] = result['volume'] / result['volume_ma']

        return result

class BacktestEngine:
    """Motor de backtest para EA2060"""

    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.indicators = BacktestIndicators()

    def check_signals(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.Series, pd.Series]:
        """Check for buy and sell signals"""
        buy_signals = pd.Series(False, index=df.index)
        sell_signals = pd.Series(False, index=df.index)

        for i in range(50, len(df)):  # Need enough data for indicators
            current = df.iloc[i]
            prev = df.iloc[i-1]

            # Buy conditions
            buy_conditions = []

            # EMA crossover bullish
            if prev['ema_fast'] <= prev['ema_slow'] and current['ema_fast'] > current['ema_slow']:
                buy_conditions.append("ema_crossover_bullish")

            # Price above moving averages
            if current['close'] > current['ma_short'] > current['ma_medium']:
                buy_conditions.append("price_above_mas")

            # RSI in optimal range
            if params['rsi_oversold'] < current['rsi'] < params['rsi_overbought']:
                buy_conditions.append("rsi_optimal")

            # Price above SuperTrend
            if current['close'] > current['supertrend']:
                buy_conditions.append("price_above_supertrend")

            # Volume confirmation
            if current['volume_ratio'] > params['volume_threshold']:
                buy_conditions.append("volume_confirm")

            # Generate buy signal if enough conditions
            if len(buy_conditions) >= params['min_conditions']:
                buy_signals.iloc[i] = True

            # Sell conditions
            sell_conditions = []

            # EMA crossover bearish
            if prev['ema_fast'] >= prev['ema_slow'] and current['ema_fast'] < current['ema_slow']:
                sell_conditions.append("ema_crossover_bearish")

            # Price below moving averages
            if current['close'] < current['ma_short'] < current['ma_medium']:
                sell_conditions.append("price_below_mas")

            # RSI in optimal range
            if params['rsi_oversold'] < current['rsi'] < params['rsi_overbought']:
                sell_conditions.append("rsi_optimal")

            # Price below SuperTrend
            if current['close'] < current['supertrend']:
                sell_conditions.append("price_below_supertrend")

            # Volume confirmation
            if current['volume_ratio'] > params['volume_threshold']:
                sell_conditions.append("volume_confirm")

            # Generate sell signal if enough conditions
            if len(sell_conditions) >= params['min_conditions']:
                sell_signals.iloc[i] = True

        return buy_signals, sell_signals

    def execute_backtest(self, df: pd.DataFrame, params: Dict) -> Dict:
        """Execute single backtest run"""
        try:
            # Calculate indicators
            df_with_indicators = self.indicators.calculate_all(df, params)

            # Remove NaN values
            df_clean = df_with_indicators.dropna()

            if len(df_clean) < 100:
                return {
                    'total_return': 0,
                    'max_drawdown': 1,
                    'sharpe_ratio': 0,
                    'total_trades': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'params': params
                }

            # Check signals
            buy_signals, sell_signals = self.check_signals(df_clean, params)

            # Initialize tracking variables
            balance = self.initial_balance
            position = None
            trades = []
            equity_curve = [balance]
            max_balance = balance

            # Execute trades
            for i in range(len(df_clean)):
                current_time = df_clean.index[i]
                current_price = df_clean.iloc[i]['close']

                # Close existing position
                if position is not None:
                    should_close = False

                    if position['type'] == 'LONG':
                        # Take profit
                        if current_price >= position['take_profit']:
                            should_close = True
                            reason = 'TP'
                        # Stop loss
                        elif current_price <= position['stop_loss']:
                            should_close = True
                            reason = 'SL'
                        # Trailing stop
                        elif current_price <= position['trailing_stop']:
                            should_close = True
                            reason = 'TRAIL'

                    elif position['type'] == 'SHORT':
                        # Take profit
                        if current_price <= position['take_profit']:
                            should_close = True
                            reason = 'TP'
                        # Stop loss
                        elif current_price >= position['stop_loss']:
                            should_close = True
                            reason = 'SL'
                        # Trailing stop
                        elif current_price >= position['trailing_stop']:
                            should_close = True
                            reason = 'TRAIL'

                    if should_close:
                        # Calculate profit/loss
                        if position['type'] == 'LONG':
                            profit = (current_price - position['entry_price']) / position['entry_price']
                        else:
                            profit = (position['entry_price'] - current_price) / position['entry_price']

                        profit_amount = balance * position['risk'] * profit
                        balance += profit_amount

                        trades.append({
                            'entry_time': position['entry_time'],
                            'exit_time': current_time,
                            'type': position['type'],
                            'entry_price': position['entry_price'],
                            'exit_price': current_price,
                            'profit': profit_amount,
                            'profit_pct': profit * 100,
                            'reason': reason
                        })

                        position = None

                # Open new position
                if position is None:
                    risk_amount = balance * params['risk_per_trade']

                    # Buy signal
                    if buy_signals.iloc[i]:
                        stop_loss = current_price - (params['stop_loss_pips'] * 0.01)
                        take_profit = current_price + (params['take_profit_pips'] * 0.01)
                        trailing_stop = stop_loss

                        position = {
                            'type': 'LONG',
                            'entry_time': current_time,
                            'entry_price': current_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'trailing_stop': trailing_stop,
                            'risk': params['risk_per_trade']
                        }

                    # Sell signal
                    elif sell_signals.iloc[i]:
                        stop_loss = current_price + (params['stop_loss_pips'] * 0.01)
                        take_profit = current_price - (params['take_profit_pips'] * 0.01)
                        trailing_stop = stop_loss

                        position = {
                            'type': 'SHORT',
                            'entry_time': current_time,
                            'entry_price': current_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'trailing_stop': trailing_stop,
                            'risk': params['risk_per_trade']
                        }

                # Update trailing stops
                if position is not None:
                    if position['type'] == 'LONG':
                        new_trailing = current_price - (params['stop_loss_pips'] * 0.01)
                        if new_trailing > position['trailing_stop']:
                            position['trailing_stop'] = new_trailing
                            # Move stop loss up
                            position['stop_loss'] = new_trailing

                    elif position['type'] == 'SHORT':
                        new_trailing = current_price + (params['stop_loss_pips'] * 0.01)
                        if new_trailing < position['trailing_stop']:
                            position['trailing_stop'] = new_trailing
                            # Move stop loss down
                            position['stop_loss'] = new_trailing

                # Track equity
                if position is not None:
                    unrealized_pnl = 0
                    if position['type'] == 'LONG':
                        unrealized_pnl = (current_price - position['entry_price']) / position['entry_price'] * balance * position['risk']
                    else:
                        unrealized_pnl = (position['entry_price'] - current_price) / position['entry_price'] * balance * position['risk']

                    current_equity = balance + unrealized_pnl
                else:
                    current_equity = balance

                equity_curve.append(current_equity)
                max_balance = max(max_balance, current_equity)

            # Calculate metrics
            if not trades:
                return {
                    'total_return': 0,
                    'max_drawdown': 0,
                    'sharpe_ratio': 0,
                    'total_trades': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'params': params
                }

            total_return = (balance - self.initial_balance) / self.initial_balance * 100
            max_drawdown = (max_balance - min(equity_curve)) / max_balance * 100

            # Sharpe ratio (simplified)
            returns = np.diff(equity_curve) / equity_curve[:-1]
            returns = returns[~np.isnan(returns)]
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
            else:
                sharpe_ratio = 0

            win_trades = [t for t in trades if t['profit'] > 0]
            loss_trades = [t for t in trades if t['profit'] <= 0]

            win_rate = len(win_trades) / len(trades) * 100 if trades else 0

            total_profit = sum(t['profit'] for t in win_trades) if win_trades else 0
            total_loss = abs(sum(t['profit'] for t in loss_trades)) if loss_trades else 1
            profit_factor = total_profit / total_loss if total_loss > 0 else 0

            return {
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'total_trades': len(trades),
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'final_balance': balance,
                'trades': trades,
                'equity_curve': equity_curve,
                'params': params
            }

        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return {
                'total_return': -100,
                'max_drawdown': 100,
                'sharpe_ratio': -10,
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'params': params
            }

class ParameterOptimizer:
    """Otimizador de parâmetros para EA2060"""

    def __init__(self):
        self.engine = BacktestEngine()

    def generate_parameter_grid(self) -> List[Dict]:
        """Generate parameter combinations for optimization"""
        param_grid = []

        # Moving average periods
        ma_short_periods = [8, 10, 12]
        ma_medium_periods = [18, 20, 22]
        ma_long_periods = [45, 50, 55]

        # EMA periods
        ema_fast_periods = [6, 8, 10]
        ema_slow_periods = [18, 21, 24]

        # Risk management
        stop_loss_pips = [150, 200, 250, 300]  # 15-30 pips
        take_profit_pips = [300, 400, 500, 600]  # 30-60 pips
        risk_per_trade = [0.01, 0.015, 0.02]  # 1-2%

        # Indicator parameters
        atr_periods = [10, 14, 18]
        rsi_periods = [12, 14, 16]
        rsi_oversold = [25, 30, 35]
        rsi_overbought = [65, 70, 75]

        # SuperTrend
        supertrend_periods = [8, 10, 12]
        supertrend_multipliers = [1.5, 2.0, 2.5]

        # Volume and signal requirements
        volume_periods = [15, 20, 25]
        volume_thresholds = [0.8, 1.0, 1.2]
        min_conditions = [2, 3, 4]

        # Generate all combinations (limit to reasonable number)
        combinations = list(itertools.product(
            ma_short_periods, ma_medium_periods, ma_long_periods,
            ema_fast_periods, ema_slow_periods,
            stop_loss_pips, take_profit_pips, risk_per_trade,
            atr_periods, rsi_periods, rsi_oversold, rsi_overbought,
            supertrend_periods, supertrend_multipliers,
            volume_periods, volume_thresholds, min_conditions
        ))

        # Limit to first 100 combinations for faster processing
        for combo in combinations[:100]:
            params = {
                'ma_short_period': combo[0],
                'ma_medium_period': combo[1],
                'ma_long_period': combo[2],
                'ema_fast_period': combo[3],
                'ema_slow_period': combo[4],
                'stop_loss_pips': combo[5],
                'take_profit_pips': combo[6],
                'risk_per_trade': combo[7],
                'atr_period': combo[8],
                'rsi_period': combo[9],
                'rsi_oversold': combo[10],
                'rsi_overbought': combo[11],
                'supertrend_period': combo[12],
                'supertrend_multiplier': combo[13],
                'volume_period': combo[14],
                'volume_threshold': combo[15],
                'min_conditions': combo[16]
            }
            param_grid.append(params)

        logger.info(f"Generated {len(param_grid)} parameter combinations")
        return param_grid

    def optimize_parameters(self, df: pd.DataFrame, param_grid: List[Dict]) -> List[Dict]:
        """Optimize parameters using grid search"""
        results = []

        logger.info(f"Starting optimization with {len(param_grid)} parameter combinations...")

        for i, params in enumerate(param_grid):
            logger.info(f"Testing combination {i+1}/{len(param_grid)}")

            result = self.engine.execute_backtest(df, params)
            results.append(result)

            # Log progress
            if (i + 1) % 10 == 0:
                logger.info(f"Completed {i+1}/{len(param_grid)} combinations")

        # Sort by total return
        results.sort(key=lambda x: x['total_return'], reverse=True)

        return results

def get_historical_data() -> pd.DataFrame:
    """Get historical data for XAUUSD from MT5"""
    try:
        import MetaTrader5 as mt5

        logger.info("Fetching historical data from MT5...")

        # Initialize MT5
        if not mt5.initialize():
            logger.error("Failed to initialize MT5")
            return None

        try:
            # Get maximum number of hourly bars available
            # MT5 typically provides up to 5000 bars for H1 timeframe
            rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H1, 0, 5000)

            if rates is None:
                logger.error(f"Failed to get rates: {mt5.last_error()}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            # Rename columns to match our format
            df = df.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            })

            # Keep only OHLCV columns
            df = df[['open', 'high', 'low', 'close', 'volume']]

            logger.info(f"Retrieved {len(df)} hourly bars from MT5")
            logger.info(f"Date range: {df.index[0]} to {df.index[-1]}")

            return df

        finally:
            mt5.shutdown()

    except Exception as e:
        logger.error(f"Error fetching historical data from MT5: {e}")
        return None

def main():
    """Main optimization function"""
    logger.info("="*80)
    logger.info("EA2060 Simple Trader - Backtest Optimization")
    logger.info("="*80)

    # Get historical data
    df = get_historical_data()
    if df is None:
        logger.error("Failed to get historical data")
        return

    # Initialize optimizer
    optimizer = ParameterOptimizer()

    # Generate parameter grid
    param_grid = optimizer.generate_parameter_grid()

    # Run optimization
    results = optimizer.optimize_parameters(df, param_grid)

    # Display top results
    logger.info("="*80)
    logger.info("OPTIMIZATION RESULTS - TOP 10 STRATEGIES")
    logger.info("="*80)

    for i, result in enumerate(results[:10]):
        logger.info(f"\\nRank #{i+1}:")
        logger.info(f"  Total Return: {result['total_return']:.2f}%")
        logger.info(f"  Max Drawdown: {result['max_drawdown']:.2f}%")
        logger.info(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        logger.info(f"  Total Trades: {result['total_trades']}")
        logger.info(f"  Win Rate: {result['win_rate']:.1f}%")
        logger.info(f"  Profit Factor: {result['profit_factor']:.2f}")
        logger.info(f"  Final Balance: ${result['final_balance']:.2f}")

        params = result['params']
        logger.info(f"  Parameters:")
        logger.info(f"    EMA: {params['ema_fast_period']}/{params['ema_slow_period']}")
        logger.info(f"    SL/TP: {params['stop_loss_pips']}/{params['take_profit_pips']} pips")
        logger.info(f"    Risk: {params['risk_per_trade']*100:.1f}%")
        logger.info(f"    RSI: {params['rsi_oversold']}-{params['rsi_overbought']}")
        logger.info(f"    Min Conditions: {params['min_conditions']}")

    # Save best parameters to file
    best_result = results[0]
    best_params = best_result['params']

    with open('ea2060_optimized_params.txt', 'w') as f:
        f.write("EA2060 Simple Trader - Optimized Parameters\\n")
        f.write("="*50 + "\\n\\n")
        f.write(f"Performance:\\n")
        f.write(f"  Total Return: {best_result['total_return']:.2f}%\\n")
        f.write(f"  Max Drawdown: {best_result['max_drawdown']:.2f}%\\n")
        f.write(f"  Sharpe Ratio: {best_result['sharpe_ratio']:.2f}\\n")
        f.write(f"  Total Trades: {best_result['total_trades']}\\n")
        f.write(f"  Win Rate: {best_result['win_rate']:.1f}%\\n")
        f.write(f"  Profit Factor: {best_result['profit_factor']:.2f}\\n\\n")
        f.write("Parameters:\\n")
        for key, value in best_params.items():
            f.write(f"  {key}: {value}\\n")

    logger.info(f"\\nBest parameters saved to 'ea2060_optimized_params.txt'")
    logger.info("Optimization completed successfully!")

if __name__ == "__main__":
    main()