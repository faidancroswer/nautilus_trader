#!/usr/bin/env python3
"""
Teste rápido do sistema de trading
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Testa se todos os imports funcionam"""
    try:
        import MetaTrader5 as mt5
        logger.info("✓ MetaTrader5 importado")
        
        import pandas as pd
        logger.info("✓ Pandas importado")
        
        import numpy as np
        logger.info("✓ Numpy importado")
        
        import requests
        logger.info("✓ Requests importado")
        
        from ollama_config import setup_ollama_for_trading
        logger.info("✓ Ollama config importado")
        
        return True
    except Exception as e:
        logger.error(f"✗ Erro no import: {e}")
        return False

def test_ollama():
    """Testa conexão com Ollama"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"✓ Ollama OK - {len(models)} modelos")
            return True
        else:
            logger.error("✗ Ollama não responde")
            return False
    except Exception as e:
        logger.error(f"✗ Erro Ollama: {e}")
        return False

def test_mt5():
    """Testa conexão com MT5"""
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"✓ MT5 OK - Conta: {account_info.login}")
                mt5.shutdown()
                return True
            else:
                logger.error("✗ MT5 sem conta")
                mt5.shutdown()
                return False
        else:
            logger.error("✗ MT5 não conecta")
            return False
    except Exception as e:
        logger.error(f"✗ Erro MT5: {e}")
        return False

def test_ollama_config():
    """Testa configuração do Ollama"""
    try:
        from ollama_config import setup_ollama_for_trading
        config = setup_ollama_for_trading("speed")
        if config.validate_model_availability():
            logger.info("✓ Config Ollama OK")
            return True
        else:
            logger.error("✗ Config Ollama falhou")
            return False
    except Exception as e:
        logger.error(f"✗ Erro config: {e}")
        return False

def main():
    logger.info("=== TESTE DO SISTEMA ===")
    
    tests = [
        ("Imports", test_imports),
        ("Ollama", test_ollama),
        ("MT5", test_mt5),
        ("Config Ollama", test_ollama_config)
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\nTestando {name}...")
        result = test_func()
        results.append((name, result))
    
    logger.info("\n=== RESULTADOS ===")
    all_ok = True
    for name, result in results:
        status = "✓ OK" if result else "✗ FALHOU"
        logger.info(f"{name}: {status}")
        if not result:
            all_ok = False
    
    if all_ok:
        logger.info("\n🎉 SISTEMA PRONTO PARA USO!")
        logger.info("Execute: python run_fast_trading.py")
    else:
        logger.error("\n❌ SISTEMA COM PROBLEMAS")
        logger.error("Execute: python setup_fast_trading.py")

if __name__ == "__main__":
    main()
