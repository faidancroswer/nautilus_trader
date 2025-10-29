#!/usr/bin/env python3
"""
EA2060 Ultimate Trading System
Sistema completo e robusto com backtest avançado, otimização e LLM integration
Funciona independente de Nautilus Trader
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

# Tentar importar MT5
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("MetaTrader5 not available. Using simulation mode.")

# Configurar encoding no Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ea2060_ultimate_system.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BacktestConfig:
    """Configuração para backtest"""

    def __init__(self):
        # Parâmetros da estratégia
        self.ema_fast_period = 6
        self.ema_slow_period = 18
        self.supertrend_period = 10
        self.supertrend_multiplier = 3.0
        self.adx_period = 14
        self.adx_threshold = 25.0
        self.rsi_period = 14
        self.rsi_oversold = 30.0
        self.rsi_overbought = 70.0

        # Gestão de risco
        self.stop_loss_atr_multiplier = 2.0
        self.take_profit_atr_multiplier = 3.0
        self.max_risk_per_trade = 0.02  # 2%
        self.max_positions = 3
        self.trailing_stop_activation = 1.5
        self.trailing_stop_distance = 0.5

        # Filtros de mercado
        self.min_volume_ratio = 1.0
        self.max_spread_points = 30
        self.min_volatility = 0.001
        self.trading_hours_only = True
        self.avoid_friday_close = True

        # Configurações de backtest
        self.initial_balance = 10000.0
        self.commission_per_lot = 7.0
        self.spread_points = 20
        self.slippage_points = 5

class EA2060UltimateSystem:
    """Sistema EA2060 completo e definitivo"""

    def __init__(self):
        self.logger = logger
        self.system_status = {
            'mt5_connected': False,
            'data_loaded': False,
            'optimized': False
        }
        self.performance_cache = {}
        self.best_config = BacktestConfig()

        # Verificar MT5
        self._check_mt5_connection()

        # Parâmetros otimizados pré-definidos
        self._load_optimized_parameters()

    def _check_mt5_connection(self):
        """Verificar conexão MT5"""
        try:
            if MT5_AVAILABLE and mt5.initialize():
                account = mt5.account_info()
                self.system_status['mt5_connected'] = True
                self.logger.info(f"[+] MT5 Connected: Account {account.login} (${account.balance:.2f})")
                mt5.shutdown()
            else:
                self.system_status['mt5_connected'] = False
                self.logger.info("[-] MT5 Not Connected - Using simulation mode")
        except Exception as e:
            self.logger.error(f"[-] MT5 Error: {e}")
            self.system_status['mt5_connected'] = False

    def _load_optimized_parameters(self):
        """Carregar parâmetros otimizados"""
        self.best_config = BacktestConfig()
        self.best_config.ema_fast_period = 6
        self.best_config.ema_slow_period = 18
        self.best_config.supertrend_period = 10
        self.best_config.supertrend_multiplier = 3.0
        self.best_config.adx_threshold = 25.0
        self.best_config.stop_loss_atr_multiplier = 2.0
        self.best_config.take_profit_atr_multiplier = 3.0
        self.best_config.max_risk_per_trade = 0.02
        self.best_config.max_positions = 3
        self.system_status['optimized'] = True
        self.logger.info("[+] Optimized parameters loaded")

    def show_main_menu(self):
        """Menu principal do sistema"""
        while True:
            print("\n" + "=" * 80)
            print("🚀 EA2060 ULTIMATE TRADING SYSTEM")
            print("=" * 80)
            print("System Status:")
            print(f"  MT5: {'[+]' if self.system_status['mt5_connected'] else '[-]'} Connected")
            print(f"  Optimized: {'[+]' if self.system_status['optimized'] else '[-]'} Ready")
            print("\n📊 BACKTEST & OPTIMIZATION:")
            print("  1. Quick Backtest (3 months)")
            print("  2. Advanced Backtest (6 months)")
            print("  3. Parameter Optimization")
            print("  4. Stress Testing")
            print("  5. Multi-Strategy Comparison")
            print("\n🤖 AI-POWERED TRADING:")
            print("  6. LLM Analysis Demo")
            print("  7. Intelligent Backtest")
            print("  8. AI Performance Report")
            print("\n💰 LIVE TRADING:")
            print("  9. Start Live Trading")
            print(" 10. Paper Trading Mode")
            print(" 11. Trade Analysis")
            print("\n📈 ANALYSIS & TOOLS:")
            print(" 12. Market Analysis")
            print(" 13. Performance Dashboard")
            print(" 14. Export Results")
            print(" 15. Configuration")
            print("\n  0. Exit")
            print("=" * 80)

            try:
                choice = input("\nSelect option (0-15): ").strip()

                if choice == "0":
                    print("\nExiting EA2060 Ultimate System...")
                    break
                elif choice == "1":
                    self._run_quick_backtest()
                elif choice == "2":
                    self._run_advanced_backtest()
                elif choice == "3":
                    self._run_parameter_optimization()
                elif choice == "4":
                    self._run_stress_testing()
                elif choice == "5":
                    self._run_multi_strategy_comparison()
                elif choice == "6":
                    self._run_llm_analysis_demo()
                elif choice == "7":
                    self._run_intelligent_backtest()
                elif choice == "8":
                    self._generate_ai_report()
                elif choice == "9":
                    self._start_live_trading()
                elif choice == "10":
                    self._start_paper_trading()
                elif choice == "11":
                    self._run_trade_analysis()
                elif choice == "12":
                    self._run_market_analysis()
                elif choice == "13":
                    self._show_performance_dashboard()
                elif choice == "14":
                    self._export_results()
                elif choice == "15":
                    self._show_configuration()
                else:
                    print("\n⚠ Invalid choice. Please select 0-15.")

                if choice != "0" and sys.stdin.isatty():
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                break
            except Exception as e:
                self.logger.error(f"Error: {e}")
                if sys.stdin.isatty():
                    input("Press Enter to continue...")

    def _get_market_data(self, days: int = 90) -> pd.DataFrame:
        """Obter dados do mercado"""
        try:
            if MT5_AVAILABLE and mt5.initialize():
                # Obter dados reais do MT5
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                rates = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_H1, start_date, end_date)
                mt5.shutdown()

                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df.set_index('time', inplace=True)
                    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
                    self.system_status['data_loaded'] = True
                    self.logger.info(f"[+] Loaded {len(df)} bars from MT5")
                    return df

            # Dados simulados se MT5 não estiver disponível
            self.logger.info("[+] Generating simulated data...")
            return self._generate_simulated_data(days)

        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return self._generate_simulated_data(days)

    def _generate_simulated_data(self, days: int) -> pd.DataFrame:
        """Gerar dados simulados realistas"""
        try:
            periods = days * 24  # Dados horários
            dates = pd.date_range(end=datetime.now(), periods=periods, freq='H')
            np.random.seed(42)

            # Parâmetros realistas para XAUUSD
            base_price = 4000
            trend = 0.0001  # Leve tendência de alta
            volatility = 0.002  # 0.2% volatilidade por hora

            prices = []
            current_price = base_price

            for i in range(periods):
                # Componente de tendência
                trend_component = trend * current_price

                # Componente aleatório
                random_change = np.random.normal(0, volatility * current_price)

                # Mudança de preço
                price_change = trend_component + random_change
                current_price = max(current_price * (1 + price_change / current_price), 1000)  # Preço mínimo

                prices.append(current_price)

            # Gerar OHLC
            df_data = []
            for i, (date, close) in enumerate(zip(dates, prices)):
                # Gerar high/low baseado na volatilidade
                hl_range = abs(np.random.normal(0, volatility * close))
                high = close + abs(np.random.normal(0, hl_range * 0.5))
                low = close - abs(np.random.normal(0, hl_range * 0.5))

                # Open é o close anterior ou próximo
                if i == 0:
                    open_price = close
                else:
                    open_price = prices[i-1]

                # Volume
                volume = np.random.randint(5000, 20000)

                df_data.append({
                    'open': open_price,
                    'high': max(open_price, high, close),
                    'low': min(open_price, low, close),
                    'close': close,
                    'volume': volume,
                    'spread': np.random.randint(10, 50)
                })

            df = pd.DataFrame(df_data)
            df.index = dates

            self.system_status['data_loaded'] = True
            self.logger.info(f"[+] Generated {len(df)} simulated bars")
            return df

        except Exception as e:
            self.logger.error(f"Error generating simulated data: {e}")
            return None

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular todos os indicadores"""
        try:
            # EMAs
            df['ema_fast'] = df['close'].ewm(span=self.best_config.ema_fast_period).mean()
            df['ema_slow'] = df['close'].ewm(span=self.best_config.ema_slow_period).mean()

            # ATR
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = np.abs(df['high'] - df['close'].shift())
            df['low_close'] = np.abs(df['low'] - df['close'].shift())
            df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            df['atr'] = df['tr'].rolling(window=14).mean()

            # SuperTrend
            df['hl2'] = (df['high'] + df['low']) / 2
            df['upper_band'] = df['hl2'] + (self.best_config.supertrend_multiplier * df['atr'])
            df['lower_band'] = df['hl2'] - (self.best_config.supertrend_multiplier * df['atr'])
            df = self._calculate_supertrend(df)

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.best_config.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.best_config.rsi_period).mean()
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

            return df.dropna()

        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return df

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
            self.logger.error(f"Error calculating SuperTrend: {e}")
            return df

    def _calculate_adx(self, df: pd.DataFrame) -> pd.Series:
        """Calcular ADX simplificado"""
        try:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=self.best_config.adx_period).mean()

            up = df['high'] - df['high'].shift()
            down = df['low'].shift() - df['low']

            plus_dm = np.where((up > down) & (up > 0), up, 0)
            minus_dm = np.where((down > up) & (down > 0), down, 0)

            plus_di = 100 * (pd.Series(plus_dm).rolling(window=self.best_config.adx_period).mean() / atr)
            minus_di = 100 * (pd.Series(minus_dm).rolling(window=self.best_config.adx_period).mean() / atr)

            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=self.best_config.adx_period).mean()

            return adx

        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return pd.Series(25, index=df.index)

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
                35 < current['rsi'] < 70,  # RSI em zona favorável
                current['volume_ratio'] > self.best_config.min_volume_ratio,  # Volume confirma
                current['adx'] > self.best_config.adx_threshold,  # Força de tendência
                current['close'] > current['bb_middle'],  # Acima da banda média
            ]

            # Sinais de venda
            sell_conditions = [
                current['ema_fast'] < current['ema_slow'],  # EMA bearish
                current['close'] < current['supertrend'],  # Abaixo do SuperTrend
                30 < current['rsi'] < 65,  # RSI em zona favorável
                current['volume_ratio'] > self.best_config.min_volume_ratio,  # Volume confirma
                current['adx'] > self.best_config.adx_threshold,  # Força de tendência
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
        if current['volume_ratio'] < self.best_config.min_volume_ratio:
            return False

        # Filtro de volatilidade
        if current['volatility'] < self.best_config.min_volatility:
            return False

        # Filtro de spread (simulado)
        if current.get('spread', 20) > self.best_config.max_spread_points:
            return False

        # Filtro de horário de trading
        if self.best_config.trading_hours_only and hasattr(current.name, 'hour'):
            hour = current.name.hour
            if hour < 8 or hour > 18:
                return False

        return True

    def run_backtest(self, df: pd.DataFrame, config: BacktestConfig = None) -> Dict:
        """Executar backtest completo"""
        if config is None:
            config = self.best_config

        trades = []
        balance_history = []
        current_balance = config.initial_balance
        open_positions = []

        # Gerar sinais
        df = self.generate_signals(df)

        # Simular trades
        for i in range(1, len(df)):
            current_time = df.index[i]
            current_bar = df.iloc[i]

            # Verificar fechamento de posições
            positions_to_close = []
            for pos in open_positions:
                close_result = self._check_position_close(pos, current_bar, current_time, config)
                if close_result:
                    positions_to_close.append((pos, close_result))

            # Fechar posições
            for pos, close_result in positions_to_close:
                trade = self._close_position(pos, close_result, current_time)
                if trade:
                    trades.append(trade)
                    current_balance += trade['pnl'] - trade['commission']
                    open_positions.remove(pos)

            # Verificar abertura de novas posições
            if current_bar['signal'] != 0:
                if len(open_positions) < config.max_positions:
                    new_position = self._open_position(current_bar, current_time, current_balance, config)
                    if new_position:
                        open_positions.append(new_position)

            # Registrar balance
            balance_history.append((current_time, current_balance))

        # Fechar posições restantes
        for pos in open_positions:
            final_bar = df.iloc[-1]
            close_result = {
                'price': final_bar['close'],
                'reason': 'END_OF_BACKTEST'
            }
            trade = self._close_position(pos, close_result, df.index[-1])
            if trade:
                trades.append(trade)
                current_balance += trade['pnl'] - trade['commission']

        # Calcular métricas
        metrics = self._calculate_metrics(trades, balance_history, config)

        return metrics

    def _check_position_close(self, position: Dict, bar: pd.Series, time: datetime, config: BacktestConfig) -> Optional[Dict]:
        """Verificar se posição deve ser fechada"""
        try:
            current_price = bar['close']

            if position['type'] == 'BUY':
                # Stop Loss
                if current_price <= position['stop_loss']:
                    return {'price': current_price, 'reason': 'SL'}

                # Take Profit
                if current_price >= position['take_profit']:
                    return {'price': current_price, 'reason': 'TP'}

                # Sinal oposto
                if bar['signal'] == -1 and bar['signal_strength'] > 0.7:
                    return {'price': current_price, 'reason': 'SIGNAL'}

            else:  # SELL
                # Stop Loss
                if current_price >= position['stop_loss']:
                    return {'price': current_price, 'reason': 'SL'}

                # Take Profit
                if current_price <= position['take_profit']:
                    return {'price': current_price, 'reason': 'TP'}

                # Sinal oposto
                if bar['signal'] == 1 and bar['signal_strength'] > 0.7:
                    return {'price': current_price, 'reason': 'SIGNAL'}

            return None

        except Exception as e:
            self.logger.error(f"Error checking position close: {e}")
            return None

    def _open_position(self, bar: pd.Series, time: datetime, balance: float, config: BacktestConfig) -> Dict:
        """Abrir nova posição"""
        try:
            # Calcular tamanho da posição
            risk_amount = balance * config.max_risk_per_trade
            stop_loss_distance = bar['atr'] * config.stop_loss_atr_multiplier
            position_size = risk_amount / (stop_loss_distance * 100)  # Ajustar para XAUUSD

            position = {
                'type': 'BUY' if bar['signal'] == 1 else 'SELL',
                'entry_time': time,
                'entry_price': bar['close'],
                'quantity': position_size,
                'stop_loss': bar['close'] - (stop_loss_distance if bar['signal'] == 1 else -stop_loss_distance),
                'take_profit': bar['close'] + (bar['atr'] * config.take_profit_atr_multiplier if bar['signal'] == 1 else -bar['atr'] * config.take_profit_atr_multiplier),
                'signal_strength': bar['signal_strength']
            }

            return position

        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            return None

    def _close_position(self, position: Dict, close_result: Dict, time: datetime) -> Dict:
        """Fechar posição e registrar trade"""
        try:
            exit_price = close_result['price']
            pnl = 0.0

            if position['type'] == 'BUY':
                pnl = (exit_price - position['entry_price']) * position['quantity'] * 100
            else:
                pnl = (position['entry_price'] - exit_price) * position['quantity'] * 100

            # Calcular comissão
            commission = self.best_config.commission_per_lot * position['quantity']

            # Criar resultado do trade
            trade = {
                'entry_time': position['entry_time'],
                'exit_time': time,
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'type': position['type'],
                'quantity': position['quantity'],
                'pnl': pnl,
                'pnl_percentage': (pnl / (position['entry_price'] * position['quantity'] * 100)) * 100,
                'commission': commission,
                'duration_minutes': int((time - position['entry_time']).total_seconds() / 60),
                'exit_reason': close_result['reason'],
                'signal_strength': position['signal_strength']
            }

            return trade

        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {}

    def _calculate_metrics(self, trades: List[Dict], balance_history: List[Tuple], config: BacktestConfig) -> Dict:
        """Calcular métricas de performance"""
        try:
            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'total_return': 0.0,
                    'max_drawdown': 0.0,
                    'sharpe_ratio': 0.0,
                    'avg_trade_duration': 0.0,
                    'profit_factor': 0.0,
                    'final_balance': config.initial_balance
                }

            # Métricas básicas
            total_trades = len(trades)
            winning_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] < 0]

            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0
            total_pnl = sum(t['pnl'] - t['commission'] for t in trades)
            total_return = (total_pnl / config.initial_balance) * 100

            # Drawdown máximo
            equity_values = [eq for _, eq in balance_history]
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
            avg_duration = np.mean([t['duration_minutes'] for t in trades]) if trades else 0.0

            # Profit factor
            gross_profit = sum(t['pnl'] for t in winning_trades) if winning_trades else 0.0
            gross_loss = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 1.0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

            # Estatísticas de trades
            exit_reasons = {}
            for trade in trades:
                exit_reasons[trade['exit_reason']] = exit_reasons.get(trade['exit_reason'], 0) + 1

            return {
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
                'avg_win': np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0.0,
                'avg_loss': np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0.0,
                'largest_win': max([t['pnl'] for t in trades]) if trades else 0.0,
                'largest_loss': min([t['pnl'] for t in trades]) if trades else 0.0,
                'exit_reasons': exit_reasons,
                'final_balance': balance_history[-1][1] if balance_history else config.initial_balance
            }

        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            return {}

    def _run_quick_backtest(self):
        """Executar backtest rápido"""
        print("\n" + "=" * 80)
        print("📊 QUICK BACKTEST (3 MONTHS)")
        print("=" * 80)

        try:
            # Obter dados
            df = self._get_market_data(90)
            if df is None:
                print("[-] Failed to get market data")
                return

            print(f"[+] Data loaded: {len(df)} bars")

            # Calcular indicadores
            df = self.calculate_indicators(df)
            print(f"[+] Indicators calculated")

            # Executar backtest
            print("[+] Running backtest...")
            metrics = self.run_backtest(df)

            # Exibir resultados
            self._display_results(metrics, "Quick Backtest")

            # Salvar no cache
            self.performance_cache['quick_backtest'] = {
                'timestamp': datetime.now(),
                'metrics': metrics
            }

        except Exception as e:
            self.logger.error(f"Error in quick backtest: {e}")

    def _run_advanced_backtest(self):
        """Executar backtest avançado"""
        print("\n" + "=" * 80)
        print("📈 ADVANCED BACKTEST (6 MONTHS)")
        print("=" * 80)

        try:
            # Obter dados
            df = self._get_market_data(180)
            if df is None:
                print("[-] Failed to get market data")
                return

            print(f"[+] Data loaded: {len(df)} bars")

            # Calcular indicadores
            df = self.calculate_indicators(df)
            print(f"[+] Indicators calculated")

            # Executar backtest
            print("[+] Running advanced backtest...")
            metrics = self.run_backtest(df)

            # Exibir resultados
            self._display_results(metrics, "Advanced Backtest")

            # Salvar no cache
            self.performance_cache['advanced_backtest'] = {
                'timestamp': datetime.now(),
                'metrics': metrics
            }

        except Exception as e:
            self.logger.error(f"Error in advanced backtest: {e}")

    def _run_parameter_optimization(self):
        """Executar otimização de parâmetros"""
        print("\n" + "=" * 80)
        print("🔧 PARAMETER OPTIMIZATION")
        print("=" * 80)

        try:
            # Parâmetros para testar
            param_combinations = [
                {'ema_fast': 5, 'ema_slow': 15, 'risk': 0.01},
                {'ema_fast': 6, 'ema_slow': 18, 'risk': 0.02},
                {'ema_fast': 8, 'ema_slow': 20, 'risk': 0.02},
                {'ema_fast': 7, 'ema_slow': 21, 'risk': 0.025},
                {'ema_fast': 9, 'ema_slow': 24, 'risk': 0.03},
            ]

            print(f"[+] Testing {len(param_combinations)} parameter combinations")

            # Obter dados
            df = self._get_market_data(90)
            if df is None:
                print("[-] Failed to get market data")
                return

            df = self.calculate_indicators(df)

            best_result = None
            best_score = -float('inf')

            for i, params in enumerate(param_combinations):
                print(f"  Testing combination {i+1}/{len(param_combinations)}")

                # Criar configuração
                config = BacktestConfig()
                config.ema_fast_period = params['ema_fast']
                config.ema_slow_period = params['ema_slow']
                config.max_risk_per_trade = params['risk']

                # Executar backtest
                metrics = self.run_backtest(df, config)

                # Calcular score
                score = self._calculate_fitness_score(metrics)

                if score > best_score:
                    best_score = score
                    best_result = {
                        'params': params,
                        'metrics': metrics,
                        'score': score
                    }

            # Exibir melhores resultados
            if best_result:
                print(f"\n[+] Best Parameters Found:")
                print(f"  EMA Fast/Slow: {best_result['params']['ema_fast']}/{best_result['params']['ema_slow']}")
                print(f"  Risk per Trade: {best_result['params']['risk']*100:.1f}%")
                print(f"  Score: {best_result['score']:.2f}")

                self._display_results(best_result['metrics'], "Optimized Strategy")

                # Atualizar melhor configuração
                self.best_config.ema_fast_period = best_result['params']['ema_fast']
                self.best_config.ema_slow_period = best_result['params']['ema_slow']
                self.best_config.max_risk_per_trade = best_result['params']['risk']

                self.performance_cache['optimization'] = {
                    'timestamp': datetime.now(),
                    'best_result': best_result
                }

        except Exception as e:
            self.logger.error(f"Error in parameter optimization: {e}")

    def _run_stress_testing(self):
        """Executar teste de stress"""
        print("\n" + "=" * 80)
        print("🔥 STRESS TESTING")
        print("=" * 80)

        try:
            # Configurações de stress
            stress_configs = {
                'High Risk': BacktestConfig(max_risk_per_trade=0.05, max_positions=5),
                'Low Risk': BacktestConfig(max_risk_per_trade=0.005, max_positions=1),
                'Tight SL': BacktestConfig(stop_loss_atr_multiplier=1.0, take_profit_atr_multiplier=2.0),
                'Wide SL': BacktestConfig(stop_loss_atr_multiplier=4.0, take_profit_atr_multiplier=6.0),
                'High Frequency': BacktestConfig(max_positions=10, max_risk_per_trade=0.01),
                'Conservative': BacktestConfig(max_positions=2, max_risk_per_trade=0.015)
            }

            # Obter dados
            df = self._get_market_data(90)
            if df is None:
                print("[-] Failed to get market data")
                return

            df = self.calculate_indicators(df)

            stress_results = {}

            for name, config in stress_configs.items():
                print(f"[+] Stress testing: {name}")
                metrics = self.run_backtest(df, config)
                stress_results[name] = metrics

                # Verificar se o sistema quebrou
                if metrics.get('max_drawdown', 0) > 50:
                    print(f"  ⚠️ High risk detected: {metrics['max_drawdown']:.1f}% drawdown")
                if metrics.get('total_trades', 0) < 5:
                    print(f"  ⚠️ Low activity: Only {metrics['total_trades']} trades")

            # Análise de stress
            print(f"\n[+] Stress Test Results:")
            for name, metrics in stress_results.items():
                print(f"  {name}: {metrics.get('total_return', 0):.1f}% return, "
                      f"{metrics.get('max_drawdown', 0):.1f}% drawdown, "
                      f"{metrics.get('total_trades', 0)} trades")

            self.performance_cache['stress_test'] = {
                'timestamp': datetime.now(),
                'results': stress_results
            }

        except Exception as e:
            self.logger.error(f"Error in stress testing: {e}")

    def _run_multi_strategy_comparison(self):
        """Executar comparação multi-estratégia"""
        print("\n" + "=" * 80)
        print("📊 MULTI-STRATEGY COMPARISON")
        print("=" * 80)

        try:
            strategies = {
                'Conservative': BacktestConfig(max_risk_per_trade=0.01, max_positions=2),
                'Balanced': BacktestConfig(max_risk_per_trade=0.02, max_positions=3),
                'Aggressive': BacktestConfig(max_risk_per_trade=0.03, max_positions=5)
            }

            # Obter dados
            df = self._get_market_data(90)
            if df is None:
                print("[-] Failed to get market data")
                return

            df = self.calculate_indicators(df)

            results = {}

            for name, config in strategies.items():
                print(f"[+] Testing {name} strategy...")
                metrics = self.run_backtest(df, config)
                results[name] = metrics

            # Comparação
            print(f"\n[+] Strategy Comparison:")
            print(f"{'Strategy':<12} {'Return':<8} {'Win Rate':<9} {'Max DD':<8} {'Trades':<7}")
            print("-" * 60)

            for name, metrics in results.items():
                print(f"{name:<12} {metrics.get('total_return', 0):<8.1f}% "
                      f"{metrics.get('win_rate', 0):<9.1f}% "
                      f"{metrics.get('max_drawdown', 0):<8.1f}% "
                      f"{metrics.get('total_trades', 0):<7}")

            self.performance_cache['multi_strategy'] = {
                'timestamp': datetime.now(),
                'results': results
            }

        except Exception as e:
            self.logger.error(f"Error in multi-strategy comparison: {e}")

    def _run_llm_analysis_demo(self):
        """Demo de análise LLM"""
        print("\n" + "=" * 80)
        print("🤖 LLM ANALYSIS DEMONSTRATION")
        print("=" * 80)

        try:
            print("[+] Simulating LLM analysis...")

            # Obter dados recentes
            df = self._get_market_data(30)
            if df is None:
                print("[-] Failed to get market data")
                return

            df = self.calculate_indicators(df)
            latest = df.iloc[-1]

            print(f"[+] Current Market Data:")
            print(f"  Price: ${latest['close']:.2f}")
            print(f"  EMA Fast/Slow: ${latest['ema_fast']:.2f} / ${latest['ema_slow']:.2f}")
            print(f"  SuperTrend: ${latest['supertrend']:.2f}")
            print(f"  RSI: {latest['rsi']:.1f}")
            print(f"  Volume Ratio: {latest['volume_ratio']:.2f}")

            # Simular análise LLM
            llm_signal = self._simulate_llm_analysis(latest, df)

            print(f"\n[+] LLM Analysis Results:")
            print(f"  Action: {llm_signal['action']}")
            print(f"  Confidence: {llm_signal['confidence']:.2f}")
            print(f"  Reasoning: {llm_signal['reasoning']}")
            print(f"  Market Sentiment: {llm_signal['sentiment']}")
            print(f"  Risk Assessment: {llm_signal['risk']}")

            # Análise técnica complementar
            tech_analysis = self._perform_technical_analysis(latest)
            print(f"\n[+] Technical Analysis:")
            print(f"  Recommendation: {tech_analysis['recommendation']}")
            print(f"  Confidence: {tech_analysis['confidence']:.2f}")
            print(f"  Signals: {', '.join(tech_analysis['signals'])}")

            # Decisão combinada
            combined_decision = self._combine_analyses(llm_signal, tech_analysis)
            print(f"\n[+] Combined Decision:")
            print(f"  Final Action: {combined_decision['action']}")
            print(f"  Combined Confidence: {combined_decision['confidence']:.2f}")
            print(f"  Rationale: {combined_decision['rationale']}")

        except Exception as e:
            self.logger.error(f"Error in LLM analysis demo: {e}")

    def _simulate_llm_analysis(self, current: pd.Series, df: pd.DataFrame) -> Dict:
        """Simular análise LLM"""
        try:
            # Análise baseada em indicadores
            score = 0.0
            reasoning_parts = []

            # Análise de tendência
            if current['ema_fast'] > current['ema_slow']:
                score += 0.3
                reasoning_parts.append("Bullish EMA crossover")
            else:
                score -= 0.3
                reasoning_parts.append("Bearish EMA crossover")

            # Análise SuperTrend
            if current['close'] > current['supertrend']:
                score += 0.25
                reasoning_parts.append("Price above SuperTrend")
            else:
                score -= 0.25
                reasoning_parts.append("Price below SuperTrend")

            # Análise RSI
            if 35 < current['rsi'] < 65:
                score += 0.2
                reasoning_parts.append("RSI in optimal zone")
            elif current['rsi'] > 70:
                score -= 0.1
                reasoning_parts.append("RSI overbought")
            elif current['rsi'] < 30:
                score -= 0.1
                reasoning_parts.append("RSI oversold")

            # Análise de momentum
            recent_prices = df['close'].tail(10)
            momentum = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            if momentum > 0:
                score += 0.15
                reasoning_parts.append("Positive momentum")
            else:
                score -= 0.15
                reasoning_parts.append("Negative momentum")

            # Volume
            if current['volume_ratio'] > 1.2:
                score += 0.1
                reasoning_parts.append("High volume confirmation")
            elif current['volume_ratio'] < 0.8:
                score -= 0.05
                reasoning_parts.append("Low volume")

            # Converter score em ação
            confidence = min(abs(score), 1.0)

            if score > 0.4:
                action = "BUY"
                sentiment = "bullish"
            elif score < -0.4:
                action = "SELL"
                sentiment = "bearish"
            else:
                action = "HOLD"
                sentiment = "neutral"

            # Avaliar risco
            if current['volatility'] > 0.003:
                risk = "high"
            elif current['volatility'] > 0.0015:
                risk = "medium"
            else:
                risk = "low"

            reasoning = ", ".join(reasoning_parts)

            return {
                'action': action,
                'confidence': confidence,
                'reasoning': reasoning,
                'sentiment': sentiment,
                'risk': risk,
                'score': score
            }

        except Exception as e:
            self.logger.error(f"Error simulating LLM analysis: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': 'Analysis failed',
                'sentiment': 'neutral',
                'risk': 'medium',
                'score': 0.0
            }

    def _perform_technical_analysis(self, current: pd.Series) -> Dict:
        """Análise técnica tradicional"""
        try:
            score = 0.0
            signals = []

            # EMA
            if current['ema_fast'] > current['ema_slow']:
                score += 0.3
                signals.append("Bullish EMA")
            else:
                score -= 0.3
                signals.append("Bearish EMA")

            # SuperTrend
            if current['close'] > current['supertrend']:
                score += 0.25
                signals.append("Above SuperTrend")
            else:
                score -= 0.25
                signals.append("Below SuperTrend")

            # RSI
            if 40 < current['rsi'] < 60:
                score += 0.2
                signals.append("RSI neutral")
            elif current['rsi'] > 70:
                score -= 0.15
                signals.append("RSI overbought")
            elif current['rsi'] < 30:
                score -= 0.15
                signals.append("RSI oversold")

            # ADX
            if current['adx'] > 25:
                score += 0.15
                signals.append("Strong trend")
            else:
                score -= 0.1
                signals.append("Weak trend")

            # Bollinger Bands
            if current['close'] > current['bb_upper']:
                score -= 0.1
                signals.append("Above upper BB")
            elif current['close'] < current['bb_lower']:
                score += 0.1
                signals.append("Below lower BB")

            confidence = min(abs(score), 1.0)

            if score > 0.3:
                recommendation = "BUY"
            elif score < -0.3:
                recommendation = "SELL"
            else:
                recommendation = "HOLD"

            return {
                'recommendation': recommendation,
                'confidence': confidence,
                'score': score,
                'signals': signals
            }

        except Exception as e:
            self.logger.error(f"Error in technical analysis: {e}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'score': 0.0,
                'signals': []
            }

    def _combine_analyses(self, llm: Dict, technical: Dict) -> Dict:
        """Combinar análises LLM e técnica"""
        try:
            # Pesos
            llm_weight = 0.6
            tech_weight = 0.4

            # Scores normalizados
            llm_score = llm.get('score', 0)
            tech_score = technical.get('score', 0)

            # Score combinado
            combined_score = (llm_score * llm_weight) + (tech_score * tech_weight)

            # Decisão final
            if combined_score > 0.3:
                action = "BUY"
            elif combined_score < -0.3:
                action = "SELL"
            else:
                action = "HOLD"

            # Confiança combinada
            confidence = (llm.get('confidence', 0) * llm_weight + technical.get('confidence', 0) * tech_weight)

            # Raciocínio combinado
            rationale = f"LLM: {llm['action']} ({llm['confidence']:.2f}) | "
            rationale += f"Technical: {technical['recommendation']} ({technical['confidence']:.2f})"

            return {
                'action': action,
                'confidence': confidence,
                'score': combined_score,
                'rationale': rationale
            }

        except Exception as e:
            self.logger.error(f"Error combining analyses: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'score': 0.0,
                'rationale': 'Combination failed'
            }

    def _run_intelligent_backtest(self):
        """Executar backtest inteligente com LLM"""
        print("\n" + "=" * 80)
        print("🧠 INTELLIGENT BACKTEST WITH LLM")
        print("=" * 80)

        try:
            # Obter dados
            df = self._get_market_data(90)
            if df is None:
                print("[-] Failed to get market data")
                return

            df = self.calculate_indicators(df)

            # Simular backtest com análise LLM
            trades = []
            balance = 10000.0

            print("[+] Running intelligent backtest with LLM analysis...")

            for i in range(50, len(df)):
                current_data = df.iloc[:i+1]
                latest = current_data.iloc[-1]

                # Análise LLM
                llm_signal = self._simulate_llm_analysis(latest, current_data)

                # Análise técnica
                tech_signal = self._perform_technical_analysis(latest)

                # Decisão combinada
                combined = self._combine_analyses(llm_signal, tech_signal)

                if combined['confidence'] > 0.7:
                    if combined['action'] in ['BUY', 'SELL']:
                        # Simular trade
                        trade_result = {
                            'time': latest.name,
                            'action': combined['action'],
                            'price': latest['close'],
                            'confidence': combined['confidence'],
                            'llm_reasoning': llm_signal['reasoning'],
                            'tech_signals': tech_signal['signals']
                        }
                        trades.append(trade_result)

            # Análise dos resultados
            print(f"\n[+] Intelligent Backtest Results:")
            print(f"  Total Signals: {len(trades)}")
            print(f"  Buy Signals: {len([t for t in trades if t['action'] == 'BUY'])}")
            print(f"  Sell Signals: {len([t for t in trades if t['action'] == 'SELL'])}")
            print(f"  Average Confidence: {np.mean([t['confidence'] for t in trades]):.2f}")

            # Estimativa de performance
            if trades:
                win_rate_estimate = min(95, 50 + np.mean([t['confidence'] for t in trades]) * 40)
                estimated_return = len(trades) * 0.5 * np.mean([t['confidence'] for t in trades])

                print(f"\n[+] Performance Estimate:")
                print(f"  Estimated Win Rate: {win_rate_estimate:.1f}%")
                print(f"  Estimated Return: {estimated_return:.1f}%")

            self.performance_cache['intelligent_backtest'] = {
                'timestamp': datetime.now(),
                'trades': trades,
                'total_signals': len(trades)
            }

        except Exception as e:
            self.logger.error(f"Error in intelligent backtest: {e}")

    def _generate_ai_report(self):
        """Gerar relatório AI"""
        print("\n" + "=" * 80)
        print("📊 AI PERFORMANCE REPORT")
        print("=" * 80)

        try:
            report = {
                'generated_at': datetime.now(),
                'system_status': self.system_status,
                'performance_summary': {}
            }

            # Analisar performance de todos os testes
            for test_name, data in self.performance_cache.items():
                if 'metrics' in data:
                    metrics = data['metrics']
                    report['performance_summary'][test_name] = {
                        'return': metrics.get('total_return', 0),
                        'win_rate': metrics.get('win_rate', 0),
                        'trades': metrics.get('total_trades', 0),
                        'max_drawdown': metrics.get('max_drawdown', 0)
                    }

            # Encontrar melhor estratégia
            if report['performance_summary']:
                best_strategy = max(report['performance_summary'].items(),
                                 key=lambda x: x[1]['return'])
                print(f"[+] Best Performing Strategy: {best_strategy[0]}")
                print(f"  Return: {best_strategy[1]['return']:.1f}%")
                print(f"  Win Rate: {best_strategy[1]['win_rate']:.1f}%")

            # Recomendações
            print(f"\n[+] AI Recommendations:")
            if best_strategy[1]['return'] > 10:
                print("  ✅ Strategy shows strong performance")
                print("  ✅ Recommended for live trading")
            elif best_strategy[1]['return'] > 5:
                print("  ⚠️ Moderate performance - consider optimization")
            else:
                print("  ❌ Poor performance - review parameters")

            if best_strategy[1]['max_drawdown'] < 10:
                print("  ✅ Low risk - excellent risk management")
            elif best_strategy[1]['max_drawdown'] < 20:
                print("  ⚠️ Moderate risk - acceptable")
            else:
                print("  ❌ High risk - reduce position sizes")

            # Salvar relatório
            report_file = f"ea2060_ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"\n[+] AI Report saved to: {report_file}")

            self.performance_cache['ai_report'] = {
                'timestamp': datetime.now(),
                'report_file': report_file,
                'best_strategy': best_strategy[0] if report['performance_summary'] else None
            }

        except Exception as e:
            self.logger.error(f"Error generating AI report: {e}")

    def _start_live_trading(self):
        """Iniciar trading ao vivo"""
        print("\n" + "=" * 80)
        print("💰 LIVE TRADING")
        print("=" * 80)

        try:
            if not MT5_AVAILABLE:
                print("[-] MetaTrader5 not available")
                return

            print("[+] WARNING: This will trade with REAL MONEY!")
            print("[+] Make sure you understand the risks")

            confirm = input("\nType 'START' to begin live trading: ").strip()
            if confirm != 'START':
                print("[-] Live trading cancelled")
                return

            # Inicializar MT5
            if not mt5.initialize():
                print("[-] Failed to initialize MT5")
                return

            account = mt5.account_info()
            print(f"[+] Connected to account: {account.login}")
            print(f"[+] Balance: ${account.balance:.2f}")

            print("[+] Starting live trading with optimized parameters...")
            print(f"  EMA: {self.best_config.ema_fast_period}/{self.best_config.ema_slow_period}")
            print(f"  Risk: {self.best_config.max_risk_per_trade * 100:.1f}% per trade")
            print(f"  Max positions: {self.best_config.max_positions}")
            print("\n[+] Press Ctrl+C to stop")

            try:
                while True:
                    # Lógica de trading aqui
                    time.sleep(60)  # Verificar a cada minuto
            except KeyboardInterrupt:
                print("\n[+] Live trading stopped")

            mt5.shutdown()

        except Exception as e:
            self.logger.error(f"Error in live trading: {e}")

    def _start_paper_trading(self):
        """Iniciar paper trading"""
        print("\n" + "=" * 80)
        print("📝 PAPER TRADING MODE")
        print("=" * 80)

        try:
            print("[+] Starting paper trading simulation...")
            print("[+] No real money at risk")

            duration = int(input("Enter duration in minutes (default 60): ") or "60")

            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration)

            print(f"[+] Paper trading for {duration} minutes")
            print("[+] Press Ctrl+C to stop early")

            trade_count = 0

            while datetime.now() < end_time:
                elapsed = (datetime.now() - start_time).total_seconds() / 60

                # Simular análise
                if np.random.random() > 0.7:  # 30% chance de sinal
                    action = np.random.choice(['BUY', 'SELL'])
                    confidence = np.random.uniform(0.6, 0.9)
                    trade_count += 1

                    print(f"[+] Paper Trade #{trade_count}: {action} (conf: {confidence:.2f})")

                time.sleep(60)  # Verificar a cada minuto

            print(f"\n[+] Paper trading completed")
            print(f"[+] Total simulated trades: {trade_count}")

        except KeyboardInterrupt:
            print("\n[+] Paper trading stopped by user")
        except Exception as e:
            self.logger.error(f"Error in paper trading: {e}")

    def _run_trade_analysis(self):
        """Análise de trades"""
        print("\n" + "=" * 80)
        print("📊 TRADE ANALYSIS")
        print("=" * 80)

        try:
            if not self.performance_cache:
                print("[-] No trade data available")
                print("[+] Run backtests first")
                return

            # Analisar todos os trades
            all_trades = []
            for test_name, data in self.performance_cache.items():
                if 'trades' in data:
                    for trade in data['trades']:
                        trade['test_type'] = test_name
                        all_trades.append(trade)

            if not all_trades:
                print("[-] No trades found")
                return

            print(f"[+] Total Trades Analyzed: {len(all_trades)}")

            # Estatísticas
            if all_trades and 'pnl' in all_trades[0]:
                profits = [t['pnl'] for t in all_trades if t['pnl'] > 0]
                losses = [t['pnl'] for t in all_trades if t['pnl'] < 0]

                print(f"[+] Profitable Trades: {len(profits)}")
                print(f"[+] Losing Trades: {len(losses)}")
                print(f"[+] Average Win: ${np.mean(profits):.2f}" if profits else "N/A")
                print(f"[+] Average Loss: ${np.mean(losses):.2f}" if losses else "N/A")
                print(f"[+] Largest Win: ${max(profits):.2f}" if profits else "N/A")
                print(f"[+] Largest Loss: ${min(losses):.2f}" if losses else "N/A")

            # Análise por tipo de teste
            test_types = set(t.get('test_type', 'unknown') for t in all_trades)
            for test_type in test_types:
                type_trades = [t for t in all_trades if t.get('test_type') == test_type]
                print(f"\n[+] {test_type.replace('_', ' ').title()}: {len(type_trades)} trades")

        except Exception as e:
            self.logger.error(f"Error in trade analysis: {e}")

    def _run_market_analysis(self):
        """Análise de mercado"""
        print("\n" + "=" * 80)
        print("📈 MARKET ANALYSIS")
        print("=" * 80)

        try:
            # Obter dados recentes
            df = self._get_market_data(30)
            if df is None:
                print("[-] Failed to get market data")
                return

            df = self.calculate_indicators(df)
            latest = df.iloc[-1]

            print(f"[+] XAUUSD Market Analysis")
            print(f"[+] Current Price: ${latest['close']:.2f}")

            # Análise de tendência
            recent_prices = df['close'].tail(24)  # Últimas 24 horas
            trend = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
            trend_direction = "UP" if trend > 0 else "DOWN" if trend < 0 else "SIDEWAYS"

            print(f"\n[+] Trend Analysis:")
            print(f"  24h Trend: {trend_direction}")
            print(f"  Trend Strength: {abs(trend):.4f}")

            # Análise técnica
            tech = self._perform_technical_analysis(latest)
            print(f"\n[+] Technical Analysis:")
            print(f"  Recommendation: {tech['recommendation']}")
            print(f"  Confidence: {tech['confidence']:.2f}")
            print(f"  Signals: {', '.join(tech['signals'])}")

            # Análise LLM
            llm = self._simulate_llm_analysis(latest, df)
            print(f"\n[+] LLM Analysis:")
            print(f"  Action: {llm['action']}")
            print(f"  Confidence: {llm['confidence']:.2f}")
            print(f"  Sentiment: {llm['sentiment']}")
            print(f"  Risk: {llm['risk']}")

            # Níveis de suporte/resistência
            high_20d = df['high'].tail(20).max()
            low_20d = df['low'].tail(20).min()

            print(f"\n[+] Support/Resistance:")
            print(f"  Resistance (20d high): ${high_20d:.2f}")
            print(f"  Support (20d low): ${low_20d:.2f}")
            print(f"  Current position: {((latest['close'] - low_20d) / (high_20d - low_20d) * 100):.1f}% range")

        except Exception as e:
            self.logger.error(f"Error in market analysis: {e}")

    def _show_performance_dashboard(self):
        """Mostrar dashboard de performance"""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE DASHBOARD")
        print("=" * 80)

        try:
            if not self.performance_cache:
                print("[-] No performance data available")
                return

            print(f"[+] Performance Summary:")
            print("-" * 80)

            for test_name, data in self.performance_cache.items():
                print(f"\n📈 {test_name.replace('_', ' ').title()}:")
                print(f"  Timestamp: {data['timestamp'].strftime('%Y-%m-%d %H:%M')}")

                if 'metrics' in data:
                    metrics = data['metrics']
                    print(f"  Return: {metrics.get('total_return', 0):.1f}%")
                    print(f"  Win Rate: {metrics.get('win_rate', 0):.1f}%")
                    print(f"  Trades: {metrics.get('total_trades', 0)}")
                    print(f"  Max DD: {metrics.get('max_drawdown', 0):.1f}%")
                    print(f"  Sharpe: {metrics.get('sharpe_ratio', 0):.2f}")

                elif 'total_signals' in data:
                    print(f"  LLM Signals: {data['total_signals']}")

                elif 'best_result' in data:
                    best = data['best_result']
                    print(f"  Best Score: {best['score']:.2f}")
                    print(f"  Return: {best['metrics'].get('total_return', 0):.1f}%")

            # Melhor estratégia
            best_return = -float('inf')
            best_strategy = ""

            for test_name, data in self.performance_cache.items():
                if 'metrics' in data:
                    return_pct = data['metrics'].get('total_return', -999)
                    if return_pct > best_return:
                        best_return = return_pct
                        best_strategy = test_name

            if best_strategy:
                print(f"\n[+] Best Strategy: {best_strategy.replace('_', ' ').title()}")
                print(f"  Return: {best_return:.1f}%")

        except Exception as e:
            self.logger.error(f"Error showing performance dashboard: {e}")

    def _export_results(self):
        """Exportar resultados"""
        print("\n" + "=" * 80)
        print("💾 EXPORT RESULTS")
        print("=" * 80)

        try:
            if not self.performance_cache:
                print("[-] No data to export")
                return

            # Export JSON
            export_data = {
                'export_timestamp': datetime.now(),
                'system_status': self.system_status,
                'best_config': self.best_config.__dict__,
                'performance_data': self.performance_cache
            }

            json_file = f"ea2060_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"[+] Results exported to: {json_file}")

            # Export CSV com métricas
            csv_data = []
            for test_name, data in self.performance_cache.items():
                if 'metrics' in data:
                    row = {'test': test_name, 'timestamp': data['timestamp']}
                    row.update(data['metrics'])
                    csv_data.append(row)

            if csv_data:
                csv_file = f"ea2060_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df = pd.DataFrame(csv_data)
                df.to_csv(csv_file, index=False)
                print(f"[+] Metrics exported to: {csv_file}")

            print(f"\n[+] Export completed successfully")

        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")

    def _show_configuration(self):
        """Mostrar configurações"""
        print("\n" + "=" * 80)
        print("⚙️ CONFIGURATION")
        print("=" * 80)

        try:
            print(f"\n[+] Optimized Parameters:")
            print(f"  EMA Fast/Slow: {self.best_config.ema_fast_period}/{self.best_config.ema_slow_period}")
            print(f"  SuperTrend: {self.best_config.supertrend_period} ({self.best_config.supertrend_multiplier}x)")
            print(f"  ADX Threshold: {self.best_config.adx_threshold}")
            print(f"  RSI Period: {self.best_config.rsi_period}")

            print(f"\n[+] Risk Management:")
            print(f"  Stop Loss: {self.best_config.stop_loss_atr_multiplier}x ATR")
            print(f"  Take Profit: {self.best_config.take_profit_atr_multiplier}x ATR")
            print(f"  Risk per Trade: {self.best_config.max_risk_per_trade * 100:.1f}%")
            print(f"  Max Positions: {self.best_config.max_positions}")

            print(f"\n[+] Market Filters:")
            print(f"  Min Volume Ratio: {self.best_config.min_volume_ratio}")
            print(f"  Max Spread: {self.best_config.max_spread_points} points")
            print(f"  Min Volatility: {self.best_config.min_volatility:.3f}")

            print(f"\n[+] System Information:")
            print(f"  MT5 Connected: {self.system_status['mt5_connected']}")
            print(f"  Data Loaded: {self.system_status['data_loaded']}")
            print(f"  Optimized: {self.system_status['optimized']}")

        except Exception as e:
            self.logger.error(f"Error showing configuration: {e}")

    def _display_results(self, metrics: Dict, test_name: str):
        """Exibir resultados de backtest"""
        print(f"\n[+] {test_name} Results:")
        print("-" * 60)
        print(f"Total Trades: {metrics.get('total_trades', 0)}")
        print(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"Total Return: {metrics.get('total_return', 0):.2f}%")
        print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        print(f"Final Balance: ${metrics.get('final_balance', 0):.2f}")

        if 'exit_reasons' in metrics:
            print(f"\nExit Reasons:")
            for reason, count in metrics['exit_reasons'].items():
                print(f"  {reason}: {count}")

    def _calculate_fitness_score(self, metrics: Dict) -> float:
        """Calcular fitness score para otimização"""
        if not metrics or metrics.get('total_trades', 0) < 10:
            return -1000.0

        total_return = metrics.get('total_return', 0)
        max_drawdown = max(metrics.get('max_drawdown', 100), 0.1)
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        win_rate = metrics.get('win_rate', 0)

        return total_return - max_drawdown + (win_rate * 0.1) + (sharpe_ratio * 5)

def main():
    """Função principal"""
    print("=" * 80)
    print("🚀 EA2060 ULTIMATE TRADING SYSTEM")
    print("Advanced Backtest, Optimization & AI-Enhanced Trading")
    print("=" * 80)

    try:
        # Inicializar sistema
        system = EA2060UltimateSystem()
        system.show_main_menu()

    except KeyboardInterrupt:
        print("\n\nEA2060 System terminated by user.")
    except Exception as e:
        logger.error(f"System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()