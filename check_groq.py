import os
import requests

# Read the API key without displaying it
with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.strip().startswith("GROQ_API_KEY="):
            os.environ["GROQ_API_KEY"] = line.strip().split("=", 1)[1].strip().strip('"').strip("'")

key = os.getenv("GROQ_API_KEY", "")
model = "openai/gpt-oss-20b"

if not key:
    print("FAIL: GROQ_API_KEY is missing")
    raise SystemExit(1)

print("API key found. Testing Groq...")

try:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": "Reply with ARLAW ONLINE"}
            ],
            "max_tokens": 30
        },
        timeout=30
    )

    print("HTTP STATUS:", response.status_code)

    if response.ok:
        print("AI RESPONSE:",
              response.json()["choices"][0]["message"]["content"])
        print("GROQ CONNECTION: SUCCESS")
    else:
        print("GROQ ERROR:", response.text[:1500])

except requests.RequestException as e:
    print("NETWORK ERROR:", str(e))