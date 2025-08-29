# Enhanced Alligator Strategy Troubleshooting Guide

## Overview
This document provides comprehensive troubleshooting guidance for common issues encountered with the enhanced Alligator strategy.

## Common Issues and Solutions

### 1. Strategy Initialization Failures

#### Problem: Strategy fails to start with "Could not find instrument" error
**Symptoms**: 
- Error message in logs: "Could not find instrument for [instrument_id]"
- Strategy stops immediately after startup

**Causes**:
1. Incorrect instrument ID in configuration
2. Instrument not available from data provider
3. Typo in instrument identifier

**Solutions**:
```bash
# 1. Verify instrument ID in configuration
grep -i instrument_id config/current.yaml

# 2. Check if instrument is available from data provider
python scripts/verify_instrument.py --instrument EUR/USD.IDEALPRO

# 3. Correct instrument ID if needed
sed -i 's/EUR\/USD\.IDEALPRO/EURUSD\.FXCM/' config/current.yaml
```

#### Problem: "Waiting for indicators to warm up" indefinitely
**Symptoms**:
- Strategy shows "Waiting for indicators to warm up" message continuously
- No trades are executed
- Indicators never become initialized

**Causes**:
1. Insufficient historical data
2. Incorrect indicator parameters
3. Data feed issues

**Solutions**:
```python
# 1. Check indicator initialization status
python scripts/debug_indicators.py --instrument EUR/USD.IDEALPRO

# 2. Verify data availability
python scripts/check_data_availability.py --instrument EUR/USD.IDEALPRO --days 7

# 3. Adjust indicator parameters if needed
# In config/current.yaml:
# alligator:
#   jaw_period: 13
#   jaw_shift: 8
#   teeth_period: 8
#   teeth_shift: 5
#   lips_period: 5
#   lips_shift: 3
```

### 2. AI Agent Issues

#### Problem: "Ollama connection failed" error
**Symptoms**:
- Error messages about Ollama connection failures
- AI agent not making decisions
- Strategy falling back to rule-based trading

**Causes**:
1. Ollama service not running
2. Incorrect Ollama host/port configuration
3. Network connectivity issues
4. Firewall blocking connection

**Solutions**:
```bash
# 1. Check if Ollama service is running
systemctl status ollama

# 2. Start Ollama service if not running
systemctl start ollama

# 3. Verify Ollama API accessibility
curl -f http://localhost:11434/api/tags

# 4. Check firewall settings
sudo ufw status
sudo ufw allow 11434/tcp

# 5. Verify configuration settings
grep -E "(OLLAMA_HOST|OLLAMA_PORT)" .env
```

#### Problem: AI agent returning invalid decisions
**Symptoms**:
- AI agent returns unexpected responses
- Strategy logs show "Invalid AI decision" warnings
- Trading decisions seem random or incorrect

**Causes**:
1. Incorrect prompt formatting
2. AI model hallucination
3. Invalid response parsing
4. Model not suitable for trading tasks

**Solutions**:
```python
# 1. Enable debug logging for AI agent
export LOG_LEVEL=DEBUG

# 2. Review AI agent prompts and responses
tail -f logs/strategy.log | grep -i "ai\|ollama"

# 3. Test AI agent with sample prompts
python scripts/test_ai_agent.py --sample-prompts

# 4. Adjust AI agent parameters
# In config/current.yaml:
# ai_agent:
#   temperature: 0.3  # Lower temperature for more consistent responses
#   max_tokens: 100
#   timeout: 30
```

### 3. Indicator Calculation Issues

#### Problem: Indicators showing incorrect values
**Symptoms**:
- Indicator values don't match expected calculations
- Trading signals appear inconsistent
- Strategy performance degraded

**Causes**:
1. Incorrect indicator parameters
2. Data quality issues
3. Implementation bugs
4. Wrong price series used for calculations

**Solutions**:
```python
# 1. Validate indicator calculations
python scripts/validate_indicators.py --instrument EUR/USD.IDEALPRO --date 2023-01-01

# 2. Compare with reference implementation
python scripts/compare_indicators.py --reference ta-lib

# 3. Check data quality
python scripts/check_data_quality.py --instrument EUR/USD.IDEALPRO

# 4. Review indicator implementation
# Check indicator source code for bugs
less indicators/alligator.py
```

#### Problem: Indicator lagging behind market
**Symptoms**:
- Trading signals arrive late
- Missed profitable opportunities
- Strategy reacts to past events

**Causes**:
1. Excessive smoothing parameters
2. Data feed delays
3. System processing bottlenecks
4. Incorrect time synchronization

