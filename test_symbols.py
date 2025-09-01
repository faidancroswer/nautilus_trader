#!/usr/bin/env python3
"""
Teste de disponibilidade dos símbolos XAUUSD e BTCUSD no broker FBS
"""

import MetaTrader5 as mt5
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_symbol_availability():
    """Testa disponibilidade dos símbolos no broker"""
    
    # Inicializar MT5
    if not mt5.initialize():
        logger.error(f"Falha ao inicializar MT5: {mt5.last_error()}")
        return False
    
    # Informações da conta
    account_info = mt5.account_info()
    if not account_info:
        logger.error("Falha ao obter informações da conta")
        mt5.shutdown()
        return False
    
    logger.info(f"Conta: {account_info.login}")
    logger.info(f"Servidor: {account_info.server}")
    logger.info(f"Broker: {account_info.company}")
    
    # Símbolos para testar
    symbols_to_test = ["XAUUSD", "BTCUSD", "GOLD", "BTC", "BITCOIN"]
    
    logger.info("\n=== TESTANDO SÍMBOLOS ===")
    
    available_symbols = []
    
    for symbol in symbols_to_test:
        logger.info(f"\nTestando {symbol}...")
        
        # Verificar se símbolo existe
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.warning(f"  ✗ {symbol} - Não encontrado")
            continue
        
        # Tentar selecionar o símbolo
        if not symbol_info.visible:
            if mt5.symbol_select(symbol, True):
                logger.info(f"  ✓ {symbol} - Selecionado com sucesso")
            else:
                logger.warning(f"  ✗ {symbol} - Não pode ser selecionado")
                continue
        else:
            logger.info(f"  ✓ {symbol} - Já visível")
        
        # Obter informações detalhadas
        logger.info(f"    Nome: {symbol_info.description}")
        logger.info(f"    Moeda base: {symbol_info.currency_base}")
        logger.info(f"    Moeda profit: {symbol_info.currency_profit}")
        logger.info(f"    Dígitos: {symbol_info.digits}")
        logger.info(f"    Point: {symbol_info.point}")
        logger.info(f"    Spread: {symbol_info.spread}")
        logger.info(f"    Volume mín: {symbol_info.volume_min}")
        logger.info(f"    Volume máx: {symbol_info.volume_max}")
        logger.info(f"    Volume step: {symbol_info.volume_step}")
        
        # Verificar se trading está habilitado
        if symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
            logger.warning(f"  ⚠ {symbol} - Trading desabilitado")
            continue
        elif symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_LONGONLY:
            logger.info(f"  ⚠ {symbol} - Apenas LONG permitido")
        elif symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_SHORTONLY:
            logger.info(f"  ⚠ {symbol} - Apenas SHORT permitido")
        elif symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_CLOSEONLY:
            logger.warning(f"  ⚠ {symbol} - Apenas fechamento permitido")
            continue
        else:
            logger.info(f"  ✓ {symbol} - Trading completo habilitado")
        
        # Testar obtenção de dados
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 10)
            if rates is not None and len(rates) > 0:
                latest_price = rates[-1]['close']
                logger.info(f"  ✓ {symbol} - Dados disponíveis (Preço: {latest_price})")
                
                # Testar tick data
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    logger.info(f"    Bid: {tick.bid} | Ask: {tick.ask} | Spread: {tick.ask - tick.bid:.5f}")
                    available_symbols.append(symbol)
                else:
                    logger.warning(f"  ✗ {symbol} - Sem dados de tick")
            else:
                logger.warning(f"  ✗ {symbol} - Sem dados históricos")
        except Exception as e:
            logger.error(f"  ✗ {symbol} - Erro ao obter dados: {e}")
    
    logger.info(f"\n=== RESUMO ===")
    logger.info(f"Símbolos disponíveis para trading: {available_symbols}")
    
    if "XAUUSD" in available_symbols:
        logger.info("✓ OURO (XAUUSD) - Pronto para trading")
    else:
        logger.warning("✗ OURO - Não disponível (tente GOLD, XAU, etc.)")
    
    if "BTCUSD" in available_symbols:
        logger.info("✓ BITCOIN (BTCUSD) - Pronto para trading")
    else:
        logger.warning("✗ BITCOIN - Não disponível (tente BTC, BITCOIN, etc.)")
    
    # Listar todos os símbolos disponíveis que contêm ouro ou bitcoin
    logger.info("\n=== SÍMBOLOS RELACIONADOS DISPONÍVEIS ===")
    all_symbols = mt5.symbols_get()
    if all_symbols:
        gold_symbols = [s.name for s in all_symbols if any(term in s.name.upper() for term in ['GOLD', 'XAU', 'GLD'])]
        btc_symbols = [s.name for s in all_symbols if any(term in s.name.upper() for term in ['BTC', 'BITCOIN'])]
        
        if gold_symbols:
            logger.info(f"Símbolos de Ouro disponíveis: {gold_symbols[:10]}")  # Primeiros 10
        if btc_symbols:
            logger.info(f"Símbolos de Bitcoin disponíveis: {btc_symbols[:10]}")  # Primeiros 10
    
    mt5.shutdown()
    return len(available_symbols) > 0


def test_ollama_for_symbols():
    """Testa Ollama com prompts específicos para os símbolos"""
    logger.info("\n=== TESTANDO OLLAMA PARA SÍMBOLOS ===")
    
    try:
        import requests
        
        # Testar conexão
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            logger.error("Ollama não está rodando")
            return False
        
        logger.info("✓ Ollama conectado")
        
        # Testar prompts para cada símbolo
        test_prompts = {
            "XAUUSD": """GOLD TRADING - High volatility precious metal
XAUUSD 2650.50
ALG: bullish (S:1.2%)
RSI: 45 MACD: 0.0012
VOL: 1.8% CHG1H: 0.3%

RESPOND: BUY/SELL/HOLD/CLOSE""",
            
            "BTCUSD": """BITCOIN TRADING - Extreme volatility cryptocurrency
BTCUSD 95000.00
ALG: bearish (S:2.1%)
RSI: 65 MACD: -0.0045
VOL: 3.2% CHG1H: -1.2%

RESPOND: BUY/SELL/HOLD/CLOSE"""
        }
        
        for symbol, prompt in test_prompts.items():
            logger.info(f"\nTestando prompt para {symbol}...")
            
            payload = {
                "model": "phi3:latest",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2,
                "max_tokens": 20
            }
            
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get('response', '').strip()
                    logger.info(f"  ✓ {symbol} - Resposta AI: {ai_response}")
                else:
                    logger.error(f"  ✗ {symbol} - Erro API: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"  ✗ {symbol} - Erro: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro no teste do Ollama: {e}")
        return False


def main():
    """Função principal de teste"""
    logger.info("=== TESTE DE SÍMBOLOS E OLLAMA ===")
    
    # Testar símbolos no MT5
    symbols_ok = test_symbol_availability()
    
    # Testar Ollama
    ollama_ok = test_ollama_for_symbols()
    
    logger.info("\n=== RESULTADO FINAL ===")
    if symbols_ok and ollama_ok:
        logger.info("🎉 SISTEMA PRONTO PARA XAUUSD E BTCUSD!")
        logger.info("Execute: python multi_symbol_ai_trading.py")
    else:
        if not symbols_ok:
            logger.error("❌ Problemas com símbolos no broker")
        if not ollama_ok:
            logger.error("❌ Problemas com Ollama")
        logger.error("Resolva os problemas antes de continuar")


if __name__ == "__main__":
    main()
