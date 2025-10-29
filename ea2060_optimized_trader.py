#!/usr/bin/env python3
"""
EA2060 819830 - Optimized Python Trading Bot
Versão otimizada com base nos resultados do backtest
Parâmetros ajustados para maximizar lucros e minimizar perdas
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
        logging.FileHandler('ea2060_optimized_trader.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OptimizedIndicators:
    """Indicadores otimizados baseados nos resultados do backtest"""

    def __init__(self):
        pass

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

    def adaptive_supertrend(self, df: pd.DataFrame, atr_period: int = 14, base_multiplier: float = 2.0) -> pd.Series:
        """SuperTrend adaptativo com multiplicador dinâmico baseado na volatilidade"""
        atr_values = self.atr(df, atr_period)
        hl2 = (df['high'] + df['low']) / 2

        # Ajustar multiplicador baseado na volatilidade recente
        atr_sma = atr_values.rolling(window=20).mean()
        volatility_ratio = atr_values / atr_sma

        # Multiplicador adaptativo (maior em alta volatilidade, menor em baixa)
        adaptive_multiplier = base_multiplier * (1 + 0.3 * (volatility_ratio - 1).clip(-0.5, 0.5))

        upper_band = hl2 + (adaptive_multiplier * atr_values)
        lower_band = hl2 - (adaptive_multiplier * atr_values)

        supertrend = pd.Series(index=df.index, dtype=float)

        for i in range(len(df)):
            if i == 0:
                supertrend.iloc[i] = hl2.iloc[i]
            elif df['close'].iloc[i] > upper_band.iloc[i]:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]

        return supertrend

    def bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """Bandas de Bollinger para confirmação de tendência"""
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return pd.DataFrame({
            'bb_middle': sma,
            'bb_upper': upper_band,
            'bb_lower': lower_band
        })

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular todos os indicadores otimizados"""
        result = df.copy()

        # Parâmetros otimizados do backtest
        result['ema_fast'] = self.ema(result['close'], 6)
        result['ema_slow'] = self.ema(result['close'], 18)

        # Indicadores de volatilidade
        result['atr'] = self.atr(result, 14)
        result['supertrend'] = self.adaptive_supertrend(result)

        # Momentum
        result['rsi'] = self.rsi(result, 14)

        # Bandas de Bollinger para confirmação
        bb = self.bollinger_bands(result)
        result = pd.concat([result, bb], axis=1)

        # Volume analysis
        volume_col = 'volume' if 'volume' in result.columns else 'tick_volume'
        result['volume_ma'] = result[volume_col].rolling(window=20).mean()
        result['volume_ratio'] = result[volume_col] / result['volume_ma']

        # Additional filters
        result['price_change'] = result['close'].pct_change()
        result['volatility'] = result['price_change'].rolling(window=14).std()

        return result

