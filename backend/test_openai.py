
"""Quick test to verify OpenAI works"""

import os
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

print("Testing OpenAI connection...")

try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'CodeGen AI is working!'"}
        ]
    )
    
    print("✅ Success!")
    print(response.choices[0].message.content)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nCheck:")
    print("1. Is your OPENAI_API_KEY in .env correct?")
    print("2. Did you add billing to OpenAI account?")

