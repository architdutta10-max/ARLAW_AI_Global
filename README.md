# ARLAW AI Global

**An AI-assisted global legal, civil, economic, financial and justice research workspace.**

- **Release:** 3.0.6 — India-default jurisdiction selection and long-prompt legal retrieval correction
- **Live application:** https://arlaw-ai-global.onrender.com
- **Repository:** https://github.com/architdutta10-max/ARLAW_AI_Global

> **Important:** ARLAW AI provides informational research and workflow assistance. It is not a law firm, lawyer, advocate, accountant, government authority or judicial decision-maker. AI output can be inaccurate, incomplete or out of date. Verify important propositions against current official primary sources and consult a qualified professional.

## What ARLAW AI does

ARLAW AI combines a FastAPI application, a browser-based research workspace, retrieval from a local SQLite/FTS5 knowledge library and configurable language-model providers.

### Main capabilities

- **Legal research:** jurisdiction-aware explanations, issue spotting, legal concepts, source-oriented research and research planning.
- **Civil and judicial research support:** neutral organisation of issues, evidence, arguments and potentially relevant authorities. It does not decide credibility, guilt, liability or outcomes.
- **Lawyer and advocate workflow assistance:** research memos, drafting support, checklists and matter organisation. It does not represent clients or certify court filings.
- **Accounting support:** bookkeeping explanations, reconciliations and financial-statement analysis. It does not certify accounts or perform statutory audits.
- **CA and tax research support:** tax research, worked calculations and compliance-preparation assistance. It does not sign, attest or certify regulated work.
- **Economic and finance research:** retrieval from the indexed research library and explanation of supplied material.
- **Multilingual prompting:** English, Hindi, Bengali and mixed-language prompts, subject to the configured model's language capability.
- **Knowledge library:** locally index text, Markdown and text-extractable PDF documents with jurisdiction, source URL, authority, language and effective/as-of date metadata.
- **Provider fallback:** route requests to the configured providers in preference order, for example local Ollama followed by Groq.
- **Workspace preferences:** light/dark appearance, 36 accent-colour palettes, interface language, text sizing, contrast and reduced motion.

## AI architecture

```text
Browser workspace
      |
      | POST /api/chat
      v
FastAPI application (app/main.py)
      |
      +--> Task classification and provider routing (app/llm.py)
      |
      +--> SQLite + FTS5 retrieval (app/knowledge.py)
      |        |
      |        +--> Jurisdiction and topic/category filters
      |        +--> Query-term relevance ranking
      |        +--> Duplicate-source collapse
      |
      +--> Configured model provider
               |
               +--> Ollama (local model runtime)
               |
               +--> Groq (cloud fallback, when configured)
```

### Model providers

- **Ollama** runs a model locally on the machine or host where Ollama is installed. The example configuration uses `qwen3:8b`; actual speed and quality depend on hardware, model quantisation and runtime settings.
- **Groq** is an optional hosted provider. Its API key is read by the server from environment configuration and must never be exposed in frontend JavaScript or committed to Git.
- **Provider order** is configurable. `ollama,groq` means try Ollama first and use Groq if the earlier provider cannot complete the request. Fallback is best-effort and depends on provider availability, credentials, quotas and network access.
- **Task routing** classifies prompts into supported workflow categories such as legal research, civil procedure, lawyer assistance, accounting, tax, judicial research, translation and general assistance. Routing labels guide prompts and provider selection; they do not create specialist professional qualifications.

### Retrieval and knowledge library

The retrieval layer stores source metadata and text chunks in SQLite and searches chunks with FTS5. Results are filtered by jurisdiction and broad content category, ranked using query-term coverage and title matches, and collapsed so a source contributes its strongest matching chunk.

The application exposes:
- `GET /api/capabilities` — declared workflows, language prompting and verification boundary.
- `GET /api/health` and `GET /api/health/model` — application and provider configuration status.
- `GET /api/jurisdictions` — jurisdiction list.
- `GET /api/coverage` — source-registry inventory only; not proof of indexed or current law.
- `GET /api/registry` — source-directory metadata.
- `GET /api/sources` — indexed-source metadata.
- `POST /api/documents` — local indexing for supported document formats.
- `POST /api/chat` — chat generation and retrieved-source metadata.

## Verification and important limitations

These limitations are intentional and should be understood before relying on outputs:

