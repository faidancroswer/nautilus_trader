#!/usr/bin/env python3
"""
EA2060 Advanced Backtest System with Intelligent Optimization
Sistema completo de backtest com algoritmo genético e otimização inteligente
"""

import sys
import os
import numpy as np
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ea2060_advanced_backtest.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    """Configuração para backtest"""
    # Parâmetros da estratégia
    ema_fast_period: int = 6
    ema_slow_period: int = 18
    supertrend_period: int = 10
    supertrend_multiplier: float = 3.0
    adx_period: int = 14
    adx_threshold: float = 25.0
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

    # Gestão de risco
    stop_loss_atr_multiplier: float = 2.0
    take_profit_atr_multiplier: float = 3.0
    max_risk_per_trade: float = 0.02  # 2%
    max_positions: int = 3
    trailing_stop_activation: float = 1.5
    trailing_stop_distance: float = 0.5

    # Filtros de mercado
    min_volume_ratio: float = 1.0
    max_spread_points: int = 30
    min_volatility: float = 0.001
    trading_hours_only: bool = True
    avoid_friday_close: bool = True

    # Configurações de backtest
    initial_balance: float = 10000.0
    commission_per_lot: float = 7.0
    spread_points: int = 20
    slippage_points: int = 5

@dataclass
class TradeResult:
    """Resultado de um trade"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position_type: str  # 'BUY' or 'SELL'
    quantity: float
    pnl: float
    pnl_percentage: float
    commission: float
    duration_minutes: int
    exit_reason: str  # 'SL', 'TP', 'TRAILING', 'SIGNAL', 'TIMEOUT'

class EA2060AdvancedBacktester:
    """Backtester avançado para EA2060 com otimização inteligente"""

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.trades: List[TradeResult] = []
        self.balance_history: List[Tuple[datetime, float]] = []
        self.equity_history: List[Tuple[datetime, float]] = []
        self.performance_metrics = {}

    def get_historical_data(self, symbol: str, timeframe: str, start_date: datetime,
                          end_date: datetime) -> pd.DataFrame:
        """Obter dados históricos do MT5"""
        try:
            if not mt5.initialize():
                logger.error("Failed to initialize MT5")
                return None

            # Converter timeframe
            mt5_timeframe = getattr(mt5, f'TIMEFRAME_{timeframe}', mt5.TIMEFRAME_H1)

            # Obter dados
            rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)
            mt5.shutdown()

            if rates is None or len(rates) == 0:
                logger.error("No data retrieved")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            df.rename(columns={'tick_volume': 'volume'}, inplace=True)

            logger.info(f"Data loaded: {len(df)} bars from {df.index[0]} to {df.index[-1]}")
            return df

        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular todos os indicadores necessários"""
        try:
            # EMAs
            df['ema_fast'] = df['close'].ewm(span=self.config.ema_fast_period).mean()
            df['ema_slow'] = df['close'].ewm(span=self.config.ema_slow_period).mean()

            # ATR
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = np.abs(df['high'] - df['close'].shift())
            df['low_close'] = np.abs(df['low'] - df['close'].shift())
            df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            df['atr'] = df['tr'].rolling(window=14).mean()

            # SuperTrend
            df['hl2'] = (df['high'] + df['low']) / 2
            df['upper_band'] = df['hl2'] + (self.config.supertrend_multiplier * df['atr'])
            df['lower_band'] = df['hl2'] - (self.config.supertrend_multiplier * df['atr'])

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.config.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.rsi_period).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # Volume
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']

            # Volatilidade
            df['volatility'] = df['close'].pct_change().rolling(window=20).std()

            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (2 * bb_std)
            df['bb_lower'] = df['bb_middle'] - (2 * bb_std)

            # ADX (simplificado)
            df['adx'] = self._calculate_adx(df)

            # Calcular SuperTrend final
            df = self._calculate_supertrend(df)

            return df.dropna()

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df

    def _calculate_adx(self, df: pd.DataFrame) -> pd.Series:
        """Calcular ADX simplificado"""
        try:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=self.config.adx_period).mean()

            up = df['high'] - df['high'].shift()
            down = df['low'].shift() - df['low']

            plus_dm = np.where((up > down) & (up > 0), up, 0)
            minus_dm = np.where((down > up) & (down > 0), down, 0)

            plus_di = 100 * (pd.Series(plus_dm).rolling(window=self.config.adx_period).mean() / atr)
            minus_di = 100 * (pd.Series(minus_dm).rolling(window=self.config.adx_period).mean() / atr)

            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=self.config.adx_period).mean()

            return adx

        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")
            return pd.Series(25, index=df.index)  # Valor padrão

    def _calculate_supertrend(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular SuperTrend"""
        try:
            supertrend = np.zeros(len(df))
            trend = np.zeros(len(df))

            for i in range(1, len(df)):
                if df['close'].iloc[i] <= df['upper_band'].iloc[i-1]:
                    supertrend[i] = df['upper_band'].iloc[i]
                    trend[i] = -1
                elif df['close'].iloc[i] >= df['lower_band'].iloc[i-1]:
                    supertrend[i] = df['lower_band'].iloc[i]
                    trend[i] = 1
                else:
                    supertrend[i] = supertrend[i-1]
                    trend[i] = trend[i-1]

            df['supertrend'] = supertrend
            df['supertrend_trend'] = trend

            return df

        except Exception as e:
            logger.error(f"Error calculating SuperTrend: {e}")
            return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Gerar sinais de trading"""
        df['signal'] = 0  # 0=HOLD, 1=BUY, -1=SELL
        df['signal_strength'] = 0.0

        for i in range(20, len(df)):
            current = df.iloc[i]

            # Verificar condições de mercado
            if not self._check_market_conditions(current):
                continue

            # Sinais de compra
            buy_conditions = [
                current['ema_fast'] > current['ema_slow'],  # EMA bullish
                current['close'] > current['supertrend'],  # Acima do SuperTrend
                current['rsi'] > 35 and current['rsi'] < 70,  # RSI em zona favorável
                current['volume_ratio'] > self.config.min_volume_ratio,  # Volume confirma
                current['adx'] > self.config.adx_threshold,  # Força de tendência
                current['close'] > current['bb_middle'],  # Acima da banda média
            ]

            # Sinais de venda
            sell_conditions = [
                current['ema_fast'] < current['ema_slow'],  # EMA bearish
                current['close'] < current['supertrend'],  # Abaixo do SuperTrend
                current['rsi'] < 65 and current['rsi'] > 30,  # RSI em zona favorável
                current['volume_ratio'] > self.config.min_volume_ratio,  # Volume confirma
                current['adx'] > self.config.adx_threshold,  # Força de tendência
                current['close'] < current['bb_middle'],  # Abaixo da banda média
            ]

            # Calcular força do sinal
            buy_strength = sum(buy_conditions)
            sell_strength = sum(sell_conditions)

            if buy_strength >= 4:  # Pelo menos 4 condições
                df.loc[df.index[i], 'signal'] = 1
                df.loc[df.index[i], 'signal_strength'] = buy_strength / 6.0

            elif sell_strength >= 4:  # Pelo menos 4 condições
                df.loc[df.index[i], 'signal'] = -1
                df.loc[df.index[i], 'signal_strength'] = sell_strength / 6.0

        return df

    def _check_market_conditions(self, current: pd.Series) -> bool:
        """Verificar condições de mercado"""
        # Filtro de volume
        if current['volume_ratio'] < self.config.min_volume_ratio:
            return False

        # Filtro de volatilidade
        if current['volatility'] < self.config.min_volatility:
            return False

        # Filtro de spread (simulado)
        if self.config.spread_points > 30:
            return False

        # Filtro de horário de trading
        if self.config.trading_hours_only:
            hour = current.name.hour if hasattr(current.name, 'hour') else 0
            if hour < 8 or hour > 18:
                return False

        # Evitar sexta-feira tarde
        if self.config.avoid_friday_close:
            weekday = current.name.weekday() if hasattr(current.name, 'weekday') else 0
            hour = current.name.hour if hasattr(current.name, 'hour') else 0
            if weekday == 4 and hour >= 20:
                return False

        return True

    def run_backtest(self, df: pd.DataFrame) -> Dict:
        """Executar backtest completo"""
        logger.info("Starting advanced backtest...")

        # Resetar estados
        self.trades = []
        self.balance_history = []
        self.equity_history = []

        current_balance = self.config.initial_balance
        current_equity = current_balance
        open_positions = []

        # Gerar sinais
        df = self.generate_signals(df)

        # Simular trades
        for i in range(1, len(df)):
            current_time = df.index[i]
            current_bar = df.iloc[i]

            # Atualizar equity com posições abertas
            current_equity = current_balance
            for pos in open_positions:
                unrealized_pnl = self._calculate_unrealized_pnl(pos, current_bar)
                current_equity += unrealized_pnl

            # Registrar equity
            self.equity_history.append((current_time, current_equity))

            # Verificar fechamento de posições
            positions_to_close = []
            for pos in open_positions:
                close_result = self._check_position_close(pos, current_bar, current_time)
                if close_result:
                    positions_to_close.append((pos, close_result))

            # Fechar posições
            for pos, close_result in positions_to_close:
                trade = self._close_position(pos, close_result, current_time)
                if trade:
                    self.trades.append(trade)
                    current_balance += trade.pnl - trade.commission
                    open_positions.remove(pos)

            # Verificar abertura de novas posições
            if current_bar['signal'] != 0:
                if len(open_positions) < self.config.max_positions:
                    new_position = self._open_position(current_bar, current_time, current_balance)
                    if new_position:
                        open_positions.append(new_position)

            # Registrar balance
            self.balance_history.append((current_time, current_balance))

        # Fechar posições restantes no final
        for pos in open_positions:
            final_bar = df.iloc[-1]
            close_result = {
                'price': final_bar['close'],
                'reason': 'END_OF_BACKTEST'
            }
            trade = self._close_position(pos, close_result, df.index[-1])
            if trade:
                self.trades.append(trade)
                current_balance += trade.pnl - trade.commission

        # Calcular métricas de performance
        self._calculate_performance_metrics()

        return self.performance_metrics

    def _open_position(self, bar: pd.Series, time: datetime, balance: float) -> Dict:
        """Abrir nova posição"""
        try:
            # Calcular tamanho da posição baseado no risco
            risk_amount = balance * self.config.max_risk_per_trade
            stop_loss_distance = bar['atr'] * self.config.stop_loss_atr_multiplier
            position_size = risk_amount / (stop_loss_distance * 100)  # Ajustar para XAUUSD

            position = {
                'type': 'BUY' if bar['signal'] == 1 else 'SELL',
                'entry_time': time,
                'entry_price': bar['close'],
                'quantity': position_size,
                'stop_loss': bar['close'] - (stop_loss_distance if bar['signal'] == 1 else -stop_loss_distance),
                'take_profit': bar['close'] + (bar['atr'] * self.config.take_profit_atr_multiplier if bar['signal'] == 1 else -bar['atr'] * self.config.take_profit_atr_multiplier),
                'trail_price': bar['close'],
                'highest_profit': 0.0,
                'signal_strength': bar['signal_strength']
            }

            return position

        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return None

    def _check_position_close(self, position: Dict, bar: pd.Series, time: datetime) -> Optional[Dict]:
        """Verificar se posição deve ser fechada"""
        try:
            current_price = bar['close']

            if position['type'] == 'BUY':
                # Verificar Stop Loss
                if current_price <= position['stop_loss']:
                    return {'price': current_price, 'reason': 'SL'}

                # Verificar Take Profit
                if current_price >= position['take_profit']:
                    return {'price': current_price, 'reason': 'TP'}

                # Verificar Trailing Stop
                profit = current_price - position['entry_price']
                if profit > position['highest_profit']:
                    position['highest_profit'] = profit

                if profit >= (position['trail_price'] - position['entry_price']) * self.config.trailing_stop_activation:
                    new_trail = current_price - (bar['atr'] * self.config.trailing_stop_distance)
                    if new_trail > position['trail_price']:
                        position['trail_price'] = new_trail

                if current_price <= position['trail_price']:
                    return {'price': current_price, 'reason': 'TRAILING'}

                # Verificar sinal oposto
                if bar['signal'] == -1 and bar['signal_strength'] > 0.7:
                    return {'price': current_price, 'reason': 'SIGNAL'}

            else:  # SELL
                # Verificar Stop Loss
                if current_price >= position['stop_loss']:
                    return {'price': current_price, 'reason': 'SL'}

                # Verificar Take Profit
                if current_price <= position['take_profit']:
                    return {'price': current_price, 'reason': 'TP'}

                # Verificar Trailing Stop
                profit = position['entry_price'] - current_price
                if profit > position['highest_profit']:
                    position['highest_profit'] = profit

                if profit >= (position['entry_price'] - position['trail_price']) * self.config.trailing_stop_activation:
                    new_trail = current_price + (bar['atr'] * self.config.trailing_stop_distance)
                    if new_trail < position['trail_price']:
                        position['trail_price'] = new_trail

                if current_price >= position['trail_price']:
                    return {'price': current_price, 'reason': 'TRAILING'}

                # Verificar sinal oposto
                if bar['signal'] == 1 and bar['signal_strength'] > 0.7:
                    return {'price': current_price, 'reason': 'SIGNAL'}

            return None

        except Exception as e:
            logger.error(f"Error checking position close: {e}")
            return None

    def _close_position(self, position: Dict, close_result: Dict, time: datetime) -> Optional[TradeResult]:
        """Fechar posição e registrar trade"""
        try:
            exit_price = close_result['price']
            pnl = 0.0

            if position['type'] == 'BUY':
                pnl = (exit_price - position['entry_price']) * position['quantity'] * 100
            else:
                pnl = (position['entry_price'] - exit_price) * position['quantity'] * 100

            # Calcular comissão
            commission = self.config.commission_per_lot * position['quantity']

            # Criar resultado do trade
            trade = TradeResult(
                entry_time=position['entry_time'],
                exit_time=time,
                entry_price=position['entry_price'],
                exit_price=exit_price,
                position_type=position['type'],
                quantity=position['quantity'],
                pnl=pnl,
                pnl_percentage=(pnl / (position['entry_price'] * position['quantity'] * 100)) * 100,
                commission=commission,
                duration_minutes=int((time - position['entry_time']).total_seconds() / 60),
                exit_reason=close_result['reason']
            )

            return trade

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return None

    def _calculate_unrealized_pnl(self, position: Dict, bar: pd.Series) -> float:
        """Calcular PnL não realizado"""
        try:
            current_price = bar['close']

            if position['type'] == 'BUY':
                pnl = (current_price - position['entry_price']) * position['quantity'] * 100
            else:
                pnl = (position['entry_price'] - current_price) * position['quantity'] * 100

            return pnl

        except Exception as e:
            logger.error(f"Error calculating unrealized PnL: {e}")
            return 0.0

    def _calculate_performance_metrics(self):
        """Calcular métricas de performance"""
        try:
            if not self.trades:
                self.performance_metrics = {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'total_return': 0.0,
                    'max_drawdown': 0.0,
                    'sharpe_ratio': 0.0,
                    'avg_trade_duration': 0.0,
                    'profit_factor': 0.0
                }
                return

            # Métricas básicas
            total_trades = len(self.trades)
            winning_trades = [t for t in self.trades if t.pnl > 0]
            losing_trades = [t for t in self.trades if t.pnl < 0]

            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0
            total_pnl = sum(t.pnl - t.commission for t in self.trades)
            total_return = (total_pnl / self.config.initial_balance) * 100

            # Drawdown máximo
            equity_values = [eq for _, eq in self.equity_history]
            peak = equity_values[0]
            max_drawdown = 0.0

            for equity in equity_values:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)

            # Sharpe ratio (simplificado)
            if len(equity_values) > 1:
                returns = pd.Series(equity_values).pct_change().dropna()
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0.0
            else:
                sharpe_ratio = 0.0

            # Duração média dos trades
            avg_duration = np.mean([t.duration_minutes for t in self.trades]) if self.trades else 0.0

            # Profit factor
            gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0.0
            gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 1.0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

            # Estatísticas de trades
            exit_reasons = {}
            for trade in self.trades:
                exit_reasons[trade.exit_reason] = exit_reasons.get(trade.exit_reason, 0) + 1

            self.performance_metrics = {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate * 100,
                'total_pnl': total_pnl,
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'avg_trade_duration': avg_duration,
                'profit_factor': profit_factor,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'avg_win': np.mean([t.pnl for t in winning_trades]) if winning_trades else 0.0,
                'avg_loss': np.mean([t.pnl for t in losing_trades]) if losing_trades else 0.0,
                'largest_win': max([t.pnl for t in self.trades]) if self.trades else 0.0,
                'largest_loss': min([t.pnl for t in self.trades]) if self.trades else 0.0,
                'exit_reasons': exit_reasons,
                'final_balance': self.balance_history[-1][1] if self.balance_history else self.config.initial_balance,
                'config': asdict(self.config)
            }

        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            self.performance_metrics = {}

