#!/usr/bin/env python3
"""
EA2060 Trading System - Main Runner
Sistema completo com opções de execução para diferentes modos
"""

import sys
import os
from pathlib import Path

# Adicionar diretório atual ao PATH
sys.path.append(str(Path(__file__).parent))

def show_menu():
    """Mostrar menu de opções"""
    print("="*80)
    print("EA2060 819830 - COMPLETE TRADING SYSTEM")
    print("="*80)
    print("Select execution mode:")
    print()
    print("STANDARD MODES:")
    print("  1. EA2060 Simple Trader           (Basic indicators)")
    print("  2. EA2060 Optimized Trader       (Optimized parameters)")
    print("  3. EA2060 Backtest               (Quick optimization)")
    print()
    print("AI-ENHANCED MODES:")
    print("  4. EA2060 LLM-Enhanced Trader   (AI-powered decisions)")
    print("  5. LLM Analysis Demo            (Test AI analysis)")
    print()
    print("ADVANCED MODES:")
    print("  6. Nautilus Integration         (Framework integration)")
    print("  7. Performance Analysis         (Compare strategies)")
    print()
    print("UTILITY:")
    print("  8. View System Status          (Check connections)")
    print("  9. Configuration Settings      (Adjust parameters)")
    print()
    print("  0. Exit")
    print("="*80)

def run_simple_trader():
    """Executar EA2060 Simple Trader"""
    print("\\nStarting EA2060 Simple Trader...")
    try:
        from ea2060_simple_trader import EA2060SimpleTrader
        trader = EA2060SimpleTrader()

        if trader.initialize_mt5():
            print("[+] Simple Trader initialized successfully")
            trader.run()
        else:
            print("[-] Failed to initialize Simple Trader")
    except Exception as e:
        print(f"[-] Error: {e}")

def run_optimized_trader():
    """Executar EA2060 Optimized Trader"""
    print("\\nStarting EA2060 Optimized Trader...")
    try:
        from ea2060_optimized_trader import EA2060OptimizedTrader
        trader = EA2060OptimizedTrader()

        if trader.initialize_mt5():
            print("[+] Optimized Trader initialized successfully")
            trader.run()
        else:
            print("[-] Failed to initialize Optimized Trader")
    except Exception as e:
        print(f"[-] Error: {e}")

def run_backtest():
    """Executar backtest"""
    print("\\nStarting EA2060 Backtest Optimization...")
    try:
        from ea2060_quick_backtest import quick_optimization
        quick_optimization()
    except Exception as e:
        print(f"[-] Error: {e}")

def run_llm_enhanced_trader():
    """Executar EA2060 com LLM"""
    print("\\nStarting EA2060 LLM-Enhanced Trader...")
    try:
        from ea2060_llm_enhanced import EA2060LLMTrader
        trader = EA2060LLMTrader()

        if trader.initialize_mt5():
            print("[+] LLM-Enhanced Trader initialized successfully")
            trader.run()
        else:
            print("[-] Failed to initialize LLM-Enhanced Trader")
    except Exception as e:
        print(f"[-] Error: {e}")

def run_llm_demo():
    """Executar demo de análise LLM"""
    print("\\nRunning LLM Analysis Demo...")
    try:
        from ea2060_llm_enhanced import EA2060LLMTrader, LLMAnalyzer

        # Demo de análise
        trader = EA2060LLMTrader()
        if trader.initialize_mt5():
            df = trader.get_historical_data('XAUUSD', trader.timeframe, 100)
            if df is not None:
                llm_analysis = trader.analyze_with_llm(df)
                if llm_analysis:
                    print("\\n" + "="*60)
                    print("LLM ANALYSIS RESULTS")
                    print("="*60)
                    print(f"Action: {llm_analysis['action']}")
                    print(f"Confidence: {llm_analysis['confidence']:.2f}")
                    print(f"Signal Strength: {llm_analysis['signal_strength']}")
                    print(f"Risk Level: {llm_analysis['risk_level']}")
                    print(f"Reward Estimate: {llm_analysis['reward_estimate']}")
                    print(f"Reasoning: {llm_analysis['reasoning']}")
                    print("="*60)
                else:
                    print("[-] LLM analysis failed")
            else:
                print("[-] Failed to get data")
        else:
            print("[-] Failed to initialize MT5")
    except Exception as e:
        print(f"[-] Error: {e}")

def run_nautilus_integration():
    """Executar integração com Nautilus"""
    print("\\nStarting Nautilus Trader Integration...")
    try:
        # Verificar se Nautilus está disponível
        try:
            from nautilus_trader.backtest.engine import BacktestEngine
            print("[+] Nautilus Trader module found")

            # Criar demonstração de configuração
            print("\\nCreating Nautilus backtest configuration...")
            print("  Strategy: EA2060LLMStrategy")
            print("  Venue: MT5 Simulation")
            print("  Initial Balance: $10,000")
            print("  Data: XAUUSD H1")
            print("  LLM Integration: Enabled")

            print("\\nConfiguration completed!")
            print("Note: Full Nautilus integration requires additional setup")
            print("Current LLM-enhanced trader is ready for live trading")

        except ImportError:
            print("[-] Nautilus Trader module not found")
            print("\\nAlternative: Using standalone LLM-enhanced trader")
            print("This provides the same LLM integration benefits")
            print("without requiring full Nautilus framework setup")

            # Oferecer para executar o trader LLM standalone
            choice = input("\\nRun LLM-enhanced trader instead? (y/n): ").strip().lower()
            if choice == 'y':
                run_llm_enhanced_trader()

    except Exception as e:
        print(f"[-] Error: {e}")