1. **Citation validation is not legal source verification.** The current validator checks whether a cited reference label (such as `[S1]`) exists among the sources supplied to the model. It does not determine whether that source actually supports the specific sentence or legal proposition, whether the quotation is accurate, whether the source is binding, whether it remains good law, or whether later amendments or judgments changed the position. Retrieval relevance is a search-ranking heuristic, not proof of legal support. Independently inspect the source and verify the proposition.
2. **Chat history is browser-local.** Recent conversations are stored in the current browser's local storage. They are not synchronized to the server or other devices. Clearing browser storage or changing browsers/devices can make that history unavailable. Server-side cross-device history requires an authenticated account system, access controls and retention/deletion safeguards; a browser-only identifier is not a safe substitute for authentication. Individual conversations can be deleted from the recent-chat list using the delete control; ARLAW asks for confirmation and removes the selected conversation from this browser.
3. **Tests are not a production audit.** Automated tests and smoke checks demonstrate selected software behaviours only. They do not constitute a production security audit, penetration test, privacy review, legal-accuracy audit, or certification of professional suitability.
4. **Knowledge currency depends on the indexed material.** The app does not automatically guarantee that statutes, regulations, judgments or source URLs are current. Record effective dates and verify changes using authoritative primary sources.
5. **Bundled digests are secondary educational material.** Short summaries are not full official judgments and are not proof of current legal status or subsequent judicial treatment.
6. **Model output is probabilistic.** Provider availability, model updates, context limits, generation settings and hardware can change response quality and latency.

## Run on Windows CMD

```cmd
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-test.txt
copy .env.example .env
notepad .env
ollama pull qwen3:8b
python run.py
```

Install Ollama separately before running `ollama pull qwen3:8b`, and keep the Ollama service running. Configure `GROQ_API_KEY` in `.env` only if you want the optional cloud fallback. Save `.env`, start the app and open `http://127.0.0.1:8000`.

If a working `.venv` already exists, activate it and install/update dependencies rather than recreating it. Never upload `.env`, `.env.backup`, API keys, private databases or virtual-environment folders to GitHub.