class GeneticOptimizer:
    """Otimizador genético para parâmetros do EA2060"""

    def __init__(self, population_size: int = 30, generations: int = 20):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = 0.1
        self.elite_size = 5

    def optimize(self, df: pd.DataFrame) -> Tuple[BacktestConfig, Dict]:
        """Executar otimização genética"""
        logger.info("Starting genetic optimization...")

        # Parâmetros a otimizar
        param_ranges = {
            'ema_fast_period': (3, 12),
            'ema_slow_period': (12, 30),
            'supertrend_period': (8, 15),
            'supertrend_multiplier': (2.0, 4.0),
            'adx_threshold': (20.0, 35.0),
            'stop_loss_atr_multiplier': (1.5, 3.0),
            'take_profit_atr_multiplier': (2.0, 5.0),
            'max_risk_per_trade': (0.01, 0.05),
            'trailing_stop_activation': (1.0, 2.5),
            'trailing_stop_distance': (0.3, 1.0)
        }

        # Gerar população inicial
        population = self._generate_initial_population(param_ranges)
        best_config = None
        best_fitness = -float('inf')
        optimization_history = []

        for generation in range(self.generations):
            logger.info(f"Generation {generation + 1}/{self.generations}")

            # Avaliar fitness
            fitness_scores = []
            for i, config in enumerate(population):
                backtester = EA2060AdvancedBacktester(config)
                metrics = backtester.run_backtest(df)

                # Função de fitness (múltiplos critérios)
                fitness = self._calculate_fitness(metrics)
                fitness_scores.append(fitness)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_config = config
                    logger.info(f"New best fitness: {fitness:.4f}")

            # Registar histórico
            generation_metrics = {
                'generation': generation + 1,
                'best_fitness': max(fitness_scores),
                'avg_fitness': np.mean(fitness_scores),
                'best_config': asdict(population[np.argmax(fitness_scores)])
            }
            optimization_history.append(generation_metrics)

            # Seleção e reprodução
            population = self._evolve_population(population, fitness_scores, param_ranges)

        # Otimização final no melhor parâmetro
        logger.info("Final optimization on best parameters...")
        final_backtester = EA2060AdvancedBacktester(best_config)
        final_metrics = final_backtester.run_backtest(df)

        return best_config, {
            'best_config': asdict(best_config),
            'best_fitness': best_fitness,
            'final_metrics': final_metrics,
            'optimization_history': optimization_history
        }

    def _generate_initial_population(self, param_ranges: Dict) -> List[BacktestConfig]:
        """Gerar população inicial"""
        population = []

        for _ in range(self.population_size):
            config = BacktestConfig()

            for param, (min_val, max_val) in param_ranges.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    setattr(config, param, np.random.randint(min_val, max_val + 1))
                else:
                    setattr(config, param, np.random.uniform(min_val, max_val))

            population.append(config)

        return population

    def _calculate_fitness(self, metrics: Dict) -> float:
        """Calcular fitness de uma configuração"""
        if not metrics or metrics.get('total_trades', 0) < 10:
            return -1000.0

        # Múltiplos critérios
        total_return = metrics.get('total_return', 0)
        max_drawdown = max(metrics.get('max_drawdown', 100), 0.1)
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        win_rate = metrics.get('win_rate', 0)
        profit_factor = metrics.get('profit_factor', 0)

        # Calcular fitness (penalizar drawdown alto)
        fitness = (total_return * 0.3 +
                  sharpe_ratio * 10 * 0.2 +
                  win_rate * 0.2 +
                  min(profit_factor, 5) * 10 * 0.2 -
                  max_drawdown * 0.1)

        # Bônus para número de trades
        total_trades = metrics.get('total_trades', 0)
        if 20 <= total_trades <= 200:
            fitness += 10

        return fitness

    def _evolve_population(self, population: List[BacktestConfig],
                          fitness_scores: List[float], param_ranges: Dict) -> List[BacktestConfig]:
        """Evoluir população para próxima geração"""
        # Seleção por torneio
        selected = self._tournament_selection(population, fitness_scores)

        # Crossover
        offspring = []
        for i in range(0, len(selected) - 1, 2):
            parent1 = selected[i]
            parent2 = selected[i + 1]
            child1, child2 = self._crossover(parent1, parent2, param_ranges)
            offspring.extend([child1, child2])

        # Mutação
        for individual in offspring:
            if np.random.random() < self.mutation_rate:
                self._mutate(individual, param_ranges)

        # Elitismo - manter os melhores
        elite_indices = np.argsort(fitness_scores)[-self.elite_size:]
        elite = [population[i] for i in elite_indices]

        # Combinar elite e offspring
        new_population = elite + offspring[:self.population_size - self.elite_size]

        return new_population

    def _tournament_selection(self, population: List[BacktestConfig],
                            fitness_scores: List[float], tournament_size: int = 3) -> List[BacktestConfig]:
        """Seleção por torneio"""
        selected = []

        for _ in range(len(population)):
            tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            winner_index = tournament_indices[np.argmax(tournament_fitness)]
            selected.append(population[winner_index])

        return selected

    def _crossover(self, parent1: BacktestConfig, parent2: BacktestConfig,
                  param_ranges: Dict) -> Tuple[BacktestConfig, BacktestConfig]:
        """Crossover entre dois pais"""
        child1 = BacktestConfig()
        child2 = BacktestConfig()

        for param in param_ranges.keys():
            if np.random.random() < 0.5:
                setattr(child1, param, getattr(parent1, param))
                setattr(child2, param, getattr(parent2, param))
            else:
                setattr(child1, param, getattr(parent2, param))
                setattr(child2, param, getattr(parent1, param))

        return child1, child2

    def _mutate(self, individual: BacktestConfig, param_ranges: Dict):
        """Mutação de um indivíduo"""
        param_to_mutate = np.random.choice(list(param_ranges.keys()))
        min_val, max_val = param_ranges[param_to_mutate]

        if isinstance(min_val, int) and isinstance(max_val, int):
            new_value = np.random.randint(min_val, max_val + 1)
        else:
            new_value = np.random.uniform(min_val, max_val)

        setattr(individual, param_to_mutate, new_value)

