#!/usr/bin/env python3
"""
Script de execução para o sistema de trading rápido
"""

import os
import sys
import logging
import time
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_startup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_prerequisites():
    """Verifica pré-requisitos antes de iniciar"""
    logger.info("Verificando pré-requisitos...")
    
    # Verificar se os arquivos necessários existem
    required_files = [
        'fast_ai_trading.py',
        'ollama_config.py',
        'advanced_ai_alligator.py'
    ]
    
    for file in required_files:
        if not Path(file).exists():
            logger.error(f"Arquivo necessário não encontrado: {file}")
            return False
    
    # Verificar se o Ollama está rodando
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            logger.error("Ollama não está rodando")
            return False
        logger.info("Ollama está rodando - OK")
    except Exception as e:
        logger.error(f"Erro ao verificar Ollama: {e}")
        return False
    
    # Verificar MetaTrader 5
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            logger.error("Não foi possível conectar ao MetaTrader 5")
            return False
        
        account_info = mt5.account_info()
        if not account_info:
            logger.error("Não foi possível obter informações da conta MT5")
            mt5.shutdown()
            return False
        
        logger.info(f"MT5 conectado - Conta: {account_info.login}")
        logger.info(f"Servidor: {account_info.server}")
        logger.info(f"Saldo: {account_info.balance} {account_info.currency}")
        
        mt5.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"Erro ao verificar MT5: {e}")
        return False


def show_menu():
    """Mostra menu de opções"""
    print("\n" + "="*60)
    print("    SISTEMA DE TRADING AI COM OLLAMA - FBS")
    print("="*60)
    print("1. Executar Trading Rápido (Otimizado para Velocidade)")
    print("2. Executar Trading Avançado (Análise Completa)")
    print("3. Configurar Sistema")
    print("4. Testar Conexões")
    print("5. Ver Status do Sistema")
    print("0. Sair")
    print("="*60)


def run_fast_trading():
    """Executa o sistema de trading rápido"""
    logger.info("Iniciando sistema de trading rápido...")
    try:
        subprocess.run([sys.executable, "fast_ai_trading.py"])
    except KeyboardInterrupt:
        logger.info("Sistema interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao executar trading rápido: {e}")


def run_advanced_trading():
    """Executa o sistema de trading avançado"""
    logger.info("Iniciando sistema de trading avançado...")
    try:
        subprocess.run([sys.executable, "advanced_ai_alligator.py"])
    except KeyboardInterrupt:
        logger.info("Sistema interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao executar trading avançado: {e}")


def setup_system():
    """Executa a configuração do sistema"""
    logger.info("Executando configuração do sistema...")
    try:
        subprocess.run([sys.executable, "setup_fast_trading.py"])
    except Exception as e:
        logger.error(f"Erro na configuração: {e}")


def test_connections():
    """Testa todas as conexões"""
    logger.info("Testando conexões...")
    
    # Testar Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"✓ Ollama OK - {len(models)} modelos disponíveis")
            for model in models:
                logger.info(f"  - {model['name']}")
        else:
            logger.error("✗ Ollama não está respondendo")
    except Exception as e:
        logger.error(f"✗ Erro no Ollama: {e}")
    
    # Testar MT5
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"✓ MT5 OK - Conta: {account_info.login}")
                logger.info(f"  Servidor: {account_info.server}")
                logger.info(f"  Saldo: {account_info.balance} {account_info.currency}")
            else:
                logger.error("✗ MT5 conectado mas sem informações da conta")
            mt5.shutdown()
        else:
            logger.error("✗ Não foi possível conectar ao MT5")
    except Exception as e:
        logger.error(f"✗ Erro no MT5: {e}")
    
    # Testar configuração do Ollama
    try:
        from ollama_config import setup_ollama_for_trading
        config = setup_ollama_for_trading("speed")
        if config.validate_model_availability():
            logger.info("✓ Configuração Ollama OK")
        else:
            logger.error("✗ Problema na configuração do Ollama")
    except Exception as e:
        logger.error(f"✗ Erro na configuração: {e}")


def show_system_status():
    """Mostra status detalhado do sistema"""
    logger.info("Status do Sistema:")
    
    # Status dos arquivos
    files_status = {
        'fast_ai_trading.py': 'Sistema de Trading Rápido',
        'advanced_ai_alligator.py': 'Sistema de Trading Avançado',
        'ollama_config.py': 'Configuração do Ollama',
        'setup_fast_trading.py': 'Script de Configuração'
    }
    
    print("\n📁 Arquivos do Sistema:")
    for file, description in files_status.items():
        if Path(file).exists():
            size = Path(file).stat().st_size
            print(f"  ✓ {file} ({size} bytes) - {description}")
        else:
            print(f"  ✗ {file} - FALTANDO")
    
    # Status das conexões
    print("\n🔗 Status das Conexões:")
    
    # Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            print("  ✓ Ollama - Conectado")
        else:
            print("  ✗ Ollama - Erro na conexão")
    except:
        print("  ✗ Ollama - Não está rodando")
    
    # MT5
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            account_info = mt5.account_info()
            if account_info:
                print(f"  ✓ MT5 - Conectado (Conta: {account_info.login})")
            else:
                print("  ⚠ MT5 - Conectado mas sem conta")
            mt5.shutdown()
        else:
            print("  ✗ MT5 - Não foi possível conectar")
    except:
        print("  ✗ MT5 - Não instalado")
    
    # Logs
    print("\n📊 Logs Recentes:")
    log_files = ['fast_ai_trading.log', 'advanced_ai_trading.log', 'trading_startup.log']
    for log_file in log_files:
        if Path(log_file).exists():
            size = Path(log_file).stat().st_size
            print(f"  📄 {log_file} ({size} bytes)")


def main():
    """Função principal"""
    print("Iniciando sistema de trading...")
    
    while True:
        show_menu()
        
        try:
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == "0":
                print("Saindo...")
                break
            elif choice == "1":
                if check_prerequisites():
                    run_fast_trading()
                else:
                    print("❌ Pré-requisitos não atendidos. Execute a opção 3 para configurar.")
            elif choice == "2":
                if check_prerequisites():
                    run_advanced_trading()
                else:
                    print("❌ Pré-requisitos não atendidos. Execute a opção 3 para configurar.")
            elif choice == "3":
                setup_system()
            elif choice == "4":
                test_connections()
            elif choice == "5":
                show_system_status()
            else:
                print("❌ Opção inválida!")
            
            input("\nPressione Enter para continuar...")
            
        except KeyboardInterrupt:
            print("\n\nSaindo...")
            break
        except Exception as e:
            logger.error(f"Erro: {e}")
            input("Pressione Enter para continuar...")


if __name__ == "__main__":
    main()
