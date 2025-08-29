#!/usr/bin/env python3
"""
AI Trading Dashboard with Real-time Monitoring
"""

import logging
import time
import sys
import json
import requests
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import tkinter as tk
from tkinter import ttk
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dashboard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TradingDashboard:
    """
    Real-time trading dashboard with AI monitoring
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI-Powered Alligator Trading Dashboard")
        self.root.geometry("1200x800")
        
        # Trading data
        self.account_info = {}
        self.positions = []
        self.market_data = []
        self.ai_decisions = []
        
        # Setup GUI
        self.setup_gui()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self.update_data, daemon=True)
        self.update_thread.start()
        
    def setup_gui(self):
        """Setup the GUI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Account tab
        self.account_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.account_frame, text="Account")
        self.setup_account_tab()
        
        # Positions tab
        self.positions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.positions_frame, text="Positions")
        self.setup_positions_tab()
        
        # Market Analysis tab
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="Market Analysis")
        self.setup_analysis_tab()
        
        # AI Decisions tab
        self.ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ai_frame, text="AI Decisions")
        self.setup_ai_tab()
        
        # Performance tab
        self.performance_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.performance_frame, text="Performance")
        self.setup_performance_tab()
    
    def setup_account_tab(self):
        """Setup account information tab"""
        # Account info frame
        info_frame = ttk.LabelFrame(self.account_frame, text="Account Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Account details
        self.balance_label = ttk.Label(info_frame, text="Balance: $0.00")
        self.balance_label.pack(anchor=tk.W)
        
        self.equity_label = ttk.Label(info_frame, text="Equity: $0.00")
        self.equity_label.pack(anchor=tk.W)
        
        self.margin_label = ttk.Label(info_frame, text="Margin: $0.00")
        self.margin_label.pack(anchor=tk.W)
        
        self.free_margin_label = ttk.Label(info_frame, text="Free Margin: $0.00")
        self.free_margin_label.pack(anchor=tk.W)
        
        self.margin_level_label = ttk.Label(info_frame, text="Margin Level: 0%")
        self.margin_level_label.pack(anchor=tk.W)
        
        # Refresh button
        refresh_btn = ttk.Button(info_frame, text="Refresh", command=self.refresh_account)
        refresh_btn.pack(pady=10)
    
    def setup_positions_tab(self):
        """Setup positions tab"""
        # Positions frame
        pos_frame = ttk.LabelFrame(self.positions_frame, text="Open Positions", padding=10)
        pos_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Positions treeview
        columns = ('Ticket', 'Symbol', 'Type', 'Volume', 'Price', 'SL', 'TP', 'Profit')
        self.positions_tree = ttk.Treeview(pos_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(pos_frame, orient=tk.VERTICAL, command=self.positions_tree.yview)
        self.positions_tree.configure(yscroll=scrollbar.set)
        
        self.positions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        refresh_btn = ttk.Button(pos_frame, text="Refresh", command=self.refresh_positions)
        refresh_btn.pack(pady=10)
    
    def setup_analysis_tab(self):
        """Setup market analysis tab"""
        # Market data frame
        market_frame = ttk.LabelFrame(self.analysis_frame, text="Market Data", padding=10)
        market_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=market_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Analysis info
        self.analysis_info = ttk.Label(market_frame, text="Analysis: Loading...")
        self.analysis_info.pack(pady=10)
        
        # Refresh button
        refresh_btn = ttk.Button(market_frame, text="Refresh Chart", command=self.refresh_chart)
        refresh_btn.pack()
    
    def setup_ai_tab(self):
        """Setup AI decisions tab"""
        # AI decisions frame
        ai_frame = ttk.LabelFrame(self.ai_frame, text="AI Trading Decisions", padding=10)
        ai_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # AI decisions text
        self.ai_text = tk.Text(ai_frame, height=20, width=80)
        self.ai_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(ai_frame, orient=tk.VERTICAL, command=self.ai_text.yview)
        self.ai_text.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Clear button
        clear_btn = ttk.Button(ai_frame, text="Clear History", command=self.clear_ai_history)
        clear_btn.pack(pady=10)
    
    def setup_performance_tab(self):
        """Setup performance tab"""
        # Performance frame
        perf_frame = ttk.LabelFrame(self.performance_frame, text="Performance Metrics", padding=10)
        perf_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Performance metrics
        self.win_rate_label = ttk.Label(perf_frame, text="Win Rate: 0%")
        self.win_rate_label.pack(anchor=tk.W)
        
        self.total_trades_label = ttk.Label(perf_frame, text="Total Trades: 0")
        self.total_trades_label.pack(anchor=tk.W)
        
        self.profit_factor_label = ttk.Label(perf_frame, text="Profit Factor: 0.00")
        self.profit_factor_label.pack(anchor=tk.W)
        
        self.avg_win_label = ttk.Label(perf_frame, text="Average Win: $0.00")
        self.avg_win_label.pack(anchor=tk.W)
        
        self.avg_loss_label = ttk.Label(perf_frame, text="Average Loss: $0.00")
        self.avg_loss_label.pack(anchor=tk.W)
        
        # Performance chart
        perf_fig, perf_ax = plt.subplots(figsize=(10, 6))
        self.perf_canvas = FigureCanvasTkAgg(perf_fig, master=perf_frame)
        self.perf_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def refresh_account(self):
        """Refresh account information"""
        try:
            account_info = mt5.account_info()
            if account_info:
                self.account_info = {
                    "balance": account_info.balance,
                    "equity": account_info.equity,
                    "margin": account_info.margin,
                    "free_margin": account_info.margin_free,
                    "margin_level": account_info.margin_level
                }
                
                # Update labels
                self.balance_label.config(text=f"Balance: ${account_info.balance:.2f}")
                self.equity_label.config(text=f"Equity: ${account_info.equity:.2f}")
                self.margin_label.config(text=f"Margin: ${account_info.margin:.2f}")
                self.free_margin_label.config(text=f"Free Margin: ${account_info.margin_free:.2f}")
                self.margin_level_label.config(text=f"Margin Level: {account_info.margin_level:.2f}%")
                
        except Exception as e:
            logger.error(f"Error refreshing account: {e}")
    
    def refresh_positions(self):
        """Refresh positions"""
        try:
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            
            # Get positions
            positions = mt5.positions_get()
            if positions:
                for position in positions:
                    self.positions_tree.insert('', 'end', values=(
                        position.ticket,
                        position.symbol,
                        'BUY' if position.type == mt5.POSITION_TYPE_BUY else 'SELL',
                        position.volume,
                        f"{position.price_open:.5f}",
                        f"{position.sl:.5f}" if position.sl > 0 else 'None',
                        f"{position.tp:.5f}" if position.tp > 0 else 'None',
                        f"${position.profit:.2f}"
                    ))
                    
        except Exception as e:
            logger.error(f"Error refreshing positions: {e}")
    
    def refresh_chart(self):
        """Refresh market chart"""
        try:
            # Get market data
            rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M1, 0, 100)
            if rates is not None:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
                # Clear previous plot
                self.ax.clear()
                
                # Plot price data
                self.ax.plot(df['time'], df['close'], label='Close Price', linewidth=1)
                self.ax.set_title('EUR/USD - Last 100 Minutes')
                self.ax.set_xlabel('Time')
                self.ax.set_ylabel('Price')
                self.ax.legend()
                self.ax.grid(True)
                
                # Rotate x-axis labels
                self.ax.tick_params(axis='x', rotation=45)
                
                # Refresh canvas
                self.canvas.draw()
                
        except Exception as e:
            logger.error(f"Error refreshing chart: {e}")
    
    def clear_ai_history(self):
        """Clear AI decision history"""
        self.ai_text.delete(1.0, tk.END)
        self.ai_decisions.clear()
    
    def update_data(self):
        """Update data periodically"""
        while True:
            try:
                # Update account info
                self.refresh_account()
                
                # Update positions
                self.refresh_positions()
                
                # Update chart
                self.refresh_chart()
                
                # Add AI decision to history (simulated)
                if len(self.ai_decisions) < 50:  # Limit history
                    decision_time = datetime.now().strftime("%H:%M:%S")
                    decisions = ["HOLD", "OPEN_BUY", "OPEN_SELL", "CLOSE_POSITION"]
                    decision = np.random.choice(decisions)
                    self.ai_decisions.append(f"[{decision_time}] AI Decision: {decision}")
                    self.ai_text.insert(tk.END, f"[{decision_time}] AI Decision: {decision}\n")
                    self.ai_text.see(tk.END)
                
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in update thread: {e}")
                time.sleep(30)
    
    def add_ai_decision(self, decision: str):
        """Add AI decision to dashboard"""
        decision_time = datetime.now().strftime("%H:%M:%S")
        self.ai_decisions.append(f"[{decision_time}] AI Decision: {decision}")
        self.ai_text.insert(tk.END, f"[{decision_time}] AI Decision: {decision}\n")
        self.ai_text.see(tk.END)
    
    def run(self):
        """Run the dashboard"""
        self.root.mainloop()


def initialize_mt5():
    """Initialize MT5 connection"""
    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    logger.info("MT5 initialized successfully")
    return True


def main():
    """Main function"""
    logger.info("Starting AI Trading Dashboard")
    
    # Initialize MT5
    if not initialize_mt5():
        return
    
    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        mt5.shutdown()
        return
    
    logger.info(f"Connected to MT5 account {account_info.login}")
    
    # Create and run dashboard
    dashboard = TradingDashboard()
    
    try:
        dashboard.run()
    except KeyboardInterrupt:
        logger.info("Stopping dashboard...")
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
    finally:
        mt5.shutdown()
        logger.info("MT5 connection closed")


if __name__ == "__main__":
    main()