def main():
    """Função principal para executar backtest avançado"""
    print("=" * 80)
    print("EA2060 Advanced Backtest System with Genetic Optimization")
    print("=" * 80)

    try:
        # Configurar data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 ano de dados

        logger.info(f"Backtest period: {start_date.date()} to {end_date.date()}")

        # Obter dados
        backtester = EA2060AdvancedBacktester()
        df = backtester.get_historical_data('XAUUSD', 'H1', start_date, end_date)

        if df is None:
            logger.error("Failed to get historical data")
            return

        # Calcular indicadores
        df = backtester.calculate_indicators(df)
        logger.info(f"Data prepared: {len(df)} bars with indicators")

        # Menu de opções
        print("\nSelect backtest mode:")
        print("1. Single run with default parameters")
        print("2. Genetic optimization")
        print("3. Grid search optimization")
        print("4. Quick test (last 3 months)")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            # Backtest único
            config = BacktestConfig()
            backtester = EA2060AdvancedBacktester(config)
            metrics = backtester.run_backtest(df)
            print_results(metrics, config)

        elif choice == "2":
            # Otimização genética
            optimizer = GeneticOptimizer(population_size=20, generations=10)
            best_config, optimization_results = optimizer.optimize(df)

            print("\n" + "=" * 80)
            print("GENETIC OPTIMIZATION RESULTS")
            print("=" * 80)
            print(f"Best Fitness Score: {optimization_results['best_fitness']:.4f}")
            print("\nBest Parameters:")
            for param, value in optimization_results['best_config'].items():
                print(f"  {param}: {value}")

            print(f"\nFinal Performance:")
            print_results(optimization_results['final_metrics'], best_config)

        elif choice == "3":
            # Grid search (simplificado)
            print("\nRunning grid search optimization...")
            best_config, best_metrics = run_grid_search(df)
            print_results(best_metrics, best_config)

        elif choice == "4":
            # Teste rápido
            logger.info("Running quick test on last 3 months...")
            quick_df = df.tail(2160)  # ~3 meses de dados H1
            config = BacktestConfig()
            backtester = EA2060AdvancedBacktester(config)
            metrics = backtester.run_backtest(quick_df)
            print_results(metrics, config)

        else:
            print("Invalid choice")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()

