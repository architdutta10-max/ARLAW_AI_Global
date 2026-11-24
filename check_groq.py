"""Optional connectivity check for the configured Groq provider.

Run manually when needed. This sends one short test request and never prints the API key.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv(override=False)

key = os.getenv("GROQ_API_KEY", "").strip()
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")

if not key:
    print("FAIL: GROQ_API_KEY is not configured.")
    raise SystemExit(1)

try:
    response = requests.post(
        base_url + "/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with the single word OK."}],
            "max_completion_tokens": 32,
            "temperature": 0,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    message = payload.get("choices", [{}])[0].get("message", {})
    answer = str(message.get("content") or "").strip()
    if not answer:
        print("FAIL: provider returned an empty response.")
        raise SystemExit(1)
    print("OK: Groq connection succeeded.")
    print("MODEL:", payload.get("model", model))
    print("ANSWER:", answer[:120])
except requests.Timeout:
    print("FAIL: Groq request timed out.")
    raise SystemExit(1)
except requests.RequestException as exc:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    print("FAIL: Groq request failed" + (f" (HTTP {status})." if status else "."))
    raise SystemExit(1)
except (ValueError, KeyError, IndexError, TypeError):
    print("FAIL: provider returned an unexpected response.")
    raise SystemExit(1)
