import ollama

# Test Ollama with a simple XAUUSD-specific prompt
response = ollama.chat(
    model='phi3',
    messages=[
        {
            'role': 'user',
            'content': 'You are a professional commodity trader. What are the key considerations when trading XAUUSD (Gold vs USD) compared to EURUSD?'
        }
    ]
)

print("Ollama response for XAUUSD considerations:")
print(response['message']['content'])