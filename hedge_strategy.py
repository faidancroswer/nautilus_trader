#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estratégia de Hedge - EUR/USD e US30
=====================================

Baseada na estratégia do Sr. Johnny (YouTube):
- Swing trade sem stop-loss
- Análise de equilíbrio/desequilíbrio
- Hedge gradual (até 7 posições por direção conforme saldo cresce)
- Espaçamento adaptativo entre ordens (700-1500 pips)
- Proteção em eventos de notícias
- ESTRATÉGIA DE CRESCIMENTO: Manter lotes fixos mesmo com saldo aumentando

ATUALIZAÇÃO VÍDEO #20 (Janeiro/2026):
=======================================
Uma lição CRUCIAL do Sr. Johnny:

"Por que eu não aumento os lotes mesmo a conta estando aí cinco vezes maior?
Porque dessa forma eu consigo abrir mais operações. Ao invés de abrir quatro,
cinco operações, posso abrir seis, sete, fracionando o tamanho do lote."

RESULTADO COMPROVADO:
- Conta menor ($40k): 60% de rebaixamento
- Conta maior ($200k+): MÁXIMO 15% de rebaixamento

A estratégia MANTÉM o mesmo tamanho de lote e aumenta o número de posições
conforme o saldo cresce, reduzindo DRASTICAMENTE o risco.

