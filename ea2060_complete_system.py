#!/usr/bin/env python3
"""
EA2060 Complete Trading System
Sistema unificado de backtest, otimização e trading com Nautilus + LLM
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import MetaTrader5 as mt5

# Configurar encoding no Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ea2060_complete_system.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Importar componentes
from ea2060_advanced_backtest import (
    BacktestConfig, EA2060AdvancedBacktester, GeneticOptimizer
)
from ea2060_nautilus_llm_strategy import EA2060NautilusLLMStrategy, EA2060NautilusLLMRunner
from ea2060_optimized_trader import EA2060OptimizedTrader
from ea2060_llm_enhanced import EA2060LLMTrader

class EA2060CompleteSystem:
    """Sistema completo EA2060 com todas as funcionalidades"""

    def __init__(self):
        self.logger = logger
        self.system_status = {
            'mt5_connected': False,
            'nautilus_available': False,
            'llm_enabled': False,
            'data_loaded': False
        }
        self.performance_cache = {}

        # Verificar componentes disponíveis
        self._check_system_components()

        # Configurações otimizadas
        self.best_config = BacktestConfig(
            ema_fast_period=6,
            ema_slow_period=18,
            supertrend_period=10,
            supertrend_multiplier=3.0,
            adx_threshold=25.0,
            rsi_period=14,
            rsi_oversold=30.0,
            rsi_overbought=70.0,
            stop_loss_atr_multiplier=2.0,
            take_profit_atr_multiplier=3.0,
            max_risk_per_trade=0.02,
            max_positions=3,
            trailing_stop_activation=1.5,
            trailing_stop_distance=0.5,
            min_volume_ratio=1.0,
            max_spread_points=30,
            min_volatility=0.001
        )

    def _check_system_components(self):
        """Verificar quais componentes estão disponíveis"""
        self.logger.info("Checking system components...")

        # Verificar MT5
        try:
            if mt5.initialize():
                self.system_status['mt5_connected'] = True
                account = mt5.account_info()
                self.logger.info(f"[+] MT5 Connected: Account {account.login} (${account.balance:.2f})")
                mt5.shutdown()
            else:
                self.system_status['mt5_connected'] = False
                self.logger.info("[-] MT5 Not Connected")
        except Exception as e:
            self.logger.error(f"[-] MT5 Error: {e}")
            self.system_status['mt5_connected'] = False

        # Verificar Nautilus
        try:
            from nautilus_trader.backtest.engine import BacktestEngine
            self.system_status['nautilus_available'] = True
            self.logger.info("[+] Nautilus Trader Available")
        except ImportError:
            self.system_status['nautilus_available'] = False
            self.logger.info("[-] Nautilus Trader Not Available")

        # Verificar componentes LLM
        try:
            from ea2060_llm_enhanced import LLMAnalyzer
            self.system_status['llm_enabled'] = True
            self.logger.info("[+] LLM Components Available")
        except ImportError:
            self.system_status['llm_enabled'] = False
            self.logger.info("[-] LLM Components Not Available")

    def show_main_menu(self):
        """Exibir menu principal"""
        while True:
            print("\n" + "=" * 80)
            print("🚀 EA2060 COMPLETE TRADING SYSTEM")
            print("=" * 80)
            print("System Status:")
            print(f"  MT5: {'[+]' if self.system_status['mt5_connected'] else '[-]'} Connected")
            print(f"  Nautilus: {'[+]' if self.system_status['nautilus_available'] else '[-]'} Available")
            print(f"  LLM: {'[+]' if self.system_status['llm_enabled'] else '[-]'} Enabled")
            print("\n📊 BACKTEST & OPTIMIZATION:")
            print("  1. Advanced Backtest (Optimized Parameters)")
            print("  2. Genetic Optimization")
            print("  3. Grid Search Optimization")
            print("  4. Multi-Strategy Comparison")
            print("  5. Parameter Stress Test")
            print("\n🤖 AI-POWERED TRADING:")
            print("  6. LLM-Enhanced Backtest")
            print("  7. Nautilus + LLM Integration")
            print("  8. LLM Analysis Demo")
            print("  9. AI Performance Report")
            print("\n💰 LIVE TRADING:")
            print(" 10. Optimized Live Trading")
            print(" 11. LLM-Enhanced Live Trading")
            print(" 12. Paper Trading Mode")
            print("\n📈 ANALYSIS & TOOLS:")
            print(" 13. Market Analysis")
            print(" 14. Performance Dashboard")
            print(" 15. Export Results")
            print("\n⚙️  SYSTEM:")
            print(" 16. Configuration Settings")
            print(" 17. System Diagnostics")
            print("  0. Exit")
            print("=" * 80)

            try:
                choice = input("\nSelect option (0-17): ").strip()

                if choice == "0":
                    print("\nExiting EA2060 Complete System...")
                    break
                elif choice == "1":
                    self._run_advanced_backtest()
                elif choice == "2":
                    self._run_genetic_optimization()
                elif choice == "3":
                    self._run_grid_search()
                elif choice == "4":
                    self._run_multi_strategy_comparison()
                elif choice == "5":
                    self._run_parameter_stress_test()
                elif choice == "6":
                    self._run_llm_enhanced_backtest()
                elif choice == "7":
                    self._run_nautilus_llm_integration()
                elif choice == "8":
                    self._run_llm_analysis_demo()
                elif choice == "9":
                    self._generate_ai_performance_report()
                elif choice == "10":
                    self._start_optimized_live_trading()
                elif choice == "11":
                    self._start_llm_enhanced_live_trading()
                elif choice == "12":
                    self._start_paper_trading()
                elif choice == "13":
                    self._run_market_analysis()
                elif choice == "14":
                    self._show_performance_dashboard()
                elif choice == "15":
                    self._export_results()
                elif choice == "16":
                    self._show_configuration()
                elif choice == "17":
                    self._run_system_diagnostics()
                else:
                    print("\n⚠ Invalid choice. Please select 0-17.")

                # Pausa para leitura
                if choice != "0" and sys.stdin.isatty():
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                break
            except Exception as e:
                self.logger.error(f"Error in menu selection: {e}")
                if sys.stdin.isatty():
                    input("Press Enter to continue...")

    def _run_advanced_backtest(self):
        """Executar backtest avançado"""
        print("\n" + "=" * 80)
        print("📊 ADVANCED BACKTEST WITH OPTIMIZED PARAMETERS")
        print("=" * 80)

        try:
            # Obter dados
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)  # 6 meses

            backtester = EA2060AdvancedBacktester(self.best_config)
            df = backtester.get_historical_data('XAUUSD', 'H1', start_date, end_date)

            if df is None:
                print("[-] Failed to get historical data")
                return

            print(f"[+] Data loaded: {len(df)} bars from {start_date.date()} to {end_date.date()}")

            # Executar backtest
            print("[+] Running advanced backtest...")
            metrics = backtester.run_backtest(df)

            # Exibir resultados
            self._display_backtest_results(metrics, self.best_config)

            # Salvar no cache
            self.performance_cache['advanced_backtest'] = {
                'timestamp': datetime.now(),
                'metrics': metrics,
                'config': self.best_config
            }

        except Exception as e:
            self.logger.error(f"Error in advanced backtest: {e}")

    def _run_genetic_optimization(self):
        """Executar otimização genética"""
        print("\n" + "=" * 80)
        print("🧬 GENETIC ALGORITHM OPTIMIZATION")
        print("=" * 80)

        try:
            # Configurar otimização
            population_size = 20
            generations = 10

            print(f"[+] Population size: {population_size}")
            print(f"[+] Generations: {generations}")

            # Obter dados (período menor para otimização mais rápida)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # 3 meses

            backtester = EA2060AdvancedBacktester()
            df = backtester.get_historical_data('XAUUSD', 'H1', start_date, end_date)

            if df is None:
                print("[-] Failed to get historical data")
                return

            print(f"[+] Optimization data: {len(df)} bars")

            # Executar otimização genética
            optimizer = GeneticOptimizer(population_size, generations)
            best_config, optimization_results = optimizer.optimize(df)

            # Exibir resultados
            print("\n" + "=" * 60)
            print("🏆 GENETIC OPTIMIZATION RESULTS")
            print("=" * 60)
            print(f"Best Fitness Score: {optimization_results['best_fitness']:.4f}")
            print(f"Total Return: {optimization_results['final_metrics'].get('total_return', 0):.2f}%")
            print(f"Win Rate: {optimization_results['final_metrics'].get('win_rate', 0):.1f}%")
            print(f"Max Drawdown: {optimization_results['final_metrics'].get('max_drawdown', 0):.2f}%")

            print(f"\n🎯 Optimized Parameters:")
            best_params = optimization_results['best_config']
            key_params = ['ema_fast_period', 'ema_slow_period', 'stop_loss_atr_multiplier',
                         'take_profit_atr_multiplier', 'max_risk_per_trade', 'max_positions']
            for param in key_params:
                if param in best_params:
                    print(f"  {param}: {best_params[param]}")

            # Atualizar melhor configuração
            self.best_config = BacktestConfig(**best_params)

            # Salvar resultados
            self.performance_cache['genetic_optimization'] = {
                'timestamp': datetime.now(),
                'results': optimization_results,
                'best_config': best_params
            }

            # Salvar arquivo JSON
            output_file = f"ea2060_genetic_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(optimization_results, f, indent=2, default=str)
            print(f"\n[+] Results saved to: {output_file}")

        except Exception as e:
            self.logger.error(f"Error in genetic optimization: {e}")

    def _run_grid_search(self):
        """Executar grid search optimization"""
        print("\n" + "=" * 80)
        print("🔍 GRID SEARCH OPTIMIZATION")
        print("=" * 80)

        try:
            # Parâmetros para testar
            param_ranges = {
                'ema_fast_period': [5, 6, 7],
                'ema_slow_period': [16, 18, 20],
                'stop_loss_atr_multiplier': [1.5, 2.0, 2.5],
                'take_profit_atr_multiplier': [2.5, 3.0, 3.5]
            }

            print("[+] Testing parameter combinations...")
            total_combinations = 1
            for key, values in param_ranges.items():
                total_combinations *= len(values)
                print(f"  {key}: {values}")

            print(f"[+] Total combinations: {total_combinations}")

            # Obter dados
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)  # 2 meses

            backtester = EA2060AdvancedBacktester()
            df = backtester.get_historical_data('XAUUSD', 'H1', start_date, end_date)

            if df is None:
                print("[-] Failed to get historical data")
                return

            # Executar grid search
            best_config = BacktestConfig()
            best_fitness = -float('inf')
            results = []

            for i, ema_fast in enumerate(param_ranges['ema_fast_period']):
                for j, ema_slow in enumerate(param_ranges['ema_slow_period']):
                    for k, sl_mult in enumerate(param_ranges['stop_loss_atr_multiplier']):
                        for l, tp_mult in enumerate(param_ranges['take_profit_atr_multiplier']):

                            combination_num = i * len(param_ranges['ema_slow_period']) * len(param_ranges['stop_loss_atr_multiplier']) * len(param_ranges['take_profit_atr_multiplier']) + \
                                           j * len(param_ranges['stop_loss_atr_multiplier']) * len(param_ranges['take_profit_atr_multiplier']) + \
                                           k * len(param_ranges['take_profit_atr_multiplier']) + l + 1

                            print(f"  Testing combination {combination_num}/{total_combinations}")

                            config = BacktestConfig(
                                ema_fast_period=ema_fast,
                                ema_slow_period=ema_slow,
                                stop_loss_atr_multiplier=sl_mult,
                                take_profit_atr_multiplier=tp_mult
                            )

                            test_backtester = EA2060AdvancedBacktester(config)
                            metrics = test_backtester.run_backtest(df)

                            # Calcular fitness
                            fitness = self._calculate_fitness(metrics)

                            result = {
                                'config': config,
                                'metrics': metrics,
                                'fitness': fitness,
                                'combination': combination_num
                            }
                            results.append(result)

                            if fitness > best_fitness:
                                best_fitness = fitness
                                best_config = config

            # Exibir melhores resultados
            print("\n" + "=" * 60)
            print("🏆 GRID SEARCH RESULTS")
            print("=" * 60)
            print(f"Best Fitness: {best_fitness:.4f}")

            best_metrics = None
            for result in results:
                if result['fitness'] == best_fitness:
                    best_metrics = result['metrics']
                    break

            if best_metrics:
                self._display_backtest_results(best_metrics, best_config)

            # Salvar resultados
            self.performance_cache['grid_search'] = {
                'timestamp': datetime.now(),
                'best_config': best_config,
                'best_fitness': best_fitness,
                'total_combinations': total_combinations,
                'all_results': results[:10]  # Top 10
            }

        except Exception as e:
            self.logger.error(f"Error in grid search: {e}")

    def _run_multi_strategy_comparison(self):
        """Comparação multi-estratégia"""
        print("\n" + "=" * 80)
        print("📊 MULTI-STRATEGY COMPARISON")
        print("=" * 80)

        try:
            strategies = {
                'Conservative': BacktestConfig(
                    max_risk_per_trade=0.01,
                    max_positions=2,
                    stop_loss_atr_multiplier=2.5,
                    take_profit_atr_multiplier=2.5
                ),
                'Balanced': BacktestConfig(
                    max_risk_per_trade=0.02,
                    max_positions=3,
                    stop_loss_atr_multiplier=2.0,
                    take_profit_atr_multiplier=3.0
                ),
                'Aggressive': BacktestConfig(
                    max_risk_per_trade=0.03,
                    max_positions=5,
                    stop_loss_atr_multiplier=1.5,
                    take_profit_atr_multiplier=4.0
                )
            }

            # Obter dados
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

            backtester = EA2060AdvancedBacktester()
            df = backtester.get_historical_data('XAUUSD', 'H1', start_date, end_date)

            if df is None:
                print("[-] Failed to get historical data")
                return

            results = {}

            for name, config in strategies.items():
                print(f"\n[+] Testing {name} strategy...")
                test_backtester = EA2060AdvancedBacktester(config)
                metrics = test_backtester.run_backtest(df)
                results[name] = {
                    'config': config,
                    'metrics': metrics
                }

            # Comparação
            print("\n" + "=" * 80)
            print("📈 STRATEGY COMPARISON")
            print("=" * 80)
            print(f"{'Strategy':<12} {'Return':<8} {'Win Rate':<9} {'Max DD':<8} {'Sharpe':<7} {'Trades':<7}")
            print("-" * 80)

            for name, result in results.items():
                metrics = result['metrics']
                print(f"{name:<12} {metrics.get('total_return', 0):<8.1f}% "
                      f"{metrics.get('win_rate', 0):<9.1f}% "
                      f"{metrics.get('max_drawdown', 0):<8.1f}% "
                      f"{metrics.get('sharpe_ratio', 0):<7.2f} "
                      f"{metrics.get('total_trades', 0):<7}")

            # Salvar comparação
            self.performance_cache['multi_strategy'] = {
                'timestamp': datetime.now(),
                'results': results
            }

        except Exception as e:
            self.logger.error(f"Error in multi-strategy comparison: {e}")

    def _run_parameter_stress_test(self):
        """Teste de stress de parâmetros"""
        print("\n" + "=" * 80)
        print("🔬 PARAMETER STRESS TEST")
        print("=" * 80)

        try:
            # Parâmetros para stress test
            stress_configs = {
                'High_Risk': BacktestConfig(max_risk_per_trade=0.05, max_positions=10),
                'Low_Risk': BacktestConfig(max_risk_per_trade=0.005, max_positions=1),
                'Tight_SL': BacktestConfig(stop_loss_atr_multiplier=1.0, take_profit_atr_multiplier=2.0),
                'Wide_SL': BacktestConfig(stop_loss_atr_multiplier=4.0, take_profit_atr_multiplier=6.0),
                'High_Frequency': BacktestConfig(max_positions=10, max_risk_per_trade=0.01),
                'Low_Frequency': BacktestConfig(max_positions=1, max_risk_per_trade=0.03)
            }

            # Obter dados
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

            backtester = EA2060AdvancedBacktester()
            df = backtester.get_historical_data('XAUUSD', 'H1', start_date, end_date)

            if df is None:
                print("[-] Failed to get historical data")
                return

            stress_results = {}

            for name, config in stress_configs.items():
                print(f"[+] Stress testing: {name}")
                test_backtester = EA2060AdvancedBacktester(config)
                metrics = test_backtester.run_backtest(df)
                stress_results[name] = metrics

                # Verificar se o sistema quebrou
                if metrics.get('max_drawdown', 0) > 50:
                    print(f"  ⚠️ High risk detected: {metrics['max_drawdown']:.1f}% drawdown")
                if metrics.get('total_trades', 0) < 5:
                    print(f"  ⚠️ Low activity: Only {metrics['total_trades']} trades")

            # Análise de stress
            print("\n" + "=" * 60)
            print("🔥 STRESS TEST ANALYSIS")
            print("=" * 60)

            safe_configs = []
            risky_configs = []

            for name, metrics in stress_results.items():
                if (metrics.get('max_drawdown', 100) < 25 and
                    metrics.get('total_trades', 0) >= 10 and
                    metrics.get('sharpe_ratio', -999) > 0.5):
                    safe_configs.append(name)
                else:
                    risky_configs.append(name)

            print(f"✅ Stable Configurations: {', '.join(safe_configs) if safe_configs else 'None'}")
            print(f"⚠️ Risky Configurations: {', '.join(risky_configs) if risky_configs else 'None'}")

            # Salvar resultados
            self.performance_cache['stress_test'] = {
                'timestamp': datetime.now(),
                'results': stress_results,
                'safe_configs': safe_configs,
                'risky_configs': risky_configs
            }

        except Exception as e:
            self.logger.error(f"Error in parameter stress test: {e}")

    def _run_llm_enhanced_backtest(self):
        """Executar backtest com LLM"""
        print("\n" + "=" * 80)
        print("🤖 LLM-ENHANCED BACKTEST")
        print("=" * 80)

        try:
            if not self.system_status['llm_enabled']:
                print("[-] LLM components not available")
                return

            # Usar trader LLM aprimorado
            trader = EA2060LLMTrader()

            if not trader.initialize_mt5():
                print("[-] Failed to initialize MT5")
                return

            print("[+] LLM-Enhanced Trader initialized")

            # Obter dados e executar backtest
            df = trader.get_historical_data('XAUUSD', trader.timeframe, 500)

            if df is None:
                print("[-] Failed to get historical data")
                return

            print(f"[+] Data loaded: {len(df)} bars")

            # Simular trading com LLM
            print("[+] Running LLM-enhanced backtest simulation...")
            trades = []
            balance = 10000.0

            for i in range(50, len(df)):
                current_data = df.iloc[:i+1]
                latest = current_data.iloc[-1]

                # Análise LLM
                llm_analysis = trader.analyze_with_llm(current_data)

                if llm_analysis and llm_analysis['confidence'] > 0.7:
                    if llm_analysis['action'] in ['BUY', 'SELL']:
                        # Simular trade
                        trade_result = {
                            'time': latest.name,
                            'action': llm_analysis['action'],
                            'price': latest['close'],
                            'confidence': llm_analysis['confidence'],
                            'reasoning': llm_analysis['reasoning'],
                            'signal_strength': llm_analysis.get('signal_strength', 0)
                        }
                        trades.append(trade_result)

            # Análise dos resultados LLM
            print(f"\n[+] LLM Analysis Results:")
            print(f"  Total LLM signals: {len(trades)}")
            print(f"  Buy signals: {len([t for t in trades if t['action'] == 'BUY'])}")
            print(f"  Sell signals: {len([t for t in trades if t['action'] == 'SELL'])}")
            print(f"  Average confidence: {np.mean([t['confidence'] for t in trades]):.2f}")
            print(f"  Average signal strength: {np.mean([t['signal_strength'] for t in trades]):.2f}")

            # Exibir exemplos
            print(f"\n[+] Recent LLM Signals:")
            for trade in trades[-5:]:
                print(f"  {trade['time'].strftime('%H:%M')} - {trade['action']} "
                      f"(conf: {trade['confidence']:.2f}) - {trade['reasoning'][:50]}...")

            # Salvar resultados
            self.performance_cache['llm_backtest'] = {
                'timestamp': datetime.now(),
                'trades': trades,
                'total_signals': len(trades)
            }

        except Exception as e:
            self.logger.error(f"Error in LLM-enhanced backtest: {e}")

    def _run_nautilus_llm_integration(self):
        """Executar integração Nautilus + LLM"""
        print("\n" + "=" * 80)
        print("🚀 NAUTILUS + LLM INTEGRATION")
        print("=" * 80)

        try:
            if not self.system_status['nautilus_available']:
                print("[-] Nautilus Trader not available")
                print("[+] Running simulation mode instead...")

            # Inicializar runner
            runner = EA2060NautilusLLMRunner()

            # Executar backtest
            print("[+] Running Nautilus + LLM backtest...")
            results = runner.run_backtest()

            if results:
                print("\n[+] Nautilus + LLM Results:")
                for key, value in results.items():
                    print(f"  {key}: {value}")

                # Salvar resultados
                self.performance_cache['nautilus_llm'] = {
                    'timestamp': datetime.now(),
                    'results': results
                }
            else:
                print("[-] No results available")

        except Exception as e:
            self.logger.error(f"Error in Nautilus + LLM integration: {e}")

    def _run_llm_analysis_demo(self):
        """Demo de análise LLM"""
        print("\n" + "=" * 80)
        print("🧠 LLM ANALYSIS DEMONSTRATION")
        print("=" * 80)

        try:
            if not self.system_status['llm_enabled']:
                print("[-] LLM components not available")
                return

            # Criar estratégia LLM
            strategy = EA2060NautilusLLMStrategy()

            # Gerar dados de teste
            print("[+] Generating test data...")
            df = strategy._generate_simulation_data()

            if df is None:
                print("[-] Failed to generate test data")
                return

            # Calcular indicadores
            df_indicators = strategy.backtester.calculate_indicators(df)
            latest = df_indicators.iloc[-1]

            print(f"[+] Current market data:")
            print(f"  Price: ${latest['close']:.2f}")
            print(f"  EMA Fast/Slow: ${latest['ema_fast']:.2f} / ${latest['ema_slow']:.2f}")
            print(f"  SuperTrend: ${latest['supertrend']:.2f}")
            print(f"  RSI: {latest['rsi']:.1f}")
            print(f"  Volume Ratio: {latest['volume_ratio']:.2f}")

            # Executar análise LLM
            print("\n[+] Running LLM analysis...")
            signal = strategy._analyze_with_llm(latest, df_indicators)

            # Exibir resultado
            print("\n" + "=" * 60)
            print("🎯 LLM ANALYSIS RESULT")
            print("=" * 60)
            print(f"Action: {signal['action']}")
            print(f"Confidence: {signal['confidence']:.2f}")
            print(f"Score: {signal['score']:.2f}")
            print(f"Reasoning: {signal['reasoning']}")

            if 'technical_analysis' in signal:
                tech = signal['technical_analysis']
                print(f"\nTechnical Analysis:")
                print(f"  Recommendation: {tech.get('recommendation', 'N/A')}")
                print(f"  Confidence: {tech.get('confidence', 0):.2f}")
                print(f"  Signals: {', '.join(tech.get('signals', []))}")

            if 'llm_analysis' in signal:
                llm = signal['llm_analysis']
                print(f"\nLLM Analysis:")
                print(f"  Sentiment: {llm.get('sentiment', 'N/A')}")
                print(f"  Risk: {llm.get('risk', 'N/A')}")
                print(f"  Simulated: {llm.get('simulated', False)}")

            print("=" * 60)

        except Exception as e:
            self.logger.error(f"Error in LLM analysis demo: {e}")

    def _generate_ai_performance_report(self):
        """Gerar relatório de performance AI"""
        print("\n" + "=" * 80)
        print("📊 AI PERFORMANCE REPORT")
        print("=" * 80)

        try:
            report = {
                'generated_at': datetime.now(),
                'system_status': self.system_status,
                'cache_summary': {}
            }

            # Analisar cache de performance
            for key, data in self.performance_cache.items():
                if isinstance(data, dict) and 'timestamp' in data:
                    report['cache_summary'][key] = {
                        'last_run': data['timestamp'],
                        'available': True
                    }
                else:
                    report['cache_summary'][key] = {'available': False}

            # Comparar performance das diferentes estratégias
            print("\n[+] Performance Summary:")
            for key, summary in report['cache_summary'].items():
                status = "[+]" if summary['available'] else "[-]"
                print(f"  {status} {key.replace('_', ' ').title()}")

            # Se tiver resultados de backtest, mostrar comparação
            if 'advanced_backtest' in self.performance_cache:
                adv = self.performance_cache['advanced_backtest']
                print(f"\n[+] Advanced Backtest Performance:")
                print(f"  Total Return: {adv['metrics'].get('total_return', 0):.2f}%")
                print(f"  Win Rate: {adv['metrics'].get('win_rate', 0):.1f}%")
                print(f"  Sharpe Ratio: {adv['metrics'].get('sharpe_ratio', 0):.2f}")

            if 'genetic_optimization' in self.performance_cache:
                gen = self.performance_cache['genetic_optimization']
                print(f"\n[+] Genetic Optimization Results:")
                print(f"  Best Fitness: {gen['results']['best_fitness']:.4f}")
                print(f"  Return: {gen['results']['final_metrics'].get('total_return', 0):.2f}%")

            # Salvar relatório
            report_file = f"ea2060_ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"\n[+] AI Performance Report saved to: {report_file}")

        except Exception as e:
            self.logger.error(f"Error generating AI performance report: {e}")

    def _start_optimized_live_trading(self):
        """Iniciar trading otimizado ao vivo"""
        print("\n" + "=" * 80)
        print("💰 OPTIMIZED LIVE TRADING")
        print("=" * 80)

        try:
            if not self.system_status['mt5_connected']:
                print("[-] MT5 not connected. Cannot start live trading.")
                return

            print("[+] Starting optimized EA2060 trader...")
            trader = EA2060OptimizedTrader()

            if trader.initialize_mt5():
                print("[+] MT5 initialized successfully")
                print("[+] Trading with optimized parameters:")
                print(f"  EMA Fast/Slow: {self.best_config.ema_fast_period}/{self.best_config.ema_slow_period}")
                print(f"  Risk per trade: {self.best_config.max_risk_per_trade * 100:.1f}%")
                print(f"  Max positions: {self.best_config.max_positions}")
                print(f"  SL/TP: {self.best_config.stop_loss_atr_multiplier:.1f}x/{self.best_config.take_profit_atr_multiplier:.1f}x ATR")
                print("\n[+] Press Ctrl+C to stop trading")

                # Iniciar trading
                trader.run()

            else:
                print("[-] Failed to initialize MT5")

        except Exception as e:
            self.logger.error(f"Error in optimized live trading: {e}")

    def _start_llm_enhanced_live_trading(self):
        """Iniciar trading LLM ao vivo"""
        print("\n" + "=" * 80)
        print("🤖 LLM-ENHANCED LIVE TRADING")
        print("=" * 80)

        try:
            if not self.system_status['mt5_connected']:
                print("[-] MT5 not connected. Cannot start live trading.")
                return

            if not self.system_status['llm_enabled']:
                print("[-] LLM components not available")
                return

            print("[+] Starting LLM-enhanced trader...")
            trader = EA2060LLMTrader()

            if trader.initialize_mt5():
                print("[+] MT5 initialized successfully")
                print("[+] LLM analysis enabled")
                print("[+] AI-powered decision making active")
                print("\n[+] Press Ctrl+C to stop trading")

                # Iniciar trading
                trader.run()

            else:
                print("[-] Failed to initialize MT5")

        except Exception as e:
            self.logger.error(f"Error in LLM-enhanced live trading: {e}")

    def _start_paper_trading(self):
        """Iniciar paper trading"""
        print("\n" + "=" * 80)
        print("📝 PAPER TRADING MODE")
        print("=" * 80)

        try:
            print("[+] Starting paper trading simulation...")
            print("[+] All trades will be simulated (no real money)")

            # Simular paper trading por 1 hora
            start_time = datetime.now()
            duration_minutes = 60

            while True:
                elapsed = (datetime.now() - start_time).total_seconds() / 60
                if elapsed >= duration_minutes:
                    print(f"\n[+] Paper trading completed ({duration_minutes} minutes)")
                    break

                # Simular análise de mercado
                current_time = datetime.now()
                print(f"\r[{current_time.strftime('%H:%M:%S')}] Analyzing market... {elapsed:.0f}/{duration_minutes} min", end="")

                # Simular sinal
                import random
                if random.random() > 0.8:  # 20% chance de sinal
                    signal = random.choice(['BUY', 'SELL'])
                    confidence = random.uniform(0.6, 0.9)
                    print(f"\n[+] Paper signal: {signal} (confidence: {confidence:.2f})")

                time.sleep(60)  # Verificar a cada minuto

        except KeyboardInterrupt:
            print("\n[+] Paper trading stopped by user")
        except Exception as e:
            self.logger.error(f"Error in paper trading: {e}")

    def _run_market_analysis(self):
        """Executar análise de mercado"""
        print("\n" + "=" * 80)
        print("📈 MARKET ANALYSIS")
        print("=" * 80)

        try:
            if not self.system_status['mt5_connected']:
                print("[-] MT5 not connected for real-time analysis")
                return

            # Inicializar MT5
            if not mt5.initialize():
                print("[-] Failed to initialize MT5")
                return

            # Obter dados recentes
            rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H1, 0, 100)
            mt5.shutdown()

            if rates is None:
                print("[-] Failed to get market data")
                return

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            df.rename(columns={'tick_volume': 'volume'}, inplace=True)

            # Análise técnica
            print(f"[+] Market Analysis for XAUUSD")
            print(f"[+] Data: {len(df)} bars (last {df.index[0]} to {df.index[-1]})")
            print(f"[+] Current Price: ${df['close'].iloc[-1]:.2f}")

            # Estatísticas básicas
            print(f"\n[+] Price Statistics:")
            print(f"  High: ${df['high'].max():.2f}")
            print(f"  Low: ${df['low'].min():.2f}")
            print(f"  Average: ${df['close'].mean():.2f}")
            print(f"  Volatility: {df['close'].pct_change().std() * 100:.2f}%")

            # Tendência
            recent_prices = df['close'].tail(20)
            trend = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
            trend_direction = "UP" if trend > 0 else "DOWN"
            print(f"\n[+] Short-term Trend: {trend_direction} ({trend:.4f})")

            # Volume
            avg_volume = df['volume'].mean()
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume
            print(f"[+] Volume Analysis:")
            print(f"  Current: {current_volume:.0f}")
            print(f"  Average: {avg_volume:.0f}")
            print(f"  Ratio: {volume_ratio:.2f}")

            # Indicadores técnicos básicos
            df['ema_20'] = df['close'].ewm(span=20).mean()
            df['rsi'] = self._calculate_rsi(df['close'])

            latest = df.iloc[-1]
            print(f"\n[+] Technical Indicators:")
            print(f"  EMA 20: ${latest['ema_20']:.2f}")
            print(f"  RSI: {latest['rsi']:.1f}")
            print(f"  Price vs EMA: {'ABOVE' if latest['close'] > latest['ema_20'] else 'BELOW'}")
            print(f"  RSI Status: {'OVERBOUGHT' if latest['rsi'] > 70 else 'OVERSOLD' if latest['rsi'] < 30 else 'NEUTRAL'}")

        except Exception as e:
            self.logger.error(f"Error in market analysis: {e}")

    def _calculate_rsi(self, prices, period=14):
        """Calcular RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _show_performance_dashboard(self):
        """Mostrar dashboard de performance"""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE DASHBOARD")
        print("=" * 80)

        try:
            if not self.performance_cache:
                print("[-] No performance data available")
                print("[+] Run backtests first to generate performance data")
                return

            print("[+] Performance Summary:")
            print("-" * 80)

            # Mostrar resumo de todos os testes
            for test_name, data in self.performance_cache.items():
                print(f"\n📈 {test_name.replace('_', ' ').title()}:")
                print(f"  Last Run: {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

                if 'metrics' in data:
                    metrics = data['metrics']
                    print(f"  Total Return: {metrics.get('total_return', 0):.2f}%")
                    print(f"  Win Rate: {metrics.get('win_rate', 0):.1f}%")
                    print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
                    print(f"  Total Trades: {metrics.get('total_trades', 0)}")

                elif 'results' in data:
                    results = data['results']
                    if isinstance(results, dict) and 'total_trades' in results:
                        print(f"  Total Trades: {results.get('total_trades', 0)}")
                        print(f"  Win Rate: {results.get('win_rate', 0):.1f}%")
                        print(f"  Total Return: {results.get('total_return', 0):.2f}%")

                elif 'total_signals' in data:
                    print(f"  LLM Signals Generated: {data['total_signals']}")

            # Se tiver múltiplos resultados, comparar
            if len(self.performance_cache) > 1:
                print(f"\n[+] Best Performing Strategy:")
                best_return = -float('inf')
                best_strategy = ""

                for test_name, data in self.performance_cache.items():
                    if 'metrics' in data:
                        return_pct = data['metrics'].get('total_return', -999)
                        if return_pct > best_return:
                            best_return = return_pct
                            best_strategy = test_name

                if best_strategy:
                    print(f"  Strategy: {best_strategy.replace('_', ' ').title()}")
                    print(f"  Return: {best_return:.2f}%")

        except Exception as e:
            self.logger.error(f"Error showing performance dashboard: {e}")

    def _export_results(self):
        """Exportar resultados"""
        print("\n" + "=" * 80)
        print("💾 EXPORT RESULTS")
        print("=" * 80)

        try:
            if not self.performance_cache:
                print("[-] No data to export")
                return

            # Criar arquivo de exportação
            export_data = {
                'export_timestamp': datetime.now(),
                'system_status': self.system_status,
                'best_config': self.best_config.__dict__,
                'performance_data': self.performance_cache
            }

            # Exportar JSON
            json_file = f"ea2060_complete_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"[+] Results exported to: {json_file}")

            # Exportar CSV se tiver dados de backtest
            if 'advanced_backtest' in self.performance_cache:
                csv_file = f"ea2060_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

                # Criar DataFrame com resultados
                results_list = []
                for test_name, data in self.performance_cache.items():
                    if 'metrics' in data:
                        row = {'test': test_name}
                        row.update(data['metrics'])
                        results_list.append(row)

                if results_list:
                    df_results = pd.DataFrame(results_list)
                    df_results.to_csv(csv_file, index=False)
                    print(f"[+] Backtest results exported to: {csv_file}")

            print(f"\n[+] Export completed successfully")

        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")

    def _show_configuration(self):
        """Mostrar configurações"""
        print("\n" + "=" * 80)
        print("⚙️ CONFIGURATION SETTINGS")
        print("=" * 80)

        try:
            print(f"\n[+] Current Optimized Configuration:")
            print(f"  EMA Fast Period: {self.best_config.ema_fast_period}")
            print(f"  EMA Slow Period: {self.best_config.ema_slow_period}")
            print(f"  SuperTrend Period: {self.best_config.supertrend_period}")
            print(f"  SuperTrend Multiplier: {self.best_config.supertrend_multiplier}")
            print(f"  ADX Threshold: {self.best_config.adx_threshold}")
            print(f"  RSI Period: {self.best_config.rsi_period}")
            print(f"  RSI Oversold: {self.best_config.rsi_oversold}")
            print(f"  RSI Overbought: {self.best_config.rsi_overbought}")

            print(f"\n[+] Risk Management:")
            print(f"  Stop Loss ATR Multiplier: {self.best_config.stop_loss_atr_multiplier}")
            print(f"  Take Profit ATR Multiplier: {self.best_config.take_profit_atr_multiplier}")
            print(f"  Max Risk per Trade: {self.best_config.max_risk_per_trade * 100:.1f}%")
            print(f"  Max Positions: {self.best_config.max_positions}")
            print(f"  Trailing Stop Activation: {self.best_config.trailing_stop_activation}")
            print(f"  Trailing Stop Distance: {self.best_config.trailing_stop_distance}")

            print(f"\n[+] Market Filters:")
            print(f"  Min Volume Ratio: {self.best_config.min_volume_ratio}")
            print(f"  Max Spread Points: {self.best_config.max_spread_points}")
            print(f"  Min Volatility: {self.best_config.min_volatility}")
            print(f"  Trading Hours Only: {self.best_config.trading_hours_only}")
            print(f"  Avoid Friday Close: {self.best_config.avoid_friday_close}")

            print(f"\n[+] Backtest Settings:")
            print(f"  Initial Balance: ${self.best_config.initial_balance:,.2f}")
            print(f"  Commission per Lot: ${self.best_config.commission_per_lot}")
            print(f"  Spread Points: {self.best_config.spread_points}")
            print(f"  Slippage Points: {self.best_config.slippage_points}")

            print(f"\n[+] To modify parameters:")
            print(f"  1. Run genetic optimization (option 2)")
            print(f"  2. Run grid search (option 3)")
            print(f"  3. Edit BacktestConfig directly in code")

        except Exception as e:
            self.logger.error(f"Error showing configuration: {e}")

    def _run_system_diagnostics(self):
        """Executar diagnósticos do sistema"""
        print("\n" + "=" * 80)
        print("🔧 SYSTEM DIAGNOSTICS")
        print("=" * 80)

        try:
            print(f"[+] Testing system components...")

            # Testar MT5
            print(f"\n[+] Testing MT5 Connection...")
            if mt5.initialize():
                account = mt5.account_info()
                print(f"  [+] Connected - Account: {account.login}")
                print(f"  [+] Balance: ${account.balance:.2f}")
                print(f"  [+] Server: {account.server}")
                mt5.shutdown()
            else:
                print(f"  [-] Connection failed")

            # Testar módulos
            modules_to_test = [
                ('pandas', 'pandas'),
                ('numpy', 'numpy'),
                ('MetaTrader5', 'MetaTrader5'),
                ('pandas_ta', 'pandas_ta'),
                ('nautilus_trader', 'nautilus_trader'),
                ('sklearn', 'sklearn')
            ]

            print(f"\n[+] Testing Python Modules:")
            for name, module in modules_to_test:
                try:
                    __import__(module)
                    print(f"  [+] {name}")
                except ImportError:
                    print(f"  [-] {name} (not installed)")

            # Testar arquivos do sistema
            required_files = [
                'ea2060_advanced_backtest.py',
                'ea2060_nautilus_llm_strategy.py',
                'ea2060_optimized_trader.py',
                'ea2060_llm_enhanced.py'
            ]

            print(f"\n[+] Testing System Files:")
            for file in required_files:
                if os.path.exists(file):
                    print(f"  [+] {file}")
                else:
                    print(f"  [-] {file} (missing)")

            # Testar desempenho
            print(f"\n[+] Testing Performance...")
            start_time = time.time()
            test_data = pd.DataFrame(np.random.randn(1000, 5), columns=['open', 'high', 'low', 'close', 'volume'])
            calculation_time = time.time() - start_time
            print(f"  [+] Data processing: {calculation_time:.4f} seconds")

            # Memória
            import psutil
            memory_usage = psutil.virtual_memory().percent
            print(f"  [+] Memory usage: {memory_usage:.1f}%")

            print(f"\n[+] Diagnostics completed")

        except Exception as e:
            self.logger.error(f"Error running system diagnostics: {e}")

    def _display_backtest_results(self, metrics: Dict, config: BacktestConfig):
        """Exibir resultados de backtest"""
        print("\n" + "=" * 80)
        print("📈 BACKTEST RESULTS")
        print("=" * 80)

        if not metrics:
            print("[-] No results available")
            return

        print(f"📊 Performance Metrics:")
        print(f"  Total Trades: {metrics.get('total_trades', 0)}")
        print(f"  Winning Trades: {metrics.get('winning_trades', 0)}")
        print(f"  Losing Trades: {metrics.get('losing_trades', 0)}")
        print(f"  Win Rate: {metrics.get('win_rate', 0):.2f}%")
        print(f"  Total PnL: ${metrics.get('total_pnl', 0):.2f}")
        print(f"  Total Return: {metrics.get('total_return', 0):.2f}%")
        print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        print(f"  Average Trade Duration: {metrics.get('avg_trade_duration', 0):.0f} minutes")
        print(f"  Final Balance: ${metrics.get('final_balance', 0):.2f}")

        if 'exit_reasons' in metrics:
            print(f"\n📋 Exit Reasons:")
            for reason, count in metrics['exit_reasons'].items():
                print(f"  {reason}: {count}")

        print(f"\n⚙️ Strategy Parameters:")
        print(f"  EMA Fast/Slow: {config.ema_fast_period}/{config.ema_slow_period}")
        print(f"  SuperTrend: {config.supertrend_period} ({config.supertrend_multiplier}x)")
        print(f"  ADX Threshold: {config.adx_threshold}")
        print(f"  Risk per Trade: {config.max_risk_per_trade * 100:.1f}%")
        print(f"  Max Positions: {config.max_positions}")
        print(f"  SL/TP Multipliers: {config.stop_loss_atr_multiplier}x/{config.take_profit_atr_multiplier}x")

        print("=" * 80)

    def _calculate_fitness(self, metrics: Dict) -> float:
        """Calcular fitness para otimização"""
        if not metrics or metrics.get('total_trades', 0) < 10:
            return -1000.0

        total_return = metrics.get('total_return', 0)
        max_drawdown = max(metrics.get('max_drawdown', 100), 0.1)
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        win_rate = metrics.get('win_rate', 0)

        return total_return - max_drawdown + (win_rate * 0.1) + (sharpe_ratio * 5)

def main():
    """Função principal"""
    print("=" * 80)
    print("🚀 EA2060 COMPLETE TRADING SYSTEM")
    print("Advanced Backtest, Optimization & LLM-Enhanced Trading")
    print("=" * 80)

    try:
        # Inicializar sistema
        system = EA2060CompleteSystem()

        # Exibir menu principal
        system.show_main_menu()

    except KeyboardInterrupt:
        print("\n\nEA2060 System terminated by user.")
    except Exception as e:
        logger.error(f"System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()