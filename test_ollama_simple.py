#!/usr/bin/env python3
"""
Simple test script for Ollama integration
"""

import ollama
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ollama():
    """Test Ollama connection and basic functionality"""
    try:
        logger.info("Testing Ollama connection...")
        
        # Test basic connection
        response = ollama.list()
        logger.info("Ollama connection successful!")
        
        # Test simple chat
        logger.info("Testing simple chat...")
        response = ollama.chat(
            model='phi3',
            messages=[
                {
                    'role': 'user',
                    'content': 'Respond with "OK" only.',
                },
            ]
        )
        
        logger.info(f"Chat response: {response['message']['content']}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing Ollama: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting simple Ollama test...")
    
    if test_ollama():
        logger.info("Ollama test passed!")
        return True
    else:
        logger.error("Ollama test failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)