def run_performance_analysis():
    """Executar análise de performance"""
    print("\\nStarting Performance Analysis...")
    try:
        import MetaTrader5 as mt5
        import pandas as pd
        import numpy as np

        if mt5.initialize():
            print("[+] MT5 connected")

            # Obter dados recentes
            rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H1, 0, 200)
            mt5.shutdown()

            if rates is not None:
                df = pd.DataFrame(rates)
                print(f"[+] Analyzed {len(df)} recent bars")
                print(f"  Date range: {pd.to_datetime(rates['time'], unit='s').min()} to {pd.to_datetime(rates['time'], unit='s').max()}")
                print(f"  Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
                print(f"  Average volume: {df['tick_volume'].mean():.0f}")
                print(f"  Volatility (std): {df['close'].std():.2f}")

                # Análise de tendência
                prices = df['close'].values
                trend = np.polyfit(range(len(prices)), prices, 1)[0]
                if trend > 0:
                    print(f"  Trend: UPTREND (+{trend:.4f})")
                else:
                    print(f"  Trend: DOWNTREND ({trend:.4f})")

                print("\\n[+] Performance analysis completed")
            else:
                print("[-] Failed to get data")
        else:
            print("[-] Failed to initialize MT5")
    except Exception as e:
        print(f"[-] Error: {e}")

def show_system_status():
    """Mostrar status do sistema"""
    print("\\n" + "="*60)
    print("SYSTEM STATUS")
    print("="*60)

    try:
        # Verificar MT5
        import MetaTrader5 as mt5
        if mt5.initialize():
            account_info = mt5.account_info()
            print("[+] MT5 Connection: Active")
            print(f"  Account: {account_info.login}")
            print(f"  Server: {account_info.server}")
            print(f"  Balance: ${account_info.balance:.2f}")
            print(f"  Equity: ${account_info.equity:.2f}")
            print(f"  Leverage: {account_info.leverage}:1")

            # Verificar posições abertas
            positions = mt5.positions_get()
            if positions:
                print(f"  Open Positions: {len(positions)}")
            else:
                print(f"  Open Positions: None")

            mt5.shutdown()
        else:
            print("[-] MT5 Connection: Failed")

        # Verificar módulos
        print(f"\\nModules Status:")
        try:
            import pandas_ta
            print(f"[+] pandas_ta: Installed")
        except ImportError:
            print(f"[-] pandas_ta: Not installed")

        try:
            import MetaTrader5
            print(f"[+] MetaTrader5: Installed")
        except ImportError:
            print(f"[-] MetaTrader5: Not installed")

        # Verificar arquivos
        print(f"\\nFiles Status:")
        files_to_check = [
            'ea2060_simple_trader.py',
            'ea2060_optimized_trader.py',
            'ea2060_llm_enhanced.py',
            'ea2060_quick_backtest.py',
            'ea2060_optimized.txt'
        ]

        for file in files_to_check:
            if os.path.exists(file):
                print(f"[+] {file}: Available")
            else:
                print(f"[-] {file}: Not found")

        print("="*60)

    except Exception as e:
        print(f"[-] Error checking status: {e}")

def show_configuration():
    """Mostrar configurações"""
    print("\\n" + "="*60)
    print("CONFIGURATION SETTINGS")
    print("="*60)

    # Parâmetros otimizados
    print(f"\\nOptimized Parameters (from backtest):")
    print(f"  EMA Fast: 6")
    print(f"  EMA Slow: 18")
    print(f"  Stop Loss: 250 pips (adaptive)")
    print(f"  Take Profit: 300 pips (RR 1:1.2)")
    print(f"  Risk per Trade: 1.0%")
    print(f"  Max Positions: 3")

    # Parâmetros LLM
    print(f"\\nLLM Parameters:")
    print(f"  Min Confidence: 0.65")
    print(f"  Max Risk Level: MEDIUM")
    print(f"  Analysis Weighting:")
    print(f"    EMA Crossover: 25%")
    print(f"    SuperTrend: 20%")
    print(f"    Momentum: 15%")
    print(f"    Volume: 10%")
    print(f"    Support/Resistance: 15%")
    print(f"    Volatility: 10%")
    print(f"    Temporal: 5%")

    # Filtros de segurança
    print(f"\\nSafety Filters:")
    print(f"  Max Spread: 30 points")
    print(f"  Min Volatility: 0.1%")
    print(f"  Volume Confirmation: >1.0")
    print(f"  RSI Range: 35-65")

    print("="*60)
    print("To modify parameters, edit the respective trader files")

def main():
    """Função principal"""
    while True:
        show_menu()

        try:
            choice = input("\\nEnter your choice (0-9): ").strip()

            if choice == "0":
                print("\\nExiting EA2060 Trading System...")
                break
            elif choice == "1":
                run_simple_trader()
            elif choice == "2":
                run_optimized_trader()
            elif choice == "3":
                run_backtest()
            elif choice == "4":
                run_llm_enhanced_trader()
            elif choice == "5":
                run_llm_demo()
            elif choice == "6":
                run_nautilus_integration()
            elif choice == "7":
                run_performance_analysis()
            elif choice == "8":
                show_system_status()
            elif choice == "9":
                show_configuration()
            else:
                print("\\n⚠ Invalid choice. Please select 0-9.")

            # Pausar após cada operação (apenas se não for automático)
            if choice != "0" and sys.stdin.isatty():
                input("\\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\\n\\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"\\n[-] Error: {e}")
            if sys.stdin.isatty():
                input("Press Enter to continue...")

if __name__ == "__main__":
    main()