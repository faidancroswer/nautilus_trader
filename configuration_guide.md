# Enhanced Alligator Strategy Configuration Guide

## Overview
This document provides detailed instructions for configuring the enhanced Alligator strategy with AI integration.

## Configuration Files

### Main Configuration File
The main configuration file (`enhanced_alligator_config.py`) contains all strategy parameters and settings.

### Environment Configuration
Environment-specific settings are managed through environment variables or a `.env` file.

## Strategy Configuration

### Instrument Configuration
```python
# Instrument settings
instrument_id = "EUR/USD.IDEALPRO"  # Instrument to trade
bar_type = "EUR/USD.IDEALPRO-1-MINUTE-BID-EXTERNAL"  # Bar type for analysis
trade_size = Decimal("1000")  # Base position size
```

### Alligator Indicator Configuration
```python
# Alligator indicator parameters
jaw_period = 13  # Period for Jaw moving average
jaw_shift = 8    # Shift for Jaw moving average
teeth_period = 8  # Period for Teeth moving average
teeth_shift = 5   # Shift for Teeth moving average
lips_period = 5   # Period for Lips moving average
lips_shift = 3   # Shift for Lips moving average
```

### Additional Indicator Configuration

#### RSI Configuration
```python
# RSI indicator parameters
rsi_period = 14  # Standard RSI period
rsi_overbought = 70  # Overbought threshold
rsi_oversold = 30    # Oversold threshold
```

#### MACD Configuration
```python
# MACD indicator parameters
macd_fast_period = 12   # Fast EMA period
macd_slow_period = 26   # Slow EMA period
macd_signal_period = 9  # Signal line period
```

#### Bollinger Bands Configuration
```python
# Bollinger Bands parameters
bb_period = 20        # MA period
bb_std_dev = 2.0      # Standard deviation multiplier
```

#### Stochastic Oscillator Configuration
```python
# Stochastic Oscillator parameters
stoch_k_period = 14   # %K period
stoch_d_period = 3    # %D period (smoothing)
```

### AI Agent Configuration

#### Ollama Connection Settings
```python
# Ollama AI agent settings
ollama_host = "localhost"  # Ollama service host
ollama_port = 11434        # Ollama service port
ollama_model = "llama3"    # AI model to use
```

#### Decision Parameters
```python
# AI decision making parameters
ai_temperature = 0.7      # Creativity vs. consistency (0.0-1.0)
ai_max_tokens = 200       # Maximum response length
ai_timeout = 30           # Timeout for AI responses (seconds)
```

### Risk Management Configuration

#### Position Sizing
```python
# Position sizing parameters
max_risk_percent = 2.0    # Maximum risk per trade (% of equity)
volatility_adjustment = True  # Adjust position size based on volatility
position_scaling_factor = 1.0  # Multiplier for position sizes
```

#### Portfolio Controls
```python
# Portfolio-level risk controls
max_exposure_percent = 10.0    # Maximum exposure per instrument (% of equity)
max_correlation_risk = 0.7     # Maximum correlation between positions
diversification_requirement = 5  # Minimum number of different instruments
```

#### Drawdown Protection
```python
# Drawdown protection settings
max_drawdown_percent = 20.0    # Maximum allowable drawdown (% of peak equity)
drawdown_reduction_factor = 0.5  # Position size reduction during drawdown
circuit_breaker_threshold = 30.0  # Severe drawdown threshold (%)
```

### Order Management Configuration

#### Order Types and Timing
```python
# Order execution parameters
order_type = "MARKET"          # Order type (MARKET, LIMIT, STOP)
time_in_force = "GTC"          # Time in force setting
slippage_tolerance = 5         # Maximum acceptable slippage (pips)
```

#### Execution Controls
```python
# Execution controls
max_order_attempts = 3         # Maximum attempts to submit order
order_retry_delay = 1          # Delay between order attempts (seconds)
execution_timeout = 10         # Timeout for order execution (seconds)
```

## Environment Variables

### Required Environment Variables
```bash
# Ollama service settings
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3

# Exchange API credentials (if trading live)
API_KEY=your_api_key
API_SECRET=your_api_secret
ACCOUNT_ID=your_account_id

# Database connection (for performance tracking)
DATABASE_URL=sqlite:///trading_data.db
```

