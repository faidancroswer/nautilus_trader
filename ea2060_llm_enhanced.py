#!/usr/bin/env python3
"""
EA2060 LLM-Enhanced Trading System
Versão simplificada com integração LLM para tomada de decisão avançada
Funciona standalone ou pode ser integrado com Nautilus Trader
"""

import MetaTrader5 as mt5
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import json
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
        logging.FileHandler('ea2060_llm_trader.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """Analisador LLM para decisões de trading"""

    def __init__(self):
        self.analysis_history = []
        self.signal_confidence_threshold = 0.65

    def analyze_market_data(self, current_data: pd.Series, historical_data: pd.DataFrame) -> Dict:
        """
        Analisa dados do mercado com LLM (simulado)
        Em produção, isso conectaria a uma API LLM real (GPT-4, Claude, etc.)
        """
        try:
            # Extrair características
            features = self._extract_features(current_data, historical_data)

            # Criar prompt para LLM
            prompt = self._create_analysis_prompt(features)

            # Simular resposta LLM (substituir por API real)
            llm_response = self._simulate_llm_response(prompt, features)

            # Registrar análise
            self.analysis_history.append({
                'timestamp': datetime.now(),
                'features': features,
                'llm_response': llm_response
            })

            return llm_response

        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return self._fallback_analysis(current_data)

    def _extract_features(self, current: pd.Series, df: pd.DataFrame) -> Dict:
        """Extrair características para análise"""
        return {
            # Preços e médias
            'current_price': float(current['close']),
            'ema_fast': float(current['ema_fast']),
            'ema_slow': float(current['ema_slow']),
            'supertrend': float(current['supertrend']),
            'bb_upper': float(current['bb_upper']),
            'bb_middle': float(current['bb_middle']),
            'bb_lower': float(current['bb_lower']),

            # Indicadores técnicos
            'rsi': float(current['rsi']),
            'atr': float(current['atr']),
            'volume_ratio': float(current['volume_ratio']),
            'volatility': float(current['volatility']),

            # Análise de posição
            'price_position': self._get_price_position(current),
            'distance_to_supertrend': (float(current['close']) - float(current['supertrend'])) / float(current['supertrend']),
            'distance_to_bb_upper': (float(current['bb_upper']) - float(current['close'])) / float(current['bb_upper']),
            'distance_to_bb_lower': (float(current['close']) - float(current['bb_lower'])) / float(current['bb_lower']),

            # Análise de tendência
            'trend_direction': self._calculate_trend_direction(df),
            'trend_strength': self._calculate_trend_strength(df),
            'momentum': self._calculate_momentum(df),

            # Análise de suporte/resistência
            'support_resistance': self._find_key_levels(df),

            # Análise de volume
            'volume_trend': self._analyze_volume_trend(df),
            'volume_strength': float(current['volume_ratio']),

            # Análise temporal
            'hour_of_day': current.name.hour if hasattr(current.name, 'hour') else 0,
            'day_of_week': current.name.dayofweek if hasattr(current.name, 'dayofweek') else 0,
        }

    def _get_price_position(self, data: pd.Series) -> str:
        """Determinar posição do preço"""
        price = float(data['close'])
        ema_fast = float(data['ema_fast'])
        ema_slow = float(data['ema_slow'])
        supertrend = float(data['supertrend'])

        if price > ema_fast > ema_slow and price > supertrend:
            return 'strong_bullish'
        elif price > ema_fast > ema_slow and price < supertrend:
            return 'bullish_correction'
        elif price < ema_fast < ema_slow and price < supertrend:
            return 'strong_bearish'
        elif price < ema_fast < ema_slow and price > supertrend:
            return 'bearish_correction'
        else:
            return 'neutral'

    def _calculate_trend_direction(self, df: pd.DataFrame) -> str:
        """Calcular direção da tendência"""
        if len(df) < 20:
            return 'unknown'

        ema_fast_current = df['ema_fast'].iloc[-1]
        ema_fast_prev = df['ema_fast'].iloc[-5]
        ema_slow_current = df['ema_slow'].iloc[-1]

        if ema_fast_current > ema_fast_prev > ema_slow_current:
            return 'strong_uptrend'
        elif ema_fast_current > ema_fast_prev and ema_fast_current > ema_slow_current:
            return 'uptrend'
        elif ema_fast_current < ema_fast_prev < ema_slow_current:
            return 'strong_downtrend'
        elif ema_fast_current < ema_fast_prev and ema_fast_current < ema_slow_current:
            return 'downtrend'
        else:
            return 'sideways'

    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calcular força da tendência (0-1)"""
        if len(df) < 20:
            return 0.5

        # Usar RSI e volatilidade para medir força
        rsi_values = df['rsi'].tail(20).values
        avg_rsi = np.mean(rsi_values)

        # Força baseada no RSI
        if avg_rsi > 60 or avg_rsi < 40:
            strength = min(1.0, abs(avg_rsi - 50) / 20)
        else:
            strength = 0.3

        # Ajustar com volatilidade
        volatility = df['volatility'].iloc[-1]
        strength = strength * (1 + min(0.5, volatility * 100))

        return min(1.0, strength)

    def _calculate_momentum(self, df: pd.DataFrame) -> Dict:
        """Calcular momentum"""
        if len(df) < 10:
            return {'short': 0, 'medium': 0, 'long': 0}

        # Momentum em diferentes períodos
        mom_short = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
        mom_medium = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
        mom_long = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]

        return {
            'short': float(mom_short),
            'medium': float(mom_medium),
            'long': float(mom_long)
        }

    def _find_key_levels(self, df: pd.DataFrame) -> Dict:
        """Encontrar níveis de suporte e resistência"""
        if len(df) < 50:
            return {'support': 0, 'resistance': 0, 'strength': 0}

        # Usar máximos e mínimos recentes
        highs = df['high'].rolling(window=10).max()
        lows = df['low'].rolling(window=10).min()

        recent_highs = highs.tail(30).max()
        recent_lows = lows.tail(30).min()

        current_price = df['close'].iloc[-1]

        # Calcular força dos níveis
        distance_to_high = abs(current_price - recent_highs) / current_price
        distance_to_low = abs(current_price - recent_lows) / current_price

        strength = max(distance_to_high, distance_to_low) * 100

        return {
            'support': float(recent_lows),
            'resistance': float(recent_highs),
            'strength': float(strength),
            'distance_to_support': float((current_price - recent_lows) / current_price),
            'distance_to_resistance': float((recent_highs - current_price) / current_price)
        }

    def _analyze_volume_trend(self, df: pd.DataFrame) -> str:
        """Analisar tendência de volume"""
        if len(df) < 20:
            return 'insufficient_data'

        volume_avg = df['volume_ratio'].tail(20).mean()
        recent_volume = df['volume_ratio'].tail(5).mean()

        if recent_volume > volume_avg * 1.2:
            return 'increasing'
        elif recent_volume < volume_avg * 0.8:
            return 'decreasing'
        else:
            return 'stable'

    def _create_analysis_prompt(self, features: Dict) -> str:
        """Criar prompt para análise LLM"""
        prompt = f"""
        EA2060 Advanced Trading Analysis - AI Decision Required

        CURRENT MARKET CONDITIONS:
        - Price: ${features['current_price']:.2f}
        - EMA Fast/Slow: ${features['ema_fast']:.2f} / ${features['ema_slow']:.2f}
        - SuperTrend: ${features['supertrend']:.2f}
        - RSI: {features['rsi']:.1f}
        - ATR: {features['atr']:.2f}
        - Volume Ratio: {features['volume_ratio']:.2f}
        - Volatility: {features['volatility']:.4f}
        - Price Position: {features['price_position']}

        TECHNICAL ANALYSIS:
        - Trend Direction: {features['trend_direction']}
        - Trend Strength: {features['trend_strength']:.2f}
        - Momentum: {features['momentum']}
        - Volume Trend: {features['volume_trend']}

        KEY LEVELS:
        - Support: ${features['support_resistance']['support']:.2f}
        - Resistance: ${features['support_resistance']['resistance']:.2f}
        - Distance to Support: {features['support_resistance']['distance_to_support']:.2%}
        - Distance to Resistance: {features['support_resistance']['distance_to_resistance']:.2%}

        TRADING RULES:
        1. EMA Crossover confirmation required
        2. SuperTrend alignment with trend
        3. RSI optimal zone: 35-65
        4. Volume confirmation > 1.0
        5. Risk/Reward minimum 1:1.2
        6. Maximum drawdown per trade: 2%

        DECISION FACTORS:
        - Signal strength and confidence
        - Risk/Reward ratio
        - Market volatility
        - Volume confirmation
        - Time of day effects
        - Support/Resistance proximity

        Provide trading decision with:
        1. ACTION: BUY/SELL/HOLD
        2. CONFIDENCE: 0.0-1.0
        3. REASONING: Brief explanation
        4. RISK_LEVEL: LOW/MEDIUM/HIGH
        5. REWARD_ESTIMATE: Potential profit/loss ratio

        Format: ACTION|CONFIDENCE|REASONING|RISK_LEVEL|REWARD_ESTIMATE
        """

        return prompt

    def _simulate_llm_response(self, prompt: str, features: Dict) -> Dict:
        """
        Simular resposta LLM (em produção, substituir por API real)
        Implementa lógica sofisticada de decisão
        """
        try:
            # Calcular score baseado em múltiplos fatores
            score = 0.0
            reasoning_parts = []

            # 1. Análise de EMA (peso: 25%)
            ema_score = self._analyze_ema_signals(features)
            score += ema_score * 0.25
            if ema_score > 0.5:
                reasoning_parts.append("Strong EMA bullish signals")
            elif ema_score < -0.5:
                reasoning_parts.append("Strong EMA bearish signals")

            # 2. Análise de SuperTrend (peso: 20%)
            st_score = self._analyze_supertrend_signals(features)
            score += st_score * 0.20
            if st_score > 0.5:
                reasoning_parts.append("Price above SuperTrend support")
            elif st_score < -0.5:
                reasoning_parts.append("Price below SuperTrend resistance")

            # 3. Análise de Momentum (peso: 15%)
            momentum_score = self._analyze_momentum_signals(features)
            score += momentum_score * 0.15
            if momentum_score > 0.3:
                reasoning_parts.append("Positive momentum across timeframes")
            elif momentum_score < -0.3:
                reasoning_parts.append("Negative momentum across timeframes")

            # 4. Análise de Volume (peso: 10%)
            volume_score = self._analyze_volume_signals(features)
            score += volume_score * 0.10
            if volume_score > 0.5:
                reasoning_parts.append("High volume confirmation")
            elif volume_score < 0:
                reasoning_parts.append("Low volume warning")

            # 5. Análise de Suporte/Resistência (peso: 15%)
            sr_score = self._analyze_support_resistance_signals(features)
            score += sr_score * 0.15
            if sr_score > 0.3:
                reasoning_parts.append("Near support level")
            elif sr_score < -0.3:
                reasoning_parts.append("Near resistance level")

            # 6. Análise de Volatilidade (peso: 10%)
            volatility_score = self._analyze_volatility_signals(features)
            score += volatility_score * 0.10
            if abs(volatility_score) < 0.3:
                reasoning_parts.append("Optimal volatility conditions")
            else:
                reasoning_parts.append("High volatility - increased risk")

            # 7. Análise Temporal (peso: 5%)
            temporal_score = self._analyze_temporal_signals(features)
            score += temporal_score * 0.05

            # Normalizar score para -1 a 1
            score = max(-1.0, min(1.0, score))

            # Determinar ação
            confidence = abs(score)
            if score > 0.3:
                action = "BUY"
            elif score < -0.3:
                action = "SELL"
            else:
                action = "HOLD"

            # Determinar nível de risco
            risk_level = self._assess_risk_level(features, score)

            # Estimar recompensa
            reward_estimate = self._estimate_reward(features, score)

            # Montar reasoning completo
            if not reasoning_parts:
                reasoning = "Mixed signals - waiting for clearer direction"
            else:
                reasoning = ", ".join(reasoning_parts[:4])  # Limitar a 4 razões principais

            return {
                'action': action,
                'confidence': confidence,
                'score': score,
                'reasoning': reasoning,
                'risk_level': risk_level,
                'reward_estimate': reward_estimate,
                'signal_strength': self._calculate_signal_strength(features, score)
            }

        except Exception as e:
            logger.error(f"Error in LLM response simulation: {e}")
            return self._fallback_analysis(None)

    def _analyze_ema_signals(self, features: Dict) -> float:
        """Analisar sinais de EMA"""
        score = 0.0

        # Crossover
        if features['ema_fast'] > features['ema_slow']:
            score += 0.5

        # Posição do preço
        if features['current_price'] > features['ema_fast']:
            score += 0.3
        if features['current_price'] > features['ema_slow']:
            score += 0.2

        # Força do crossover
        ema_spread = (features['ema_fast'] - features['ema_slow']) / features['ema_slow']
        score += min(0.5, max(-0.5, ema_spread * 10))

        return max(-1.0, min(1.0, score))

    def _analyze_supertrend_signals(self, features: Dict) -> float:
        """Analisar sinais do SuperTrend"""
        if features['current_price'] > features['supertrend']:
            return 0.8
        else:
            return -0.8

    def _analyze_momentum_signals(self, features: Dict) -> float:
        """Analisar sinais de momentum"""
        momentum = features['momentum']
        score = 0.0

        # Ponderar diferentes períodos
        score += momentum['short'] * 0.5
        score += momentum['medium'] * 0.3
        score += momentum['long'] * 0.2

        return max(-1.0, min(1.0, score))

    def _analyze_volume_signals(self, features: Dict) -> float:
        """Analisar sinais de volume"""
        if features['volume_ratio'] > 1.5:
            return 0.8
        elif features['volume_ratio'] > 1.0:
            return 0.4
        elif features['volume_ratio'] > 0.8:
            return 0.0
        else:
            return -0.3

    def _analyze_support_resistance_signals(self, features: Dict) -> float:
        """Analisar sinais de suporte/resistência"""
        sr = features['support_resistance']

        # Perto do suporte (sinal de compra)
        if sr['distance_to_support'] < 0.01:
            return 0.6
        # Perto da resistência (sinal de venda)
        elif sr['distance_to_resistance'] < 0.01:
            return -0.6
        else:
            return 0.0

    def _analyze_volatility_signals(self, features: Dict) -> float:
        """Analisar sinais de volatilidade"""
        vol = features['volatility']

        if vol > 0.004:  # Muito alta volatilidade
            return -0.5
        elif vol < 0.001:  # Muito baixa volatilidade
            return -0.3
        else:  # Volatilidade ideal
            return 0.2

    def _analyze_temporal_signals(self, features: Dict) -> float:
        """Analisar sinais temporais"""
        hour = features['hour_of_day']
        day = features['day_of_week']

        # Evitar trading em horários de baixa liquidez
        if hour < 6 or hour > 20:
            return -0.3

        # Evitar sexta-feira tarde
        if day == 4 and hour > 16:
            return -0.2

        return 0.1

    def _assess_risk_level(self, features: Dict, score: float) -> str:
        """Avaliar nível de risco"""
        risk_factors = []

        # Volatilidade
        if features['volatility'] > 0.003:
            risk_factors.append('high_volatility')

        # Score extremo
        if abs(score) > 0.8:
            risk_factors.append('extreme_signal')

        # Volume baixo
        if features['volume_ratio'] < 0.8:
            risk_factors.append('low_volume')

        # Proximidade de níveis
        sr = features['support_resistance']
        if sr['distance_to_support'] < 0.005 or sr['distance_to_resistance'] < 0.005:
            risk_factors.append('near_key_levels')

        if len(risk_factors) >= 2:
            return 'HIGH'
        elif len(risk_factors) == 1:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _estimate_reward(self, features: Dict, score: float) -> str:
        """Estimar recompensa potencial"""
        strength = features['trend_strength']
        momentum = features['momentum']

        # Calcular RR ratio estimado
        base_rr = 1.2

        if strength > 0.7:
            base_rr *= 1.3
        elif strength < 0.3:
            base_rr *= 0.8

        if abs(momentum['medium']) > 0.02:
            base_rr *= 1.2

        if features['volume_ratio'] > 1.5:
            base_rr *= 1.1

        return f"1:{base_rr:.1f}"

    def _calculate_signal_strength(self, features: Dict, score: float) -> str:
        """Calcular força do sinal"""
        strength = abs(score)

        if strength > 0.8:
            return 'VERY_STRONG'
        elif strength > 0.6:
            return 'STRONG'
        elif strength > 0.4:
            return 'MODERATE'
        elif strength > 0.2:
            return 'WEAK'
        else:
            return 'VERY_WEAK'

    def _fallback_analysis(self, data: Optional[pd.Series]) -> Dict:
        """Análise de fallback em caso de erro"""
        return {
            'action': 'HOLD',
            'confidence': 0.0,
            'score': 0.0,
            'reasoning': 'Analysis error - using fallback',
            'risk_level': 'HIGH',
            'reward_estimate': '1:1.0',
            'signal_strength': 'VERY_WEAK'
        }

class LLMEnhancedIndicators:
    """Indicadores otimizados com integração LLM"""

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
        """SuperTrend adaptativo"""
        atr_values = self.atr(df, atr_period)
        hl2 = (df['high'] + df['low']) / 2

        # Ajustar multiplicador baseado na volatilidade
        atr_sma = atr_values.rolling(window=20).mean()
        volatility_ratio = atr_values / atr_sma
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
        """Bandas de Bollinger"""
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()

        return pd.DataFrame({
            'bb_upper': sma + (std * std_dev),
            'bb_middle': sma,
            'bb_lower': sma - (std * std_dev)
        })

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular todos os indicadores"""
        result = df.copy()

        # EMAs otimizadas
        result['ema_fast'] = self.ema(result['close'], 6)
        result['ema_slow'] = self.ema(result['close'], 18)

        # Indicadores de volatilidade
        result['atr'] = self.atr(result, 14)
        result['supertrend'] = self.adaptive_supertrend(result)

        # Momentum
        result['rsi'] = self.rsi(result, 14)

        # Bandas de Bollinger
        bb = self.bollinger_bands(result)
        result = pd.concat([result, bb], axis=1)

        # Volume
        volume_col = 'volume' if 'volume' in result.columns else 'tick_volume'
        result['volume_ma'] = result[volume_col].rolling(window=20).mean()
        result['volume_ratio'] = result[volume_col] / result['volume_ma']

        # Volatilidade
        result['price_change'] = result['close'].pct_change()
        result['volatility'] = result['price_change'].rolling(window=14).std()

        return result

class EA2060LLMTrader:
    """
    EA2060 com integração LLM para tomada de decisão avançada
    """

    def __init__(self):
        self.is_running = False
        self.indicators = LLMEnhancedIndicators()
        self.llm_analyzer = LLMAnalyzer()
        self.open_positions = []
        self.magic_numbers = list(range(11111, 11136))
        self.current_magic_index = 0

        # Parâmetros de trading
        self.symbol = "XAUUSD"
        self.timeframe = mt5.TIMEFRAME_H1
        self.base_lot_size = 0.01
        self.max_positions = 3
        self.risk_per_trade = 0.01

        # Filtros LLM
        self.min_llm_confidence = 0.65
        self.max_risk_level = 'MEDIUM'

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

    def analyze_with_llm(self, df: pd.DataFrame) -> Optional[Dict]:
        """Analisar mercado com LLM"""
        try:
            if len(df) < 50:
                return None

            # Calcular indicadores
            df_with_indicators = self.indicators.calculate_all(df)
            df_clean = df_with_indicators.dropna()

            if len(df_clean) < 20:
                return None

            current_data = df_clean.iloc[-1]

            # Análise LLM
            llm_analysis = self.llm_analyzer.analyze_market_data(current_data, df_clean)

            logger.info("LLM Analysis Results:")
            logger.info(f"  Action: {llm_analysis['action']}")
            logger.info(f"  Confidence: {llm_analysis['confidence']:.2f}")
            logger.info(f"  Signal Strength: {llm_analysis['signal_strength']}")
            logger.info(f"  Risk Level: {llm_analysis['risk_level']}")
            logger.info(f"  Reward Estimate: {llm_analysis['reward_estimate']}")
            logger.info(f"  Reasoning: {llm_analysis['reasoning']}")

            return llm_analysis

        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return None

    def calculate_dynamic_sl_tp(self, current_price: float, atr_value: float, llm_analysis: Dict) -> Tuple[float, float]:
        """Calcular SL e TP dinâmicos baseados na análise LLM"""
        try:
            # Ajustar baseado no risco
            risk_multiplier = 1.0
            if llm_analysis['risk_level'] == 'HIGH':
                risk_multiplier = 1.5
            elif llm_analysis['risk_level'] == 'LOW':
                risk_multiplier = 0.8

            # SL baseado em ATR
            sl_pips = int(atr_value * 100 * 2.0 * risk_multiplier)

            # TP baseado no reward estimate do LLM
            reward_ratio = float(llm_analysis['reward_estimate'].replace('1:', ''))
            tp_pips = int(sl_pips * reward_ratio)

            return sl_pips, tp_pips

        except Exception as e:
            logger.error(f"Error calculating SL/TP: {e}")
            return 250, 300  # Fallback

    def place_llm_order(self, llm_analysis: Dict, current_data: pd.Series) -> bool:
        """Place order based on LLM analysis"""
        try:
            # Verificar se atende aos critérios mínimos
            if llm_analysis['confidence'] < self.min_llm_confidence:
                logger.info(f"LLM confidence too low: {llm_analysis['confidence']:.2f} < {self.min_llm_confidence}")
                return False

            if llm_analysis['risk_level'] == 'HIGH' and self.max_risk_level == 'LOW':
                logger.info(f"Risk level too high: {llm_analysis['risk_level']}")
                return False

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

            # Calcular SL/TP dinâmicos
            atr_value = current_data['atr']
            sl_pips, tp_pips = self.calculate_dynamic_sl_tp(current_data['close'], atr_value, llm_analysis)

            # Preparar ordem
            if llm_analysis['action'] == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                sl = price - (sl_pips * 0.01)
                tp = price + (tp_pips * 0.01)
            else:  # SELL
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                sl = price + (sl_pips * 0.01)
                tp = price - (tp_pips * 0.01)

            # Arredondar para tick size
            tick_size = symbol_info.trade_tick_size
            price = round(price / tick_size) * tick_size
            sl = round(sl / tick_size) * tick_size
            tp = round(tp / tick_size) * tick_size

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": self.base_lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": magic,
                "comment": f"EA2060_LLM_{llm_analysis['action']}_{magic}",
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

            logger.info("="*80)
            logger.info("LLM-ENHANCED ORDER PLACED SUCCESSFULLY!")
            logger.info(f"Action: {llm_analysis['action']}")
            logger.info(f"Symbol: {self.symbol}")
            logger.info(f"Volume: {self.base_lot_size} lots")
            logger.info(f"Entry Price: {price:.5f}")
            logger.info(f"Stop Loss: {sl:.5f} ({sl_pips} pips)")
            logger.info(f"Take Profit: {tp:.5f} ({tp_pips} pips)")
            logger.info(f"Magic Number: {magic}")
            logger.info(f"LLM Confidence: {llm_analysis['confidence']:.2f}")
            logger.info(f"Signal Strength: {llm_analysis['signal_strength']}")
            logger.info(f"Risk Level: {llm_analysis['risk_level']}")
            logger.info(f"Reward Estimate: {llm_analysis['reward_estimate']}")
            logger.info(f"LLM Reasoning: {llm_analysis['reasoning']}")
            logger.info(f"Order Ticket: {result.order}")
            logger.info("="*80)

            return True

        except Exception as e:
            logger.error(f"Error placing LLM order: {e}")
            return False

    def get_open_positions(self) -> List:
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
        """Main trading loop with LLM integration"""
        logger.info("="*100)
        logger.info("EA2060 LLM-ENHANCED PYTHON TRADER")
        logger.info("="*100)
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Timeframe: H1")
        logger.info(f"Base Lot Size: {self.base_lot_size}")
        logger.info(f"Max Positions: {self.max_positions}")
        logger.info(f"Min LLM Confidence: {self.min_llm_confidence}")
        logger.info(f"Max Risk Level: {self.max_risk_level}")
        logger.info(f"Magic Numbers: {self.magic_numbers[0]}-{self.magic_numbers[-1]}")
        logger.info("="*100)

        self.is_running = True
        cycle_count = 0

        try:
            while self.is_running:
                cycle_count += 1
                logger.info(f"--- LLM Trading Cycle #{cycle_count} ---")

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

                # LLM Analysis
                llm_analysis = self.analyze_with_llm(df)

                if llm_analysis and llm_analysis['action'] in ['BUY', 'SELL']:
                    # Check confidence and risk criteria
                    if (llm_analysis['confidence'] >= self.min_llm_confidence and
                        (self.max_risk_level == 'HIGH' or llm_analysis['risk_level'] != 'HIGH' or self.max_risk_level != 'MEDIUM')):

                        # Obter dados atuais para ordem
                        df_with_indicators = self.indicators.calculate_all(df)
                        df_clean = df_with_indicators.dropna()

                        if len(df_clean) > 0:
                            current_data = df_clean.iloc[-1]

                            # Executar ordem baseada na análise LLM
                            success = self.place_llm_order(llm_analysis, current_data)

                            if success:
                                logger.info("LLM-enhanced trade executed successfully, waiting 15 minutes...")
                                time.sleep(900)  # 15 minutes
                            else:
                                logger.error("Failed to execute LLM trade, waiting 1 minute...")
                                time.sleep(60)
                        else:
                            logger.error("No clean data available for order execution")
                            time.sleep(60)
                    else:
                        logger.info(f"LLM signal filtered out - Confidence: {llm_analysis['confidence']:.2f}, Risk: {llm_analysis['risk_level']}")
                        time.sleep(60)
                else:
                    logger.info("No LLM trading signals detected")
                    time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Trading stopped by user")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
        finally:
            self.is_running = False
            logger.info("EA2060 LLM trading session ended")

    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping EA2060 LLM trading bot...")
        self.is_running = False

def main():
    """Main function"""
    logger.info("Starting EA2060 LLM-Enhanced Python Trader...")

    trader = EA2060LLMTrader()

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