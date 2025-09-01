import json
from alligator_ai_trading import AlligatorStrategy

def test_xauusd_analysis():
    \"\"\"Test the XAUUSD analysis with Ollama\"\"\"
    print(\"Testing XAUUSD analysis with Ollama...\")
    
    # Initialize the strategy
    strategy = AlligatorStrategy()
    
    # Get current indicators
    print(\"Fetching current indicators for XAUUSD...\")
    indicators = strategy.get_current_indicators()
    
    if indicators is None:
        print(\"Failed to get indicators\")
        return
    
    print(\"\\nCurrent Indicators:\")
    for key, value in indicators.items():
        print(f\"{key}: {value}\")
    
    # Get AI decision
    print(\"\\nGetting AI decision...\")
    decision = strategy.get_ai_decision(indicators)
    print(f\"AI Decision: {decision}\")
    
    # Show the prompt that was sent to Ollama
    print(\"\\nPrompt sent to Ollama:\")
    
    def format_value(value, precision=5):
        \"\"\"Format numeric value or return 'N/A' if None\"\"\"
        if value is None:
            return 'N/A'
        return f\"{value:.{precision}f}\"
    
    prompt = f\"\"\"
You are a professional forex trader specializing in the Alligator strategy.
Analyze the following market conditions for {strategy.symbol} and provide a trading decision.

Current Market Data:
Price: {format_value(indicators['price'], 5)}
Alligator Jaw: {format_value(indicators['alligator_jaw'], 5)}
Alligator Teeth: {format_value(indicators['alligator_teeth'], 5)}
Alligator Lips: {format_value(indicators['alligator_lips'], 5)}
RSI ({strategy.rsi_params['period']}): {format_value(indicators['rsi'], 2)}
MACD Line: {format_value(indicators['macd_line'], 5)}
MACD Signal: {format_value(indicators['macd_signal'], 5)}
MACD Histogram: {format_value(indicators['macd_histogram'], 5)}

Trading Rules:
1. OPEN_BUY when Alligator lines align in upward direction (Lips > Teeth > Jaw) and RSI < 70
2. OPEN_SELL when Alligator lines align in downward direction (Lips < Teeth < Jaw) and RSI > 30
3. CLOSE_POSITION when opposite alignment occurs or RSI indicates overbought/oversold
4. HOLD when conditions are unclear

Risk Management:
- Risk per trade: {strategy.risk_percent}%
- Lot size: {strategy.lot_size}

Respond with ONLY ONE of these decisions:
- OPEN_BUY
- OPEN_SELL
- CLOSE_POSITION
- HOLD
\"\"\"
    
    print(prompt)

if __name__ == \"__main__\":
    test_xauusd_analysis()