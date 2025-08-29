#!/usr/bin/env python3
"""
Setup script for the Alligator AI trading environment
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
import pkg_resources

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_packages():
    """Check and install required Python packages"""
    required_packages = [
        'MetaTrader5',
        'pandas',
        'numpy',
        'ollama'
    ]
    
    logger.info("Checking Python packages...")
    
    try:
        # Get installed packages
        installed_packages = {pkg.key for pkg in pkg_resources.working_set}
        
        for package in required_packages:
            if package.lower() not in installed_packages:
                logger.info(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            else:
                logger.info(f"{package} is already installed")
                
        logger.info("All Python packages are installed")
        return True
    except Exception as e:
        logger.error(f"Error checking/installing Python packages: {e}")
        return False

def check_ollama():
    """Check if Ollama is installed and running"""
    logger.info("Checking Ollama installation...")
    
    try:
        # Check if Ollama is installed
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Ollama is not installed. Please install it from https://ollama.ai/")
            return False
            
        logger.info(f"Ollama version: {result.stdout.strip()}")
        
        # Check if Ollama is running
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.info("Starting Ollama service...")
            subprocess.Popen(['ollama', 'serve'])
            # Wait a moment for the service to start
            import time
            time.sleep(5)
            
        logger.info("Ollama is installed and running")
        return True
    except Exception as e:
        logger.error(f"Error checking Ollama: {e}")
        return False

def check_ollama_model(model_name: str = "phi3"):
    """Check if the required Ollama model is available"""
    logger.info(f"Checking Ollama model: {model_name}")
    
    try:
        # Check if model is available
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if model_name not in result.stdout:
            logger.info(f"Pulling {model_name} model...")
            subprocess.run(['ollama', 'pull', model_name], check=True)
            logger.info(f"{model_name} model pulled successfully")
        else:
            logger.info(f"{model_name} model is already available")
            
        return True
    except Exception as e:
        logger.error(f"Error checking/pulling Ollama model: {e}")
        return False

def check_mt5():
    """Check if MT5 is installed"""
    logger.info("Checking MT5 installation...")
    
    try:
        import MetaTrader5 as mt5
        logger.info("MT5 Python package is installed")
        return True
    except ImportError:
        logger.error("MT5 Python package is not installed")
        return False
    except Exception as e:
        logger.error(f"Error importing MT5: {e}")
        return False

def create_default_config():
    """Create default configuration file"""
    config_file = "alligator_trading_config.json"
    
    if os.path.exists(config_file):
        logger.info(f"Configuration file {config_file} already exists")
        return True
    
    default_config = {
        "trading": {
            "symbol": "EURUSD",
            "timeframe": "M1",
            "lot_size": 0.1,
            "risk_percent": 1.5,
            "strategy": "alligator"
        },
        "indicators": {
            "alligator": {
                "jaw_period": 13,
                "jaw_shift": 8,
                "teeth_period": 8,
                "teeth_shift": 5,
                "lips_period": 5,
                "lips_shift": 3
            },
            "rsi": {
                "period": 14,
                "overbought": 70,
                "oversold": 30
            },
            "macd": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            }
        },
        "ollama": {
            "model": "phi3",
            "timeout": 10,
            "temperature": 0.1
        },
        "mt5": {
            "server": "FBS-Real"
        }
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"Default configuration file {config_file} created")
        return True
    except Exception as e:
        logger.error(f"Error creating configuration file: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("Setting up Alligator AI trading environment...")
    
    # Check Python packages
    if not check_python_packages():
        logger.error("Failed to check/install Python packages")
        return False
    
    # Check Ollama
    if not check_ollama():
        logger.error("Failed to check Ollama")
        return False
    
    # Check Ollama model
    if not check_ollama_model("phi3"):
        logger.error("Failed to check/pull Ollama model")
        return False
    
    # Check MT5
    if not check_mt5():
        logger.error("Failed to check MT5")
        return False
    
    # Create default configuration
    if not create_default_config():
        logger.error("Failed to create default configuration")
        return False
    
    logger.info("Alligator AI trading environment setup completed successfully!")
    logger.info("You can now run the trading strategy with:")
    logger.info("  python fast_alligator_ai.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)