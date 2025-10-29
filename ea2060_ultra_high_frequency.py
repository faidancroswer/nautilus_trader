#!/usr/bin/env python3
"""
EA2060 Ultra High Frequency Trader - Maximum Operations
Versão ultra otimizada para o máximo de operações e ganhos
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

# Configurar encoding no Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ea2060_ultra_hf.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Importar MT5
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("MetaTrader5 not available. Using simulation mode.")

class UltraHighFrequencyConfig:
    """Configuração ultra otimizada para máxima frequência"""

    def __init__(self):
        # EMAs ultra rápidas
        self.ema_ultra_fast = 1      # EMA de 1 período
        self.ema_fast = 2              # EMA de 2 períodos
        self.ema_medium = 4             # EMA de 4 períodos
        self.ema_slow = 8              # EMA de 8 períodos

        # SuperTrend ultra sensível
        self.supertrend_period = 5
        self.supertrend_multiplier = 1.0  # Muito sensível

        # RSI ultra rápido
        self.rsi_period = 5
        self.rsi_oversold = 20           # Mais amplo
        self.rsi_overbought = 80

        # Gestão de risco para alta frequência
        self.stop_loss_atr_multiplier = 0.8  # Stop ultra apertado
        self.take_profit_atr_multiplier = 1.2  # Take ultra rápido
        self.max_risk_per_trade = 0.01      # 1% por trade
        self.max_positions = 15              # Muitas posições

        # Filtros mínimos para mais sinais
        self.min_volume_ratio = 0.3          # Volume muito baixo
        self.max_spread_points = 100          # Aceita spread grande
        self.min_volatility = 0.0002         # Volatilidade mínima

        # Timeframes múltiplos
        self.use_m1_signals = True           # Usar M1 principal
        self.use_m5_confirmation = True      # Confirmação M5
        self.use_m15_trend = True            # Tendência M15

        # Estratégias adicionais
        self.use_micro_scalping = True       # Micro scalping
        self.use_reversal_scalping = True   # Reversão rápida
        self.use_breakout_scraping = True   # Breakout scalping
        self.use_momentum_scraping = True   # Momentum scalping
        self.use_arbitrage = True           # Arbitragem mini

        # Parâmetros de execução
        self.initial_balance = 10000.0
        self.commission_per_lot = 5.0       # Comissão menor
        self.spread_points = 20
        self.slippage_points = 3

class EA2060UltraHighFrequencyTrader:
    """Trader Ultra Alta Frequência EA2060"""

    def __init__(self, config: UltraHighFrequencyConfig = None):
        self.config = config or UltraHighFrequencyConfig()
        self.logger = logger
        self.mt5_connected = False
        self.check_mt5_connection()

    def check_mt5_connection(self):
        """Verificar conexão MT5"""
        try:
            if MT5_AVAILABLE and mt5.initialize():
                account = mt5.account_info()
                self.mt5_connected = True
                print(f"[+] MT5 Connected: Account {account.login} (${account.balance:.2f})")
                mt5.shutdown()
            else:
                self.mt5_connected = False
                print("[-] MT5 Not Connected - Using simulation mode")
        except Exception as e:
            print(f"[-] MT5 Error: {e}")
            self.mt5_connected = False

    def get_ultra_high_frequency_data(self, days: int = 7) -> Dict[str, pd.DataFrame]:
        """Obter dados ultra alta frequência"""
        try:
            data = {}

            if MT5_AVAILABLE and mt5.initialize():
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                # Obter M1 para operações ultra rápidas
                m1_rates = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_M1, start_date, end_date)
                if m1_rates is not None and len(m1_rates) > 0:
                    df_m1 = pd.DataFrame(m1_rates)
                    df_m1['time'] = pd.to_datetime(df_m1['time'], unit='s')
                    df_m1.set_index('time', inplace=True)
                    df_m1.rename(columns={'tick_volume': 'volume'}, inplace=True)
                    data['M1'] = df_m1

                # Obter M5 para contexto
                m5_rates = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_M5, start_date, end_date)
                if m5_rates is not None and len(m5_rates) > 0:
                    df_m5 = pd.DataFrame(m5_rates)
                    df_m5['time'] = pd.to_datetime(df_m5['time'], unit='s')
                    df_m5.set_index('time', inplace=True)
                    df_m5.rename(columns={'tick_volume': 'volume'}, inplace=True)
                    data['M5'] = df_m5

                mt5.shutdown()

                print(f"[+] Loaded ultra high-frequency data from MT5")
                return data

            # Dados simulados
            print("[+] Generating simulated ultra high-frequency data...")
            return self.generate_ultra_high_frequency_data(days)

        except Exception as e:
            print(f"Error getting ultra high-frequency data: {e}")
            return self.generate_ultra_high_frequency_data(days)

    def generate_ultra_high_frequency_data(self, days: int) -> Dict[str, pd.DataFrame]:
        """Gerar dados simulados ultra alta frequência"""
        try:
            data = {}

            # Gerar dados M1
            m1_periods = days * 24 * 60
            m1_dates = pd.date_range(end=datetime.now(), periods=m1_periods, freq='T')
            np.random.seed(42)

            base_price = 4000
            volatility = 0.003  # Maior volatilidade

            prices = []
            current_price = base_price

            for i in range(m1_periods):
                # Variação por minuto
                minute_volatility = volatility / np.sqrt(60)
                random_change = np.random.normal(0, minute_volatility * current_price)
                micro_trend = np.sin(i / 100) * 0.0001 * current_price  # Micro tendência

                price_change = random_change + micro_trend
                current_price = max(current_price * (1 + price_change / current_price), 1000)
                prices.append(current_price)

            # Criar DataFrame M1 com realismo de mercado
            m1_data = []
            for i in range(m1_periods):
                hl_range = abs(np.random.normal(0, volatility * current_price * 0.5))
                high = prices[i] + abs(np.random.normal(0, hl_range * 0.3))
                low = prices[i] - abs(np.random.normal(0, hl_range * 0.3))

                if i == 0:
                    open_price = prices[i]
                else:
                    open_price = m1_data[-1]['close']

                # Volume com picos
                base_volume = np.random.randint(500, 3000)
                volume_spike = np.random.random() > 0.95
                if volume_spike:
                    volume = base_volume * np.random.randint(2, 5)
                else:
                    volume = base_volume

                m1_data.append({
                    'open': open_price,
                    'high': max(open_price, high, prices[i]),
                    'low': min(open_price, low, prices[i]),
                    'close': prices[i],
                    'volume': volume,
                    'spread': np.random.randint(5, 50)
                })

            df_m1 = pd.DataFrame(m1_data)
            df_m1.index = m1_dates
            data['M1'] = df_m1

            # Gerar M5 (agregando M1)
            m5_data = []
            for i in range(0, len(m1_data), 5):
                chunk = m1_data[i:i+5]
                if len(chunk) == 5:
                    m5_candle = {
                        'open': chunk[0]['open'],
                        'high': max(c['high'] for c in chunk),
                        'low': min(c['low'] for c in chunk),
                        'close': chunk[-1]['close'],
                        'volume': sum(c['volume'] for c in chunk),
                        'spread': np.mean([c['spread'] for c in chunk])
                    }
                    m5_data.append(m5_candle)

            m5_dates = [m1_dates[i] for i in range(0, len(m1_dates), 5)]
            df_m5 = pd.DataFrame(m5_data)
            df_m5.index = m5_dates
            data['M5'] = df_m5

            print(f"[+] Generated ultra high-frequency data: M1({len(df_m1)}), M5({len(df_m5)}) bars")
            return data

        except Exception as e:
            print(f"Error generating ultra high-frequency data: {e}")
            return {}

    def calculate_ultra_high_frequency_indicators(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Calcular indicadores ultra alta frequência"""
        try:
            processed_data = {}

            # Processar M1 para operações ultra rápidas
            if 'M1' in data:
                df_m1 = data['M1'].copy()

                # EMAs ultra rápidas
                df_m1['ema_ultra'] = df_m1['close'].ewm(span=self.config.ema_ultra_fast).mean()
                df_m1['ema_fast'] = df_m1['close'].ewm(span=self.config.ema_fast).mean()
                df_m1['ema_medium'] = df_m1['close'].ewm(span=self.config.ema_medium).mean()
                df_m1['ema_slow'] = df_m1['close'].ewm(span=self.config.ema_slow).mean()

                # ATR ultra rápido
                df_m1['high_low'] = df_m1['high'] - df_m1['low']
                df_m1['tr'] = df_m1[['high_low']].max(axis=1)
                df_m1['atr'] = df_m1['tr'].rolling(window=5).mean()

                # SuperTrend ultra sensível
                df_m1['hl2'] = (df_m1['high'] + df_m1['low']) / 2
                df_m1['upper_band'] = df_m1['hl2'] + (self.config.supertrend_multiplier * df_m1['atr'])
                df_m1['lower_band'] = df_m1['hl2'] - (self.config.supertrend_multiplier * df_m1['atr'])

                supertrend = np.zeros(len(df_m1))
                for i in range(1, len(df_m1)):
                    if df_m1['close'].iloc[i] <= df_m1['upper_band'].iloc[i-1]:
                        supertrend[i] = df_m1['upper_band'].iloc[i]
                    elif df_m1['close'].iloc[i] >= df_m1['lower_band'].iloc[i-1]:
                        supertrend[i] = df_m1['lower_band'].iloc[i]
                    else:
                        supertrend[i] = supertrend[i-1]
                df_m1['supertrend'] = supertrend

                # RSI ultra rápido
                delta = df_m1['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=self.config.rsi_period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.rsi_period).mean()
                rs = gain / loss
                df_m1['rsi'] = 100 - (100 / (1 + rs))

                # Volume
                df_m1['volume_ma'] = df_m1['volume'].rolling(window=3).mean()
                df_m1['volume_ratio'] = df_m1['volume'] / df_m1['volume_ma']

                # Momentum ultra rápido
                df_m1['momentum_1'] = df_m1['close'].pct_change(periods=1)
                df_m1['momentum_2'] = df_m1['close'].pct_change(periods=2)
                df_m1['momentum_3'] = df_m1['close'].pct_change(periods=3)

                # Micro tendências
                df_m1['micro_trend_5'] = df_m1['close'].rolling(window=5).mean()
                df_m1['micro_trend_10'] = df_m1['close'].rolling(window=10).mean()

                # Micro support/resistance
                df_m1['micro_resistance'] = df_m1['high'].rolling(window=3).max()
                df_m1['micro_support'] = df_m1['low'].rolling(window=3).min()

                # Taxa de variação
                df_m1['tick_volatility'] = (df_m1['high'] - df_m1['low']) / df_m1['close']

                processed_data['M1'] = df_m1.dropna()

            # Processar M5 para contexto
            if 'M5' in data:
                df_m5 = data['M5'].copy()

                # EMAs para M5
                df_m5['ema_fast'] = df_m5['close'].ewm(span=3).mean()
                df_m5['ema_slow'] = df_m5['close'].ewm(span=8).mean()

                # ATR para M5
                df_m5['high_low'] = df_m5['high'] - df_m5['low']
                df_m5['tr'] = df_m5[['high_low']].max(axis=1)
                df_m5['atr'] = df_m5['tr'].rolling(window=7).mean()

                # RSI para M5
                delta = df_m5['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
                rs = gain / loss
                df_m5['rsi'] = 100 - (100 / (1 + rs))

                # Volume para M5
                df_m5['volume_ma'] = df_m5['volume'].rolling(window=5).mean()
                df_m5['volume_ratio'] = df_m5['volume'] / df_m5['volume_ma']

                processed_data['M5'] = df_m5.dropna()

            print(f"[+] Calculated ultra high-frequency indicators for {len(processed_data)} timeframes")
            return processed_data

        except Exception as e:
            print(f"Error calculating ultra high-frequency indicators: {e}")
            return data

    def generate_ultra_high_frequency_signals(self, indicators_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Gerar sinais ultra alta frequência"""
        try:
            signals_data = {}

            # Sinais M1 para operações ultra rápidas
            if 'M1' in indicators_data:
                df_m1 = indicators_data['M1'].copy()
                df_m1['m1_signal'] = 0
                df_m1['m1_strength'] = 0.0
                df_m1['signal_type'] = 'none'

                # Obter tendência M5 para contexto
                m5_trend = 0
                if 'M5' in indicators_data:
                    df_m5 = indicators_data['M5']
                    # Calcular tendência M5
                    df_m5['m5_trend'] = np.where(df_m5['ema_fast'] > df_m5['ema_slow'], 1, -1)
                    m5_trend_avg = df_m5['m5_trend'].rolling(window=3).mean()

                for i in range(3, len(df_m1)):
                    current = df_m1.iloc[i]

                    # Sinal 1: Ultra Fast Crossover (1 vs 2 períodos)
                    ultra_fast_signal = 0
                    if current['ema_ultra'] > current['ema_fast']:
                        ultra_fast_signal = 1
                    elif current['ema_ultra'] < current['ema_fast']:
                        ultra_fast_signal = -1

                    # Sinal 2: Fast Crossover (2 vs 4 períodos)
                    fast_signal = 0
                    if current['ema_fast'] > current['ema_medium']:
                        fast_signal = 1
                    elif current['ema_fast'] < current['ema_medium']:
                        fast_signal = -1

                    # Sinal 3: SuperTrend
                    supertrend_signal = 0
                    if current['close'] > current['supertrend']:
                        supertrend_signal = 1
                    elif current['close'] < current['supertrend']:
                        supertrend_signal = -1

                    # Sinal 4: Momentum (períodos 1-3)
                    momentum_signal = 0
                    if current['momentum_1'] > 0.001:
                        momentum_signal = 1
                    elif current['momentum_1'] < -0.001:
                        momentum_signal = -1

                    # Sinal 5: Micro Scalping (pullback)
                    micro_scalp_signal = 0
                    if current['ema_ultra'] > current['ema_slow'] and current['close'] < current['ema_ultra']:
                        if abs(current['close'] - current['ema_ultra']) / current['atr'] < 0.5:
                            micro_scalp_signal = 1
                    elif current['ema_ultra'] < current['ema_slow'] and current['close'] > current['ema_ultra']:
                        if abs(current['close'] - current['ema_ultra']) / current['atr'] < 0.5:
                            micro_scalp_signal = -1

                    # Sinal 6: Breakout Micro
                    breakout_signal = 0
                    if current['close'] > current['micro_resistance'] * 1.0002:  # Breakout mínimo
                        breakout_signal = 1
                    elif current['close'] < current['micro_support'] * 0.9998:
                        breakout_signal = -1

                    # Sinal 7: Reversão Extrema
                    reversal_signal = 0
                    if current['rsi'] < self.config.rsi_oversold and current['momentum_3'] < -0.02:
                        reversal_signal = 1
                    elif current['rsi'] > self.config.rsi_overbought and current['momentum_3'] > 0.02:
                        reversal_signal = -1

                    # Combinar sinais com pesos
                    signal_score = (
                        ultra_fast_signal * 3 +
                        fast_signal * 2 +
                        supertrend_signal * 2 +
                        momentum_signal * 2 +
                        micro_scalp_signal * 4 +
                        breakout_signal * 3 +
                        reversal_signal * 3
                    )

                    # Adicionar contexto M5
                    if i < len(df_m1) and 'M5' in indicators_data:
                        # Alinhar timestamp M1 com M5
                        current_time = df_m1.index[i]
                        m5_idx = None
                        try:
                            m5_idx = indicators_data['M5'].index.get_loc(current_time)
                            if m5_idx is not None and m5_idx > 0:
                                m5_trend = indicators_data['M5']['m5_trend'].iloc[m5_idx]
                        except:
                            m5_trend = 0

                        signal_score += m5_trend * 2

                    # Volume confirmation
                    volume_boost = 1.0
                    if current['volume_ratio'] > 1.5:
                        volume_boost = 1.5
                    elif current['volume_ratio'] < 0.5:
                        volume_boost = 0.5

                    final_score = signal_score * volume_boost

                    # Gerar sinal final
                    if final_score >= 6:  # Threshold baixo para mais sinais
                        df_m1.loc[df_m1.index[i], 'm1_signal'] = 1
                        df_m1.loc[df_m1.index[i], 'm1_strength'] = min(final_score / 15, 1.0)

                        # Identificar tipo de sinal dominante
                        if micro_scalp_signal == 1 or micro_scalp_signal == -1:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'micro_scalp'
                        elif breakout_signal == 1 or breakout_signal == -1:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'breakout'
                        elif reversal_signal == 1 or reversal_signal == -1:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'reversal'
                        elif abs(momentum_signal) > 0:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'momentum'
                        else:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'trend'

                    elif final_score <= -6:
                        df_m1.loc[df_m1.index[i], 'm1_signal'] = -1
                        df_m1.loc[df_m1.index[i], 'm1_strength'] = min(abs(final_score) / 15, 1.0)

                        if micro_scalp_signal == 1 or micro_scalp_signal == -1:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'micro_scalp'
                        elif breakout_signal == 1 or breakout_signal == -1:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'breakout'
                        elif reversal_signal == 1 or reversal_signal == -1:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'reversal'
                        elif abs(momentum_signal) > 0:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'momentum'
                        else:
                            df_m1.loc[df_m1.index[i], 'signal_type'] = 'trend'

                signals_data['M1'] = df_m1

            print(f"[+] Generated ultra high-frequency signals for {len(signals_data)} timeframes")
            return signals_data

        except Exception as e:
            print(f"Error generating ultra high-frequency signals: {e}")
            return indicators_data

    def run_ultra_high_frequency_backtest(self, days: int = 7) -> Dict:
        """Executar backtest ultra alta frequência"""
        try:
            print("=" * 80)
            print("🚀 EA2060 ULTRA HIGH FREQUENCY BACKTEST")
            print("Maximum Operations and Profits Optimization")
            print("=" * 80)

            # 1. Obter dados
            print(f"\n📊 STEP 1: Loading Ultra High-Frequency Data ({days} days)")
            print("-" * 60)
            data = self.get_ultra_high_frequency_data(days)
            if not data:
                print("[-] Failed to get market data")
                return {}

            print(f"[+] Data loaded: {[(tf, len(df)) for tf, df in data.items()]}")

            # 2. Calcular indicadores
            print("\n🔧 STEP 2: Calculating Ultra High-Frequency Indicators")
            print("-" * 60)
            indicators_data = self.calculate_ultra_high_frequency_indicators(data)

            # 3. Gerar sinais
            print("\n📈 STEP 3: Generating Ultra High-Frequency Signals")
            print("-" * 60)
            signals_data = self.generate_ultra_high_frequency_signals(indicators_data)

            # 4. Executar backtest
            print("\n🔄 STEP 4: Running Ultra High-Frequency Backtest")
            print("-" * 60)
            metrics = self.simulate_ultra_high_frequency_trading(indicators_data, signals_data)

            # 5. Exibir resultados
            self.display_ultra_high_frequency_results(metrics)

            return metrics

        except Exception as e:
            print(f"Error in ultra high-frequency backtest: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def simulate_ultra_high_frequency_trading(self, indicators_data: Dict, signals_data: Dict) -> Dict:
        """Simular trading ultra alta frequência"""
        try:
            initial_balance = self.config.initial_balance
            balance = initial_balance
            trades = []
            open_positions = []

            # Usar M1 como timeframe principal
            if 'M1' not in indicators_data or 'M1' not in signals_data:
                return {}

            df_m1 = indicators_data['M1']
            df_signals = signals_data['M1']

            print(f"[+] Processing {len(df_m1)} M1 bars for ultra high-frequency trading...")

            # Simular trades
            for i in range(10, len(df_m1)):
                current_time = df_m1.index[i]
                current_bar = df_m1.iloc[i]
                current_signal = df_signals.iloc[i]

                # Verificar fechamento de posições
                positions_to_close = []
                for pos in open_positions:
                    if self.should_close_position_ultra(pos, current_bar, i, df_m1):
                        positions_to_close.append((pos, current_bar['close'], current_time))

                # Fechar posições
                for pos, close_price, close_time in positions_to_close:
                    trade = self.close_position_ultra(pos, close_price, close_time)
                    if trade:
                        trades.append(trade)
                        balance += trade['pnl']
                        open_positions.remove(pos)

                # Verificar abertura de novas posições
                if len(open_positions) < self.config.max_positions:
                    if current_signal['m1_signal'] != 0:
                        # Verificar se não há posição aberta recentemente no mesmo tipo
                        recent_same_type = any(
                            pos['type'] == ('BUY' if current_signal['m1_signal'] > 0 else 'SELL') and
                            (current_time - pos['entry_time']).total_seconds() < 60  # 1 minuto cooldown
                            for pos in open_positions
                        )

                        if not recent_same_type:
                            new_position = self.open_position_ultra(
                                current_bar, current_time, balance,
                                current_signal['m1_signal'],
                                current_signal.get('signal_type', 'trend'),
                                current_signal['m1_strength']
                            )
                            if new_position:
                                open_positions.append(new_position)

            # Calcular métricas
            metrics = self.calculate_ultra_metrics(trades, initial_balance)
            metrics['config'] = self.config.__dict__

            return metrics

        except Exception as e:
            print(f"Error simulating ultra high-frequency trading: {e}")
            return {}

    def should_close_position_ultra(self, position: Dict, bar: pd.Series, bar_index: int, df: pd.DataFrame) -> bool:
        """Verificar fechamento ultra rápido"""
        try:
            current_time = bar.name

            # Stop Loss e Take Profit
            if position['type'] == 'BUY':
                if bar['close'] <= position['stop_loss']:
                    return True
                if bar['close'] >= position['take_profit']:
                    return True
            else:  # SELL
                if bar['close'] >= position['stop_loss']:
                    return True
                if bar['close'] <= position['take_profit']:
                    return True

            # Timeout ultra rápido (máximo 10 minutos para scalping)
            position_duration = (current_time - position['entry_time']).total_seconds() / 60
            if position['signal_type'] in ['micro_scalp', 'breakout'] and position_duration > 10:
                return True
            elif position['signal_type'] == 'reversal' and position_duration > 15:
                return True
            elif position_duration > 30:
                return True

            # Reversão de sinal rápido
            if bar_index > 3:
                recent_signals = df['m1_signal'].iloc[bar_index-3:bar_index]
                if position['type'] == 'BUY' and (recent_signals == -1).sum() >= 2:
                    return True
                elif position['type'] == 'SELL' and (recent_signals == 1).sum() >= 2:
                    return True

            # Break even ultra rápido
            if position_duration > 2:
                if position['type'] == 'BUY':
                    current_pnl_pct = (bar['close'] - position['entry_price']) / position['entry_price']
                    if current_pnl_pct > 0.001:  # 0.1% de lucro
                        position['stop_loss'] = position['entry_price']
                else:  # SELL
                    current_pnl_pct = (position['entry_price'] - bar['close']) / position['entry_price']
                    if current_pnl_pct > 0.001:
                        position['stop_loss'] = position['entry_price']

            return False

        except Exception as e:
            print(f"Error checking ultra position close: {e}")
            return False

    def open_position_ultra(self, bar: pd.Series, time: datetime, balance: float, signal: int, signal_type: str, signal_strength: float) -> Dict:
        """Abrir posição ultra rápida"""
        try:
            # Ajustar risco baseado no tipo de sinal
            risk_multipliers = {
                'micro_scalp': 0.5,
                'breakout': 0.7,
                'reversal': 0.8,
                'momentum': 0.6,
                'trend': 1.0
            }

            risk_multiplier = risk_multipliers.get(signal_type, 1.0)
            risk_amount = balance * self.config.max_risk_per_trade * risk_multiplier

            # ATR ultra rápido
            atr_value = bar.get('atr', bar['high'] - bar['low'])
            stop_distance = atr_value * self.config.stop_loss_atr_multiplier

            # Ajuste ainda menor para scalping
            if signal_type == 'micro_scalp':
                stop_distance *= 0.5

            position_size = risk_amount / (stop_distance * 100)

            # Take Profit ultra rápido
            tp_multipliers = {
                'micro_scalp': 1.0,
                'breakout': 1.2,
                'reversal': 1.3,
                'momentum': 1.1,
                'trend': 1.2
            }

            tp_multiplier = tp_multipliers.get(signal_type, self.config.take_profit_atr_multiplier)

            position = {
                'type': 'BUY' if signal > 0 else 'SELL',
                'entry_time': time,
                'entry_price': bar['close'],
                'quantity': position_size,
                'stop_loss': bar['close'] - (stop_distance if signal > 0 else -stop_distance),
                'take_profit': bar['close'] + (atr_value * tp_multiplier if signal > 0 else -atr_value * tp_multiplier),
                'signal_type': signal_type,
                'signal_strength': signal_strength
            }

            return position

        except Exception as e:
            print(f"Error opening ultra position: {e}")
            return None

    def close_position_ultra(self, position: Dict, close_price: float, time: datetime) -> Dict:
        """Fechar posição ultra rápida"""
        try:
            if position['type'] == 'BUY':
                pnl = (close_price - position['entry_price']) * position['quantity'] * 100
            else:
                pnl = (position['entry_price'] - close_price) * position['quantity'] * 100

            # Comissão ultra baixa para alta frequência
            commission = 3.0 * position['quantity']

            trade = {
                'entry_time': position['entry_time'],
                'exit_time': time,
                'entry_price': position['entry_price'],
                'exit_price': close_price,
                'type': position['type'],
                'signal_type': position['signal_type'],
                'quantity': position['quantity'],
                'pnl': pnl,
                'pnl_percentage': (pnl / (position['entry_price'] * position['quantity'] * 100)) * 100,
                'commission': commission,
                'duration_minutes': int((time - position['entry_time']).total_seconds() / 60),
                'signal_strength': position['signal_strength']
            }

            return trade

        except Exception as e:
            print(f"Error closing ultra position: {e}")
            return {}

    def calculate_ultra_metrics(self, trades: List[Dict], initial_balance: float) -> Dict:
        """Calcular métricas ultra alta frequência"""
        try:
            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'total_return': 0.0,
                    'avg_trade': 0.0,
                    'final_balance': initial_balance,
                    'trades_per_hour': 0,
                    'trades_per_day': 0
                }

            total_trades = len(trades)
            winning_trades = [t for t in trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / total_trades * 100
            total_pnl = sum(t['pnl'] - t['commission'] for t in trades)
            total_return = (total_pnl / initial_balance) * 100
            avg_trade = total_pnl / total_trades

            # Separar trades por tipo
            trade_types = {}
            for trade in trades:
                signal_type = trade.get('signal_type', 'unknown')
                if signal_type not in trade_types:
                    trade_types[signal_type] = []
                trade_types[signal_type].append(trade)

            # Calcular trades por hora/dia
            if trades:
                time_span = (trades[-1]['exit_time'] - trades[0]['entry_time']).total_seconds()
                trades_per_hour = total_trades / max(time_span / 3600, 1)
                trades_per_day = total_trades / max(time_span / 86400, 1)

            return {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': total_trades - len(winning_trades),
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'total_return': total_return,
                'avg_trade': avg_trade,
                'largest_win': max([t['pnl'] for t in trades]),
                'largest_loss': min([t['pnl'] for t in trades]),
                'avg_duration': np.mean([t['duration_minutes'] for t in trades]),
                'shortest_duration': min([t['duration_minutes'] for t in trades]),
                'longest_duration': max([t['duration_minutes'] for t in trades]),
                'final_balance': initial_balance + total_pnl,
                'trades_per_hour': trades_per_hour,
                'trades_per_day': trades_per_day,
                'trade_types': trade_types,
                'trade_type_performance': {
                    signal_type: {
                        'count': len(type_trades),
                        'win_rate': len([t for t in type_trades if t['pnl'] > 0]) / len(type_trades) * 100,
                        'avg_pnl': np.mean([t['pnl'] for t in type_trades]),
                        'avg_duration': np.mean([t['duration_minutes'] for t in type_trades])
                    }
                    for signal_type, type_trades in trade_types.items()
                }
            }

        except Exception as e:
            print(f"Error calculating ultra metrics: {e}")
            return {}

    def display_ultra_high_frequency_results(self, metrics: Dict):
        """Exibir resultados ultra alta frequência"""
        try:
            print("\n🚀 ULTRA HIGH FREQUENCY BACKTEST RESULTS")
            print("=" * 80)

            if not metrics:
                print("[-] No results available")
                return

            print(f"📊 Performance Overview:")
            print(f"  Total Trades: {metrics.get('total_trades', 0)}")
            print(f"  Win Rate: {metrics.get('win_rate', 0):.1f}%")
            print(f"  Total Return: {metrics.get('total_return', 0):.2f}%")
            print(f"  Final Balance: ${metrics.get('final_balance', 0):.2f}")
            print(f"  Average Trade: ${metrics.get('avg_trade', 0):.2f}")
            print(f"  Largest Win: ${metrics.get('largest_win', 0):.2f}")
            print(f"  Largest Loss: ${metrics.get('largest_loss', 0):.2f}")

            print(f"\n⚡ Ultra High-Frequency Metrics:")
            print(f"  Trades per Hour: {metrics.get('trades_per_hour', 0):.1f}")
            print(f"  Trades per Day: {metrics.get('trades_per_day', 0):.1f}")
            print(f"  Average Duration: {metrics.get('avg_duration', 0):.1f} minutes")
            print(f"  Shortest Duration: {metrics.get('shortest_duration', 0):.1f} minutes")
            print(f"  Longest Duration: {metrics.get('longest_duration', 0):.1f} minutes")

            print(f"\n📈 Signal Type Breakdown:")
            trade_types = metrics.get('trade_types', {})
            trade_performance = metrics.get('trade_type_performance', {})

            for signal_type, type_trades in trade_types.items():
                perf = trade_performance.get(signal_type, {})
                print(f"  {signal_type}:")
                print(f"    Count: {len(type_trades)}")
                print(f"    Win Rate: {perf.get('win_rate', 0):.1f}%")
                print(f"    Avg PnL: ${perf.get('avg_pnl', 0):.2f}")
                print(f"    Avg Duration: {perf.get('avg_duration', 0):.1f} min")

            # Avaliação de performance
            total_return = metrics.get('total_return', 0)
            trades_per_hour = metrics.get('trades_per_hour', 0)

            print(f"\n🎯 Ultra Performance Assessment:")
            if total_return > 50 and trades_per_hour > 50:
                grade = "A++ (EXCELLENT - Maximum profitability with ultra high frequency)"
            elif total_return > 30 and trades_per_hour > 30:
                grade = "A+ (EXCELLENT - High profitability with high frequency)"
            elif total_return > 20 and trades_per_hour > 20:
                grade = "A (VERY GOOD - Excellent returns with good frequency)"
            elif total_return > 10:
                grade = "B+ (GOOD - Profitable with decent frequency)"
            elif trades_per_hour > 50:
                grade = "B (ULTRA HIGH FREQUENCY - Amazing activity but improve profitability)"
            elif total_return > 0:
                grade = "C+ (ACCEPTABLE - Profitable but needs optimization)"
            else:
                grade = "D (NEEDS IMPROVEMENT)"

            print(f"  Overall Grade: {grade}")

            # Métricas de eficiência
            if metrics.get('avg_duration', 0) < 10:
                print(f"  ✅ Ultra-fast execution (< 10 min avg duration)")
            elif metrics.get('avg_duration', 0) < 30:
                print(f"  ✅ Fast execution (< 30 min avg duration)")

            if metrics.get('trades_per_hour', 0) > 30:
                print(f"  ✅ Ultra-high frequency (> 30 trades/hour)")
            elif metrics.get('trades_per_hour', 0) > 10:
                print(f"  ✅ High frequency (> 10 trades/hour)")

            if metrics.get('win_rate', 0) > 45:
                print(f"  ✅ Good win rate (> 45%)")

            print("=" * 80)

        except Exception as e:
            print(f"Error displaying ultra results: {e}")

def main():
    """Função principal"""
    try:
        print("=" * 80)
        print("🚀 EA2060 ULTRA HIGH FREQUENCY TRADER")
        print("Maximum Operations and Profits Optimization")
        print("=" * 80)

        # Criar trader ultra alta frequência
        trader = EA2060UltraHighFrequencyTrader()

        # Executar backtest
        metrics = trader.run_ultra_high_frequency_backtest(days=7)

        if metrics:
            # Salvar resultados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"ea2060_ultra_hf_results_{timestamp}.json"

            with open(output_file, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)

            print(f"\n[+] Detailed results saved to: {output_file}")

            # Recomendações específicas
            print(f"\n💡 Ultra High-Frequency Recommendations:")

            if metrics.get('trades_per_hour', 0) < 20:
                print(f"  - Lower signal thresholds to increase frequency")
                print(f"  - Add more signal types for diversification")
                print(f" - Reduce position size to allow more concurrent trades")

            if metrics.get('win_rate', 0) < 40:
                print(f"  - Increase signal strength requirements")
                print(f"  - Add volume confirmation filters")
                print(f"  - Implement momentum confirmation")

            if metrics.get('avg_duration', 0) > 20:
                print(f"  - Implement tighter stop losses (0.5x ATR)")
                print(f"  - Use faster take profit levels (1.0x ATR)")
                print(f"  - Add break-even triggers after 2-3 minutes")

            if metrics.get('total_return', 0) < 20:
                print(f"  - Optimize signal combination weights")
                print(f"  - Increase position size for profitable signal types")
                print(f"  - Implement dynamic risk adjustment")

            print(f"\n✅ Ultra high-frequency system optimized for maximum operations!")

    except KeyboardInterrupt:
        print("\n\nUltra high-frequency backtest cancelled by user.")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()