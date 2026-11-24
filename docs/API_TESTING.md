# API testing (Windows PowerShell 5.1)

Start the app in one PowerShell window and leave it running:

```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\ARLAW_AI_Global"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second PowerShell window, run:

```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\ARLAW_AI_Global"
.\scripts\test_api.ps1
```

The chat endpoint expects this JSON structure (not a top-level `message` field):

```json
{
  "messages": [{"role": "user", "content": "Explain Article 21 of the Constitution of India."}],
  "jurisdiction": "IN",
  "use_knowledge": true
}
```

Use registered jurisdiction codes from `GET /api/jurisdictions`, such as `IN`, `US`, `GLOBAL`, `INTL`, and `EU`; do not send display names such as `India`. The API accepts 1–30 messages, each with 1–14,000 characters.

The smoke test checks endpoint operation and ambiguity clarification. It does not certify legal accuracy, source support, or current validity.
