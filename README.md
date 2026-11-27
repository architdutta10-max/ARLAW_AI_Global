<!-- ARLAW-4.0.0-RELEASE-SECTION -->

# ARLAW AI Global - Version 4.0.0

**Specialised legal, economic, judicial, governance and public-policy research assistant.**

## What's new in 4.0.0

- Strict purpose-scope gate for designated professional research and workflows.
- Shared external web-research gateway before conversational model-provider selection.
- Groq, Gemini and Ollama receive the same assembled local and external source packet.
- India is the default jurisdiction; relevant international and comparative research is supported.
- Research status is exposed at `/api/research/status`.

## Web research configuration

Set `TAVILY_API_KEY` in the deployment environment. `ARLAW_WEB_RESEARCH_ENABLED` defaults to `true`; set it to `false` to disable external search. Without the key, the application reports that live web research is unavailable and does not pretend to have searched. Search results are unverified research leads, not proof of source authority, authenticity, legal support or current validity.

## Limitations

A shared prompt and source packet do not guarantee identical model answers or legal accuracy. Citation-label validation is not semantic claim verification. Legal accuracy, source authenticity, source currency, production readiness and security are not certified. Verify important propositions against current official primary sources and obtain qualified professional review.

---

<!-- ARLAW-3.5.1-RELEASE-SECTION -->

# ARLAW AI Global - Version 3.5.1

**An AI-powered platform for legal research, economic understanding and judicial information.**

Release status: Release candidate prepared; production deployment is subject to successful merge and Render health verification.

## What's new in 3.5.1

- Improved statute-scoped retrieval for explicitly named Indian legislation.
- Added regression coverage to prevent same-numbered provisions from unrelated statutes appearing in named-statute searches.
- Refreshed official full-text BNS and Indian Contract Act corpus in the local audit database.
- Corrected same-day evidence review date handling in the legal release gate.
- Expanded automated regression coverage.

## Verification

- Automated test suite: 182 passed in the local audit environment.
- Python compilation: passed.
- Git diff whitespace check: passed.
- Local database retrieval checks: 4 of 4 passed for BNS Sections 303 and 308 and Contract Act Sections 10 and 11.

These checks do not certify overall legal accuracy, legal completeness, semantic citation support, production readiness or security.

## Production and legal limitations

The platform provides legal research and workflow assistance. It is not a law firm, court system or substitute for advice from a qualified lawyer. It does not make judicial decisions.

Legal accuracy, production readiness and security are not certified.

- Live application: https://arlaw-ai-global.onrender.com
- GitHub repository: https://github.com/architdutta10-max/ARLAW_AI_Global
- Health: https://arlaw-ai-global.onrender.com/api/health
- Model health: https://arlaw-ai-global.onrender.com/api/health/model

---
# ARLAW AI Global

**Version 3.3.1 — AI-assisted legal information and research platform**

- **Live application:** https://arlaw-ai-global.onrender.com
- **GitHub repository:** https://github.com/architdutta10-max/ARLAW_AI_Global

---

## Overview

ARLAW AI Global is an AI-powered application for exploring legal, civil, and economic topics through a conversational interface. It supports jurisdiction-aware legal information retrieval and statutory research workflows.

The platform is intended for informational and educational use. It is **not a law firm, does not provide legal representation, and is not a substitute for advice from a qualified lawyer**.

## Version 3.3.1 highlights

This release branch contains improvements to:

- Recognition of full statutory names, including the Bharatiya Nyaya Sanhita, 2023.
- Retrieval of relevant statutory provisions, including BNS Sections 303(1) and 303(2).
- Distinguishing statutory definition provisions from punishment provisions.
- Ambiguity handling when a question explicitly identifies the applicable legislation.
- Regression tests for statutory recognition and retrieval behaviour.

**Branch:** `fix/bns-section-retrieval-3.3.1`  
**Commit:** `f639495`

## Project information

| Item | Details |
|---|---|
| Project | ARLAW AI Global |
| Application framework | FastAPI |
| Hosting | Render |
| AI providers | Ollama and Groq are configured in the development environment; availability depends on deployment configuration |
| Current release branch | `fix/bns-section-retrieval-3.3.1` |

## Testing status

The 3.3.1 change set passed:

- Python compilation check.
- Automated test suite: **177 passed**.

