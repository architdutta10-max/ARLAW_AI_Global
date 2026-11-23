# ARLAW AI Global

**An AI-assisted global legal, civil, economic and justice research platform.**

Release: **2.3.0 — Retrieval Integrity and Workspace Refinement** · See [RELEASE_QA.md](RELEASE_QA.md) for verified checks and limitations.

- Live application: https://arlaw-ai-global.onrender.com
- GitHub repository: https://github.com/architdutta10-max/ARLAW_AI_Global

ARLAW AI is an informational research assistant, not a law firm or substitute for qualified legal advice. AI output can be incomplete or wrong. Verify important matters against current official primary sources and consult a qualified professional.

## Integrated architecture

The existing FastAPI application and teal frontend are retained. The backend now includes:

- Ollama local inference with configurable Groq cloud fallback. Default preference is Ollama first, then Groq when a Groq key is configured.
- Task-specific routing for legal research, civil procedure, lawyer/advocate workflow assistance, accounting support, CA/tax research, neutral judicial research, finance, document review, translation and general tasks.
- Professional-workspace boundaries that prohibit claims of legal representation, account certification, statutory audit, tax attestation or judicial decision-making.
- Dedicated capability endpoint at `/api/capabilities` and in-app starter prompts for the professional workflows.
- Multilingual prompting for English, Hindi, Bengali and mixed-language queries.
- Optional independent multi-model peer review (`ARLAW_MULTI_MODEL_REVIEW=true`).
- Retrieval from the existing SQLite/FTS5 legal knowledge library.
- Topic- and jurisdiction-aware retrieval, ranked by query-term coverage, with duplicate-source collapse. Citation-reference checking accepts `[S#]` and bold `**S#**` labels, and explicitly reports that label existence is not proof of claim support.
- LoRA/QLoRA supervised training and provenance-gated teacher-output distillation preparation.
- Automated tests and an API evaluation smoke runner.

See `docs/MULTI_MODEL_ARCHITECTURE.md` and `docs/PROFESSIONAL_WORKSPACES.md` for configuration, workflow scope and limitations.

## Run on Windows CMD

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install pytest
copy .env.example .env
notepad .env
ollama pull qwen3:8b
python run.py
```

Install Ollama separately before running `ollama pull qwen3:8b`. Keep Ollama running in the background. The default provider order is `ollama,groq`; local Ollama inference works without a cloud key. Add a Groq key to `.env` as `GROQ_API_KEY=...` only if you want cloud fallback. Save `.env`, run `python run.py`, and open `http://127.0.0.1:8000`. The app loads `.env` automatically. Keep `.env` private and never commit API keys. If you already have a working `.venv`, do not recreate it; activate it and install/update dependencies instead.

## Configuration

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Required Groq credential; keep server-side |
| `GROQ_MODEL` | Groq model name |
| `GROQ_BASE_URL` | Groq API base URL |
| `OLLAMA_ENABLED` | Enable/disable the local Ollama provider |
| `OLLAMA_BASE_URL` | Ollama server URL (default `http://127.0.0.1:11434`) |
| `OLLAMA_MODEL` | Local model name (default `qwen3:8b`) |
| `OLLAMA_TIMEOUT` | Ollama request timeout in seconds |
| `OLLAMA_NUM_PREDICT` | Maximum generated tokens |
| `ARLAW_PROVIDER_ORDER` | Provider order, e.g. `ollama,groq` |
| `ARLAW_TOP_K` | Maximum retrieved source records |


Ollama is a local model runtime, not a model itself. `qwen3:8b` is a general-purpose open-weight model choice, not a copy of Grok and not guaranteed to match its capabilities. Local speed and quality depend on RAM, CPU/GPU and model quantisation. If the local server is unavailable, ARLAW tries the next enabled provider in the configured order.

## Release scope

Version 2.3.0 adds topic/jurisdiction-aware retrieval, safer citation-label reporting, persistent browser-local recent chats, clearer request status and a refined responsive interface. The provider preference/fallback behavior remains configurable and is not a guarantee of model availability. It is not a promise that software will never need maintenance: security fixes, dependency compatibility, model-provider changes and legal-source updates may still be necessary. See [RELEASE_QA.md](RELEASE_QA.md) for the exact release boundaries and [RELEASE_NOTES.md](RELEASE_NOTES.md) for the 2.3.0 changes.

To update an existing Git checkout, back up the project and extract this ZIP into the existing checkout, allowing the release files to replace older project files. The ZIP intentionally excludes `.git`, `.env`, `.venv` and local database/upload contents. Then run `PUSH_TO_GITHUB.cmd` from the project root, review the staged changes when prompted, and confirm the push. The helper does not create or change your Git remote.

## Tests and evaluation

```cmd
python -m pip install pytest
python -m pytest -q
```

With the app running:

```cmd
python evaluation\run_eval.py --base-url http://127.0.0.1:8000
```

The evaluation runner checks API availability and response generation; it does not certify legal correctness.

## Production deployment checklist

Before exposing this application to real users, add authentication and role-based access, API rate limits, HTTPS, secure secret management, encrypted backups, retention/deletion controls, audit logging, malware scanning for uploads, monitoring and an incident-response process. The current starter application is intended for controlled development and evaluation; do not treat it as a production-secure legal case-management system.

## Deployment

The existing `render.yaml`, GitHub Actions workflow and FastAPI start command are retained. Configure `GROQ_API_KEY` through Render Environment settings for hosted deployment. Locally, configure `.env` and run `python run.py`.

## Responsible data and legal use

Index only lawful, public, licensed and non-confidential material. Record jurisdiction, authority, language, URL and effective/as-of date. The bundled landmark-case digests are short secondary educational summaries, not the full official judgments and not proof of current legal status; retrieve and verify the primary decision and later treatment before relying on a proposition. The bundled economic/shortage content is a research framework, not a live data feed or current shortage alert. Use dated official releases for current values. Do not upload privileged or confidential client records without an appropriate legal basis and safeguards. Confirm dataset and model licences before training or distribution. Retrieval augmentation is not fine-tuning; no foundation model weights are retrained by this release.

## Developer

Archit Dutta · Siliguri, West Bengal, India

GitHub: https://github.com/architdutta10-max  
LinkedIn: https://www.linkedin.com/in/archit-dutta-4522693aa/  
Instagram: https://www.instagram.com/architdutta17?xtok=MWJoem0yZW9lcWVmOQ==

## License

MIT. See `LICENSE`.

## User settings and accessibility

Open **Settings** from the top-right area of the application header. Recent chats are stored in this browser only (up to 10 conversations); they are not synced to the server or other devices. Preferences are stored locally in the current browser and are not sent to the AI backend.

Available controls:
- Appearance: Light or Dark mode
- Interface language: English, Hindi, or Bengali
- Text size: Small, Default, Large, or Extra large
- Higher contrast
- Reduce motion

The Settings dialog can be closed with its close button, by clicking outside it, or with Escape. Use **Reset preferences** to restore defaults.