class EA2060OptimizedTrader:
    """
    EA2060 819830 - Versão Otimizada
    Baseada nos resultados do backtest com melhorias na estratégia
    """

    def __init__(self):
        self.is_running = False
        self.indicators = OptimizedIndicators()
        self.open_positions = []
        self.magic_numbers = list(range(11111, 11136))
        self.current_magic_index = 0

        # Trading parameters otimizados
        self.symbol = "XAUUSD"
        self.timeframe = mt5.TIMEFRAME_H1
        self.base_lot_size = 0.01
        self.max_positions = 3  # Reduzido para melhor gerenciamento

        # Parâmetros otimizados do backtest
        self.stop_loss_pips = 250
        self.take_profit_pips = 300
        self.risk_per_trade = 0.01

        # Filtros de qualidade de sinal
        self.min_volatility = 0.001  # Volatilidade mínima para entrar
        self.max_spread = 30  # Spread máximo em pontos

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

    def calculate_dynamic_position_size(self, account_balance: float, atr_value: float, volatility: float) -> float:
        """Calculate position size based on market conditions"""
        base_risk = self.risk_per_trade

        # Ajustar risco baseado na volatilidade
        if volatility > 0.002:  # Alta volatilidade
            risk_adjusted = base_risk * 0.7  # Reduzir risco
        elif volatility < 0.0005:  # Baixa volatilidade
            risk_adjusted = base_risk * 1.3  # Aumentar risco
        else:
            risk_adjusted = base_risk

        # Calcular tamanho da posição
        risk_amount = account_balance * risk_adjusted
        position_size = risk_amount / (atr_value * 2)  # Usar 2x ATR como risco

        return max(0.01, round(position_size / 0.01) * 0.01)

    def check_market_conditions(self, df: pd.DataFrame) -> Dict:
        """Check if market conditions are favorable for trading"""
        latest = df.iloc[-1]

        # Verificar spread
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return {'tradeable': False, 'reason': 'No tick data'}

        spread = (tick.ask - tick.bid) * 10000  # Convert to points
        if spread > self.max_spread:
            return {'tradeable': False, 'reason': f'High spread: {spread:.1f}'}

        # Verificar volatilidade
        if latest['volatility'] < self.min_volatility:
            return {'tradeable': False, 'reason': 'Low volatility'}

        # Verificar se há dados suficientes
        if len(df) < 50:
            return {'tradeable': False, 'reason': 'Insufficient data'}

        return {'tradeable': True, 'spread': spread, 'volatility': latest['volatility']}

    def check_buy_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Check for buy signals with enhanced filters"""
        signals = []

        if len(df) < 50:
            return signals

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # Verificar condições do mercado
        market_conditions = self.check_market_conditions(df)
        if not market_conditions['tradeable']:
            return signals

        # Score de sinal (0-10)
        signal_score = 0
        conditions = []

        # 1. EMA crossover (peso: 3)
        if prev['ema_fast'] <= prev['ema_slow'] and latest['ema_fast'] > latest['ema_slow']:
            signal_score += 3
            conditions.append("ema_crossover_bullish")

        # 2. Preço acima das médias (peso: 2)
        if latest['close'] > latest['ema_fast'] and latest['ema_fast'] > latest['ema_slow']:
            signal_score += 2
            conditions.append("price_above_emas")

        # 3. SuperTrend bullish (peso: 2)
        if latest['close'] > latest['supertrend']:
            signal_score += 2
            conditions.append("above_supertrend")

        # 4. RSI na zona ideal (peso: 1)
        if 35 < latest['rsi'] < 65:
            signal_score += 1
            conditions.append("rsi_optimal")

        # 5. Confirmação de volume (peso: 1)
        if latest['volume_ratio'] > 1.0:
            signal_score += 1
            conditions.append("volume_confirm")

        # 6. Bandas de Bollinger (peso: 1)
        if latest['close'] > latest['bb_middle']:
            signal_score += 1
            conditions.append("above_bb_middle")

        # Gerar sinal se score >= 6 (60% do máximo)
        if signal_score >= 6:
            # Calcular SL/TP dinâmicos
            atr_value = latest['atr']
            volatility = latest['volatility']

            # Stop loss adaptativo
            if volatility > 0.002:
                sl_multiplier = 1.5  # Menor SL em alta volatilidade
            elif volatility < 0.0005:
                sl_multiplier = 2.5  # Maior SL em baixa volatilidade
            else:
                sl_multiplier = 2.0

            sl_pips = int(atr_value * 100 * sl_multiplier)
            tp_pips = int(sl_pips * 1.2)  # Risk/Reward de 1:1.2

            signal = {
                'type': 'BUY',
                'price': latest['close'],
                'time': latest.name,
                'stop_loss': latest['close'] - (sl_pips * 0.01),
                'take_profit': latest['close'] + (tp_pips * 0.01),
                'conditions': conditions,
                'score': signal_score,
                'confidence': signal_score / 10.0,
                'sl_pips': sl_pips,
                'tp_pips': tp_pips
            }
            signals.append(signal)

        return signals

    def check_sell_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Check for sell signals with enhanced filters"""
        signals = []

        if len(df) < 50:
            return signals

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # Verificar condições do mercado
        market_conditions = self.check_market_conditions(df)
        if not market_conditions['tradeable']:
            return signals

        # Score de sinal (0-10)
        signal_score = 0
        conditions = []

        # 1. EMA crossover bearish (peso: 3)
        if prev['ema_fast'] >= prev['ema_slow'] and latest['ema_fast'] < latest['ema_slow']:
            signal_score += 3
            conditions.append("ema_crossover_bearish")

        # 2. Preço abaixo das médias (peso: 2)
        if latest['close'] < latest['ema_fast'] and latest['ema_fast'] < latest['ema_slow']:
            signal_score += 2
            conditions.append("price_below_emas")

        # 3. SuperTrend bearish (peso: 2)
        if latest['close'] < latest['supertrend']:
            signal_score += 2
            conditions.append("below_supertrend")

        # 4. RSI na zona ideal (peso: 1)
        if 35 < latest['rsi'] < 65:
            signal_score += 1
            conditions.append("rsi_optimal")

        # 5. Confirmação de volume (peso: 1)
        if latest['volume_ratio'] > 1.0:
            signal_score += 1
            conditions.append("volume_confirm")

        # 6. Bandas de Bollinger (peso: 1)
        if latest['close'] < latest['bb_middle']:
            signal_score += 1
            conditions.append("below_bb_middle")

        # Gerar sinal se score >= 6
        if signal_score >= 6:
            # Calcular SL/TP dinâmicos
            atr_value = latest['atr']
            volatility = latest['volatility']

            # Stop loss adaptativo
            if volatility > 0.002:
                sl_multiplier = 1.5
            elif volatility < 0.0005:
                sl_multiplier = 2.5
            else:
                sl_multiplier = 2.0

            sl_pips = int(atr_value * 100 * sl_multiplier)
            tp_pips = int(sl_pips * 1.2)

            signal = {
                'type': 'SELL',
                'price': latest['close'],
                'time': latest.name,
                'stop_loss': latest['close'] + (sl_pips * 0.01),
                'take_profit': latest['close'] - (tp_pips * 0.01),
                'conditions': conditions,
                'score': signal_score,
                'confidence': signal_score / 10.0,
                'sl_pips': sl_pips,
                'tp_pips': tp_pips
            }
            signals.append(signal)

        return signals

    def place_order(self, signal: Dict, position_size: float) -> bool:
        """Place trading order with enhanced risk management"""
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
                "comment": f"EA2060_Optimized_{signal['type']}_{magic}",
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

            logger.info("="*70)
            logger.info("OPTIMIZED ORDER PLACED SUCCESSFULLY!")
            logger.info(f"Type: {signal['type']}")
            logger.info(f"Symbol: {self.symbol}")
            logger.info(f"Volume: {position_size} lots")
            logger.info(f"Entry Price: {price:.5f}")
            logger.info(f"Stop Loss: {sl:.5f} ({signal['sl_pips']} pips)")
            logger.info(f"Take Profit: {tp:.5f} ({signal['tp_pips']} pips)")
            logger.info(f"Magic Number: {magic}")
            logger.info(f"Signal Score: {signal['score']}/10")
            logger.info(f"Confidence: {signal['confidence']:.2f}")
            logger.info(f"Conditions: {', '.join(signal['conditions'])}")
            logger.info(f"Order Ticket: {result.order}")
            logger.info("="*70)

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
        logger.info("="*90)
        logger.info("EA2060 819830 - OPTIMIZED PYTHON VERSION")
        logger.info("="*90)
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Timeframe: H1")
        logger.info(f"Base Lot Size: {self.base_lot_size}")
        logger.info(f"Max Positions: {self.max_positions}")
        logger.info(f"Risk per Trade: {self.risk_per_trade*100:.1f}%")
        logger.info(f"Magic Numbers: {self.magic_numbers[0]}-{self.magic_numbers[-1]}")
        logger.info("="*90)

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
                df = self.get_historical_data(self.symbol, self.timeframe, 200)
                if df is None:
                    logger.error("Failed to get historical data, retrying...")
                    time.sleep(60)
                    continue

                # Calculate indicators
                df_with_indicators = self.indicators.calculate_all(df)

                # Remove rows with NaN values
                df_clean = df_with_indicators.dropna()

                if len(df_clean) < 50:
                    logger.warning("Insufficient clean data for analysis")
                    time.sleep(60)
                    continue

                # Check market conditions
                market_conditions = self.check_market_conditions(df_clean)
                logger.info(f"Market conditions: {market_conditions}")

                # Check for signals
                buy_signals = self.check_buy_signals(df_clean)
                sell_signals = self.check_sell_signals(df_clean)

                all_signals = buy_signals + sell_signals

                if all_signals:
                    # Get highest confidence signal
                    best_signal = max(all_signals, key=lambda x: x['confidence'])

                    logger.info("OPTIMIZED SIGNAL DETECTED!")
                    logger.info(f"Type: {best_signal['type']}")
                    logger.info(f"Time: {best_signal['time']}")
                    logger.info(f"Price: {best_signal['price']:.5f}")
                    logger.info(f"Score: {best_signal['score']}/10")
                    logger.info(f"Confidence: {best_signal['confidence']:.2f}")
                    logger.info(f"SL/TP: {best_signal['sl_pips']}/{best_signal['tp_pips']} pips")
                    logger.info(f"Conditions: {', '.join(best_signal['conditions'])}")

                    # Calculate dynamic position size
                    account_info = mt5.account_info()
                    latest_data = df_clean.iloc[-1]
                    position_size = self.calculate_dynamic_position_size(
                        account_info.balance,
                        latest_data['atr'],
                        latest_data['volatility']
                    )

                    # Place order
                    success = self.place_order(best_signal, position_size)

                    if success:
                        logger.info("Trade executed successfully, waiting 10 minutes...")
                        time.sleep(600)
                    else:
                        logger.error("Failed to execute trade, waiting 1 minute...")
                        time.sleep(60)
                else:
                    logger.info("No optimized trading signals detected")
                    time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Trading stopped by user")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
        finally:
            self.is_running = False
            logger.info("EA2060 Optimized trading session ended")

    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping EA2060 Optimized trading bot...")
        self.is_running = False

def main():
    """Main function"""
    logger.info("Starting EA2060 819830 Optimized Python Trader...")

    trader = EA2060OptimizedTrader()

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