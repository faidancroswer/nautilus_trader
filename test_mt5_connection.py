import MetaTrader5 as mt5
import sys

# Initialize MT5
if not mt5.initialize():
    print("Failed to initialize MT5")
    sys.exit(1)

# Get account info
account_info = mt5.account_info()
if account_info is None:
    print("Failed to get account info")
    mt5.shutdown()
    sys.exit(1)

print("MT5 Connection Successful!")
print(f"Account Number: {account_info.login}")
print(f"Account Balance: {account_info.balance} {account_info.currency}")
print(f"Account Equity: {account_info.equity}")
print(f"Server: {account_info.server}")

# Check if EURUSD is available
eurusd_info = mt5.symbol_info("EURUSD")
if eurusd_info is not None:
    print(f"EURUSD is available. Current price: {eurusd_info.ask}")
else:
    print("EURUSD is not available")

mt5.shutdown()