### Optional Environment Variables
```bash
# Debugging and logging
DEBUG=true
LOG_LEVEL=INFO
LOG_FILE=strategy.log

# Performance optimization
CACHE_SIZE=1000
PARALLEL_PROCESSING=true
```

## Configuration Validation

### Runtime Validation
The strategy performs validation of configuration parameters at startup:

1. **Parameter Range Checks**: Verify all numeric parameters are within acceptable ranges
2. **Required Field Verification**: Ensure all mandatory parameters are provided
3. **Cross-Parameter Validation**: Check for logical consistency between related parameters
4. **External Service Connectivity**: Test connections to Ollama and exchange APIs

### Configuration Templates

#### Conservative Configuration
```python
# Conservative settings for lower-risk trading
{
    "max_risk_percent": 1.0,
    "max_drawdown_percent": 10.0,
    "ai_temperature": 0.3,
    "position_scaling_factor": 0.5
}
```

#### Aggressive Configuration
```python
# Aggressive settings for higher-risk trading
{
    "max_risk_percent": 3.0,
    "max_drawdown_percent": 30.0,
    "ai_temperature": 0.8,
    "position_scaling_factor": 2.0
}
```

#### Learning Configuration
```python
# Settings optimized for strategy learning and adaptation
{
    "ai_temperature": 0.9,
    "max_risk_percent": 1.5,
    "position_scaling_factor": 1.0,
    "enable_continuous_learning": True
}
```

## Dynamic Configuration Updates

### Runtime Parameter Adjustment
Certain parameters can be adjusted during runtime without restarting the strategy:

1. **Risk Management Parameters**: Max risk percent, drawdown limits
2. **Position Sizing**: Scaling factors and volatility adjustments
3. **AI Settings**: Temperature and response parameters
4. **Order Management**: Time in force and slippage tolerance

### Configuration Persistence
Configuration changes can be persisted to:
1. **Local File**: Save to configuration file for future sessions
2. **Database**: Store in database for centralized management
3. **Cloud Storage**: Sync with cloud services for backup and sharing

## Best Practices

### Configuration Management
1. **Version Control**: Keep configuration files in version control
2. **Environment Separation**: Use different configs for dev, test, and prod
3. **Documentation**: Comment all non-obvious configuration choices
4. **Regular Review**: Periodically review and update configurations

### Security Considerations
1. **Credential Protection**: Never store API keys in plain text config files
2. **Access Control**: Restrict access to configuration files
3. **Encryption**: Encrypt sensitive configuration data when possible
4. **Audit Trail**: Log all configuration changes

### Performance Optimization
1. **Cache Settings**: Optimize cache sizes for available memory
2. **Parallel Processing**: Enable parallel processing for multi-core systems
3. **Resource Monitoring**: Monitor CPU and memory usage
4. **Network Optimization**: Use local services when possible

## Troubleshooting

### Common Configuration Issues
1. **Connection Failures**: Verify Ollama service is running and accessible
2. **Parameter Errors**: Check parameter ranges and required fields
3. **Performance Problems**: Review resource usage and optimize settings
4. **Logic Errors**: Validate indicator and strategy logic

### Diagnostic Tools
1. **Configuration Validator**: Built-in tool to check configuration validity
2. **Parameter Inspector**: View current configuration values
3. **Dependency Checker**: Verify all required services are available
4. **Performance Profiler**: Monitor system resource usage

## Advanced Configuration

### Custom Indicator Integration
To add custom indicators:
1. Create indicator class following Nautilus Trader patterns
2. Register indicator in strategy initialization
3. Add configuration parameters to config file
4. Update AI agent prompts to include new indicator data

### Multi-Instrument Support
Configure multiple instruments:
1. Define instrument-specific parameters
2. Set correlation-based risk controls
3. Implement cross-market arbitrage logic
4. Configure instrument-specific AI models

### Machine Learning Integration
Advanced ML features:
1. Auto-parameter optimization
2. Market regime detection
3. Predictive analytics
4. Adaptive strategy selection

This configuration guide provides a comprehensive framework for setting up and managing the enhanced Alligator strategy. Proper configuration is essential for achieving optimal performance and risk management.