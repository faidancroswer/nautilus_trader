#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher Multi-Símbolo - Estratégia de Hedge
============================================

Executa estratégias de hedge para EUR/USD e US30 simultaneamente
"""

import MetaTrader5 as mt5
import sys
import time
import logging
from multiprocessing import Process
from hedge_strategy import HedgeStrategy

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hedge_multi_symbol.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('HedgeMultiSymbol')


def run_strategy_for_symbol(symbol: str, lot_size: float, magic_number: int, account_balance: float = 1000.0):
    """
    Executa estratégia para um símbolo específico

    Args:
        symbol: Símbolo (EURUSD ou US30)
        lot_size: Tamanho do lote
        magic_number: Magic number
        account_balance: Saldo da conta para ajuste dinâmico
    """
    # Inicializar MT5 neste processo
    if not mt5.initialize():
        logger.error(f"[{symbol}] Falha ao inicializar MT5")
        return

    try:
        logger.info(f"[{symbol}] Iniciando estratégia...")

        strategy = HedgeStrategy(
            symbol=symbol,
            lot_size=lot_size,
            magic_number=magic_number,
            account_balance=account_balance
        )
        
        strategy.run(sleep_seconds=30)
        
    except Exception as e:
        logger.error(f"[{symbol}] Erro: {e}", exc_info=True)
    finally:
        mt5.shutdown()
        logger.info(f"[{symbol}] Estratégia encerrada")


def main():
    """Função principal - lança estratégias em processos paralelos"""

    # Obter saldo da conta
    account_info = mt5.account_info()
    account_balance = account_info.balance if account_info else 1000.0

    logger.info("=" * 60)
    logger.info("🚀 ESTRATÉGIA DE HEDGE - MULTI-SÍMBOLO")
    logger.info("=" * 60)
    logger.info("\nSímbolos: EUR/USD + US30")
    logger.info(f"Capital: ${account_balance:,.2f} USD")
    logger.info("Lote fixo: 0.025 por símbolo")
    logger.info("Máximo: 7 posições por direção, por símbolo (ajustado pelo saldo)")
    logger.info("Proteção: Eventos de notícias")
    logger.info("\n📌 VÍDEO #20: Manter lotes fixos, aumentar posições com saldo")
    logger.info("\n" + "=" * 60 + "\n")

    # Configurações
    config = {
        'EURUSD': {
            'lot_size': 0.025,
            'magic_number': 888999
        },
        'US30': {
            'lot_size': 0.025,
            'magic_number': 888998  # Magic number diferente para cada símbolo
        }
    }
    
    # Verificar MT5 antes de iniciar processos
    if not mt5.initialize():
        logger.error("❌ Falha ao inicializar MT5")
        sys.exit(1)
    
    # Verificar símbolos disponíveis
    available_symbols = []
    for symbol in config.keys():
        info = mt5.symbol_info(symbol)
        if info is None:
            logger.warning(f"⚠️ Símbolo {symbol} não encontrado")
        else:
            if not info.visible:
                logger.info(f"Habilitando símbolo {symbol}...")
                mt5.symbol_select(symbol, True)
            available_symbols.append(symbol)
    
    mt5.shutdown()
    
    if not available_symbols:
        logger.error("❌ Nenhum símbolo disponível")
        sys.exit(1)
    
    logger.info(f"✅ Símbolos disponíveis: {', '.join(available_symbols)}\n")
    
    # Criar processos para cada símbolo
    processes = []
    
    for symbol in available_symbols:
        cfg = config[symbol]
        
        logger.info(f"🔄 Iniciando processo para {symbol}...")
        
        p = Process(
            target=run_strategy_for_symbol,
            args=(symbol, cfg['lot_size'], cfg['magic_number'], account_balance),
            name=f"Hedge_{symbol}"
        )
        
        p.start()
        processes.append(p)
        
        # Delay entre inicializações
        time.sleep(2)
    
    logger.info("\n✅ Todas as estratégias foram iniciadas!")
    logger.info("📊 Use 'python hedge_dashboard.py' para monitorar")
    logger.info("⏸️ Pressione Ctrl+C para encerrar todas as estratégias\n")
    
    # Aguardar processos
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.info("\n⏸️ Encerrando todas as estratégias...")
        
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join(timeout=5)
        
        logger.info("✅ Todas as estratégias foram encerradas")


if __name__ == "__main__":
    main()