Passing automated tests verifies only the behaviours covered by those tests. It does not independently establish legal accuracy, completeness of legal-source coverage, or production readiness.

## Legal-source and production-readiness status

ARLAW AI Global must distinguish verified legal materials from unverified or unavailable sources. It must not fabricate statutory text, quotations, case citations, section numbers, or source references. When authoritative source material is unavailable, the system should disclose that limitation.

Production certification requires, among other things:

- Verified legal-source coverage for supported jurisdictions.
- Frozen benchmarks and independently prepared answer keys.
- Verified persistent hosted storage.
- Independent security audit.
- Qualified human legal review and approval.
- Certified release metadata.

The 3.3.1 branch has **not** been certified as production-ready. The automated test result alone does not satisfy these release requirements.

## Live application

The currently hosted application is available at:

https://arlaw-ai-global.onrender.com

This link refers to the existing hosted service; it does not imply that branch `fix/bns-section-retrieval-3.3.1` has been deployed there.

## Technology

- Python
- FastAPI
- Ollama / Groq model-provider integrations
- Render

Refer to the repository's dependency and deployment configuration for the exact runtime requirements.

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/architdutta10-max/ARLAW_AI_Global.git
cd ARLAW_AI_Global
```

### 2. Create and activate a virtual environment

**Windows Command Prompt:**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

If the repository includes `requirements.txt`, run:

```bash
pip install -r requirements.txt
```

### 4. Configure provider credentials

Configure only the environment variables required by the provider(s) enabled in your deployment. For Groq, set `GROQ_API_KEY`.

**Windows Command Prompt (current session):**

```cmd
set GROQ_API_KEY=your_groq_api_key
```

**macOS / Linux:**

```bash
export GROQ_API_KEY="your_groq_api_key"
```

Never commit API keys, passwords, or other secrets to GitHub. Configure production secrets through the hosting provider's environment settings.

### 5. Start the application

The FastAPI application entry point is `app.main:app`. If Uvicorn is included in the project's dependencies, run:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open http://127.0.0.1:8000.

If the repository's dependency file or start command differs, follow the configuration included in the checked-out branch.

## Responsible use and legal disclaimer

AI-generated information may be incomplete, outdated, or incorrect. Laws and legal procedures vary by jurisdiction and change over time.

- Verify important information against current official legislation, regulations, and court or government sources.
- Consult a qualified legal professional about a real case, legal rights, deadlines, contracts, or court proceedings.
- Do not rely on generated output as the sole basis for legal, financial, or other high-impact decisions.
- Do not submit confidential, privileged, or sensitive personal information unless you understand and accept the application's data-handling arrangements.

**Using this application does not create a lawyer-client relationship.**

## Contributing

Suggestions, bug reports, and improvements are welcome. Please open an issue in the GitHub repository before proposing substantial changes.

For pull requests:

1. Explain the purpose of the change.
2. Keep API keys and other secrets out of the code.
3. Include relevant testing or reproduction steps.
4. Do not describe the application as legally certified or production-ready unless the required independent evidence and approvals exist.

## Developer

**Archit Dutta**

- **GitHub:** https://github.com/architdutta10-max

## Creator

Created by **Archit Dutta**. [LinkedIn profile](https://www.linkedin.com/in/archit-dutta-4522693aa/)

## Source verification limitations

A source citation does not determine whether that source actually supports the generated answer. Legal citations and retrieved materials must be independently checked against the authoritative statutory text.

## License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## Social links

- LinkedIn: https://www.linkedin.com/in/archit-dutta-4522693aa/
- Instagram: https://www.instagram.com/architdutta17

## Verification, history and security limitations

A source citation does not determine whether that source actually supports the generated answer. Legal citations and retrieved materials must be independently checked against authoritative statutory text.

Conversation history is stored locally in the browser and is not synchronized to the server or other devices.

Automated tests do not constitute a production security audit. Independent security review is required before production certification.


## v3.5.1 ? Legal retrieval reliability

- Corrected source metadata selection in legal knowledge retrieval so
  full-text source filtering can operate as intended.
- Prevented bundled full-statute text from crowding out focused legal
  research sources for unrelated legal queries.
- Retained full-statute retrieval for queries that explicitly identify
  the relevant statute.
- Added regression coverage for legal-source retrieval and ranking.
- Release validation: 182 automated tests passed.