def run_grid_search(df: pd.DataFrame) -> Tuple[BacktestConfig, Dict]:
    """Executar grid search simplificado"""
    logger.info("Running grid search...")

    # Parâmetros para testar
    ema_fast_options = [5, 6, 7, 8]
    ema_slow_options = [16, 18, 20, 22]
    sl_multipliers = [1.5, 2.0, 2.5]
    tp_multipliers = [2.5, 3.0, 3.5]

    best_config = BacktestConfig()
    best_fitness = -float('inf')
    best_metrics = {}

    total_combinations = len(ema_fast_options) * len(ema_slow_options) * len(sl_multipliers) * len(tp_multipliers)
    current = 0

    for ema_fast in ema_fast_options:
        for ema_slow in ema_slow_options:
            for sl_mult in sl_multipliers:
                for tp_mult in tp_multipliers:
                    current += 1
                    logger.info(f"Testing combination {current}/{total_combinations}")

                    config = BacktestConfig(
                        ema_fast_period=ema_fast,
                        ema_slow_period=ema_slow,
                        stop_loss_atr_multiplier=sl_mult,
                        take_profit_atr_multiplier=tp_mult
                    )

                    backtester = EA2060AdvancedBacktester(config)
                    metrics = backtester.run_backtest(df)
                    fitness = calculate_simple_fitness(metrics)

                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_config = config
                        best_metrics = metrics
                        logger.info(f"New best: {fitness:.4f}")

    return best_config, best_metrics

