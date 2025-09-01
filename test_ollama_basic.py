#!/usr/bin/env python3
"""
Simple Ollama connectivity test
"""

import requests
import json
import time

def test_ollama_basic():
    """Test basic Ollama connectivity"""
    url = "http://localhost:11434/api/generate"
    model = "phi3:latest"
    
    # Simple test prompt
    payload = {
        "model": model,
        "prompt": "Say hello",
        "stream": False
    }
    
    try:
        print(f"Testing basic Ollama connectivity with model: {model}")
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"Request took {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Basic connectivity test passed!")
            print(f"Response: {result.get('response', '')[:100]}...")
            return True
        else:
            print(f"ERROR: Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Request error: {e}")
        return False

def test_ollama_tags():
    """Test if we can get model tags"""
    url = "http://localhost:11434/api/tags"
    
    try:
        print("Testing Ollama tags endpoint...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            print("SUCCESS: Tags endpoint working!")
            print(f"Models available: {[model['name'] for model in models_data.get('models', [])]}")
            return True
        else:
            print(f"ERROR: Tags endpoint failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: Tags endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("=== OLLAMA BASIC CONNECTIVITY TEST ===")
    print()
    
    # Test tags endpoint first
    if not test_ollama_tags():
        print("\nTags endpoint failed - Ollama may not be running properly")
        exit(1)
    
    print()
    
    # Test basic connectivity
    test_ollama_basic()