**Solutions**:
```bash
# 1. Check system performance
top -p $(pgrep -f enhanced_alligator)

# 2. Monitor data feed latency
python scripts/monitor_latency.py --instrument EUR/USD.IDEALPRO

# 3. Optimize indicator parameters
# In config/current.yaml:
# alligator:
#   jaw_period: 10  # Reduced from 13
#   jaw_shift: 6    # Reduced from 8

# 4. Check system clock synchronization
ntpq -p
```

### 4. Risk Management Issues

#### Problem: Excessive position sizing
**Symptoms**:
- Position sizes larger than expected
- Rapid equity drawdown
- Violation of risk limits

**Causes**:
1. Incorrect risk percentage configuration
2. Faulty volatility calculations
3. Equity calculation errors
4. Missing risk controls

**Solutions**:
```python
# 1. Review risk management configuration
grep -A 10 "risk_management" config/current.yaml

# 2. Check current position sizing
python scripts/analyze_positions.py --current

# 3. Verify account equity calculations
python scripts/check_equity.py

# 4. Test risk calculations
python scripts/test_risk_calculations.py
```

#### Problem: Strategy not closing losing positions
**Symptoms**:
- Losing positions held beyond stop loss levels
- Drawdown exceeding limits
- Risk controls not triggering

**Causes**:
1. Incorrect stop loss configuration
2. Missing exit logic
3. Order execution failures
4. Risk management disabled

**Solutions**:
```python
# 1. Check stop loss settings
grep -A 5 "stop_loss" config/current.yaml

# 2. Review exit logic implementation
# Check strategy code for exit conditions
grep -A 10 "close_position\|exit_" strategy/enhanced_alligator.py

# 3. Monitor order execution
tail -f logs/strategy.log | grep -i "order\|execution"

# 4. Test exit conditions
python scripts/test_exit_conditions.py
```

### 5. Data Feed Issues

#### Problem: Missing or delayed market data
**Symptoms**:
- Gaps in bar data
- Delayed price updates
- Strategy not receiving expected data

**Causes**:
1. Data provider connectivity issues
2. Network problems
3. Subscription errors
4. Rate limiting

**Solutions**:
```bash
# 1. Check data provider connectivity
ping -c 4 data-provider-host

# 2. Verify subscriptions
python scripts/check_subscriptions.py

# 3. Monitor data feed health
python scripts/monitor_data_feed.py --instrument EUR/USD.IDEALPRO

# 4. Check for rate limiting
tail -f logs/data_provider.log | grep -i "rate\|limit"
```

#### Problem: Data quality issues
**Symptoms**:
- Erroneous price spikes
- Missing data points
- Inconsistent volume data
- Duplicate timestamps

**Causes**:
1. Data provider errors
2. Network transmission issues
3. Data processing bugs
4. Clock synchronization problems

**Solutions**:
```python
# 1. Validate data quality
python scripts/validate_data.py --instrument EUR/USD.IDEALPRO --days 1

# 2. Check for outliers
python scripts/detect_outliers.py --instrument EUR/USD.IDEALPRO

# 3. Clean corrupted data
python scripts/clean_data.py --instrument EUR/USD.IDEALPRO --remove-outliers

# 4. Verify timestamp synchronization
python scripts/check_timestamps.py
```

### 6. Order Execution Issues

#### Problem: Orders not being filled
**Symptoms**:
- Submitted orders not appearing in execution reports
- Positions not opening/closing as expected
- Order status remains "SUBMITTED"

**Causes**:
1. Incorrect order parameters
2. Exchange connectivity issues
3. Insufficient funds
4. Market liquidity problems

**Solutions**:
```python
# 1. Check order submission logs
grep -i "submit_order" logs/strategy.log

# 2. Verify exchange connectivity
python scripts/test_exchange_connection.py

# 3. Check account balance
python scripts/check_balance.py

# 4. Review order parameters
python scripts/validate_orders.py --recent
```

#### Problem: Slippage exceeding expectations
**Symptoms**:
- Large difference between expected and actual execution prices
- Reduced profitability
- Increased transaction costs

**Causes**:
1. Market volatility
2. Insufficient liquidity
3. Poor order timing
4. Incorrect order types

**Solutions**:
```python
# 1. Analyze slippage patterns
python scripts/analyze_slippage.py --period 30-days

# 2. Optimize order execution
# In config/current.yaml:
# order_management:
#   order_type: "LIMIT"  # Instead of MARKET
#   slippage_tolerance: 3  # Reduced from 5

# 3. Check market conditions
python scripts/check_market_conditions.py --instrument EUR/USD.IDEALPRO

# 4. Review execution timing
python scripts/optimize_execution_timing.py
```

