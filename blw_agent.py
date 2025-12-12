import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
import json
import time
from datetime import datetime

class RiskManager:
    def __init__(self, magic_number, symbol="XAUUSD"):
        self.magic = magic_number
        self.symbol = symbol
        self.history_file = "trade_history.csv"
        self.status_file = "agent_status.json"
        
        # Learning Parameters (Defaults)
        self.sl_multiplier = 2.0       # 2x ATR
        self.tp_multiplier = 4.0       # 4x ATR
        
        # Volatility Regimes (Learned Parameters)
        # "Low": ATR < 200, "Normal": 200 <= ATR < 500, "High": ATR >= 500
        self.volatility_regimes = {
            "Low": {"sl_mult": 2.0, "tp_mult": 4.0, "win_rate": 0.0},
            "Normal": {"sl_mult": 2.0, "tp_mult": 4.0, "win_rate": 0.0},
            "High": {"sl_mult": 1.5, "tp_mult": 5.0, "win_rate": 0.0} # Tighter SL, wider TP in high vol
        }
        
        self.current_regime = "Normal"

        self.profit_lock_percent = 0.4 # If profit drops X% from max, close. (0.4 = 40% drop)
        
        # State tracking for Profit Lock (Max profit seen per ticket)
        self.max_profits = {} 
        self.last_save_time = 0
        
        # Market Status (from Strategy)
        self.market_status = {
            "atr": 0,
            "atr_threshold": 0,
            "is_volatility_ok": False,
            "is_time_ok": False,
            "current_hour": 0
        }

    def update_market_status(self, atr, threshold, vol_ok, time_ok, hour):
        self.market_status = {
            "atr": atr,
            "atr_threshold": threshold,
            "is_volatility_ok": vol_ok,
            "is_time_ok": time_ok,
            "current_hour": hour
        }
        
        # Determine Regime
        if atr < 200:
            self.current_regime = "Low"
        elif atr >= 500:
            self.current_regime = "High"
        else:
            self.current_regime = "Normal"
            
        # Update active multipliers from regime
        regime_params = self.volatility_regimes[self.current_regime]
        self.sl_multiplier = regime_params["sl_mult"]
        self.tp_multiplier = regime_params["tp_mult"]

    def get_dynamic_sl(self, atr):
        if atr <= 0: return 500 # Fallback
        return atr * self.sl_multiplier

    def get_dynamic_tp(self, atr):
        if atr <= 0: return 3000 # Fallback
        return atr * self.tp_multiplier

    def save_status(self):
        """
        Saves current agent state to JSON for dashboard monitoring.
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "symbol": self.symbol,
            "parameters": {
                "sl_multiplier": self.sl_multiplier,
                "tp_multiplier": self.tp_multiplier,
                "current_regime": self.current_regime,
                "profit_lock_percent": self.profit_lock_percent
            },
            "market_status": self.market_status,
            "active_tracking": len(self.max_profits),
            "learning_history_size": os.path.getsize(self.history_file) if os.path.exists(self.history_file) else 0
        }
        
        try:
            with open(self.status_file, "w") as f:
                json.dump(status, f, indent=4)
        except Exception as e:
            print(f"Failed to save agent status: {e}")

    def manage_positions(self):
        """
        Scans open positions and applies risk management rules.
        """
        # Save status periodically (e.g., every 5 seconds)
        if time.time() - self.last_save_time > 5:
            self.save_status()
            self.last_save_time = time.time()

        positions = mt5.positions_get(symbol=self.symbol, magic=self.magic)
        if not positions:
            self.max_profits = {} # Reset cache if no positions
            return

        # Get current ATR for dynamic management
        current_atr = self.market_status.get('atr', 0)
        if current_atr <= 0:
            current_atr = 200 # Fallback default
            
        # Dynamic Parameters
        be_trigger = 1.5 * current_atr
        be_padding = 0.2 * current_atr
        trail_start = 2.0 * current_atr
        trail_dist = 1.0 * current_atr

        for pos in positions:
            self._manage_single_position(pos, be_trigger, be_padding, trail_start, trail_dist)

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
            
            winners = df[df['Profit'] > 0]
            losers = df[df['Profit'] <= 0]
            
            # Update Win Rate for current regime
            regime = self.current_regime
            if not df.empty:
                win_rate = len(winners) / len(df)
                self.volatility_regimes[regime]['win_rate'] = win_rate
            
            # Adjust Multipliers based on performance
            if not winners.empty and not losers.empty:
                avg_win = winners['Profit'].mean()
                avg_loss = abs(losers['Profit'].mean())
                
                # If Risk/Reward is bad (Loss > Win), tighten SL Multiplier
                if avg_loss > avg_win:
                    self.volatility_regimes[regime]['sl_mult'] = max(1.0, self.volatility_regimes[regime]['sl_mult'] * 0.95)
                    print(f"AI Agent ({regime}): Tightened SL Multiplier to {self.volatility_regimes[regime]['sl_mult']:.2f}")
                
                # If Win Rate is high, boost TP Multiplier
                if win_rate > 0.6:
                    self.volatility_regimes[regime]['tp_mult'] *= 1.05
                    print(f"AI Agent ({regime}): Increased TP Multiplier to {self.volatility_regimes[regime]['tp_mult']:.2f}")

            self.save_status() # Save immediately after update
                    
        except Exception as e:
            print(f"AI Learning Error: {e}")

    def _manage_single_position(self, pos, be_trigger, be_padding, trail_start, trail_dist):
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
        
        # 1. Smart BreakEven (Dynamic)
        if profit_points >= be_trigger:
            new_sl = 0.0
            if pos_type == mt5.POSITION_TYPE_BUY:
                proposed_sl = entry_price + be_padding * mt5.symbol_info(self.symbol).point
                if sl < proposed_sl or sl == 0:
                    new_sl = proposed_sl
            else:
                proposed_sl = entry_price - be_padding * mt5.symbol_info(self.symbol).point
                if sl > proposed_sl or sl == 0:
                    new_sl = proposed_sl
            
            if new_sl != 0:
                self._modify_position(ticket, new_sl, tp, "Smart BreakEven (ATR)")

        # 2. Dynamic Trailing Stop (ATR)
        if profit_points >= trail_start:
            new_sl = 0.0
            if pos_type == mt5.POSITION_TYPE_BUY:
                proposed_sl = current_price - trail_dist * mt5.symbol_info(self.symbol).point
                if proposed_sl > sl: # Only move SL up
                    new_sl = proposed_sl
            else:
                proposed_sl = current_price + trail_dist * mt5.symbol_info(self.symbol).point
                if proposed_sl < sl or sl == 0: # Only move SL down
                    new_sl = proposed_sl
            
            if new_sl != 0:
                self._modify_position(ticket, new_sl, tp, "Dynamic Trailing (ATR)")

        # 3. Profit Lock (Anti-Reversal)
        if max_profit >= trail_start:
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
