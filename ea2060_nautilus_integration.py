#!/usr/bin/env python3
"""
EA2060 + Nautilus Trader Integration with LLM
Integração do EA2060 otimizado com o framework Nautilus Trader
Utilizando LLM para tomada de decisão avançada
"""

import asyncio
import os
import sys
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Optional

# Nautilus Trader imports
from nautilus_trader.adapters.betfair.providers import BetfairProvider
from nautilus_trader.adapters.betfair.factories import BetfairInstrumentProvider
from nautilus_trader.adapters.betfair.config import BetfairConfig
from nautilus_trader.config import BacktestRunConfig, BacktestVenueConfig, BacktestDataConfig, BacktestEngineConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Symbol, Venue
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.persistence.external.core import process_files, process_csv_file
from nautilus_trader.persistence.external.readers import CSVReader, ParquetReader, FeatherReader
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy

# Importar EA2060 otimizado
from ea2060_optimized_trader import EA2060OptimizedTrader, OptimizedIndicators

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import MetaTrader5 as mt5

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EA2060LLMStrategy(Strategy):
    """
    Estratégia EA2060 com integração LLM para análise avançada
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.indicators = OptimizedIndicators()
        self.symbol = Symbol("XAUUSD", Venue("MT5"))
        self.current_data = None
        self.llm_analysis = {}
        self.signal_cache = {}

        # Parâmetros otimizados
        self.ema_fast = 6
        self.ema_slow = 18
        self.risk_per_trade = 0.01
        self.max_positions = 3

    def on_start(self) -> None:
        """Inicialização da estratégia"""
        self.log.info("EA2060 LLM Strategy Started")
        self.log.info(f"Symbol: {self.symbol}")
        self.log.info("Ready for LLM-enhanced trading decisions")

    def on_quote_tick(self, tick) -> None:
        """Processar ticks de cotação"""
        # Armazenar dados para análise
        if hasattr(tick, 'bid') and hasattr(tick, 'ask'):
            self.current_data = {
                'bid': float(tick.bid),
                'ask': float(tick.ask),
                'timestamp': tick.ts_event
            }

    def on_trade_tick(self, tick) -> None:
        """Processar ticks de trade"""
        pass

    def on_bar(self, bar) -> None:
        """Analisar barras com LLM"""
        try:
            # Preparar dados para análise
            df = self._prepare_dataframe(bar)

            if df is None or len(df) < 50:
                return

            # Calcular indicadores
            df_indicators = self.indicators.calculate_all(df)
            df_clean = df_indicators.dropna()

            if len(df_clean) < 10:
                return

            latest = df_clean.iloc[-1]

            # Análise LLM
            llm_signal = self._analyze_with_llm(latest, df_clean)

            # Tomar decisão com base na análise LLM
            if llm_signal['action'] == 'BUY' and llm_signal['confidence'] > 0.7:
                self._execute_buy_order(latest, llm_signal)
            elif llm_signal['action'] == 'SELL' and llm_signal['confidence'] > 0.7:
                self._execute_sell_order(latest, llm_signal)
            else:
                self.log.info(f"LLM Analysis: HOLD - Confidence: {llm_signal['confidence']:.2f}")

        except Exception as e:
            self.log.error(f"Error in bar analysis: {e}")

    def _prepare_dataframe(self, bar) -> Optional[pd.DataFrame]:
        """Preparar DataFrame para análise"""
        try:
            # Criar DataFrame com dados históricos do MT5
            if not mt5.initialize():
                self.log.error("Failed to initialize MT5")
                return None

            rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H1, 0, 100)
            mt5.shutdown()

            if rates is None:
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            df = df.rename(columns={'tick_volume': 'volume'})

            return df

        except Exception as e:
            self.log.error(f"Error preparing dataframe: {e}")
            return None

    def _analyze_with_llm(self, current_data: pd.Series, df: pd.DataFrame) -> Dict:
        """Analisar dados com LLM"""
        try:
            # Extrair características principais
            features = self._extract_features(current_data, df)

            # Criar prompt para LLM
            prompt = self._create_llm_prompt(features)

            # Simular análise LLM (em produção, aqui você chamaria uma API LLM real)
            llm_decision = self._simulate_llm_analysis(prompt, features)

            return llm_decision

        except Exception as e:
            self.log.error(f"Error in LLM analysis: {e}")
            return {'action': 'HOLD', 'confidence': 0.0, 'reasoning': 'Analysis failed'}

    def _extract_features(self, current: pd.Series, df: pd.DataFrame) -> Dict:
        """Extrair características para análise LLM"""
        return {
            'price': float(current['close']),
            'ema_fast': float(current['ema_fast']),
            'ema_slow': float(current['ema_slow']),
            'supertrend': float(current['supertrend']),
            'rsi': float(current['rsi']),
            'volume_ratio': float(current['volume_ratio']),
            'volatility': float(current['volatility']),
            'bb_upper': float(current['bb_upper']),
            'bb_lower': float(current['bb_lower']),
            'price_position': self._get_price_position(current),
            'trend_strength': self._calculate_trend_strength(df),
            'momentum': self._calculate_momentum(df),
            'support_resistance': self._find_support_resistance(df)
        }

    def _get_price_position(self, data: pd.Series) -> str:
        """Determinar posição do preço"""
        if data['close'] > data['supertrend'] and data['close'] > data['ema_fast']:
            return 'bullish'
        elif data['close'] < data['supertrend'] and data['close'] < data['ema_fast']:
            return 'bearish'
        else:
            return 'neutral'

    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calcular força da tendência"""
        if len(df) < 20:
            return 0.0

        # Usar inclinação do EMA
        ema_values = df['ema_fast'].tail(20).values
        x = np.arange(len(ema_values))
        slope = np.polyfit(x, ema_values, 1)[0]

        # Normalizar para 0-1
        max_slope = np.std(ema_values) * 0.1
        return min(1.0, max(0.0, abs(slope) / max_slope))

    def _calculate_momentum(self, df: pd.DataFrame) -> float:
        """Calcular momentum"""
        if len(df) < 10:
            return 0.0

        price_change = df['close'].pct_change().tail(10).mean()
        return float(price_change)

    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Encontrar suportes e resistências"""
        if len(df) < 50:
            return {'support': 0, 'resistance': 0}

        highs = df['high'].rolling(window=5).max()
        lows = df['low'].rolling(window=5).min()

        recent_high = highs.tail(20).max()
        recent_low = lows.tail(20).min()

        current_price = df['close'].iloc[-1]

        return {
            'support': float(recent_low),
            'resistance': float(recent_high),
            'distance_to_support': float((current_price - recent_low) / current_price),
            'distance_to_resistance': float((recent_high - current_price) / current_price)
        }

    def _create_llm_prompt(self, features: Dict) -> str:
        """Criar prompt para análise LLM"""
        prompt = f"""
        EA2060 Trading Analysis - Requesting AI Decision

        Current Market Data:
        - Price: ${features['price']:.2f}
        - EMA Fast/Slow: ${features['ema_fast']:.2f} / ${features['ema_slow']:.2f}
        - SuperTrend: ${features['supertrend']:.2f}
        - RSI: {features['rsi']:.1f}
        - Volume Ratio: {features['volume_ratio']:.2f}
        - Volatility: {features['volatility']:.4f}
        - Price Position: {features['price_position']}
        - Trend Strength: {features['trend_strength']:.2f}
        - Momentum: {features['momentum']:.4f}

        Support/Resistance Levels:
        - Support: ${features['support_resistance']['support']:.2f}
        - Resistance: ${features['support_resistance']['resistance']:.2f}
        - Distance to Support: {features['support_resistance']['distance_to_support']:.2%}
        - Distance to Resistance: {features['support_resistance']['distance_to_resistance']:.2%}

        Technical Analysis Rules:
        1. EMA Crossover (Fast > Slow) = Bullish signal
        2. Price above SuperTrend = Bullish momentum
        3. RSI between 35-65 = Neutral zone
        4. Volume ratio > 1.0 = Confirmation
        5. Trend strength > 0.5 = Strong trend

        Risk Management:
        - Max positions: 3
        - Risk per trade: 1%
        - Stop loss: Dynamic based on ATR
        - Take profit: 1.2x risk

        Based on all this data, provide a trading decision:
        - Action: BUY/SELL/HOLD
        - Confidence: 0.0-1.0
        - Reasoning: Brief explanation

        Response format: ACTION|CONFIDENCE|REASONING
        """

        return prompt

    def _simulate_llm_analysis(self, prompt: str, features: Dict) -> Dict:
        """Simular análise LLM (em produção, substituir por API real)"""
        # Lógica simplificada de decisão baseada em regras

        score = 0
        reasoning_parts = []

        # EMA Crossover
        if features['ema_fast'] > features['ema_slow']:
            score += 0.3
            reasoning_parts.append("EMA bullish crossover")
        else:
            score -= 0.3
            reasoning_parts.append("EMA bearish crossover")

        # SuperTrend
        if features['close'] > features['supertrend']:
            score += 0.25
            reasoning_parts.append("Above SuperTrend")
        else:
            score -= 0.25
            reasoning_parts.append("Below SuperTrend")

        # RSI
        if 35 < features['rsi'] < 65:
            score += 0.15
            reasoning_parts.append("RSI in optimal zone")
        elif features['rsi'] > 70:
            score -= 0.1
            reasoning_parts.append("RSI overbought")
        elif features['rsi'] < 30:
            score -= 0.1
            reasoning_parts.append("RSI oversold")

        # Volume
        if features['volume_ratio'] > 1.0:
            score += 0.1
            reasoning_parts.append("Volume confirmation")

        # Trend strength
        if features['trend_strength'] > 0.5:
            score += 0.1
            reasoning_parts.append("Strong trend")
        elif features['trend_strength'] < 0.2:
            score -= 0.05
            reasoning_parts.append("Weak trend")

        # Momentum
        if features['momentum'] > 0:
            score += 0.1
            reasoning_parts.append("Positive momentum")
        else:
            score -= 0.1
            reasoning_parts.append("Negative momentum")

        # Suporte/Resistência
        sr = features['support_resistance']
        if sr['distance_to_resistance'] < 0.01:  # Perto da resistência
            score -= 0.1
            reasoning_parts.append("Near resistance")
        elif sr['distance_to_support'] < 0.01:  # Perto do suporte
            score += 0.1
            reasoning_parts.append("Near support")

        # Converter score em ação
        confidence = abs(score)

        if score > 0.3:
            action = "BUY"
        elif score < -0.3:
            action = "SELL"
        else:
            action = "HOLD"

        reasoning = ", ".join(reasoning_parts)

        return {
            'action': action,
            'confidence': min(1.0, confidence),
            'score': score,
            'reasoning': reasoning
        }

    def _execute_buy_order(self, data: pd.Series, llm_signal: Dict) -> None:
        """Executar ordem de compra"""
        try:
            # Calcular SL/TP
            atr_value = data['atr']
            sl_pips = int(atr_value * 100 * 2.0)  # 2x ATR
            tp_pips = int(sl_pips * 1.2)  # 1:1.2 RR

            stop_loss = data['close'] - (sl_pips * 0.01)
            take_profit = data['close'] + (tp_pips * 0.01)

            # Aqui você executaria a ordem no Nautilus
            self.log.info(f"LLM BUY Signal - Confidence: {llm_signal['confidence']:.2f}")
            self.log.info(f"Reasoning: {llm_signal['reasoning']}")
            self.log.info(f"Entry: {data['close']:.5f}, SL: {stop_loss:.5f}, TP: {take_profit:.5f}")

        except Exception as e:
            self.log.error(f"Error executing buy order: {e}")

    def _execute_sell_order(self, data: pd.Series, llm_signal: Dict) -> None:
        """Executar ordem de venda"""
        try:
            # Calcular SL/TP
            atr_value = data['atr']
            sl_pips = int(atr_value * 100 * 2.0)
            tp_pips = int(sl_pips * 1.2)

            stop_loss = data['close'] + (sl_pips * 0.01)
            take_profit = data['close'] - (tp_pips * 0.01)

            # Aqui você executaria a ordem no Nautilus
            self.log.info(f"LLM SELL Signal - Confidence: {llm_signal['confidence']:.2f}")
            self.log.info(f"Reasoning: {llm_signal['reasoning']}")
            self.log.info(f"Entry: {data['close']:.5f}, SL: {stop_loss:.5f}, TP: {take_profit:.5f}")

        except Exception as e:
            self.log.error(f"Error executing sell order: {e}")

class EA2060NautilusRunner:
    """Runner para executar EA2060 com Nautilus e LLM"""

    def __init__(self):
        self.strategy = EA2060LLMStrategy()

    def run_backtest(self):
        """Executar backtest com Nautilus"""
        try:
            # Configurar dados para backtest
            data_config = BacktestDataConfig(
                catalog_path=str(Path.cwd() / "data"),
                catalog_fs_protocol="memory",  # ou "file", "s3", etc.
            )

            # Configurar venue
            venue_config = BacktestVenueConfig(
                name="MT5",
                oms_type=OmsType.HEDGING,
                account_type=AccountType.CASH,
                base_currency=USD,
                starting_balances=[Money(10_000, USD)],
            )

            # Configurar engine
            engine_config = BacktestEngineConfig(
                trader_id="EA2060_LLM_001",
                log_level="INFO",
            )

            # Configurar run
            config = BacktestRunConfig(
                engine=engine_config,
                data=data_config,
                venues=[venue_config],
                strategies=[self.strategy],
            )

            # Aqui você executaria o backtest
            logger.info("Nautilus backtest configured")
            logger.info("Ready to run with LLM integration")

        except Exception as e:
            logger.error(f"Error in backtest configuration: {e}")

    def run_live(self):
        """Executar em modo live com MT5"""
        try:
            logger.info("Starting EA2060 with LLM integration...")
            logger.info("Note: Full Nautilus integration requires additional setup")

            # Por enquanto, usar implementação direta
            trader = EA2060OptimizedTrader()

            if trader.initialize_mt5():
                trader.run()
            else:
                logger.error("Failed to initialize MT5")

        except Exception as e:
            logger.error(f"Error in live run: {e}")

def main():
    """Função principal"""
    print("="*80)
    print("EA2060 + Nautilus Trader + LLM Integration")
    print("="*80)

    runner = EA2060NautilusRunner()

    # Menu de opções
    print("Select mode:")
    print("1. Backtest with Nautilus")
    print("2. Live Trading (MT5 + LLM)")
    print("3. LLM Analysis Demo")

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        runner.run_backtest()
    elif choice == "2":
        runner.run_live()
    elif choice == "3":
        # Demo de análise LLM
        strategy = EA2060LLMStrategy()

        # Criar dados de exemplo
        sample_data = pd.Series({
            'close': 4020.0,
            'ema_fast': 4010.0,
            'ema_slow': 3995.0,
            'supertrend': 4000.0,
            'rsi': 55.0,
            'volume_ratio': 1.2,
            'volatility': 0.0025,
            'bb_upper': 4030.0,
            'bb_lower': 3990.0,
            'atr': 25.0
        })

        sample_df = pd.DataFrame([sample_data])

        result = strategy._analyze_with_llm(sample_data, sample_df)
        print(f"\\nLLM Analysis Result:")
        print(f"Action: {result['action']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Score: {result['score']:.2f}")
        print(f"Reasoning: {result['reasoning']}")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()