## Diagnostic Tools

### Built-in Diagnostic Scripts

#### 1. Strategy Health Check
```bash
# Run comprehensive health check
python scripts/health_check.py --full

# Output example:
# Strategy Health Check Report
# =============================
# Status: HEALTHY
# 
# Components:
# - Data Feed: OK
# - Indicators: OK
# - AI Agent: OK
# - Risk Management: OK
# - Order Execution: OK
# 
# Last Update: 2023-01-01 12:00:00 UTC
```

#### 2. Performance Analysis
```bash
# Analyze strategy performance
python scripts/performance_analysis.py --period 7-days

# Output example:
# Performance Analysis Report
# ==========================
# Period: 2022-12-25 to 2023-01-01
# 
# Metrics:
# - Total Return: 2.5%
# - Sharpe Ratio: 1.8
# - Win Rate: 62%
# - Profit Factor: 1.9
# 
# Top Performing Instruments:
# 1. EUR/USD: 1.8%
# 2. GBP/USD: 1.5%
# 3. USD/JPY: 0.8%
```

#### 3. Configuration Validator
```bash
# Validate configuration
python scripts/validate_config.py

# Output example:
# Configuration Validation Report
# ===============================
# Status: VALID
# 
# Checked Sections:
# - Instrument Configuration: OK
# - Indicator Parameters: OK
# - Risk Management: OK
# - AI Agent Settings: OK
# 
# Warnings:
# - max_risk_percent (3.0%) is higher than recommended (2.0%)
```

### External Diagnostic Tools

#### 1. System Monitoring
```bash
# Monitor system resources
htop

# Check disk I/O
iotop

# Monitor network usage
iftop

# Check memory usage
free -h
```

#### 2. Network Diagnostics
```bash
# Check network connectivity
ping -c 4 ollama-service

# Trace network route
traceroute ollama-service

# Check open ports
netstat -tulpn | grep 11434

# Monitor network traffic
tcpdump -i any port 11434
```

#### 3. Log Analysis
```bash
# Search for specific error patterns
grep -i "error\|exception\|critical" logs/strategy.log

# Analyze log volume over time
awk '{print $1" "$2}' logs/strategy.log | cut -d: -f1 | sort | uniq -c

# Filter logs by component
grep "ai_agent" logs/strategy.log | tail -20
```

## Performance Optimization

### Resource Usage Optimization

#### 1. Memory Optimization
```python
# Profile memory usage
python -m memory_profiler strategy_runner.py

# Optimize memory-intensive operations
# Use generators instead of lists for large datasets
def data_generator():
    for item in large_dataset:
        yield process_item(item)

# Implement object pooling
class ObjectPool:
    def __init__(self, klass, initial_size=10):
        self.klass = klass
        self.pool = [klass() for _ in range(initial_size)]
        
    def acquire(self):
        if self.pool:
            return self.pool.pop()
        return self.klass()
        
    def release(self, obj):
        obj.reset()
        self.pool.append(obj)
```

#### 2. CPU Optimization
```python
# Profile CPU usage
python -m cProfile -o profile.out strategy_runner.py

# Optimize hotspots
# Use numba for numerical computations
import numba

@numba.jit(nopython=True)
def fast_calculation(data):
    result = 0.0
    for i in range(len(data)):
        result += data[i] * data[i]
    return result

# Use multiprocessing for parallel processing
from multiprocessing import Pool

def parallel_process(chunk):
    return expensive_calculation(chunk)

with Pool() as pool:
    results = pool.map(parallel_process, data_chunks)
```

### Database Optimization

#### 1. Query Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_instrument ON trades(instrument_id);
CREATE INDEX idx_trades_status ON trades(status);

-- Optimize complex queries
EXPLAIN QUERY PLAN 
SELECT * FROM trades t
JOIN positions p ON t.position_id = p.id
WHERE t.timestamp >= date('now', '-7 days')
ORDER BY t.timestamp DESC;
```

#### 2. Data Archiving
```python
# Archive old data to improve performance
def archive_old_data(cutoff_date):
    # Move old trades to archive table
    cursor.execute("""
        INSERT INTO trades_archive 
        SELECT * FROM trades 
        WHERE timestamp < ?
    """, (cutoff_date,))
    
    # Delete archived data
    cursor.execute("""
        DELETE FROM trades 
        WHERE timestamp < ?
    """, (cutoff_date,))
    
    # Commit changes
    conn.commit()
```

## Advanced Troubleshooting

### Debugging Techniques

#### 1. Interactive Debugging
```python
# Add breakpoints for interactive debugging
import pdb

