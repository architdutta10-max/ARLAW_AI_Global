# ARLAW AI Global

**An AI-assisted global legal, civil, economic and justice research platform.**

Release: **2.0.2 — Consolidated Direct-Launch Release** · See [RELEASE_QA.md](RELEASE_QA.md) for verified checks and limitations.

- Live application: https://arlaw-ai-global.onrender.com
- GitHub repository: https://github.com/architdutta10-max/ARLAW_AI_Global

ARLAW AI is an informational research assistant, not a law firm or substitute for qualified legal advice. AI output can be incomplete or wrong. Verify important matters against current official primary sources and consult a qualified professional.

## Integrated architecture

The existing FastAPI application and teal frontend are retained. The backend now includes:

- Groq cloud provider adapter. Gemini and Ollama are removed; no local model download is required.
- Task-specific routing for legal research, civil procedure, lawyer/advocate workflow assistance, accounting support, CA/tax research, neutral judicial research, finance, document review, translation and general tasks.
- Professional-workspace boundaries that prohibit claims of legal representation, account certification, statutory audit, tax attestation or judicial decision-making.
- Dedicated capability endpoint at `/api/capabilities` and in-app starter prompts for the professional workflows.
- Multilingual prompting for English, Hindi, Bengali and mixed-language queries.
- Optional independent multi-model peer review (`ARLAW_MULTI_MODEL_REVIEW=true`).
- Retrieval from the existing SQLite/FTS5 legal knowledge library.
- Citation-reference validation that checks whether `[S#]` labels exist in the retrieved set. This is not proof that a source supports a claim.
- LoRA/QLoRA supervised training and provenance-gated teacher-output distillation preparation.
- Automated tests and an API evaluation smoke runner.

See `docs/MULTI_MODEL_ARCHITECTURE.md` and `docs/PROFESSIONAL_WORKSPACES.md` for configuration, workflow scope and limitations.

## Run on Windows CMD

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
notepad .env
python run.py
```

Add your Groq key to `.env` as `GROQ_API_KEY=...`, save the file, then run `python run.py`. Open `http://127.0.0.1:8000` in your browser. The application loads `.env` automatically. No BAT launcher or local model runtime is needed. Keep `.env` private and never commit API keys.

## Configuration

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Required Groq credential; keep server-side |
| `GROQ_MODEL` | Groq model name |
| `GROQ_BASE_URL` | Groq API base URL |


Free-tier limits and availability vary. Only the Groq cloud provider is enabled in this release.

## Upgrade-free feature scope

Version 2.0.2 is intended as the consolidated, feature-complete handoff for the currently implemented scope. It is not a promise that software will never need maintenance: security fixes, dependency compatibility, model-provider changes and legal-source updates may still be necessary. See [RELEASE_QA.md](RELEASE_QA.md) for the exact release boundaries.

To update an existing Git checkout, first make a backup of your project and confirm that your working tree is clean. Extract this release to a separate folder, then manually copy the application files into your checkout while preserving `.git`, `.env`, `.venv` and your local `data` directory. Review `git status`, run the tests, and commit only after reviewing the diff. This release does not automatically modify or push your Git repository.

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

## Production deployment checklist

Before exposing this application to real users, add authentication and role-based access, API rate limits, HTTPS, secure secret management, encrypted backups, retention/deletion controls, audit logging, malware scanning for uploads, monitoring and an incident-response process. The current starter application is intended for controlled development and evaluation; do not treat it as a production-secure legal case-management system.

## Deployment

The existing `render.yaml`, GitHub Actions workflow and FastAPI start command are retained. Configure `GROQ_API_KEY` through Render Environment settings for hosted deployment. Locally, configure `.env` and run `python run.py`.

## Responsible data and legal use

Index only lawful, public, licensed and non-confidential material. Record jurisdiction, authority, language, URL and effective/as-of date. Do not upload privileged or confidential client records without an appropriate legal basis and safeguards. Confirm dataset and model licences before training or distribution.

## Developer

Archit Dutta · Siliguri, West Bengal, India

GitHub: https://github.com/architdutta10-max  
LinkedIn: https://www.linkedin.com/in/archit-dutta-4522693aa/  
Instagram: https://www.instagram.com/architdutta17?xtok=MWJoem0yZW9lcWVmOQ==

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
