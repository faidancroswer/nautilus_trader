from alligator_ai_trading import AlligatorStrategy

def test_ollama_xauusd_analysis():
    \"\"\"Test Ollama analysis with real XAUUSD data\"\"\"
    print(\"Testing Ollama analysis for XAUUSD...\")

    # Initialize strategy
    strategy = AlligatorStrategy()

    # Verify symbol
    print(f\"Trading symbol: {strategy.symbol}\")

    # Get indicators
    print(\"Fetching indicators...\")
    indicators = strategy.get_current_indicators()

    if indicators is None:
        print(\"Failed to get indicators\")
        return

    print(\"\\nCurrent Indicators:\")
    for key, value in indicators.items():
        print(f\"  {key}: {value}\")

    # Get AI decision
    print(\"\\nGetting AI decision...\")
    decision = strategy.get_ai_decision(indicators)
    print(f\"AI Decision: {decision}\")

if __name__ == \"__main__\":
    test_ollama_xauusd_analysis()