def problematic_function(data):
    pdb.set_trace()  # Debugger will stop here
    result = complex_calculation(data)
    return result

# Run with debugger
python -m pdb strategy_runner.py
```

#### 2. Remote Debugging
```python
# Enable remote debugging
import pydevd_pycharm

def remote_debug_function():
    pydevd_pycharm.settrace('localhost', port=12345, stdoutToServer=True, stderrToServer=True)
    # Code to debug
    pass
```

#### 3. Logging Enhancement
```python
# Add detailed logging for debugging
import logging

logger = logging.getLogger(__name__)

def complex_function(data):
    logger.debug(f"Input data: {data[:10]}...")  # Log first 10 elements
    
    intermediate_result = step_one(data)
    logger.debug(f"Step one result: {intermediate_result[:10]}...")
    
    final_result = step_two(intermediate_result)
    logger.debug(f"Final result: {final_result}")
    
    return final_result
```

### Performance Profiling

#### 1. CPU Profiling
```bash
# Profile CPU usage
python -m cProfile -o profile.out strategy_runner.py

# Analyze results
python -m pstats profile.out

# Generate visual profile
pyprof2calltree -i profile.out -o profile.kgrind
# Open profile.kgrind with KCachegrind
```

#### 2. Memory Profiling
```bash
# Profile memory usage
pip install memory_profiler
python -m memory_profiler strategy_runner.py

# Line-by-line memory profiling
@profile
def memory_intensive_function():
    data = [i for i in range(1000000)]
    processed = [x * 2 for x in data]
    return processed
```

#### 3. I/O Profiling
```python
# Profile I/O operations
python -m trace --trace strategy_runner.py

# Monitor file operations
strace -e trace=open,read,write python strategy_runner.py
```

## Emergency Procedures

### Strategy Shutdown

#### 1. Graceful Shutdown
```python
# Implement graceful shutdown handler
import signal
import sys

def graceful_shutdown(signum, frame):
    logger.info("Received shutdown signal, initiating graceful shutdown...")
    
    # Cancel all orders
    strategy.cancel_all_orders()
    
    # Close all positions
    strategy.close_all_positions()
    
    # Save strategy state
    strategy.save_state()
    
    # Shutdown cleanly
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)
```

#### 2. Emergency Stop
```python
# Emergency stop procedure
def emergency_stop():
    # Immediately cancel all orders
    exchange.cancel_all_orders()
    
    # Close all positions at market
    exchange.close_all_positions(market_order=True)
    
    # Disable strategy
    strategy.disable()
    
    # Alert administrators
    send_alert("Emergency stop activated - all positions closed")
```

### Disaster Recovery

#### 1. Data Recovery
```python
# Recover from data corruption
def recover_data(backup_source):
    # Restore from latest backup
    restore_from_backup(backup_source)
    
    # Reconcile with exchange data
    reconcile_with_exchange()
    
    # Validate recovered data
    validate_data_integrity()
```

#### 2. System Recovery
```bash
# Full system recovery procedure
#!/bin/bash

# 1. Stop all services
systemctl stop enhanced-alligator
systemctl stop ollama

# 2. Restore from backup
tar -xzf backups/latest_backup.tar.gz -C /

# 3. Restore database
gunzip < backups/db_backup.sql.gz | sqlite3 trading_data.db

# 4. Verify restoration
python scripts/verify_restoration.py

# 5. Start services
systemctl start ollama
systemctl start enhanced-alligator

# 6. Monitor recovery
journalctl -fu enhanced-alligator
```

## Prevention Strategies

### Regular Maintenance Tasks

#### 1. Automated Health Checks
```bash
# Schedule regular health checks
# Add to crontab:
# 0 * * * * /opt/enhanced-alligator/scripts/health_check.py --brief
# 0 0 * * * /opt/enhanced-alligator/scripts/health_check.py --full
```

#### 2. Proactive Monitoring
```python
# Implement proactive monitoring
def proactive_monitoring():
    # Check system resources
    if system_resources_low():
        send_alert("Low system resources detected")
        
    # Check data feed health
    if data_feed_issues():
        restart_data_feed()
        
    # Check AI agent performance
    if ai_performance_degraded():
        retrain_ai_model()
```

#### 3. Regular Updates
```bash
# Schedule regular updates
# Add to crontab:
# 0 2 * * 0 /opt/enhanced-alligator/scripts/update_dependencies.py
# 0 3 * * 0 /opt/enhanced-alligator/scripts/update_ollama_models.py
```

This troubleshooting guide provides comprehensive solutions for common issues with the enhanced Alligator strategy. Regular maintenance and proactive monitoring help prevent many issues from occurring in the first place.