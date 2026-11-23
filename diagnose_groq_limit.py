
import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

if not key:
    print("GROQ API KEY MISSING")
    raise SystemExit(1)

try:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": "Reply with: ARLAW connection test successful."}
            ],
            "max_completion_tokens": 256
        },
        timeout=60
    )

    print("HTTP STATUS:", response.status_code)
    print("RESPONSE:", response.text[:3000])

except requests.RequestException as error:
    print("CONNECTION ERROR:", str(error))

