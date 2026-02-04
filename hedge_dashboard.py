#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard de Monitoramento - Estratégia de Hedge
================================================

Monitora posições ativas, P&L, equilíbrio e próximos níveis
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time
import os
import sys
from typing import Dict, List

# Importar estratégia
from hedge_strategy import HedgeStrategy, EquilibriumAnalyzer


class HedgeDashboard:
    """Dashboard para monitorar múltiplas estratégias de hedge"""
    
    def __init__(self, symbols: List[str], magic_number: int = 888999):
        self.symbols = symbols
        self.magic_number = magic_number
        self.strategies = {}
        
        # Inicializar estratégias
        for symbol in symbols:
            lot_size = 0.025 if symbol == 'EURUSD' else 0.025  # Pode ajustar por símbolo
            self.strategies[symbol] = HedgeStrategy(
                symbol=symbol,
                lot_size=lot_size,
                magic_number=magic_number
            )
    
    def clear_screen(self):
        """Limpa a tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_account_info(self) -> Dict:
        """Obtém informações da conta"""
        account_info = mt5.account_info()
        if account_info is None:
            return {}
        
        return {
            'balance': account_info.balance,
            'equity': account_info.equity,
            'profit': account_info.profit,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'margin_level': account_info.margin_level
        }
    
    def get_symbol_positions(self, symbol: str) -> Dict:
        """Obtém informações das posições de um símbolo"""
        positions = mt5.positions_get(symbol=symbol)
        
        if positions is None:
            positions = []
        
        # Filtrar por magic number
        my_positions = [p for p in positions if p.magic == self.magic_number]
        
        buy_positions = [p for p in my_positions if p.type == mt5.ORDER_TYPE_BUY]
        sell_positions = [p for p in my_positions if p.type == mt5.ORDER_TYPE_SELL]
        
        total_profit = sum(p.profit for p in my_positions)
        buy_profit = sum(p.profit for p in buy_positions)
        sell_profit = sum(p.profit for p in sell_positions)
        
        return {
            'buy_count': len(buy_positions),
            'sell_count': len(sell_positions),
            'total_count': len(my_positions),
            'total_profit': total_profit,
            'buy_profit': buy_profit,
            'sell_profit': sell_profit,
            'in_hedge': len(buy_positions) > 0 and len(sell_positions) > 0,
            'buy_positions': buy_positions,
            'sell_positions': sell_positions
        }
    
    def format_price(self, symbol: str, price: float) -> str:
        """Formata preço de acordo com o símbolo"""
        info = mt5.symbol_info(symbol)
        if info is None:
            return f"{price:.5f}"
        
        return f"{price:.{info.digits}f}"
    
    def display_header(self):
        """Exibe cabeçalho do dashboard"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("=" * 80)
        print("📊 HEDGE STRATEGY DASHBOARD - EUR/USD & US30")
        print(f"🕐 {now}")
        print("=" * 80)
    
    def display_account_summary(self, account_info: Dict):
        """Exibe resumo da conta"""
        print("\n💰 CONTA FBS:")
        print(f"   Balance: ${account_info.get('balance', 0):.2f}")
        print(f"   Equity:  ${account_info.get('equity', 0):.2f}")
        print(f"   Profit:  ${account_info.get('profit', 0):.2f} ", end="")
        
        profit = account_info.get('profit', 0)
        if profit > 0:
            print("📈")
        elif profit < 0:
            print("📉")
        else:
            print("")
        
        print(f"   Margin:  ${account_info.get('margin', 0):.2f}")
        print(f"   Free:    ${account_info.get('free_margin', 0):.2f}")
        
        margin_level = account_info.get('margin_level', 0)
        if margin_level > 0:
            print(f"   Level:   {margin_level:.1f}%")
    
    def display_symbol_status(self, symbol: str):
        """Exibe status de um símbolo"""
        print(f"\n{'─' * 80}")
        print(f"📌 {symbol}")
        print(f"{'─' * 80}")
        
        # Obter preço atual
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print("   ❌ Não foi possível obter dados do símbolo")
            return
        
        current_price = tick.bid
        
        # Análise de equilíbrio
        strategy = self.strategies[symbol]
        bias = strategy.analyzer.get_market_bias(current_price)
        
        # Equilíbrio mensal
        if strategy.analyzer.monthly_equilibrium:
            eq = strategy.analyzer.monthly_equilibrium
            print(f"   Equilíbrio Mensal: {self.format_price(symbol, eq)}")
            print(f"   Topo:  {self.format_price(symbol, strategy.analyzer.last_top)}")
            print(f"   Fundo: {self.format_price(symbol, strategy.analyzer.last_bottom)}")
        
        # MA Semanal
        weekly_ma = strategy.analyzer.get_weekly_ma()
        if weekly_ma:
            print(f"   MA 20 Semanal: {self.format_price(symbol, weekly_ma)}")
        
        # Contador de velas
        candle_count = strategy.analyzer.count_weekly_candles()
        print(f"   Velas 20 Semanas: 🟢 {candle_count['green']} | 🔴 {candle_count['red']}")
        
        # Preço atual e bias
        print(f"\n   💲 Preço Atual: {self.format_price(symbol, current_price)}")
        
        if bias == 'BUY_ONLY':
            print(f"   📊 Viés: COMPRA (abaixo do equilíbrio)")
        elif bias == 'SELL_ONLY':
            print(f"   📊 Viés: VENDA (acima do equilíbrio)")
        else:
            print(f"   📊 Viés: NEUTRO (próximo do equilíbrio)")
        
        # Posições
        pos_info = self.get_symbol_positions(symbol)
        
        print(f"\n   🔢 Posições Ativas:")
        print(f"      Compras:  {pos_info['buy_count']}/4 | P&L: ${pos_info['buy_profit']:.2f}")
        print(f"      Vendas:   {pos_info['sell_count']}/4 | P&L: ${pos_info['sell_profit']:.2f}")
        
        if pos_info['in_hedge']:
            print(f"      🔒 STATUS: EM HEDGE ⚠️")
        else:
            print(f"      ✅ STATUS: Normal")
        
        print(f"\n   💵 P&L Total {symbol}: ${pos_info['total_profit']:.2f}")
        
        # Detalhes das posições
        if pos_info['buy_positions']:
            print(f"\n   📈 Compras Abertas:")
            for i, p in enumerate(pos_info['buy_positions'], 1):
                print(f"      #{i}: {self.format_price(symbol, p.price_open)} | P&L: ${p.profit:.2f}")
        
        if pos_info['sell_positions']:
            print(f"\n   📉 Vendas Abertas:")
            for i, p in enumerate(pos_info['sell_positions'], 1):
                print(f"      #{i}: {self.format_price(symbol, p.price_open)} | P&L: ${p.profit:.2f}")
        
        # Próximo nível de entrada
        spacing = strategy.get_adaptive_spacing()
        spacing_price = strategy.pips_to_price(spacing)
        
        print(f"\n   📏 Espaçamento Adaptativo: {spacing} pips")
        
        if pos_info['buy_count'] > 0:
            last_buy = sorted(pos_info['buy_positions'], key=lambda p: p.time, reverse=True)[0]
            next_buy_level = last_buy.price_open - spacing_price
            print(f"      Próxima COMPRA: {self.format_price(symbol, next_buy_level)}")
        
        if pos_info['sell_count'] > 0:
            last_sell = sorted(pos_info['sell_positions'], key=lambda p: p.time, reverse=True)[0]
            next_sell_level = last_sell.price_open + spacing_price
            print(f"      Próxima VENDA:  {self.format_price(symbol, next_sell_level)}")
    
    def display_footer(self):
        """Exibe rodapé"""
        print(f"\n{'=' * 80}")
        print("💡 Pressione Ctrl+C para sair")
        print("🔄 Atualização a cada 15 segundos")
        print("=" * 80)
    
    def run(self, refresh_seconds: int = 15):
        """
        Loop principal do dashboard
        
        Args:
            refresh_seconds: Segundos entre atualizações
        """
        print("🚀 Iniciando Dashboard de Hedge...")
        
        # Calcular equilíbrios iniciais
        for symbol in self.symbols:
            self.strategies[symbol].analyzer.calculate_monthly_equilibrium()
        
        while True:
            try:
                self.clear_screen()
                
                # Cabeçalho
                self.display_header()
                
                # Resumo da conta
                account_info = self.get_account_info()
                self.display_account_summary(account_info)
                
                # Status de cada símbolo
                for symbol in self.symbols:
                    self.display_symbol_status(symbol)
                
                # Rodapé
                self.display_footer()
                
                time.sleep(refresh_seconds)
                
            except KeyboardInterrupt:
                print("\n\n⏸️ Dashboard encerrado pelo usuário")
                break
            except Exception as e:
                print(f"\n❌ Erro no dashboard: {e}")
                time.sleep(refresh_seconds)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Dashboard de Monitoramento - Hedge Strategy')
    parser.add_argument('--symbols', nargs='+', default=['EURUSD', 'US30'],
                       help='Símbolos para monitorar')
    parser.add_argument('--magic', type=int, default=888999,
                       help='Magic number')
    parser.add_argument('--refresh', type=int, default=15,
                       help='Segundos entre atualizações')
    
    args = parser.parse_args()
    
    # Inicializar MT5
    if not mt5.initialize():
        print("❌ Falha ao inicializar MT5")
        sys.exit(1)
    
    try:
        dashboard = HedgeDashboard(
            symbols=args.symbols,
            magic_number=args.magic
        )
        
        dashboard.run(refresh_seconds=args.refresh)
    finally:
        mt5.shutdown()
