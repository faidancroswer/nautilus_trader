import ollama

try:
    # Simple test
    response = ollama.chat(
        model='phi3',
        messages=[
            {
                'role': 'user',
                'content': 'Hello, are you working?'
            }
        ]
    )
    print("Ollama is working correctly!")
    print("Response:", response['message']['content'])
except Exception as e:
    print(f"Error connecting to Ollama: {e}")