## Configuration

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Server-side Groq credential |
| `GROQ_MODEL` | Groq model identifier |
| `GROQ_BASE_URL` | Groq-compatible API base URL |
| `OLLAMA_ENABLED` | Enable or disable local Ollama |
| `OLLAMA_BASE_URL` | Ollama endpoint; defaults to `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Local model name; example `qwen3:8b` |
| `OLLAMA_TIMEOUT` | Ollama request timeout |
| `OLLAMA_NUM_PREDICT` | Generation token limit |
| `ARLAW_PROVIDER_ORDER` | Provider preference, e.g. `ollama,groq` |
| `ARLAW_TOP_K` | Maximum retrieved source records |

See `.env.example`, `OLLAMA_SETUP.md`, `DEPLOYMENT.md` and `docs/MULTI_MODEL_ARCHITECTURE.md` for the full configuration context.

## User interface and colour options

Open **Settings** in the application header. Choose Light or Dark appearance and one of 36 accent palettes: Teal, Ocean, Sky, Blue, Royal, Indigo, Violet, Purple, Orchid, Magenta, Pink, Rose, Ruby, Red, Coral, Orange, Amber, Gold, Lime, Green, Emerald, Mint, Forest, Sage, Cyan, Turquoise, Aqua, Slate, Steel, Graphite, Charcoal, Brown, Copper, Terracotta, Plum or Lavender.

The chosen accent and other preferences are stored in local browser storage. They are not sent to the model API. Recent chats are also stored locally in this browser only (up to 10 conversations); they are not synced across devices.

## Tests and evaluation

```cmd
python -m pip install -r requirements-test.txt
python -m pytest -q
python -m compileall -q app tests
```

With the app running, use:

```cmd
python evaluation\\run_eval.py --base-url http://127.0.0.1:8000
```

The test suite checks selected functions and integration contracts. The evaluation runner checks API availability and response generation. Neither can certify legal correctness, source support, security or production readiness.

## Version 3.0 security and deployment changes

- Per-IP, in-process request throttling for chat and uploads (defaults: 20 chat requests/minute and 5 uploads/minute). This is a basic abuse control, not distributed rate limiting.
- Strict user/assistant message-role validation and jurisdiction-code validation.
- Bounded upload reads, UTF-8 text validation, PDF encryption/page-count checks, extracted-text limits and generated storage filenames that do not retain user-supplied filenames.
- Response security headers and no-store caching for API responses.
- Clean release packaging: secrets, local databases, virtual environments, Git metadata, caches and backup folders are excluded.
- Storage paths remain configurable with `ARLAW_DATA_DIR`, `ARLAW_DB_PATH` and `ARLAW_UPLOAD_DIR`.

**Important deployment limits:** Render Free uses ephemeral filesystem storage. SQLite data and uploaded files can be lost during restarts or redeploys. The included `render.yaml` deliberately stays on the free plan and does not pretend to provide persistent storage. Attach a paid persistent disk mounted at `/var/data` and set `ARLAW_DATA_DIR=/var/data`, or use managed external database/object storage, before expecting durable data.

**Authentication is not yet implemented.** Do not use this public deployment for privileged, confidential, personal, client, financial or other sensitive documents. Before production use, add user login, authorization, per-user data isolation, secure session/CSRF controls, deletion and retention workflows, malware scanning, shared rate limiting and an independent security review.

## Production deployment checklist

Before opening the service to real users, implement and independently review:
- Authentication, account lifecycle and role-based authorization.
- Secure server-side conversation storage with per-user access controls, retention limits, export and deletion.
- HTTPS, secure secret management, key rotation and restricted deployment permissions.
- API rate limits, request-size limits and abuse monitoring.
- Encrypted backups, audit logging, monitoring and incident response.
- Malware scanning and safe handling for uploaded documents.
- Privacy notice, data-retention policy and legal basis for uploaded material.
- Independent security testing and legal-source validation workflows.

Version 3.0 adds request throttling, stricter request validation, safer document handling, security headers and clean release packaging. It still does not include user accounts, role-based access control, distributed rate limiting, malware scanning, persistent storage on Render Free, or an independent security/legal-accuracy audit. Treat it as a public research demo until those controls are added.

## Responsible data and legal use

Index only lawful, public, licensed and non-confidential material. Record jurisdiction, authority, language, URL and effective/as-of date. Do not upload privileged or confidential client records without an appropriate legal basis and safeguards. Confirm dataset and model licences before training or distribution. Retrieval-augmented generation is not fine-tuning; the normal chat/retrieval path does not retrain foundation-model weights.

## Developer

**Archit Dutta** · Siliguri, West Bengal, India

- GitHub: https://github.com/architdutta10-max
- LinkedIn: https://www.linkedin.com/in/archit-dutta-4522693aa/
- Instagram: https://www.instagram.com/architdutta17/

## License

MIT. See [LICENSE](LICENSE).

## Accuracy and jurisdiction coverage safeguards

- `GET /api/coverage` reports which jurisdictions have source-registry starting points. This is an inventory only; it does not claim full-text indexing, completeness, currency, or legal authority for a particular issue.
- The chat endpoint asks a clarification question for selected underspecified numbered references (for example, an agenda number without an issuing body/session, a resolution number without issuer/year, or an article/section number without its legal instrument). It does not call the language model for these cases.
- Legal retrieval remains jurisdiction-restricted. A registry link is not treated as retrieved evidence, and a declared authority label is not independently verified.
- Before expanding any jurisdiction's corpus, verify the official publisher, version/effective date, reuse terms, language, and stable document identifier. Keep official primary texts separate from case summaries and commentary.

## Version 3.2 optional model integrations

The standard installation remains lightweight. Optional image and NLP models are installed separately with `pip install -r requirements-ml.txt` (TensorFlow CPU, TensorFlow Hub, Pillow, Transformers and PyTorch). The model catalog is available at `GET /api/models`; image classification is exposed at `POST /api/models/vision/{mobilenet|resnet50|vgg16}` using a multipart `file`, and Hugging Face text inference at `POST /api/models/huggingface` with JSON `{ "text": "...", "task": "sentiment-analysis", "model": "..." }`. Models load lazily and may require substantial RAM, disk space and first-run downloads; do not install the ML extra on a small Render instance unless its resources support it. MobileNetV2 and ResNet-50 use TensorFlow Hub ImageNet classifiers; VGG-16 uses TensorFlow Keras Applications because a maintained matching VGG-16 classifier is not listed in the TensorFlow Hub image-classification catalogue. These are generic object classifiers, not OCR or legal-document models. The Hugging Face endpoint supports sentiment/text classification, zero-shot classification (supply 2–20 `candidate_labels`), token classification/NER and feature extraction. Set `ARLAW_HF_ALLOWED_MODELS` to a comma-separated model allowlist if exposing inference to untrusted callers. The default Hugging Face model is sentiment analysis, not a legal-answer model. They do not replace the legal retrieval/evidence gate or certify legal accuracy.

Chat history is stored in browser local storage. Version 3.2 adds individual deletion, selecting and deleting multiple conversations, and clearing all local conversations. It is not synchronized between devices.


### Indian legal corpus refresh (3.2.0)

The bundled retrieval guides cover BNS, BNSS, BSA, the DPDP Act, DPDP Rules 2025, the DPDP commencement notification, the Limitation Act 1963 (including Schedule navigation), Indian Contract Act 1872 Sections 2, 19, 22 and 23, and Income-tax Act 2025 / Income-tax Rules 2026 material for Tax Year 2026-27. These guides are not full statutory reproductions. To fetch and index the complete official PDFs and official Income Tax Department HTML guidance, run this explicitly from the project root:

```bash
python scripts/refresh_indian_legal_corpus.py
```

The script uses a fixed HTTPS host allowlist and size limit, refuses short/empty extracts, replaces only its own managed records, and does not run during web-service startup. Review the result for every source and check later Gazette amendments before legal use.
