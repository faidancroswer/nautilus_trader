#!/usr/bin/env python3
"""
Main execution script for AI-Powered Alligator Trading System
"""

import logging
import time
import sys
import subprocess
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_prerequisites():
    """Check if all prerequisites are installed"""
    logger.info("Checking prerequisites...")
    
    # Check Python version
    import sys
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    
    # Check required packages
    required_packages = [
        'MetaTrader5',
        'pandas',
        'numpy',
        'requests',
        'matplotlib'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} is installed")
        except ImportError:
            logger.error(f"✗ {package} is not installed")
            return False
    
    return True


def check_mt5_connection():
    """Check MT5 connection"""
    logger.info("Checking MT5 connection...")
    
    import MetaTrader5 as mt5
    
    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    
    account_info = mt5.account_info()
    if account_info is None:
        logger.error(f"Failed to get account info: {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    logger.info(f"✓ Connected to MT5 account {account_info.login}")
    logger.info(f"  Balance: {account_info.balance} {account_info.currency}")
    logger.info(f"  Equity: {account_info.equity} {account_info.currency}")
    
    mt5.shutdown()
    return True


def check_ollama_connection():
    """Check Ollama connection"""
    logger.info("Checking Ollama connection...")
    
    import requests
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"✓ Ollama is running with {len(models)} models")
            for model in models:
                logger.info(f"  - {model['name']}")
            return True
        else:
            logger.error(f"✗ Ollama API returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Failed to connect to Ollama: {e}")
        return False


def setup_logging():
    """Setup comprehensive logging"""
    # Create logs directory
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Setup rotating file handler
    from logging.handlers import RotatingFileHandler
    
    # Main log file
    main_handler = RotatingFileHandler(
        'logs/trading_system.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    main_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Error log file
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
    ))
    
    # Apply handlers to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    
    logger.info("Logging setup completed")


def run_strategy(strategy_type: str = "basic"):
    """Run selected trading strategy"""
    strategies = {
        "basic": "simple_alligator_trading.py",
        "ai": "ai_alligator_trading.py",
        "advanced": "advanced_ai_alligator.py",
        "learning": "learning_ai_alligator.py"
    }
    
    if strategy_type not in strategies:
        logger.error(f"Unknown strategy type: {strategy_type}")
        return False
    
    strategy_file = strategies[strategy_type]
    
    if not os.path.exists(strategy_file):
        logger.error(f"Strategy file not found: {strategy_file}")
        return False
    
    logger.info(f"Starting {strategy_type} strategy...")
    
    try:
        # Run the strategy
        result = subprocess.run([
            sys.executable, 
            strategy_file
        ], check=True, capture_output=True, text=True)
        
        logger.info(f"Strategy completed with return code: {result.returncode}")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        if result.stderr:
            logger.warning(f"Errors: {result.stderr}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Strategy failed with return code: {e.returncode}")
        logger.error(f"Output: {e.output}")
        logger.error(f"Error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to run strategy: {e}")
        return False


def run_dashboard():
    """Run trading dashboard"""
    dashboard_file = "trading_dashboard.py"
    
    if not os.path.exists(dashboard_file):
        logger.error(f"Dashboard file not found: {dashboard_file}")
        return False
    
    logger.info("Starting trading dashboard...")
    
    try:
        # Run the dashboard
        result = subprocess.run([
            sys.executable,
            dashboard_file
        ], check=True, capture_output=True, text=True)
        
        logger.info(f"Dashboard completed with return code: {result.returncode}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Dashboard failed with return code: {e.returncode}")
        logger.error(f"Output: {e.output}")
        logger.error(f"Error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to run dashboard: {e}")
        return False


def show_menu():
    """Show main menu"""
    print("\n" + "="*60)
    print("AI-Powered Alligator Trading System")
    print("="*60)
    print("1. Run Basic Alligator Strategy")
    print("2. Run AI-Powered Alligator Strategy")
    print("3. Run Advanced AI Alligator Strategy")
    print("4. Run Learning AI Alligator Strategy")
    print("5. Run Trading Dashboard")
    print("6. System Diagnostics")
    print("7. Exit")
    print("-"*60)
    
    while True:
        try:
            choice = input("Select an option (1-7): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6', '7']:
                return choice
            else:
                print("Invalid option. Please select 1-7.")
        except KeyboardInterrupt:
            return '7'


def run_diagnostics():
    """Run system diagnostics"""
    logger.info("Running system diagnostics...")
    
    print("\n" + "="*50)
    print("SYSTEM DIAGNOSTICS")
    print("="*50)
    
    # Check prerequisites
    print("\n1. Prerequisites Check:")
    if check_prerequisites():
        print("   ✓ All prerequisites OK")
    else:
        print("   ✗ Some prerequisites missing")
    
    # Check MT5
    print("\n2. MT5 Connection:")
    if check_mt5_connection():
        print("   ✓ MT5 connection OK")
    else:
        print("   ✗ MT5 connection failed")
    
    # Check Ollama
    print("\n3. Ollama Connection:")
    if check_ollama_connection():
        print("   ✓ Ollama connection OK")
    else:
        print("   ✗ Ollama connection failed")
    
    # System info
    print("\n4. System Information:")
    print(f"   Python Version: {sys.version}")
    print(f"   Platform: {sys.platform}")
    print(f"   Working Directory: {os.getcwd()}")
    
    print("\n" + "="*50)
    input("Press Enter to continue...")


def main():
    """Main function"""
    logger.info("Starting AI-Powered Alligator Trading System Setup")
    
    # Setup logging
    setup_logging()
    
    # Welcome message
    print("\n" + "="*60)
    print("Welcome to AI-Powered Alligator Trading System")
    print("="*60)
    print(f"System started at: {datetime.now()}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    
    # Run diagnostics automatically on first run
    print("\nPerforming initial system check...")
    if not (check_prerequisites() and check_mt5_connection() and check_ollama_connection()):
        logger.warning("Some system checks failed. Continue anyway? (y/n): ")
        if input().lower() != 'y':
            logger.info("Exiting system setup")
            return
    
    # Main menu loop
    while True:
        choice = show_menu()
        
        if choice == '1':
            logger.info("User selected Basic Alligator Strategy")
            run_strategy("basic")
        elif choice == '2':
            logger.info("User selected AI-Powered Alligator Strategy")
            run_strategy("ai")
        elif choice == '3':
            logger.info("User selected Advanced AI Alligator Strategy")
            run_strategy("advanced")
        elif choice == '4':
            logger.info("User selected Learning AI Alligator Strategy")
            run_strategy("learning")
        elif choice == '5':
            logger.info("User selected Trading Dashboard")
            run_dashboard()
        elif choice == '6':
            run_diagnostics()
        elif choice == '7':
            logger.info("User selected Exit")
            print("\nThank you for using AI-Powered Alligator Trading System!")
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()