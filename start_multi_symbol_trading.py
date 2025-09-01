#!/usr/bin/env python3
"""
Script de inicialização para trading multi-símbolo
XAUUSD (Ouro) e BTCUSD (Bitcoin)
"""

import os
import sys
import time
import logging
import subprocess
import MetaTrader5 as mt5
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_and_start_ollama():
    """Verifica e inicia Ollama se necessário"""
    try:
        import requests
        
        # Testar se já está rodando
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                logger.info("✓ Ollama já está rodando")
                return True
        except:
            pass
        
        # Tentar iniciar
        logger.info("Iniciando Ollama...")
        if os.name == 'nt':  # Windows
            subprocess.Popen(['ollama', 'serve'], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(['ollama', 'serve'])
        
        # Aguardar inicialização
        for i in range(15):
            time.sleep(2)
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    logger.info("✓ Ollama iniciado com sucesso")
                    return True
            except:
                continue
        
        logger.warning("⚠ Ollama pode não estar funcionando perfeitamente")
        return False
        
    except Exception as e:
        logger.error(f"Erro com Ollama: {e}")
        return False


def verify_symbols():
    """Verifica se os símbolos estão disponíveis"""
    if not mt5.initialize():
        logger.error("Falha ao conectar MT5")
        return False
    
    symbols = ["XAUUSD", "BTCUSD"]
    available = []
    
    for symbol in symbols:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            if not symbol_info.visible:
                mt5.symbol_select(symbol, True)
            
            # Testar dados
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 5)
            if rates is not None:
                available.append(symbol)
                logger.info(f"✓ {symbol} disponível (Preço: {rates[-1]['close']})")
            else:
                logger.warning(f"⚠ {symbol} sem dados")
        else:
            logger.warning(f"✗ {symbol} não encontrado")
    
    mt5.shutdown()
    
    if len(available) == 2:
        logger.info("🎉 Ambos os símbolos estão prontos!")
        return True
    elif len(available) == 1:
        logger.info(f"⚠ Apenas {available[0]} disponível")
        return True
    else:
        logger.error("❌ Nenhum símbolo disponível")
        return False


def show_trading_menu():
    """Mostra menu de opções de trading"""
    print("\n" + "="*60)
    print("   TRADING AI - XAUUSD (OURO) & BTCUSD (BITCOIN)")
    print("="*60)
    print("1. 🚀 Executar Trading Multi-Símbolo (Novo Sistema)")
    print("2. ⚡ Executar Trading Rápido (Sistema Otimizado)")
    print("3. 📊 Executar Trading Avançado (Análise Completa)")
    print("4. 🔍 Testar Símbolos e Conexões")
    print("5. 📈 Ver Status das Posições")
    print("6. ⚙️ Configurar Sistema")
    print("0. ❌ Sair")
    print("="*60)


def show_positions_status():
    """Mostra status das posições atuais"""
    if not mt5.initialize():
        logger.error("Falha ao conectar MT5")
        return
    
    try:
        account_info = mt5.account_info()
        if account_info:
            print(f"\n📊 CONTA: {account_info.login}")
            print(f"💰 Saldo: {account_info.balance:.2f} {account_info.currency}")
            print(f"💎 Equity: {account_info.equity:.2f} {account_info.currency}")
            print(f"📈 Margem Livre: {account_info.margin_free:.2f} {account_info.currency}")
        
        symbols = ["XAUUSD", "BTCUSD"]
        total_positions = 0
        
        for symbol in symbols:
            positions = mt5.positions_get(symbol=symbol)
            if positions:
                print(f"\n🔸 {symbol} - {len(positions)} posições:")
                for pos in positions:
                    profit_emoji = "📈" if pos.profit > 0 else "📉" if pos.profit < 0 else "➖"
                    direction = "🟢 BUY" if pos.type == 0 else "🔴 SELL"
                    print(f"   {direction} {pos.volume} lots | "
                          f"Preço: {pos.price_open} | "
                          f"Atual: {pos.price_current} | "
                          f"{profit_emoji} P&L: {pos.profit:.2f}")
                total_positions += len(positions)
            else:
                print(f"\n🔸 {symbol} - Sem posições")
        
        print(f"\n📊 Total de posições: {total_positions}")
        
    except Exception as e:
        logger.error(f"Erro ao verificar posições: {e}")
    finally:
        mt5.shutdown()


def main():
    """Função principal"""
    print("🤖 Iniciando Sistema de Trading AI Multi-Símbolo")
    
    while True:
        show_trading_menu()
        
        try:
            choice = input("\n👉 Escolha uma opção: ").strip()
            
            if choice == "0":
                print("👋 Saindo...")
                break
                
            elif choice == "1":
                logger.info("Iniciando Trading Multi-Símbolo...")
                
                # Verificar pré-requisitos
                if not verify_symbols():
                    print("❌ Símbolos não disponíveis")
                    continue
                
                # Iniciar Ollama
                check_and_start_ollama()
                
                # Executar sistema
                try:
                    subprocess.run([sys.executable, "multi_symbol_ai_trading.py"])
                except KeyboardInterrupt:
                    print("\n⏹ Trading interrompido")
                
            elif choice == "2":
                logger.info("Iniciando Trading Rápido...")
                try:
                    subprocess.run([sys.executable, "fast_ai_trading.py"])
                except KeyboardInterrupt:
                    print("\n⏹ Trading interrompido")
                
            elif choice == "3":
                logger.info("Iniciando Trading Avançado...")
                try:
                    subprocess.run([sys.executable, "advanced_ai_alligator.py"])
                except KeyboardInterrupt:
                    print("\n⏹ Trading interrompido")
                
            elif choice == "4":
                logger.info("Testando sistema...")
                subprocess.run([sys.executable, "test_symbols.py"])
                
            elif choice == "5":
                show_positions_status()
                
            elif choice == "6":
                logger.info("Configurando sistema...")
                subprocess.run([sys.executable, "setup_fast_trading.py"])
                
            else:
                print("❌ Opção inválida!")
            
            if choice != "5":  # Não pausar para status
                input("\n⏸ Pressione Enter para continuar...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Saindo...")
            break
        except Exception as e:
            logger.error(f"Erro: {e}")
            input("⏸ Pressione Enter para continuar...")


if __name__ == "__main__":
    main()
