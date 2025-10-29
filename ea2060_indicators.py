#!/usr/bin/env python3
"""
EA2060 Indicators Module
Implementação Python dos indicadores usados pelo EA2060 819830
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class EA2060Indicators:
    """
    Classe com todos os indicadores do EA2060 implementados em Python
    """

    def __init__(self):
        pass

    def smma(self, data: pd.Series, period: int) -> pd.Series:
        """Smoothed Moving Average"""
        return data.ewm(span=period, adjust=False).mean()

    def alligator(self, df: pd.DataFrame,
                   jaw_period: int = 13, jaw_shift: int = 8,
                   teeth_period: int = 8, teeth_shift: int = 5,
                   lips_period: int = 5, lips_shift: int = 3) -> pd.DataFrame:
        """
        Bill Williams Alligator Indicator

        Returns:
            DataFrame com colunas: jaw, teeth, lips
        """
        median_price = (df['high'] + df['low']) / 2

        alligator = pd.DataFrame()
        alligator['jaw'] = self.smma(median_price, jaw_period).shift(jaw_shift)
        alligator['teeth'] = self.smma(median_price, teeth_period).shift(teeth_shift)
        alligator['lips'] = self.smma(median_price, lips_period).shift(lips_shift)

        return alligator

    def atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Average True Range

        Returns:
            Series com valores ATR
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        return true_range.rolling(window=period).mean()

    def supertrend(self, df: pd.DataFrame,
                    atr_period: int = 24,
                    multiplier: float = 3.0) -> pd.DataFrame:
        """
        SuperTrend Indicator

        Returns:
            DataFrame com colunas: supertrend, trend_up, trend_down
        """
        atr_values = self.atr(df, atr_period)
        hl2 = (df['high'] + df['low']) / 2

        upper_band = hl2 + (multiplier * atr_values)
        lower_band = hl2 - (multiplier * atr_values)

        supertrend = pd.Series(index=df.index, dtype=float)
        trend_up = pd.Series(index=df.index, dtype=float)
        trend_down = pd.Series(index=df.index, dtype=float)

        # Initialize first value
        supertrend.iloc[0] = upper_band.iloc[0]
        trend_up.iloc[0] = supertrend.iloc[0]

        for i in range(1, len(df)):
            prev_close = df['close'].iloc[i-1]
            prev_supertrend = supertrend.iloc[i-1]
            current_close = df['close'].iloc[i]

            # Check if we need to switch trend
            if current_close <= upper_band.iloc[i] and prev_close > prev_supertrend:
                supertrend.iloc[i] = upper_band.iloc[i]
            elif current_close >= lower_band.iloc[i] and prev_close < prev_supertrend:
                supertrend.iloc[i] = lower_band.iloc[i]
            elif i > 0 and supertrend.iloc[i-1] == upper_band.iloc[i-1]:
                # Continue with upper band, but check if we should use previous value
                supertrend.iloc[i] = min(upper_band.iloc[i], prev_supertrend)
            else:
                # Continue with lower band, but check if we should use previous value
                supertrend.iloc[i] = max(lower_band.iloc[i], prev_supertrend)

            # Set trend buffers
            if current_close > supertrend.iloc[i]:
                trend_up.iloc[i] = supertrend.iloc[i]
                trend_down.iloc[i] = np.nan
            else:
                trend_down.iloc[i] = supertrend.iloc[i]
                trend_up.iloc[i] = np.nan

        result = pd.DataFrame({
            'supertrend': supertrend,
            'trend_up': trend_up,
            'trend_down': trend_down
        })

        return result

    def adx(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Average Directional Movement Index

        Returns:
            DataFrame com colunas: adx, +di, -di
        """
        high = df['high']
        low = df['low']
        close = df['close']

        # Calculate True Range
        tr1 = high - low
        tr2 = np.abs(high - close.shift(1))
        tr3 = np.abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        # Convert to Series and align with original index
        tr = pd.Series(tr, index=close.index)
        plus_dm = pd.Series(plus_dm, index=close.index)
        minus_dm = pd.Series(minus_dm, index=close.index)

        # Calculate Wilder's smoothing
        atr_smooth = tr.ewm(alpha=1/period, adjust=False).mean()
        plus_di_smooth = plus_dm.ewm(alpha=1/period, adjust=False).mean()
        minus_di_smooth = minus_dm.ewm(alpha=1/period, adjust=False).mean()

        # Calculate DI
        plus_di = 100 * (plus_di_smooth / atr_smooth)
        minus_di = 100 * (minus_di_smooth / atr_smooth)

        # Calculate ADX
        dx = np.abs(plus_di - minus_di)
        sum_di = plus_di + minus_di

        adx = dx.ewm(alpha=1/period, adjust=False).mean() * (sum_di / (sum_di + 1e-10))

        return pd.DataFrame({
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        })

    def heiken_ashi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Heiken Ashi Candles

        Returns:
            DataFrame com colunas: ha_open, ha_high, ha_low, ha_close
        """
        ha_close = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        ha_open = pd.Series(index=df.index, dtype=float)
        ha_open.iloc[0] = (df['open'].iloc[0] + df['close'].iloc[0]) / 2

        for i in range(1, len(df)):
            ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2

        ha_high = pd.concat([df['high'], ha_open, ha_close], axis=1).max(axis=1)
        ha_low = pd.concat([df['low'], ha_open, ha_close], axis=1).min(axis=1)

        return pd.DataFrame({
            'ha_open': ha_open,
            'ha_high': ha_high,
            'ha_low': ha_low,
            'ha_close': ha_close
        })

    def volume_analysis(self, df: pd.DataFrame,
                         period_short: int = 30,
                         period_long: int = 14) -> pd.DataFrame:
        """
        Volume Analysis with multiple periods

        Returns:
            DataFrame com médias de volume e tendências
        """
        # Handle both 'volume' and 'tick_volume' column names
        volume_col = 'volume' if 'volume' in df.columns else 'tick_volume'
        volume_data = df[volume_col]

        volume_ma_short = volume_data.rolling(window=period_short).mean()
        volume_ma_long = volume_data.rolling(window=period_long).mean()

        # Volume falling detection
        volume_trend = np.where(volume_ma_short < volume_ma_short.shift(5), -1,
                              np.where(volume_ma_short > volume_ma_short.shift(5), 1, 0))

        return pd.DataFrame({
            'volume': volume_data,
            'volume_ma_short': volume_ma_short,
            'volume_ma_long': volume_ma_long,
            'volume_trend': volume_trend,
            'volume_ratio': volume_ma_short / volume_ma_long
        })

    def stochastic(self, df: pd.DataFrame,
                     k_period: int = 14,
                     d_period: int = 3,
                     slowing: int = 3) -> pd.DataFrame:
        """
        Stochastic Oscillator

        Returns:
            DataFrame com colunas: %k, %d
        """
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()

        # Calculate %K with slowing
        k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low + 1e-10))
        k_smooth = k_percent.rolling(window=slowing).mean()

        # Calculate %D
        d_percent = k_smooth.rolling(window=d_period).mean()

        return pd.DataFrame({
            'k_percent': k_smooth,
            'd_percent': d_percent
        })

    def rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Relative Strength Index

        Returns:
            Series com valores RSI
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators used by EA2060

        Returns:
            DataFrame com todos os indicadores calculados
        """
        result_df = df.copy()

        # Add Alligator
        alligator = self.alligator(df)
        result_df = pd.concat([result_df, alligator], axis=1)

        # Add ATR
        result_df['atr'] = self.atr(df)

        # Add SuperTrend
        supertrend = self.supertrend(df)
        result_df = pd.concat([result_df, supertrend], axis=1)

        # Add ADX
        adx = self.adx(df)
        result_df = pd.concat([result_df, adx], axis=1)

        # Add Heiken Ashi
        heiken = self.heiken_ashi(df)
        result_df = pd.concat([result_df, heiken], axis=1)

        # Add Volume Analysis
        volume = self.volume_analysis(df)
        result_df = pd.concat([result_df, volume], axis=1)

        # Add Stochastic
        stoch = self.stochastic(df)
        result_df = pd.concat([result_df, stoch], axis=1)

        # Add RSI
        result_df['rsi'] = self.rsi(df)

        return result_df

# Teste dos indicadores
if __name__ == "__main__":
    # Criar dados de exemplo
    dates = pd.date_range('2024-01-01', periods=100, freq='H')
    np.random.seed(42)

    # Simular dados de XAUUSD
    base_price = 2000
    price_data = []
    current_price = base_price

    for i in range(100):
        change = np.random.normal(0, 5)  # Mudança de preço com volatilidade típica de ouro
        current_price *= (1 + change / 10000)  # Converter para mudança percentual
        price_data.append(current_price)

    df = pd.DataFrame({
        'time': dates,
        'open': price_data,
        'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in price_data],
        'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in price_data],
        'close': price_data,
        'volume': np.random.randint(1000, 10000, 100)
    })
    df.set_index('time', inplace=True)

    # Testar indicadores
    indicators = EA2060Indicators()
    result = indicators.calculate_all_indicators(df)

    print("EA2060 Indicators Module - Teste Concluido")
    print(f"Shape dos dados: {result.shape}")
    print(f"Colunas: {list(result.columns)}")
    print(f"Ultimas 5 linhas:")
    print(result.tail())