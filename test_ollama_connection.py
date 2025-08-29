import ollama
import sys

try:
    # Test Ollama connection
    response = ollama.list()
    print("Ollama Connection Successful!")
    print(f"Number of models available: {len(response.models)}")
    
    # Test a simple prompt
    response = ollama.chat(model='llama3', messages=[
        {
            'role': 'user',
            'content': 'Hello, please respond with "Connection test successful" if you receive this message.',
        },
    ])
    print(f"Test response: {response.message.content}")
    
    print("Ollama is ready for use!")
    
except Exception as e:
    print(f"Error connecting to Ollama: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)