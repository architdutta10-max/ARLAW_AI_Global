# ARLAW AI Global 3.0 — Deployment

## 1. Prepare secrets

1. Rotate any Groq API key that was included in an earlier ZIP, email, log or public repository.
2. Add the replacement as `GROQ_API_KEY` in Render's Environment settings.
3. Never commit `.env`, `.env.backup`, API keys, local databases or uploaded documents.
4. Keep `OLLAMA_ENABLED=false` on Render unless you have separately provisioned an Ollama service reachable from the web service.

## 2. Deploy

1. Push the clean project folder to the GitHub repository.
2. In Render, create a Blueprint from that repository, or create a Python web service.
3. Use `pip install -r requirements.txt` as the build command.
4. Use `uvicorn app.main:app --host 0.0.0.0 --port $PORT` as the start command.
5. Set `GROQ_API_KEY` as a secret environment variable.
6. Confirm `/api/health`, `/api/health/model` and `/docs`.

## 3. Storage

The free Render filesystem is ephemeral. Data in `data/`, including SQLite and uploaded source files, may be lost on restart/redeploy.

For durable storage, attach a persistent disk (paid Render plan) mounted at `/var/data` and set:

```text
ARLAW_DATA_DIR=/var/data
```

Alternatively, configure managed database and object storage and update the storage layer accordingly. Do not assume a successful deploy means data is persistent.

## 4. Operational safeguards in 3.0

- Chat: default 20 requests per minute per client IP.
- Uploads: default 5 requests per minute per client IP.
- Upload size: default maximum 20 MiB.
- PDF page count: default maximum 300 pages.
- API responses: no-store cache policy and security headers.
- Jurisdiction and message role validation.

These rate limits are in-process and reset on restart. They are not a substitute for edge/WAF controls or shared Redis-backed limits.

## 5. Before real-user or client-data use

This release does not include user authentication or per-user authorization/data isolation. Do not accept privileged, confidential, personal or sensitive documents. Add authentication, authorization, secure session and CSRF protections, malware scanning, retention/deletion controls, audit logging, monitoring, backups, shared rate limiting and independent security testing first.

## 6. Smoke tests

```bash
python -m pip install -r requirements-test.txt
python -m pytest -q
python -m compileall -q app tests
```

After deployment:

```bash
curl https://YOUR-SERVICE.onrender.com/api/health
curl https://YOUR-SERVICE.onrender.com/api/health/model
```

Automated tests and health endpoints do not certify legal accuracy, source support, security or production suitability.
