import os
import requests

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.strip().startswith("GROQ_API_KEY="):
            os.environ["GROQ_API_KEY"] = line.strip().split("=", 1)[1].strip().strip('"'^).strip^("'"^)

key = os.getenv("GROQ_API_KEY", "")
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

if not key:
    print("FAIL: API key missing")
    raise SystemExit(1)

r = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}"},
    json={
        "model": model,
        "messages": [{"role": "user", "content": "Compare Ohio civil rights law with federal anti-discrimination law. Give a concise answer."}],
        "max_completion_tokens": 4096
    },
    timeout=90
)
print("HTTP:", r.status_code)
data = r.json()
if not r.ok:
    print("ERROR:", data.get("error", {}).get("message", "Unknown error"))
    raise SystemExit(1)
choice = data["choices"][0]
message = choice.get("message") or {}
content = message.get("content") or ""
print("MODEL:", data.get("model"))
print("FINISH REASON:", choice.get("finish_reason"))
print("CONTENT LENGTH:", len(content))
print("USAGE:", data.get("usage"))
print("ANSWER:", content[:5000] if content else "[EMPTY]")
