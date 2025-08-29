# Nautilus Trader Project Context

## Project Overview

NautilusTrader is a high-performance, production-grade algorithmic trading platform built with a hybrid of Python, Cython, and Rust. It provides quantitative traders with the ability to backtest portfolios of automated trading strategies on historical data with an event-driven engine, and also deploy those same strategies live, with no code changes.

Key features include:
- Fast core written in Rust with asynchronous networking
- Reliable, type-safe, and thread-safe architecture
- Portable across Linux, macOS, and Windows
- Flexible modular adapters for various trading venues and data providers
- Advanced order types and execution instructions
- Customizable components and actors
- Backtesting with multiple venues and instruments
- Live trading with identical strategy implementations
- AI training capabilities for trading agents

This directory contains a specialized AI-driven trading system built on top of NautilusTrader, integrating with MetaTrader 5 (MT5) and utilizing Ollama for AI decision-making, specifically configured for FBS trading accounts.

## System Architecture

The AI trading system is designed for speed and real-time decision making. It consists of several key components:

1. **Fast AI Trading System (`fast_ai_trading.py`)**: The main optimized trading loop that fetches market data, performs technical analysis, queries the AI agent for decisions, and executes trades.
2. **Advanced AI Alligator Strategy (`advanced_ai_alligator.py`)**: A more comprehensive trading strategy using the Alligator indicator and other technical analysis tools.
3. **Ollama Configuration (`ollama_config.py`)**: Manages connection and configuration settings for the Ollama AI service, optimized for either speed or accuracy.
4. **Setup and Execution Scripts (`setup_fast_trading.py`, `run_fast_trading.py`)**: Automation scripts for system setup and execution.

## Building and Running

### Prerequisites
1. Python 3.8+
2. MetaTrader 5 installed and configured with an FBS account
3. Ollama installed and running (https://ollama.ai/download)
4. Required Python packages: MetaTrader5, pandas, numpy, requests

### Installation
Run the automated setup script:
```bash
python setup_fast_trading.py
```

This script will verify all prerequisites, install necessary Python packages, check/start Ollama, download the required Llama3:8b model, and create configuration files.

### Running the System
Use the execution menu:
```bash
python run_fast_trading.py
```

This presents a menu with options to:
1. Execute Fast Trading (optimized for speed)
2. Execute Advanced Trading (comprehensive analysis)
3. Setup System
4. Test Connections
5. View System Status

### Key Components Explained

#### Fast AI Trading (`fast_ai_trading.py`)
- Implements a high-frequency trading loop optimized for sub-10-second decision cycles
- Uses a fast technical analyzer for indicators like Alligator, RSI, and MACD
- Integrates with Ollama via a FastOllamaAgent that uses intelligent caching to avoid unnecessary AI calls
- Manages position opening/closing with dynamic stop-loss and take-profit based on market volatility
- Configured for EURUSD trading on a 1-minute timeframe with a default lot size of 0.1

#### Ollama Configuration (`ollama_config.py`)
- Manages connection to the Ollama service (localhost:11434)
- Supports three optimization modes:
  - Speed: 8-second timeout, low temperature (0.1), 30 max tokens, 60-second cache
  - Accuracy: 20-second timeout, higher temperature (0.3), 100 max tokens, 15-second cache
  - Balanced: Default settings
- Includes model validation and warm-up capabilities
- Features an intelligent caching mechanism to avoid redundant AI queries

#### Alligator Strategy (`alligator_strategy.py` and related files)
- Implements Bill Williams' Alligator indicator for market trend analysis
- Uses a combination of technical indicators (RSI, MACD, Bollinger Bands) for decision making
- Designed for both backtesting and live trading scenarios

## Development Conventions

This project follows a hybrid approach combining Python for high-level logic and configuration with performance-critical components potentially implemented in Rust or Cython.

### Code Structure
- Python trading logic and AI integration in `.py` files
- Configuration files in `.json` format
- Documentation in `.md` files
- Build and automation scripts in `.py` files

### Testing
- Unit tests for individual components
- Integration tests for system connectivity (MT5, Ollama)
- Performance testing for trading loop timing

### Logging
- Comprehensive logging to both file and console
- Different log files for different system components (fast trading, advanced trading, startup)
- Log levels for debugging and production monitoring

### Configuration Management
- Centralized configuration in `ollama_config.py`
- JSON-based configuration files for persistent settings
- Environment-specific configurations (speed vs. accuracy)

## Key Files and Directories

### Core Trading System
- `fast_ai_trading.py`: Main optimized trading system
- `advanced_ai_alligator.py`: Advanced trading strategy
- `ollama_config.py`: Ollama configuration and management
- `run_fast_trading.py`: Main execution menu
- `setup_fast_trading.py`: System setup automation

### Supporting Components
- `alligator_indicator.py`: Implementation of the Alligator indicator
- `alligator_strategy.py`: Basic Alligator trading strategy
- `backtest_nautilus_alligator.py`: Backtesting framework for Alligator strategy
- `mt5_adapter.py`: Adapter for MetaTrader 5 integration
- Various test files (`test_*.py`) for unit and integration testing

### Configuration and Data
- `enhanced_alligator_config.json`: Configuration for enhanced Alligator strategy
- `ollama_trading_config.json`: Ollama trading configuration
- `EURUSD_historical_data.csv`: Sample historical data for backtesting
- `config.ini`: General system configuration

### Documentation
- `README.md`: Main NautilusTrader documentation
- `README_TRADING_AI.md`: Documentation for the AI trading system
- `technical_requirements.md`: Technical specifications
- `implementation_plan.md`: Development roadmap
- Various guide files (`*_guide.md`) for specific topics

## Performance Considerations

1. **Decision Latency**: The fast trading system is optimized for sub-10-second decision cycles
2. **Caching**: Intelligent caching in the Ollama agent reduces unnecessary AI queries
3. **Data Efficiency**: Minimal data fetching and processing to reduce overhead
4. **Connection Management**: Persistent connections where possible to reduce latency
5. **Resource Usage**: Designed to be lightweight with minimal CPU and memory footprint

## Risk Management

1. **Position Sizing**: Dynamic position sizing based on account equity (1.5% risk per trade)
2. **Stop Loss and Take Profit**: Dynamically calculated based on market volatility
3. **Account Monitoring**: Real-time monitoring of account balance and equity
4. **Connection Health**: Regular checks of MT5 and Ollama connectivity
5. **Manual Intervention**: System can be paused or stopped manually at any time

## Troubleshooting

Common issues and solutions:
1. **Ollama Connection**: Verify Ollama is running (`ollama list`) and accessible
2. **MT5 Connection**: Check MT5 installation, account credentials, and connection status
3. **Model Availability**: Ensure the required Llama3:8b model is downloaded (`ollama pull llama3:8b`)
4. **Trading Permissions**: Verify automated trading is enabled in MT5
5. **Performance Issues**: Check system resources and network connectivity

Useful diagnostic commands:
```bash
# Check Ollama status
curl http://localhost:11434/api/tags
ollama run llama3:8b "Test trading decision"

# Check logs
tail -f fast_ai_trading.log
```