def calculate_simple_fitness(metrics: Dict) -> float:
    """Calcular fitness simples para grid search"""
    if not metrics or metrics.get('total_trades', 0) < 10:
        return -1000.0

    total_return = metrics.get('total_return', 0)
    max_drawdown = max(metrics.get('max_drawdown', 100), 0.1)
    win_rate = metrics.get('win_rate', 0)

    return total_return - max_drawdown + (win_rate * 0.1)

def print_results(metrics: Dict, config: BacktestConfig):
    """Imprimir resultados do backtest"""
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)

    if not metrics:
        print("No results available")
        return

    print(f"Total Trades: {metrics.get('total_trades', 0)}")
    print(f"Winning Trades: {metrics.get('winning_trades', 0)}")
    print(f"Losing Trades: {metrics.get('losing_trades', 0)}")
    print(f"Win Rate: {metrics.get('win_rate', 0):.2f}%")
    print(f"Total PnL: ${metrics.get('total_pnl', 0):.2f}")
    print(f"Total Return: {metrics.get('total_return', 0):.2f}%")
    print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
    print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    print(f"Avg Win: ${metrics.get('avg_win', 0):.2f}")
    print(f"Avg Loss: ${metrics.get('avg_loss', 0):.2f}")
    print(f"Largest Win: ${metrics.get('largest_win', 0):.2f}")
    print(f"Largest Loss: ${metrics.get('largest_loss', 0):.2f}")
    print(f"Avg Trade Duration: {metrics.get('avg_trade_duration', 0):.0f} minutes")
    print(f"Final Balance: ${metrics.get('final_balance', 0):.2f}")

    print(f"\nExit Reasons:")
    for reason, count in metrics.get('exit_reasons', {}).items():
        print(f"  {reason}: {count}")

    print(f"\nStrategy Parameters:")
    print(f"  EMA Fast: {config.ema_fast_period}")
    print(f"  EMA Slow: {config.ema_slow_period}")
    print(f"  SuperTrend Period: {config.supertrend_period}")
    print(f"  SuperTrend Multiplier: {config.supertrend_multiplier}")
    print(f"  ADX Threshold: {config.adx_threshold}")
    print(f"  Stop Loss ATR Multiplier: {config.stop_loss_atr_multiplier}")
    print(f"  Take Profit ATR Multiplier: {config.take_profit_atr_multiplier}")
    print(f"  Max Risk per Trade: {config.max_risk_per_trade * 100:.1f}%")
    print(f"  Max Positions: {config.max_positions}")
    print(f"  Trailing Stop Activation: {config.trailing_stop_activation}")
    print(f"  Trailing Stop Distance: {config.trailing_stop_distance}")

    print("=" * 80)

if __name__ == "__main__":
    main()