#!/usr/bin/env python3
"""
Test script for Ollama integration
"""

import ollama
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ollama_connection():
    """Test Ollama connection and model availability"""
    try:
        logger.info("Testing Ollama connection...")
        
        # Test connection
        response = ollama.list()
        logger.info("Ollama connection successful!")
        
        # Print available models
        if hasattr(response, 'models'):
            logger.info(f"Available models: {[model.name for model in response.models]}")
        elif isinstance(response, dict) and 'models' in response:
            logger.info(f"Available models: {response['models']}")
        else:
            logger.info("Unable to determine available models format")
        
        # Test phi3 model with a simple prompt
        logger.info("Testing phi3 model...")
        response = ollama.chat(
            model='phi3',
            messages=[
                {
                    'role': 'user',
                    'content': 'Respond with "OK" if you receive this message.',
                },
            ],
            options={
                'temperature': 0.1,
                'timeout': 10
            }
        )
        
        if isinstance(response, dict) and 'message' in response:
            logger.info(f"Model response: {response['message']['content']}")
        else:
            logger.info(f"Model response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing Ollama: {e}")
        return False

def test_trading_prompt():
    """Test a sample trading prompt"""
    try:
        logger.info("Testing trading prompt...")
        
        # Sample trading data
        prompt = """
        EURUSD=1.12345 JAW=1.12340 TEETH=1.12335 LIPS=1.12330
        RULES: LIPS>TEETH>JAW=BUY, LIPS<TEETH<JAW=SELL, ELSE=HOLD
        RESPOND: BUY/SELL/HOLD ONLY
        """
        
        response = ollama.chat(
            model='phi3',
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            options={
                'temperature': 0.1,
                'timeout': 10
            }
        )
        
        if isinstance(response, dict) and 'message' in response:
            logger.info(f"Trading prompt response: {response['message']['content']}")
        else:
            logger.info(f"Trading prompt response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing trading prompt: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting Ollama integration tests...")
    
    # Test connection
    if not test_ollama_connection():
        logger.error("Ollama connection test failed")
        return False
    
    # Test trading prompt
    if not test_trading_prompt():
        logger.error("Trading prompt test failed")
        return False
    
    logger.info("All Ollama integration tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)