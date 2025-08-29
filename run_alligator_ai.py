#!/usr/bin/env python3
"""
Run script for the Alligator AI trading strategy
"""

import sys
import logging
from fast_alligator_ai import FastAlligatorAIStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('run_alligator_ai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the Alligator AI trading strategy"""
    logger.info("Starting Alligator AI trading strategy...")
    
    try:
        # Create and run the strategy
        strategy = FastAlligatorAIStrategy()
        strategy.run()
        
        logger.info("Alligator AI trading strategy completed successfully")
        return True
        
    except KeyboardInterrupt:
        logger.info("Trading strategy interrupted by user")
        return True
    except Exception as e:
        logger.error(f"Error running Alligator AI trading strategy: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)