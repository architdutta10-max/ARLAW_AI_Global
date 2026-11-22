# ARLAW AI Global

**An AI-assisted global legal, civil, economic and justice research platform.**

- Live application: https://arlaw-ai-global.onrender.com
- GitHub repository: https://github.com/architdutta10-max/ARLAW_AI_Global

ARLAW AI is an informational research assistant, not a law firm or substitute for qualified legal advice. AI output can be incomplete or wrong. Verify important matters against current official primary sources and consult a qualified professional.

## Integrated architecture

The existing FastAPI application and teal frontend are retained. The backend now includes:

- Groq, Ollama and OpenAI-compatible provider adapters with automatic fallback.
- Task-specific routing for legal research, civil procedure, finance/tax, document review, translation and general tasks.
- Multilingual prompting for English, Hindi, Bengali and mixed-language queries.
- Optional independent multi-model peer review (`ARLAW_MULTI_MODEL_REVIEW=true`).
- Retrieval from the existing SQLite/FTS5 legal knowledge library.
- Citation-reference validation that checks whether `[S#]` labels exist in the retrieved set. This is not proof that a source supports a claim.
- LoRA/QLoRA supervised training and provenance-gated teacher-output distillation preparation.
- Automated tests and an API evaluation smoke runner.

See `docs/MULTI_MODEL_ARCHITECTURE.md` for configuration and limitations.

## Run on Windows CMD

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Configure provider environment variables in the current CMD session or deployment dashboard. Never commit API keys. For local Ollama, install Ollama separately, pull the model in `OLLAMA_MODEL`, and set `ARLAW_PROVIDER_ORDER=ollama`. Example model download command: `ollama pull qwen3:1.7b`.

## Configuration

| Variable | Purpose |
|---|---|
| `ARLAW_PROVIDER_ORDER` | Default provider priority |
| `ARLAW_ROUTE_LEGAL_RESEARCH` | Provider priority for legal research |
| `ARLAW_ROUTE_CIVIL_PROCEDURE` | Provider priority for civil procedure |
| `ARLAW_ROUTE_FINANCE_TAX` | Provider priority for finance/tax |
| `ARLAW_ROUTE_DOCUMENT_REVIEW` | Provider priority for document review |
| `ARLAW_ROUTE_TRANSLATION` | Provider priority for translation |
| `ARLAW_MULTI_MODEL_REVIEW` | Enable independent peer review from other configured providers |
| `GROQ_API_KEY` | Optional Groq credential; keep server-side |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Local Ollama endpoint/model |
| `OPENAI_COMPATIBLE_BASE_URL`, `OPENAI_COMPATIBLE_MODEL` | Optional compatible endpoint/model |

Free-tier limits and availability vary. Render cannot reach Ollama running on a developer's own computer via `localhost`; use a reachable hosted endpoint or keep Ollama local.

## Tests and evaluation

```cmd
python -m pip install pytest
pytest -q
```

With the app running:

```cmd
python evaluation\run_eval.py --base-url http://127.0.0.1:8000
```

The evaluation runner checks API availability and response generation; it does not certify legal correctness.

## Deployment

The existing `render.yaml`, GitHub Actions workflow and FastAPI start command are retained. Configure secrets through Render Environment settings. Set a provider accessible from Render (for example Groq with an environment key). Local Ollama is intended for local development unless deployed on an accessible host.

## Responsible data and legal use

Index only lawful, public, licensed and non-confidential material. Record jurisdiction, authority, language, URL and effective/as-of date. Do not upload privileged or confidential client records without an appropriate legal basis and safeguards. Confirm dataset and model licences before training or distribution.

## Developer

Archit Dutta · Siliguri, West Bengal, India

GitHub: https://github.com/architdutta10-max

## License

MIT. See `LICENSE`.

## User settings and accessibility

Open **Settings** from the top-right area of the application header. Preferences are stored locally in the current browser and are not sent to the AI backend.

Available controls:
- Appearance: Light or Dark mode
- Interface language: English, Hindi, or Bengali
- Text size: Small, Default, Large, or Extra large
- Higher contrast
- Reduce motion

The Settings dialog can be closed with its close button, by clicking outside it, or with Escape. Use **Reset preferences** to restore defaults.
