#!/usr/bin/env python3
"""
Script to fetch historical data from MT5 and save it for backtesting.
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import MetaTrader5 as mt5
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_mt5():
    """
    Initialize MT5 connection
    """
    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    logger.info("MT5 initialized successfully")
    return True


def fetch_historical_data(symbol, timeframe, days=30):
    """
    Fetch historical data from MT5
    
    Parameters:
    symbol (str): Symbol to fetch data for
    timeframe (int): Timeframe (e.g., mt5.TIMEFRAME_M1)
    days (int): Number of days of historical data to fetch
    
    Returns:
    pandas.DataFrame: Historical data
    """
    # Calculate start and end times
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Fetch data
    rates = mt5.copy_rates_range(symbol, timeframe, start_time, end_time)
    if rates is None:
        logger.error(f"Failed to fetch data for {symbol}: {mt5.last_error()}")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Rename columns to match Nautilus Trader format
    df.rename(columns={
        'time': 'timestamp',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'tick_volume': 'volume'
    }, inplace=True)
    
    # Add additional required columns
    df['symbol'] = symbol
    df['bar_type'] = f"{symbol}-1-MINUTE-BID-EXTERNAL"
    
    logger.info(f"Fetched {len(df)} bars for {symbol}")
    return df


def save_data_to_csv(data, filename):
    """
    Save data to CSV file
    
    Parameters:
    data (pandas.DataFrame): Data to save
    filename (str): Filename to save to
    """
    data.to_csv(filename, index=False)
    logger.info(f"Data saved to {filename}")


def main():
    logger.info("Starting MT5 data fetch")
    
    # Initialize MT5
    if not initialize_mt5():
        return
    
    # Configuration
    symbol = "EURUSD"
    timeframe = mt5.TIMEFRAME_M1
    days = 30
    
    # Fetch data
    data = fetch_historical_data(symbol, timeframe, days)
    if data is None:
        mt5.shutdown()
        return
    
    # Save data
    filename = f"{symbol}_historical_data.csv"
    save_data_to_csv(data, filename)
    
    # Shutdown MT5
    mt5.shutdown()
    logger.info("MT5 data fetch completed")


if __name__ == "__main__":
    main()