Capital base: $1000 USD
Lote fixo: 0.025 (proporcional aos $1000) - MANTER MESMO COM SALDO MAIOR
"""

import sys
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
import logging
import os

# Fix encoding for Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hedge_strategy.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('HedgeStrategy')


class NewsProtection:
    """Proteção contra eventos de notícias de alto impacto"""
    
    # Eventos de alto impacto (horários UTC)
    HIGH_IMPACT_EVENTS = {
        'NFP': {'day': 'Friday', 'week': 1, 'hour': 13, 'minute': 30},  # First Friday
        'FOMC': {'hour': 19, 'minute': 0},  # 2PM ET
        'ECB': {'hour': 12, 'minute': 45},
        'CPI_US': {'hour': 13, 'minute': 30},
        'CPI_EU': {'hour': 10, 'minute': 0},
    }
    
    @staticmethod
    def is_news_time(buffer_minutes: int = 30) -> Tuple[bool, str]:
        """
        Verifica se estamos próximos de um evento de notícias
        
        Args:
            buffer_minutes: Minutos antes/depois do evento para considerar
            
        Returns:
            (is_news, event_name)
        """
        now = datetime.utcnow()
        current_hour = now.hour
        current_minute = now.minute
        
        # Simplificado: evitar horários conhecidos de alto impacto
        # NFP: Primeira sexta do mês, 8:30 ET (13:30 UTC)
        if now.weekday() == 4 and now.day <= 7:  # Primeiro Friday
            if 13 <= current_hour <= 14:
                return True, "NFP"
        
        # FOMC: Quarta-feira, geralmente 2:00 PM ET (19:00 UTC)
        if now.weekday() == 2:  # Wednesday
            if 18 <= current_hour <= 20:
                return True, "FOMC"
        
        # CPI US: Geralmente 8:30 AM ET (13:30 UTC)
        if current_hour == 13 and 0 <= current_minute <= 59:
            return True, "CPI_US"
        
        # ECB: Geralmente 7:45 AM ET (12:45 UTC)
        if current_hour == 12 and 30 <= current_minute <= 59:
            return True, "ECB"
        
        return False, ""


class EquilibriumAnalyzer:
    """
    Análise de Equilíbrio/Desequilíbrio do Mercado
    Baseado em linha de equilíbrio mensal e MA semanal
    """
    
    def __init__(self, symbol: str, lookback_years: int = 5):
        self.symbol = symbol
        self.lookback_years = lookback_years
        self.monthly_equilibrium = None
        self.last_top = None
        self.last_bottom = None
        
    def calculate_monthly_equilibrium(self) -> Optional[float]:
        """
        Calcula a linha de equilíbrio mensal
        (Topo + Fundo) / 2 dos últimos 4-5 anos
        """
        try:
            # Buscar dados mensais
            bars = self.lookback_years * 12 + 12  # Anos + margem
            rates = mt5.copy_rates_from_pos(
                self.symbol,
                mt5.TIMEFRAME_MN1,
                0,
                bars
            )
            
            if rates is None or len(rates) < 12:
                logger.warning(f"Dados mensais insuficientes para {self.symbol}")
                return None
            
            df = pd.DataFrame(rates)
            
            # Identificar topo e fundo
            self.last_top = df['high'].max()
            self.last_bottom = df['low'].min()
            
            # Linha de equilíbrio
            self.monthly_equilibrium = (self.last_top + self.last_bottom) / 2
            
            logger.info(f"[{self.symbol}] Equilíbrio Mensal Calculado:")
            logger.info(f"  Topo: {self.last_top:.5f}")
            logger.info(f"  Fundo: {self.last_bottom:.5f}")
            logger.info(f"  Equilíbrio: {self.monthly_equilibrium:.5f}")
            
            return self.monthly_equilibrium
            
        except Exception as e:
            logger.error(f"Erro ao calcular equilíbrio mensal: {e}")
            return None
    
    def get_weekly_ma(self, period: int = 20) -> Optional[float]:
        """
        Calcula a Média Móvel Simples de 20 períodos semanal
        """
        try:
            rates = mt5.copy_rates_from_pos(
                self.symbol,
                mt5.TIMEFRAME_W1,
                0,
                period + 5
            )
            
            if rates is None or len(rates) < period:
                logger.warning(f"Dados semanais insuficientes para {self.symbol}")
                return None
            
            df = pd.DataFrame(rates)
            ma = df['close'].rolling(window=period).mean().iloc[-1]
            
            return ma
            
        except Exception as e:
            logger.error(f"Erro ao calcular MA semanal: {e}")
            return None
    
    def count_weekly_candles(self, lookback: int = 20) -> Dict[str, int]:
        """
        Conta velas verdes e vermelhas nas últimas 20 semanas
        """
        try:
            rates = mt5.copy_rates_from_pos(
                self.symbol,
                mt5.TIMEFRAME_W1,
                0,
                lookback
            )
            
            if rates is None:
                return {'green': 0, 'red': 0}
            
            df = pd.DataFrame(rates)
            green = (df['close'] > df['open']).sum()
            red = (df['close'] < df['open']).sum()
            
            return {'green': int(green), 'red': int(red)}
            
        except Exception as e:
            logger.error(f"Erro ao contar velas: {e}")
            return {'green': 0, 'red': 0}
    
    def get_market_bias(self, current_price: float) -> str:
        """
        Determina viés do mercado baseado na análise de equilíbrio
        
        Returns:
            'BUY_ONLY' - Apenas compras (abaixo do equilíbrio)
            'SELL_ONLY' - Apenas vendas (acima do equilíbrio)
            'NEUTRAL' - Próximo do equilíbrio, aguardar
        """
        if self.monthly_equilibrium is None:
            self.calculate_monthly_equilibrium()
        
        if self.monthly_equilibrium is None:
            return 'NEUTRAL'
        
        # Calcular distância percentual do equilíbrio
        distance_pct = ((current_price - self.monthly_equilibrium) / self.monthly_equilibrium) * 100
        
        # Zona neutra: ±0.5% do equilíbrio
        neutral_zone = 0.5
        
        if abs(distance_pct) < neutral_zone:
            return 'NEUTRAL'
        elif current_price < self.monthly_equilibrium:
            return 'BUY_ONLY'
        else:
            return 'SELL_ONLY'


class HedgeStrategy:
    """
    Estratégia Principal de Hedge
    """
    
    def __init__(
        self,
        symbol: str,
        lot_size: float = 0.025,
        max_positions_per_side: int = 7,  # ATUALIZADO: 4→7 (Vídeo #20)
        min_spacing_pips: int = 700,
        normal_spacing_pips: int = 1000,
        max_spacing_pips: int = 1500,
        magic_number: int = 888999,
        account_balance: float = 1000.0,  # Saldo da conta para ajuste dinâmico
    ):
        self.symbol = symbol
        self.lot_size = lot_size
        self.base_max_positions = max_positions_per_side  # Armazena o valor base
        self.max_positions_per_side = max_positions_per_side
        self.min_spacing_pips = min_spacing_pips
        self.normal_spacing_pips = normal_spacing_pips
        self.max_spacing_pips = max_spacing_pips
        self.magic_number = magic_number
        self.account_balance = account_balance  # Saldo da conta para ajuste dinâmico
        
        # Componentes
        self.analyzer = EquilibriumAnalyzer(symbol)
        self.news_protection = NewsProtection()
        
        # Estado
        self.positions: Dict[str, List] = {'BUY': [], 'SELL': []}
        self.in_hedge = False
        
        # Symbol info
        self.point = None
        self.digits = None
        self._init_symbol_info()

        # Atualizar posições máximas baseado no saldo
        self._update_max_positions_by_balance()

    def _update_max_positions_by_balance(self):
        """
        ATUALIZAÇÃO VÍDEO #20: Ajustar número de posições baseado no saldo

        Filosofia do Sr. Johnny:
        - MANTER o mesmo tamanho de lote mesmo com saldo maior
        - AUMENTAR o número de posições conforme saldo cresce
        - Isso reduz DRASTICAMENTE o rebaixamento (60% → 15%)

        Escala sugerida:
        - $1.000: 4 posições por lado
        - $5.000+: 5 posições por lado
        - $10.000+: 6 posições por lado
        - $20.000+: 7 posições por lado (máximo recomendado)
        """
        if self.account_balance >= 20000:
            self.max_positions_per_side = 7
        elif self.account_balance >= 10000:
            self.max_positions_per_side = 6
        elif self.account_balance >= 5000:
            self.max_positions_per_side = 5
        else:
            self.max_positions_per_side = 4  # Mínimo para contas pequenas

        logger.info(f"[{self.symbol}] Saldo: ${self.account_balance:,.2f} → Máx posições/lado: {self.max_positions_per_side}")

    def _init_symbol_info(self):
        """Inicializa informações do símbolo"""
        info = mt5.symbol_info(self.symbol)
        if info is None:
            logger.error(f"Símbolo {self.symbol} não encontrado")
            return
        
        self.point = info.point
        self.digits = info.digits
        logger.info(f"[{self.symbol}] Point: {self.point}, Digits: {self.digits}")
    
    def pips_to_price(self, pips: float) -> float:
        """Converte pips para diferença de preço"""
        # Para pares de moeda: 1 pip = 0.0001 (4 dígitos) ou 0.00001 (5 dígitos)
        # Para índices: 1 pip = 0.01 ou 0.1
        if 'USD' in self.symbol or 'EUR' in self.symbol:
            # Par de moeda
            if self.digits == 5 or self.digits == 3:
                return pips * self.point * 10
            else:
                return pips * self.point
        else:
            # Índice (US30, etc)
            return pips * self.point
    
    def price_to_pips(self, price_diff: float) -> float:
        """Converte diferença de preço para pips"""
        if 'USD' in self.symbol or 'EUR' in self.symbol:
            if self.digits == 5 or self.digits == 3:
                return price_diff / (self.point * 10)
            else:
                return price_diff / self.point
        else:
            return price_diff / self.point
    
    def update_positions(self):
        """Atualiza lista de posições abertas"""
        positions = mt5.positions_get(symbol=self.symbol)
        
        if positions is None:
            positions = []
        
        # Filtrar por magic number
        my_positions = [p for p in positions if p.magic == self.magic_number]
        
        # Separar por tipo
        self.positions['BUY'] = [p for p in my_positions if p.type == mt5.ORDER_TYPE_BUY]
        self.positions['SELL'] = [p for p in my_positions if p.type == mt5.ORDER_TYPE_SELL]
        
        # Verificar se está em hedge
        buy_count = len(self.positions['BUY'])
        sell_count = len(self.positions['SELL'])
        
        self.in_hedge = (buy_count > 0 and sell_count > 0)
        
        logger.debug(f"[{self.symbol}] Posições: {buy_count} BUY, {sell_count} SELL, Hedge: {self.in_hedge}")
    
    def get_adaptive_spacing(self) -> int:
        """
        Calcula espaçamento adaptativo baseado em volatilidade
        """
        try:
            # Buscar dados recentes para calcular volatilidade
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H4, 0, 50)
            
            if rates is None or len(rates) < 20:
                return self.normal_spacing_pips
            
            df = pd.DataFrame(rates)
            
            # Calcular ATR (Average True Range)
            df['h_l'] = df['high'] - df['low']
            df['h_pc'] = abs(df['high'] - df['close'].shift(1))
            df['l_pc'] = abs(df['low'] - df['close'].shift(1))
            
            df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
            atr = df['tr'].rolling(14).mean().iloc[-1]
            
            # Converter ATR para pips
            atr_pips = self.price_to_pips(atr)
            
            # Tendência forte = ATR alto = espaçamento maior
            if atr_pips > 150:  # Alta volatilidade
                spacing = self.max_spacing_pips
            elif atr_pips < 50:  # Baixa volatilidade
                spacing = self.min_spacing_pips
            else:
                spacing = self.normal_spacing_pips
            
            logger.debug(f"[{self.symbol}] ATR: {atr_pips:.1f} pips → Spacing: {spacing} pips")
            return spacing
            
        except Exception as e:
            logger.error(f"Erro ao calcular spacing adaptativo: {e}")
            return self.normal_spacing_pips
    
    def should_open_position(self, direction: str, current_price: float) -> bool:
        """
        Verifica se deve abrir uma nova posição
        
        Args:
            direction: 'BUY' ou 'SELL'
            current_price: Preço atual
            
        Returns:
            True se deve abrir posição
        """
        positions = self.positions[direction]
        
        # Verificar se já atingiu máximo de posições
        if len(positions) >= self.max_positions_per_side:
            return False
        
        # Se não tem posições, usar análise de equilíbrio
        if len(positions) == 0:
            bias = self.analyzer.get_market_bias(current_price)
            
            if direction == 'BUY' and bias != 'BUY_ONLY':
                return False
            elif direction == 'SELL' and bias != 'SELL_ONLY':
                return False
            
            return True
        
        # Se já tem posições, verificar espaçamento
        spacing = self.get_adaptive_spacing()
        spacing_price = self.pips_to_price(spacing)
        
        # Encontrar última posição
        last_position = sorted(positions, key=lambda p: p.time, reverse=True)[0]
        last_price = last_position.price_open
        
        # Verificar se mercado foi longe o suficiente contra nós
        if direction == 'BUY':
            # Para compras, se mercado desceu o suficiente
            return current_price <= (last_price - spacing_price)
        else:
            # Para vendas, se mercado subiu o suficiente
            return current_price >= (last_price + spacing_price)
    
    def open_position(self, direction: str):
        """
        Abre uma nova posição

        Args:
            direction: 'BUY' ou 'SELL'
        """
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            logger.error(f"Não foi possível obter tick para {self.symbol}")
            return

        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            logger.error(f"Não foi possível obter info do símbolo {self.symbol}")
            return

        # Normalizar volume para dentro dos limites do símbolo
        volume = self.lot_size
        volume = max(symbol_info.volume_min, min(volume, symbol_info.volume_max))

        # Arredondar para o passo de volume
        volume_steps = int((volume - symbol_info.volume_min) / symbol_info.volume_step)
        volume = symbol_info.volume_min + (volume_steps * symbol_info.volume_step)

        # Determinar tipo de ordem e preço
        order_type = mt5.ORDER_TYPE_BUY if direction == 'BUY' else mt5.ORDER_TYPE_SELL
        price = tick.ask if direction == 'BUY' else tick.bid

        # Determinar modo de preenchimento correto
        filling_type = mt5.ORDER_FILLING_FOK
        if symbol_info.filling_mode & 2:  # ORDER_FILLING_IOC
            filling_type = mt5.ORDER_FILLING_IOC
        elif symbol_info.filling_mode & 1:  # ORDER_FILLING_FOK
            filling_type = mt5.ORDER_FILLING_FOK
        else:
            # Usar GTC se nenhum dos anteriores disponível
            filling_type = None

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "magic": self.magic_number,
            "comment": f"HEDGE_{direction}_{len(self.positions[direction]) + 1}",
            "type_time": mt5.ORDER_TIME_GTC,
        }

        # Adicionar type_filling apenas se não for None
        if filling_type is not None:
            request["type_filling"] = filling_type

        result = mt5.order_send(request)

        if result is None:
            logger.error(f"Erro ao enviar ordem: resultado None")
            return

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Erro ao abrir posição: {result.retcode} - {result.comment}")
            logger.error(f"Request: {request}")
        else:
            logger.info(f"✅ [{self.symbol}] {direction} aberto @ {price:.5f} | Lote: {volume} | Posição #{len(self.positions[direction]) + 1}")
    
    def close_position_pair(self):
        """
        Fecha um par de posições (1 BUY + 1 SELL) quando hedge está positivo
        Estratégia: usar lucros das hedges para pagar prejuízos das originais
        """
        if not self.in_hedge:
            return
        
        buy_positions = sorted(self.positions['BUY'], key=lambda p: p.profit, reverse=True)
        sell_positions = sorted(self.positions['SELL'], key=lambda p: p.profit, reverse=True)
        
        if not buy_positions or not sell_positions:
            return
        
        # Calcular P&L total
        total_pnl = sum(p.profit for p in buy_positions + sell_positions)
        
        # Se total está positivo ou próximo de zero, tentar fechar um par
        # Priorizar fechar as posições mais recentes (que são as hedges)
        if total_pnl > -5.0:  # Margem de $5 de perda aceitável
            # Pegar a hedge mais recente de cada lado
            latest_buy = buy_positions[0]
            latest_sell = sell_positions[0]
            
            # Fechar par
            self._close_position(latest_buy)
            self._close_position(latest_sell)
            
            pair_pnl = latest_buy.profit + latest_sell.profit
            logger.info(f"🔄 [{self.symbol}] Fechado par de hedge | P&L: ${pair_pnl:.2f} | Total: ${total_pnl:.2f}")
    
    def _close_position(self, position):
        """Fecha uma posição específica"""
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return

        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            logger.error(f"Não foi possível obter info do símbolo {self.symbol}")
            return

        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask

        # Determinar modo de preenchimento correto
        filling_type = mt5.ORDER_FILLING_FOK
        if symbol_info.filling_mode & 2:  # ORDER_FILLING_IOC
            filling_type = mt5.ORDER_FILLING_IOC
        elif symbol_info.filling_mode & 1:  # ORDER_FILLING_FOK
            filling_type = mt5.ORDER_FILLING_FOK
        else:
            filling_type = None

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "magic": self.magic_number,
            "comment": "HEDGE_CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
        }

        if filling_type is not None:
            request["type_filling"] = filling_type

        result = mt5.order_send(request)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✓ Posição {position.ticket} fechada @ {price:.5f} | P&L: ${position.profit:.2f}")
        else:
            logger.error(f"Erro ao fechar posição {position.ticket}: {result.retcode if result else 'None'} - {result.comment if result else 'No result'}")
    
    def run_cycle(self):
        """Executa um ciclo da estratégia"""
        # 1. Verificar proteção de notícias
        is_news, event = self.news_protection.is_news_time()
        if is_news:
            logger.warning(f"⚠️ [{self.symbol}] Proteção de notícias ativa: {event}")
            return

        # 2. ATUALIZAÇÃO VÍDEO #20: Atualizar saldo e recalcular posições máximas
        account_info = mt5.account_info()
        if account_info:
            old_balance = self.account_balance
            self.account_balance = account_info.balance
            # Recalcular posições máximas se o saldo mudou significativamente (>5%)
            if abs(self.account_balance - old_balance) / old_balance > 0.05:
                self._update_max_positions_by_balance()

        # 3. Atualizar posições
        self.update_positions()
        
        # 3. Obter preço atual
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return
        
        current_price = tick.bid
        
        # 4. Verificar se deve abrir novas posições
        # Se estamos em hedge, continuar abrindo conforme necessário
        # Se não estamos em hedge, usar análise de equilíbrio
        
        # Determinar bias
        bias = self.analyzer.get_market_bias(current_price)
        
        # Lógica de entrada
        if not self.in_hedge:
            # Não está em hedge - usar análise de equilíbrio
            if bias == 'BUY_ONLY':
                if self.should_open_position('BUY', current_price):
                    self.open_position('BUY')
            elif bias == 'SELL_ONLY':
                if self.should_open_position('SELL', current_price):
                    self.open_position('SELL')
        else:
            # Está em hedge - continuar estratégia de hedge
            # Verificar qual lado tem mais posições
            buy_count = len(self.positions['BUY'])
            sell_count = len(self.positions['SELL'])
            
            if buy_count > sell_count:
                # Mais compras - mercado subiu contra vendas
                # Continuar abrindo compras se necessário
                if buy_count < self.max_positions_per_side:
                    if self.should_open_position('BUY', current_price):
                        self.open_position('BUY')
            elif sell_count > buy_count:
                # Mais vendas - mercado desceu contra compras
                # Continuar abrindo vendas se necessário
                if sell_count < self.max_positions_per_side:
                    if self.should_open_position('SELL', current_price):
                        self.open_position('SELL')
            
            # Verificar se deve fechar pares
            self.close_position_pair()
    
    def run(self, sleep_seconds: int = 30):
        """
        Loop principal da estratégia
        
        Args:
            sleep_seconds: Segundos entre cada ciclo
        """
        logger.info(f"🚀 Iniciando estratégia de Hedge para {self.symbol}")
        logger.info(f"   Capital: ${self.account_balance:,.2f} | Lote: {self.lot_size}")
        logger.info(f"   Máx posições/lado: {self.max_positions_per_side} (ajustado pelo saldo)")
        logger.info(f"   📌 ESTRATÉGIA VÍDEO #20: Manter lotes fixos, aumentar posições com saldo")
        
        # Calcular equilíbrio inicial
        self.analyzer.calculate_monthly_equilibrium()
        
        while True:
            try:
                self.run_cycle()
                time.sleep(sleep_seconds)
            except KeyboardInterrupt:
                logger.info(f"⏸️ Estratégia interrompida pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro no ciclo principal: {e}", exc_info=True)
                time.sleep(sleep_seconds)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Estratégia de Hedge - EUR/USD e US30')
    parser.add_argument('--symbol', type=str, default='EURUSD', 
                       help='Símbolo para negociar (EURUSD ou US30)')
    parser.add_argument('--lot', type=float, default=0.025,
                       help='Tamanho do lote fixo')
    parser.add_argument('--max-positions', type=int, default=4,
                       help='Máximo de posições por direção')
    parser.add_argument('--min-spacing', type=int, default=700,
                       help='Espaçamento mínimo em pips')
    parser.add_argument('--normal-spacing', type=int, default=1000,
                       help='Espaçamento normal em pips')
    parser.add_argument('--max-spacing', type=int, default=1500,
                       help='Espaçamento máximo em pips')
    parser.add_argument('--magic', type=int, default=888999,
                       help='Magic number')
    parser.add_argument('--balance', type=float, default=1000.0,
                       help='Saldo da conta para ajuste dinâmico de posições')
    
    args = parser.parse_args()
    
    # Inicializar MT5
    if not mt5.initialize():
        logger.error("Falha ao inicializar MT5")
        sys.exit(1)
    
    try:
        # Obter saldo da conta automaticamente se não fornecido
        if args.balance == 1000.0:
            account_info = mt5.account_info()
            if account_info:
                args.balance = account_info.balance

        strategy = HedgeStrategy(
            symbol=args.symbol,
            lot_size=args.lot,
            max_positions_per_side=args.max_positions,
            min_spacing_pips=args.min_spacing,
            normal_spacing_pips=args.normal_spacing,
            max_spacing_pips=args.max_spacing,
            magic_number=args.magic,
            account_balance=args.balance
        )
        
        strategy.run()
    finally:
        mt5.shutdown()
