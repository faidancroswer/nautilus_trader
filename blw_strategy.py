import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from datetime import datetime

# --- Configuration ---
SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_H1
MAGIC = 1147485642
DEVIATION = 20

# Strategy Parameters (Default from MQ4)
RISK_PERCENT = 1.0
LOT_VAR = 1  # 0: FixLot, 1: AutoLot (Risk %), 2: Balance Step
FIX_LOT = 0.01
BREAK_EVEN = 1000  # Points
MIN_PROFIT = 500   # Points
TRAILING_STOP = 1000 # Points
STOP_LOSS = 3000     # Points
TAKE_PROFIT = 10000  # Points
MAX_SPREAD = 30      # Points
ROLL_BACK = 1000     # Points
INDENT = 0           # Points
START_HOUR = 0
END_HOUR = 23
USE_SMART_TP = True
SMART_TP_DOLLARS = 10.0
USE_MAX_DD = True
MAX_DD_PERCENT = 30.0

# ZigZag Parameters
EXT_DEPTH = 18
EXT_DEVIATION = 5
EXT_BACKSTEP = 3

from blw_agent import RiskManager

class BLWStrategy:
    def __init__(self):
        self.symbol = SYMBOL
        self.timeframe = TIMEFRAME
        self.magic = MAGIC
        
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            # quit() 
            
        print(f"Connected to MT5: {mt5.version()}")
        
        # Initialize AI Agent
        self.agent = RiskManager(self.magic, self.symbol)
        print("AI Risk Agent Initialized.")

    def get_data(self, bars=1000):
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, bars)
        if rates is None:
            print("Failed to get rates")
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def point(self, df):
        # Helper to get point size
        return 0.01

    def calculate_zigzag(self, df, depth=12, deviation=5, backstep=3):
        """
        Calculates ZigZag indicator using standard High/Low + Deviation logic.
        """
        high = df['high'].values
        low = df['low'].values
        n = len(df)
        
        zigzag = np.zeros(n)
        zigzag[:] = np.nan
        
        last_high = high[0]
        last_low = low[0]
        last_high_pos = 0
        last_low_pos = 0
        
        # 1 = Looking for Peak, -1 = Looking for Valley
        trend = 0 
        
        for i in range(depth, n):
            curr_high = high[i]
            curr_low = low[i]
            
            if trend == 0:
                if curr_high > last_high:
                    last_high = curr_high
                    last_high_pos = i
                if curr_low < last_low:
                    last_low = curr_low
                    last_low_pos = i
                
                if (curr_high - last_low) >= (deviation * self.point(df)):
                    trend = 1 # Found a low, now going up
                    zigzag[last_low_pos] = last_low
                    last_high = curr_high
                    last_high_pos = i
                elif (last_high - curr_low) >= (deviation * self.point(df)):
                    trend = -1 # Found a high, now going down
                    zigzag[last_high_pos] = last_high
                    last_low = curr_low
                    last_low_pos = i
                    
            elif trend == 1: # Looking for Peak
                if curr_high > last_high:
                    last_high = curr_high
                    last_high_pos = i
                elif (last_high - curr_low) >= (deviation * self.point(df)):
                    # Confirmed Peak
                    zigzag[last_high_pos] = last_high
                    trend = -1 # Switch to looking for Valley
                    last_low = curr_low
                    last_low_pos = i
                    
            elif trend == -1: # Looking for Valley
                if curr_low < last_low:
                    last_low = curr_low
                    last_low_pos = i
                elif (curr_high - last_low) >= (deviation * self.point(df)):
                    # Confirmed Valley
                    zigzag[last_low_pos] = last_low
                    trend = 1 # Switch to looking for Peak
                    last_high = curr_high
                    last_high_pos = i
                    
        df['zigzag'] = zigzag
        return df

    def get_last_zigzag_values(self, df):
        # Get last 2 non-nan zigzag values
        zz_values = df[df['zigzag'].notna()]
        if len(zz_values) < 2:
            return None, None
        
        last_zz = zz_values.iloc[-1]
        prev_zz = zz_values.iloc[-2]
        
        return last_zz, prev_zz

    def get_signal(self, df):
        """
        Generates trading signals based on ZigZag.
        Returns: (signal_type, price, sl, tp) or None
        """
        df = self.calculate_zigzag(df, EXT_DEPTH, EXT_DEVIATION, EXT_BACKSTEP)
        last_zz, prev_zz = self.get_last_zigzag_values(df)
        
        if last_zz is None:
            return None

        last_val = last_zz['zigzag']
        prev_val = prev_zz['zigzag']
        
        # Determine which is High and which is Low
        if last_val > prev_val: # Last point is High, Prev is Low
            high_val = last_val
            low_val = prev_val
        else: # Last point is Low, Prev is High
            high_val = prev_val
            low_val = last_val
            
        point = self.point(df)
        
        buy_price = high_val + INDENT * point
        sell_price = low_val - INDENT * point
        
        return {
            'buy_stop': buy_price,
            'sell_stop': sell_price,
            'sl_buy': buy_price - STOP_LOSS * point if STOP_LOSS > 0 else 0,
            'tp_buy': buy_price + TAKE_PROFIT * point if TAKE_PROFIT > 0 else 0,
            'sl_sell': sell_price + STOP_LOSS * point if STOP_LOSS > 0 else 0,
            'tp_sell': sell_price - TAKE_PROFIT * point if TAKE_PROFIT > 0 else 0
        }

    def check_trading_conditions(self, df):
        signals = self.get_signal(df)
        if not signals:
            return

        print(f"Signals at {df.iloc[-1]['time']}: {signals}")
        
        # Execution Logic
        if not mt5.terminal_info().trade_allowed:
            print("AutoTrading disabled in terminal")
            return

        # Get existing orders
        orders = mt5.orders_get(symbol=self.symbol, magic=self.magic)
        
        # Delete all pending orders (Simple approach: Replace all)
        if orders:
            for order in orders:
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": order.ticket,
                    "magic": self.magic,
                }
                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"Failed to remove order {order.ticket}: {result.comment}")

        # Get current market prices
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            print("Failed to get tick data")
            return
            
        ask = tick.ask
        bid = tick.bid
        
        # Place New Orders
        # Buy Stop
        buy_price = float(signals['buy_stop'])
        sl_buy = float(signals['sl_buy'])
        tp_buy = float(signals['tp_buy'])
        
        if buy_price > ask:
            request_buy = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": self.symbol,
                "volume": FIX_LOT,
                "type": mt5.ORDER_TYPE_BUY_STOP,
                "price": buy_price,
                "sl": sl_buy,
                "tp": tp_buy,
                "magic": self.magic,
                "comment": "BLW Python Buy",
                "type_time": mt5.ORDER_TIME_GTC, 
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result_buy = mt5.order_send(request_buy)
            if result_buy.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Failed to place Buy Stop: {result_buy.comment} (Retcode: {result_buy.retcode})")
            else:
                print(f"Placed Buy Stop at {buy_price}")
        else:
            print(f"Skipping Buy Stop: Price {buy_price} is not above Ask {ask}")
            
        # Sell Stop
        sell_price = float(signals['sell_stop'])
        sl_sell = float(signals['sl_sell'])
        tp_sell = float(signals['tp_sell'])
        
        if sell_price < bid:
            request_sell = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": self.symbol,
                "volume": FIX_LOT,
                "type": mt5.ORDER_TYPE_SELL_STOP,
                "price": sell_price,
                "sl": sl_sell,
                "tp": tp_sell,
                "magic": self.magic,
                "comment": "BLW Python Sell",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result_sell = mt5.order_send(request_sell)
            if result_sell.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Failed to place Sell Stop: {result_sell.comment} (Retcode: {result_sell.retcode})")
            else:
                print(f"Placed Sell Stop at {sell_price}")
        else:
            print(f"Skipping Sell Stop: Price {sell_price} is not below Bid {bid}")

    def run(self):
        print("Starting BLW Strategy with AI Agent...")
        last_learn_time = time.time()
        
        while True:
            # 1. AI Agent Management (Fast Loop)
            self.agent.manage_positions()
            
            # 2. Strategy Logic (Every 10 seconds or new bar?)
            # We can check conditions less frequently
            if int(time.time()) % 10 == 0:
                df = self.get_data()
                if df is not None:
                    self.check_trading_conditions(df)
            
            # 3. Learning (Every hour)
            if time.time() - last_learn_time > 3600:
                print("Running AI Learning...")
                self.agent.learn()
                last_learn_time = time.time()
                
            time.sleep(1) # Fast loop for risk management

if __name__ == "__main__":
    strategy = BLWStrategy()
    strategy.run()
