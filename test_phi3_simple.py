#!/usr/bin/env python3
"""
Simple phi3 test with minimal prompt
"""

import requests
import json
import time

def test_phi3_simple():
    """Test phi3 with a very simple prompt"""
    url = "http://localhost:11434/api/generate"
    model = "phi3:latest"
    
    # Very simple prompt
    payload = {
        "model": model,
        "prompt": "BUY or SELL or HOLD?",
        "stream": False,
        "temperature": 0.2,
        "max_tokens": 10
    }
    
    try:
        print(f"Testing phi3 with simple prompt: {model}")
        print("="*50)
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"Request took {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            decision_text = result.get('response', '').strip().upper()
            print("SUCCESS: Request successful!")
            print(f"Response: {result.get('response', '')}")
            return True
        else:
            print(f"ERROR: Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Request error: {e}")
        return False

if __name__ == "__main__":
    print("=== PHI3 SIMPLE TEST ===")
    print()
    test_phi3_simple()