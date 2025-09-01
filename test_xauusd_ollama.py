import json
import ollama

def test_xauusd_ollama_analysis():
    \"\"\"Test Ollama analysis for XAUUSD with specific considerations\"\"\"
    
    # Simulated indicator data for XAUUSD
    indicators = {
        'price': 2350.50,
        'alligator_jaw': 2348.20,
        'alligator_teeth': 2349.80,
        'alligator_lips': 2351.30,
        'rsi': 65.5,
        'macd_line': 0.00125,
        'macd_signal': 0.00085,
        'macd_histogram': 0.00040
    }
    
    # Create an enhanced prompt specifically for XAUUSD
    def format_value(value, precision=5):
        \"\"\"Format numeric value or return 'N/A' if None\"\"\"
        if value is None:
            return 'N/A'
        return f\"{value:.{precision}f}\"
    
    prompt = f\"\"\"
You are a professional commodity trader specializing in the Alligator strategy for XAUUSD (Gold vs USD).
Analyze the following market conditions for XAUUSD and provide a trading decision.

Key considerations for XAUUSD:
1. Gold is a safe-haven asset with different volatility patterns than forex pairs
2. Gold often moves inversely to USD strength and risk sentiment
3. Economic data like inflation, interest rates, and geopolitical events heavily impact gold
4. Gold typically has lower pip values but higher point values than forex pairs

Current Market Data:
Price: {format_value(indicators['price'], 2)}
Alligator Jaw: {format_value(indicators['alligator_jaw'], 2)}
Alligator Teeth: {format_value(indicators['alligator_teeth'], 2)}
Alligator Lips: {format_value(indicators['alligator_lips'], 2)}
RSI (14): {format_value(indicators['rsi'], 2)}
MACD Line: {format_value(indicators['macd_line'], 5)}
MACD Signal: {format_value(indicators['macd_signal'], 5)}
MACD Histogram: {format_value(indicators['macd_histogram'], 5)}

Alligator Strategy Rules for XAUUSD:
1. OPEN_BUY when Alligator lines align in upward direction (Lips > Teeth > Jaw) AND RSI < 70
2. OPEN_SELL when Alligator lines align in downward direction (Lips < Teeth < Jaw) AND RSI > 30
3. CLOSE_POSITION when opposite alignment occurs OR RSI indicates overbought/oversold
4. HOLD when conditions are unclear or conflicting

Risk Management:
- Risk per trade: 1.5%
- Lot size: 0.1
- Consider the higher volatility of gold compared to forex pairs

Respond with ONLY ONE of these decisions:
- OPEN_BUY
- OPEN_SELL
- CLOSE_POSITION
- HOLD

Provide your reasoning in 1-2 sentences.
\"\"\"
    
    print(\"Prompt sent to Ollama:\")
    print(prompt)
    print(\"\\n\" + \"=\"*50 + \"\\n\")
    
    try:
        # Get decision from Ollama
        response = ollama.chat(
            model=\"phi3\",
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={
                'temperature': 0.1,
                'timeout': 10
            }
        )
        
        print(\"Ollama Response:\")
        print(response['message']['content'])
        
        # Extract decision
        decision_text = response['message']['content'].strip().upper()
        valid_decisions = ['OPEN_BUY', 'OPEN_SELL', 'CLOSE_POSITION', 'HOLD']
        
        decision = 'HOLD'
        for valid_decision in valid_decisions:
            if valid_decision in decision_text:
                decision = valid_decision
                break
        
        print(f\"\\nExtracted Decision: {decision}\")
        return decision
        
    except Exception as e:
        print(f\"Error getting AI decision: {e}\")
        return 'HOLD'

if __name__ == \"__main__\":
    test_xauusd_ollama_analysis()