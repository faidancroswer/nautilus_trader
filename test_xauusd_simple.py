import ollama

# Test Ollama with XAUUSD-specific prompt
prompt = """
You are a professional commodity trader. What are key considerations when trading XAUUSD (Gold vs USD) compared to forex pairs like EURUSD?
"""

response = ollama.chat(
    model='phi3',
    messages=[
        {
            'role': 'user',
            'content': prompt
        }
    ]
)

print("Ollama response for XAUUSD considerations:")
print(response['message']['content'])