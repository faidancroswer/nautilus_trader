#!/usr/bin/env python3
"""
EA2060 Nautilus Trader + LLM Runner
Script para executar o EA2060 com Nautilus Trader e integração LLM
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar diretório atual ao PATH
sys.path.append(str(Path(__file__).parent))

from nautilus_trader.config import BacktestRunConfig, BacktestVenueConfig, BacktestDataConfig, BacktestEngineConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Symbol, Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.external.core import process_files, process_csv_file
from nautilus_trader.persistence.external.readers import CSVReader, ParquetReader, FeatherReader
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.backtest.modules import BacktestDataConfig, BacktestVenueConfig, BacktestRunConfig

from ea2060_nautilus_integration import EA2060LLMStrategy

import pandas as pd
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_data():
    """Criar dados de exemplo para backtest"""
    try:
        # Importar MT5 para obter dados reais
        import MetaTrader5 as mt5

        if mt5.initialize():
            # Obter dados do XAUUSD
            rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H1, 0, 1000)
            mt5.shutdown()

            if rates is not None:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                df = df.rename(columns={
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'tick_volume': 'volume',
                    'spread': 'spread'
                })

                # Salvar dados para backtest
                data_dir = Path("data")
                data_dir.mkdir(exist_ok=True)

                # Salvar como CSV
                csv_path = data_dir / "XAUUSD_H1.csv"
                df.to_csv(csv_path)
                logger.info(f"Sample data saved to {csv_path}")
                logger.info(f"Data range: {df.index[0]} to {df.index[-1]}")
                logger.info(f"Total bars: {len(df)}")

                return str(csv_path)

        logger.error("Failed to get MT5 data, creating synthetic data...")

        # Criar dados sintéticos se MT5 falhar
        dates = pd.date_range('2024-01-01', periods=1000, freq='H')
        np.random.seed(42)

        base_price = 4000
        prices = []
        current_price = base_price

        for _ in range(1000):
            change = np.random.normal(0, 0.002)  # 0.2% volatilidade
            current_price *= (1 + change)
            prices.append(current_price)

        df = pd.DataFrame({
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.001))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.001))) for p in prices],
            'close': prices,
            'volume': np.random.randint(5000, 20000, 1000),
            'spread': np.random.randint(10, 50, 1000)
        }, index=dates)

        # Salvar dados
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        csv_path = data_dir / "XAUUSD_H1_synthetic.csv"
        df.to_csv(csv_path)

        logger.info(f"Synthetic data saved to {csv_path}")
        return str(csv_path)

    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return None

def run_nautilus_backtest():
    """Executar backtest com Nautilus Trader"""
    try:
        logger.info("Creating EA2060 strategy with LLM integration...")

        # Criar estratégia
        strategy = EA2060LLMStrategy()

        # Criar dados de exemplo
        data_path = create_sample_data()

        if data_path is None:
            logger.error("Failed to create data")
            return

        # Configurar dados
        data_config = BacktestDataConfig(
            catalog_path=str(Path("data").resolve()),
            catalog_fs_protocol="file",
        )

        # Configurar venue (simulada)
        venue_config = BacktestVenueConfig(
            name="SIMULATED",
            oms_type=OmsType.HEDGING,
            account_type=AccountType.CASH,
            base_currency=USD,
            starting_balances=[Money(10_000, USD)],
            fill_mode="instant",  # Preenchimento instantâneo para backtest
        )

        # Configurar engine
        engine_config = BacktestEngineConfig(
            trader_id="EA2060_LLM_BACKTEST",
            log_level="INFO",
            debug=False,
        )

        # Configurar run
        run_config = BacktestRunConfig(
            engine=engine_config,
            data=data_config,
            venues=[venue_config],
            strategies=[strategy],
            # Aqui você adicionaria os dados específicos
        )

        logger.info("Backtest configuration completed")
        logger.info("Note: Full Nautilus integration requires additional setup")
        logger.info("Current implementation demonstrates LLM integration concept")

        # Mostrar configuração
        print("\\n" + "="*80)
        print("EA2060 + Nautilus Trader + LLM Configuration")
        print("="*80)
        print(f"Strategy: EA2060LLMStrategy")
        print(f"Venue: {venue_config.name}")
        print(f"Initial Balance: $10,000")
        print(f"Data Path: {data_config.catalog_path}")
        print(f"LLM Integration: Simulated (can be replaced with real LLM API)")
        print("="*80)

        return True

    except Exception as e:
        logger.error(f"Error in Nautilus backtest: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_live_with_llm():
    """Executar em modo live com LLM"""
    try:
        logger.info("Starting EA2060 with LLM integration...")

        # Usar implementação direta com LLM
        from ea2060_nautilus_integration import EA2060NautilusRunner

        runner = EA2060NautilusRunner()
        runner.run_live()

    except Exception as e:
        logger.error(f"Error in live run: {e}")
        import traceback
        traceback.print_exc()

def demo_llm_analysis():
    """Demo de análise LLM"""
    try:
        logger.info("Running LLM Analysis Demo...")

        from ea2060_nautilus_integration import EA2060LLMStrategy

        strategy = EA2060LLMStrategy()

        # Criar dados de teste
        sample_data = pd.Series({
            'close': 4025.50,
            'ema_fast': 4018.30,
            'ema_slow': 3995.20,
            'supertrend': 4005.10,
            'rsi': 58.5,
            'volume_ratio': 1.35,
            'volatility': 0.0028,
            'bb_upper': 4035.60,
            'bb_lower': 3995.40,
            'atr': 28.5
        })

        sample_df = pd.DataFrame({
            'close': [4025.50] * 50,
            'ema_fast': [4018.30] * 50,
            'ema_slow': [3995.20] * 50,
            'supertrend': [4005.10] * 50,
            'rsi': [58.5] * 50,
            'volume_ratio': [1.35] * 50,
            'volatility': [0.0028] * 50,
            'bb_upper': [4035.60] * 50,
            'bb_lower': [3995.40] * 50,
            'atr': [28.5] * 50
        })

        # Executar análise LLM
        result = strategy._analyze_with_llm(sample_data, sample_df)

        print("\\n" + "="*80)
        print("LLM Analysis Results")
        print("="*80)
        print(f"Market Data Summary:")
        print(f"  Current Price: ${sample_data['close']:.2f}")
        print(f"  EMA Fast/Slow: ${sample_data['ema_fast']:.2f} / ${sample_data['ema_slow']:.2f}")
        print(f"  SuperTrend: ${sample_data['supertrend']:.2f}")
        print(f"  RSI: {sample_data['rsi']:.1f}")
        print(f"  Volume Ratio: {sample_data['volume_ratio']:.2f}")
        print(f"  Volatility: {sample_data['volatility']:.4f}")
        print(f"\\nLLM Decision:")
        print(f"  Action: {result['action']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Score: {result['score']:.2f}")
        print(f"  Reasoning: {result['reasoning']}")
        print("="*80)

        return result

    except Exception as e:
        logger.error(f"Error in LLM demo: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Função principal"""
    print("="*80)
    print("EA2060 + Nautilus Trader + LLM Integration Runner")
    print("="*80)
    print("Select execution mode:")
    print()
    print("1. Nautilus Backtest Configuration")
    print("2. Live Trading with LLM")
    print("3. LLM Analysis Demo")
    print("4. Run optimized EA2060 (standard)")
    print()

    try:
        choice = input("Enter choice (1-4): ").strip()

        if choice == "1":
            print("\\nConfiguring Nautilus backtest...")
            success = run_nautilus_backtest()
            if success:
                print("\\n✓ Backtest configuration completed!")
                print("Note: To run actual backtest, use nautilus_trader.backtest.engine")
            else:
                print("\\n✗ Backtest configuration failed")

        elif choice == "2":
            print("\\nStarting live trading with LLM...")
            run_live_with_llm()

        elif choice == "3":
            print("\\nRunning LLM analysis demo...")
            demo_llm_analysis()

        elif choice == "4":
            print("\\nRunning standard optimized EA2060...")
            from ea2060_optimized_trader import EA2060OptimizedTrader

            trader = EA2060OptimizedTrader()
            if trader.initialize_mt5():
                print("✓ MT5 initialized successfully")
                print("Starting trading bot...")
                trader.run()
            else:
                print("✗ Failed to initialize MT5")

        else:
            print("\\nInvalid choice. Please select 1-4.")

    except KeyboardInterrupt:
        print("\\n\\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\\nError: {e}")

if __name__ == "__main__":
    main()