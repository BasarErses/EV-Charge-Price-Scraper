import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("ANTHROPIC_API_KEY")
print(f"Key loaded: {key[:10]}...{key[-4:] if key else ''}")

client = Anthropic(api_key=key)

try:
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Hello, world"}
        ]
    )
    print(f"Success: {message.content[0].text}")
except Exception as e:
    print(f"Error: {e}")
