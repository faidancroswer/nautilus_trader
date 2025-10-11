#!/usr/bin/env python3
"""
Main launcher for AI Trading with Performance Optimizer
Complete system with automated performance optimization
"""

import sys
import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_trading_main.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print startup banner"""
    banner = """
    ================================================================
               AI TRADING SYSTEM WITH PERFORMANCE OPTIMIZER
    ================================================================

    Features:
    [x] AI-Powered Alligator Strategy
    [x] Real-time Performance Optimization
    [x] Automatic Parameter Adjustment
    [x] Risk Management & Position Sizing
    [x] Performance Monitoring & Reporting

    Trading: BTCUSD with Llama3.2:3b AI Model
    Broker: FBS

    ================================================================
    """
    print(banner)


def check_dependencies():
    """Check system dependencies"""
    logger.info("Checking system dependencies...")

    try:
        import MetaTrader5 as mt5
        import pandas as pd
        import numpy as np
        import requests
        logger.info("[OK] All required packages installed")
        return True
    except ImportError as e:
        logger.error(f"[ERROR] Missing dependency: {e}")
        return False


def check_mt5_connection():
    """Check MT5 connection"""
    logger.info("Checking MT5 connection...")

    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            account = mt5.account_info()
            if account:
                logger.info(f"✓ MT5 connected - Account: {account.login}")
                logger.info(f"  Balance: {account.balance:.2f} {account.currency}")
                logger.info(f"  Equity: {account.equity:.2f} {account.currency}")
                mt5.shutdown()
                return True
            else:
                logger.error("❌ No account info available")
                return False
        else:
            logger.error("❌ Failed to initialize MT5")
            return False
    except Exception as e:
        logger.error(f"❌ MT5 connection error: {e}")
        return False


def check_ollama_connection():
    """Check Ollama connection"""
    logger.info("Checking Ollama connection...")

    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                model_names = [model['name'] for model in models]
                logger.info(f"✓ Ollama connected - Available models: {', '.join(model_names)}")
                return True
            else:
                logger.error("❌ No models available in Ollama")
                return False
        else:
            logger.error(f"❌ Ollama API error: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ollama connection error: {e}")
        return False


def load_configuration():
    """Load or create configuration"""
    logger.info("Loading configuration...")

    try:
        from ai_alligator_btcusd_optimized import BTCUSDConfig
        config = BTCUSDConfig()

        # Validate key settings
        logger.info(f"  Symbol: {config.symbol}")
        logger.info(f"  Model: {config.model}")
        logger.info(f"  Timeframe: M{config.timeframe}")
        logger.info(f"  Risk: {config.max_risk_percent}%")
        logger.info(f"  SL/TP: {config.sl_points}/{config.tp_points}")

        return config
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        return None


def display_trading_plan():
    """Display the trading plan"""
    plan = """
    📋 TRADING PLAN
    ================

    Strategy: AI-Enhanced Alligator
    - Entry signals from AI analysis
    - Automatic SL/TP placement
    - Dynamic position sizing
    - Real-time optimization

    Risk Management:
    - Max 1% risk per trade
    - Automatic stop loss
    - Take profit: 2:1 ratio
    - Spread monitoring

    Optimization:
    - Performance analysis every 5 minutes
    - Automatic parameter adjustment
    - Win rate improvement targeting 55%+
    - Drawdown control < 10%

    Monitoring:
    - Real-time performance metrics
    - Trade history tracking
    - P&L reporting
    - Optimization logs
    """
    print(plan)


def start_trading_system():
    """Start the complete trading system"""
    print_banner()

    # System checks
    if not check_dependencies():
        logger.error("System dependencies check failed")
        return False

    if not check_mt5_connection():
        logger.error("MT5 connection check failed")
        return False

    if not check_ollama_connection():
        logger.error("Ollama connection check failed")
        return False

    # Load configuration
    config = load_configuration()
    if not config:
        logger.error("Configuration loading failed")
        return False

    # Display trading plan
    display_trading_plan()

    # Get user confirmation
    logger.info("🚀 Starting AI Trading System with Performance Optimizer...")
    logger.info("Press Ctrl+C to stop at any time")

    try:
        # Import and run the enhanced strategy
        from ai_alligator_with_optimizer import main as run_enhanced_strategy
        run_enhanced_strategy()

    except KeyboardInterrupt:
        logger.info("\n⏹️ Trading system stopped by user")
    except Exception as e:
        logger.error(f"💥 System error: {e}")
        return False

    return True


def main():
    """Main entry point"""
    logger.info("AI Trading System Launcher")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Startup time: {datetime.now().isoformat()}")

    success = start_trading_system()

    if success:
        logger.info("✅ Trading system completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Trading system failed")
        sys.exit(1)


if __name__ == "__main__":
    main()