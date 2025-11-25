import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
from datetime import datetime

class RiskManager:
    def __init__(self, magic_number, symbol="XAUUSD"):
        self.magic = magic_number
        self.symbol = symbol
        self.history_file = "trade_history.csv"
        
        # Learning Parameters (Defaults)
        self.breakeven_trigger = 300   # Points profit to trigger BE
        self.breakeven_padding = 50    # Points above entry to place BE
        self.trailing_start = 500      # Points profit to start trailing
        self.trailing_dist = 200       # Distance for trailing stop
        self.profit_lock_percent = 0.4 # If profit drops X% from max, close. (0.4 = 40% drop)
        
        # State tracking for Profit Lock (Max profit seen per ticket)
        self.max_profits = {} 

    def manage_positions(self):
        """
        Scans open positions and applies risk management rules.
        """
        positions = mt5.positions_get(symbol=self.symbol, magic=self.magic)
        if not positions:
            self.max_profits = {} # Reset cache if no positions
            return

        for pos in positions:
            self._manage_single_position(pos)

    def _manage_single_position(self, pos):
        ticket = pos.ticket
        entry_price = pos.price_open
        current_price = pos.price_current
        sl = pos.sl
        tp = pos.tp
        pos_type = pos.type
        
        # Calculate Profit in Points
        if pos_type == mt5.POSITION_TYPE_BUY:
            profit_points = (current_price - entry_price) / mt5.symbol_info(self.symbol).point
        else:
            profit_points = (entry_price - current_price) / mt5.symbol_info(self.symbol).point
            
        # Track Max Profit for this ticket
        if ticket not in self.max_profits:
            self.max_profits[ticket] = 0.0
        
        if profit_points > self.max_profits[ticket]:
            self.max_profits[ticket] = profit_points
            
        max_profit = self.max_profits[ticket]
        
        # 1. Smart BreakEven
        # If profit > trigger and SL is worse than entry + padding
        if profit_points >= self.breakeven_trigger:
            new_sl = 0.0
            if pos_type == mt5.POSITION_TYPE_BUY:
                proposed_sl = entry_price + self.breakeven_padding * mt5.symbol_info(self.symbol).point
                if sl < proposed_sl or sl == 0:
                    new_sl = proposed_sl
            else:
                proposed_sl = entry_price - self.breakeven_padding * mt5.symbol_info(self.symbol).point
                if sl > proposed_sl or sl == 0:
                    new_sl = proposed_sl
            
            if new_sl != 0:
                self._modify_position(ticket, new_sl, tp, "Smart BreakEven")

        # 2. Dynamic Trailing Stop
        if profit_points >= self.trailing_start:
            new_sl = 0.0
            if pos_type == mt5.POSITION_TYPE_BUY:
                proposed_sl = current_price - self.trailing_dist * mt5.symbol_info(self.symbol).point
                if proposed_sl > sl: # Only move SL up
                    new_sl = proposed_sl
            else:
                proposed_sl = current_price + self.trailing_dist * mt5.symbol_info(self.symbol).point
                if proposed_sl < sl or sl == 0: # Only move SL down
                    new_sl = proposed_sl
            
            if new_sl != 0:
                self._modify_position(ticket, new_sl, tp, "Dynamic Trailing")

        # 3. Profit Lock (Anti-Reversal)
        # If we had significant profit but it dropped by X%, close immediately.
        # Only active if we have reached at least some decent profit (e.g. Trailing Start)
        if max_profit >= self.trailing_start:
            drop_percent = (max_profit - profit_points) / max_profit
            if drop_percent >= self.profit_lock_percent:
                print(f"Profit Lock Triggered: Max {max_profit}, Curr {profit_points}, Drop {drop_percent:.2%}")
                self._close_position(ticket, "Profit Lock Reversal Protection")

    def _modify_position(self, ticket, sl, tp, comment):
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": float(sl),
            "tp": float(tp),
            "magic": self.magic,
            "comment": comment
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to modify position {ticket} ({comment}): {result.comment}")
        else:
            print(f"Modified position {ticket} ({comment})")

    def _close_position(self, ticket, comment):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "magic": self.magic,
            "comment": comment,
            "type": mt5.ORDER_TYPE_BUY if mt5.positions_get(ticket=ticket)[0].type == mt5.POSITION_TYPE_SELL else mt5.ORDER_TYPE_SELL,
            "volume": mt5.positions_get(ticket=ticket)[0].volume,
        }
        # Actually closing is simpler with library usually, but let's use standard close request
        # We need to send opposite order
        pos = mt5.positions_get(ticket=ticket)[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(self.symbol).bid if close_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(self.symbol).ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "magic": self.magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close position {ticket} ({comment}): {result.comment}")
        else:
            print(f"Closed position {ticket} ({comment})")

    def log_trade(self, ticket, profit, reason):
        """
        Logs closed trade to CSV for learning.
        """
        file_exists = os.path.isfile(self.history_file)
        with open(self.history_file, "a") as f:
            if not file_exists:
                f.write("Time,Ticket,Profit,Reason,MaxProfit\n")
            
            # We might not have MaxProfit if we just initialized, but we try
            max_p = self.max_profits.get(ticket, 0)
            f.write(f"{datetime.now()},{ticket},{profit},{reason},{max_p}\n")

    def monitor_closed_trades(self):
        """
        Scans MT5 history for recently closed trades to log them for learning.
        """
        from_date = datetime.now() - pd.Timedelta(hours=24)
        deals = mt5.history_deals_get(date_from=from_date, group="*")
        
        if deals:
            for deal in deals:
                if deal.symbol == self.symbol and deal.magic == self.magic and deal.entry == mt5.DEAL_ENTRY_OUT:
                    # Check if already logged (Simple check by ticket in file?)
                    # For efficiency, we might just append and let pandas handle duplicates later or keep a set of logged tickets in memory
                    self.log_trade(deal.ticket, deal.profit, "MT5 History")

    def learn(self):
        """
        Analyzes history and updates parameters.
        """
        self.monitor_closed_trades() # Update log first
        
        if not os.path.isfile(self.history_file):
            return

        try:
            df = pd.read_csv(self.history_file)
            if len(df) < 10: 
                return
            
            # Remove duplicates based on Ticket
            df = df.drop_duplicates(subset=['Ticket'])
            
            # Logic:
            # If we have winning trades, see if we could have trailed tighter?
            # If we have losing trades, see if they were once profitable?
            
            winners = df[df['Profit'] > 0]
            if not winners.empty:
                # Simple learning: Adjust trailing start
                avg_win_max = winners['MaxProfit'].mean() if 'MaxProfit' in winners.columns else 0
                if avg_win_max > 0:
                    suggested_trail = avg_win_max * 0.5
                    self.trailing_start = (self.trailing_start * 0.9) + (suggested_trail * 0.1)
                    print(f"AI Agent: Adjusted Trailing Start to {self.trailing_start:.2f}")
                    
        except Exception as e:
            print(f"AI Learning Error: {e}")
