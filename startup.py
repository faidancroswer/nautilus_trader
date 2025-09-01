#!/usr/bin/env python3
"""
Startup script for AI-Powered Alligator Trading System
"""

import logging
import sys
import os
import time
from datetime import datetime
import subprocess

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('startup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_system_status():
    """Check overall system status"""
    logger.info("Checking system status...")
    
    status = {
        'mt5': False,
        'ollama': False,
        'python_packages': False,
        'directories': False
    }
    
    # Check MT5
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"[OK] MT5 connected to account {account_info.login}")
                status['mt5'] = True
            mt5.shutdown()
        else:
            logger.error("[ERROR] MT5 initialization failed")
    except Exception as e:
        logger.error(f"[ERROR] MT5 check failed: {e}")
    
    # Check Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"[OK] Ollama running with {len(models)} models")
            status['ollama'] = True
        else:
            logger.error("[ERROR] Ollama not responding correctly")
    except Exception as e:
        logger.error(f"[ERROR] Ollama check failed: {e}")
    
    # Check Python packages
    required_packages = ['MetaTrader5', 'pandas', 'numpy', 'requests', 'matplotlib']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'MetaTrader5':
                import MetaTrader5
            else:
                __import__(package.lower().replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"[ERROR] Missing packages: {missing_packages}")
    else:
        logger.info("[OK] All required Python packages installed")
        status['python_packages'] = True
    
    # Check directories
    required_dirs = ['logs', 'data', 'models', 'reports']
    missing_dirs = []
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_dirs.append(directory)
    
    if missing_dirs:
        logger.error(f"[ERROR] Missing directories: {missing_dirs}")
    else:
        logger.info("[OK] All required directories present")
        status['directories'] = True
    
    return status


def start_ollama_if_needed():
    """Start Ollama if it's not running"""
    logger.info("Checking if Ollama needs to be started...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/", timeout=2)
        if response.status_code == 200:
            logger.info("✓ Ollama is already running")
            return True
    except:
        pass
    
    # Try to start Ollama
    logger.info("Attempting to start Ollama...")
    try:
        # On Windows, Ollama usually runs as a service
        # On Linux/Mac, we might need to start it manually
        import platform
        if platform.system() == "Windows":
            # Check if Ollama service is installed
            result = subprocess.run(["sc", "query", "ollama"], 
                                  capture_output=True, text=True)
            if "RUNNING" in result.stdout:
                logger.info("✓ Ollama service is running")
                return True
            else:
                logger.warning("⚠ Ollama service not running - please start it manually")
                return False
        else:
            # Try to start Ollama daemon
            result = subprocess.Popen(["ollama", "serve"], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
            time.sleep(3)  # Give it time to start
            return True
            
    except Exception as e:
        logger.error(f"✗ Failed to start Ollama: {e}")
        return False


def pull_required_models():
    """Pull required AI models"""
    logger.info("Checking required AI models...")
    
    try:
        import requests
        
        # Check what models are available
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            required_models = ['phi3:latest']
            available_models = []
            
            for req_model in required_models:
                if any(req_model in model_name for model_name in model_names):
                    available_models.append(req_model)
            
            if available_models:
                logger.info(f"✓ Available models: {available_models}")
                return True
            else:
                logger.warning("⚠ No required models found")
                logger.info("  Consider pulling a model: ollama pull phi3:latest")
                return False
        else:
            logger.error("✗ Failed to get model list from Ollama")
            return False
            
    except Exception as e:
        logger.error(f"✗ Failed to check models: {e}")
        return False


def create_startup_script():
    """Create platform-specific startup script"""
    import platform
    
    if platform.system() == "Windows":
        # Create batch file
        batch_content = """@echo off
REM AI-Powered Alligator Trading System Startup Script

echo Starting AI-Powered Alligator Trading System...
echo ===============================================

REM Activate virtual environment if it exists
if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
    echo Virtual environment activated
)

REM Start the trading system
python run_trading_system.py

echo.
echo Trading system finished. Press any key to exit...
pause >nul
"""
        
        with open("start_trading.bat", "w") as f:
            f.write(batch_content)
        logger.info("✓ Created Windows batch file: start_trading.bat")
        
    else:
        # Create shell script
        shell_content = """#!/bin/bash
# AI-Powered Alligator Trading System Startup Script

echo "Starting AI-Powered Alligator Trading System..."
echo "==============================================="

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Start the trading system
python run_trading_system.py

echo ""
echo "Trading system finished. Press Enter to exit..."
read
"""
        
        with open("start_trading.sh", "w") as f:
            f.write(shell_content)
        # Make it executable
        os.chmod("start_trading.sh", 0o755)
        logger.info("✓ Created Unix shell script: start_trading.sh")


def show_system_info():
    """Show system information"""
    logger.info("="*60)
    logger.info("AI-POWERED ALLIGATOR TRADING SYSTEM")
    logger.info("="*60)
    logger.info(f"Startup Time: {datetime.now()}")
    logger.info(f"Python Version: {sys.version.split()[0]}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info("="*60)


def main():
    """Main startup function"""
    show_system_info()
    
    logger.info("Starting system initialization...")
    
    # Check system status
    status = check_system_status()
    all_good = all(status.values())
    
    if not all_good:
        logger.warning("Some system components are not ready:")
        for component, ready in status.items():
            status_icon = "[OK]" if ready else "[ERROR]"
            logger.info(f"  {status_icon} {component}: {'Ready' if ready else 'Not Ready'}")
        
        logger.info("")
        logger.info("Please check the individual components and resolve any issues.")
        logger.info("You can still start the system, but some features may not work.")
        logger.info("")
        
        user_input = input("Continue anyway? (y/N): ").strip().lower()
        if user_input != 'y':
            logger.info("Startup cancelled by user.")
            return
    
    # Start Ollama if needed
    start_ollama_if_needed()
    
    # Pull required models
    pull_required_models()
    
    # Create startup scripts
    create_startup_script()
    
    # Show final status
    logger.info("="*60)
    logger.info("SYSTEM INITIALIZATION COMPLETE")
    logger.info("="*60)
    logger.info("You can now start the trading system by running:")
    logger.info("  python run_trading_system.py")
    logger.info("")
    logger.info("Or use the platform-specific startup script:")
    import platform
    if platform.system() == "Windows":
        logger.info("  start_trading.bat")
    else:
        logger.info("  ./start_trading.sh")
    logger.info("="*60)


if __name__ == "__main__":
    main()