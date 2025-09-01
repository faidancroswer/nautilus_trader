#!/usr/bin/env python3
"""
Test script to verify Ollama is returning correct trading information
"""

import requests
import json
import time

def test_ollama_trading_response():
    """Test if Ollama is returning correct trading decisions"""
    url = "http://localhost:11434/api/generate"
    model = "phi3:latest"
    
    # Sample trading prompt similar to what the system uses
    prompt = """GOLD TRADING - High volatility precious metal
Spread consideration: 30 points minimum
Market sessions affect volatility significantly

XAUUSD 2345.67
ALG: bullish (S:2.3%)
RSI: 65 MACD: 0.0045
VOL: 1.23% CHG1H: 0.5%

RULES:
- Strong Bull (>80% confidence): OPEN_BUY
- Strong Bear (>80% confidence): OPEN_SELL  
- Weak signals (<60% confidence): HOLD
- Opposite signals: CLOSE_POSITION

RESPOND: BUY/SELL/HOLD/CLOSE"""
    
    # Test payload
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.2,
        "max_tokens": 20
    }
    
    try:
        print(f"Testing Ollama trading decision with model: {model}")
        print(f"Prompt: {prompt[:100]}...")
        print("="*50)
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"Request took {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            decision_text = result.get('response', '').strip().upper()
            print("SUCCESS: Request successful!")
            print(f"Decision text: {decision_text}")
            
            # Check if the response contains valid trading decisions
            valid_decisions = ["BUY", "SELL", "HOLD", "CLOSE"]
            found_decision = False
            for decision in valid_decisions:
                if decision in decision_text:
                    print(f"SUCCESS: Valid trading decision found: {decision}")
                    found_decision = True
                    break
            
            if not found_decision:
                print("WARNING: No valid trading decision found in response")
                print("Response might not be in expected format")
            
            return True
        else:
            print(f"ERROR: Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Request error: {e}")
        return False

def test_available_models():
    """Check if the required model is available"""
    url = "http://localhost:11434/api/tags"
    
    try:
        print("Checking available Ollama models...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            models = [model['name'] for model in models_data.get('models', [])]
            print(f"Available models: {models}")
            
            # Check if our model is available
            if "phi3:latest" in models:
                print("SUCCESS: Model 'phi3:latest' is available!")
                return True
            else:
                print("ERROR: Model 'phi3:latest' not found!")
                return False
        else:
            print(f"ERROR: Failed to get models. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: Error checking models: {e}")
        return False

if __name__ == "__main__":
    print("=== OLLAMA TRADING RESPONSE TEST ===")
    print()
    
    # First check if model is available
    if not test_available_models():
        print("\nCannot proceed with trading test - model not available")
        exit(1)
    
    print()
    
    # Then test the trading response
    test_ollama_trading_response()