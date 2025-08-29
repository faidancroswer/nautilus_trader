#!/usr/bin/env python3
"""
Installation script for AI-Powered Alligator Trading System
"""

import logging
import sys
import subprocess
import os
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('installation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_python_version():
    """Check Python version"""
    logger.info("Checking Python version...")
    
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    
    logger.info(f"✓ Python {sys.version} is OK")
    return True


def install_package(package_name: str, pip_args: list = None):
    """Install a Python package"""
    logger.info(f"Installing {package_name}...")
    
    try:
        cmd = [sys.executable, "-m", "pip", "install"]
        if pip_args:
            cmd.extend(pip_args)
        cmd.append(package_name)
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"✓ Successfully installed {package_name}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed to install {package_name}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error installing {package_name}: {e}")
        return False


def check_and_install_packages():
    """Check and install required packages"""
    logger.info("Checking and installing required packages...")
    
    required_packages = [
        ("MetaTrader5", []),
        ("pandas", []),
        ("numpy", []),
        ("requests", []),
        ("matplotlib", []),
        ("tkinter", []),  # Usually comes with Python
    ]
    
    missing_packages = []
    
    # Check what's already installed
    for package, args in required_packages:
        try:
            if package == "tkinter":
                import tkinter
            else:
                __import__(package.lower().replace("-", "_"))
            logger.info(f"✓ {package} is already installed")
        except ImportError:
            logger.info(f"✗ {package} is missing")
            missing_packages.append((package, args))
    
    # Install missing packages
    if missing_packages:
        logger.info(f"Installing {len(missing_packages)} missing packages...")
        for package, args in missing_packages:
            if not install_package(package, args):
                return False
    
    return True


def check_mt5_installation():
    """Check MT5 installation"""
    logger.info("Checking MT5 installation...")
    
    # Check if MT5 is installed
    try:
        import MetaTrader5 as mt5
        logger.info("✓ MetaTrader5 Python package is installed")
    except ImportError:
        logger.error("✗ MetaTrader5 Python package is not installed")
        return False
    
    # Check if MT5 terminal is installed (Windows only)
    if platform.system() == "Windows":
        import winreg
        
        mt5_paths = [
            r"SOFTWARE\MetaQuotes\MetaTrader 5",
            r"SOFTWARE\Wow6432Node\MetaQuotes\MetaTrader 5"
        ]
        
        mt5_found = False
        for path in mt5_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    install_path = winreg.QueryValueEx(key, "InstallDir")[0]
                    logger.info(f"✓ MT5 found at: {install_path}")
                    mt5_found = True
                    break
            except FileNotFoundError:
                continue
        
        if not mt5_found:
            logger.warning("⚠ MT5 terminal not found in registry")
            logger.info("  Please ensure MetaTrader 5 is installed on your system")
    
    return True


def check_ollama_installation():
    """Check Ollama installation"""
    logger.info("Checking Ollama installation...")
    
    try:
        # Check if Ollama is running
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Ollama is running")
            models = response.json().get('models', [])
            if models:
                logger.info(f"  Available models: {[m['name'] for m in models]}")
            else:
                logger.warning("  No models found in Ollama")
                logger.info("  Consider pulling a model: ollama pull llama3")
            return True
        else:
            logger.warning("⚠ Ollama is not responding correctly")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.warning("⚠ Ollama is not running")
        logger.info("  Please start Ollama service")
        logger.info("  Download from: https://ollama.com/")
        return False
    except Exception as e:
        logger.error(f"✗ Error checking Ollama: {e}")
        return False


def create_directories():
    """Create required directories"""
    logger.info("Creating required directories...")
    
    directories = [
        "logs",
        "data",
        "models",
        "reports"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logger.info(f"✓ Created directory: {directory}")
            except Exception as e:
                logger.error(f"✗ Failed to create directory {directory}: {e}")
                return False
        else:
            logger.info(f"✓ Directory already exists: {directory}")
    
    return True


def create_sample_config():
    """Create sample configuration file"""
    logger.info("Creating sample configuration...")
    
    config_content = """# AI-Powered Alligator Trading System Configuration

[trading]
symbol = EURUSD
timeframe = M1
lot_size = 0.1
sl_points = 100
tp_points = 100
max_risk_percent = 1.5

[ai]
model = llama3
host = localhost
port = 11434

[logging]
level = INFO
log_file = logs/trading_system.log
"""
    
    config_file = "sample_config.ini"
    if not os.path.exists(config_file):
        try:
            with open(config_file, 'w') as f:
                f.write(config_content)
            logger.info(f"✓ Created sample configuration: {config_file}")
        except Exception as e:
            logger.error(f"✗ Failed to create sample configuration: {e}")
            return False
    else:
        logger.info(f"✓ Sample configuration already exists: {config_file}")
    
    return True


def run_tests():
    """Run basic tests"""
    logger.info("Running basic tests...")
    
    # Test imports
    try:
        import MetaTrader5
        import pandas
        import numpy
        import requests
        import matplotlib
        logger.info("✓ All required modules can be imported")
    except ImportError as e:
        logger.error(f"✗ Import test failed: {e}")
        return False
    
    # Test basic functionality
    try:
        # Test pandas
        df = pandas.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        logger.info("✓ Pandas basic functionality OK")
        
        # Test numpy
        arr = numpy.array([1, 2, 3, 4, 5])
        logger.info("✓ NumPy basic functionality OK")
        
        # Test requests (if Ollama is running)
        try:
            requests.get("http://localhost:11434/", timeout=1)
            logger.info("✓ Requests basic functionality OK")
        except:
            logger.info("ℹ Requests test skipped (Ollama not responding)")
        
    except Exception as e:
        logger.error(f"✗ Basic functionality test failed: {e}")
        return False
    
    return True


def main():
    """Main installation function"""
    logger.info("Starting AI-Powered Alligator Trading System Installation")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Python: {sys.version}")
    
    # Check prerequisites
    if not check_python_version():
        logger.error("Installation failed: Python version too old")
        return False
    
    # Check and install packages
    if not check_and_install_packages():
        logger.error("Installation failed: Package installation error")
        return False
    
    # Check MT5 installation
    if not check_mt5_installation():
        logger.warning("MT5 installation check failed")
        logger.info("Continuing with installation...")
    
    # Check Ollama installation
    if not check_ollama_installation():
        logger.warning("Ollama installation check failed")
        logger.info("Continuing with installation...")
    
    # Create directories
    if not create_directories():
        logger.error("Installation failed: Directory creation error")
        return False
    
    # Create sample configuration
    if not create_sample_config():
        logger.error("Installation failed: Configuration creation error")
        return False
    
    # Run tests
    if not run_tests():
        logger.error("Installation failed: Basic tests failed")
        return False
    
    # Success message
    logger.info("="*60)
    logger.info("INSTALLATION COMPLETED SUCCESSFULLY!")
    logger.info("="*60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Ensure MetaTrader 5 is installed and running")
    logger.info("2. Ensure Ollama is installed and running")
    logger.info("3. Pull required AI model: ollama pull llama3")
    logger.info("4. Configure your trading settings in config.ini")
    logger.info("5. Run the system: python run_trading_system.py")
    logger.info("")
    logger.info("For detailed setup instructions, see README.md")
    logger.info("="*60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)